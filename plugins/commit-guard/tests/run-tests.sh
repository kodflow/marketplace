#!/usr/bin/env bash
# Suite de non-régression de commit-guard.
#
#   ./tests/run-tests.sh
#
# Chaque cas envoie une charge utile de hook PreToolUse au détecteur et vérifie
# la nature de la réponse : rien (la commande passe), un refus, ou un simple
# avertissement.
#
# Les cas « faux positif » sont les plus importants : ce sont eux qui garantissent
# que le vocabulaire télécom — décalage de phase, traitement par lot, agent X1 —
# ne déclenche jamais le détecteur.
set -u

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
guard="$root/scripts/commit_guard.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

ok=0
ko=0

# cas <attendu: vide|deny|warn> <libellé> <commande git>
cas() {
  local attendu="$1" libelle="$2" commande="$3" cwd="${4:-$tmp}"
  local charge sortie
  charge=$(python3 - "$commande" "$cwd" <<'PY'
import json, sys
print(json.dumps({
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "cwd": sys.argv[2],
    "tool_input": {"command": sys.argv[1]},
}))
PY
)
  sortie=$(printf '%s' "$charge" | python3 "$guard")

  local reel="vide"
  case "$sortie" in
    *'"permissionDecision": "deny"'*) reel="deny" ;;
    *additionalContext*) reel="warn" ;;
  esac

  if [ "$reel" = "$attendu" ]; then
    ok=$((ok + 1))
    printf '  \033[32m✔\033[0m %-58s %s\n' "$libelle" "$attendu"
  else
    ko=$((ko + 1))
    printf '  \033[31m✘\033[0m %-58s attendu=%s reel=%s\n' "$libelle" "$attendu" "$reel"
    [ -n "$sortie" ] && printf '      %s\n' "$(printf '%s' "$sortie" | head -c 200)"
  fi
}

echo "Marqueurs de rédaction par IA — doivent bloquer"
cas deny "trailer Co-Authored-By Claude" \
  'git commit -m "fix(x1): valider le XID" -m "Co-Authored-By: Claude <noreply@anthropic.com>"'
cas deny "trailer Co-Authored-By Cursor" \
  'git commit -m "fix(x1): valider le XID" -m "Co-authored-by: Cursor <cursoragent@cursor.com>"'
cas deny "pied Generated with Claude Code" \
  'git commit -m "feat(li): x" -m "🤖 Generated with Claude Code"'
cas deny "lien vers un assistant" \
  'git commit -m "feat(li): x" -m "https://claude.com/claude-code"'
cas deny "trailer de session d agent" \
  'git commit -m "feat(li): x" -m "Devin-Session-Id: abc123"'

echo
echo "Vocabulaire télécom légitime — ne doit jamais bloquer"
cas vide "décalage de phase" \
  'git commit -m "fix(x2): corriger le décalage de phase sur le lien PDH"'
cas vide "agent X1 (agent nu)" \
  'git commit -m "feat(li): agent X1 conforme ETSI TS 103 221-1"'
cas vide "traitement par lot" \
  'git commit -m "perf(cdr): traitement par lot des CDR"'
cas vide "user agent SIP" \
  'git commit -m "fix(sip): corriger le user agent SIP tronqué"'
cas vide "orchestration de slices" \
  'git commit -m "refactor(mano): simplifier orchestration des slices 5G"'
cas vide "bruit de phase" \
  'git commit -m "fix(rf): compenser le bruit de phase de la PLL"'

echo
echo "Convention de commit"
cas vide "message conforme" \
  'git commit -m "fix(x1): rejeter les ActivateTask sans XID"'
cas vide "changement cassant" \
  'git commit -m "feat(li-core)!: charger la configuration depuis un YAML unique"'
cas deny "sujet sans type" \
  'git commit -m "correction du bug X1"'
cas deny "type non autorisé" \
  'git commit -m "chore(x1): nettoyage"'
cas deny "point final" \
  'git commit -m "fix(x1): valider le XID."'
cas deny "sujet trop long" \
  "git commit -m \"fix(x1): $(printf 'a%.0s' $(seq 1 80))\""
cas vide "merge exempté" \
  'git commit -m "Merge branch feat/x into master"'
cas vide "fixup exempté" \
  'git commit -m "fixup! fix(x1): valider le XID"'

