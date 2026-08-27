# go-review-panel

Panel de revue de merge request Go : trois agents complémentaires et une skill qui les
orchestre en threads GitLab prêts à coller.

```
/plugin install go-review-panel@kodflow
```

## Contenu

| Composant | Rôle |
| --------- | ---- |
| Agent `dogmatic-go-reviewer` | idiomatique Go, Go Proverbs, Uber Style Guide, sécurité |
| Agent `paranoid-perf-gopher` | performance, résilience, scalabilité — lit, benchmarke, profile ; n'édite pas le code |
| Agent `annoying-product-owner` | clarté du domaine métier, naming, qualité des tests (préfère les tests contre de vrais services aux mocks) |
| Skill `coding-style` | conventions de code Go Kodflow — godoc, layout `models.go`, logs zap, métriques Prometheus, gestion des erreurs |
| Skill `review-mr` | orchestre les trois agents en une revue de MR consolidée, dédupliquée, vérifiée, postée en threads GitLab |

## Utiliser `review-mr`

```
/go-review-panel:review-mr [MR-IID | <sha>..<sha> | <chemin>] [instructions...]
```

Isole la revue dans un worktree jetable, lance les trois agents en parallèle, déduplique
leurs findings par fusion, vérifie chaque finding contre le code réel (jamais un
`fichier:ligne` recopié tel quel d'un rapport d'agent), et écrit le résultat dans
`.drafts/`. La publication sur GitLab (draft notes) est une étape séparée, toujours
confirmée explicitement — voir le détail dans la skill elle-même.

Le serveur MCP `gitlab` étant en lecture seule chez Kodflow, la publication passe par
`curl`, authentifié via les variables d'environnement `GITLAB_API_URL` et
`GITLAB_PERSONAL_ACCESS_TOKEN` — les mêmes que le serveur MCP `gitlab` utilise. Ce plugin
ne prescrit pas comment les alimenter (export shell, gestionnaire de secrets, etc.), il
n'attend que ces deux noms de variable dans l'environnement.

## Dépendances optionnelles

`review-mr` délègue un audit 3GPP conditionnel, actif seulement si **les deux** tiennent :
le diff touche du code protocolaire/télécom et le plugin `3gpp-expert` est installé.
Sans lui, cette passe est simplement sautée — aucune action requise.

Si le plugin `issue-workflow` est installé, `review-mr` réutilise son découpage de
panel (`implement-issue`), sa table de jargon (`writing-rules`) et son ledger de suivi
d'issue (`.claude/progress/`) pour affiner la déduplication. Aucun des deux n'est requis
pour utiliser ce plugin seul.

`review-mr` charge aussi, s'ils existent dans le projet cible, sa propre skill/doc
d'architecture et une skill `neutrality-audit` — sans présumer de leur nom exact.

## Mémoire persistante des agents

Les trois agents déclarent `memory: user` et un chemin `~/.claude/agent-memory/<agent>/`
pour accumuler des connaissances spécifiques au projet d'une revue à l'autre. Le
comportement de cette mémoire pour un agent fourni par un plugin (par opposition à un
agent défini en portée utilisateur) n'est pas documenté par Claude Code au moment de la
rédaction de ce README — à vérifier en testant le plugin en local
(`/plugin marketplace add ./` puis `/plugin install go-review-panel@kodflow`).

## Tester en local

```
/plugin marketplace add ./
/plugin install go-review-panel@kodflow
/reload-plugins
```
