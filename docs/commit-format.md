# Convention de commit Kodflow

Format retenu : **en-tête Conventional Commits, corps aux règles git, trailers
du noyau Linux et de GitLab.** Ce document dit ce qui est *spécifié* par une
norme et ce qui relève de l'*usage* : la distinction compte quand on arbitre.

Le plugin [`commit-guard`](../plugins/commit-guard/) applique cette
convention automatiquement.

## Gabarit

```
<type>(<scope>)[!]: <description à l'impératif, ≤ 72 caractères, sans point final>

<Corps en prose, enveloppé à 72 colonnes.
Paragraphe 1 : quel est le problème, au présent.
Paragraphe 2 : ce que fait le changement et pourquoi cette solution.
Pas le « comment » : le diff s'en charge.>

<BREAKING CHANGE: ... si applicable>

<bloc de trailers, en dernier, précédé d'une ligne vide>
```

## Types

Liste fermée : `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`,
`revert`.

Seuls `feat` et `fix` sont définis par la spécification Conventional Commits ;
les autres sont une recommandation, reprise de la convention Angular. `chore` et
`style` sont volontairement **exclus** : `chore` est un fourre-tout absent de la
spécification comme de la liste Angular, et le formatage est de toute façon
automatisé par `clang-format` et `gofmt`.

`feat` correspond à un `MINOR` SemVer, `fix` à un `PATCH`, et tout
`BREAKING CHANGE` à un `MAJOR`, quel que soit le type.

## Scope

Le composant ou l'interface concernée : `x1`, `x2`, `x3`, `admf`, `mdf2`,
`mdf3`, `asn1`, `netconf`… Un scope par commit. La liste peut être fermée par
projet dans `.claude/commit-guard.json`, ce qui la rend vérifiable.

## Sujet

- **≤ 72 caractères.** Les chiffres varient selon les sources : la page de manuel
  `git-commit` recommande 50 en précisant « though not required », le noyau Linux
  impose 70-75. Il n'existe pas de norme unique ; 72 est le compromis retenu.
- **Mode impératif.** Test de validation : « Si appliqué, ce commit va
  *&lt;sujet&gt;* ». C'est ce que prescrit `Documentation/SubmittingPatches` du
  dépôt git, et ce que git lui-même produit pour ses commits automatiques.
- **Pas de point final.**
- **Casse de la description non contrainte.** Chris Beams recommande la
  majuscule, le projet git demande l'inverse après un préfixe de zone : les deux
  sources se contredisent, donc la règle n'est pas imposée. Les sigles gardent
  naturellement leur casse (`ETSI`, `X1`, `PDU`).

## Corps

- **Enveloppé à 72 colonnes.** git n'enveloppe jamais le texte automatiquement et
  l'indente de 4 espaces à l'affichage : 72 colonnes gardent `git log` lisible
  dans un terminal de 80, ce qui compte quand on lit un historique en SSH sur un
  équipement.
- **Le quoi et le pourquoi, jamais le comment.** Le code documente le comment.
- **Décrire le problème au présent** : « le dispatch déréférence un pointeur
  nul », pas « le dispatch déréférençait ». Ne pas supposer que le relecteur
  connaît le contexte d'origine.
- **Prose plutôt que puces.** Aucune norme ne prescrit ni n'interdit les listes —
  la seule source qui les aborde (Chris Beams) les autorise. Le choix Kodflow est
  la prose, parce qu'une liste exprime mal la causalité, qui est précisément ce
  que le corps doit transmettre. Une liste se justifie pour énumérer des éléments
  réellement indépendants : plateformes testées, paramètres ajoutés, fichiers
  migrés. Un commit qui a besoin de cinq puces sans lien entre elles devrait être
  cinq commits.

## Trailers

Un trailer est une ligne `Clé: valeur`, en **bloc final**, précédée d'une ligne
vide. Une seule ligne non-trailer glissée dans ce bloc et git cesse de le
reconnaître : le bloc doit être propre et en dernier.

| Trailer | Statut | Usage |
| ------- | ------ | ----- |
| `Fixes: <sha12> ("<sujet>")` | spécifié par le noyau Linux | Réfère le **commit** qui a introduit la régression |
| `Closes #NNN` | spécifié par GitLab | Ferme une issue. Ne prend effet que vers la branche par défaut |
| `Refs: #NNN` | usage, non spécifié | Référence sans fermer |
| `Reviewed-by: Nom <email>` | spécifié (kernel) | Revue technique approfondie, qui engage le relecteur |
| `Tested-by: Nom <email>` | spécifié (kernel) | Validation sur banc ou plateforme réelle — préciser laquelle dans le corps |
| `Co-authored-by: Nom <email>` | spécifié (GitHub, reconnu GitLab) | Binômage. **Jamais vers un assistant de code** |
| `Signed-off-by: Nom <email>` | spécifié (DCO) | Uniquement si l'équipe adopte le DCO. Un trailer posé mécaniquement sans processus derrière ne certifie rien |

### Référencer un commit fautif

Convention du noyau Linux : SHA abrégé à **au moins 12 caractères**, puis le
sujet du commit entre guillemets droits dans des parenthèses, sans point final.

```
Fixes: 54a4f0239f2e ("x1: refactorer le parseur de requêtes ETSI")
```

La ligne n'est jamais coupée, même au-delà de 72 colonnes.

Configuration qui produit la ligne directement :

