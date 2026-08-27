# project

Initialisation de l'outillage Claude Code d'un projet Kodflow.

## Bootstrap — la seule partie manuelle

L'ajout d'une marketplace n'installe jamais de plugin (choix de sécurité de
Claude Code : installer un plugin active ses hooks, donc du code). Le premier
pas tient en une ligne :

```bash
claude plugin marketplace add git@github.com:kodflow/marketplace.git \
  && claude plugin install project@kodflow \
  && claude "/project:init"
```

La même commande couvre la première installation et la mise à jour : les deux
premières étapes sont idempotentes (sans effet si la marketplace est déjà
enregistrée, si le plugin est déjà installé), et c'est `init` qui porte la mise
à jour — rafraîchissement du catalogue, `plugin update` des plugins installés,
y compris `project` lui-même pour l'exécution suivante.

Prérequis SSH : `Port 2222` déclaré pour `gitlab.example.com` dans `~/.ssh/config`
(voir le [README de la marketplace](../../README.md)). À défaut, remplacer l'URL
par `https://github.com/kodflow/marketplace.git`.

Ensuite, dans le projet à équiper :

```
/project:init
```

## Ce que fait `init`

Sept étapes, affichées comme liste de tâches suivie en direct :

1. **Analyse du projet** — langages, marqueurs télécom/3GPP, forge, CI,
   outillage déjà présent, catalogue vivant de la marketplace.
2. **Validation** — les suggestions, chacune justifiée par un constat de
   l'analyse, sont soumises à sélection. Rien ne s'installe sans choix
   explicite.
3. **Marketplace** — enregistrement si absent, SSH ou HTTPS selon le poste.
4. **Plugins** — installation des sélections, à la portée choisie.
5. **Binaires** — rtk, gopls… ce que l'installation de plugin ne fait
   volontairement pas.
6. **Configuration projet** — `.claude/settings.json` versionné
   (`extraKnownMarketplaces` + `enabledPlugins`) : c'est lui qui fait que
   **chaque collègue ouvrant le dépôt est invité à installer l'outillage
   automatiquement**. Plus `.claude/commit-guard.json` et la configuration git
   de traçabilité (`core.abbrev 12`, `pretty.fixes`).
7. **Bilan** — tableau installé / déjà présent / échec / écarté, sans
   maquillage.

Ré-exécutable sans risque : l'existant est détecté et sauté.

## La boucle de propagation

```
 poste 1 : bootstrap une ligne + /project:init sur le projet
                         │
                         ▼
        .claude/settings.json versionné dans le dépôt
                         │
                         ▼
 postes 2..n : ouverture du dépôt → proposition d'installation automatique
```

La marketplace rend disponible, l'installation active, la skill orchestre —
et le dépôt propage.
