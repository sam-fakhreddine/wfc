---
name: wfc-lfg
description: |-
  Executes the full WFC pipeline autonomously: plan → deepen → implement → review
  → resolve → test → push PR. Zero human interaction during execution. Terminal
  output is a PR on success; halts with a structured report on failure.

  Requirements:
  - Git repository with configured remote and clean working directory.
  - Authenticated `gh` CLI.
  - Target branch (default: develop) must exist on remote.

  Trigger: /wfc-lfg; "full wfc auto"; "ship it end to end" (requires active code
  context); regex pattern "^lfg (implement|build|add|create|refactor|fix) .{20,}$"

  Not for: single-stage requests (route to that skill), deployment/infra tasks,
  auth/encryption/compliance/PII features (need human review), requests with
  approval gates, vague descriptions (e.g., "fix some issues"), repositories with
  uncommitted changes, requests contradicting guardrails (e.g., "push to main").

license: MIT
---

# WFC:LFG - Autonomous Pipeline

**"One command. Structured output. PR on success, report on halt."**

## What It Does

Sequences every WFC phase into a single autonomous run. Output of each step feeds the next. No human interaction during execution.

```
/wfc-lfg "add rate limiting to API"
    ↓
1. wfc-plan (generate TASKS.md, PROPERTIES.md, TEST-PLAN.md)
    ↓
2. wfc-deepen (parallel research enrichment)
    ↓
3. wfc-implement (parallel agents, TDD, quality gates)
    ↓
4. wfc-review (5-agent consensus review)
    ↓
5. Resolve findings (auto-fix clear issues, halt on ambiguous)
    ↓
6. Test suite (run full test suite)
    ↓
7. Push + PR (branch pushed, PR created)
    ↓
DONE or HALT (with structured report)
```

## Pre-Flight Checks

Before starting the pipeline, verify:

```
0. Feature description present
   → A feature description is a human-readable string describing what to build.
   → A file path (starts with `/`, `./`, or `plans/`) is NOT a description.
   → If only a path was provided and no description string:
      HALT: "Feature description required.
      Usage: /wfc-lfg \"describe what to build\" [optional: path/to/plans/dir]
      Example: /wfc-lfg \"add rate limiting to the API\""

1. Working directory clean (git status --porcelain returns empty)
   → If dirty: HALT with "Commit or stash changes before running wfc-lfg"

1.5. WFC initialized
   → Run: ls .wfc/ 2>/dev/null
   → If .wfc/ directory is missing:
      HALT: "WFC not initialized in this repository.
      Run /wfc-init first, then re-run this command."

2. HEAD is not detached
   → If detached: HALT with "Checkout a branch before running wfc-lfg"

3. Target branch exists on remote (default: develop)
   → Run: git fetch origin develop
   → If missing: HALT with "Target branch 'develop' not found on remote"

4. Test command detection
   → Check: pytest.ini → "uv run pytest"
   → Check: pyproject.toml with pytest → "uv run pytest"
   → Check: package.json → "npm test"
   → Check: Makefile with "test" target → "make test"
   → If undetected: HALT with "No test runner found. Specify manually or add test infrastructure."
```

```
   4.5. No active plan in progress
      → Run: ls plans/*/TASKS.md 2>/dev/null | head -1
      → If an existing TASKS.md is found:
         PAUSE: "Existing TASKS.md found at [path].
         Running wfc-lfg will generate a new plan and may overwrite it.
         Proceed? (yes to continue, no to abort)"
         → Wait for user response before continuing.
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

# Dry run (show plan without executing)
/wfc-lfg --dry-run "add caching layer"
```

## Pipeline Steps

### Step 1: Plan

**Start of step**: Check for existing phase marker:

```bash
ls .wfc-progress/lfg-phase1-done.marker 2>/dev/null
```

If marker exists → skip this step entirely, proceed to Step 2.

