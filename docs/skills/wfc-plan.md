# wfc-plan

## What It Does

`wfc-plan` runs an adaptive interview and converts your answers into three structured planning artifacts: `TASKS.md` (task breakdown with IDs, dependencies, and acceptance criteria), `PROPERTIES.md` (formal SAFETY, LIVENESS, INVARIANT, and PERFORMANCE properties), and `TEST-PLAN.md` (test cases linked to tasks and properties). After generating the draft, the plan automatically passes through a validation pipeline — `wfc-validate` scores it, `wfc-review` loops until a consensus score of 8.5 or above is reached — before writing an immutable audit trail.

## When to Use It

- Starting a medium-to-large feature that will take more than a day to implement
- You need to coordinate multiple related tasks with dependencies
- The feature has security or performance requirements that should be formalized as properties
- You want a living document that `wfc-implement` can execute and update as work proceeds
- You need a full audit trail (validation score, review score, SHA-256 plan hashes)

Do not use `wfc-plan` for quick bug fixes or single-file changes — use `/wfc-build` instead.

## Usage

```bash
/wfc-plan
/wfc-plan --skip-validation          # Skip validation pipeline (not recommended)
```

Plans are saved to `.development/plans/plan_{name}_{timestamp}/` with a history index at `.development/plans/HISTORY.md`.

## Example

```
User: /wfc-plan

[ADAPTIVE INTERVIEW]
Q: What are you trying to build?
A: REST API for user management

Q: What are the core features?
A: User CRUD, authentication, role-based access

Q: Security requirements?
A: JWT tokens, role-based authorization

Q: Performance requirements?
A: P99 latency under 200ms

[GENERATION]
Created TASKS.md (5 tasks, S/M complexity)
Created PROPERTIES.md (3 properties: 1 SAFETY, 2 INVARIANT)
Created TEST-PLAN.md (12 test cases)

[ARCHITECTURE OPTIONS]
Generated 3 approaches:
  Option 1: Minimal changes (lowest risk)
  Option 2: Clean architecture (maintainability-first)
  Option 3: Pragmatic balance (recommended)
Saved to ARCHITECTURE-OPTIONS.md

[VALIDATION PIPELINE]
SHA-256 hash recorded: a1b2c3...
Validate Gate: 7.8/10
  Applied 2 Must-Do revisions
  Applied 1 Should-Do revision
Review Gate round 1: 8.1/10 — applying 2 findings
Review Gate round 2: 8.7/10 — PASSED

Output: .development/plans/plan_rest_api_20260215_103000/
  TASKS.md, PROPERTIES.md, TEST-PLAN.md
  ARCHITECTURE-OPTIONS.md, interview-results.json
  revision-log.md, plan-audit_20260215_103000.json

Next: /wfc-implement .development/plans/plan_rest_api_20260215_103000/TASKS.md
```

## Options

```bash
/wfc-plan                     # Interactive interview, full validation pipeline
/wfc-plan --skip-validation   # Skip validation (creates audit trail with skipped=true)
```

## Integration

**Produces:**

- `TASKS.md` — task list consumed by `wfc-implement` and `wfc-deepen`
- `PROPERTIES.md` — formal properties used by TDD agents and `wfc-review`
- `TEST-PLAN.md` — test strategy linked to tasks and properties
- `ARCHITECTURE-OPTIONS.md` — 3 architecture approaches for human selection
- `revision-log.md` — record of all changes made during validation
- `plan-audit_{timestamp}.json` — immutable audit trail (original hash, validate score, review score, final hash)

**Consumes:**

- Your answers to the adaptive interview
- `docs/solutions/` — searched automatically for known pitfalls to surface as task warnings

**Next step:** Run `/wfc-deepen` to enrich the plan with parallel research, then `/wfc-implement` to execute it. Or run `/wfc-lfg` to do all three automatically.
