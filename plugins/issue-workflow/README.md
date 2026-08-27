# issue-workflow

Workflow d'issue GitLab de bout en bout : rédaction cadrée, implémentation pas à pas avec
gate de commit à chaque étape, publication.

```
/plugin install issue-workflow@kodflow
```

## Contenu

| Composant | Rôle |
| --------- | ---- |
| Skill `writing-rules` | conventions de rédaction des drafts d'issue sous `.drafts/` : en-tête « Vue d'Ensemble », section « Out of scope / Deferred » obligatoire, jargon technique non francisé, gate de cadrage avant gel |
| Skill `implement-issue` | implémente un draft pas à pas, un gate de commit par step, checkpoint/reprise sous `.claude/progress/` |
| Skill `pragmatic-coder` | posture d'implémentation : diffs minimaux, pas d'abstraction spéculative |
| Commande `/issue-workflow:post-issue` | publie un draft gelé comme une vraie issue GitLab, par `curl`, après confirmation explicite |
| `.mcp.json` | enregistre le serveur MCP `gitlab` (`@zereight/mcp-gitlab`), en lecture seule par défaut |

## Serveur MCP `gitlab` : contrat de variables d'environnement

Ce plugin enregistre le serveur MCP `gitlab`. Il ne fournit ni ne stocke aucun secret : il
attend trois variables d'environnement déjà présentes dans le shell qui lance Claude Code.

| Variable | Rôle | Obligatoire |
| -------- | ---- | ----------- |
| `GITLAB_PERSONAL_ACCESS_TOKEN` | jeton d'accès personnel GitLab | oui |
| `GITLAB_API_URL` | URL de l'API, ex. `https://gitlab.example.com/api/v4` | non, défaut `https://gitlab.example.com/api/v4` |
| `GITLAB_READ_ONLY_MODE` | désactive les outils d'écriture du MCP | non, défaut `true` (posture actuelle de l'organisation) |
| `NODE_EXTRA_CA_CERTS` | chemin vers une CA interne, si le poste ne la connaît pas déjà | non |

Comment alimenter `GITLAB_PERSONAL_ACCESS_TOKEN` (export dans le shell, gestionnaire de
secrets, dérivé d'un `~/.netrc` personnel) est un choix individuel : ce plugin ne
présume que du nom de la variable, jamais de sa source. La skill `review-mr` du plugin
`go-review-panel` et la commande `post-issue` de ce plugin lisent les mêmes
variables pour leurs appels `curl` (le serveur MCP est en lecture seule chez Kodflow, les
écritures passent par `curl`) : une seule configuration sert aux deux.

## Dépendance optionnelle

`implement-issue` et `pragmatic-coder` délèguent la revue de code et le style au panel du
plugin `go-review-panel` (agents `dogmatic-go-reviewer`, `annoying-product-owner`,
`paranoid-perf-gopher`, skill `coding-style`) quand il est installé. Sans lui, la revue se
fait inline, dans le même contexte, plutôt que d'être sautée.

`implement-issue` délègue en plus un audit 3GPP conditionnel, actif seulement si le diff
touche du code protocolaire/télécom et que le plugin `3gpp-expert` est installé.

## Tester en local

```
/plugin marketplace add ./
/plugin install issue-workflow@kodflow
/reload-plugins
```
