---
name: example-skill
description: Décrire ici, en une phrase, ce que fait la skill et quand l'utiliser. C'est ce texte qui sert à Claude pour décider de l'invoquer.
---

# Exemple de skill

Le corps du fichier contient les instructions données à Claude quand la skill
est invoquée, via `/plugin-template:example-skill` ou par Claude lui-même.

Une skill peut embarquer des fichiers annexes dans son répertoire :

```
skills/example-skill/
├── SKILL.md
├── reference.md      # documentation chargée à la demande
└── scripts/          # scripts appelés par la skill
```

Remplacer ce contenu par les instructions réelles.
