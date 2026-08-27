# PermissionDenied

Se déclenche quand **le mode auto** refuse un appel d'outil, y compris sur un
refus sans verdict de classifieur. Le refus a déjà eu lieu et ne peut pas être
annulé.

**Ne se déclenche pas** sur un refus manuel de l'utilisateur, sur un blocage
[`PreToolUse`](../PreToolUse/), ni sur une règle `deny` des permissions. Un
journal des refus bâti sur ce seul événement ne voit donc qu'une partie du
tableau.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `tool_name`, `tool_input`, `tool_use_id` | l'appel refusé |
| `reason` | motif du refus — **`reason`, pas `denial_reason`** |

Valeurs observées de `reason` : `Blocked by classifier`, l'explication écrite du
classifieur quand il en fournit une, une chaîne commençant par `Auto mode could
not evaluate this action and is blocking it for safety`, ou
`Classifier unavailable`.

## Décision

Un seul champ est lu :

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionDenied",
    "retry": true
  }
}
```

`retry: true` ajoute un message indiquant à Claude qu'il peut réessayer. **Le
refus n'est pas levé pour autant.** Le champ est ignoré pour les refus sans
verdict.

Code de sortie et stderr sont ignorés.

## Ce qu'on peut y mettre

- **Journal des refus** : quels outils, quelles commandes, quel motif. C'est la
  matière première pour ajuster `permissions.allow` — un refus récurrent sur une
  commande manifestement sûre signale une allowlist trop étroite.
- **Autoriser une nouvelle tentative** dans les cas où le refus vient d'une
  indisponibilité du classifieur plutôt que d'un jugement : `Classifier
  unavailable` n'est pas un refus de fond.
- **Métrique de friction** : un taux de refus élevé sur un poste indique une
  configuration de permissions mal calibrée.

## Pièges

- Ne pas prendre `retry: true` pour un contournement : c'est une invitation à
  réessayer, pas une autorisation.
- Distinguer les refus de fond (`Blocked by classifier` avec explication) des
  refus techniques (`Classifier unavailable`) avant de proposer une reprise.
