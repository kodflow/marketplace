#!/usr/bin/env python3
"""Garde-fou des messages de commit — hook PreToolUse de commit-guard.

Intercepte les commandes `git commit` avant leur exécution et refuse celles qui :

  1. portent un marqueur de rédaction par IA (attribution, pied « Generated
     with », emoji robot, trailer de session d'agent) ;
  2. ne respectent pas la convention de commit Kodflow ;
  3. contournent les hooks git avec --no-verify ;
  4. ouvriraient un éditeur interactif, ce qui fige la session.

Le refus passe par `permissionDecision: "deny"`, dont la raison est le seul canal
de sortie d'un hook PreToolUse que Claude lit réellement : le message contient
donc la règle violée et le gabarit attendu, pour que la correction soit possible
sans aller-retour.

Les tournures seulement suspectes (vocabulaire d'orchestration, méta-discours)
ne bloquent jamais : elles remontent en `additionalContext`. Le vocabulaire
télécom légitime — décalage de phase, traitement par lot, agent X1 — ne doit
produire aucun bruit.

Toute anomalie interne se solde par un exit 0 silencieux : fail-open.

Entrée  : charge utile du hook, en JSON sur stdin.
Sortie  : un objet JSON sur stdout, ou rien.
Code    : toujours 0 — le refus est porté par le JSON, pas par le code de sortie.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import unicodedata

# --------------------------------------------------------------------------
# Convention de commit Kodflow (valeurs par défaut, surchargeables par projet)
# --------------------------------------------------------------------------

DEFAULT_TYPES = [
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "test",
    "build",
    "ci",
    "revert",
]

DEFAULT_SUBJECT_MAX = 72

# Largeur du corps. git n'enveloppe jamais le texte et l'indente de 4 espaces à
# l'affichage : 72 colonnes gardent `git log` lisible dans un terminal de 80.
# Mettre 0 dans la configuration de projet désactive ce contrôle.
DEFAULT_BODY_MAX = 72

GABARIT = """Convention de commit Kodflow :

    <type>(<scope>)[!]: <description à l'impératif>
    <ligne vide>
    <corps en prose, enveloppé à 72 colonnes : le problème, puis pourquoi
    cette solution. Pas le « comment », le diff s'en charge.>
    <ligne vide>
    <trailers, en dernier>

Types autorisés : {types}
Sujet : {maxlen} caractères maximum, à l'impératif, sans point final.
Trailers : Fixes: <sha12> ("<sujet>") pour une régression, Closes #NNN pour
une issue GitLab, Refs: #NNN pour référencer sans fermer.

Exemple :

    fix(x1): rejeter les ActivateTask sans XID au lieu de paniquer

    Depuis la refonte du parseur X1, une requête dépourvue du champ XID
    franchit la validation. Le dispatch déréférence alors un pointeur nul
    et fait tomber l'ADMF, ce qui interrompt les interceptions actives.

    Valider la présence du XID avant le dispatch et répondre par une
    ErrorResponse ETSI : la conformité impose une réponse au demandeur,
    y compris sur requête malformée.

    Fixes: 3f2a1b9c4d5e ("x1: refactorer le parseur de requêtes ETSI")
    Closes #517"""

# --------------------------------------------------------------------------
# Volet A — marqueurs de rédaction par IA. Bloquants.
#
# Chaque motif vise une signature d'outil, jamais un mot du vocabulaire métier.
# Le libellé accompagne le refus pour que la remédiation soit évidente.
# --------------------------------------------------------------------------

