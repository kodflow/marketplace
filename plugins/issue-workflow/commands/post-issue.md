---
name: post-issue
description: Publier un draft d'issue (.drafts/*.md, format writing-rules) comme une vraie issue GitLab, par curl, après confirmation explicite.
argument-hint: "<chemin-du-draft> [labels séparés par des virgules...]"
allowed-tools: Bash, Read, Edit, Grep
---

# Post Issue

Publie un draft d'issue GitLab (format `writing-rules` : en-tête `# Issue #XXX : [Titre]`
suivi d'une section `## Vue d'Ensemble`) comme une vraie issue sur le projet courant.

**Prérequis** : le draft devrait avoir passé le gate de gel de `writing-rules` (§ « Before
Freezing an Issue ») avant d'être posté. Cette commande ne le vérifie pas elle-même, elle
publie ce qu'on lui donne.

Arguments (`$ARGUMENTS`) : le premier token est le chemin du fichier draft. Le reste,
optionnel, est une liste de labels séparés par des virgules à appliquer à l'issue créée.

## Pourquoi `curl` et pas le MCP

Le serveur MCP `gitlab` est en **lecture seule** chez Kodflow (`GITLAB_READ_ONLY_MODE=true`,
voir `.mcp.json` de ce plugin) : aucun outil de création d'issue n'y est exposé. La
publication passe par `curl`, exactement comme le fait la skill `review-mr` du plugin
`go-review-panel` pour ses commentaires de MR — même mécanisme, mêmes variables
d'environnement, pour éviter une deuxième convention de publication.

## 1. Résoudre le projet et le contenu

```bash
PROJECT_PATH=$(git remote get-url origin \
  | sed -E 's#^[a-z+]+://##; s#^[^@]+@##; s#^[^/:]+(:[0-9]+)?[/:]##; s#\.git$##')
PROJECT=$(python3 -c "import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1], safe=''))" "$PROJECT_PATH")
```

Retirer le schéma, l'utilisateur, l'hôte et le port, puis le `.git` final, et garder tout le
reste. Ne pas revenir à un `.*[:/]` en tête : il est gourmand, consomme jusqu'au dernier
séparateur qui laisse encore matcher la suite, et rend `kodflow/marketplace` là où le
projet est `kodflow/marketplace`. Tous les projets Kodflow sont rangés en
sous-groupes, donc le POST partirait en 404 partout.

Vérifier avant d'aller plus loin : `GET /projects/$PROJECT` doit rendre 200, et son
`path_with_namespace` doit être identique à `$PROJECT_PATH`.

Lire le draft. La première ligne `# Issue #XXX : [Titre]` donne le titre — poster
uniquement `[Titre]` comme `title` GitLab (GitLab affiche déjà son propre numéro, pas
besoin de le dupliquer dans le titre). Le reste du fichier, à partir de `## Vue d'Ensemble`,
devient la `description`.

Si le draft ne suit pas ce format (pas de `# Issue #XXX : [Titre]` en première ligne),
s'arrêter et le dire : cette commande ne devine pas un titre à la place de l'auteur.

## 2. Gate de confirmation

Afficher avant tout envoi, et ne rien poster sans confirmation explicite :

```
⏸  Publier une nouvelle issue sur kodflow/marketplace
   Titre : <titre>
   Labels : <labels, ou "aucun">
   Description : <N> lignes, aperçu des 5 premières :
     <ligne 1>
     ...

   [1] publier
   [2] dry-run (affiche le payload exact, n'envoie rien)
   [3] annuler
```

## 3. Publication

Auth par les mêmes variables d'environnement que le serveur MCP `gitlab` et que
`review-mr` : `GITLAB_API_URL`, `GITLAB_PERSONAL_ACCESS_TOKEN`. Le token ne sort jamais en
clair : pas d'`echo`, pas dans une URL, uniquement dans l'en-tête `PRIVATE-TOKEN`.

Si ces variables ne sont pas dans l'environnement, les lire depuis la configuration du serveur
MCP `gitlab`, sous `.mcpServers.gitlab.env` de `~/.claude.json` : c'est la même credential,
déclarée au même endroit. La lecture se fait en substitution de commande, sans affichage
intermédiaire. Même repli pour `NODE_EXTRA_CA_CERTS`. Sans lui, un shell qui n'exporte pas les
variables bloque la publication alors que la credential est là, à portée de lecture.

Si `curl` échoue sur une erreur de certificat, réessayer avec `--cacert "$NODE_EXTRA_CA_CERTS"`
si cette variable est définie.

```bash
curl -sS -X POST \
  --header "PRIVATE-TOKEN: $GITLAB_PERSONAL_ACCESS_TOKEN" \
  --data-urlencode "title=$TITLE" \
  --data-urlencode "description=$DESCRIPTION" \
  --data-urlencode "labels=$LABELS" \
  "$GITLAB_API_URL/projects/$PROJECT/issues"
```

Un `4xx` est définitif : afficher le corps de la réponse (il contient la raison, ex. label
inconnu) et s'arrêter. Une erreur de connexion (timeout, TLS) n'est pas définitive : la
signaler et proposer de réessayer, ne pas la confondre avec un rejet de l'API.

## 4. Après publication

Sur succès, GitLab renvoie l'objet issue créé, dont `iid` (numéro dans le projet) et
`web_url`. Annoncer les deux.

**Mettre à jour le draft local** : remplacer `# Issue #XXX : [Titre]` par
`# Issue #<iid> : [Titre]` dans le fichier, avec `Edit`. Si le nom de fichier du draft
portait un repère local (« draft NNN » au sens de `writing-rules`), le signaler à
l'utilisateur plutôt que renommer automatiquement : d'autres drafts peuvent référencer ce
« draft NNN » par ce nom (section « Out of scope / Deferred »), et un renommage silencieux
casserait ces renvois sans que personne ne le voie. Lister, par un `grep -rl "draft NNN"
.drafts/`, les fichiers qui référencent ce draft, et les montrer à l'utilisateur pour qu'il
décide de la mise à jour.

Ne jamais poster deux fois le même draft sans confirmation explicite : si le draft porte
déjà un numéro d'issue réel en en-tête (pas un repère local), le dire et demander avant de
créer un doublon.
