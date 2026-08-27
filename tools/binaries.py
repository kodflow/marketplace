#!/usr/bin/env python3
"""Moteur du catalogue de binaires Kodflow — tools/binaries.json.

    binaries.py status [--json]        état de chaque binaire : installé / dernière / verdict
    binaries.py install <nom>|--all [--yes]
    binaries.py update  <nom>|--all [--yes]

Règles non négociables :
  - un binaire ne s'installe QUE depuis la source officielle déclarée dans le
    catalogue : releases GitHub du dépôt déclaré, ou proxy Go officiel via
    `go install`. Les redirections HTTP sont contraintes à HTTPS et aux hôtes
    GitHub ; toute sortie de ce périmètre est un refus.
  - quand la release publie un fichier de sommes, la vérification est
    fail-closed : asset absent du fichier, format illisible ou écart de somme,
    l'installation est refusée.
  - jamais de sudo ; le moteur n'écrit QUE dans ~/.local/bin (ou GOPATH/GOBIN
    pour la chaîne Go). Un binaire homonyme actif ailleurs dans le PATH n'est
    jamais touché : il est signalé.
  - le binaire remplacé est sauvegardé en <nom>.previous à côté du nouveau ;
    la bascule est atomique (os.replace sur le même système de fichiers).
  - une panne réseau donne un état ou un échec explicite, jamais un traceback.

Codes de sortie : 0 rien à faire · 1 échec réel · 2 usage · 3 actions
possibles (status) · 4 source injoignable, rien de tenté.

`install` et `update` sont le même geste (le catalogue ne connaît que la
dernière version officielle) ; les deux verbes existent pour la lisibilité.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request

CATALOGUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binaries.json")
DEST = os.path.expanduser("~/.local/bin")
VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+)")
TAG_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GZIP_MAGIC = b"\x1f\x8b"

GITHUB_API = "https://api.github.com"
GITHUB_DL = "https://github.com"
HOTES_AUTORISES = {
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}

# Marqueurs d'état, distincts de « source injoignable »
GO_ABSENT = "GO_ABSENT"
RATE_LIMIT = "RATE_LIMIT"


class RedirectionContrainte(urllib.request.HTTPRedirectHandler):
    """Refuse toute redirection hors HTTPS ou hors des hôtes GitHub connus."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urlparse
        p = urlparse(newurl)
        if p.scheme != "https" or (
            p.hostname not in HOTES_AUTORISES
            and not (p.hostname or "").endswith(".githubusercontent.com")
        ):
            raise urllib.error.URLError(
                f"redirection refusée hors du périmètre officiel : {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(RedirectionContrainte())


def _entetes():
    h = {"User-Agent": "kodflow-binaries-catalogue"}
    jeton = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if jeton:
        h["Authorization"] = f"Bearer {jeton}"
    return h


def http_json(url):
    req = urllib.request.Request(url, headers=_entetes())
    with _OPENER.open(req, timeout=15) as resp:
        return json.load(resp)


def http_download(url, dest_path):
    req = urllib.request.Request(url, headers=_entetes())
    with _OPENER.open(req, timeout=300) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out)


def go_env(cle):
    out = subprocess.run(["go", "env", cle], capture_output=True, text=True,
                         timeout=30)
    return (out.stdout or "").strip()


def go_isole(cmd, timeout):
    """Commande go isolée du module courant : cwd neutre, GOFLAGS/GOWORK neutralisés."""
    env = {**os.environ, "GOFLAGS": "", "GOWORK": "off"}
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          cwd=tempfile.gettempdir(), env=env)


def plateforme():
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "arm64": "aarch64"}.get(machine, machine)
    return f"{machine}-{platform.system().lower()}"


def version_installee(entry):
    """Version du binaire présent : None absent, '?' illisible, sinon x.y.z."""
    cmd = entry["version_cmd"]
    if not shutil.which(cmd[0]):
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        m = VERSION_RE.search((out.stdout or "") + (out.stderr or ""))
        return m.group(1) if m else "?"
    except (OSError, subprocess.SubprocessError):
        return "?"


_RELEASES = {}  # repo -> data : un seul appel API par dépôt et par exécution


def release_github(repo):
    if repo not in _RELEASES:
        _RELEASES[repo] = http_json(f"{GITHUB_API}/repos/{repo}/releases/latest")
    return _RELEASES[repo]


def version_derniere(entry):
    """(version, marqueur) : version x.y.z ou None ; marqueur d'état éventuel."""
    latest = entry["latest"]
    try:
        if latest["kind"] == "github-release":
            data = release_github(latest["repo"])
            m = VERSION_RE.search(data.get("tag_name") or "")
            return (m.group(1) if m else None), None
        if latest["kind"] == "go-module":
            if not shutil.which("go"):
                return None, GO_ABSENT
            out = go_isole(["go", "list", "-m", f"{latest['module']}@latest"], 60)
            m = VERSION_RE.search(out.stdout or "")
            return (m.group(1) if m else None), None
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            return None, RATE_LIMIT
        return None, None
    except Exception:
        return None, None
    return None, None


