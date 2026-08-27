# StopFailure

Se déclenche quand un tour se termine sur une erreur d'API plutôt que sur une
réponse.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `error` | type d'erreur — **`error`, pas `error_type`** |
| `error_details` | détail, optionnel (`429 Too Many Requests`…) |
| `last_assistant_message` | **la chaîne d'erreur d'API elle-même**, pas une réponse de Claude |

Valeurs de `error` : `rate_limit`, `overloaded`, `authentication_failed`,
`oauth_org_not_allowed`, `billing_error`, `invalid_request`, `model_not_found`,
`server_error`, `max_output_tokens`, `unknown`.

Le `matcher` porte sur `error`, avec un jeu de correspondance restreint :
lettres, chiffres, `_` et `|` seulement. Un tiret, un espace ou une virgule
bascule la valeur en expression régulière.

## Décision

Aucune. **La sortie et le code de retour sont ignorés**, à l'exception de
`terminalSequence`. L'événement ne sert qu'aux effets de bord.

## Ce qu'on peut y mettre

- **Notification** sur les erreurs qui demandent une action humaine :
  `authentication_failed`, `billing_error`, `oauth_org_not_allowed`. Un
  `terminalSequence` fonctionne ici alors que le reste est ignoré.
- **Journal des erreurs d'API** : distinguer une saturation passagère
  (`rate_limit`, `overloaded`) d'un problème de configuration
  (`model_not_found`, `invalid_request`) évite de chercher un bug là où il n'y en
  a pas.
- **Détection de `max_output_tokens`** : signale une réponse tronquée, donc un
  travail incomplet qu'il faut reprendre.

## Pièges

- **Ne pas lire `last_assistant_message` comme une réponse de Claude** : ici, il
  contient le message d'erreur. Un hook partagé avec [`Stop`](../Stop/) doit
  distinguer les deux cas.
- Toute logique de décision écrite pour cet événement est sans effet : le
  concevoir comme un capteur.
