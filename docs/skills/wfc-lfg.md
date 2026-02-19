# wfc-lfg

## What It Does

`wfc-lfg` is the full-auto pipeline. It chains every WFC phase in sequence — plan, deepen, implement, review, resolve findings, test suite, push, PR — without stopping for human input between steps. You give it a feature description, it gives you a PR. The pipeline has hard stops for critical security findings (CS >= 9.0) and test suite failure, so main stays clean. Everything else runs unattended.

## When to Use It

- The feature scope is clear from a one-sentence description
- You trust the pipeline for this class of work (e.g., adding a well-understood pattern like rate limiting, health checks, or CRUD endpoints)
- You want to parallelize delivery and come back to a ready-to-merge PR
- You are working in a well-understood codebase where conventions are established

Do not use `wfc-lfg` for exploratory work, features that need human decisions at each step, or critical security features that warrant manual review.

## Usage

```bash
/wfc-lfg "add rate limiting to API"
/wfc-lfg --complexity S "fix typo in error message"
/wfc-lfg --complexity L "refactor authentication system"
/wfc-lfg --skip-deepen "add health check endpoint"
/wfc-lfg --dry-run "add caching layer"
```

## Example

```
User: /wfc-lfg "add rate limiting to API"

Step 1 — Plan
  Quick interview (3 questions)
  TASKS.md: 3 tasks, 2 properties (SAFETY, PERFORMANCE)
  Validation skipped (review step covers quality)

Step 2 — Deepen
  Codebase Analyst: Found existing middleware pattern at api/middleware.py:12
  Solutions Researcher: Found redis-pool-exhaustion.md (known pitfall)
  Best Practices: Added RS256 recommendation to PROP-002
  Dependency Analyst: redis-py 4.6+ required for cluster support

Step 3 — Implement
  Agent 1: TASK-001 (rate limiter middleware) — TDD complete
  Agent 2: TASK-002 (Redis integration) — TDD complete
  Agent 3: TASK-003 (429 error handling) — TDD complete

Step 4 — Review
  CS = 2.8 (informational) — PASSED

Step 5 — Resolve
  0 findings to fix

Step 6 — Test
  42 tests passed, 0 failed

Step 7 — Ship
  Branch: claude/rate-limiting-api
  PR #47: https://github.com/user/repo/pull/47

Duration: ~8 minutes
```

## Options

```bash
/wfc-lfg "description"          # Full auto pipeline
/wfc-lfg --complexity S         # Hint: small, skip deepen automatically
/wfc-lfg --complexity L         # Hint: large, deepen thoroughly
/wfc-lfg --skip-deepen          # Skip research phase (faster for simple features)
/wfc-lfg --dry-run              # Show what would happen without executing
```

## Integration

**Produces:**

- PR targeting `develop` branch (never `main`)
- Full pipeline receipt (one log entry per step with duration and outcome)
- Post-deploy validation plan in the PR body

**Consumes:**

- Feature description (the argument you pass)
- `docs/solutions/` knowledge base (during deepen step)
- Existing codebase (agents read relevant files during implementation)

**Hard stops (pipeline halts entirely):**

- Review CS >= 9.0 (critical security or reliability finding)
- Test suite failure after the resolve step
- Merge conflict that cannot be auto-resolved

**Next step:** Review the PR on GitHub. `claude/*` branches auto-merge to `develop` when CI passes. You control when `develop` promotes to `main` via the release candidate process.
