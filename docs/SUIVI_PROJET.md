# Suivi projet

Derniere reprise : 2026-05-18.

## Resume

Agent Competence est un backend FastAPI pour collecter des offres d'emploi,
extraire les competences demandees, puis sauvegarder les analyses dans
PostgreSQL quand une base locale est configuree.

## Fonctionnel

- `GET /health`
- `POST /jobs/search`
- `POST /jobs/search/from-config`
- `POST /competencies/extract`
- `POST /competencies/analyze`
- `POST /competencies/analyze/from-config`

Le connecteur actif est France Travail. Les resultats sont normalises, filtres
et dedoublonnes avant extraction.

## Extraction

L'extraction privilegie un LLM local compatible OpenAI quand les variables
`LOCAL_LLM_*` sont presentes. Si le serveur local est absent ou repond mal, le
backend utilise un extracteur deterministe par aliases.

Les etapes visibles dans la reponse sont conservees dans `agent_trace`.

## Stockage

La persistance est optionnelle. Quand `DATABASE_URL` est renseigne, les analyses
sont enregistrees via le schema `migrations/001_competency_market_schema.sql`.
Sinon les endpoints et CLI retournent un resultat non persiste.

## Hygiene Git

- `.env`, caches, couverture et `data/runtime/` sont ignores.
- `.agents/skills/` est versionne volontairement pour garder les conventions de
  travail du projet.
- `skills-lock.json` documente les skills installes.
- La CI controle format, lint, typage et tests.

## Prochaines etapes

1. Valider le flux PostgreSQL de bout en bout dans un environnement avec Docker.
2. Decider le statut de `config/job_search_request.json` si la config devient
   personnelle.
3. Ajouter un test d'integration PostgreSQL optionnel.
4. Etendre la resolution de villes.
5. Ajouter un deuxieme connecteur seulement apres stabilisation de France
   Travail.
