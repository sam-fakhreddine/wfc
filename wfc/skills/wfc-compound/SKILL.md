---
name: wfc-compound
description: Knowledge codification skill that documents solved problems into searchable docs/solutions/ categories. Runs parallel subagents (context analyzer, solution extractor, related docs finder, prevention strategist, category classifier) then assembles a single searchable solution document. Triggers on "that worked", "it's fixed", "problem solved", "document this solution", or explicit /wfc-compound. Ideal after solving non-trivial bugs, performance issues, or integration problems. Not for trivial fixes or documentation-only changes.
license: MIT
---

# WFC:COMPOUND - Distill What You Learned

**"Solve it once. Write it down. Look it up forever."**

## What It Does

Distills solved problems into structured, indexed knowledge that feeds back into planning and review.

1. **Recognize** - Detects a resolved issue (auto-trigger or explicit invocation)
2. **Decompose** - Parallel subagents pull apart context, root cause, fix, prevention, and category
3. **Synthesize** - Orchestrator consolidates into one searchable markdown file
4. **Catalog** - Filed under `docs/solutions/{category}/` with YAML frontmatter
5. **Wire In** - wfc-plan and wfc-review query the catalog during their workflows

## Usage

```bash
# After solving a problem
/wfc-compound

# With description
/wfc-compound "fixed N+1 query in user dashboard"

# With explicit context
/wfc-compound "resolved Redis connection pool exhaustion under load"
```

## Auto-Trigger Phrases

wfc-compound activates when you say:

- "that worked"
- "it's fixed"
- "problem solved"
- "figured it out"
- "root cause was..."
- "the fix was..."

## Two-Phase Execution

### Phase 1: Parallel Research (subagents return TEXT only)

5 subagents run in parallel via Task tool. **None write files** — they return text to the orchestrator.

| Subagent | Role | Output |
|----------|------|--------|
| **Context Analyzer** | Extract problem type, component, symptoms | YAML frontmatter skeleton |
| **Solution Extractor** | Identify root cause, extract working solution with code | Solution section with code blocks |
| **Related Docs Finder** | Search `docs/solutions/` for related docs, cross-refs | Related documents list |
| **Prevention Strategist** | Develop prevention strategies, test cases, best practices | Prevention section |
| **Category Classifier** | Determine category, suggest filename | Category + filename |

### Phase 2: Assembly (orchestrator writes ONE file)

1. Collect all Phase 1 text results
2. Assemble complete markdown document
3. Create directory: `mkdir -p docs/solutions/{category}/`
4. Write SINGLE file: `docs/solutions/{category}/{filename}.md`

### Phase 3: Optional Enhancement (conditional, parallel)

Based on problem type, spawn specialized reviewers:

- `performance_issue` → Performance reviewer
- `security_issue` → Security reviewer
- `database_issue` → Data integrity check
- Code-heavy issues → Correctness + Maintainability reviewers

## Output Format

```markdown
---
title: Redis Connection Pool Exhaustion Under Load
module: api-gateway
component: redis-client
tags: [redis, connection-pool, performance, timeout]
category: performance-issues
date: 2026-02-18
severity: high
status: resolved
root_cause: Connection pool size was static (10) while concurrent requests scaled to 500+
---

# Redis Connection Pool Exhaustion Under Load

## Problem

**Symptoms:** API responses timing out after 30s under moderate load (>100 req/s)
**Environment:** Production, API gateway service
**First noticed:** 2026-02-17

## Root Cause

The Redis connection pool was configured with a static size of 10 connections.
Under load, 500+ concurrent requests competed for 10 connections, causing
queue backpressure and eventual timeouts.

## Solution

```python
# Before: static pool
redis_pool = redis.ConnectionPool(max_connections=10)

# After: dynamic pool scaled to worker count
import os
workers = int(os.getenv("WEB_CONCURRENCY", 4))
redis_pool = redis.ConnectionPool(
    max_connections=workers * 20,
    timeout=5,
    retry_on_timeout=True,
)
```

## Prevention

- **Test case:** Load test with 10x expected concurrent connections
- **Monitoring:** Alert on redis connection pool utilization > 80%
- **Best practice:** Size connection pools relative to worker/thread count, not static
- **Property:** PERFORMANCE - Redis pool utilization MUST stay below 80% at P99 load

## Related

- [Database Connection Limits](../database-issues/connection-limits.md)
- [API Timeout Configuration](../runtime-errors/api-timeout-config.md)

```

## Categories (Auto-Detected)

| Category | Directory | Trigger Signals |
|----------|-----------|-----------------|
| Build Errors | `build-errors/` | compile, build, bundle, webpack |
| Test Failures | `test-failures/` | test, assert, fixture, mock |
| Runtime Errors | `runtime-errors/` | exception, crash, timeout, 500 |
| Performance Issues | `performance-issues/` | slow, N+1, memory, latency |
| Database Issues | `database-issues/` | migration, query, connection, deadlock |
| Security Issues | `security-issues/` | auth, injection, CORS, token |
| UI Bugs | `ui-bugs/` | render, layout, CSS, responsive |
| Integration Issues | `integration-issues/` | API, webhook, third-party, sync |
| Logic Errors | `logic-errors/` | wrong result, edge case, off-by-one |
| Configuration | `configuration/` | env, config, deploy, infrastructure |

## Integration with WFC

### Consumed By
- **wfc-plan** - Searches `docs/solutions/` during planning to avoid repeating work
- **wfc-review** - Checks for related past issues during code review
- **wfc-build** - Quick knowledge lookup before implementation

### Consumes
- Git diff (recent changes that fixed the issue)
- Conversation context (problem description, debugging steps)
- Existing `docs/solutions/` entries (for cross-referencing)

### Knowledge Lifecycle

```

Problem Solved → /wfc-compound → docs/solutions/{category}/{file}.md
                                        ↓
                    Indexed by YAML frontmatter (title, tags, module, component)
                                        ↓
                    Searchable by wfc-plan, wfc-review, wfc-build
                                        ↓
                    Drift detection (staleness >180 days, contradictions)
                                        ↓
                    Promotion to global knowledge (~/.wfc/knowledge/global/)

```

## Configuration

```json
{
  "compound": {
    "solutions_dir": "docs/solutions",
    "auto_trigger": true,
    "require_code_examples": true,
    "require_prevention": true,
    "enhancement_threshold": "high"
  }
}
```

## Rules

1. **One file per compound** - Never create multiple files per invocation
2. **Orchestrator writes, subagents return text** - Clear write ownership
3. **Non-trivial problems only** - Skip typos, formatting, simple config changes
4. **Code examples required** - Before/after showing the actual fix
5. **Prevention required** - Every solution must include how to prevent recurrence
6. **Never overwrite** - If file exists, append or create new with timestamp suffix

## Philosophy

**COMPOUND**: Every fix sharpens the next one
**INDEXED**: YAML frontmatter powers machine and human lookup
**PRESCRIPTIVE**: Every entry carries code, prevention, and monitoring
**LEAN**: One file per problem, zero fluff
