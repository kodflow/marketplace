#!/usr/bin/env bash
# Shim d'entrée du hook PreToolUse de commit-guard.
#
# Rôle : localiser un Python 3 utilisable et lui passer la charge utile du hook.
# Toute anomalie de l'environnement se solde par un exit 0 silencieux : un
# garde-fou cassé ne doit jamais empêcher de travailler (fail-open).
#
# Ce script ne décide rien ; toute la logique est dans commit_guard.py.
set -u

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
guard="$here/commit_guard.py"

# Les messages de commit sont en français : sans locale UTF-8, les regex
# accentuées et les emoji ne se comparent pas correctement.
export PYTHONUTF8=1
if [ -z "${LC_ALL:-}" ]; then
  export LC_ALL=C.UTF-8
fi

for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$py" "$guard"
  fi
done

# Aucun Python 3.8+ : on laisse passer sans bruit.
exit 0
