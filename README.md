# Marketplace Claude Code — Kodflow

Catalogue d'extensions Claude Code : **skills**, **commandes**, **agents**,
**workflows**, **hooks** et **serveurs MCP**, distribués sous forme de plugins et
mis à jour depuis ce dépôt.

- Dépôt : `https://github.com/kodflow/marketplace`
- Nom de la marketplace : `kodflow` (c'est ce nom qui apparaît dans `<plugin>@kodflow`)
- Branche de publication : `main`

> **Le nom de la marketplace et ceux des plugins sont indépendants du nom du
> dépôt.** Renommer le dépôt ne change pas les identifiants `<plugin>@kodflow` et
> n'impose aucune entrée `renames` : seule l'URL source change.

## Sommaire

- [Installation](#installation)
- [Plugins disponibles](#plugins-disponibles)
- [Documentation](#documentation)
- [Mise à jour et propagation](#mise-à-jour-et-propagation)
- [Déployer la marketplace sur un projet ou une équipe](#déployer-la-marketplace-sur-un-projet-ou-une-équipe)
- [Contribuer](#contribuer)
- [Dépannage](#dépannage)

## Prérequis

- Claude Code ≥ 2.1 (`claude --version`)

Le dépôt étant public, aucune configuration d'accès n'est nécessaire.

## Installation

### Démarrage rapide

Fresh install ou mise à jour, même commande — chaque étape est idempotente et
c'est `init` qui rafraîchit le catalogue et met les plugins à jour :

```bash
claude plugin marketplace add kodflow/marketplace \
  && claude plugin install project@kodflow \
  && claude "/project:init"
```

Enregistre la marketplace (sans effet si déjà présente), installe `project`
(sans effet si déjà installé), puis ouvre une session sur `/project:init` — qui
analyse le projet, rafraîchit le catalogue, met à jour les plugins installés et
propose le reste de l'outillage.

Le détail de chaque étape suit.

### 1. Enregistrer la marketplace

Depuis une session Claude Code :

```
/plugin marketplace add kodflow/marketplace
```

ou, hors session :

```bash
claude plugin marketplace add kodflow/marketplace
```

Les formes acceptées par `marketplace add` sont `owner/repo`, une URL `https://`,
la forme `git@hôte:chemin` et un chemin local. Une URL `ssh://…` **n'est pas
acceptée** : Claude Code répond `Invalid marketplace source format.`

Ajouter cette étape ne télécharge que le catalogue : aucun plugin n'est installé.

### 2. Installer les plugins

```
/plugin install devkit@kodflow
```

Claude Code demande la portée d'installation :

| Portée | Effet | Où c'est écrit |
| ------ | ----- | -------------- |
| `user` | pour vous, sur tous vos projets | `~/.claude/settings.json` |
| `project` | pour tous les contributeurs du dépôt courant | `.claude/settings.json` (versionné) |
| `local` | pour vous, sur ce dépôt seulement | `.claude/settings.local.json` |

En ligne de commande, la portée est explicite (`user` par défaut) :

```bash
claude plugin install devkit@kodflow --scope project
```

Si le résumé d'installation affiche `Run /reload-plugins to activate.`, lancez
`/reload-plugins` — sinon le plugin est déjà actif dans la session.

### 3. Vérifier

```
/plugin              # onglets Discover / Installed / Marketplaces / Errors
/plugin list
```

Les composants d'un plugin sont préfixés par son nom : la skill `new-plugin` du
plugin `devkit` s'invoque avec `/devkit:new-plugin`.

## Plugins disponibles

| Plugin | Description | Contenu |
| ------ | ----------- | ------- |
| `golang` | Standards de développement Go | Commandes `review` et `build`, agents `go-expert`, `ddd-architect`, `code-reviewer`, `performance-optimizer`, hook de formatage, serveurs MCP `github` et `codacy` |
| `devkit` | Outillage de la marketplace | Skill `new-plugin` : créer, enregistrer et valider un nouveau plugin |
| `commit-guard` | Convention de commit imposée | Hook `PreToolUse` sur `git commit` + skill `commit` |
| `go-review-panel` | Panel de revue de MR/PR Go | Agents `dogmatic-go-reviewer`, `paranoid-perf-gopher`, `annoying-product-owner` + skills `coding-style` et `review-mr` |
| `issue-workflow` | Workflow d'issue de bout en bout | Skills `writing-rules`, `implement-issue`, `pragmatic-coder` + commande `post-issue` + serveur MCP `gitlab` |
| `3gpp-expert` | Connaissance 3GPP/télécom | Skill `3gpp-expert` : releases, protocoles, architecture, audit de conformité, cache de specs ETSI |
| `project` | Initialisation d'un projet | Skill `init` : analyse du projet, installation des plugins/binaires après validation, configuration projet propagée à l'équipe |

Le catalogue fait foi : `.claude-plugin/marketplace.json`.

## Documentation

| Document | Contenu |
| -------- | ------- |
| [docs/hooks/](docs/hooks/) | Catalogue des **31 événements de hook** : une fiche par événement — déclenchement, payload, capacité de blocage et d'injection, usages pertinents, pièges |
| [docs/commit-format.md](docs/commit-format.md) | Convention de commit, avec la distinction entre ce qui est normatif et ce qui relève de l'usage |
| [tools/binaries.json](tools/binaries.json) | Catalogue des **binaires externes** (gopls, golangci-lint…) : source officielle déclarée par binaire, moteur `tools/binaries.py` (`status` / `update`) avec vérification des sommes de contrôle — c'est lui que `/project:init` pilote |
| [.devcontainer/](.devcontainer/) | Environnement de développement conteneurisé du dépôt (Ubuntu 24.04, zsh, MCP) — voir son [README](.devcontainer/README.md) |

## Mise à jour et propagation

### Comment une modification du dépôt arrive sur un poste

```
   PR fusionnée sur main
            │
            ▼
   ① le poste rafraîchit le catalogue      (git pull du dépôt marketplace)
            │                                → /plugin marketplace update kodflow
            ▼
   ② le poste met à jour les plugins installés  (nouvelle version en cache)
            │                                → /plugin update <plugin>@kodflow
            ▼
   ③ la session charge la nouvelle version  → /reload-plugins, ou prochain démarrage
```

Ces trois étapes sont automatiques si l'auto-update est activé pour la
marketplace (voir plus bas), manuelles sinon.

### Version d'un plugin : par SHA de commit

Les plugins de cette marketplace **ne déclarent pas de champ `version`**, ni dans
`plugin.json`, ni dans leur entrée de `marketplace.json`. Claude Code résout
alors la version d'un plugin par le **SHA du commit** de sa source.

Conséquence, et c'est le comportement voulu ici : **tout commit fusionné sur
`main` qui touche un plugin devient une nouvelle version de ce plugin**, et se
propage sans aucune action de publication.

L'alternative — déclarer `"version": "1.2.0"` — épingle le plugin : tant que le
champ n'est pas incrémenté, les nouveaux commits ne sont **pas** distribués et
`/plugin update` répond « already at the latest version ». C'est un piège
classique ; ne pas ajouter de `version` à un plugin sans décider en même temps
qui incrémente le champ à chaque release.

Le `CHANGELOG.md` sert d'historique lisible ; il n'a aucun effet sur la
distribution.

### Mise à jour manuelle

```
/plugin marketplace update kodflow          # rafraîchit le catalogue
/plugin update devkit@kodflow               # met à jour un plugin installé
/reload-plugins                             # applique sans redémarrer
```

Équivalents hors session : `claude plugin marketplace update kodflow`,
`claude plugin update devkit@kodflow`.

`update` ≠ `remove` : **supprimer la marketplace désinstalle tous les plugins qui
en proviennent**. Pour resynchroniser, toujours utiliser `update`.

### Mise à jour automatique

L'auto-update est **désactivé par défaut** pour les marketplaces tierces — donc
pour celle-ci. Chaque utilisateur l'active une fois :

1. `/plugin`
2. onglet **Marketplaces**
3. sélectionner `kodflow`
4. **Enable auto-update**

Une fois activé, Claude Code vérifie le catalogue et les plugins installés
**après le démarrage de la session, avec un délai aléatoire pouvant aller jusqu'à
dix minutes** ; la session en cours continue de tourner sur les versions chargées
au lancement. Si des plugins ont été mis à jour, une notification propose
`/reload-plugins` — sinon les nouvelles versions sont chargées au lancement
suivant.

Côté administration, l'auto-update peut être imposé sans intervention des
utilisateurs en déclarant la marketplace dans les *managed settings* avec
`"autoUpdate": true` (voir la section suivante).

Pour couper toute mise à jour automatique, la variable d'environnement
`DISABLE_AUTOUPDATER` désactive celles de Claude Code **et** des plugins. Pour ne
couper que celles de Claude Code en gardant les plugins à jour :

```bash
export DISABLE_AUTOUPDATER=1
export FORCE_AUTOUPDATE_PLUGINS=1
```

## Déployer la marketplace sur un projet ou une équipe

### Par projet (versionné avec le dépôt)

Dans le `.claude/settings.json` d'un dépôt :

```json
{
  "extraKnownMarketplaces": {
    "kodflow": {
      "source": {
        "source": "github",
        "repo": "kodflow/marketplace"
      }
    }
  },
  "enabledPlugins": {
    "devkit@kodflow": true
  }
}
```

Quand un contributeur ouvre le projet et accorde sa confiance au dossier, Claude
Code lui propose d'installer la marketplace et les plugins listés. Un plugin
déclaré uniquement dans `enabledPlugins` d'un projet et provenant d'une source
distante ne se charge pas tant qu'il n'a pas été installé : Claude Code affiche
alors la commande `claude plugin install` à lancer.

Ce fichier est fourni prêt à copier dans `examples/project-settings.json`.

### Pour toute l'organisation (managed settings)

Poussé par l'IT dans le fichier de *managed settings* du poste, pour enregistrer
la marketplace sans action utilisateur et forcer son auto-update :

```json
{
  "extraKnownMarketplaces": {
    "kodflow": {
      "source": {
        "source": "github",
        "repo": "kodflow/marketplace"
      },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "devkit@kodflow": true
  }
}
```

Les plugins déclarés dans les managed settings sont en portée `managed` :
l'utilisateur ne peut pas les désactiver.

Restriction des sources autorisées (optionnel, managed settings) :

```json
{
  "strictKnownMarketplaces": [
    { "source": "hostPattern", "hostPattern": "^github\\.com$" }
  ]
}
```

Un `hostPattern` est préférable à une URL littérale : la comparaison d'URL est
exacte, et les formes `https://`, `ssh://`, avec ou sans suffixe `.git`, ne
correspondraient pas entre elles.

### Postes en conteneur / CI

Pour éviter tout clone à l'exécution, préremplir un répertoire de graine à la
construction de l'image et pointer `CLAUDE_CODE_PLUGIN_SEED_DIR` dessus :

```bash
CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed \
  claude plugin marketplace add kodflow/marketplace
CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed \
  claude plugin install devkit@kodflow
# puis, au runtime :
export CLAUDE_CODE_PLUGIN_SEED_DIR=/opt/claude-seed
```

Une marketplace issue d'une graine est en lecture seule : ses auto-updates sont
désactivés, et `/plugin marketplace update` ou `remove` échouent dessus. La mise
à jour passe alors par la reconstruction de l'image.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md). En résumé :

```bash
git clone https://github.com/kodflow/marketplace.git
cd marketplace
cp -r templates/plugin-template plugins/<nom>       # ou /devkit:new-plugin
# ... éditer, ajouter l'entrée dans .claude-plugin/marketplace.json ...
./scripts/validate.sh
```

Test local avant PR, depuis le clone :

```
/plugin marketplace add ./
/plugin install <nom>@kodflow
/reload-plugins
```

Ce test enregistre une marketplace nommée `kodflow` pointant sur votre clone
local. Comme un même nom ne peut désigner qu'une seule marketplace, cela
**remplace** l'enregistrement distant. Pour revenir à la version publiée :

```
/plugin marketplace remove kodflow
/plugin marketplace add kodflow/marketplace
```

(la suppression désinstalle les plugins issus de cette marketplace, à réinstaller
ensuite).

## Dépannage

| Symptôme | Cause | Action |
| -------- | ----- | ------ |
| `Marketplace "kodflow" not found` | marketplace non enregistrée | `/plugin marketplace add kodflow/marketplace` |
| Plugin absent du catalogue alors qu'il est sur `main` | catalogue local périmé | `/plugin marketplace update kodflow` |
| `/plugin update` répond « already at the latest version » | version épinglée par un champ `version` | retirer le champ, ou l'incrémenter |
| Modifications poussées mais rien ne change en session | la session tourne sur les versions chargées au lancement | `/reload-plugins` (puis `--force` si l'invalidation du cache est signalée) |
| `Invalid marketplace source format` | URL `ssh://…` : format non accepté | utiliser `kodflow/marketplace` ou l'URL `https://` |
| Auto-update qui échoue en boucle (hors ligne) | re-clone tenté à chaque `git pull` en échec | `export CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` |
| `Git clone timed out after 120s` | dépôt volumineux ou lien lent | `export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000` |
| Les skills d'un plugin n'apparaissent pas | cache de plugins corrompu | `rm -rf ~/.claude/plugins/cache`, redémarrer, réinstaller |

Détail des erreurs de chargement : `/plugin`, onglet **Errors**.

## Licence

Aucune licence n'est accordée sur ce dépôt : tous droits réservés.

Exception — le skill `3gpp-expert` intègre du contenu tiers issu de
[lugasia/3gpp-skill](https://github.com/lugasia/3gpp-skill), sous licence MIT.
Cette licence et son attribution sont conservées dans
`plugins/3gpp-expert/skills/3gpp-expert/LICENSE-UPSTREAM` et s'appliquent aux
fichiers qui y sont désignés.

## Références

- [Créer et distribuer une marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- [Découvrir et installer des plugins](https://code.claude.com/docs/en/discover-plugins)
- [Référence des plugins](https://code.claude.com/docs/en/plugins-reference)
