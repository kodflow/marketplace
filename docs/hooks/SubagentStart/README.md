# SubagentStart

Se déclenche au démarrage d'un sous-agent, avant son premier tour.

**C'est le hook le plus sous-utilisé.** Un sous-agent n'hérite pas du contexte de
son parent : il ne connaît ni les conventions de l'équipe, ni la branche, ni les
règles du projet, sauf si on les lui donne ici.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `agent_id` | identifiant du sous-agent |
| `agent_type` | `general-purpose`, `Explore`, `Plan`, un nom personnalisé, ou `<plugin>:<agent>` pour un agent de plugin |

Pour un sous-agent personnalisé, `agent_type` est le champ `name` du frontmatter,
pas le nom de fichier. Le `matcher` porte sur ce champ.

## Décision

Aucun blocage. Uniquement `hookSpecificOutput.additionalContext`, ajouté au
contexte du sous-agent avant son premier tour.

## Ce qu'on peut y mettre

- **Les conventions d'équipe non négociables** : format de commit, interdiction
  de committer sur la branche par défaut, outils à privilégier. Sans cela, un
  sous-agent qui rédige un commit ignore la convention que le parent respecte.
- **L'état du travail en cours** : branche, ticket, périmètre de fichiers assigné.
- **Des consignes différenciées par type d'agent**, via le matcher : un agent de
  revue et un agent d'exploration n'ont pas besoin des mêmes règles.
- **Journalisation** du type et du volume des délégations, pour mesurer le coût
  réel du travail en sous-agents.

## Pièges

- **Ne pas mettre ce hook en `async`** s'il produit du contexte : un hook
  asynchrone ne peut plus rien injecter à temps, l'agent a déjà démarré.
- Le contexte est payé par **chaque** sous-agent lancé : rester bref.
- `exit 2` ne bloque pas ici ; stderr s'affiche comme une erreur de hook dans le
  transcript **du sous-agent**, pas dans la conversation parente.

## Exemple

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/conventions.sh\"", "timeout": 5 }
        ]
      }
    ]
  }
}
```

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Conventions Kodflow : les messages de commit suivent docs/commit-format.md et ne portent aucune mention d'assistant. La branche par défaut ne reçoit pas de commit direct."
  }
}
```
