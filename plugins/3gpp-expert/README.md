# 3gpp-expert

Skill de connaissance 3GPP/télécom (2G à 6G, toutes releases, protocoles, architecture
réseau) avec récupération et cache local des specs ETSI, pour tout projet télécom de
l'équipe.

```
/plugin install 3gpp-expert@kodflow
```

## Contenu

| Fichier | Rôle |
| ------- | ---- |
| `skills/3gpp-expert/SKILL.md` | corps de la skill : réponse par domaine (releases, RAN, 5GC, features 5G, déploiement, 5G-Advanced/6G), et une méthodologie d'audit de conformité protocolaire (table walk littéral des IE/AVP, présence M/C/O, applicabilité par interface) |
| `skills/3gpp-expert/references/releases.md` | référence détaillée release par release, Phase 1 → Rel-21 |
| `skills/3gpp-expert/references/latest-version.py` | résout et met en cache la dernière version publiée d'une spec ETSI pour une release donnée |
| `skills/3gpp-expert/references/etsi-section.py` | télécharge (ou lit un PDF déjà en cache) et en extrait une section précise |

Le corps de `SKILL.md` (~20 Ko) n'est chargé que quand la skill se déclenche — seule sa
description de frontmatter est toujours en mémoire, donc l'installation n'a pas de coût de
contexte permanent.

Les deux scripts contournent le blocage `WebFetch` par le WAF Cloudflare d'ETSI
(anthropic/claude-code#22846) : `curl` avec un User-Agent de navigateur passe là où
`WebFetch` renvoie 403. Cache dans `~/.cache/3gpp-specs/`, partagé entre les deux scripts et
persistant d'une session à l'autre.

## Provenance et licence

`SKILL.md` et `references/releases.md` proviennent de
[github.com/lugasia/3gpp-skill](https://github.com/lugasia/3gpp-skill), sous licence MIT
(copyright lugasia, 2026 — texte complet dans
[`skills/3gpp-expert/LICENSE-UPSTREAM`](skills/3gpp-expert/LICENSE-UPSTREAM), vérifié
directement contre le `LICENSE` du dépôt amont). Ce plugin ne modifie pas ces deux fichiers.

`references/etsi-section.py` et `references/latest-version.py` **ne viennent pas** du dépôt
amont : ce sont des scripts ajoutés localement, écrits pour ce même besoin (récupération de
specs ETSI) mais indépendants du projet `lugasia/3gpp-skill`. Ils ne sont pas couverts par
la licence MIT ci-dessus.

## Coordination avec `go-review-panel`

La skill `review-mr` du plugin `go-review-panel` brief un sous-agent pour charger
cette skill par son nom (`3gpp-expert`), de façon conditionnelle : seulement quand le diff
touche du code protocolaire/télécom et que ce plugin est installé. Aucune configuration
supplémentaire n'est nécessaire des deux côtés — l'un cherche la skill par nom, l'autre la
fournit.

**Si vous aviez déjà cette skill en portée utilisateur** (`~/.claude/skills/3gpp-expert/`),
la retirer une fois ce plugin installé : la priorité entre une skill fournie par un plugin
et une skill de même nom en portée utilisateur n'est pas documentée par Claude Code, mieux
vaut ne pas avoir les deux copies en même temps.

## Tester en local

```
/plugin marketplace add ./
/plugin install 3gpp-expert@kodflow
/reload-plugins
```
