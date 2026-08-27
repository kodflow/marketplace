# plugin-template

Squelette de plugin pour la marketplace Kodflow. Ce répertoire n'est **pas** listé
dans `.claude-plugin/marketplace.json` : il n'est donc pas installable tel quel.

## Utilisation

```bash
cp -r templates/plugin-template plugins/<nom-du-plugin>
```

Puis :

1. adapter `.claude-plugin/plugin.json` (`name` = `<nom-du-plugin>`) ;
2. supprimer les répertoires de composants inutilisés ;
3. ajouter l'entrée correspondante dans `.claude-plugin/marketplace.json` ;
4. valider : `claude plugin validate ./plugins/<nom-du-plugin> --strict`.

Ou laisser la skill faire le travail : `/devkit:new-plugin`.

## Arborescence

| Chemin | Composant | Emplacement par défaut lu par Claude Code |
| ------ | --------- | ----------------------------------------- |
| `.claude-plugin/plugin.json` | Manifeste | oui |
| `skills/<nom>/SKILL.md` | Skill | `skills/` |
| `commands/<nom>.md` | Commande (skill en fichier plat) | `commands/` |
| `agents/<nom>.md` | Sous-agent | `agents/` |
| `workflows/<nom>.js` | Workflow | `workflows/` |
| `hooks/hooks.json` | Hooks | `hooks/hooks.json` |
| `.mcp.json` | Serveurs MCP | `.mcp.json` |

Ces répertoires vont à la racine du plugin, jamais dans `.claude-plugin/`.

Dans les hooks et les configurations MCP, référencer les fichiers du plugin avec
`${CLAUDE_PLUGIN_ROOT}` : le plugin est copié dans un cache versionné à
l'installation, les chemins absolus du dépôt ne sont pas valides chez
l'utilisateur.
