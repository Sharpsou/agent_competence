# Agent Competence Backend

Backend Python minimal pour chercher des offres d'emploi, en extraire des competences, puis
eventuellement sauvegarder l'analyse dans PostgreSQL.

## Volonte technique

Le projet privilegie un socle simple et local-first:

- une API FastAPI mince, sans couche applicative artificielle;
- des fonctions Python testables directement, reutilisees par l'API et les CLI;
- une extraction deterministe par aliases, avec LLM local optionnel et non obligatoire;
- une persistance PostgreSQL optionnelle, activee seulement si `DATABASE_URL` est renseigne;
- des donnees runtime et caches HTTP ignores par Git pour garder le depot propre.

L'objectif n'est pas de construire une plateforme complete trop tot. Le code doit rester lisible,
portable et facile a verifier avant d'ajouter un front, plus de sources d'offres ou des traitements
LLM plus ambitieux.

## Stack

- Python 3.12+
- FastAPI
- Pydantic
- Pytest
- Ruff
- Mypy
- PostgreSQL optionnel

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

Endpoints utiles:

- `GET /health`
- `GET /docs`
- `POST /jobs/search`
- `POST /jobs/search/from-config`
- `POST /competencies/extract`
- `POST /competencies/analyze`
- `POST /competencies/analyze/from-config`

## Utiliser les CLI

Recherche d'offres depuis le terminal:

```powershell
python -m app.cli
```

ou, apres installation editable:

```powershell
search-jobs
```

Analyse des offres de `config/job_search_request.json`:

```powershell
python -m app.analyze_cli
```

Client SQL minimal:

```powershell
python -m app.sql_client -q "select name, category from competencies order by name limit 20"
```

## Configuration

La recherche par defaut est dans `config/job_search_request.json`.

Exemple:

```json
{
  "keywords": ["data", "sql"],
  "locations": ["nantes"],
  "location": "nantes",
  "radius_km": 10,
  "contract_type": "CDI",
  "remote_mode": "hybrid",
  "sources": ["france_travail"],
  "max_results": 20,
  "excluded_keywords": [],
  "include_raw_payload": false
}
```

Variables `.env` supportees:

- `DATABASE_URL`: active la sauvegarde PostgreSQL.
- `LOCAL_LLM_BASE_URL` et `LOCAL_LLM_MODEL`: activent l'extraction LLM locale.
- `LOCAL_LLM_TIMEOUT_SECONDS`: timeout du client LLM, defaut `45`.
- `LOCAL_LLM_MAX_TOKENS`: budget de sortie LLM, defaut `1200`.
- `LOCAL_LLM_OFFERS_PER_CALL`: taille des lots envoyes au LLM, defaut `1`.

Si le LLM local est absent ou indisponible, le projet repasse sur l'extracteur par aliases.

## PostgreSQL

```powershell
docker compose up -d postgres
```

Les migrations SQL sont montees automatiquement par Docker Compose au premier demarrage du volume.

## Qualite

```powershell
ruff format .
ruff check .
mypy app
pytest
```

## Structure

```text
app/
  main.py                 # routes FastAPI
  jobs.py                 # recherche et parsing France Travail
  competencies.py         # extraction et verification des competences
  competency_analysis.py  # orchestration recherche + extraction + sauvegarde
  storage.py              # depot PostgreSQL optionnel
  cli.py                  # recherche interactive
  analyze_cli.py          # analyse depuis la config
  sql_client.py           # petit client SQL
config/
  job_search_request.json # recherche locale par defaut
docs/
  *.md                    # notes projet
tests/
  test_*.py               # tests automatises
```

## Notes projet

- `data/runtime/` contient les caches et fichiers temporaires locaux.
- `.agents/skills/` versionne les skills qui cadrent la methode de travail du repo.
- `docs/JOB_COLLECTION.md` et `docs/AGENTIC_COMPETENCY_MODEL.md` decrivent les pistes produit.
