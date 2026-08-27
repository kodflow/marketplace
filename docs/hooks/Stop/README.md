# Stop

Se déclenche quand Claude s'apprête à rendre la main. C'est l'endroit naturel du
contrôle qualité groupé : tout le travail de la session est fait, rien n'est
encore considéré comme terminé.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `stop_hook_active` | `true` si Claude continue **déjà** à cause d'un hook Stop — à tester impérativement |
| `last_assistant_message` | la réponse finale de Claude |
| `background_tasks` | tâches de fond en vol (`id`, `type`, `status`, `description`, `command`…) |
| `session_crons` | réveils programmés (`id`, `schedule`, `recurring`, `prompt`) |

`last_assistant_message` est à préférer au transcript : le fichier est écrit de
façon asynchrone et peut ne pas contenir le dernier message au moment du Stop.

`background_tasks` et `session_crons` permettent de distinguer « la session est
finie » de « la session attend qu'un travail de fond la réveille ».

## Décision

| Sortie | Effet |
| ------ | ----- |
| `decision: "block"` + `reason` | empêche l'arrêt ; `reason` devient l'instruction suivante de Claude |
| `hookSpecificOutput.additionalContext` | même effet de continuation, mais affiché comme un retour de hook et non comme une erreur |
| `exit 2` | bloque, stderr servant de motif |

**Ne jamais émettre `hookSpecificOutput` avec `hookEventName: "Stop"` et d'autres
champs de décision** : `Stop` n'appartient pas à l'union qui valide ce bloc, et
une sortie invalide est rejetée en silence. La forme correcte pour bloquer est
`decision` + `reason` à la racine.

## Ce qu'on peut y mettre

- **Lint, typage et tests limités aux fichiers réellement édités** pendant la
  session — liste accumulée par un hook [`PostToolUse`](../PostToolUse/). Ne
  jamais retomber sur `git diff`, qui mélange le travail des autres sessions.
- **Barrière de conformité** : vérifier qu'une modification d'interface ETSI
  s'accompagne du test de conformité correspondant.
- **Résumé de session** sur stderr : nombre d'opérations, erreurs, outils les
  plus utilisés.
- **Rappel des tâches ouvertes** avant de rendre la main.

## Pièges

- **Coupe-circuit obligatoire.** Un hook Stop qui bloque relance Claude, qui
  re-déclenche le hook : sans compteur, la boucle est infinie. Claude Code force
  la fin après 8 continuations consécutives, mais c'est un filet, pas un
  mécanisme sur lequel s'appuyer. Compteur péremptible, remis à zéro par
  [`UserPromptSubmit`](../UserPromptSubmit/).
- **Tester `stop_hook_active`** en tête de script.
- **Sonder avant tout appel réseau à long timeout.** Un service de qualité
  injoignable et un timeout de 30 s, c'est 30 s d'attente à chaque arrêt : un
  `curl --connect-timeout 1` préalable évite d'accumuler des heures d'attente
  morte sur un mois.
- Distinguer barrière de validation et auto-correction : renvoyer les résultats
  en `additionalContext` fait travailler Claude ; un `systemMessage` ne parle
  qu'à l'utilisateur.

## Exemple

```bash
#!/usr/bin/env bash
set -u
charge="$(cat)"

# Sans cette garde, un blocage relance Claude qui re-déclenche ce hook.
if [ "$(jq -r '.stop_hook_active // false' <<<"$charge")" = "true" ]; then
  exit 0
fi

session="$(jq -r '.session_id' <<<"$charge")"
compteur="${TMPDIR:-/tmp}/.stop-$session"
n=$(( $(cat "$compteur" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$compteur"
[ "$n" -ge 3 ] && exit 0   # coupe-circuit

# ... contrôles sur les fichiers édités pendant la session ...

jq -n --arg r "Les tests du paquet modifié échouent. Corrige-les avant de conclure." \
  '{decision: "block", reason: $r}'
```