```bash
git config --global core.abbrev 12
git config --global pretty.fixes 'Fixes: %h ("%s")'
git log -1 --pretty=fixes <sha>     # copier-coller le résultat
```

Cette traçabilité est directement exploitable en télécom : `git log --grep="^Fixes: <sha>"`
donne l'historique des correctifs d'un commit donné, ce qui décide des backports
sur les branches de release déployées chez les opérateurs.

### `Fixes:` contre `Fixes #123`

GitLab ferme une issue sur les mots-clés `Close(s|d)`, `Fix(es|ed)`,
`Resolve(s|d)`, `Implement(s|ed)` suivis d'une référence d'issue. Un SHA
hexadécimal ne correspond à aucune des formes de référence acceptées, donc un
`Fixes: <sha> ("sujet")` ne devrait pas fermer d'issue par accident — cela reste
une lecture de l'expression régulière publiée, pas un test sur l'instance.

Pour lever toute ambiguïté, la règle Kodflow est stricte :

- `Fixes:` → **uniquement** un commit fautif ;
- `Closes #NNN` → **uniquement** une issue GitLab ;
- `Refs: #NNN` → référence sans fermeture.

## Changement cassant

Deux formes équivalentes selon la spécification : un `!` avant les deux-points
dans l'en-tête, ou un footer `BREAKING CHANGE:`. Kodflow utilise **les deux** : le
`!` rend la rupture visible dans `git log --oneline`, le footer porte les
instructions de migration. `BREAKING CHANGE` est le seul élément de la
spécification sensible à la casse — il doit être en majuscules.

## Revert

`git revert` produit `This reverts commit <sha 40 caractères>.` Conserver cette
ligne, ajouter la raison — la documentation git le recommande explicitement — et
un `Fixes:`, puisqu'un revert est une correction d'un commit identifié.

## Exemples

### Fonctionnalité

```
feat(x2): émettre un keep-alive applicatif sur la session X2

Le MDF2 ferme la session TCP après 60 s sans trafic. Sur les
interceptions à faible débit, la session est donc rétablie à chaque
PDU, ce qui ajoute une latence de reconnexion et provoque des pertes
lorsque le rétablissement échoue.

Un keep-alive applicatif est émis toutes les 30 s conformément à
ETSI TS 103 221-2. La période est configurable via x2.keepalive_sec,
la valeur 0 désactivant le mécanisme pour les MDF2 qui ne le
supportent pas.

Closes #482
Tested-by: Prénom Nom <dev@example.com>
```

### Correction d'une régression

```
fix(x1): rejeter les ActivateTask sans XID au lieu de paniquer

Depuis la refonte du parseur X1, une requête ActivateTask dépourvue
du champ XID franchit la validation. Le dispatch déréférence alors un
pointeur nul dans handleActivate(), ce qui fait tomber le processus
ADMF et interrompt toutes les interceptions actives.

Valider la présence du XID avant le dispatch et répondre par une
ErrorResponse ETSI plutôt que d'échouer tardivement : la conformité
impose une réponse au demandeur, y compris sur requête malformée.

Fixes: 3f2a1b9c4d5e ("x1: refactorer le parseur de requêtes ETSI")
Closes #517
Reviewed-by: Prénom Nom <dev@example.com>
```

### Changement cassant

```
feat(li-core)!: charger la configuration des NF depuis un YAML unique

Chaque NF lit aujourd'hui son propre fichier INI. Les paramètres
réseau communs y sont dupliqués, et une divergence entre deux
fichiers produit un déploiement incohérent qui ne se manifeste qu'à
l'exécution.

La configuration est désormais chargée depuis un unique li.yaml
contenant une section par NF, validé au démarrage contre un schéma.
Une divergence devient impossible par construction.

BREAKING CHANGE: les fichiers /etc/kodflow/*.ini ne sont plus lus. Les
migrer avant déploiement avec
`kodflowctl config migrate --from /etc/kodflow --to /etc/kodflow/li.yaml`.
Le démarrage échoue si li.yaml est absent.

Refs: #530
```

## Ce qui n'a pas sa place dans un message de commit

- Toute mention d'un assistant de code : trailer `Co-Authored-By` vers un outil,
  « Generated with », emoji robot, lien vers un assistant.
- Le vocabulaire d'orchestration du travail : « Phase 2 », « Lot 3 »,
  « étape 1/3 », « comme demandé ».
- Le méta-discours : « ce commit met en œuvre les modifications demandées »,
  « voir analyse ci-dessus ».
- La mise en forme de rapport : sections « Résumé » / « Test plan », tableaux,
  puces en gras — redondantes avec le diff et illisibles dans `git log`.
- La première personne : le sujet est à l'impératif.

## Sources

- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Angular — Commit Message Guidelines](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md)
- [git-commit](https://git-scm.com/docs/git-commit) · [SubmittingPatches](https://github.com/git/git/blob/master/Documentation/SubmittingPatches) · [git-interpret-trailers](https://git-scm.com/docs/git-interpret-trailers) · [git-revert](https://git-scm.com/docs/git-revert)
- [Linux kernel — Submitting patches](https://docs.kernel.org/process/submitting-patches.html)
- [Chris Beams — How to Write a Git Commit Message](https://cbea.ms/git-commit/)
- [GitLab — Managing issues](https://docs.gitlab.com/user/project/issues/managing_issues/)
