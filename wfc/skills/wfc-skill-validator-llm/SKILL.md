---
name: wfc-skill-validator-llm
description: >-
  LLM-based validator for WFC Agent Skills. Uses adversarial prompting to find routing gaps,
  logic faults, edge case failures, and propose concrete SKILL.md rewrites with a health score.
  Triggers on "validate skill routing", "check skill descriptions", "test if my skill triggers
  correctly", "find routing gaps in my skill", "does my skill description work", "validate skill
  logic", "stress-test my skill", "refine my skill definition", or explicit /wfc-skill-validator-llm.
  Not for: structural checks (use make validate), fixing skill formatting, runtime skill debugging,
  general code review.
license: MIT
---

# wfc-skill-validator-llm

LLM-based validator that stress-tests WFC skill definitions across 4 progressive stages using
adversarial prompting.

## What It Does

Runs up to 4 validation stages per skill, each writing a timestamped report to `~/.wfc`:

| Stage | What it checks |
|-------|---------------|
| `discovery` | Will agents load this skill when they should? Routing gaps, near-miss prompts |
| `logic` | Hallucination risks, ambiguous steps, missing context |
| `edge_case` | Boundary conditions that break routing or execution |
| `refinement` | Synthesises all 3 prior reports → proposed SKILL.md rewrite + health score (0–10) |

## Usage

```bash
# Validate a single skill — all 4 stages
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-review

# Validate all skills in wfc/skills/
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --yes

# Run a single stage only
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-build --stage discovery
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-build --stage refinement

# Dry run — estimate cost, no API calls
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-review --dry-run

# CI safe — no API calls, writes offline stub reports
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --yes --offline

# Skip confirmation
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --yes
```

## Environment

```bash
export ANTHROPIC_SKILLS_VALIDATOR=sk-ant-...   # Required for live runs
# Not needed for --offline or --dry-run
```

## Workflow

1. **Argument parsing** — `cli.py` parses skill path or `--all`, plus `--stage`/`--dry-run`/`--yes`/`--offline`.
2. **Skill reading** — Read `SKILL.md`; extract `name`/`description` (frontmatter) and full body.
3. **Stage execution** — Run selected stages sequentially: discovery → logic → edge_case → refinement.
4. **Prior report lookup** — `refinement` reads the 3 prior reports from `~/.wfc` via
   `find_latest_stage_report()` (scans by mtime). Fails with `FileNotFoundError` if any are missing.
5. **LLM call** — Each stage calls `claude-sonnet-4-6` via `ANTHROPIC_SKILLS_VALIDATOR` key.
   Discovery uses extended thinking; others use standard completion.
6. **Health score** — Refinement parses sub-scores and computes:
   `(0.4 × trigger_clarity) + (0.35 × scope_accuracy) + (0.25 × step_clarity)`
7. **Report writing** — Per-stage `.md` reports written to `~/.wfc/.../docs/skill-validation/{timestamp}/`.
8. **Summary** — After refinement runs, a `summary-{timestamp}.md` is written ranking all validated
   skills by health score (ascending = most broken first).

## Output

### Report paths

```
~/.wfc/projects/{repo}/branches/{branch}/docs/skill-validation/{timestamp}/
  {skill_name}-discovery.md
  {skill_name}-logic.md
  {skill_name}-edge_case.md
  {skill_name}-refinement.md    ← includes "Health Score: X.X / 10"
  summary-{timestamp}.md        ← cross-skill ranking table
```

### Corpus path

```
~/.wfc/projects/{repo}/skill-validation-corpus.json
```

## Flags Reference

| Flag | Description |
|------|-------------|
| `--all` | Validate every skill in `wfc/skills/wfc-*/` |
| `--stage NAME` | Run only one stage: `discovery`, `logic`, `edge_case`, `refinement` |
| `--offline` | No API calls; write `[OFFLINE STUB]` reports (CI safe) |
| `--dry-run` | Print cost estimate; no API calls, no file writes |
| `--yes` | Skip cost confirmation prompt |

## Not For

- **Structural / formatting checks** — use `make validate` instead.
- **Fixing skill formatting or frontmatter** — use `make format` or edit manually.
- **Runtime skill execution debugging** — this validates the definition, not execution.
- **General code review** — use `wfc-review`.
