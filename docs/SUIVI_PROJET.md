# Suivi projet

Derniere reprise : 2026-04-29, session locale Windows / PowerShell.

## Resume executif

Le projet est un backend FastAPI pour collecter des offres d'emploi, extraire les competences demandees par le marche, puis sauvegarder les analyses dans PostgreSQL quand la base est disponible.

Etat actuel :

- API FastAPI en place avec endpoints health, recherche d'offres et analyse de competences.
- Premier connecteur implemente : France Travail via pages publiques et extraction JSON-LD / microdata.
- CLI interactive de recherche d'offres disponible.
- Pipeline d'analyse de competences disponible avec agent LLM local optionnel et fallback deterministe.
- Schema PostgreSQL initial ajoute dans `migrations/`.
- `docker-compose.yml` ajoute pour lancer PostgreSQL localement.
- Tests, lint et typage passent localement.

## Etat fonctionnel

### API

Endpoints presents dans `app/main.py` :

- `GET /health`
- `POST /jobs/search`
- `POST /jobs/search/from-config`
- `POST /competencies/extract`
- `POST /competencies/analyze`
- `POST /competencies/analyze/from-config`

### Collecte d'offres

Le module principal est `app/jobs.py`.

Fonctions disponibles :

- validation de la requete avec Pydantic ;
- lecture/ecriture de `config/job_search_request.json` ;
- mode CLI interactif ;
- cache HTTP dans `data/runtime/http-cache` ;
- resolution simple de codes ville INSEE pour quelques villes ;
- filtrage contrat, teletravail et mots exclus ;
- dedoublonnage par source et identifiant source ;
- extraction France Travail depuis URL publique.

Limites connues :

- un seul connecteur actif pour l'instant : France Travail ;
- table de villes codee en dur ;
- extraction HTML sensible aux changements de structure cote source ;
- pas encore de limite de persistance ou d'historique de cache configurable ;
- `published_since` est documente comme besoin futur mais pas encore implemente dans le modele.

### Extraction de competences

Modules principaux :

- `app/competencies.py`
- `app/competency_analysis.py`

Comportement :

- tentative d'extraction par LLM local compatible OpenAI si configure ;
- fallback deterministe si le serveur LLM local est absent ou en erreur ;
- normalisation, regroupement et verification des competences ;
- conservation du contexte offre / societe / titre ;
- trace des agents dans la reponse.

Configuration LLM attendue :

```powershell
$env:LOCAL_LLM_BASE_URL="http://localhost:1234"
$env:LOCAL_LLM_MODEL="qwen2.5-3b-instruct"
$env:LOCAL_LLM_TIMEOUT_SECONDS="45"
```

### Stockage

Modules et fichiers :

- `app/storage.py`
- `app/sql_client.py`
- `migrations/001_competency_market_schema.sql`

Tables prevues :

- `companies`
- `job_search_runs`
- `job_offers`
- `job_search_run_offers`
- `competencies`
- `competency_observations`

La persistance est optionnelle : si `DATABASE_URL` n'est pas renseigne, l'analyse retourne un resultat non persiste.

## Configuration actuelle

Fichier suivi par git :

- `config/job_search_request.json`

Contenu fonctionnel observe :

- mots-cles : `data`, `analys`, `scienc`, `sql`
- localisation : `france`
- type de contrat : `CDI`
- teletravail : `hybrid`
- source : `france_travail`
- limite : 20 offres

Variable PostgreSQL attendue dans `.env.example` :

```text
DATABASE_URL=postgresql://agent_competence:agent_competence@localhost:5432/agent_competence
```

## Docker

Fichier compose present :

- `docker-compose.yml`

Service declare :

- `postgres`
- image `postgres:16-alpine`
- port local `5432`
- volume `postgres_data`
- migrations montees dans `/docker-entrypoint-initdb.d`

Check effectue le 2026-04-29 :

```powershell
docker ps
docker compose ps
docker compose config
```

Resultat :

- la commande `docker` n'est pas reconnue dans ce shell ;
- `C:\Program Files\Docker\Docker\resources\bin\docker.exe` est absent ;
- aucun service ou process Docker detecte par PowerShell.

Conclusion :

Docker n'est pas disponible dans l'environnement courant. Le compose est pret cote repo, mais PostgreSQL ne peut pas etre lance tant que Docker Desktop ou un Docker CLI compatible n'est pas installe et accessible dans le PATH.

Commande a relancer apres installation/configuration Docker :

```powershell
docker compose up -d postgres
docker compose ps
python -m app.sql_client -q "select now()"
```

## Verification locale

Commandes lancees le 2026-04-29 :

```powershell
python -m pytest
python -m ruff check app tests
python -m mypy app
python -m app.analyze_cli --help
python -m app.sql_client --help
```

Resultats :

- `pytest` : 23 tests passent ;
- couverture globale affichee : 70% ;
- `ruff` : aucun probleme ;
- `mypy` : aucun probleme sur 10 fichiers source ;
- les aides CLI `analyze_cli` et `sql_client` repondent correctement.

Note environnement :

- les tests ont tourne avec Python `3.14.4` ;
- le projet declare `requires-python = ">=3.12"`.

## Etat Git observe

Branche :

- `main`, en suivi de `origin/main`

Changements suivis modifies :

- `.env.example`
- `README.md`
- `app/cli.py`
- `app/jobs.py`
- `app/main.py`
- `config/job_search_request.json`
- `docs/JOB_COLLECTION.md`
- `pyproject.toml`
- `tests/test_jobs.py`

Nouveaux fichiers non suivis :

- `app/analyze_cli.py`
- `app/competencies.py`
- `app/competency_analysis.py`
- `app/settings.py`
- `app/sql_client.py`
- `app/storage.py`
- `docker-compose.yml`
- `docs/AGENTIC_COMPETENCY_MODEL.md`
- `migrations/001_competency_market_schema.sql`
- `scripts/analyze-competencies.cmd`
- `scripts/analyze-competencies.ps1`
- `scripts/query-db.cmd`
- `scripts/query-db.ps1`
- `tests/conftest.py`
- `tests/test_cli.py`
- `tests/test_competencies.py`
- `tests/test_competency_analysis.py`

Point d'attention :

- `.env` existe localement et est ignore par git, ce qui est correct.
- `config/job_search_request.json` est versionne pour cadrer le format, mais pourra devenir local/ignore si les criteres deviennent personnels.

## Prochaines etapes recommandees

1. Installer ou rendre disponible Docker Desktop, puis valider PostgreSQL avec `docker compose up -d postgres`.
2. Lancer une analyse de bout en bout avec base disponible :

```powershell
python -m app.analyze_cli
python -m app.sql_client -q "select name, category from competencies order by name limit 20"
```

3. Decider si `config/job_search_request.json` reste versionne ou si un exemple public remplace la config locale.
4. Ajouter un test d'integration PostgreSQL optionnel, marque ou conditionne par `DATABASE_URL`.
5. Ajouter `published_since` au modele si le besoin de fraicheur des offres devient prioritaire.
6. Remplacer progressivement la table de villes statique par une source plus complete.
7. Ajouter un deuxieme connecteur seulement apres validation stable du flux France Travail.

## Commandes utiles

Demarrer l'API :

```powershell
uvicorn app.main:app --reload
```

Recherche interactive :

```powershell
python -m app.cli
```

Analyse depuis la config :

```powershell
python -m app.analyze_cli
```

Client SQL :

```powershell
python -m app.sql_client
```

Qualite :

```powershell
python -m ruff check app tests
python -m mypy app
python -m pytest
```
