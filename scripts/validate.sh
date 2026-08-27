#!/usr/bin/env bash
# Validation de la marketplace Kodflow.
#
#   ./scripts/validate.sh
#
# 1. contrôles structurels du catalogue (JSON, unicité, kebab-case, sources)
# 2. `claude plugin validate` sur la marketplace et sur chaque plugin, si le
#    binaire `claude` est disponible.
#
# L'avertissement « version: No version specified » est attendu : les plugins de
# cette marketplace sont versionnés par le SHA du commit (voir README.md).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$root/.claude-plugin/marketplace.json"
status=0

fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; status=1; }
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }

echo "Marketplace: $manifest"

[ -f "$manifest" ] || { fail "fichier .claude-plugin/marketplace.json introuvable"; exit 1; }

python3 - "$manifest" "$root" <<'PY' || status=1
import json, re, sys, os

manifest_path, root = sys.argv[1], sys.argv[2]
status = 0

def fail(msg):
    global status
    print(f"  \033[31m✘\033[0m {msg}")
    status = 1

def ok(msg):
    print(f"  \033[32m✔\033[0m {msg}")

try:
    with open(manifest_path, encoding="utf-8") as fh:
        data = json.load(fh)
except json.JSONDecodeError as exc:
    fail(f"JSON invalide: {exc}")
    sys.exit(1)

ok("JSON valide")

for field in ("name", "owner", "plugins"):
    if field not in data:
        fail(f"champ obligatoire manquant: {field}")

kebab = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
name = data.get("name", "")
if not kebab.match(name):
    fail(f"nom de marketplace non kebab-case: {name!r}")

plugins = data.get("plugins", [])
if not plugins:
    fail("aucun plugin declare dans le catalogue")

seen = set()
for i, plugin in enumerate(plugins):
    pname = plugin.get("name")
    prefix = f"plugins[{i}]"
    if not pname:
        fail(f"{prefix}: champ 'name' manquant")
        continue
    if not kebab.match(pname):
        fail(f"{prefix}: nom non kebab-case: {pname!r}")
    if pname in seen:
        fail(f"{prefix}: nom duplique: {pname!r}")
    seen.add(pname)
    if not plugin.get("description"):
        fail(f"{prefix} ({pname}): description manquante")
    if "version" in plugin:
        fail(f"{prefix} ({pname}): champ 'version' interdit (versionnement par SHA de commit)")

    source = plugin.get("source")
    if source is None:
        fail(f"{prefix} ({pname}): champ 'source' manquant")
        continue
    if isinstance(source, str):
        if ".." in source:
            fail(f"{prefix} ({pname}): source hors de la racine: {source}")
            continue
        path = os.path.join(root, source)
        if not os.path.isdir(path):
            fail(f"{prefix} ({pname}): repertoire source introuvable: {source}")
            continue
        pjson = os.path.join(path, ".claude-plugin", "plugin.json")
        if not os.path.isfile(pjson):
            fail(f"{prefix} ({pname}): .claude-plugin/plugin.json manquant dans {source}")
            continue
        try:
            with open(pjson, encoding="utf-8") as fh:
                pdata = json.load(fh)
        except json.JSONDecodeError as exc:
            fail(f"{prefix} ({pname}): plugin.json invalide: {exc}")
            continue
        if pdata.get("name") != pname:
            fail(f"{prefix}: plugin.json declare name={pdata.get('name')!r}, catalogue {pname!r}")
        if "version" in pdata:
            fail(f"{prefix} ({pname}): 'version' interdit dans plugin.json (versionnement par SHA)")
        for d in (".claude-plugin/skills", ".claude-plugin/commands",
                  ".claude-plugin/agents", ".claude-plugin/hooks"):
            if os.path.isdir(os.path.join(path, d)):
                fail(f"{prefix} ({pname}): {d} doit etre a la racine du plugin")

ok(f"{len(plugins)} plugin(s) dans le catalogue")
sys.exit(status)
PY

if command -v claude >/dev/null 2>&1; then
  echo
  echo "claude plugin validate"
  claude plugin validate "$root" || status=1
  for entry in "$root"/plugins/*/ "$root"/templates/*/; do
    [ -f "$entry/.claude-plugin/plugin.json" ] || continue
    claude plugin validate "$entry" || status=1
  done
else
  echo
  echo "  ! binaire 'claude' absent : validation de schema ignoree"
fi

echo
if [ "$status" -eq 0 ]; then
  printf '\033[32mValidation OK\033[0m\n'
else
  printf '\033[31mValidation en echec\033[0m\n'
fi
exit "$status"
