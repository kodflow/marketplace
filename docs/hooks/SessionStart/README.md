# SessionStart

Se déclenche au démarrage d'une session, avant le premier prompt. Également au
retour d'un `/clear`, d'une compaction, d'une reprise ou d'un fork.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `source` | `startup`, `resume`, `clear`, `compact`, `fork` |
| `model` | identifiant du modèle actif — **peut être absent**, tester avant de lire |
| `agent_type` | présent avec `claude --agent <nom>` |
| `session_title` | titre déjà défini par `--name` ou `/rename` |

`source` est aussi ce sur quoi porte le `matcher` : `"compact"` cible le retour
de compaction, `"startup"` le démarrage réel.

Seul cet événement peut recevoir `model`, et il n'existe aucune variable
d'environnement `$CLAUDE_MODEL`.

## Décision

Aucun blocage possible. Uniquement de l'injection :

| Sortie | Effet |
| ------ | ----- |
| `additionalContext` | contexte ajouté avant le premier prompt |
| stdout brut | également ajouté comme contexte |
| `initialUserMessage` | **crée** un premier tour utilisateur (mode `-p`) |
| `sessionTitle` | nomme la session |
| `watchPaths` | liste de chemins absolus à surveiller pour [`FileChanged`](../FileChanged/) |
| `reloadSkills` | re-scanne les répertoires de skills après les hooks |

## Ce qu'on peut y mettre

- **Pré-calculer les métadonnées coûteuses** et les persister dans
  `$CLAUDE_ENV_FILE` (disponible ici, sur `Setup`, `CwdChanged` et
  `FileChanged`) : organisation, dépôt, branche, branche par défaut. Un
  `git rev-parse` économisé à chaque appel d'outil ensuite.
- **Nettoyer les ressources orphelines** : worktrees abandonnés, verrous
  périmés, conteneurs de test.
- **Émettre une ligne de sonde stable** sur l'état de l'outillage
  (`mode=enforcing reason=ok`), en distinguant un contournement volontaire d'une
  panne — c'est ce qui rend l'état diagnosticable sans lire le code.
- **Sur `matcher: "compact"`** : réinjecter les quelques règles non négociables
  perdues à la compaction. Cinq à huit lignes, pas un manuel — le texte est payé
  à chaque compaction.
- Contexte projet dynamique : version déployée, fenêtre de maintenance en cours,
  cible de test.

## Pièges

- `additionalContext` en **constat**, jamais en instruction système.
- Les hooks `SessionStart` **rejouent** à la reprise (`source: "resume"`), ce qui
  permet de rafraîchir un contexte que le transcript aurait figé.
- Ne pas écraser un `session_title` posé explicitement par l'utilisateur : tester
  le champ avant d'émettre `sessionTitle`.
- Un contexte volumineux est payé à chaque session : au-delà de 10 000
  caractères, il est écrit dans un fichier et remplacé par un aperçu.

## Exemple

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/init.sh\"", "timeout": 10 }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/post-compact.sh\"" }
        ]
      }
    ]
  }
}
```