def verdict(installee, derniere, marqueur):
    if marqueur == GO_ABSENT:
        return "chaîne Go absente du poste"
    if marqueur == RATE_LIMIT:
        return "rate-limit GitHub (définir GITHUB_TOKEN, ou réessayer plus tard)"
    if derniere is None:
        return "inconnu (source injoignable)"
    if installee is None:
        return "absent"
    if installee == "?":
        return "version installée illisible (mise à jour en la nommant explicitement)"
    if installee == derniere:
        return "à jour"
    return f"mise à jour disponible ({installee} → {derniere})"


def sha256_fichier(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 16), b""):
            h.update(bloc)
    return h.hexdigest()


def somme_attendue(checksums_path, asset_name):
    """Somme sha256 déclarée pour l'asset — formats GNU et BSD. None si absente."""
    bsd = re.compile(r"^\s*SHA-?256\s*\(([^)]+)\)\s*=\s*([0-9a-fA-F]{64})\s*$")
    with open(checksums_path, encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            m = bsd.match(ligne)
            if m and os.path.basename(m.group(1)) == asset_name:
                return m.group(2).lower()
            morceaux = ligne.split()
            if len(morceaux) >= 2:
                nom = os.path.basename(morceaux[-1].lstrip("*"))
                if nom == asset_name and SHA256_RE.match(morceaux[0].lower()):
                    return morceaux[0].lower()
    return None


def basculer_atomiquement(extrait, bin_name):
    """Installe extrait comme DEST/bin_name : .previous puis os.replace (même fs)."""
    os.makedirs(DEST, exist_ok=True)
    os.chmod(DEST, 0o755)  # le mode de makedirs est masqué par l'umask
    cible = os.path.join(DEST, bin_name)
    if os.path.islink(cible) or os.path.islink(cible + ".previous"):
        return None, f"{cible} ou son .previous est un lien symbolique : refus"

    # Étape intermédiaire dans DEST : os.replace n'est atomique que sur le même fs.
    etape = os.path.join(DEST, f".{bin_name}.new")
    shutil.copy2(extrait, etape)
    os.chmod(etape, 0o755)
    if os.path.exists(cible):
        shutil.copy2(cible, cible + ".previous")
    os.replace(etape, cible)
    return cible, None


def installer_github_release(entry):
    spec = entry["install"]
    plat = plateforme()
    asset = spec["assets"].get(plat)
    if not asset:
        return f"plateforme {plat} non couverte par le catalogue"

    data = release_github(spec["repo"])
    tag = data.get("tag_name") or ""
    if not TAG_RE.match(tag):
        return f"tag de release suspect ({tag!r}) : refus"

    base = f"{GITHUB_DL}/{spec['repo']}/releases/download/{tag}"
    bin_name = spec["bin_name"]

    with tempfile.TemporaryDirectory() as tmp:
        archive = os.path.join(tmp, asset)
        http_download(f"{base}/{asset}", archive)

        with open(archive, "rb") as fh:
            if fh.read(2) != GZIP_MAGIC:
                return "le téléchargement n'est pas une archive gzip (proxy captif ?) : refus"

        checks = spec.get("checksums_asset")
        if checks:
            # Fail-closed : sommes annoncées par le catalogue = sommes exigées.
            checks_path = os.path.join(tmp, checks)
            try:
                http_download(f"{base}/{checks}", checks_path)
            except Exception:
                return f"{checks} introuvable dans la release : installation refusée"
            attendu = somme_attendue(checks_path, asset)
            if attendu is None:
                return (f"{asset} absent de {checks} (ou format illisible) : "
                        "installation refusée")
            if sha256_fichier(archive) != attendu:
                return "SOMME DE CONTRÔLE INVALIDE : installation refusée"

        extrait = os.path.join(tmp, bin_name)
        with tarfile.open(archive, "r:gz") as tar:
            membre = next(
                (m for m in tar.getmembers()
                 if m.isfile() and os.path.basename(m.name) == bin_name),
                None,
            )
            if membre is None:
                return f"binaire {bin_name} absent de l'archive"
            with tar.extractfile(membre) as src, open(extrait, "wb") as out:
                shutil.copyfileobj(src, out)

        cible, err = basculer_atomiquement(extrait, bin_name)
        if err:
            return err

    # Jamais d'écriture hors de DEST : un homonyme actif ailleurs est signalé.
    actif = shutil.which(bin_name)
    if actif and os.path.realpath(actif) != os.path.realpath(cible):
        print(f"  ! {actif} précède {cible} dans le PATH et le masquera — "
              "le retirer ou réordonner le PATH", file=sys.stderr)
    elif not actif:
        return f"installé dans {cible}, qui n'est pas dans le PATH"
    return None


def installer_go(entry):
    if not shutil.which("go"):
        return "la chaîne Go n'est pas installée sur ce poste"
    pkg = entry["install"]["package"]
    out = go_isole(["go", "install", f"{pkg}@latest"], 600)
    if out.returncode != 0:
        # La fin de stderr porte l'erreur réelle ; le début n'est que la
        # progression des téléchargements.
        return (out.stderr or "échec de go install").strip()[-400:]
    bin_name = entry["install"].get("bin_name", entry["name"])
    if not shutil.which(bin_name):
        gobin = go_env("GOBIN") or os.path.join(go_env("GOPATH"), "bin")
        return f"installé dans {gobin}, qui n'est pas dans le PATH"
    return None


def installer(entry):
    kind = entry["install"]["kind"]
    if kind == "github-release-binary":
        return installer_github_release(entry)
    if kind == "go-install":
        return installer_go(entry)
    return f"type d'installation inconnu : {kind}"


def charger():
    with open(CATALOGUE, encoding="utf-8") as fh:
        return json.load(fh)["binaries"]


def cmd_status(args):
    lignes = []
    for entry in charger():
        inst = version_installee(entry)
        der, marq = version_derniere(entry)
        lignes.append({
            "name": entry["name"],
            "description": entry["description"],
            "official_source": entry["official_source"],
            "installed": inst,
            "latest": der,
            "verdict": verdict(inst, der, marq),
        })
    if args.json:
        json.dump(lignes, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        larg = max(len(l["name"]) for l in lignes) + 2
        for l in lignes:
            print(f"{l['name']:<{larg}} installé: {l['installed'] or '—':<10} "
                  f"dernière: {l['latest'] or '?':<10} {l['verdict']}")
    if any(l["latest"] is None for l in lignes):
        return 4
    if any(l["verdict"] != "à jour" for l in lignes):
        return 3
    return 0


def confirmer(question):
    """input() traité en refus sur stdin fermé ou interruption."""
    if not sys.stdin.isatty():
        print("stdin non interactif : ajouter --yes pour confirmer", file=sys.stderr)
        return False
    try:
        return input(question).strip().lower() in ("o", "oui", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def cmd_install(args):
    entries = charger()
    if not args.all:
        entries = [e for e in entries if e["name"] in args.names]
        manquants = set(args.names) - {e["name"] for e in entries}
        if manquants:
            print(f"inconnu(s) au catalogue : {', '.join(sorted(manquants))}",
                  file=sys.stderr)
            return 2
    rc = 0
    injoignables = 0
    for entry in entries:
        inst = version_installee(entry)
        der, marq = version_derniere(entry)
        etat = verdict(inst, der, marq)
        if etat == "à jour":
            print(f"✔ {entry['name']} déjà à jour ({inst})")
            continue
        if der is None:
            print(f"! {entry['name']} : {etat}, rien de tenté")
            injoignables += 1
            continue
        if inst == "?" and args.all:
            # Version illisible (build local ?) : ne jamais écraser via --all.
            print(f"– {entry['name']} : version illisible, ignoré par --all "
                  "(mettre à jour en le nommant explicitement)")
            continue
        if not args.yes and not confirmer(
                f"{entry['name']} : {etat} — installer depuis "
                f"{entry['official_source']} ? [o/N] "):
            print(f"– {entry['name']} ignoré")
            continue
        print(f"… {entry['name']} ← {entry['official_source']}")
        try:
            err = installer(entry)
        except (urllib.error.URLError, OSError, subprocess.SubprocessError,
                tarfile.TarError, EOFError) as exc:
            err = f"{type(exc).__name__}: {exc}"
        if err:
            print(f"✘ {entry['name']} : {err}", file=sys.stderr)
            rc = 1
            continue
        obtenu = version_installee(entry)
        if obtenu != der:
            # Cas typique : tag GitHub publié, proxy Go encore en retard.
            print(f"! {entry['name']} : {obtenu} installé mais {der} attendu "
                  "(miroir en retard ?)", file=sys.stderr)
            rc = rc or 1
        else:
            print(f"✔ {entry['name']} {obtenu} installé")
    if rc == 0 and injoignables:
        return 4
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="état installé/dernière de chaque binaire")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    for verbe in ("install", "update"):
        p = sub.add_parser(verbe, help="installer/mettre à jour depuis la source officielle")
        p.add_argument("names", nargs="*", metavar="nom")
        p.add_argument("--all", action="store_true", help="tout le catalogue")
        p.add_argument("--yes", "-y", action="store_true", help="sans confirmation")
        p.set_defaults(func=cmd_install)

    args = ap.parse_args()
    if args.cmd in ("install", "update") and not args.all and not args.names:
        ap.error("préciser un nom de binaire ou --all")
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
