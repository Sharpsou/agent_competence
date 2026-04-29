# Agent Competence Backend

Backend Python FastAPI destiné a exposer une API pour un futur front web et a servir de base pour des fonctionnalites agentiques.

## Stack

- Python 3.12+
- FastAPI
- Pydantic Settings
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
- `GET /api/v1/health`
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
  agents/        # services et contrats pour la future logique agentique
  api/           # routes HTTP versionnees
  core/          # configuration et briques transverses
  schemas/       # schemas Pydantic publics
tests/           # tests automatises
docs/            # notes projet, decisions, conventions
```

## Skills Codex installes

Les skills suivants ont ete installes pour soutenir le projet :

- `openai-docs` pour les bonnes pratiques OpenAI et agentiques a jour
- `security-best-practices` et `security-threat-model` pour la securite
- `gh-address-comments`, `gh-fix-ci` et `yeet` pour GitHub, CI, reviews et PR

Redemarre Codex pour prendre en compte les nouveaux skills.
