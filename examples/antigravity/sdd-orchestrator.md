# Antigravity — WFC Integration

## WFC Skills

WFC skills are installed at `~/.antigravity/skills/wfc-*/`.

### Setup

Add WFC instructions to your `.agent/rules/` or `~/.gemini/GEMINI.md`.

### Available Commands

- `/wfc-review` — 5-agent consensus code review
- `/wfc-build "feature"` — Quick feature builder with TDD
- `/wfc-plan` — Structured task breakdown
- `/wfc-implement` — Parallel TDD execution
- `/wfc-security` — STRIDE threat modeling

### Quality Standards

- Consensus Score ≥7.0 to merge
- Run `/wfc-review` before every PR
