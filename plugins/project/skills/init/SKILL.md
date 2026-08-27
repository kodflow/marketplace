---
name: init
description: Initialiser l'outillage Claude Code d'un projet Kodflow — analyser le projet, proposer les plugins et outils pertinents, les installer après validation, écrire la configuration projet qui propage l'outillage au reste de l'équipe. À lancer une fois par projet, ré-exécutable sans risque.
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion, TaskCreate, TaskUpdate
---

# Initialisation de l'outillage d'un projet Kodflow

Cette skill orchestre la mise en place complète de l'outillage Claude Code sur
le projet courant. Elle est **idempotente** : relancée sur un projet déjà
initialisé, elle détecte l'existant, ne refait rien, et ne propose que ce qui
manque.

Principe non négociable : **rien ne s'installe sans sélection explicite de
l'utilisateur** (étape 2). L'analyse propose, l'utilisateur dispose.

## Étape 0 — Créer la liste de tâches, avant tout travail

Crée immédiatement, avec l'outil TaskCreate, les sept tâches suivantes, dans
cet ordre, avec ces libellés exacts — c'est le tableau de bord que suit
l'utilisateur :

1. `init(1/7) : analyser le projet et préparer les suggestions`
2. `init(2/7) : valider la sélection d'outillage avec l'utilisateur`
3. `init(3/7) : enregistrer la marketplace kodflow`
4. `init(4/7) : installer les plugins sélectionnés`
5. `init(5/7) : installer les binaires externes`
6. `init(6/7) : écrire la configuration projet (.claude/)`
7. `init(7/7) : vérifier et faire le bilan`

Ensuite, au fil de l'exécution : passe chaque tâche `in_progress` quand tu
l'entames, `completed` quand elle est finie. Une étape sans objet (déjà faite,
ou rien de sélectionné) est marquée `completed` avec un commentaire d'une ligne
expliquant pourquoi — jamais laissée pendante.

## Étape 1 — Analyser le projet

Uniquement de la lecture. Collecte :

**Nature du projet**
- Langages : `go.mod`, `Cargo.toml`, `package.json`, `pyproject.toml`,
  `CMakeLists.txt`, `Makefile`…
- Marqueurs télécom : fichiers ou références `asn1`/`ASN.1`, interfaces
  `X1`/`X2`/`X3`, mentions 3GPP/ETSI (`TS 33.128`, `TS 103 221`…), SIP,
  Diameter, GTP — via Grep sur le dépôt.
- Forge : remote git (`git remote -v`) — un remote `gitlab.example.com` active les
  suggestions liées à GitLab.
- CI : `.gitlab-ci.yml`, conventions existantes (`CLAUDE.md`,
  `.claude/settings.json`, `.claude/commit-guard.json`).

**État de l'outillage sur le poste**
- Marketplace `kodflow` déjà enregistrée ? (`claude plugin marketplace list`)
- Plugins déjà installés ? (`claude plugin list --json`)
- Binaires : `python3 <installLocation>/tools/binaries.py status --json` si la
  marketplace est déjà enregistrée (sinon `command -v` en première approche,
  et l'état complet sera fait à l'étape 5).
- Accès SSH GitLab : `grep -A3 'gitlab.example.com' ~/.ssh/config` — le port 2222
  doit y être déclaré pour la voie SSH (voir README de la marketplace).

**Catalogue vivant** — ne jamais suggérer depuis une liste codée en dur :
lis le catalogue réel pour connaître les plugins disponibles à ce moment-là.

```bash
claude plugin list --available --json   # champ "available", filtrer sur @kodflow
```

Si la marketplace n'est pas encore enregistrée, ce sera fait à l'étape 3 ;
utilise alors la connaissance des plugins standards comme base de suggestion et
revalide après l'enregistrement.

Construis le tableau de suggestions : pour chaque plugin ou outil, la
**justification tirée de l'analyse** (« go.mod présent → revue Go », « remote
gitlab.example.com → workflow d'issue », « références TS 103 221 → expertise
3GPP »). Correspondances de base — à confronter au catalogue réel :

