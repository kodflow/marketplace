# TaskCompleted

Se déclenche quand une tâche est marquée terminée.

## Payload

Identique à [`TaskCreated`](../TaskCreated/) : `task_id`, `task_subject`,
`task_description`, `teammate_name`, `team_name` (déprécié).

Pas de `matcher`.

## Décision

`exit 2` **empêche le passage en terminé**, stderr servant de motif. Un JSON
`{"continue": false, "stopReason": "..."}` arrête l'agent.

## Ce qu'on peut y mettre

- **Libération du verrou** posé par `TaskCreated` : faire transiter l'entrée du
  registre de `active` à `completed`. Sans cela, le verrou par chemin ne se
  relâche jamais et bloque toutes les tâches suivantes.
- **Contrôle de complétude** : refuser la clôture d'une tâche dont le livrable
  attendu est absent — tests non lancés, fichier non produit, revue non demandée.
- **Métrique** : durée entre création et clôture, taux de tâches abandonnées.

## Pièges

- **Écriture concurrente sur le registre** : plusieurs agents peuvent clôturer en
  même temps. Verrouiller (`flock`) et réécrire de façon atomique — fichier
  temporaire puis renommage.
- Refuser une clôture met l'agent en difficulté s'il n'a pas les moyens de
  satisfaire la condition : le motif doit dire quoi faire, précisément.
- Ce hook et `TaskCreated` forment un couple : l'un sans l'autre laisse le
  registre incohérent.