MARQUEURS_BLOQUANTS = [
    (
        re.compile(
            r"^[ \t]*co-authored-by:.*<[^>]*("
            r"noreply@anthropic\.com|claude@users\.noreply\.github\.com|"
            r"cursoragent@cursor\.com|copilot@github\.com|noreply@openai\.com|"
            r"\[bot\]@users\.noreply\.github\.com"
            r")",
            re.IGNORECASE | re.MULTILINE,
        ),
        "trailer Co-Authored-By pointant l'adresse d'un assistant de code",
    ),
    (
        re.compile(
            r"^[ \t]*co-authored-by:[ \t]*"
            r"(claude|codex|copilot|cursor|devin|aider|gemini|jules|windsurf|cline)"
            r"([^0-9a-z]|$)",
            re.IGNORECASE | re.MULTILINE,
        ),
        "trailer Co-Authored-By nommant un assistant de code",
    ),
    (
        re.compile(
            r"(generated|created|written|co-authored)[ \t]+(with|by)[ \t]+\[?"
            r"(claude code|claude|codex|cursor|github copilot|copilot|"
            r"gemini cli|devin|aider|windsurf|cline)\]?",
            re.IGNORECASE,
        ),
        "mention « Generated with <outil> »",
    ),
    (
        re.compile(
            r"https?://("
            r"claude\.ai/code|claude\.com/claude-code|cursor\.com|devin\.ai|"
            r"aider\.chat|github\.com/features/copilot)",
            re.IGNORECASE,
        ),
        "lien vers un assistant de code",
    ),
    (
        re.compile(r"^[ \t]*(\U0001F916|\U0001F9BE)", re.MULTILINE),
        "emoji robot en tête de ligne",
    ),
    (
        re.compile(
            r"^[ \t]*(replit-commit-session-id|devin-session(-id)?|"
            r"codex-session(-id)?|claude-session-id|cursor-session|"
            r"x-agent-session|generated-by|ai-assisted)[ \t]*:",
            re.IGNORECASE | re.MULTILINE,
        ),
        "trailer de session d'agent",
    ),
    (
        re.compile(
            r"co-?authored[ \-](by|with)[ \t]+(an?[ \t]+)?"
            r"(ai|a\.i\.|ia|artificial intelligence|llm|assistant ia)"
            r"([^0-9a-zàâçéèêëîïôûùüÿñæœ]|$)",
            re.IGNORECASE,
        ),
        "auto-déclaration de co-rédaction par IA",
    ),
]

# --------------------------------------------------------------------------
# Volet B — tournures caractéristiques d'un message rédigé par une IA.
# Jamais bloquantes : signalement seulement, et seulement à partir de deux
# familles distinctes.
#
# Aucun mot métier isolé n'est un marqueur : « agent » nu, « phase » nue,
# « lot » nu, « orchestration » ne figurent volontairement dans aucun motif.
# --------------------------------------------------------------------------

