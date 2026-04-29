---
name: fastapi-backend
description: Use when working on this project's FastAPI backend, adding API routes, request/response schemas, dependency injection, error handling, or local server behavior.
---

# FastAPI Backend

Keep the backend simple until the product need is clear.

## Rules

- Start with one route in `app/main.py`.
- Add a new module only when `app/main.py` becomes hard to read.
- Keep HTTP handlers thin: parse input, call one function, return output.
- Use explicit response models when a route returns structured business data.
- Keep route names stable and boring.
- Prefer `/health` for infrastructure checks.

## Before Finishing

- Add or update one focused test per public route.
- Run `ruff format .`, `ruff check .`, `mypy app`, and `pytest`.
