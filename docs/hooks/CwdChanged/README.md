# CwdChanged

Se déclenche quand le répertoire de travail de la session change.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `old_cwd` | répertoire précédent |
| `new_cwd` | nouveau répertoire |

Pas de `matcher`.

## Décision

Pas de blocage : le changement de répertoire a déjà eu lieu. `exit 2` affiche
stderr à l'utilisateur.

Deux champs sont lus : `watchPaths`, qui **redéfinit** la liste de surveillance
dynamique de [`FileChanged`](../FileChanged/) — un tableau vide la purge — et
`systemMessage`, affiché comme brève notification terminale. Ce message
**n'atteint ni Claude ni le flux de messages du SDK**. `continue` est jeté.

`$CLAUDE_ENV_FILE` est disponible ici : c'est ce qui rend l'événement utile.

## Ce qu'on peut y mettre

- **Recalculer les métadonnées liées au dépôt** — organisation, projet, branche —
  et les republier dans `$CLAUDE_ENV_FILE`. Sans cela, les valeurs mises en cache
  au démarrage deviennent fausses dès qu'on change de projet dans une même
  session, ce qui est fréquent en monorepo ou avec plusieurs dépôts ouverts.
- **Ajuster la liste des fichiers surveillés** via `watchPaths`, les chemins
  relatifs du nouveau répertoire n'étant plus les mêmes.
- **Signaler un changement de périmètre** : passer d'un projet en test à un projet
  en production mérite un rappel explicite.

## Pièges

- Ne pas supposer que `new_cwd` est un dépôt git.
- Le hook peut se déclencher souvent dans une session qui navigue entre
  répertoires : le garder rapide.
