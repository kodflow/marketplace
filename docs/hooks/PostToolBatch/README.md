# PostToolBatch

Se déclenche après un lot d'appels d'outils exécutés dans le même tour, avant
l'appel suivant au modèle. Permet de raisonner sur l'ensemble plutôt que sur
chaque appel isolément.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `tool_calls` | tableau d'objets `{tool_name, tool_input, tool_use_id, tool_response}` |

**Différence de forme importante avec [`PostToolUse`](../PostToolUse/)** : ici
`tool_response` est le contenu sérialisé **tel que le modèle le voit** — pour un
`Read`, du texte préfixé de numéros de ligne, pas un objet structuré. Les
réponses peuvent être volumineuses : ne parser que ce dont on a besoin.

Pas de `matcher` sur cet événement.

## Décision

| Sortie | Effet |
| ------ | ----- |
| `additionalContext` | contexte ajouté à côté des résultats |
| `decision: "block"` ou `continue: false` | **arrête la boucle agentique** avant le prochain appel au modèle |
| `exit 2` | même effet de blocage, stderr servant de motif |

## Ce qu'on peut y mettre

- **Contexte déduit de l'ensemble du lot** : quand Claude vient de lire cinq
  fichiers d'un même module, rappeler la contrainte qui s'applique à ce module —
  ce qu'un hook par appel ne peut pas faire puisqu'il ne voit qu'un fichier.
- **Détection d'un motif de travail improductif** : relectures répétées des mêmes
  fichiers, exploration qui tourne en rond.
- **Garde-fou de volume** : arrêter une boucle qui enchaîne les appels sans
  progresser.

## Pièges

- Le payload peut être **très gros** : itérer sur `tool_calls` sans charger
  l'intégralité des réponses en mémoire.
- Bloquer ici interrompt le tour entier, pas un seul outil : effet plus brutal
  qu'un refus `PreToolUse`.
- Événement peu répandu : vérifier son comportement réel avant de bâtir une
  politique dessus.
