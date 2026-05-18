# Agent Competence

Backend FastAPI pour explorer des offres d'emploi, en extraire les competences
citees, puis garder une trace exploitable dans PostgreSQL quand une base locale
est configuree.

Le projet reste volontairement simple : une API lisible, des fonctions Python
testables sans serveur, quelques CLI pratiques, et une documentation de travail
assez courte pour rester utile.

## Ce que fait le projet

- recherche d'offres via un premier connecteur France Travail ;
- filtrage par mots-cles, lieu, contrat, teletravail et exclusions ;
- extraction de competences par LLM local compatible OpenAI, avec fallback
  deterministe si le LLM n'est pas disponible ;
- sauvegarde optionnelle des recherches, offres et observations de competences
  dans PostgreSQL ;
- commandes CLI pour chercher, analyser et interroger la base.

## Esprit de travail

Le repo sert aussi de terrain de pratique pour une facon de coder plus
agentique : petites boucles, verification frequente, skills projet versionnes et
notes de decision dans `docs/`. L'idee n'est pas de deleguer le jugement au LLM,
mais de s'en servir comme accelerateur tout en gardant un code relisible.

## Stack

- Python 3.12+
- FastAPI, Pydantic
- PostgreSQL optionnel
- Pytest, Ruff, Mypy

## Installation

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## Lancer l'API

```powershell
uvicorn app.main:app --reload
```

Endpoints principaux :

- `GET /health`
- `POST /jobs/search`
- `POST /jobs/search/from-config`
- `POST /competencies/extract`
- `POST /competencies/analyze`
- `POST /competencies/analyze/from-config`

La documentation interactive est disponible sur `http://127.0.0.1:8000/docs`.

## Commandes utiles

```powershell
python -m app.cli
python -m app.analyze_cli
python -m app.sql_client -q "select name, category from competencies order by name limit 20"
```

Apres installation editable, les memes commandes existent aussi sous forme de
scripts :

```powershell
search-jobs
analyze-competencies
query-db -q "select now()"
```

## Configuration

La recherche par defaut est dans `config/job_search_request.json`. Ce fichier
sert d'exemple versionne et de point d'entree pratique pour les CLI.

Variables d'environnement supportees :

- `DATABASE_URL` : active la persistance PostgreSQL.
- `LOCAL_LLM_BASE_URL` : URL d'un serveur LLM local compatible OpenAI.
- `LOCAL_LLM_MODEL` : modele utilise pour l'extraction.
- `LOCAL_LLM_TIMEOUT_SECONDS` : timeout du client LLM, defaut `45`.
- `LOCAL_LLM_MAX_TOKENS` : budget de sortie LLM, defaut `1200`.
- `LOCAL_LLM_OFFERS_PER_CALL` : taille des lots envoyes au LLM, defaut `1`.

Sans LLM local, l'extraction repasse automatiquement sur des aliases
deterministes.

## PostgreSQL local

```powershell
docker compose up -d postgres
```

Au premier demarrage du volume, Docker applique les migrations de `migrations/`.
Si `DATABASE_URL` n'est pas renseigne, l'API et les CLI continuent de fonctionner
sans sauvegarde.

## Qualite

```powershell
ruff format .
ruff check .
mypy app
pytest
```

La CI GitHub lance les memes controles sur les pushes vers `main` et les pull
requests.

## Reperes

```text
app/          API, connecteurs, extraction et stockage
config/       configuration d'exemple pour les recherches
docs/         notes projet et pistes produit
migrations/   schema PostgreSQL
scripts/      wrappers Windows pratiques
tests/        tests automatises
```

Les fichiers locaux de runtime restent hors Git : `.env`, caches, couverture,
artefacts de test et `data/runtime/`.
