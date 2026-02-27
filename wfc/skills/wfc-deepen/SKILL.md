---
name: wfc-deepen
description: >
  Augments an existing /wfc-plan directory by researching codebase patterns,
  project documentation, and dependency constraints to add supporting evidence
  to tasks. Reads TASKS.md and PROPERTIES.md, simulates parallel analysis across
  4 dimensions, and appends sourced findings as annotations. Does NOT modify
  task structure, add/remove tasks, or write implementation steps.

  Triggers: /wfc-deepen, /wfc-deepen <path>, "add research evidence to the plan",
  "validate plan against codebase patterns", "annotate plan with known pitfalls",
  "cross-reference plan with existing solutions".

  Not for: writing or expanding task implementation steps; decomposing tasks into
  subtasks; prioritizing or reordering tasks; adding or removing tasks; pre-planning
  research before a plan directory exists; targeted research on specific questions
  unrelated to plan validation; re-deepening plans with existing Research Findings
  sections (use --force to override); general research with no plan context.

license: MIT
---

# WFC:DEEPEN - Annotate Plan with Evidence

**"Draft fast. Sharpen with evidence."**

## What It Does

Researches an existing plan directory to add supporting evidence, known pitfalls, and codebase pattern references to tasks—without modifying task structure or content.

1. **Locate** - Resolve plan directory from path argument or discovery
2. **Ingest** - Load TASKS.md and PROPERTIES.md
3. **Investigate** - Analyze codebase patterns, solutions docs, and dependencies
4. **Annotate** - Append sourced findings as a dedicated section
5. **Verify** - Confirm task IDs and structure remain intact

## Usage

```bash
# Deepen plan in current directory
/wfc-deepen

# Deepen specific plan directory
/wfc-deepen plans/plan_oauth2_auth_20260218_140000/

# Deepen with security focus (filters findings to security-relevant items)
/wfc-deepen --focus security

# Force re-deepen on already-annotated plan
/wfc-deepen --force
```

## Path Resolution

When no path is provided:

1. Check current directory for `TASKS.md` → use current directory
2. Check `./plans/` subdirectories for `TASKS.md` → sort by `TASKS.md` modification time
3. If multiple candidates found → list them and abort with request for clarification
4. If no candidates found → abort with error "No plan directory found"

If path points to a file → resolve to parent directory.

## Prerequisites

Before dispatching research, verify:

- `TASKS.md` exists and contains ≥1 valid task ID pattern (e.g., `TASK-###:` or `## Task`)
- `TASKS.md` contains ≥100 tokens of semantic content
- If `## Research Findings (wfc-deepen)` section already exists and `--force` is not set → abort with message

## Research Dimensions

Four analysis dimensions are evaluated (sequentially or concurrently based on platform):

| Dimension | What It Analyzes | Output |
|-----------|------------------|--------|
| **Codebase Patterns** | Existing implementations, conventions, similar code in repo | Pattern references for relevant tasks |
| **Solutions Docs** | `docs/solutions/` for related problems and known pitfalls | Warning annotations, regression test suggestions |
| **Conventions** | Config files, README, inline documentation for stated standards | Convention notes for properties |
| **Dependencies** | Package manifests and lockfiles for version constraints | Compatibility notes, deprecation warnings |

**Important**: This skill does NOT access external package registries, CVE databases, or live documentation. All analysis is based on local files and general software engineering principles. For security-critical dependency verification, run external tools separately.

## Annotation Format

Findings are appended as a single section at the end of `TASKS.md`:

```markdown
---

## Research Findings (wfc-deepen)
<!-- Generated: 2026-02-18T14:30:00Z -->
<!-- Do not edit this section manually; regenerate with --force to update -->

### TASK-003: Implement JWT Authentication
- **Pattern**: See `auth/session.py:45` for existing middleware pattern
- **Pitfall**: See `docs/solutions/security-issues/jwt-refresh-race.md`
- **Convention**: Project uses dependency injection via `src/di/`

### TASK-005: Token Refresh Logic
- **Pitfall**: Race condition documented in solutions (see above)
- **Dependency**: PyJWT constraint is ^2.8.0 in requirements.txt

---
```

### What Doesn't Change

- Task IDs, dependencies, hierarchy, and acceptance criteria
- Order and structure of existing tasks
- Original plan content

### Conflict Resolution

If findings from different dimensions conflict (e.g., a pattern exists but the dependency is deprecated):

1. Include both findings with a `**Resolution Required**` marker
2. Do not attempt automatic resolution
3. Log the conflict in `deepen-log.md` for manual review

## Output Files

| File | Changes |
|------|---------|
| `TASKS.md` | Appends `## Research Findings (wfc-deepen)` section (or updates if --force) |
| `PROPERTIES.md` | May append convention-derived properties |
| `TEST-PLAN.md` | May append regression test suggestions from solutions |
| `deepen-log.md` | Created/updated with research summary |

## Deepen Log Format

```markdown
# Deepen Log

## Session
- **Timestamp**: 2026-02-18T14:30:00Z
- **Plan**: plans/plan_oauth2_auth_20260218_140000/
- **Focus**: general (or: security, performance, patterns, dependencies)

## Analysis Summary
| Dimension | Files Analyzed | Findings |
|-----------|----------------|----------|
| Codebase Patterns | 12 | 3 relevant patterns |
| Solutions Docs | 4 | 2 pitfalls, 1 regression test |
| Conventions | 3 | 2 coding standards |
| Dependencies | 2 | 1 deprecation warning |

## Conflicts Requiring Resolution
- TASK-005: Existing pattern uses deprecated library (see findings)

## Files Modified
- TASKS.md: Added Research Findings section (47 lines)
- TEST-PLAN.md: Added 1 regression test case
```

## Focus Areas

The `--focus` flag filters which findings are included in output:

- `security` → Include only security-relevant patterns, pitfalls, and dependency warnings
- `performance` → Include only performance-relevant findings
- `patterns` → Include only codebase pattern references
- `dependencies` → Include only dependency and compatibility notes
- (no flag) → Include all findings

If `--focus` value is not in the above list → abort with error "Unknown focus area: X. Valid: security, performance, patterns, dependencies."

## Integration with WFC

```
/wfc-plan → /wfc-deepen → /wfc-implement
```

- **Consumes**: Existing plan files, `docs/solutions/`, codebase files, package manifests
- **Consumed by**: `wfc-implement` (reads annotated tasks), `wfc-review` (uses findings as review context)

## Configuration

```json
{
  "deepen": {
    "focus_areas": ["security", "performance", "patterns", "dependencies"],
    "min_task_content_tokens": 100
  }
}
```

## Philosophy

**READ-ONLY**: Never modifies existing task content, only appends
**SOURCED**: Every finding cites a file path or specific source
**ACCRETIVE**: Multiple deepen runs append, never replace (unless --force)
**CONFLICT-EXPLICIT**: Conflicting findings are flagged, not silently resolved