echo
echo "Options git"
cas deny "--no-verify" 'git commit --no-verify -m "fix(x1): x"'
cas deny "grappe -anm (contient n)" 'git commit -anm "fix(x1): x"'
cas vide "grappe -am (sans n)" 'git commit -am "fix(x1): x"'
cas deny "push --no-verify" 'git push --no-verify origin master'
cas deny "mode éditeur (figerait la session)" 'git add -A && git commit'
cas vide "--amend --no-edit" 'git commit --amend --no-edit'

echo
echo "Portée du hook"
cas vide "commande sans git" 'ls -la'
cas vide "git sans commit ni push" 'git status --short'

echo
echo "Style suspect — avertissement, jamais de blocage"
printf 'feat(x2): activer le keep-alive applicatif\n\nPhase 2 : mise en place du timer\n\nRésumé\n' \
  > "$tmp/msg-suspect.txt"
cas warn "numérotation d étapes + section de rapport" \
  "git commit -F $tmp/msg-suspect.txt"
printf 'feat(x2): activer le keep-alive applicatif\n\nPhase 2 du plan de migration.\n' \
  > "$tmp/msg-une-famille.txt"
cas vide "une seule famille suspecte" \
  "git commit -F $tmp/msg-une-famille.txt"

echo
echo "Message repris d un autre commit"
# Sans lecture du message référencé, `git commit -C <commit>` réintroduirait
# n'importe quelle mention : le message n'apparaît nulle part dans la commande.
depot="$tmp/depot"
if git init -q "$depot" 2>/dev/null; then
  (
    cd "$depot" || exit 1
    git config user.email dev@example.com
    git config user.name Test
    # Le poste peut déclarer un core.hooksPath global dont le hook commit-msg
    # refuse précisément le message que ce fixture doit contenir.
    git config core.hooksPath /dev/null
    echo un > a.txt && git add -A
    git commit -q -m "fix(x1): message porteur" \
                  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
    git rev-parse HEAD > "$tmp/sha-pollue"
    echo deux > b.txt && git add -A
    git commit -q -m "feat(x2): message propre"
    git rev-parse HEAD > "$tmp/sha-propre"
    echo trois > c.txt && git add -A
  )
  cas deny "-C sur un commit portant une mention" \
    "git commit -C $(cat "$tmp/sha-pollue")" "$depot"
  cas vide "-C sur un commit propre" \
    "git commit -C $(cat "$tmp/sha-propre")" "$depot"
  cas vide "référence commençant par un tiret, ignorée" \
    "git commit -C --pretty=oops" "$depot"
else
  printf '  \033[33m!\033[0m git indisponible, section ignorée\n'
fi

echo
echo "Robustesse"
cas vide "fichier -F inexistant" "git commit -F $tmp/absent.txt --amend --no-edit"

# Exemption de projet
# Même message que msg-suspect.txt, qui déclenche deux familles et donc un
# avertissement. L'exemption de projet en neutralise une : on repasse sous le
# seuil de deux familles, et le message ne produit plus rien.
mkdir -p "$tmp/projet/.claude"
printf 'Phase [0-9]+ : recette\n' > "$tmp/projet/.claude/commit-guard-allow"
printf 'feat(x2): activer le keep-alive applicatif\n\nPhase 2 : recette\n\nRésumé\n' \
  > "$tmp/msg-exempte.txt"
cas warn "sans exemption : deux familles, avertissement" \
  "git commit -F $tmp/msg-exempte.txt"
cas vide "avec exemption projet : repasse sous le seuil" \
  "git commit -F $tmp/msg-exempte.txt" "$tmp/projet"

mkdir -p "$tmp/desactive/.claude"
printf '{"check_convention": false, "check_style": false}\n' \
  > "$tmp/desactive/.claude/commit-guard.json"
cas vide "contrôles désactivés par configuration" \
  'git commit -m "message totalement libre."' "$tmp/desactive"
cas deny "volet IA actif même contrôles désactivés" \
  'git commit -m "x" -m "Co-Authored-By: Claude <noreply@anthropic.com>"' "$tmp/desactive"

echo
if [ "$ko" -eq 0 ]; then
  printf '\033[32m%d cas, tous conformes\033[0m\n' "$ok"
else
  printf '\033[31m%d échec(s) sur %d cas\033[0m\n' "$ko" "$((ok + ko))"
fi
exit $([ "$ko" -eq 0 ] && echo 0 || echo 1)
