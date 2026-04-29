---
name: agentic-design
description: Use when adding agentic model behavior, LLM calls, tool use, planning loops, memory, prompts, evaluation, or safety controls to this project.
---

# Agentic Design

Do not build a framework before the first useful agent exists.

## Rules

- Start with one concrete user task.
- Keep prompts versioned in code or docs when they become important.
- Separate model calls from HTTP routes.
- Log enough context to debug behavior without storing secrets.
- Make tool boundaries explicit: inputs, outputs, failure modes.
- Add tests around deterministic logic and small contract tests around model-facing code.

## First Milestone

Define:

- the agent's job
- allowed tools
- expected input
- expected output
- refusal or escalation rules
