# Notes projet

## Objectif

Construire un backend FastAPI clair, testable et pret a etre connecte a un front web.

## Principes

- API versionnee sous `/api/v1`.
- Configuration via variables d'environnement.
- Logique metier hors des routes HTTP.
- Services agentiques encapsules derriere des interfaces simples et testables.
- Tests rapides pour chaque comportement public.

## Prochaines etapes proposees

- Definir le premier cas d'usage agentique.
- Choisir le fournisseur LLM et la strategie d'orchestration.
- Ajouter une couche persistence si necessaire.
- Ajouter CI GitHub Actions quand le depot distant existe.
