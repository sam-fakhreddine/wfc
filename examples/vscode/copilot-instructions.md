# VS Code Copilot — WFC Integration

## WFC Skills

WFC skills are installed at `~/.vscode/skills/wfc-*/`. Use them via slash commands in Copilot Chat.

### Core Commands

- `/wfc-review` — 5-agent consensus code review
- `/wfc-build "feature"` — Quick feature builder with TDD workflow
- `/wfc-plan` — Structured task breakdown with dependency graphs
- `/wfc-implement` — Parallel TDD execution engine
- `/wfc-security` — STRIDE threat modeling and security audit

### When to Use

- Feature development: `/wfc-build` or `/wfc-plan` → `/wfc-implement`
- Code review: `/wfc-review` before any PR merge
- Security audit: `/wfc-security --stride`
