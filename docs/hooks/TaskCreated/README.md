# TaskCreated

Se déclenche à la création d'une tâche. Spécifique au travail multi-agents.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `task_id` | identifiant de la tâche |
| `task_subject` | titre — **`task_subject`, pas `task_title`** |
| `task_description` | description détaillée, **peut être absente** |
| `teammate_name` | agent créateur, **peut être absent** |
| `team_name` | **déprécié**, sera retiré |

Pas de `matcher` sur cet événement.

## Décision

`exit 2` **annule la création de la tâche**, stderr servant de motif. Un JSON
`{"continue": false, "stopReason": "..."}` arrête complètement l'agent.

## Ce qu'on peut y mettre

C'est le seul point de contrôle qui voit une tâche **avant** qu'elle n'existe.
En multi-agents sur un même dépôt, c'est là qu'on évite les collisions :

- **Verrou d'écriture par chemin** : refuser une tâche en écriture dont le
  périmètre recoupe celui d'une tâche active assignée à un autre agent. C'est ce
  qui manque le plus quand plusieurs agents travaillent en parallèle sur le même
  code.
- **Contrat de tâche versionné** : imposer que la description porte les champs
  requis — périmètre, mode d'accès, chemins possédés — et refuser sinon.
- **Idempotence** : rejeter une tâche dont la clé a déjà été enregistrée, pour
  qu'une relance ne duplique pas le travail.
- **Refus d'une tâche sans sujet** ou manifestement hors périmètre.

## Pièges

- **Commencer en mode consultatif.** Un registre de tâches qui refuse trop tôt
  bloque le travail sans que personne ne comprenne pourquoi. Avertir d'abord,
  refuser seulement sur les violations explicites et sûres.
- **Prévoir le ramasse-miettes** du registre : sans purge des entrées mortes, les
  faux conflits s'accumulent et le verrou finit par tout bloquer.
- `task_description` et `teammate_name` peuvent être absents : ne pas supposer
  leur présence.
- `team_name` est déprécié : ne pas construire dessus.
