#!/usr/bin/env bash
# PostToolUse — reformate le fichier Go qui vient d'etre ecrit.
#
# Le hook recoit le payload de l'evenement sur stdin ; il n'y a pas
# d'interpolation de variables dans `command`, et le matcher ne filtre que sur
# le nom de l'outil : le filtrage par extension se fait donc ici.
#
# Fail-open : toute erreur sort en 0 pour ne jamais bloquer la session.
set -uo pipefail

payload=$(cat)

file=$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((d.get("tool_input") or {}).get("file_path", ""))
' 2>/dev/null)

case "$file" in
  *.go) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

command -v gofmt     >/dev/null 2>&1 && gofmt -w     "$file" >/dev/null 2>&1
command -v goimports >/dev/null 2>&1 && goimports -w "$file" >/dev/null 2>&1

exit 0
