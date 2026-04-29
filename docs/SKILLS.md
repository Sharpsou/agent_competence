# Project Skills

Les skills projet sont installes depuis `skills.sh` et versionnes dans `.agents/skills/`.

Commande utilisee :

```powershell
npx skills add obra/superpowers --skill using-superpowers test-driven-development systematic-debugging writing-plans executing-plans verification-before-completion requesting-code-review receiving-code-review finishing-a-development-branch writing-skills --agent codex --copy -y
npx skills add github/awesome-copilot --skill git-commit --agent codex --copy -y
npx skills add skillcreatorai/ai-agent-skills --skill backend-development llm-application-dev --agent codex --copy -y
```

## Skills installes

- `.agents/skills/using-superpowers/SKILL.md`
- `.agents/skills/test-driven-development/SKILL.md`
- `.agents/skills/systematic-debugging/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`
- `.agents/skills/executing-plans/SKILL.md`
- `.agents/skills/verification-before-completion/SKILL.md`
- `.agents/skills/requesting-code-review/SKILL.md`
- `.agents/skills/receiving-code-review/SKILL.md`
- `.agents/skills/finishing-a-development-branch/SKILL.md`
- `.agents/skills/writing-skills/SKILL.md`
- `.agents/skills/git-commit/SKILL.md`
- `.agents/skills/backend-development/SKILL.md`
- `.agents/skills/llm-application-dev/SKILL.md`

## Notes

- Les anciens skills maison dans `.codex/skills/` ont ete retires car redondants.
- `skills-lock.json` garde la trace des skills installes et permet de les restaurer.
- `--copy` a ete utilise pour garder les fichiers Markdown dans le projet.