MARQUEURS_SUSPECTS = [
    (
        "numérotation d'orchestration",
        # Ancré en tête de ligne, majuscule initiale et chiffre obligatoires :
        # « Phase 2 : ... » est capturé, « décalage de phase » ne l'est pas.
        re.compile(
            r"^[ \t]*(Phase|Étape|Etape|Lot|Batch|Passe|Itération|Iteration|"
            r"Step|Vague|Wave|Round)[ \t]*[0-9]+([ \t]*[:/–—-]|[ \t]*$)",
            re.MULTILINE,
        ),
    ),
    (
        "vocabulaire d'agents",
        # Composés uniquement : « agent X1 », « agent SNMP », « user agent SIP »
        # ne sont pas capturés.
        re.compile(
            r"(sous-agents?|sub-?agents?|multi-agents?|agents?[ \t]+(IA|AI)|"
            r"(pipeline|équipe|equipe|essaim|flotte)[ \t]+d.[ \t]*agents|"
            r"agent[ \t]+(Claude|Codex|Cursor)|agent team|swarm)",
            re.IGNORECASE,
        ),
    ),
    (
        "méta-discours sur le processus",
        re.compile(
            r"((comme|tel que)[ \t]+demandé(?![ \t]+(par|dans|au))|as[ \t]+requested|"
            r"ce[ \t]+commit[ \t]+(met[ \t]+en[ \t]+œuvre|implémente|applique)|"
            r"this[ \t]+commit[ \t]+(implements|applies|introduces)[ \t]+the[ \t]+"
            r"(requested|above|discussed)|"
            r"(voir|cf\.?)[ \t]+(l.)?analyse[ \t]+ci-dessus|"
            r"as[ \t]+(discussed|analyzed|described)[ \t]+above)",
            re.IGNORECASE,
        ),
    ),
    (
        "première personne au lieu de l'impératif",
        # Appliqué au sujet seul, où l'impératif est la convention.
        re.compile(
            r"(^|[^0-9a-z])(j.ai[ \t]+(implémenté|ajouté|corrigé|modifié|créé|"
            r"supprimé|refactorisé|remplacé)|i[ \t]+(have[ \t]+)?"
            r"(implemented|added|fixed|updated|created|refactored|removed))",
            re.IGNORECASE,
        ),
    ),
    (
        "sections de rapport",
        re.compile(
            r"^[ \t]*(#{1,4}[ \t]*|\*\*)?(Summary|Résumé|Changes[ \t]made|"
            r"Modifications[ \t]apportées|Test[ \t]plan|Next[ \t]steps|"
            r"Prochaines[ \t]étapes|Rationale)[ \t]*:?[ \t]*(\*\*)?[ \t]*$",
            re.MULTILINE,
        ),
    ),
    (
        "puces en gras répétées",
        re.compile(r"^[ \t]*[-*•][ \t]+\*\*[^*]{2,60}\*\*[ \t]*[:—-]", re.MULTILINE),
    ),
    (
        "tableau markdown",
        re.compile(r"^[ \t]*\|[ \t]*[:\-]{3,}", re.MULTILINE),
    ),
]

# Un seuil pour les motifs qui ne comptent qu'en répétition.
SEUIL_OCCURRENCES = {"puces en gras répétées": 3}

# Sujets exemptés de la convention : messages générés par git lui-même.
SUJET_EXEMPT = re.compile(r"^(Merge |Revert \"|fixup! |squash! |amend! )")


def sortie(payload=None):
    """Émet au plus un objet JSON et termine. Le hook ne bloque jamais par code."""
    if payload:
        json.dump(payload, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    sys.exit(0)


def refuser(raison):
    sortie(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": raison,
            }
        }
    )


def signaler(texte):
    sortie(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": texte,
            }
        }
    )


def normaliser(texte):
    """NFC : « é » saisi en forme décomposée doit matcher les motifs accentués."""
    return unicodedata.normalize("NFC", texte)


def charger_config(cwd):
    """Configuration de projet optionnelle : .claude/commit-guard.json."""
    config = {
        "types": DEFAULT_TYPES,
        "scopes": [],
        "subject_max": DEFAULT_SUBJECT_MAX,
        "body_max": DEFAULT_BODY_MAX,
        "check_convention": True,
        "check_style": True,
    }
    chemin = os.path.join(cwd, ".claude", "commit-guard.json")
    try:
        with open(chemin, encoding="utf-8") as fh:
            config.update(json.load(fh))
    except (OSError, ValueError):
        pass
    return config


def charger_allowlist(cwd):
    """Exemptions de projet : .claude/commit-guard-allow, une regex par ligne."""
    motifs = []
    chemin = os.path.join(cwd, ".claude", "commit-guard-allow")
    try:
        with open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if ligne and not ligne.startswith("#"):
                    try:
                        motifs.append(re.compile(ligne, re.IGNORECASE))
                    except re.error:
                        continue
    except OSError:
        pass
    return motifs


def appliquer_allowlist(texte, motifs):
    """Retire les lignes couvertes par une exemption avant analyse."""
    if not motifs:
        return texte
    gardees = [
        ligne
        for ligne in texte.splitlines()
        if not any(motif.search(ligne) for motif in motifs)
    ]
    return "\n".join(gardees)


