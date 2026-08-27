# commit-guard

Impose la convention de commit Kodflow et refuse les messages portant une trace de
rédaction par un assistant de code.

```
/plugin install commit-guard@kodflow
```

## Ce que fait le hook

Un hook `PreToolUse` sur l'outil `Bash` inspecte chaque commande avant son
exécution. Il ne s'active que sur `git commit` et `git push` ; toute autre
commande ressort immédiatement.

| Situation | Décision | Ce que voit Claude |
| --------- | -------- | ------------------ |
| Marqueur de rédaction par IA dans le message | **refus** | le marqueur détecté et comment le supprimer |
| Message non conforme à la convention | **refus** | la liste des écarts et le gabarit attendu |
| `--no-verify` sur `commit` ou `push` | **refus** | pourquoi le contournement est refusé |
| `git commit` sans `-m`/`-F` (éditeur interactif) | **refus** | l'option à utiliser à la place |
| Tournures d'écriture automatique | avertissement | un rappel, sans blocage |
| Message conforme | rien | rien |

Le refus passe par `permissionDecision: "deny"`. C'est le seul canal de sortie
d'un hook `PreToolUse` que Claude lit réellement : sur `allow` et `ask`, la
raison va à l'utilisateur et jamais au modèle. Refuser est donc le seul moyen de
faire corriger le message plutôt que de simplement s'en plaindre.

## Marqueurs de rédaction par IA

Refus immédiat, sans configuration possible :

- trailer `Co-Authored-By` pointant l'adresse d'un assistant
  (`noreply@anthropic.com`, `cursoragent@cursor.com`, `copilot@github.com`,
  `noreply@openai.com`, comptes `[bot]@users.noreply.github.com`) ;
- trailer `Co-Authored-By` nommant un assistant, si l'adresse a été changée ;
- mention « Generated with &lt;outil&gt; » ;
- lien vers un assistant de code ;
- emoji robot en tête de ligne ;
- trailer de session d'agent (`Devin-Session-Id`, `Codex-Session-Id`, …) ;
- auto-déclaration « co-authored by AI ».

Ces motifs visent des **signatures d'outil**, jamais un mot du vocabulaire
métier. Le détecteur analyse le message reconstitué depuis `-m`, `-F` et, pour un
`--amend` sans message, le message du commit précédent — commentaires, blocs de
code et citations retirés au préalable.

Si l'attribution est ajoutée automatiquement, la couper à la source :

```json
{ "attribution": { "commit": "", "pr": "" } }
```

dans `settings.json`. Le réglage `includeCoAuthoredBy` est déprécié depuis la
v2.0.62 et ne doit pas être utilisé conjointement.

## Faux positifs : la contrainte de conception

En télécom, `phase`, `lot`, `batch`, `agent`, `orchestration`, `session` sont du
vocabulaire métier courant. **Aucun mot isolé n'est un marqueur.** Les motifs ne
capturent que des composés (`sous-agent`, `agent IA`), des mots ancrés en tête de
ligne suivis d'un chiffre (`Phase 2 :`), ou des syntagmes complets (`ce commit
met en œuvre`).

La suite de tests vérifie explicitement que ces messages passent sans bruit :

```
fix(x2): corriger le décalage de phase sur le lien PDH
feat(li): agent X1 conforme ETSI TS 103 221-1
perf(cdr): traitement par lot des CDR
fix(sip): corriger le user agent SIP tronqué
refactor(mano): simplifier orchestration des slices 5G
```

Les tournures d'écriture automatique — numérotation d'étapes, méta-discours,
sections de rapport, puces en gras, tableaux — sont des **heuristiques**, sans
statut de norme. Elles ne bloquent jamais et ne remontent qu'à partir de deux
familles distinctes.

## Convention appliquée

Voir [docs/commit-format.md](../../docs/commit-format.md) pour la convention
complète et sa justification. En résumé :

```
<type>(<scope>)[!]: <description à l'impératif, ≤ 72 car., sans point final>

<corps en prose, enveloppé à 72 colonnes : le problème, puis pourquoi
cette solution>

