# PostToolUseFailure

Se déclenche quand un outil a échoué. L'échec est déjà survenu ; l'intérêt est
d'aider Claude à le comprendre du premier coup.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `tool_name`, `tool_input`, `tool_use_id` | l'appel qui a échoué |
| `error` | description de l'échec — **`error`, il n'existe pas de champ `error_type`** |
| `is_interrupt` | `true` quand il s'agit d'un abandon plutôt que d'une erreur remontée par l'outil |
| `duration_ms` | durée avant échec |

Pour `Bash`, `error` commence généralement par une ligne `Exit code N`, suivie de
la sortie avec stdout et stderr entrelacés. Le texte est tronqué au-delà de
10 000 caractères.

La documentation recommande de ne se fier qu'à `tool_name`, `is_interrupt` et la
première ligne `Exit code N` : le reste est du texte d'affichage, pas un format
stable.

## Décision

Pas de blocage. `hookSpecificOutput.additionalContext` est le seul champ utile.
`exit 2` fait remonter stderr à Claude.

Ne se déclenche **pas** pour un appel rejeté avant exécution (outil inconnu,
schéma invalide) ni pour un refus de permission.

## Ce qu'on peut y mettre

- **Table de remédiation maison** : traduire les erreurs récurrentes de
  l'environnement Kodflow en action concrète. « connection refused sur 172.19.1.x »
  → « le VPN LI Dauphin est probablement coupé, ou la route est masquée par le
  bridge Docker ». C'est là que se capitalise ce qu'on redécouvre sinon à chaque
  fois.
- **Conseils génériques** indexés sur le motif d'erreur : dépendance absente,
  droits insuffisants, chemin inexistant, timeout.
- **Métrique de friction outillage** : un journal des échecs par outil et par
  motif montre où l'environnement de développement fait perdre du temps.

## Pièges

- Rester utile : un conseil générique répété à chaque échec devient du bruit que
  Claude apprend à ignorer.
- Ne pas rejouer la commande depuis le hook pour « diagnostiquer » — le hook doit
  rester rapide et sans effet de bord.

## Exemple

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "Le port 7717 est celui du daemon ktn-linter, qui n'est pas démarré par défaut. Cette erreur n'indique pas un problème de code."
  }
}
```
