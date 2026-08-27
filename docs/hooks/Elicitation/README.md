# Elicitation

Se déclenche quand un serveur MCP sollicite une saisie de l'utilisateur —
formulaire ou authentification navigateur.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `mcp_server_name` | serveur à l'origine de la demande — **`mcp_server_name`, pas `server_name`** |
| `message` | texte présenté à l'utilisateur |
| `mode` | `form` ou `url` |
| `url` | en mode `url` : adresse d'authentification |
| `requested_schema` | en mode `form` : schéma JSON des champs demandés |
| `elicitation_id` | identifiant, optionnel |

Il n'y a ni `tool_name`, ni `tool_use_id`. Le `matcher` porte sur
`mcp_server_name`.

## Décision

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept",
    "content": { "username": "alice" }
  }
}
```

| Champ | Valeurs |
| ----- | ------- |
| `action` | `accept`, `decline`, `cancel` |
| `content` | valeurs des champs du formulaire, uniquement sur `accept` |

`exit 2` refuse la sollicitation. Sur cet événement, un hook qui sort en 2 voit
son `hookSpecificOutput` **ignoré**. Les champs `systemMessage` et `continue` sont
également jetés.

## Ce qu'on peut y mettre

- **Réponse automatique** aux sollicitations d'un serveur MCP interne, quand la
  valeur est connue de l'environnement — un identifiant de service, un
  environnement cible — ce qui évite d'interrompre une session non surveillée.
- **Refus automatique** des sollicitations d'un serveur non approuvé, ou de toute
  demande d'authentification navigateur en session automatisée.
- **Trace d'audit** des demandes de saisie : quel serveur réclame quoi.

## Pièges

- **Ne jamais injecter de secret** depuis un hook en réponse à un formulaire : la
  valeur transite vers le serveur MCP et se retrouve dans les journaux.
- Répondre automatiquement à la place de l'utilisateur retire un point de
  contrôle : à réserver aux serveurs internes et aux champs anodins.
- Vérifier `mcp_server_name` avant toute réponse automatique.