Fixes: <sha12> ("<sujet du commit fautif>")
Closes #NNN
```

Types acceptés : `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`,
`ci`, `revert`. `Merge`, `Revert "`, `fixup!` et `squash!` sont exemptés.

## Configuration par projet

Fichier optionnel `.claude/commit-guard.json` à la racine du dépôt :

```json
{
  "types": ["feat", "fix", "perf", "refactor", "docs", "test", "build", "ci", "revert"],
  "scopes": ["x1", "x2", "x3", "admf", "mdf2", "mdf3", "asn1"],
  "subject_max": 72,
  "body_max": 72,
  "check_convention": true,
  "check_style": true
}
```

| Clé | Effet |
| --- | ----- |
| `types` | liste fermée des types autorisés |
| `scopes` | liste fermée des scopes ; vide = tout scope accepté |
| `subject_max` | longueur maximale du sujet |
| `body_max` | largeur du corps ; `0` désactive le contrôle |
| `check_convention` | `false` désactive le contrôle de forme |
| `check_style` | `false` désactive les avertissements heuristiques |

La détection des marqueurs de rédaction par IA n'est pas désactivable par
configuration.

Exemptions ciblées dans `.claude/commit-guard-allow`, une expression régulière
par ligne, `#` pour un commentaire :

```
# Vocabulaire de recette interne
Phase [0-9]+ : recette
Lot [0-9]+ de qualification
```

Les lignes correspondantes sont retirées avant analyse.

## Tests

```bash
./tests/run-tests.sh
```

34 cas : marqueurs à bloquer, vocabulaire télécom à laisser passer, convention,
options git, portée du hook, robustesse. Toute évolution des motifs doit
s'accompagner d'un cas de test, en particulier d'un cas de faux positif.

## Portée et limites

- **C'est un lint de message de commit, pas un détecteur d'IA.** L'attribution
  étant configurable, le contrôle mesure la conformité à une convention
  d'écriture, pas la provenance réelle du code.
- **Un hook Claude Code ne voit qu'un chemin sur trois.** Il s'applique aux
  commandes passées par l'outil Bash ; un commit tapé à la main dans un terminal
  lui échappe, et le mode éditeur (`git commit` sans `-m`) est hors de sa portée
  puisque le message n'existe pas encore au moment où il s'exécute. La couverture
  complète demande trois couches :

  | Couche | Portée | Ce qu'elle rattrape |
  | ------ | ------ | ------------------- |
  | Ce plugin (`PreToolUse`) | commandes de Claude Code | avant exécution, avec correction immédiate par le modèle |
  | Hook git `commit-msg` | tous les commits du poste | le mode éditeur et les commits hors Claude Code |
  | Job CI sur `git log origin/master..HEAD` | tout ce qui est poussé | les postes non configurés |

  Le refus de `--no-verify` par ce plugin est ce qui empêche de court-circuiter
  la deuxième couche. Les deux se complètent : aucune ne suffit seule.
- **Fail-open assumé.** Absence de Python 3.8+, JSON illisible, erreur interne :
  le hook se tait et laisse passer. Un garde-fou cassé ne doit pas empêcher de
  travailler.
- **Le mode éditeur est refusé**, pas contourné : `git commit` sans `-m` ni `-F`
  attendrait un éditeur interactif que l'outil Bash ne peut pas servir, et la
  commande resterait figée jusqu'au timeout.
- Le matcher porte sur `Bash`. Sur un poste Windows sans Git Bash, Claude Code
  route les commandes par `PowerShell` et le hook ne se déclenche pas ; ajouter
  `Bash|PowerShell` au matcher si le cas se présente.

## Avant d'activer sur un dépôt existant

Passer l'historique au détecteur pour mesurer le bruit :

```bash
git log --format='%H%x00%B%x00' | ...   # un message par appel au détecteur
```

Tout marqueur de rédaction par IA trouvé sur des commits antérieurs à l'usage
d'assistants signale un motif trop large, à corriger avant activation.
