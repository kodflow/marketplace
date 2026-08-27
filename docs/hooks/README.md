# Catalogue des hooks Claude Code — Kodflow

Un hook est un script (ou un appel HTTP, ou un prompt) que Claude Code exécute
automatiquement à un moment précis de son cycle de vie. C'est le seul mécanisme
qui permet d'**imposer** une règle plutôt que de la suggérer : un fichier
`CLAUDE.md` demande, un hook empêche.

Ce catalogue contient **un dossier par événement de hook**. Chaque fiche décrit
ce que l'événement permet réellement de faire, et ce qu'il est pertinent d'y
mettre chez Kodflow.

- Source de vérité : <https://code.claude.com/docs/en/hooks>
  (attention : `/docs/en/hooks-reference` renvoie **404**, la page de référence
  est bien `/docs/en/hooks`)
- Hooks embarqués dans un plugin : `hooks/hooks.json` à la racine du plugin,
  jamais dans `.claude-plugin/`. Voir [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Les 31 événements

Colonne « Bloque » : ce que fait un `exit 2` (verbatim de la doc officielle).
Colonne « Contexte » : l'événement accepte-t-il `additionalContext`, c'est-à-dire
peut-il injecter du texte que Claude lira.

| Événement | Bloque (`exit 2`) | Contexte | Fiche |
| --------- | ----------------- | :------: | ----- |
| `PreToolUse` | oui — bloque l'appel d'outil | oui | [fiche](PreToolUse/) |
| `PermissionRequest` | **non** — `exit 2` non honoré, refuser via `decision.behavior` | non | [fiche](PermissionRequest/) |
| `PermissionDenied` | non — le refus a déjà eu lieu | non | [fiche](PermissionDenied/) |
| `PostToolUse` | non — montre stderr à Claude, l'outil a déjà tourné | oui | [fiche](PostToolUse/) |
| `PostToolUseFailure` | non — montre stderr à Claude | oui | [fiche](PostToolUseFailure/) |
| `PostToolBatch` | oui — arrête la boucle agentique | oui | [fiche](PostToolBatch/) |
| `UserPromptSubmit` | oui — rejette le prompt et l'efface | oui | [fiche](UserPromptSubmit/) |
| `UserPromptExpansion` | oui — bloque l'expansion | oui | [fiche](UserPromptExpansion/) |
| `SessionStart` | non — stderr montré à l'utilisateur | oui | [fiche](SessionStart/) |
| `Setup` | non — stderr montré à l'utilisateur | oui | [fiche](Setup/) |
| `SessionEnd` | non — stderr montré à l'utilisateur | non | [fiche](SessionEnd/) |
| `Stop` | oui — empêche Claude de s'arrêter | oui | [fiche](Stop/) |
| `StopFailure` | non — sortie et code ignorés | non | [fiche](StopFailure/) |
| `SubagentStart` | non — stderr montré à l'utilisateur | oui | [fiche](SubagentStart/) |
| `SubagentStop` | oui — empêche le sous-agent de s'arrêter | oui | [fiche](SubagentStop/) |
| `TaskCreated` | oui — annule la création de tâche | non | [fiche](TaskCreated/) |
| `TaskCompleted` | oui — empêche le passage en terminé | non | [fiche](TaskCompleted/) |
| `TeammateIdle` | oui — empêche la mise en veille | non | [fiche](TeammateIdle/) |
| `PreCompact` | oui — bloque la compaction | non | [fiche](PreCompact/) |
| `PostCompact` | non — stderr montré à l'utilisateur | non | [fiche](PostCompact/) |
| `ConfigChange` | oui — bloque le changement (sauf `policy_settings`) | non | [fiche](ConfigChange/) |
| `Notification` | non — code et stderr ignorés | non | [fiche](Notification/) |
| `MessageDisplay` | non — le texte d'origine est affiché | non | [fiche](MessageDisplay/) |
| `InstructionsLoaded` | non — code de sortie ignoré | non | [fiche](InstructionsLoaded/) |
| `CwdChanged` | non — stderr montré à l'utilisateur | non | [fiche](CwdChanged/) |
| `DirectoryAdded` | non — stderr en debug uniquement | non | [fiche](DirectoryAdded/) |
| `FileChanged` | non — stderr montré à l'utilisateur | non | [fiche](FileChanged/) |
| `WorktreeCreate` | oui — **tout** code non nul fait échouer la création | non | [fiche](WorktreeCreate/) |
| `WorktreeRemove` | non — échecs journalisés en debug | non | [fiche](WorktreeRemove/) |
| `Elicitation` | oui — refuse la sollicitation | non | [fiche](Elicitation/) |
| `ElicitationResult` | oui — bloque la réponse (devient un refus) | non | [fiche](ElicitationResult/) |

Les 11 événements qui acceptent `additionalContext` sont, verbatim :
`SessionStart`, `Setup`, `SubagentStart`, `UserPromptSubmit`,
`UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
`PostToolBatch`, `Stop`, `SubagentStop`.

## Champs communs du payload

Tout hook reçoit ces champs, en plus de ceux propres à son événement. Sur un
hook `command` ils arrivent en JSON sur stdin ; sur un hook `http`, dans le corps
de la requête POST.

| Champ | Type | Contenu |
| ----- | ---- | ------- |
| `session_id` | string | Identifiant de la session |
| `prompt_id` | string (UUID) | UUID du prompt en cours. Correspond à l'attribut OpenTelemetry `prompt.id`, ce qui permet de corréler hook et télémétrie. **Absent tant qu'aucune entrée utilisateur n'a eu lieu** |
| `transcript_path` | string | Chemin du JSON de conversation. **Écrit de façon asynchrone : il peut être en retard** sur la conversation en mémoire et ne pas contenir les derniers messages du tour |
| `cwd` | string | Répertoire de travail au moment de l'invocation |
| `permission_mode` | string | `default`, `plan`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`. Le mode affiché **Manual** arrive comme `default`, jamais `manual`. **Tous les événements ne le reçoivent pas** |
| `effort` | object | `{"level": "low"\|"medium"\|"high"\|"xhigh"\|"max"}` — le niveau réellement utilisé, éventuellement rétrogradé. Présent sur les événements liés à un usage d'outil. Aussi exposé en `$CLAUDE_EFFORT` |
| `hook_event_name` | string | Nom de l'événement |

Deux champs supplémentaires sous `--agent` ou à l'intérieur d'un sous-agent :

| Champ | Contenu |
| ----- | ------- |
| `agent_id` | Identifiant du sous-agent. Présent **uniquement** dans un sous-agent : c'est le moyen de distinguer un appel de sous-agent d'un appel du fil principal |
| `agent_type` | Nom de l'agent. Pour un sous-agent, son type prime sur la valeur `--agent` de la session |

`permission_mode` **est absent** des exemples officiels de `SessionStart`,
`Setup`, `InstructionsLoaded`, `Notification`, `MessageDisplay`,
`SubagentStart`, `StopFailure`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`,
`FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`
et `SessionEnd`. La documentation ne publie pas de liste normative : elle renvoie
à l'exemple JSON de chaque section.

Seul `SessionStart` peut recevoir un champ `model`, et sa présence n'est pas
garantie. **Il n'existe pas de variable `$CLAUDE_MODEL`.**

`$CLAUDE_ENV_FILE` — où persister des `export` pour les commandes Bash suivantes
— n'est disponible que sur **quatre** événements : `SessionStart`, `Setup`,
`CwdChanged`, `FileChanged`.

Claude Code retire les variables `OTEL_*` de tout sous-processus qu'il lance,
hooks compris.

## Les sept règles à connaître avant d'écrire un hook

1. **`exit 2` est le seul code qui bloque.** `exit 1` est traité comme une erreur
   non bloquante et l'action passe quand même. Trois exceptions :
   `WorktreeCreate` échoue sur **tout** code non nul ; `PermissionRequest`
   n'honore pas `exit 2` du tout ; sur `Elicitation` et `ElicitationResult`, un
   `exit 2` fait **ignorer** le `hookSpecificOutput` du hook.
   À l'inverse, Claude Code lit le JSON de stdout sur **tous** les codes de
   sortie : quand le code n'est ni 0 ni 2, un JSON valide décide seul. Le blocage
   d'`exit 2` est la seule chose que le JSON ne peut pas annuler.
2. **Un timeout ne bloque pas** — le hook est annulé, sa sortie jetée, et
   l'action continue. Un garde-fou qui dépasse son `timeout` s'ouvre en grand.
3. **`permissionDecisionReason` n'atteint Claude que sur `"deny"`.** Sur
   `"allow"` et `"ask"`, le texte va à l'utilisateur, pas au modèle. Pour faire
   corriger Claude, il faut refuser.
4. **Un seul producteur de JSON par chaîne** : quand plusieurs hooks du même
   événement écrivent du JSON, le dernier écrase les précédents — un
   `decision: "block"` peut disparaître silencieusement.
5. **Tout hook capable de bloquer a besoin d'un coupe-circuit.** Un hook `Stop`
   qui bloque relance Claude, qui re-déclenche le hook : compteur péremptible
   obligatoire, remis à zéro au prompt suivant.
6. **Les hooks async ne peuvent rien bloquer** : `decision`, `permissionDecision`
   et `continue` y sont sans effet, l'action est déjà terminée.
7. **`additionalContext` se rédige en constat, pas en ordre.** « La cible de
   déploiement est la production » passe ; un texte formulé comme une instruction
   système hors bande déclenche les défenses anti-injection de Claude, qui
   remonte alors le texte à l'utilisateur au lieu de le traiter.

## Anatomie d'un hook

```jsonc
{
  "description": "À quoi sert ce fichier",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",                       // sur quels outils
        "hooks": [
          {
            "type": "command",                   // command | http | mcp_tool | prompt | agent
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/garde.sh\"",
            "if": "Bash(git commit:*)",         // voir l'avertissement ci-dessous
            "timeout": 15,
            "statusMessage": "Vérification..."
          }
        ]
      }
    ]
  }
}
```

Entrée : un objet JSON sur stdin. Sortie : rien, ou **un seul** objet JSON sur
stdout. Code de sortie : `0` (rien à signaler), `2` (blocage).

**Le champ `if` n'est évalué que sur cinq événements** : `PreToolUse`,
`PostToolUse`, `PostToolUseFailure`, `PermissionRequest` et `PermissionDenied`.
Partout ailleurs, un hook portant un `if` **ne s'exécute jamais** — il n'est pas
« ignoré », il ne tire pas du tout. C'est une cause de hook silencieusement mort
difficile à diagnostiquer.

Même sur ces cinq événements, `if` est un filtre **best-effort qui s'ouvre en
grand** quand la commande ne peut pas être analysée : commode pour éviter du
travail inutile, jamais suffisant comme barrière. Il n'accepte qu'une règle —
ni `&&`, ni `||`, ni liste.

## Conventions Kodflow

- **Fail-open par défaut.** `exit 0` en cas d'erreur interne, de dépendance
  absente ou de JSON illisible. Un hook cassé ne doit jamais empêcher de
  travailler. On ne bloque que délibérément.
- **Vérifier ses dépendances** (`command -v jq`) et se dégrader en silence.
- **Sortie rapide en tête de script** : filtrer le cas non concerné avant tout
  travail coûteux — un hook `PreToolUse`/`Bash` s'exécute à chaque commande.
- **Ne jamais journaliser de contenu de fichier ni de secret** : chemins,
  longueurs et commandes caviardées suffisent.
- **`${CLAUDE_PLUGIN_ROOT}` est éphémère** (il change à chaque mise à jour du
  plugin) : l'état persistant va dans `${CLAUDE_PLUGIN_DATA}`.
- **Invoquer l'interpréteur explicitement** (`bash "…/x.sh"`) plutôt que de
  compter sur le bit exécutable.

## Ce qui est implémenté chez Kodflow

| Plugin | Événements utilisés |
| ------ | ------------------- |
| [`commit-guard`](../../plugins/commit-guard/) | `PreToolUse` (Bash) |

Chaque fiche liste des idées d'usage non encore implémentées. Un plugin qui
couvre l'une d'elles est le bienvenu : voir [CONTRIBUTING.md](../../CONTRIBUTING.md).
