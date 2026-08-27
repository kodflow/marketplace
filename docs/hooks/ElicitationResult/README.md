# ElicitationResult

Se déclenche après qu'une sollicitation MCP a reçu une réponse, avant que
celle-ci ne soit transmise au serveur.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `mcp_server_name` | serveur destinataire |
| `action` | ce que l'utilisateur a répondu : `accept`, `decline`, `cancel` |
| `content` | valeurs saisies, optionnel |
| `mode` | `form` ou `url` |
| `elicitation_id` | identifiant, optionnel |

Le `matcher` porte sur `mcp_server_name`.

## Décision

```json
{
  "hookSpecificOutput": {
    "hookEventName": "ElicitationResult",
    "action": "decline",
    "content": {}
  }
}
```

`action` **remplace** la réponse de l'utilisateur, et `content` remplace les
valeurs saisies. `exit 2` bloque la réponse, qui devient un refus — mais sur
`exit 2` le `hookSpecificOutput` du hook est **ignoré**, et stderr n'est affiché
nulle part. Il faut donc choisir : soit sortir en 2, soit émettre du JSON, jamais
les deux. `systemMessage` et `continue` sont jetés.

C'est donc un point d'interception sur ce qui part vers le serveur MCP.

## Ce qu'on peut y mettre

- **Validation avant transmission** : refuser une saisie qui ne respecte pas le
  format attendu, plutôt que de laisser le serveur échouer.
- **Normalisation** des valeurs saisies : casse, espaces, préfixes.
- **Garde-fou de fuite** : détecter qu'une valeur ressemblant à un secret
  interne s'apprête à partir vers un serveur MCP externe, et transformer la
  réponse en refus.
- **Trace d'audit** : qui a répondu quoi, à quel serveur.

## Pièges

- **Ne pas journaliser `content` en clair** : c'est précisément là que se
  trouvent les identifiants saisis.
- Remplacer la réponse d'un utilisateur sans qu'il le sache est déroutant :
  réserver aux cas de sécurité, et le signaler.
