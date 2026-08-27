# PermissionRequest

Se déclenche quand Claude Code s'apprête à demander une autorisation à
l'utilisateur. Permet de trancher à sa place.

Se déclenche **aussi** quand Claude Code refuserait automatiquement un appel
faute de pouvoir demander — cas d'un sous-agent en mode `-p`. Dans cette
situation, si aucun hook ne décide, l'appel est refusé : un hook est le seul
moyen d'autoriser une action dans un contexte non interactif.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `tool_name`, `tool_input` | comme [`PreToolUse`](../PreToolUse/), mais **sans `tool_use_id`** |
| `permission_suggestions` | tableau des options « toujours autoriser » que verrait l'utilisateur |

Chaque entrée de `permission_suggestions` a la forme des entrées de sortie
`updatedPermissions` : un `type` (`addRules`, `replaceRules`, `removeRules`,
`setMode`, `addDirectories`, `removeDirectories`) et un `destination`
(`session`, `localSettings`, `projectSettings`, `userSettings`).

Un hook peut renvoyer telle quelle une suggestion reçue : c'est l'équivalent de
l'utilisateur qui sélectionne cette option.

## Décision

Tout passe par l'objet `decision` **à l'intérieur de** `hookSpecificOutput` :

| Champ | Effet |
| ----- | ----- |
| `behavior: "allow"` | accorde l'autorisation |
| `behavior: "deny"` | la refuse |
| `updatedInput` | sur `allow` uniquement : modifie les arguments, réévalués ensuite contre les règles de refus |
| `updatedPermissions` | sur `allow` uniquement : applique des règles durables |
| `message` | sur `deny` uniquement : explique à Claude |
| `interrupt` | sur `deny` uniquement : arrête Claude |

**`exit 2` n'est pas honoré sur cet événement** et son stderr est jeté : seul
l'objet `decision` décide. Un `allow` ne surpasse pas une règle de refus.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": { "behavior": "allow" }
  }
}
```

## Ce qu'on peut y mettre

- **Décisions qui dépendent d'un contexte dynamique** : autoriser un déploiement
  seulement en heures ouvrées, seulement depuis une branche donnée, seulement
  vers l'environnement de test.
- **Application d'une politique d'équipe** que la liste `permissions.allow` ne
  peut pas exprimer, parce qu'elle dépend de l'état du dépôt ou du réseau.

## Pièges

- **Préférer `permissions.allow` quand la règle est statique.** Une allowlist
  déclarative est auditable, ne peut pas être contournée par du chaînage de
  commandes ou une substitution `$(...)`, et ne coûte aucun processus. Un hook qui
  auto-approuve sur des motifs de commande est plus fragile qu'il n'en a l'air :
  un motif ancré sur `^ls ` autorise aussi `ls; rm -rf /`.
- Ne pas dupliquer ici ce que `permissions.allow` couvre déjà : deux mécanismes
  pour la même décision, dont un seul est robuste.
- Réserver ce hook aux cas que le déclaratif ne sait pas exprimer.
