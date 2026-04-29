---
name: python-quality
description: Use when writing or reviewing Python code in this project, especially for clarity, typing, tests, conventions, and maintainable functions.
---

# Python Quality

Write code that is easy to delete, test, and read.

## Rules

- Prefer small functions with clear names.
- Type public functions and non-obvious data structures.
- Avoid abstractions before there are at least two real use cases.
- Keep comments rare and useful.
- Prefer standard library features before adding dependencies.
- Keep tests close to behavior, not implementation details.

## Validation

Run:

```powershell
ruff format .
ruff check .
mypy app
pytest
```
