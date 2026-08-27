# Changelog

Historique des évolutions de la marketplace Kodflow.

Les plugins étant versionnés par le SHA du commit, ce fichier est purement
informatif : il ne conditionne pas la distribution. Ajouter une ligne à chaque
pull request qui touche un plugin ou le catalogue.

## Non publié

- Ajout du catalogue de binaires externes `tools/binaries.json` et de son
  moteur `tools/binaries.py` : pour chaque binaire de l'outillage (gopls,
  golangci-lint…), la source officielle est déclarée dans le catalogue et le
  moteur ne peut installer que depuis elle — releases GitHub du dépôt déclaré
  avec vérification `checksums.txt`, ou proxy Go officiel via `go install`.
  `status` compare l'installé à la dernière version officielle ; tout binaire
  remplacé est sauvegardé en `<nom>.previous`. L'étape 5 de `/project:init`
  pilote ce catalogue au lieu d'improviser des commandes d'installation.

- Ajout du plugin `project` : skill `init` qui initialise l'outillage
  Claude Code d'un projet en sept étapes affichées comme liste de tâches —
  analyse du projet, validation des suggestions, enregistrement de la
  marketplace, installation des plugins puis des binaires, écriture du
  `.claude/settings.json` versionné qui propage l'outillage à l'équipe, bilan.

- Fusion des deux skills `coding-style` en une seule, dans `go-review-panel` :
  SKILL.md court + un fichier `references/` par catégorie, chargés à la demande.
  Quatre contradictions de fond tranchées et documentées (labels Prometheus en
  snake_case, pas de préfixe `_Err`, doublons de logs avec exceptions, liste de
  préfixes ouverte), et les bugs des exemples hérités corrigés (conditions
  inversées, `zap.Error`, pointeurs `*os.PathError`).

## 2026-08-13

- Ajout du plugin `3gpp-expert` : skill de connaissance 3GPP/télécom et ses deux
  scripts de récupération/cache de specs ETSI. `SKILL.md` et
  `references/releases.md` proviennent de `github.com/lugasia/3gpp-skill`
  (MIT — attribution et licence conservées dans
  `skills/3gpp-expert/LICENSE-UPSTREAM`) ; les deux scripts sont des ajouts
  locaux, hors licence amont. Coordonné avec `review-mr` de `go-review-panel`,
  qui charge cette skill par son nom quand elle est installée et que le diff
  touche du code protocolaire.

- Ajout du plugin `issue-workflow` : skills `writing-rules` (conventions de
  rédaction des drafts d'issue), `implement-issue` (implémentation pas à pas
  avec gate de commit et checkpoint de reprise) et `pragmatic-coder` (posture
  d'implémentation minimaliste). Ajoute une commande `post-issue` qui publie un
  draft gelé par `curl` lorsque le serveur MCP est en lecture seule, et un
  `.mcp.json` qui enregistre ce serveur avec ses variables d'environnement en
  placeholders (`GITLAB_API_URL`, `GITLAB_PERSONAL_ACCESS_TOKEN`,
  `GITLAB_READ_ONLY_MODE`), jamais de valeur en dur.

- Ajout du plugin `go-review-panel` : trois agents de revue Go
  (`dogmatic-go-reviewer`, `paranoid-perf-gopher`, `annoying-product-owner`) et
  une skill `review-mr` qui les orchestre en threads prêts à coller, plus la
  skill `coding-style`. L'audit 3GPP de `review-mr` est une passe
  conditionnelle, activée si le plugin `3gpp-expert` est installé et que le diff
  touche du code protocolaire.

- Ajout du plugin `commit-guard` : hook `PreToolUse` qui refuse les messages de
  commit portant une trace de rédaction par IA, impose la convention de commit
  et refuse `--no-verify` ; skill `commit` associée.

- Ajout de `docs/hooks/` : une fiche par événement de hook Claude Code (31),
  avec usages pertinents et pièges.

- Ajout de `docs/commit-format.md` : convention de commit et ses sources.

- `commit-guard` : lecture du message repris par `-C`, `--reuse-message`,
  `--fixup` et `--squash`, qui échappait jusque-là au contrôle.

- `docs/hooks/` : ajout des champs communs du payload, de l'avertissement sur le
  champ `if` — non évalué hors des cinq événements outil, où le hook ne tire
  alors jamais — et correction de `Setup`, `DirectoryAdded`, `WorktreeCreate`,
  `ConfigChange`, `PermissionRequest` et `PermissionDenied`.

## 2026-08-12

- Initialisation de la marketplace `kodflow` (`.claude-plugin/marketplace.json`).
- Ajout du plugin `devkit` (skill `new-plugin`).
- Ajout du squelette `templates/plugin-template`.
- Ajout de `scripts/validate.sh` et de la CI.
- Documentation : installation, mise à jour, propagation (`README.md`),
  contribution (`CONTRIBUTING.md`).
