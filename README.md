# Agent Competence Backend

Backend Python FastAPI minimal, destine a exposer une API pour un futur front web.

Le projet commence volontairement simple. Les conventions de travail viennent de skills Markdown installes depuis `skills.sh` et versionnes avec le repo.

## Stack

- Python 3.12+
- FastAPI
- Pytest
- Ruff
- Mypy

## Demarrage local

Installe d'abord Python 3.12 ou plus, puis :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Lance l'API :

```powershell
uvicorn app.main:app --reload
```

Endpoints utiles :

- `GET /health`
- `GET /docs`

Direction court terme :

- `POST /jobs/search` pour chercher des offres d'emploi par mots-cles, localisation et filtres.
- Voir `docs/JOB_COLLECTION.md`.

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
  main.py        # application FastAPI minimale
tests/           # tests automatises
docs/            # notes projet et index des skills
.agents/skills/  # skills Markdown installes depuis skills.sh
```

## Skills projet

Les skills qui cadrent le projet sont dans `.agents/skills/`, installes depuis `skills.sh`.

Principaux skills :

- `backend-development`
- `llm-application-dev`
- `test-driven-development`
- `systematic-debugging`
- `writing-plans`
- `executing-plans`
- `verification-before-completion`
- `git-commit`

Voir aussi `docs/SKILLS.md`.
