# wfc-compound

## What It Does

`wfc-compound` documents a solved problem into the `docs/solutions/` knowledge base so it can be found automatically during future planning and review. It dispatches five parallel subagents to analyze the problem from different angles — context, root cause, related docs, prevention, and category — then the orchestrator assembles their findings into one structured markdown file with YAML frontmatter. Every solution document includes a before/after code example and a prevention checklist. Once filed, `wfc-plan` and `wfc-review` search this catalog automatically.

## When to Use It

- You just fixed a bug or solved a problem that took more than 15 minutes
- The root cause was non-obvious and the fix is worth remembering
- You want future implementations to avoid the same pitfall automatically
- You resolved a performance regression, security issue, or integration failure

Do not use `wfc-compound` for trivial fixes (typos, simple config changes, formatting).

## Usage

```bash
/wfc-compound
/wfc-compound "fixed N+1 query in user dashboard"
/wfc-compound "resolved Redis connection pool exhaustion under load"
```

`wfc-compound` also activates automatically when you say phrases like "that worked", "it's fixed", "problem solved", "root cause was...", or "the fix was...".

## Example

```
User: /wfc-compound "resolved Redis connection pool exhaustion under load"

Phase 1 — Parallel research (5 subagents)
  Context Analyzer:     API gateway, redis-client component, timeout symptoms
  Solution Extractor:   Static pool size (10) vs 500+ concurrent requests
  Related Docs Finder:  Found database-issues/connection-limits.md
  Prevention Strategist: Load test, monitor utilization > 80%, dynamic sizing
  Category Classifier:  performance-issues/redis-pool-exhaustion.md

Phase 2 — Assembly
  Writing docs/solutions/performance-issues/redis-pool-exhaustion.md...

Output:
  docs/solutions/performance-issues/redis-pool-exhaustion.md

  Title: Redis Connection Pool Exhaustion Under Load
  Category: performance-issues
  Tags: redis, connection-pool, performance, timeout
  Root cause: Static pool size didn't scale with worker count

  Includes:
    - Before/after code (static pool → dynamic scaling)
    - Prevention checklist (load test, alerting, pool sizing formula)
    - Related docs cross-references
    - PERFORMANCE property for future plans
```

## Options

```bash
/wfc-compound                              # Compound based on recent conversation context
/wfc-compound "description of problem"    # Provide explicit context
```

No additional flags. The category, filename, and directory structure are determined automatically by the Category Classifier subagent.

## Integration

**Produces:**

- One file at `docs/solutions/{category}/{filename}.md`
- YAML frontmatter (title, module, component, tags, category, date, severity, status, root_cause)
- Sections: Problem, Root Cause, Solution (with before/after code), Prevention, Related

**Consumes:**

- Recent conversation context (problem description, debugging steps taken)
- Git diff (recent changes that produced the fix)
- Existing `docs/solutions/` entries (for cross-referencing)

**Knowledge lifecycle:**

```
wfc-compound → docs/solutions/{category}/{file}.md
                    ↓
    Searched automatically by wfc-plan (pitfall warnings in tasks)
    Searched automatically by wfc-review (known past issues)
    Searched automatically by wfc-deepen (solutions researcher agent)
                    ↓
    Drift detection flags entries older than 180 days for review
```

**Next step:** No immediate follow-up required. The solution is indexed automatically. The next time you run `/wfc-plan` on a related feature, the relevant pitfall warnings will appear in the generated TASKS.md.
