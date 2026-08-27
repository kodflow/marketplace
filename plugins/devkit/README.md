# devkit

Outillage de la marketplace Kodflow.

## Installation

```
/plugin marketplace add git@github.com:kodflow/marketplace.git
/plugin install devkit@kodflow
```

## Contenu

| Composant | Invocation | Rôle |
| --------- | ---------- | ---- |
| Skill `new-plugin` | `/devkit:new-plugin` | Créer un plugin dans la marketplace, l'enregistrer dans `marketplace.json` et le valider |

Les composants des plugins sont préfixés par le nom du plugin, d'où
`/devkit:new-plugin`.