```
Invoke /wfc-plan with feature description
  - NO interview (use --non-interactive flag)
  - Generate TASKS.md, PROPERTIES.md, TEST-PLAN.md
  - Validate description clarity
  - Fetch target branch: git fetch origin [pr_target]
```

**Output Schemas:**

```markdown
# TASKS.md
- [ ] Task description [P1|P2|P3]
  - Subtask: description
  - Files: path/to/file.py

# PROPERTIES.md
---
performance:
  - metric_name: threshold
security:
  - constraint: value
monitoring:
  - alert_name: condition
---

# TEST-PLAN.md
## Task: [task description]
- Given: [precondition]
- When: [action]
- Then: [expected result]
```

**Clarity Validation:**
If feature description lacks actionable specificity (e.g., "update the thing"), HALT immediately with:

```
WFC:LFG Clarity Check Failed

Description: "update the thing"
Reason: Description lacks actionable specificity.
Required: Specific component, action, and scope.

Example: "add rate limiting to the /api/v1 endpoints with 100 req/min threshold"
```

**Safety Validation:**
Before generating tasks, scan description for guardrail violations:

- "push to main" → HALT: "Guardrail violation: Cannot push to main/master"
- "print env vars" → HALT: "Security policy violation: Credential exposure risk"
- "disable auth" → HALT: "Exclusion match: Auth features require human review"

**End of Step 1**: Write phase marker:

```bash
mkdir -p .wfc-progress && touch .wfc-progress/lfg-phase1-done.marker
echo "[WFC-LFG] Phase 1/4 complete: Plan generated. Progress saved."
```

---

### Step 2: Deepen

**Start of step**: Check for phase 1 marker:

```bash
ls .wfc-progress/lfg-phase1-done.marker 2>/dev/null || echo "MISSING"
```

If missing → HALT: "Phase 1 (Plan) must complete before Deepen. Re-run from Step 1."

```
Invoke /wfc-deepen on generated plan
  - Parallel research: codebase, solutions, best practices, dependencies
  - Enrich plan with findings
```

**Skip with:** `--skip-deepen` or `--complexity S` (auto-skipped for S).

### Step 3: Implement

**Start of step**: Check for phase 2 marker:

```bash
ls .wfc-progress/lfg-phase2-done.marker 2>/dev/null || echo "MISSING"
```

If missing → HALT: "Phase 2 (Deepen) must complete before Implement. Re-run from Step 2."

```
Invoke /wfc-implement with enriched plan
  - Parse TASKS.md for task DAG (checkboxes with [P1/P2/P3])
  - Spawn parallel agents in worktrees
  - Each agent: TDD → Quality → Submit
  - Merge sequentially with rollback
```

**Worktree Management:**

```
Create: git worktree add .git/worktrees/wfc-{id} -b claude/{feature-slug}
Cleanup: git worktree remove .git/worktrees/wfc-{id} (on success or failure)
```

**End of Step 3**: Write phase marker:

```bash
touch .wfc-progress/lfg-phase3-done.marker
echo "[WFC-LFG] Phase 3/4 complete: Implementation done. Progress saved."
```

---

### Step 4: Review

**Start of step**: Check for phase 3 marker:

```bash
ls .wfc-progress/lfg-phase3-done.marker 2>/dev/null || echo "MISSING"
```

If missing → HALT: "Phase 3 (Implement) must complete before Review. Re-run from Step 3."

```
Invoke /wfc-review on implementation
  - 5 specialist reviewers (Security, Correctness, Performance, Maintainability, Reliability)
  - Consensus Score calculation
  - Finding deduplication
```

**Consensus Score Formula:**

```
CS = max(severity_scores) where severity_scores = [security, correctness, performance, maintainability, reliability]
Scale: 0.0 (no issues) to 10.0 (critical failure)
```

### Step 5: Resolve

```
If CS >= 7.0 (Moderate or higher):
  - Parse review findings
  - For each finding with code snippet remediation:
    - Apply fix
    - Run FULL test suite (affected test detection not implemented)
  - For findings without code snippets:
    - HALT: "Ambiguous finding requires human review: [finding]"
  - If fixes applied:
    - Increment resolve_iteration counter
    - If resolve_iteration > 2: HALT: "Max resolve iterations exceeded"
    - Re-run review (Step 4)
```

