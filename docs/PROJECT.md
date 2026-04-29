# Notes projet

## Objectif

Construire un backend FastAPI clair, minimal, testable et pret a etre connecte a un futur front web.

## Principes

- Commencer simple : `app/main.py` suffit tant que le besoin reste petit.
- Ajouter des dossiers seulement quand le code le justifie.
- Garder les conventions projet dans `.agents/skills/`, installees depuis `skills.sh`.
- Tests rapides pour chaque comportement public.

## Prochaines etapes proposees

- Definir le premier cas d'usage agentique.
- Ajouter une premiere route utile au front.
- Choisir le fournisseur LLM seulement quand le premier cas d'usage est clair.
- Ajouter une couche persistence uniquement si necessaire.
