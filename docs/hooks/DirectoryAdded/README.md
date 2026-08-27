# DirectoryAdded

Se déclenche quand un répertoire est ajouté au périmètre de travail de la
session.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `directory` | chemin du répertoire ajouté — **`directory`, pas `directory_path`** |
| `source` | `slash_command` (`/add-dir`) ou `register_repo_root` (requête du SDK) |

Le `matcher` porte sur `source`.

> La documentation est contradictoire sur ce point : le tableau des matchers
> liste `DirectoryAdded` parmi les événements sans matcher, mais sa section
> dédiée détaille les deux valeurs ci-dessus. La section dédiée fait foi.

**Ne se déclenche pas** pour le drapeau de démarrage `--add-dir`, ni depuis
l'onglet Workspace de `/permissions`, ni pour un répertoire déjà présent. Claude
Code n'attend pas le hook : l'ajout est immédiat et le hook tourne en arrière-plan.

## Décision

Pas de blocage : le répertoire est déjà ajouté quand le hook se déclenche, et
`exit 2` n'envoie stderr qu'au journal de debug.

**Mais il existe un canal d'injection, par une voie atypique** : sur
`source: "slash_command"`, le `systemMessage` du hook est délivré **à Claude
comme contexte au tour suivant**, au lieu d'être affiché à l'utilisateur. C'est
le seul événement où `systemMessage` se comporte ainsi.

Sur `source: "register_repo_root"`, `systemMessage` part au journal de debug.
`continue` est jeté dans les deux cas.

## Ce qu'on peut y mettre

- **Trace d'audit de l'élargissement du périmètre** : savoir quand une session a
  gagné l'accès à un répertoire extérieur au projet, et lequel. C'est un
  changement de surface d'exposition qui mérite une trace.
- **Alerte sur un répertoire sensible** : ajout d'un chemin contenant des
  secrets, une configuration de production ou un dépôt sans rapport avec le
  travail en cours.
- **Signaler à Claude les conventions du nouveau répertoire** via
  `systemMessage`, en profitant du canal décrit ci-dessus : un dépôt ajouté en
  cours de session a ses propres règles, que Claude n'a aucun moyen de connaître
  autrement.

## Pièges

- L'ajout ne peut pas être empêché : c'est un capteur, pas une barrière. Pour
  restreindre les répertoires accessibles, passer par les règles de permissions.
- Le canal `systemMessage` → contexte ne vaut que pour `slash_command` : un hook
  qui compte dessus est silencieux sur `register_repo_root`.
- stderr n'est visible qu'en mode debug : journaliser dans un fichier si la trace
  doit être exploitable.
