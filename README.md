# Agent Competence Backend

Backend Python FastAPI minimal, destine a exposer une API pour un futur front web.

Le projet commence volontairement simple. Les conventions de travail sont dans des skills Markdown locaux, versionnes avec le repo.

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
.codex/skills/   # skills Markdown propres au projet
```

## Skills projet

Les skills qui cadrent le projet sont dans `.codex/skills/` :

- `fastapi-backend`
- `python-quality`
- `agentic-design`
- `project-management`
- `git-workflow`

Voir aussi `docs/SKILLS.md`.
