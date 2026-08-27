# Contribuer à la marketplace Kodflow

## Ce que contient un plugin

Un plugin regroupe un ou plusieurs composants Claude Code :

| Composant | Emplacement | Invocation |
| --------- | ----------- | ---------- |
| Skill | `skills/<nom>/SKILL.md` | `/<plugin>:<nom>` |
| Commande | `commands/<nom>.md` | `/<plugin>:<nom>` |
| Agent | `agents/<nom>.md` | `<plugin>:<nom>` |
| Workflow | `workflows/<nom>.js` | via l'outil Workflow |
| Hooks | `hooks/hooks.json` | automatique |
| Serveur MCP | `.mcp.json` | automatique |

Ces répertoires sont à la **racine du plugin**, jamais dans `.claude-plugin/`,
qui ne contient que `plugin.json`.

## Découpage en plugins

Un plugin = un périmètre fonctionnel installable et désinstallable d'un bloc.
Regrouper par domaine (par exemple l'outillage d'une stack ou d'un produit), pas
par type de composant : un utilisateur installe « l'outillage X », pas « les
agents ».

Chaque plugin installé coûte du contexte à chaque tour de session. Préférer
plusieurs plugins ciblés à un plugin fourre-tout que tout le monde installerait
en entier.

## Nommage

- `name` en kebab-case, sans espace, unique dans le catalogue.
- **`name` est un identifiant définitif** : il sert de clé dans les réglages des
  utilisateurs (`enabledPlugins`, `pluginConfigs`) et dans `/plugin install`.
  Le changer casse toutes les installations existantes.
  - Pour changer seulement le libellé affiché : utiliser `displayName`.
  - Pour renommer ou supprimer réellement un plugin : ajouter une entrée dans
    l'objet `renames` de `marketplace.json` (`"ancien-nom": "nouveau-nom"`, ou
    `"ancien-nom": null` en cas de suppression). Les utilisateurs migrent alors
    automatiquement au lieu de tomber sur `plugin-not-found`.
    `renames` est un historique : on y ajoute, on n'en retire jamais.

## Versionnement

Aucun plugin ne déclare de champ `version`, ni dans `plugin.json` ni dans son
entrée de catalogue. Claude Code résout donc la version par le SHA du commit :
tout commit fusionné sur `main` est distribué. Le script de validation refuse
un champ `version`.

`CHANGELOG.md` documente les évolutions pour les humains ; il n'a aucun effet sur
la distribution.

## Workflow de contribution

```bash
git clone https://github.com/kodflow/marketplace.git
cd marketplace
git checkout -b feat/<plugin>
```

1. **Créer le plugin** : `cp -r templates/plugin-template plugins/<nom>`,
   ou lancer `/devkit:new-plugin` qui fait le scaffolding et l'enregistrement.
2. **Adapter** `plugins/<nom>/.claude-plugin/plugin.json` et supprimer les
   répertoires de composants inutilisés.
3. **Enregistrer** le plugin dans le tableau `plugins` de
   `.claude-plugin/marketplace.json`.
4. **Valider** : `./scripts/validate.sh`.
5. **Tester en local** (voir ci-dessous).
6. **Documenter** : `README.md` du plugin + une ligne dans `CHANGELOG.md` +
   la ligne correspondante dans le tableau « Plugins disponibles » du README racine.
7. **Pull request** vers `main`. La CI rejoue la validation.

### Tester en local

Depuis le clone :

```
/plugin marketplace add ./
/plugin install <nom>@kodflow
/reload-plugins
```

Le catalogue local porte le même nom (`kodflow`) que le catalogue distant et le
**remplace** dans vos réglages : un nom de marketplace ne peut désigner qu'une
source à la fois. Après le test, revenir à la source publiée :

```
/plugin marketplace remove kodflow
/plugin marketplace add kodflow/marketplace
```

Retirer une marketplace désinstalle les plugins qui en proviennent : les
réinstaller ensuite.

Pour itérer sur un plugin sans passer par la marketplace, `claude --plugin-dir
./plugins/<nom>` charge le plugin pour la durée de la session.

## Revue

Points regardés en pull request :

- le plugin est validé (`./scripts/validate.sh` passe, CI verte) ;
- `name` en kebab-case, unique, et cohérent entre `plugin.json` et le catalogue ;
- aucun champ `version` ;
- description utile : c'est sur elle que Claude décide d'invoquer une skill ou un agent ;
- chemins internes exprimés avec `${CLAUDE_PLUGIN_ROOT}` (le plugin est copié
  dans un cache versionné, les chemins du dépôt ne valent rien chez l'utilisateur) ;
- aucun secret, jeton, URL interne sensible ou donnée client dans les fichiers ;
- scripts de hooks exécutables (`chmod +x`) et sobres en temps d'exécution ;
- coût en contexte proportionné à l'usage attendu.

## Sécurité

Un plugin exécute du code sur le poste de celui qui l'installe, avec ses droits.
Tout ce qui est fusionné ici est distribué automatiquement à tous les postes qui
ont ce plugin installé et l'auto-update activé. La revue par un pair est donc
obligatoire, y compris pour les modifications d'apparence anodine.
