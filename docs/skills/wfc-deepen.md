# wfc-deepen

## What It Does

`wfc-deepen` takes an existing plan and enriches it with parallel research before implementation begins. It dispatches four subagents simultaneously — one searches the codebase for existing patterns, one searches `docs/solutions/` for past problems, one looks for external best practices and security guidelines, and one checks package versions for breaking changes and CVEs. Findings are woven into the existing TASKS.md, PROPERTIES.md, and TEST-PLAN.md as annotated research sections. The original task structure, IDs, and acceptance criteria are never altered.

## When to Use It

- You ran `wfc-plan` quickly and want deeper research before committing to implementation
- New information has surfaced after planning (a CVE advisory, a stakeholder concern, a relevant codebase pattern you missed)
- The feature touches security or performance and you want external best practice validation
- The plan validated at a borderline score and you want to strengthen it before implementing

Do not use `wfc-deepen` when the plan does not exist yet (use `/wfc-plan` first), or when requirements have fundamentally changed (re-plan instead).

## Usage

```bash
/wfc-deepen
/wfc-deepen plans/plan_oauth2_auth_20260218_140000/
/wfc-deepen --focus security
/wfc-deepen --focus performance
```

## Example

```
User: /wfc-deepen plans/plan_oauth2_auth_20260218_140000/

Loading plan artifacts...
  TASKS.md: 5 tasks
  PROPERTIES.md: 3 properties
  TEST-PLAN.md: 12 test cases

Dispatching 4 research agents in parallel...

Codebase Analyst:
  → Found existing auth middleware at auth/session.py:45
  → Annotated TASK-003 with pattern reference

Solutions Researcher:
  → Found docs/solutions/security-issues/jwt-refresh-race.md
  → Annotated TASK-003 with pitfall warning
  → Added TEST-015: JWT refresh token race condition to TEST-PLAN.md

Best Practices:
  → RS256 preferred over HS256 for multi-service architectures
  → Added PROP-007: SAFETY — JWT algorithm must be restricted to RS256
  → Added TEST-016: Algorithm confusion attack prevention

Dependency Analyst:
  → PyJWT 2.8+ required for algorithm restriction API
  → No CVEs found in current dependency set
  → Annotated TASK-001 with version constraint

Writing deepen-log.md...
Done. 4 annotations added, 1 new property, 2 new tests.
```

## Options

```bash
/wfc-deepen                           # Deepen the most recent plan
/wfc-deepen plans/plan_{name}_{ts}/  # Deepen a specific plan directory
/wfc-deepen --focus security          # Focus all agents on security research
/wfc-deepen --focus performance       # Focus all agents on performance research
```

## Integration

**Produces:**

- Updated `TASKS.md` — research annotations added per task (codebase patterns, pitfall warnings, dependency notes)
- Updated `PROPERTIES.md` — new properties discovered during research
- Updated `TEST-PLAN.md` — additional test cases from edge case and regression research
- `deepen-log.md` — timestamped record of agents run and changes made

**Consumes:**

- An existing plan directory (TASKS.md, PROPERTIES.md, TEST-PLAN.md)
- `docs/solutions/` knowledge base (via `wfc-compound`)
- Codebase grep and glob (codebase analyst)
- Package registries (dependency analyst)

**Next step:** Run `/wfc-implement` with the enriched plan. The research annotations will be visible to each implementation agent so they can apply the patterns and avoid the known pitfalls.