### Step 6: Test

```
Run test suite using detected command from Pre-Flight Check
  - Full suite required (no partial runs)
  - Quality checks: lint, format
  - If failure: HALT with test output
```

### Step 7: Ship

```
Push branch and create PR
  - Push to claude/* branch
  - Create GitHub PR targeting [pr_target] (default: develop)
  - PR body includes:
    - Feature summary
    - Review summary (CS score, findings resolved/deferred)
    - Test results summary
    - Post-deploy validation (derived from PROPERTIES.md monitoring section)
```

**Cleanup**: Remove phase markers from the completed run:

```bash
rm -f .wfc-progress/lfg-phase*.marker
echo "[WFC-LFG] Pipeline complete. Phase markers cleared."
```

---

## Guardrails

### Hard Stops (pipeline halts with report)

- Review CS >= 9.0 (Critical findings)
- Security findings with severity >= 8.5
- Test suite failure after resolve step
- Merge conflicts that can't be auto-resolved
- Max resolve iterations (2) exceeded
- Ambiguous findings (no code snippet remediation)
- Pre-flight check failures
- Clarity validation failures
- Safety validation failures (guardrail violations in description)

### Soft Warnings (pipeline continues with note)

- Review CS 7.0-9.0 (Important findings, auto-resolve attempted)
- Skipped reviewers (irrelevant file types)
- Deferred low-priority tasks from TASKS.md

### Never Does

- Push to main/master
- Force push
- Skip TDD workflow
- Ignore security findings
- Merge without tests passing
- Proceed with ambiguous findings
- Execute in dirty repository state

## Output

### Success Output

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

### Halt Output

```
WFC:LFG Pipeline Halted

Feature: Add rate limiting to API
Duration: ~4 minutes
Halt Reason: Review CS >= 9.0 (Critical finding)

Steps Completed:
  1. Plan:      TASKS.md (3 tasks, 2 properties)
  2. Deepen:    +2 patterns, +1 known pitfall
  3. Implement: 3/3 tasks complete (TDD)
  4. Review:    CS=9.2 (CRITICAL) - HALTED

Critical Findings:
  - [Security] Severity 9.2: Rate limiter bypass vulnerability in header parsing
    - File: src/middleware/rate_limit.py:47
    - Remediation: N/A (requires architectural decision)

Resolution Required:
  Manual review needed for security finding.
  Run: /wfc-review --full for complete report.

Branch preserved: claude/rate-limiting-api
Worktree cleaned up.
```

## When to Use

### Use LFG when

- Feature scope is clear and actionable from description
- Repository is in clean state
- Target branch exists on remote
- Test infrastructure is configured
- Working on well-understood codebase patterns
- No auth/encryption/compliance concerns

### Don't use when

- Exploring ideas (use /wfc-vibe)
- Need human decisions at each step (use manual workflow)
- Critical security feature (use /wfc-plan + manual review)
- First-time in a new codebase (use step-by-step)
- Repository has uncommitted changes
- Description is vague or non-actionable
- Request contradicts guardrails

## Configuration

```json
{
  "lfg": {
    "skip_deepen_for_complexity": ["S"],
    "auto_resolve_threshold": 7.0,
    "hard_stop_threshold": 9.0,
    "max_resolve_iterations": 2,
    "require_test_pass": true,
    "create_pr": true,
    "pr_target": "develop",
    "worktree_path": ".git/worktrees/wfc-{id}"
  }
}
```

## Philosophy

**AUTONOMOUS**: Zero human interaction during execution
**GUARDED**: Hard-stops on critical findings, main stays untouched
**AUDITABLE**: Every phase writes receipts; halt reports preserve state
**SAFE**: Pre-flight checks prevent execution in invalid states
**TRANSPARENT**: Halt conditions are explicit and actionable