def depouiller(texte):
    """Retire ce qui n'est pas de la prose de commit : commentaires, code, citations."""
    texte = re.sub(r"```.*?```", " ", texte, flags=re.DOTALL)
    texte = re.sub(r"`[^`\n]*`", " ", texte)
    lignes = [
        ligne
        for ligne in texte.splitlines()
        if not ligne.lstrip().startswith("#") and not ligne.lstrip().startswith(">")
    ]
    return "\n".join(lignes)


class Commande:
    """Ce qu'on a pu déduire d'une ligne de commande `git commit`."""

    def __init__(self):
        self.est_commit = False
        self.est_push = False
        self.no_verify = False
        self.messages = []
        self.fichiers_message = []
        self.amend = False
        self.no_edit = False
        self.reuse = False  # -C / -c / --fixup / --squash : message repris
        self.reuse_refs = []  # les commits dont le message est repris
        self.parse_ok = True


def analyser_commande(commande):
    """Repère les invocations de git et en extrait les sources de message.

    Le parsing est fait sur les jetons shell, ce qui donne les valeurs exactes
    de -m et -F. En cas d'échec du découpage (heredoc, quoting exotique), on le
    signale : le contrôle de convention est alors abandonné, mais la recherche
    de marqueurs continue sur la commande brute.
    """
    infos = Commande()

    try:
        jetons = shlex.split(commande, comments=False, posix=True)
    except ValueError:
        infos.parse_ok = False
        jetons = commande.split()

    i = 0
    sous_commande = None
    while i < len(jetons):
        jeton = jetons[i]

        if os.path.basename(jeton) == "git":
            sous_commande = None
            j = i + 1
            # Sauter les options globales de git (-c x=y, -C dir, ...).
            while j < len(jetons) and jetons[j].startswith("-"):
                if jetons[j] in ("-c", "-C", "--git-dir", "--work-tree"):
                    j += 1
                j += 1
            if j < len(jetons):
                sous_commande = jetons[j]
                if sous_commande == "commit":
                    infos.est_commit = True
                elif sous_commande == "push":
                    infos.est_push = True
                i = j
        elif sous_commande == "commit":
            if jeton in ("--no-verify", "-n"):
                infos.no_verify = True
            elif jeton == "--amend":
                infos.amend = True
            elif jeton == "--no-edit":
                infos.no_edit = True
            elif jeton in ("-C", "-c", "--reuse-message", "--reedit-message",
                           "--fixup", "--squash"):
                infos.reuse = True
                if i + 1 < len(jetons):
                    infos.reuse_refs.append(jetons[i + 1])
                    i += 1
            elif jeton.startswith(("--reuse-message=", "--reedit-message=",
                                   "--fixup=", "--squash=")):
                infos.reuse = True
                infos.reuse_refs.append(jeton.split("=", 1)[1])
            elif jeton in ("-m", "--message"):
                if i + 1 < len(jetons):
                    infos.messages.append(jetons[i + 1])
                    i += 1
            elif jeton.startswith("--message="):
                infos.messages.append(jeton.split("=", 1)[1])
            elif jeton in ("-F", "--file"):
                if i + 1 < len(jetons):
                    infos.fichiers_message.append(jetons[i + 1])
                    i += 1
            elif jeton.startswith("--file="):
                infos.fichiers_message.append(jeton.split("=", 1)[1])
            elif re.fullmatch(r"-[a-zA-Z]{2,}", jeton):
                # Grappe de options courtes : -am, -anm, ...
                lettres = jeton[1:]
                if "n" in lettres:
                    infos.no_verify = True
                if lettres.endswith("m") and i + 1 < len(jetons):
                    infos.messages.append(jetons[i + 1])
                    i += 1
        elif sous_commande == "push" and jeton in ("--no-verify", "-n"):
            infos.no_verify = True

        i += 1

    return infos


