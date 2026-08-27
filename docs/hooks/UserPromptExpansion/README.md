# UserPromptExpansion

Se déclenche quand une commande slash ou un prompt MCP est développé en son
contenu réel, avant que Claude ne le traite.

**Il couvre un angle mort de [`PreToolUse`](../PreToolUse/)** : quand
l'utilisateur tape `/ma-skill` directement, aucun outil n'est appelé, donc aucun
hook `PreToolUse` ne se déclenche. C'est ici, et seulement ici, qu'on peut
intercepter ce chemin.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `expansion_type` | `slash_command` (skill ou commande) ou `mcp_prompt` |
| `command_name` | nom de la commande invoquée |
| `command_args` | arguments passés |
| `command_source` | provenance (`plugin`, …) |
| `prompt` | la chaîne originale, par exemple `/ma-skill arg1 arg2` |

Le `matcher` porte sur `command_name`.

## Décision

| Sortie | Effet |
| ------ | ----- |
| `decision: "block"` + `reason` | empêche l'expansion |
| `additionalContext` | contexte ajouté à côté du prompt développé |
| stdout brut | également ajouté comme contexte — un des trois seuls événements dans ce cas |

## Ce qu'on peut y mettre

- **Contexte spécifique à une commande** : injecter l'état pertinent seulement
  quand la skill concernée est invoquée, plutôt que de le payer à chaque tour.
  Une skill de déploiement peut ainsi recevoir la version en production sans que
  toutes les autres sessions la portent.
- **Restreindre une commande sensible** : refuser l'expansion d'une skill de
  déploiement hors des conditions autorisées.
- **Bannière ou avertissement** à l'entrée d'un outil à effet de bord.
- **Mesure d'usage des skills** : quelles commandes sont réellement utilisées,
  avec quels arguments — la base pour décider ce qui mérite d'être maintenu dans
  la marketplace.

## Pièges

- Le matcher porte sur le nom de commande : pour une skill de plugin, c'est le
  nom court (`commit`), pas l'identifiant préfixé.
- Bloquer une expansion est visible pour l'utilisateur qui vient de taper la
  commande : le motif doit être explicite et actionnable.
