# SubagentStop

Se déclenche quand un sous-agent s'apprête à rendre son résultat.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `stop_hook_active` | `true` si le sous-agent continue déjà à cause d'un hook |
| `agent_id`, `agent_type` | identité du sous-agent |
| `agent_transcript_path` | transcript propre du sous-agent, dans un dossier `subagents/` |
| `last_assistant_message` | son message final, c'est-à-dire sa valeur de retour |
| `background_tasks`, `session_crons` | **scopés à la session parente**, pas au sous-agent |

`transcript_path` est celui de la session principale ; le transcript du
sous-agent est dans `agent_transcript_path`.

## Décision

Identique à [`Stop`](../Stop/) : `decision: "block"` + `reason` empêche le
sous-agent de conclure et lui donne l'instruction suivante ;
`hookSpecificOutput.additionalContext` produit le même effet en s'affichant comme
un retour de hook plutôt qu'une erreur.

## Ce qu'on peut y mettre

- **Contrôle de complétude du livrable** : un sous-agent de recherche qui rend un
  résultat vide ou sans source peut être renvoyé au travail.
- **Vérification du format de retour** attendu par l'appelant : la réponse finale
  d'un sous-agent est une valeur de retour, pas un message ; un contrôle de forme
  ici évite un aller-retour côté parent.
- **Mesure du coût de délégation** : durée, verbosité, type d'agent — la base
  d'un budget de sous-agents.

## Pièges

- **Garde `stop_hook_active` obligatoire**, même raison que pour `Stop`.
- `additionalContext` alimente le contexte **du sous-agent**, pas de la session
  parente. Pour injecter dans la conversation appelante, passer par un
  [`PostToolUse`](../PostToolUse/) sur l'outil `Agent`.
- Comme pour `Stop`, ne pas émettre `hookSpecificOutput` porteur d'une décision
  avec `hookEventName: "SubagentStop"` : la forme de blocage est `decision` +
  `reason` à la racine.
- Bloquer un sous-agent le fait repartir pour un tour complet : le coût est
  celui d'une relance, pas d'une correction locale.
