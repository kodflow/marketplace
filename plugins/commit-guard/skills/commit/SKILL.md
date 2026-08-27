---
name: commit
description: Rédiger et créer un commit au format Kodflow — analyse des changements en attente, message conforme à la convention, référence au commit fautif pour une régression.
---

# Commit au format Kodflow

## 1. Établir l'état

```bash
git status --short
git diff --staged
git diff            # ce qui n'est pas encore indexé
git log --oneline -5
```

Si rien n'est indexé, indexe ce qui relève du changement décrit, et lui seul.
Un commit porte **un** changement cohérent : si tu ne peux pas résumer le tout en
une phrase, découpe-le.

## 2. Comprendre avant de rédiger

Ne décris pas le diff, il est déjà lisible. Le message doit répondre à ce que le
diff ne dit pas :

- quel comportement est en défaut aujourd'hui, ou quel besoin n'est pas couvert ;
- pourquoi cette solution plutôt qu'une autre ;
- ce qui a été écarté et pourquoi, si c'est utile au relecteur.

Si le changement corrige une régression, retrouve le commit fautif :

```bash
git log -S '<symbole ou chaîne concerné>' --oneline
git log -1 --pretty=fixes <sha>      # si pretty.fixes est configuré
```

## 3. Rédiger

```
<type>(<scope>)[!]: <description à l'impératif, ≤ 72 caractères, sans point final>

<Corps en prose, enveloppé à 72 colonnes.
Premier paragraphe : le problème, au présent.
Second paragraphe : ce que fait le changement et pourquoi.>

<trailers, en dernier, précédés d'une ligne vide>
```

Types : `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`,
`revert`. Le scope désigne le composant ou l'interface (`x1`, `x2`, `admf`,
`mdf2`, `asn1`…).

Test du sujet : « Si appliqué, ce commit va _&lt;sujet&gt;_ » doit se lire
correctement. « corriger le décalage » passe, « correction du décalage » et
« j'ai corrigé le décalage » non.

Trailers :

| Trailer | Usage |
| ------- | ----- |
| `Fixes: <sha12> ("<sujet>")` | régression : réfère le **commit** fautif |
| `Closes #NNN` | ferme une issue GitLab |
| `Refs: #NNN` | référence sans fermer |
| `Reviewed-by: Nom <email>` | revue technique |
| `Tested-by: Nom <email>` | validation sur banc ou plateforme |

`Fixes:` réfère un commit, `Closes` une issue : ne pas confondre les deux.

## 4. Ce qui est proscrit

- **Aucune mention d'assistant** : pas de trailer `Co-Authored-By` vers un
  outil, pas de « Generated with », pas d'emoji robot. Le hook du plugin refuse
  le commit et la commande devra être rejouée.
- **Aucun vocabulaire d'orchestration** : « Phase 2 », « Lot 3 », « étape 1/3 »,
  « comme demandé ». Un message de commit décrit un changement, pas le
  déroulement du travail.
- **Pas de mise en forme de rapport** : ni sections « Résumé » / « Test plan »,
  ni tableaux, ni puces en gras. La prose exprime la causalité, ce qu'une liste
  ne fait pas. Une liste ne se justifie que pour énumérer des éléments réellement
  indépendants — plateformes testées, paramètres ajoutés.
- **Pas de référence à l'outillage interne** de la session de travail.

## 5. Créer le commit

Toujours avec `-m` (une occurrence par paragraphe) ou `-F` pour un message long.
Jamais sans, l'éditeur interactif figerait la session.

```bash
git commit -m "fix(x1): rejeter les ActivateTask sans XID" \
           -m "Depuis la refonte du parseur X1, une requête dépourvue du champ
XID franchit la validation. Le dispatch déréférence alors un pointeur nul et
fait tomber l'ADMF, ce qui interrompt les interceptions actives." \
           -m "Valider la présence du XID avant le dispatch et répondre par une
ErrorResponse ETSI : la conformité impose une réponse au demandeur, y compris
sur requête malformée." \
           -m 'Fixes: 3f2a1b9c4d5e ("x1: refactorer le parseur de requêtes ETSI")
Closes #517'
```

Ne jamais ajouter `--no-verify` : les hooks git portent les contrôles de qualité
et de secrets. Si l'un d'eux est en défaut, corrige-le ou signale-le.

## 6. Vérifier

```bash
git log -1 --stat
```

Relis le message : est-il compréhensible dans six mois par quelqu'un qui n'a pas
suivi ce travail, sans ouvrir le diff ?