| Constat | Suggestion |
| ------- | ---------- |
| dépôt git (toujours) | `commit-guard` — convention de commit |
| catalogue (toujours) | `devkit` seulement si l'utilisateur contribue à la marketplace |
| `go.mod` | `go-review-panel`, et `gopls-lsp@claude-plugins-official` + binaire `gopls` |
| remote `gitlab.example.com` | `issue-workflow` |
| marqueurs télécom/3GPP | `3gpp-expert` |
| `rtk` absent et plugin rtk au catalogue | plugin rtk + son binaire |

## Étape 2 — Valider avec l'utilisateur

Une seule interaction AskUserQuestion, deux questions :

1. **Sélection** (multiSelect) : chaque suggestion est une option dont la
   description porte la justification. Ne présélectionne rien mentalement :
   l'absence de réponse vaut refus.
2. **Portée** : `project` (recommandé — écrit dans `.claude/settings.json`
   versionné, propage à l'équipe) ou `user` (poste seul).

Tout ce qui n'est pas sélectionné est définitivement écarté pour cette
exécution. Ne jamais re-proposer en fin de course.

## Étape 3 — Enregistrer ou rafraîchir la marketplace

Si `claude plugin marketplace list` montre déjà `kodflow`, ne pas ré-enregistrer :
rafraîchir le catalogue, c'est le chemin de mise à jour.

```bash
claude plugin marketplace update kodflow
```

Sinon, enregistrer :

- Si `~/.ssh/config` déclare le port 2222 pour `gitlab.example.com` :
  ```bash
  claude plugin marketplace add git@github.com:kodflow/marketplace.git
  ```
- Sinon, HTTPS :
  ```bash
  claude plugin marketplace add https://github.com/kodflow/marketplace.git
  ```
  et signale à l'utilisateur que la voie SSH (auto-update robuste) demande
  d'ajouter au `~/.ssh/config` :
  ```
  Host gitlab.example.com
    Port 2222
    User git
  ```

Ne jamais utiliser une URL `ssh://…:2222/…` : format refusé par Claude Code.

## Étape 4 — Installer ou mettre à jour les plugins sélectionnés

Pour chaque plugin retenu, dans l'ordre du tableau de suggestions :

```bash
claude plugin install <plugin>@kodflow --scope <portée choisie>   # sans effet si déjà installé
claude plugin update <plugin>@kodflow                              # amène au dernier SHA
```

Les deux commandes sont idempotentes : la même séquence couvre la première
installation et la mise à jour. Un échec n'interrompt pas la boucle : consigne
l'erreur, continue, et reporte au bilan. À la fin, préviens que
`/reload-plugins` activera le tout dans la session courante.

**Les suppressions sont automatiques à la mise à jour.** Chaque version d'un
plugin est un instantané complet dans un répertoire de cache dédié
(`cache/kodflow/<plugin>/<sha>/`) : une skill retirée du plugin n'existe
simplement plus dans la nouvelle version. **Ne jamais supprimer de fichiers du
cache à la main** — c'est le mécanisme de version qui gère.

## Étape 5 — Binaires externes : le catalogue officiel, rien d'autre

L'installation d'un plugin n'installe jamais son binaire (choix de sécurité de
Claude Code) — c'est le rôle de cette étape, et elle passe **exclusivement**
par le catalogue de binaires de la marketplace : `tools/binaries.json`, piloté
par `tools/binaries.py`. Chaque entrée y déclare LA source officielle du
binaire ; le moteur refuse toute autre origine et vérifie les sommes de
contrôle des releases GitHub. **Ne jamais improviser une commande
d'installation hors catalogue.**

1. Localiser le clone de la marketplace :
   ```bash
   claude plugin marketplace list --json   # champ installLocation de « kodflow »
   ```
2. État complet — **tous** les binaires du catalogue, pas seulement ceux liés
   aux sélections :
   ```bash
   python3 <installLocation>/tools/binaries.py status
   ```
   Présenter le tableau tel quel : installé / dernière version officielle /
   verdict.
