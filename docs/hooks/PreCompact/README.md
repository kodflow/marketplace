# PreCompact

Se déclenche avant une compaction du contexte, manuelle ou automatique. Dernier
moment où l'intégralité du contexte est encore disponible.

## Payload

| Champ | Contenu |
| ----- | ------- |
| `trigger` | `manual` (`/compact`) ou `auto` (seuil atteint) |
| `custom_instructions` | ce que l'utilisateur a passé à `/compact` ; **vide en mode `auto`** |

Le `matcher` porte sur `trigger`.

## Décision

`exit 2` ou `decision: "block"` **bloque la compaction**. Sur un `/compact`
manuel, stderr est montré à l'utilisateur.

Bloquer une compaction **automatique** a deux effets très différents selon son
origine : si elle était proactive, elle est simplement sautée et la conversation
continue sans être compactée ; si elle servait à récupérer d'une erreur de limite
de contexte **déjà renvoyée par l'API**, l'erreur remonte et **la requête en
cours échoue**. C'est une raison sérieuse de ne pas bloquer ici sans discernement.

`systemMessage` et `continue` sont jetés : le hook ne peut pas expliquer son
refus par ce canal.

## Ce qu'on peut y mettre

- **Persister l'état sur disque avant la perte** : décisions prises, chemin des
  fichiers en cours, plan actif, résultats d'analyse. Ce qui est écrit survit à
  la compaction ; ce qui ne l'est pas dépend du résumé.
- **Instantané horodaté** du point de reprise, pour pouvoir revenir en arrière si
  le résumé s'avère lacunaire.
- **Pointer explicitement les fichiers de reprise** en contexte, pour que la
  session d'après sache où retrouver l'état.

## Pièges

- **Prévoir la purge des instantanés.** Un hook qui écrit un fichier par
  compaction remplit le disque en silence ; `cleanupPeriodDays` ne couvre que les
  transcripts de Claude Code, pas les fichiers écrits par les hooks.
- En mode `auto`, `custom_instructions` est vide : ne pas en dépendre.
- Le hook est payé au moment où la session est déjà sous tension : le garder
  rapide, ou le passer en `async` puisqu'il n'a pas de décision à rendre.

## Complément

Le pendant côté reprise est [`SessionStart`](../SessionStart/) avec
`matcher: "compact"`, qui réinjecte les règles essentielles après coup, et
[`PostCompact`](../PostCompact/), qui donne accès au résumé produit.
