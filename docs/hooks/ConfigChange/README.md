# ConfigChange

Se déclenche quand une configuration change en cours de session.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `source` | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `file_path` | fichier concerné, optionnel |

**`source` et `file_path`, pas `config_source` / `config_path`.**
Le `matcher` porte sur `source`.

## Décision

`exit 2` ou `decision: "block"` **empêche la prise en compte du changement** dans
la session en cours. Exception : `policy_settings` — les hooks tirent pour
l'audit, mais toute décision bloquante y est ignorée, les réglages gérés
s'appliquant toujours.

**Un blocage est totalement silencieux** : `reason` est accepté mais jamais
affiché, `systemMessage` et `continue` sont jetés. Ni l'utilisateur ni Claude
n'apprennent que le changement a été refusé — seule une ligne part au journal de
debug. Un hook qui bloque ici doit donc prévoir son propre canal d'information.

## Ce qu'on peut y mettre

- **Journal de sécurité dédié.** Un changement de configuration en cours de
  session mérite une trace distincte du journal courant : quoi, quand, dans
  quelle portée.
- **Alerte sur élargissement des permissions** : apparition de
  `bypassPermissions`, ajout d'une règle `allow` large, changement de
  `defaultMode`. C'est le signal qu'on veut voir passer, pas découvrir après coup.
- **Refus des modifications non autorisées** de réglages critiques dans la portée
  projet, quand la politique d'équipe les réserve à la portée gérée.
- **Expédition vers un SIEM** plutôt qu'un fichier local, pour une flotte.

## Pièges

- `policy_settings` échappe au blocage : c'est voulu, la politique gérée prime.
- Attention à la boucle : un hook qui écrit dans un fichier de configuration
  surveillé se re-déclenche lui-même.
- Bloquer un changement légitime est **doublement** déroutant : l'utilisateur
  vient de modifier son fichier et rien ne lui dit que le refus vient d'un hook.
  Privilégier l'alerte, réserver le refus aux réglages réellement critiques, et
  toujours journaliser le blocage quelque part de consultable.
