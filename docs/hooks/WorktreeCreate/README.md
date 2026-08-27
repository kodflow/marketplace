# WorktreeCreate

Se déclenche à la création d'un worktree git. **Le hook est responsable de créer
le worktree et d'en renvoyer le chemin.**

## Payload

| Champ | Contenu |
| ----- | ------- |
| `name` | slug du worktree, fourni par l'utilisateur ou généré (`bold-oak-a3f2`) |

C'est le **seul** champ spécifique : ni `repository_path`, ni `worktree_path` en
entrée. Pas de `matcher`.

## Décision

Cet événement sort du modèle habituel :

- un hook `command` **imprime le chemin du worktree comme dernière ligne non vide
  de stdout** — les codes ANSI sont retirés. Il ne peut donc renvoyer aucun JSON,
  sa sortie standard étant lue comme un chemin ;
- un hook `http` renvoie `hookSpecificOutput.worktreePath` ;
- **tout code de sortie non nul fait échouer la création** — pas seulement `2` ;
- un chemin contenant `.` ou `..`, ou traversant un lien symbolique sous la
  racine du dépôt, est refusé ;
- `systemMessage` et `continue` sont jetés.

> **Configurer ce hook remplace entièrement le comportement git par défaut.**
> `.worktreeinclude` n'est alors plus traité : si le dépôt s'en sert, le hook
> doit reprendre ce travail à son compte.

## Ce qu'on peut y mettre

- **Amorçage d'un worktree neuf** : copie des fichiers de configuration locaux
  non versionnés, installation des dépendances, mise en place des hooks git,
  liens vers les caches de build. Un worktree fraîchement créé est inutilisable
  tant que ce travail n'est pas fait, et le faire ici évite de le redécouvrir à
  chaque fois.
- **Politique de nommage** : refuser un nom hors convention, en sortant non nul.
- **Emplacement imposé** : créer le worktree sous un répertoire choisi plutôt
  qu'à l'emplacement par défaut.
- **`git fetch` préalable** pour partir d'une base à jour.

## Pièges

- **Rien d'autre que le chemin en dernière ligne de stdout.** Toute trace de
  diagnostic part sur stderr : une ligne surnuméraire imprimée après le chemin
  devient le chemin.
- **`.worktreeinclude` cesse d'être traité** dès qu'un hook est configuré.
- **Tout code non nul fait échouer** : un `set -e` mal placé casse la création.
- Assainir le `name` avant de l'utiliser dans un chemin : c'est une entrée
  utilisateur.
- Prévoir le cas où le répertoire cible existe déjà, et celui d'un
  `.git/index.lock` périmé.
