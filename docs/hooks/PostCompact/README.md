# PostCompact

Se déclenche après une compaction, une fois le résumé produit.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `trigger` | `manual` ou `auto` |
| `compact_summary` | le résumé généré par la compaction |

Le `matcher` porte sur `trigger`.

## Décision

Aucune. `exit 2` affiche stderr à l'utilisateur, sans autre effet. Cet événement
**n'injecte pas de contexte** : pour cela, utiliser
[`SessionStart`](../SessionStart/) avec `matcher: "compact"`, qui se déclenche
également après une compaction.

## Ce qu'on peut y mettre

- **Archiver le résumé** à côté de l'instantané écrit par
  [`PreCompact`](../PreCompact/) : le couple « état avant / résumé après » permet
  de constater ce que la compaction a perdu.
- **Mesurer la qualité des compactions** : longueur du résumé, fréquence des
  compactions automatiques par projet. Une session qui compacte toutes les dix
  minutes signale un problème d'hygiène de contexte, pas un problème de modèle.
- **Notifier** l'utilisateur qu'une compaction automatique a eu lieu, ce qui
  explique une éventuelle perte de fil.

## Pièges

- Ne pas chercher à réinjecter le contexte perdu ici : l'événement n'a pas de
  canal d'injection. C'est `SessionStart` / `compact` qui le fait.
- Le résumé peut être long : ne pas le journaliser intégralement sans limite.
