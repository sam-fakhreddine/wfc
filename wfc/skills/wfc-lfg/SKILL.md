---
name: wfc-lfg
description: Autonomous end-to-end pipeline that chains the full WFC workflow without stopping between steps. Runs plan, deepen, implement, review, resolve findings, and test in sequence. Triggers on "lfg", "ship it end to end", "full auto", "autonomous build", or explicit /wfc-lfg. Ideal for well-understood features where you trust the pipeline. Not for exploratory work or features requiring human decisions at each step.
license: MIT
---

# WFC:LFG - Full-Send Pipeline

**"One command. Zero hand-offs. PR on the other side."**

## What It Does

Sequences every WFC phase into a single unattended run. Output of each step feeds the next — you get a PR at the end.

```
/wfc-lfg "add rate limiting to API"
    ↓
1. wfc-plan (quick interview → TASKS.md)
    ↓
2. wfc-deepen (parallel research enrichment)
    ↓
3. wfc-implement (parallel agents, TDD, quality gates)
    ↓
4. wfc-review (5-agent consensus review)
    ↓
5. Resolve findings (fix review issues automatically)
    ↓
6. Test suite (run full test suite)
    ↓
7. Push + PR (branch pushed, PR created)
    ↓
DONE
```

## Usage

```bash
# Full autonomous pipeline
/wfc-lfg "add rate limiting to API"

# With explicit complexity hint
/wfc-lfg --complexity S "fix typo in error message"
/wfc-lfg --complexity L "refactor authentication system"

# Skip deepen for simple features
/wfc-lfg --skip-deepen "add health check endpoint"

# Dry run (show what would happen)
/wfc-lfg --dry-run "add caching layer"
```

## Pipeline Steps

### Step 1: Plan

```
Invoke /wfc-plan with feature description
  - Quick adaptive interview (3-5 questions)
  - Generate TASKS.md, PROPERTIES.md, TEST-PLAN.md
  - Skip validation for speed (--skip-validation)
```

**Why skip validation in LFG:** The review step (Step 4) catches quality issues. Validation in planning would double the feedback loop.

### Step 2: Deepen

```
Invoke /wfc-deepen on generated plan
  - Parallel research: codebase, solutions, best practices, dependencies
  - Enrich plan with findings
```

**Skip with:** `--skip-deepen` for simple, well-understood features.

### Step 3: Implement

```
Invoke /wfc-implement with enriched plan
  - Parse TASKS.md for task DAG
  - Spawn parallel agents in worktrees
  - Each agent: TDD → Quality → Submit
  - Merge sequentially with rollback
```

### Step 4: Review

```
Invoke /wfc-review on implementation
  - 5 specialist reviewers (Security, Correctness, Performance, Maintainability, Reliability)
  - Consensus Score calculation
  - Finding deduplication
```

### Step 5: Resolve

```
If CS indicates issues (Moderate or higher):
  - Parse review findings
  - For each finding with clear remediation:
    - Apply fix automatically
    - Run affected tests
  - For ambiguous findings:
    - Log as deferred (human review needed)
  - Re-run review if significant changes made
```

### Step 6: Test

```
Run full test suite
  - uv run pytest (or detected test command)
  - Integration tests if available
  - Quality checks (lint, format)
```

### Step 7: Ship

```
Push branch and create PR
  - Push to claude/* branch
  - Create GitHub PR targeting develop
  - Include review summary in PR body
  - Include post-deploy validation plan
```

## Guardrails

Even in autonomous mode, WFC maintains safety:

### Hard Stops (pipeline halts)
- Review CS >= 9.0 (Critical findings)
- Security findings with severity >= 8.5
- Test suite failure after resolve step
- Merge conflicts that can't be auto-resolved

### Soft Warnings (pipeline continues with note)
- Review CS 7.0-9.0 (Important findings deferred)
- Skipped reviewers (irrelevant file types)
- Deferred ambiguous findings

### Never Does
- Push to main/master
- Force push
- Skip TDD workflow
- Ignore security findings
- Merge without tests passing

## Output

When pipeline completes:

```
WFC:LFG Pipeline Complete

Feature: Add rate limiting to API
Duration: ~8 minutes

Steps:
  1. Plan:      TASKS.md (3 tasks, 2 properties)
  2. Deepen:    +2 patterns, +1 known pitfall
  3. Implement: 3/3 tasks complete (TDD)
  4. Review:    CS=2.8 (informational) - PASSED
  5. Resolve:   0 findings to fix
  6. Test:      42 tests passed, 0 failed
  7. Ship:      PR #47 created

Branch: claude/rate-limiting-api
PR: https://github.com/user/repo/pull/47

Post-Deploy Validation:
  - Monitor: rate_limit_hits, rate_limit_429_responses
  - Alert: rate_limit_429 > 5% of total requests
  - Window: 24 hours after deploy
```

## When to Use

### Use LFG when:
- Feature scope is clear from description
- You trust the pipeline for this type of work
- Want to parallelize and speed up delivery
- Working on well-understood codebase patterns

### Don't use when:
- Exploring ideas (use /wfc-vibe)
- Need human decisions at each step (use manual workflow)
- Critical security feature (use /wfc-plan + manual review)
- First-time in a new codebase (use step-by-step)

## Configuration

```json
{
  "lfg": {
    "skip_deepen_for_complexity": ["S"],
    "auto_resolve_threshold": 7.0,
    "hard_stop_threshold": 9.0,
    "require_test_pass": true,
    "create_pr": true,
    "pr_target": "develop"
  }
}
```

## Philosophy

**UNATTENDED**: Zero hand-offs between phases
**GUARDED**: Hard-stops on critical findings, main stays untouched
**SATURATING**: Concurrent where safe, serial where ordering matters
**AUDITABLE**: Every phase writes its own receipt
**OPT-IN**: You decide when to hand over the keys
