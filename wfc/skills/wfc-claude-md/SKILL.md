---
name: wfc-claude-md
description: >
  Agentic CLAUDE.md remediation pipeline. Diagnoses and fixes CLAUDE.md files
  using a 5-agent sequential pipeline: Context Mapper (local inventory) →
  Analyst (rubric scoring) → Fixer (subtraction-first rewrite) → QA Validator
  (adversarial review with retry) → Reporter (migration plan + final file).
  Produces a rewritten CLAUDE.md and migration plan. Never auto-writes files —
  presents report for human approval. Invoke with: /wfc-claude-md [project_root]
license: MIT
---

# wfc-claude-md — CLAUDE.md Remediation Pipeline

Diagnose and fix CLAUDE.md files using a 5-agent sequential pipeline.

## When to Use

- Your CLAUDE.md exceeds 200 lines
- Claude is ignoring instructions it should follow
- You suspect instruction budget exhaustion (>80 instructions)
- Commands or paths in your CLAUDE.md are stale
- You have linter configs but still inline code style rules

## Triggers

```bash
# Analyze and report (default — no writes)
/wfc-claude-md

# Specific project
/wfc-claude-md /path/to/project

# Write after reviewing the report
/wfc-claude-md --write

# Heuristic mode (no API key required)
/wfc-claude-md --no-llm
```

## Pipeline

```
Context Mapper → Analyst → Fixer → QA Validator → Reporter
   (local)       (LLM)    (LLM)    (rule+LLM)     (LLM)
                            ↑           |
                            └─── FAIL ──┘ (up to 2 retries)
```

**Agent responsibilities:**

| Agent | Model | What it does |
|-------|-------|--------------|
| Context Mapper | Local | Inventories CLAUDE.md + codebase; cross-references commands/paths |
| Analyst | sonnet | Scores 16 dimensions across 4 categories; produces issues list |
| Fixer | sonnet | Rewrites via subtraction; extracts content to docs/; recommends hooks |
| QA Validator | sonnet | Adversarial review; fails on regressions; triggers retry |
| Reporter | haiku | Generates human-readable report with Migration Actions section |

## Grades

| Grade | Criteria |
|-------|---------|
| A | <150 lines, <60 instructions, progressive disclosure, no linter dup |
| B | <200 lines, <80 instructions, minimal non-universal content |
| C | <300 lines or 1-2 major issues |
| D | >300 lines, overdrawn budget, stale commands, significant linter dup |
| F | Actively harmful — wrong commands, contradictions, relevance filter triggered |

Grade A files are returned unchanged.

## Output

```
## Summary
- Original: 420 lines, ~130 instructions
- Rewritten: 85 lines, ~35 instructions (80% reduction)
- Budget status: overdrawn → healthy
- Grade: D → A
- Verdict: PASS

## What Was Cut
- Inline code style rules (project has ruff.toml)
- Database schema (80 lines) extracted to docs/data-model.md
- Deployment workflow extracted to .claude/commands/deploy.md

## Migration Actions (Human Required)
1. Create docs/data-model.md with extracted content (below)
2. Configure PostToolUse hook for auto-format on Write/Edit
3. Create .claude/commands/deploy.md with extracted procedure

## Rewritten CLAUDE.md
[Final file, ready to commit]
```

## Key Constraints It Enforces

| Antipattern | Action |
|-------------|--------|
| >300 lines | Critical issue → full rewrite |
| >100 instructions | Critical issue → extract non-universal content |
| Inline style rules with linter | Remove entirely |
| Stale commands | Fix or flag |
| No progressive disclosure | Extract + pointer |
| Hook-enforceable rules | Recommend PreToolUse hook |
| Module-specific content in root | Recommend subdirectory CLAUDE.md |

## CLI (Direct)

```bash
# Heuristic mode (no API key)
uv run python -m wfc.scripts.orchestrators.claude_md.cli . --no-llm

# Full LLM pipeline
uv run python -m wfc.scripts.orchestrators.claude_md.cli .

# Write result after approval
uv run python -m wfc.scripts.orchestrators.claude_md.cli . --write

# JSON output for scripting
uv run python -m wfc.scripts.orchestrators.claude_md.cli . --json

# Save report to file
uv run python -m wfc.scripts.orchestrators.claude_md.cli . --output report.md
```

## Architecture

```
wfc/scripts/orchestrators/claude_md/
├── __init__.py
├── schemas.py          # Shared dataclasses (ContextManifest, Diagnosis, etc.)
├── context_mapper.py   # Local filesystem inventory (no LLM)
├── prompts.py          # Agent XML system prompts
├── analyst.py          # Diagnostic rubric scoring
├── fixer.py            # Subtraction-first rewriter
├── qa_validator.py     # Adversarial validator + rule-based checks
├── reporter.py         # Markdown report generator
├── orchestrator.py     # Pipeline coordinator
└── cli.py              # CLI entry point
```

## Philosophy

- **Subtract first**: primary metric is instruction count reduction
- **Fail-open**: errors in any agent return the original file unchanged
- **Human approval**: pipeline produces recommendations, never auto-deploys
- **Heuristic fallback**: works without LLM via rule-based agents
- **Deterministic core**: Context Mapper and QA rule-based checks are LLM-free
