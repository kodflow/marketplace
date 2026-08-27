# Notification

Se déclenche quand Claude Code émet une notification à l'utilisateur.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `message` | texte de la notification |
| `title` | titre, optionnel |
| `notification_type` | type — c'est ce sur quoi porte le `matcher` |

Valeurs de `notification_type` : `permission_prompt`, `idle_prompt`,
`auth_success`, `elicitation_dialog`, `elicitation_url_dialog`,
`elicitation_complete`, `elicitation_response`, `agent_needs_input`,
`agent_completed`.

## Décision

Aucune. Code de sortie et stderr sont ignorés, et `systemMessage` comme
`continue` sont jetés.

Le seul champ qui produise encore un effet est `terminalSequence`, qui demande à Claude Code d'émettre une
séquence d'échappement terminal à votre place : notification de bureau, titre de
fenêtre, sonnerie. Restreint aux OSC `0`, `1`, `2`, `9`, `99`, `777` et au BEL.
C'est le mécanisme prévu, `/dev/tty` étant inaccessible aux hooks.

## Ce qu'on peut y mettre

- **Router vers le canal réel de l'équipe** — Slack, webhook interne — plutôt que
  la sonnerie du terminal, en filtrant sur `notification_type` pour ne relayer
  que ce qui demande une action : `permission_prompt`, `agent_needs_input`.
- **Notification de bureau** via `terminalSequence` quand une session longue
  attend une réponse.
- **Mesure du temps d'attente** : combien de fois par jour une session reste
  bloquée sur une demande de permission, et sur quelles commandes.

## Pièges

- `terminalSequence` est **ignoré en mode `-p`** et dans l'Agent SDK.
- Ne pas relayer tous les types : `idle_prompt` est fréquent et sans intérêt pour
  un canal d'équipe.
- Un webhook synchrone ralentit la session : passer le hook en `async`, puisqu'il
  n'a aucune décision à rendre.

## Exemple

```bash
#!/usr/bin/env bash
charge="$(cat)"
type="$(jq -r '.notification_type // ""' <<<"$charge")"
case "$type" in
  permission_prompt|agent_needs_input) ;;
  *) exit 0 ;;
esac
titre="Claude Code"
corps="$(jq -r '.message // "Attente d une réponse"' <<<"$charge")"
seq="$(printf '\033]777;notify;%s;%s\007' "$titre" "$corps")"
jq -nc --arg s "$seq" '{terminalSequence: $s}'
```
