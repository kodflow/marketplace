---
name: new-plugin
description: Créer un nouveau plugin dans la marketplace Kodflow (skills, commandes, agents, workflows), l'enregistrer dans marketplace.json et le valider avant publication.
---

# Créer un plugin dans la marketplace Kodflow

Cette skill s'exécute depuis un clone du dépôt `kodflow/marketplace`.

## 1. Vérifier le contexte

Vérifie que le répertoire courant contient `.claude-plugin/marketplace.json`.
Si ce n'est pas le cas, demande à l'utilisateur le chemin du clone de la marketplace
et travaille depuis là.

## 2. Collecter les informations

Demande à l'utilisateur, s'il ne les a pas déjà données :

- le nom du plugin (kebab-case, sans espace — c'est l'identifiant public,
  utilisé par `/plugin install <nom>@kodflow` et il ne doit plus changer ensuite) ;
- une description en une phrase ;
- les composants à embarquer : skills, commandes, agents, workflows, hooks, serveurs MCP.

## 3. Créer l'arborescence

Copie `templates/plugin-template/` vers `plugins/<nom>/`, puis supprime les
répertoires de composants qui ne servent pas. Structure de référence :

```
plugins/<nom>/
├── .claude-plugin/plugin.json   # manifeste (name obligatoire)
├── skills/<skill>/SKILL.md      # skills
├── commands/<cmd>.md            # commandes (fichiers .md plats)
├── agents/<agent>.md            # sous-agents
├── workflows/<wf>.js            # workflows
├── hooks/hooks.json             # hooks
├── .mcp.json                    # serveurs MCP
└── README.md
```

Tous ces répertoires sont à la racine du plugin, **jamais** dans `.claude-plugin/`.

## 4. Renseigner le manifeste

Édite `plugins/<nom>/.claude-plugin/plugin.json` : `name`, `displayName`,
`description`, `author`, `keywords`.

**Ne mets pas de champ `version`.** La marketplace Kodflow versionne les plugins
par le SHA du commit : ajouter un `version` figé bloquerait les mises à jour
tant que personne ne le bump. Voir la section « Mise à jour » du README racine.

## 5. Enregistrer le plugin dans la marketplace

Ajoute une entrée dans le tableau `plugins` de `.claude-plugin/marketplace.json` :

```json
{
  "name": "<nom>",
  "source": "./plugins/<nom>",
  "description": "...",
  "author": { "name": "Kodflow" },
  "category": "...",
  "keywords": ["..."]
}
```

## 6. Valider

```bash
./scripts/validate.sh              # cohérence du catalogue + validation de chaque plugin
```

ou directement :

```bash
claude plugin validate .           # la marketplace
claude plugin validate ./plugins/<nom>   # le plugin
```

Corrige toutes les erreurs. Un seul avertissement est attendu et normal :
`version: No version specified` — c'est le choix de versionnement de la
marketplace. Ne pas utiliser `--strict`, qui transformerait cet avertissement
en erreur.

## 7. Tester en local avant de pousser

```
/plugin marketplace add ./                  # depuis le clone
/plugin install <nom>@kodflow
/reload-plugins
```

## 8. Publier

Branche dédiée, pull request vers `main`. Une fois la PR fusionnée, les
utilisateurs reçoivent le plugin via `/plugin marketplace update kodflow` ou par
l'auto-update. Ajoute une ligne au `CHANGELOG.md`.
