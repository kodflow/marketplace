# UserPromptSubmit

Se déclenche quand l'utilisateur valide un prompt, avant que Claude ne le
traite.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `prompt` | le texte soumis |

C'est le seul champ spécifique.

## Décision

| Sortie | Effet |
| ------ | ----- |
| `additionalContext` (dans `hookSpecificOutput`) | texte ajouté à côté du prompt |
| stdout brut | également ajouté comme contexte — cas rare, seuls trois événements le permettent |
| `decision: "block"` + `reason` (au niveau racine) | rejette le prompt **et l'efface du contexte** |
| `sessionTitle` | nomme la session automatiquement |

Attention à la répartition : `decision` et `reason` à la racine du JSON,
`additionalContext` et `sessionTitle` dans `hookSpecificOutput`.

Le prompt ne peut pas être **remplacé**, seulement complété ou rejeté.

## Ce qu'on peut y mettre

- **Injection d'état à chaque tour** : branche courante, ticket en cours,
  environnement ciblé, plan actif. Peu coûteux et très utile après une
  compaction, quand Claude a perdu le contexte de départ.
- **Réinitialisation des compteurs de session** : un nouveau prompt signifie
  qu'on n'est plus dans une boucle, c'est le bon endroit pour remettre à zéro le
  coupe-circuit d'un hook [`Stop`](../Stop/).
- **Détection d'un secret collé dans le prompt** : bloquer avant que la valeur
  n'entre dans le contexte et dans le transcript.
- **Nommage automatique de session** à partir du premier prompt.

## Pièges

- **Timeout par défaut abaissé à 30 s** sur cet événement, au lieu de 600.
- Un timeout jette la sortie, `additionalContext` compris : le prompt part sans
  le contexte, sans erreur visible autre qu'une notice.
- Rédiger `additionalContext` en **constat**, pas en instruction système : un
  texte formulé comme un ordre hors bande déclenche les défenses anti-injection
  et se retrouve affiché à l'utilisateur au lieu d'être exploité.
- Le contexte injecté est **enregistré dans le transcript** : à la reprise d'une
  session, c'est le texte sauvegardé qui est rejoué, pas le hook. Les valeurs
  volatiles (SHA, horodatage) deviennent périmées.
- Pour des consignes qui ne changent jamais, `CLAUDE.md` est préférable : il ne
  coûte aucune exécution de script.

## Exemple

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/etat.sh\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Branche courante : feat/x2-keepalive. Ticket associé : #482. Cible de déploiement : core100 (test)."
  }
}
```
