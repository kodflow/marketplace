# TeammateIdle

Se déclenche quand un agent coéquipier s'apprête à se mettre en veille, faute de
travail.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `teammate_name` | nom du coéquipier — **`teammate_name`, pas `teammate_id`** |
| `team_name` | **déprécié** |

Il n'existe pas de champ `teammate_type`. Pas de `matcher`.

## Décision

`exit 2` **empêche la mise en veille** : le coéquipier continue de travailler,
avec stderr comme instruction. Un JSON `{"continue": false, "stopReason": "..."}`
l'arrête complètement.

C'est l'un des rares cas où `exit 2` pilote le comportement de l'agent plutôt que
de bloquer un outil.

## Ce qu'on peut y mettre

- **Refuser la veille tant que des tâches assignées restent ouvertes** : un agent
  qui s'endort avec du travail en attente immobilise la chaîne.
- **Réaffectation** : au lieu de laisser un agent inactif, lui donner la tâche
  disponible suivante.
- **Mesure du temps d'inactivité**, pour dimensionner le nombre d'agents.

## Pièges

- **Plafonner les relances.** Si le registre de tâches se désynchronise, un agent
  à qui on refuse indéfiniment la veille ne peut plus jamais s'arrêter. Prévoir
  un compteur, comme le coupe-circuit d'un hook [`Stop`](../Stop/).
- Le motif renvoyé devient l'instruction de l'agent : il doit désigner un travail
  précis, pas seulement constater qu'il en reste.
