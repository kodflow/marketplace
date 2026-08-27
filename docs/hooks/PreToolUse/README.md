# PreToolUse

Se déclenche **avant** l'exécution d'un outil, après que Claude a décidé de
l'appeler et avant que le système de permissions ne tranche.

C'est le point de contrôle le plus rentable : le seul qui puisse empêcher une
action et faire corriger Claude dans la foulée.

## Payload

Champs spécifiques, en plus des [champs communs](../README.md) :

| Champ | Contenu |
| ----- | ------- |
| `tool_name` | `Bash`, `Write`, `Edit`, `Read`, `Grep`, `Agent`, `mcp__<serveur>__<outil>`… |
| `tool_input` | Les arguments de l'outil |
| `tool_use_id` | Identifiant de cet appel |

`tool_input` pour `Bash` : `command` (string), `description` (string, optionnel),
`timeout` (millisecondes), `run_in_background` (booléen).
Pour `Write` : `file_path`, `content`. Pour `Edit` : `file_path`, `old_string`,
`new_string`, `replace_all`.

`file_path` est **toujours absolu** — `~` et les chemins relatifs sont résolus
avant les hooks, un contrôle sur chemin ne peut donc pas être contourné par une
écriture relative.

## Décision

| Sortie | Effet |
| ------ | ----- |
| `permissionDecision: "deny"` + `permissionDecisionReason` | refuse l'appel, **et la raison est transmise à Claude** |
| `permissionDecision: "ask"` | demande confirmation ; la raison va à l'utilisateur, pas à Claude |
| `permissionDecision: "allow"` | saute l'invite ; la raison va à l'utilisateur, pas à Claude |
| `updatedInput` | remplace les arguments de l'outil — remplacement **intégral**, inclure les champs inchangés |
| `additionalContext` | ajoute du texte à côté du résultat de l'outil |
| `exit 2` | équivalent à `deny`, stderr servant de motif |

Quand plusieurs hooks répondent, la précédence est `deny` > `defer` > `ask` >
`allow`. Un `allow` ne surpasse pas une règle de refus des permissions.

**Seul `deny` parle à Claude.** Pour faire corriger une action, il faut la
refuser en expliquant : un `allow` assorti d'un avertissement ne change rien au
comportement du modèle.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Les migrations appliquées ne se modifient pas. Créer une nouvelle migration."
  }
}
```

## Ce qu'on peut y mettre

**Sur `Bash`**

- Garde git : refus de `--no-verify`, du push direct sur branche protégée,
  contrôle du message de commit — c'est ce que fait
  [`commit-guard`](../../../plugins/commit-guard/).
- Réécriture plutôt que refus : transformer `git push --force` en
  `--force-with-lease` via `updatedInput`, ce qui corrige sans interrompre.
- Scan de secrets sur les blobs **indexés** avant un commit.
- Refus des commandes destructrices hors périmètre : `rm -rf` en dehors du
  workspace, `DROP TABLE` sur une base de production, `kubectl --context=prod`.
- Refus des commandes interactives qui figeraient la session (éditeur, `less`,
  `top`, `ssh` sans commande).

**Sur `Write`/`Edit`**

- Chemins protégés déclarés en YAML versionné : lockfiles, migrations déjà
  appliquées, code généré, manifestes d'infrastructure de production.
- Refus d'écriture hors du périmètre assigné à un agent, en multi-agents.
- Injection de contexte ciblé : « ce fichier est généré depuis `schema.ts`,
  éditer la source ».

**Sur les outils MCP** — le matcher doit s'écrire `mcp__memory__.*` : `mcp__memory`
seul ne contient que des caractères d'égalité stricte et ne matche rien.

## Pièges

- **Le hook ne se déclenche pas pour les fichiers référencés par `@`** dans un
  prompt : leur contenu est inséré sans appel d'outil. Pour bloquer un chemin en
  lecture, utiliser une règle de refus `Read`, pas un hook.
- **Un timeout ne bloque pas** : le hook est annulé et l'appel passe. Un
  garde-fou trop lent s'ouvre en grand.
- **Le filtre `if` est best-effort et fail-open** quand la commande ne parse pas.
  Utile pour éviter du travail inutile, jamais comme barrière.
- Le hook s'exécute **avant chaque appel d'outil correspondant** : filtrer le cas
  non concerné en tête de script, avant tout travail coûteux.
- Sur Windows sans Git Bash, les commandes shell passent par `PowerShell` :
  matcher `Bash|PowerShell` si le poste est concerné.

## Exemple

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/garde.sh\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Implémentation de référence : [`commit-guard`](../../../plugins/commit-guard/scripts/commit_guard.py).
