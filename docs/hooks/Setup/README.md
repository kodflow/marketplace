# Setup

Se déclenche uniquement sur `claude --init-only`, ou sur `--init` / `--maintenance`
combinés avec `-p`. **Il ne tire pas au démarrage normal d'une session** — c'est
[`SessionStart`](../SessionStart/) qui joue ce rôle.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `trigger` | `init` ou `maintenance` — **`trigger`, pas `setup_trigger`** |

Le `matcher` porte sur ce champ.

## Décision

Pas de blocage. Uniquement `hookSpecificOutput.additionalContext`. Les valeurs de
plusieurs hooks sont **concaténées**.

Contrairement à [`SessionStart`](../SessionStart/), **le stdout brut n'est pas
injecté** : il part au journal de debug. Seul `additionalContext` remonte.

Seuls les hooks de type `command` et `mcp_tool` sont supportés ici.

## Ce qu'on peut y mettre

- **Préparation de l'environnement** : installation de dépendances, génération de
  fichiers de configuration locaux, amorçage d'un environnement virtuel.
- **Vérification des prérequis** d'un projet Kodflow : présence des outils de
  build, accès au VPN, disponibilité d'un registre interne — et signalement du
  résultat en contexte.
- **Maintenance périodique** sur `trigger: "maintenance"` : purge de caches,
  rotation de journaux locaux.
- `$CLAUDE_ENV_FILE` est disponible ici : les variables persistées sont ensuite
  visibles des commandes Bash de la session.

## Pièges

- **Ne pas confondre avec `SessionStart`.** Un hook `Setup` qui suppose tirer à
  chaque session ne tirera en pratique presque jamais : il faut un
  `--init-only`, ou `--init`/`--maintenance` avec `-p`.
- L'installation de dépendances peut être longue : dimensionner le `timeout` en
  conséquence, et prévoir le cas où le réseau est indisponible.
