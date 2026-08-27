# WorktreeRemove

Se déclenche à la suppression d'un worktree.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `worktree_path` | chemin absolu du worktree — celui qu'avait renvoyé [`WorktreeCreate`](../WorktreeCreate/) |

Pas de `repository_path`. Pas de `matcher`.

## Décision

Aucune. Les échecs ne sont journalisés qu'en mode debug.

## Ce qu'on peut y mettre

- **Suppression effective** du répertoire et `git worktree prune`, quand la
  création a été prise en charge par un hook.
- **Garde-fou avant tout `rm -rf`** — le point le plus important de cette fiche :
  canonicaliser le chemin (`realpath -m`), vérifier qu'il se trouve bien sous un
  répertoire autorisé, refuser les liens symboliques, et ne supprimer qu'ensuite.
  C'est le motif à exiger en revue de tout hook qui supprime quoi que ce soit.
- **Sauvegarde du travail non commité** avant suppression, ou refus de
  supprimer un worktree contenant des modifications.
- **Nettoyage des ressources associées** : conteneurs, volumes, bases de test
  créés pour ce worktree.

## Pièges

- Le hook ne peut pas empêcher la suppression : le contrôle porte sur ce que
  **lui-même** supprime, pas sur la décision de Claude Code.
- Un échec est invisible hors mode debug : journaliser explicitement.
- Ne jamais faire confiance au chemin reçu sans canonicalisation.
