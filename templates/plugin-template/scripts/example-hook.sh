#!/usr/bin/env bash
# Exemple de script de hook.
# Claude Code transmet la charge utile du hook sur stdin, au format JSON.
# Sortie non nulle = le hook signale une erreur a Claude Code.
set -euo pipefail

payload="$(cat)"
echo "hook recu: ${payload:0:200}" >&2
exit 0
