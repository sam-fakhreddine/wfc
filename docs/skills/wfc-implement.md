# wfc-implement

## What It Does

`wfc-implement` reads a `TASKS.md` file, resolves the task dependency graph, and orchestrates N parallel agents — each working in an isolated git worktree provisioned by `worktree-manager.sh`. Every agent follows a strict TDD cycle: write failing tests first, implement until tests pass, refactor, then run quality gates before submitting. Completed tasks are routed through consensus review, merged sequentially with rollback capability, and the final result is a PR targeting `develop`.

## When to Use It

- You have a `TASKS.md` from `wfc-plan` (or `wfc-deepen`) ready to execute
- The feature has multiple tasks that can run in parallel
- You want TDD enforced per task with automatic rollback if tests break
- You need a post-deploy validation plan generated from your formal properties

Use `/wfc-build` instead when you do not have a TASKS.md and want to skip formal planning.

## Usage

```bash
/wfc-implement
/wfc-implement --tasks path/to/TASKS.md
/wfc-implement --agents 5
/wfc-implement --dry-run
```

## Example

```
User: /wfc-implement --tasks .development/plans/plan_rest_api_20260215_103000/TASKS.md

Orchestrator: Parsing task graph...
  TASK-001 (S): Setup project structure     → no deps
  TASK-002 (M): Implement JWT auth          → deps: [TASK-001]
  TASK-003 (M): Add RBAC middleware         → deps: [TASK-002]
  TASK-004 (S): Write integration tests     → deps: [TASK-003]

Orchestrator: Spawning agents...
  Agent 1 → TASK-001 (worktree-1)
  [TASK-001 complete] → Agent 2 → TASK-002 (worktree-2)
  [TASK-002 complete] → Agent 3 → TASK-003 (worktree-3)
  [TASK-003 complete] → Agent 4 → TASK-004 (worktree-4)

TASK-001: ✅ TEST_FIRST → ✅ IMPLEMENT → ✅ REFACTOR → ✅ QUALITY → ✅ REVIEW
TASK-002: ✅ TEST_FIRST → ✅ IMPLEMENT → ✅ REFACTOR → ✅ QUALITY → ✅ REVIEW
TASK-003: ✅ TEST_FIRST → ✅ IMPLEMENT → ✅ REFACTOR → ✅ QUALITY → ✅ REVIEW
TASK-004: ✅ TEST_FIRST → ✅ IMPLEMENT → ✅ REFACTOR → ✅ QUALITY → ✅ REVIEW

Integration tests: 42 passed, 0 failed
Post-deploy plan: Generated from PROP-001 (SAFETY) + PROP-002 (PERFORMANCE)
Branch pushed: claude/rest-api-user-management
PR #51 created → https://github.com/user/repo/pull/51
```

## Options

```bash
/wfc-implement                       # Looks for TASKS.md in ./plan/
/wfc-implement --tasks path/TASKS.md # Specify tasks file
/wfc-implement --agents 5            # Override default agent count
/wfc-implement --strategy smart      # Agent assignment strategy
/wfc-implement --dry-run             # Show execution plan without running
```

## Integration

**Produces:**

- PR targeting `develop` branch
- Updated `TASKS.md` with checkbox progress and divergence log
- Post-deploy monitoring plan in the PR body (mapped from PROPERTIES.md)
- Agent telemetry and per-task review reports

**Consumes:**

- `TASKS.md` — task definitions, dependencies, acceptance criteria
- `PROPERTIES.md` — formal properties for TDD coverage and post-deploy validation
- `TEST-PLAN.md` — test strategy to guide each agent

**Next step:** Review the PR on GitHub. The TASKS.md file is updated in place as tasks complete — check it for divergence notes if implementation deviated from the plan.