def lire_fichier_message(cwd, chemin):
    try:
        if not os.path.isabs(chemin):
            chemin = os.path.join(cwd, chemin)
        with open(chemin, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def message_commit(cwd, ref="HEAD"):
    """Message d'un commit : le précédent pour --amend, ou celui repris par -C."""
    # `ref` vient de la ligne de commande. Un tiret initial serait lu comme une
    # option de git : on refuse plutôt que de tenter de l'échapper. Le `--`
    # final ferme la liste des options sans introduire de pathspec.
    if ref.startswith("-"):
        return ""
    try:
        resultat = subprocess.run(
            ["git", "log", "-1", "--pretty=%B", ref, "--"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if resultat.returncode == 0:
            return resultat.stdout
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def controler_convention(sujet, corps, config):
    """Renvoie la liste des écarts à la convention Kodflow. Vide si conforme."""
    ecarts = []
    types = config.get("types") or DEFAULT_TYPES
    maxlen = config.get("subject_max") or DEFAULT_SUBJECT_MAX

    entete = re.match(
        r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<desc>.+)$",
        sujet,
    )
    if not entete:
        ecarts.append(
            "le sujet ne suit pas la forme « type(scope): description » "
            "(deux-points puis une espace obligatoires)"
        )
    else:
        if entete.group("type") not in types:
            ecarts.append(
                "type « {} » non autorisé ; types admis : {}".format(
                    entete.group("type"), ", ".join(types)
                )
            )
        scopes = config.get("scopes") or []
        scope = entete.group("scope")
        if scopes and scope and scope not in scopes:
            ecarts.append(
                "scope « {} » non autorisé ; scopes admis : {}".format(
                    scope, ", ".join(scopes)
                )
            )
        if entete.group("desc").endswith("."):
            ecarts.append("le sujet ne doit pas se terminer par un point")

    if len(sujet) > maxlen:
        ecarts.append(
            "sujet de {} caractères, maximum {}".format(len(sujet), maxlen)
        )

    lignes_corps = corps.splitlines()
    if lignes_corps and lignes_corps[0].strip():
        ecarts.append("une ligne vide doit séparer le sujet du corps")

    body_max = config.get("body_max", DEFAULT_BODY_MAX)
    if body_max:
        trop_longues = [
            ligne
            for ligne in lignes_corps
            # Les trailers et les URL ne se coupent pas.
            if len(ligne) > body_max
            and not re.match(r"^[A-Z][A-Za-z-]+: ", ligne)
            and "://" not in ligne
        ]
        if trop_longues:
            ecarts.append(
                "corps non enveloppé à {} colonnes ({} ligne(s) trop longue(s))".format(
                    body_max, len(trop_longues)
                )
            )

    return ecarts


def main():
    try:
        charge = json.load(sys.stdin)
    except (ValueError, OSError):
        sortie()

    if charge.get("tool_name") != "Bash":
        sortie()

    commande = (charge.get("tool_input") or {}).get("command") or ""
    if not commande:
        sortie()

    # Sortie rapide : ce hook s'exécute avant chaque commande Bash.
    if "git" not in commande or not re.search(r"\b(commit|push)\b", commande):
        sortie()

    infos = analyser_commande(commande)
    if not infos.est_commit and not infos.est_push:
        sortie()

    if infos.no_verify:
        refuser(
            "L'option --no-verify contourne les hooks git, qui portent les "
            "contrôles de qualité et de secrets de Kodflow. Relance la commande "
            "sans cette option. Si un hook git est réellement en défaut, "
            "corrige-le ou signale-le, mais ne le désactive pas."
        )

    if not infos.est_commit:
        sortie()

    cwd = charge.get("cwd") or os.getcwd()
    config = charger_config(cwd)

    # Aucune source de message : git ouvrirait un éditeur interactif, que
    # l'outil Bash ne peut pas servir — la commande resterait figée.
    if not infos.messages and not infos.fichiers_message and not infos.reuse:
        if not (infos.amend and infos.no_edit):
            refuser(
                "Cette commande ouvrirait un éditeur interactif, qui ne peut pas "
                "aboutir depuis l'outil Bash : la session resterait bloquée.\n\n"
                "Fournis le message avec -m, ou -F pour un message multi-ligne, "
                "ou --amend --no-edit pour conserver le message existant.\n\n"
                + GABARIT.format(
                    types=", ".join(config.get("types") or DEFAULT_TYPES),
                    maxlen=config.get("subject_max") or DEFAULT_SUBJECT_MAX,
                )
            )
        sortie()

    # Reconstitution du message. Plusieurs -m forment autant de paragraphes,
    # comme le fait git lui-même.
    morceaux = list(infos.messages)
    for chemin in infos.fichiers_message:
        contenu = lire_fichier_message(cwd, chemin)
        if contenu:
            morceaux.append(contenu)
    if infos.amend and not morceaux:
        precedent = message_commit(cwd)
        if precedent:
            morceaux.append(precedent)

    message = normaliser("\n\n".join(morceaux))

    # Un message repris d'un autre commit (-C, --reuse-message, --fixup...)
    # n'apparaît nulle part dans la commande : sans cette lecture, il suffirait
    # de pointer un ancien commit pour réintroduire une mention d'assistant.
    # Il alimente la recherche de marqueurs, mais pas le contrôle de convention :
    # sa forme est celle du commit d'origine, ou générée par git.
    repris = ""
    for ref in infos.reuse_refs:
        contenu = message_commit(cwd, ref)
        if contenu:
            repris += "\n" + normaliser(contenu)

    # Le volet A s'applique aussi à la commande brute : un heredoc que shlex
    # n'a pas su découper y reste visible.
    allowlist = charger_allowlist(cwd)
    haystack = appliquer_allowlist(
        depouiller(message + "\n" + repris + "\n" + normaliser(commande)), allowlist
    )

    for motif, libelle in MARQUEURS_BLOQUANTS:
        if motif.search(haystack):
            refuser(
                "Message de commit refusé : {}.\n\n"
                "Les commits Kodflow ne portent aucune trace de rédaction par un "
                "assistant. Réécris le message sans cette mention.\n\n"
                "Si l'attribution est ajoutée automatiquement, désactive-la dans "
                "settings.json :\n"
                '    "attribution": {{ "commit": "", "pr": "" }}'.format(libelle)
            )

    if not message.strip():
        sortie()

    lignes = message.strip().splitlines()
    sujet = lignes[0].strip()
    corps = "\n".join(lignes[1:])

    if config.get("check_convention", True) and not SUJET_EXEMPT.match(sujet):
        ecarts = controler_convention(sujet, corps, config)
        if ecarts:
            refuser(
                "Message de commit non conforme à la convention Kodflow :\n"
                + "\n".join("  - " + e for e in ecarts)
                + "\n\nSujet proposé : "
                + sujet
                + "\n\n"
                + GABARIT.format(
                    types=", ".join(config.get("types") or DEFAULT_TYPES),
                    maxlen=config.get("subject_max") or DEFAULT_SUBJECT_MAX,
                )
            )

    # Volet B : signalement seulement, à partir de deux familles distinctes.
    if config.get("check_style", True):
        familles = []
        for libelle, motif in MARQUEURS_SUSPECTS:
            cible = sujet if libelle == "première personne au lieu de l'impératif" else haystack
            occurrences = len(motif.findall(cible))
            if occurrences >= SEUIL_OCCURRENCES.get(libelle, 1):
                familles.append(libelle)
        if len(familles) >= 2:
            signaler(
                "Le message de commit présente des tournures caractéristiques "
                "d'une rédaction automatique : "
                + ", ".join(familles)
                + ". Le commit n'est pas bloqué. Un message de commit décrit le "
                "changement et sa raison, pas le déroulement du travail : "
                "supprimer les numéros d'étape, le méta-discours et la mise en "
                "forme de rapport rend l'historique lisible."
            )

    sortie()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:  # fail-open : jamais d'entrave au travail en cours
        sys.exit(0)