3. Valider avec AskUserQuestion (multiSelect) ce qui doit être installé ou mis
   à jour parmi ce qui n'est pas à jour. Les binaires liés à une sélection de
   l'étape 2 (ex. `gopls` quand `gopls-lsp` est retenu) sont présentés en
   premier avec leur justification ; le reste du catalogue est proposé sans
   insistance. Toujours une option « tout mettre à jour ».
4. Exécuter, uniquement via le moteur :
   ```bash
   python3 <installLocation>/tools/binaries.py update <noms…> --yes
   ```
5. Le moteur sauvegarde tout binaire remplacé en `<nom>.previous` à côté du
   nouveau : le mentionner au bilan, c'est le chemin de retour arrière.
6. Source injoignable (hors ligne, proxy) : le moteur rend « inconnu » —
   consigner, continuer, reporter au bilan.

Ajouter un binaire à l'outillage d'équipe = ajouter une entrée à
`tools/binaries.json` via une MR sur la marketplace, jamais une commande ad hoc
dans un projet.

## Étape 6 — Écrire la configuration projet

C'est l'étape qui **propage l'outillage au reste de l'équipe** : un
`.claude/settings.json` versionné fait que chaque collègue ouvrant le dépôt se
voit proposer l'installation automatiquement.

1. `.claude/settings.json` — fusionner (jamais écraser un fichier existant :
   le lire, compléter, réécrire) :
   ```json
   {
     "extraKnownMarketplaces": {
       "kodflow": {
         "source": {
           "source": "url",
           "url": "git@github.com:kodflow/marketplace.git"
         }
       }
     },
     "enabledPlugins": {
       "<chaque plugin sélectionné>@kodflow": true
     }
   }
   ```
2. Si `commit-guard` est retenu : proposer un `.claude/commit-guard.json`
   avec les `scopes` déduits de l'arborescence (noms des composants/répertoires
   de premier niveau pertinents), et le faire valider avant écriture.
3. Configuration git de traçabilité (si absente) :
   ```bash
   git config core.abbrev 12
   git config pretty.fixes 'Fixes: %h ("%s")'
   ```
4. Vérifier que `.gitignore` couvre `.claude/settings.local.json`.

Cette étape n'a lieu qu'en portée `project`. En portée `user`, la marquer
completed avec la mention « portée user : pas de configuration projet ».

## Étape 7 — Vérifier et faire le bilan

1. `claude plugin list` — confirmer chaque installation.
2. **Cohérence installé/catalogue** : croiser `claude plugin list --json`
   (champ `installed`) avec le catalogue (`available`). Un plugin `@kodflow`
   installé mais absent du catalogue est un **zombie** : il continue de se
   charger mais ne recevra plus jamais de mise à jour. Deux cas :
   - le catalogue porte une entrée `renames` pour lui → la migration est
     automatique au prochain chargement, rien à faire, le mentionner au bilan ;
   - aucune entrée `renames` → le signaler au bilan et proposer
     `claude plugin uninstall <p>@kodflow`. **Proposer, jamais désinstaller
     d'office** — et jamais de suppression manuelle de fichiers.
3. Bilan sous forme de tableau : élément / action (installé, mis à jour, déjà
   à jour, échec, écarté) / détail. **Chaque échec de l'exécution y figure — le
   bilan ne maquille rien.**
4. Rappeler : `/reload-plugins` pour la session courante, et le fait que les
   collègues seront invités à installer à l'ouverture du dépôt si la portée
   `project` a été retenue.
5. S'il reste un défaut bloquant (marketplace inaccessible), le dire
   explicitement avec la remédiation — section Dépannage du README de la
   marketplace.

## Ce que cette skill ne fait jamais

- Installer quoi que ce soit d'écarté ou de non présenté à l'étape 2.
- Écrire un secret ou un jeton dans un fichier versionné.
- Modifier `~/.claude/settings.json` (portée user gérée par
  `claude plugin install --scope user`, pas par édition directe).
- Toucher au `~/.ssh/config` de l'utilisateur : elle fournit le bloc à
  ajouter, l'utilisateur l'applique.
- Committer : les fichiers écrits dans le projet sont laissés en zone de
  travail, leur commit appartient à l'utilisateur.
