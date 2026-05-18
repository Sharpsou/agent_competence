# Contribuer

## Workflow Git

1. Partir d'une branche courte et explicite : `feature/job-filters`, `fix/config-loading`.
2. Garder des commits lisibles, centres sur une seule intention.
3. Lancer format, lint, typage et tests avant d'ouvrir une PR.
4. Mettre a jour le README ou `docs/` quand le comportement public change.

Les fichiers locaux de travail restent hors Git : `.env`, caches, couverture,
donnees temporaires et sorties d'experimentation.

## Methode

Le projet assume une pratique de vibe coding encadree : on peut avancer vite avec
un assistant, mais chaque changement doit rester relisible, teste et verifie. Les
skills dans `.agents/skills/` servent de garde-fous de workflow, pas de vitrine.

## Definition of Done

- Le code est type et lisible.
- Les routes exposees ont au moins un test nominal.
- Les erreurs publiques sont explicites et stables.
- Les nouvelles decisions techniques importantes sont documentees dans `docs/`.
