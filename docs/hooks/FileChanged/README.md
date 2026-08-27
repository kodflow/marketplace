# FileChanged

Se déclenche quand un fichier surveillé change sur le disque, y compris
lorsqu'une modification vient de l'extérieur de la session.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `file_path` | chemin du fichier |
| `event` | `change`, `add`, `unlink` — **`event`, pas `change_type`, et pas `modified`/`created`/`deleted`** |

## Le matcher a un double rôle

C'est la particularité de cet événement :

1. **Il construit la liste de surveillance.** La valeur est découpée sur `|` et
   chaque segment devient un **nom de fichier littéral** du répertoire de
   travail. Les expressions régulières sont donc inutiles ici : un matcher
   `^\.env` surveillerait un fichier littéralement nommé `^\.env`.
2. **Il filtre les hooks à exécuter** quand un fichier surveillé change, selon
   les règles de matcher habituelles appliquées au nom de base.

Le jeu de correspondance stricte est plus étroit qu'ailleurs : lettres, chiffres,
`_` et `|` uniquement. Tout autre caractère bascule la valeur en expression
régulière.

Des chemins peuvent être ajoutés dynamiquement via `watchPaths`, émis par
[`SessionStart`](../SessionStart/), `CwdChanged` ou `FileChanged` lui-même.

## Décision

Pas de blocage : le fichier a déjà changé. `exit 2` affiche stderr à
l'utilisateur.

`watchPaths` met à jour la liste surveillée. `systemMessage` s'affiche comme
brève notification terminale et **n'atteint ni Claude ni le flux du SDK** ;
`continue` est jeté.

`$CLAUDE_ENV_FILE` est disponible ici.

## Ce qu'on peut y mettre

- **Signaler un changement de configuration d'environnement** : `.env`, `.envrc`,
  fichier de configuration d'un NF. Claude travaille sinon sur une vision périmée.
- **Recharger des variables d'environnement** via `$CLAUDE_ENV_FILE` quand le
  fichier source change.
- **Détecter une modification concurrente** : un fichier que la session vient
  d'éditer et qui change à nouveau depuis l'extérieur signale un conflit.

## Pièges

- **Ne pas mettre de regex dans le matcher** : ce sont des noms de fichiers
  littéraux.
- La surveillance porte sur le répertoire de travail : un fichier ailleurs doit
  passer par `watchPaths` en chemin absolu.
- Un fichier qui change souvent — journal, artefact de build — déclenche autant
  d'exécutions : ne surveiller que ce qui change rarement et compte vraiment.
