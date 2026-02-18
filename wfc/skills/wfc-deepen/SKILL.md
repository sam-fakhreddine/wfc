---
name: wfc-deepen
description: Post-plan research enhancement that spawns parallel research subagents to deepen an existing plan with external best practices, framework documentation, codebase patterns, and past solutions. Takes a plan directory as input and enriches TASKS.md, PROPERTIES.md, and TEST-PLAN.md with research findings. Triggers on "deepen this plan", "research more", "enhance the plan", or explicit /wfc-deepen. Ideal after /wfc-plan when you want more thorough research without re-planning. Not for creating new plans.
license: MIT
---

# WFC:DEEPEN - Sharpen the Plan

**"Draft fast. Sharpen with evidence."**

## What It Does

Injects parallel research into an existing plan without re-running the full planning cycle.

1. **Ingest** - Load the plan artifacts (TASKS.md, PROPERTIES.md, TEST-PLAN.md)
2. **Investigate** - Dispatch parallel subagents for targeted evidence gathering
3. **Annotate** - Weave findings into existing plan files as research addenda
4. **Revalidate** - Confirm the annotated plan still clears validation

## Usage

```bash
# Deepen the most recent plan
/wfc-deepen

# Deepen a specific plan
/wfc-deepen plans/plan_oauth2_auth_20260218_140000/

# Deepen with focus area
/wfc-deepen --focus security
/wfc-deepen --focus performance
```

## When to Use

### Use wfc-deepen when:
- Plan created quickly and needs more research
- New information discovered after planning
- Stakeholder feedback requires deeper analysis
- Security/performance concerns need investigation

### Don't use when:
- Plan doesn't exist yet (use /wfc-plan)
- Requirements changed fundamentally (re-plan instead)
- Plan already validated with high score (>9.0)

## Parallel Research Agents

4 subagents run in parallel via Task tool:

| Agent | What It Researches | Enriches |
|-------|-------------------|----------|
| **Codebase Analyst** | Existing patterns, conventions, similar implementations in the repo | TASKS.md (files affected, patterns to follow) |
| **Solutions Researcher** | `docs/solutions/` for past related problems, known pitfalls | TASKS.md (warnings, gotchas), TEST-PLAN.md (regression cases) |
| **Best Practices** | External best practices, security guidelines, framework patterns | PROPERTIES.md (new properties), TEST-PLAN.md (edge cases) |
| **Dependency Analyst** | Package versions, breaking changes, compatibility, CVEs | TASKS.md (dependency notes), PROPERTIES.md (SAFETY properties) |

## Enrichment Process

### What Gets Added

```markdown
## TASK-003: Implement JWT Authentication
- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-001, PROP-002]
- **Files**: auth/jwt.py, auth/middleware.py

+ ## Research Findings (wfc-deepen)
+ - **Codebase pattern**: See auth/session.py:45 for existing auth middleware pattern
+ - **Known pitfall**: docs/solutions/security-issues/jwt-refresh-race.md
+ - **Best practice**: Use RS256 over HS256 for multi-service architectures
+ - **Dependency note**: PyJWT 2.8+ required for algorithm restriction
```

### What Doesn't Change

- Task IDs, dependencies, and structure remain unchanged
- Original acceptance criteria preserved
- Plan validation hash updated in audit trail

## Output

Enriched plan files in the same directory:
- `TASKS.md` - Tasks annotated with research findings
- `PROPERTIES.md` - New properties from security/performance research
- `TEST-PLAN.md` - Additional test cases from edge case research
- `deepen-log.md` - Record of what was researched and added

### Deepen Log Format

```markdown
# Deepen Log

## Research Date
2026-02-18T14:30:00Z

## Plan
plans/plan_oauth2_auth_20260218_140000/

## Agents Run
- Codebase Analyst: Found 3 relevant patterns
- Solutions Researcher: Found 2 related solutions
- Best Practices: Added 4 recommendations
- Dependency Analyst: Found 1 CVE advisory

## Changes Made
### TASKS.md
- TASK-003: Added codebase pattern reference (auth/session.py)
- TASK-005: Added known pitfall warning (JWT refresh race)

### PROPERTIES.md
- Added PROP-007: SAFETY - JWT algorithm must be restricted to RS256

### TEST-PLAN.md
- Added TEST-015: JWT refresh token race condition
- Added TEST-016: Algorithm confusion attack prevention
```

## Integration with WFC

### Typical Flow

```
/wfc-plan → /wfc-deepen → /wfc-implement
```

Or within /wfc-build for complex features:
```
Interview → Plan → Deepen → Implement → Review
```

### Consumed By
- **wfc-implement** - Reads enriched plan with research annotations
- **wfc-review** - Uses research findings as review context

### Consumes
- Existing plan files (TASKS.md, PROPERTIES.md, TEST-PLAN.md)
- `docs/solutions/` knowledge base
- Codebase patterns (via grep/glob)
- Package registries (for dependency analysis)

## Configuration

```json
{
  "deepen": {
    "max_research_agents": 4,
    "include_external_research": true,
    "focus_areas": ["security", "performance", "patterns", "dependencies"],
    "token_budget_per_agent": 2000
  }
}
```

## Philosophy

**DECOUPLED**: Planning and evidence-gathering run as separate phases
**CONCURRENT**: All research agents fire at once
**ACCRETIVE**: Findings layer on top — nothing gets stripped
**SOURCED**: Every annotation cites where it came from
