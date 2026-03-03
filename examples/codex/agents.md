# Codex — WFC Integration

## WFC Skills

WFC skills are installed at `~/.codex/skills/wfc-*/`.

### Available Commands

- `/wfc-review` — 5-agent consensus code review
- `/wfc-build "feature"` — Quick feature builder with TDD
- `/wfc-plan` — Structured task breakdown
- `/wfc-implement` — Parallel TDD execution
- `/wfc-security` — STRIDE threat modeling
- `/wfc-test` — Property-based test generation

### Quality Standards

- Consensus Score ≥7.0 to merge
- Zero critical findings from Security or Reliability
- Run `/wfc-review` before every PR
