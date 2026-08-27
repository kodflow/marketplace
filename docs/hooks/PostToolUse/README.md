# PostToolUse

Se déclenche **après** l'exécution réussie d'un outil. L'action a déjà eu lieu :
on ne peut plus l'empêcher, seulement réagir.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `tool_name`, `tool_input` | comme [`PreToolUse`](../PreToolUse/) |
| `tool_response` | le résultat de l'outil — **`tool_response`, pas `tool_output`** |
| `tool_use_id` | identifiant de l'appel |
| `duration_ms` | durée d'exécution, hors invites de permission et hooks `PreToolUse` |

Forme de `tool_response` : `{filePath, success}` pour `Write` ;
`{stdout, stderr, interrupted, isImage}` pour `Bash`.

## Décision

| Sortie | Effet |
| ------ | ----- |
| `additionalContext` | texte ajouté à côté du résultat, lu par Claude |
| `decision: "block"` + `reason` | ajoute le motif à côté du résultat ; Claude voit toujours la sortie d'origine |
| `updatedToolOutput` | **remplace** ce que Claude voit du résultat |
| `exit 2` | ne bloque rien, mais montre stderr à Claude |

`updatedToolOutput` ne change que ce que Claude voit — l'outil a déjà tourné.
C'est le point d'interception pour caviarder un résultat entrant. Une valeur qui
ne respecte pas la forme de sortie de l'outil est ignorée silencieusement.

## Ce qu'on peut y mettre

- **Formatage immédiat** après `Write`/`Edit` : rapide et sans état. Réserver
  lint, typage et tests au [`Stop`](../Stop/), qui les groupe.
- **Accumulation des fichiers touchés** dans un fichier de session : c'est ce qui
  permet ensuite de limiter les contrôles lourds aux fichiers réellement
  modifiés, plutôt qu'à un `git diff` pollué par les autres sessions.
- **Journal d'audit assaini** : chemins et longueurs, jamais le contenu ;
  commandes tronquées et caviardées des jetons et mots de passe.
- **Caviardage des résultats entrants** via `updatedToolOutput` : sortie d'une
  commande qui expose un secret, réponse d'un outil MCP tiers.
- **Rappel ciblé** : « ce fichier est généré, éditer la source ».

## Pièges

- **Un seul producteur de JSON par chaîne.** Quand plusieurs hooks `PostToolUse`
  écrivent du JSON, seul le dernier est retenu : un `decision: "block"` peut
  disparaître silencieusement derrière un hook de formatage bavard. Concentrer la
  production de JSON dans un seul hook de la chaîne.
- Un hook synchrone ici est payé à **chaque** édition : le garder sous la seconde,
  ou le passer en `async` s'il ne produit pas de décision.
- `exit 2` ne bloque pas mais fait remonter stderr à Claude — c'est le seul moyen
  de lui signaler un problème depuis cet événement sans passer par le JSON.

## Exemple

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/format.sh\"",
            "timeout": 15,
            "statusMessage": "Formatage..."
          }
        ]
      }
    ]
  }
}
```
