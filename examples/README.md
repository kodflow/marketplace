# Exemples de configuration

## `project-settings.json`

À fusionner dans le `.claude/settings.json` d'un dépôt pour que la
marketplace et les plugins choisis soient proposés à l'installation à tous les
contributeurs du projet.

```bash
mkdir -p .claude
cp examples/project-settings.json .claude/settings.json   # ou fusionner s'il existe déjà
```

Le fichier est versionné avec le projet : c'est le moyen de propager un socle
d'outillage à une équipe sans passer par les postes un par un.

Ajouter dans `enabledPlugins` les plugins voulus, au format
`<plugin>@kodflow`.

Pour un déploiement à l'échelle de l'organisation (enregistrement sans action de
l'utilisateur et auto-update imposé), la même structure va dans les *managed
settings* du poste avec `"autoUpdate": true` sur l'entrée de la marketplace.
Voir la section correspondante du [README](../README.md#déployer-la-marketplace-sur-un-projet-ou-une-équipe).
