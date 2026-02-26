---
name: wfc-skill-validator-llm
description: >-
  LLM-based adversarial validator for WFC Agent Skills (agentskills.io spec
  only). Requires a SKILL.md file path or YAML metadata block as input.

  Trigger when the user wants to: test trigger phrase routing ("validate my
  WFC skill routing", "find routing gaps in my SKILL.md"); probe a skill
  description for edge case failures ("stress-test my WFC SKILL.md", "find
  false-positive triggers"); get a health score and candidate rewrite ("score
  my WFC skill description", "improve my SKILL.md trigger logic"); run a
  specific stage ("run discovery stage", "run edge case analysis").

  Not for:
  - Schema/structural validation or YAML syntax errors — use `make validate`
  - Formatting or restructuring SKILL.md files — use `make format`
  - Runtime execution debugging — evaluates definition quality only
  - General code review of skill files — use `wfc-review`
  - Skill definitions outside WFC / agentskills.io framework

  Explicit command: /wfc-skill-validator-llm
license: MIT
---

# wfc-skill-validator-llm

LLM-based validator that runs up to 4 structured analysis stages against a WFC skill
definition. Each stage that completes successfully writes a timestamped report to `~/.wfc`.
Partial runs produce partial reports; no automatic retry or recovery is implemented.

## What It Does

| Stage | What it checks |
|-------|---------------|
| `discovery` | Trigger routing coverage: will agents load this skill when they should, and not when they should not? Routing gaps, near-miss prompts, false-positive triggers |
| `logic` | Hallucination risks, ambiguous workflow steps, missing context that would force an implementing agent to invent behaviour |
| `edge_case` | Boundary conditions that break routing or execution: flag conflicts, missing prior reports, input format failures, silent partial completion |
| `refinement` | Synthesises the three prior stage reports → candidate SKILL.md rewrite + health score (0–10). Requires all three prior reports to exist; fails with `FileNotFoundError` if any are absent |

**Health score**: Refinement computes `(0.4 × trigger_clarity) + (0.35 × scope_accuracy) + (0.25 × step_clarity)` only when the LLM returns all three sub-scores in the structured format specified in the refinement prompt template. If any sub-score is absent or unparseable, the health score is marked `INVALID` — no zero-substitution is performed.

**Rewrite proposal**: The candidate SKILL.md rewrite is LLM-generated from the three prior stage reports. It is a suggestion requiring human review before application, not a verified-correct output.

## Usage

```bash
# Validate a single skill — all 4 stages
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-review

# Validate all skills in wfc/skills/
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli --all --yes

# Run a single stage only
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-build --stage discovery
uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli wfc/skills/wfc-build --stage refinement

# Dry run — print token count estimate based on file size; no API calls, no file writes
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
   If `--stage` is specified, only that stage runs; `--all` and `--stage` together run only the specified stage across all skills.
4. **Prior report lookup** — `refinement` reads the 3 prior reports from `~/.wfc` via
   `find_latest_stage_report()` (scans by mtime within the skill's report directory). Does not
   filter by run session or offline/live status — offline stub reports from prior CI runs will
   be used if they are the most recent files present.
5. **LLM call** — Each stage calls the Anthropic API via `ANTHROPIC_SKILLS_VALIDATOR` key using
   stage-specific prompt templates (defined in `assets/templates/`).
   Discovery uses extended thinking; others use standard completion.
6. **Health score** — Refinement parses sub-scores and computes:
   `(0.4 × trigger_clarity) + (0.35 × scope_accuracy) + (0.25 × step_clarity)`.
   Marked `INVALID` if any sub-score is missing from the LLM response.
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
  {skill_name}-refinement.md    ← includes "Health Score: X.X / 10" or "INVALID"
  summary-{timestamp}.md        ← cross-skill ranking table
```

## Flags Reference

| Flag | Description |
|------|-------------|
| `--all` | Validate every skill in `wfc/skills/wfc-*/` |
| `--stage NAME` | Run only one stage: `discovery`, `logic`, `edge_case`, `refinement` |
| `--offline` | No API calls; write `[OFFLINE STUB]` reports (CI safe) |
| `--dry-run` | Print token count estimate based on file size; no API calls, no file writes |
| `--yes` | Skip cost confirmation prompt |

## Not For

- **Structural / formatting checks** — use `make validate` instead.
- **Fixing skill formatting or frontmatter** — use `make format` or edit manually.
- **Runtime skill execution debugging** — this validates the definition, not execution.
- **General code review** — use `wfc-review`.
- **Non-WFC skill definitions** — this skill only processes WFC-format SKILL.md files.
- **Missing input invocations** — a WFC SKILL.md file path or YAML block must be provided.
