---
name: git-workflow
description: Use when making commits, reviewing changes, creating branches, writing commit messages, or preparing project history for GitHub.
---

# Git Workflow

Keep history understandable.

## Rules

- Work on `main` only for project bootstrap or tiny solo changes.
- Use short branch names for features: `feature/agent-endpoint`.
- Commit one coherent change at a time.
- Use imperative commit messages: `Add health endpoint`.
- Check `git status` before and after changes.
- Do not commit secrets, `.env`, `.venv`, caches, or generated noise.

## Before Commit

Run quality checks when Python code changed.
