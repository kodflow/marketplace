# SessionEnd

Se déclenche à la fin d'une session.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `reason` | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |

**`reason`, pas `end_reason`. Il n'existe pas de champ `exit_code`.**
Le `matcher` porte sur ce champ.

## Décision

Aucune. L'événement sert aux effets de bord : journalisation, nettoyage.
`exit 2` affiche stderr à l'utilisateur, sans autre effet.

## Ce qu'on peut y mettre

- **Index global des sessions** : durée, volume d'opérations, branche, projet.
  Toutes branches confondues, c'est la base d'une métrique d'usage d'équipe.
- **Signalement de sécurité** : `bypass_permissions_disabled` mérite une trace
  dédiée, distincte du journal courant.
- **Nettoyage** des fichiers temporaires de session : compteurs, verrous,
  trackers de fichiers édités.
- **Rappel de travail non commité** avant fermeture.

## Pièges

- **Budget de temps très court : 1,5 s partagé entre tous les hooks
  `SessionEnd`.** Le budget monte au plus long `timeout` déclaré en settings,
  jusqu'à 60 s — mais **le `timeout` d'un hook de plugin ne relève pas le
  budget**. Un hook de plugin doit donc rester bien en deçà de la seconde.
  Surcharge possible via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`.
- `reason: "resume"` n'est pas une vraie fin : c'est un changement de session.
  Filtrer si le traitement suppose une fin réelle.
- Ne rien tenter d'interactif ni de réseau ici : le temps manque.
