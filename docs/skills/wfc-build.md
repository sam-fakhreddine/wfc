# wfc-build

## What It Does

`wfc-build` is the "Intentional Vibe" skill — it runs a short adaptive interview (3-5 questions), assesses whether the task needs one agent or multiple, then delegates implementation to subagent(s) in isolated git worktrees. Each subagent follows a full TDD cycle (test first, implement, refactor), passes quality gates, goes through consensus review, and the result lands as a PR targeting the `develop` branch. The orchestrator never writes code itself — it only coordinates.

## When to Use It

- You have a single feature or small addition with a clear scope
- You want to move fast without formal upfront planning
- The request fits in one sentence: "add X to Y"
- You are okay with TDD, quality checks, and review running automatically
- You do not need formal SAFETY/LIVENESS properties or a multi-week task breakdown

Use `/wfc-plan` + `/wfc-implement` instead when the feature spans multiple weeks, has complex dependencies, or requires formal property verification.

## Usage

```bash
/wfc-build
/wfc-build "add rate limiting to API"
/wfc-build "add OAuth2 authentication to FastAPI backend"
```

## Example

```
User: /wfc-build "add rate limiting to API"

Orchestrator:
  Q: What's the main goal?
  A: Prevent API abuse — 100 requests/minute per user

  Q: Which endpoints?
  A: All /api/* endpoints

  Q: Tech stack?
  A: FastAPI, Redis for rate limit storage

  Q: Expected behavior on limit exceeded?
  A: Return 429 Too Many Requests

Orchestrator: Assessing complexity...
  → SIMPLE task (single component)
  → Spawning 1 subagent

Subagent-1 (worktree-1):
  ✅ TEST_FIRST: Write rate limit tests (RED)
  ✅ IMPLEMENT: Add FastAPI middleware + Redis client (GREEN)
  ✅ REFACTOR: Extract config, clean up
  ✅ QUALITY_CHECK: black, ruff, pytest → PASS
  ✅ SUBMIT: Agent report ready

Orchestrator:
  ✅ Routed to wfc-review (5 specialist reviewers)
  ✅ Consensus Score: 2.8 (informational) — PASSED
  ✅ Branch pushed: claude/rate-limiting-api
  ✅ PR #47 created → https://github.com/user/repo/pull/47
```

## Options

```bash
/wfc-build                           # Orchestrator asks "what are you building?"
/wfc-build "description"             # Start with a feature description
```

Complex tasks automatically spawn multiple parallel subagents (up to 3 by default). No flags are needed — the orchestrator decides based on scope.

## Integration

**Produces:**

- PR targeting `develop` branch (never `main`)
- Post-deploy monitoring plan in the PR body (metrics to watch, rollback criteria)
- Agent telemetry reports

**Consumes:**

- Your answers to the adaptive interview
- Existing codebase (subagents read relevant files)
- `docs/solutions/` knowledge base (for known pitfalls)

**Next step:** Review the PR on GitHub. `claude/*` branches auto-merge to `develop` when CI passes. `feat/*` branches require manual approval.
