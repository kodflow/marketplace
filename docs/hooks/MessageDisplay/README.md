# MessageDisplay

Se déclenche à l'affichage d'un fragment de réponse de Claude. Permet de
transformer ce qui est **affiché**, sans toucher au contenu réel.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `turn_id` | identifiant du tour |
| `message_id` | identifiant du message assistant, stable sur tous ses fragments — **ce n'est pas l'identifiant `msg_…` de l'API**, il n'est pas corrélable au transcript |
| `index` | index du fragment, à partir de 0 |
| `final` | `true` sur le dernier fragment |
| `delta` | les lignes nouvellement complétées, sauts de ligne compris |

Pas de `matcher`. Timeout par défaut abaissé à **10 s**.

## Décision

Un seul champ : `hookSpecificOutput.displayContent`, qui remplace le texte
affiché.

**Purement cosmétique** : le transcript et ce que voit Claude conservent le texte
d'origine.

## Ce qu'on peut y mettre

- **Caviardage à l'affichage** : masquer un motif sensible qui apparaîtrait à
  l'écran lors d'une démonstration ou d'un partage d'écran. Attention : le
  contenu réel n'est pas modifié pour autant.
- **Simplification typographique** : retirer le gras et les accents graves pour
  un terminal qui les rend mal.
- **Mise en évidence** d'un motif dans la sortie.

## Pièges

- **En interactif, le `delta` du dernier fragment est vide** quand le message se
  termine par un saut de ligne : se fier à `final`, jamais à un `delta` non vide.
- En mode non interactif, un seul appel par message : `index: 0`, `final: true`,
  `delta` contenant le message entier.
- Le hook s'exécute à **chaque fragment** d'affichage : il doit être trivial.
  Tout traitement coûteux ici se voit immédiatement à l'écran.
- Ne pas confondre avec un mécanisme de sécurité : ce qui est masqué à l'écran
  reste présent dans le transcript et dans le contexte.
