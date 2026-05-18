# Projet

## Objectif

Construire un backend simple pour observer les competences demandees dans les
offres d'emploi : collecter des annonces, normaliser les donnees, extraire les
competences, puis conserver les resultats quand PostgreSQL est disponible.

## Principes

- Garder une API mince et des fonctions testables directement.
- Versionner les conventions de travail utiles, notamment `.agents/skills/`.
- Preferer des boucles courtes : petit changement, verification, ajustement.
- Documenter les decisions durables dans `docs/`, pas les brouillons locaux.
- Ajouter des connecteurs ou couches d'abstraction seulement quand le besoin est
  concret.

## Etat actuel

- API FastAPI avec endpoints de sante, recherche et analyse.
- Connecteur France Travail base sur les pages publiques.
- CLI de recherche, d'analyse et de requete SQL.
- Extraction de competences par LLM local optionnel, avec fallback deterministe.
- Schema PostgreSQL initial et `docker-compose.yml` pour la base locale.
- CI GitHub pour format, lint, typage et tests.

## Decisions ouvertes

- Garder `config/job_search_request.json` comme exemple versionne ou le remplacer
  par un fichier `.example` si les criteres deviennent personnels.
- Remplacer la petite table de villes statique par une source plus complete.
- Ajouter un second connecteur apres stabilisation du flux France Travail.
- Ajouter un test d'integration PostgreSQL conditionne par `DATABASE_URL`.
