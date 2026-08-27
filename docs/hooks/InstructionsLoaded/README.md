# InstructionsLoaded

Se déclenche au chargement d'un fichier d'instructions — `CLAUDE.md`,
`.claude/rules/*.md` — au démarrage pour les fichiers chargés d'emblée, puis à
chaque chargement paresseux : `CLAUDE.md` imbriqué d'un sous-répertoire, règle
conditionnelle `paths:`.

**Le hook tourne de façon asynchrone**, l'événement étant conçu pour
l'observabilité.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `file_path` | chemin absolu du fichier chargé |
| `memory_type` | `User`, `Project`, `Local`, `Managed` |
| `load_reason` | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact` |
| `globs` | motifs du frontmatter `paths:`, uniquement pour un chargement `path_glob_match` |
| `trigger_file_path` | fichier dont l'accès a provoqué un chargement paresseux |
| `parent_file_path` | fichier parent, pour un chargement par `include` |

Le `matcher` porte sur `load_reason`.

## Décision

Aucune. Le code de sortie est ignoré, et le JSON — `systemMessage`, `continue` —
est jeté. L'événement ne peut ni bloquer ni modifier le chargement.

## Ce qu'on peut y mettre

- **Cartographier ce qui entre réellement en contexte** : quels `CLAUDE.md` sont
  chargés, depuis où, et pourquoi. Sur un dépôt avec plusieurs niveaux
  d'instructions, c'est le seul moyen de constater la hiérarchie effective plutôt
  que de la supposer.
- **Mesurer le coût des instructions** : taille cumulée des fichiers chargés par
  session. Un `CLAUDE.md` qui gonfle se paie à chaque tour.
- **Détecter les chargements inattendus** : un fichier d'instructions personnel
  qui s'applique à un dépôt d'équipe, un `include` qui tire une chaîne de
  fichiers plus longue que prévu.

## Pièges

- Purement observationnel : toute logique de décision écrite ici est sans effet.
- Le hook se déclenche potentiellement plusieurs fois par session, les
  chargements paresseux survenant au fil des accès aux fichiers.
