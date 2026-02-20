---
name: wfc-plan
description: Adaptive planning system that converts requirements into structured implementation plans. Conducts intelligent interview to understand goals, then generates TASKS.md (with dependencies), PROPERTIES.md (formal properties like SAFETY, PERFORMANCE), and TEST-PLAN.md. Use when starting new features, projects, or refactoring efforts that need structured planning. Triggers on "plan this feature", "break down these requirements", "create implementation plan", or explicit /wfc-plan. Ideal for medium-to-large features requiring coordination. Not for quick bug fixes or single-file changes.
license: MIT
---

# WFC:PLAN - Adaptive Planning with Formal Properties

Converts requirements into structured implementation plans through adaptive interviewing.

## What It Does

1. **Adaptive Interview** - Asks intelligent questions that adapt based on answers
2. **Task Generation** - Breaks down requirements into structured TASKS.md with dependencies
3. **Property Extraction** - Identifies formal properties (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
4. **Test Planning** - Creates comprehensive TEST-PLAN.md linked to requirements and properties

## Usage

```bash
# Default (creates timestamped plan with history)
/wfc-plan
# → Generates: plans/plan_oauth2_authentication_20260211_143022/
#              plans/HISTORY.md
#              plans/HISTORY.json

# Custom output directory (disables history)
/wfc-plan path/to/output

# With options (future)
/wfc-plan --interactive  # Step through interview
/wfc-plan --from-file requirements.md  # Import requirements

# Skip validation (not recommended)
/wfc-plan --skip-validation
```

## Plan History

**Each plan gets a unique timestamped directory.**

### Directory Structure

```
plans/
├── HISTORY.md                                    # Human-readable history
├── HISTORY.json                                  # Machine-readable index
├── plan_oauth2_authentication_20260211_143022/  # Timestamped plan
│   ├── TASKS.md
│   ├── PROPERTIES.md
│   ├── TEST-PLAN.md
│   ├── interview-results.json
│   ├── revision-log.md
│   └── plan-audit_20260211_143022.json
├── plan_caching_layer_20260211_150135/
│   ├── TASKS.md
│   ├── PROPERTIES.md
│   ├── TEST-PLAN.md
│   ├── interview-results.json
│   ├── revision-log.md
│   └── plan-audit_20260211_150135.json
└── plan_user_dashboard_20260212_091523/
    ├── TASKS.md
    ├── PROPERTIES.md
    ├── TEST-PLAN.md
    ├── interview-results.json
    ├── revision-log.md
    └── plan-audit_20260212_091523.json
```

### History File

**plans/HISTORY.md** contains a searchable record:

```markdown
# Plan History

**Total Plans:** 3

---

## plan_user_dashboard_20260212_091523
- **Created:** 2026-02-12T09:15:23
- **Goal:** Build user analytics dashboard
- **Context:** Product team needs visibility into user behavior
- **Directory:** `plans/plan_user_dashboard_20260212_091523`
- **Tasks:** 7
- **Properties:** 4
- **Tests:** 15
- **Validated:** yes (score: 8.7)

## plan_caching_layer_20260211_150135
- **Created:** 2026-02-11T15:01:35
- **Goal:** Implement caching layer for API
- **Context:** Reduce database load and improve response times
- **Directory:** `plans/plan_caching_layer_20260211_150135`
- **Tasks:** 3
- **Properties:** 2
- **Tests:** 8
- **Validated:** skipped
```

### Benefits

- **Version control** - Never lose old plans
- **Searchable** - Find plans by goal or date
- **Traceable** - See evolution of project planning
- **Reference** - Compare approaches across time

## Architecture Design Phase

After the interview, WFC generates 2-3 architecture approaches:

### Option 1: Minimal Changes

- Smallest diff, maximum code reuse
- Lowest risk, fastest to implement
- Best for simple features or hotfixes

### Option 2: Clean Architecture

- Proper abstractions, maintainability-first
- Best long-term design
- Higher initial effort

### Option 3: Pragmatic Balance

- Speed + quality tradeoff
- Addresses key concerns without over-engineering
- Best for most features

The approaches are saved to `ARCHITECTURE-OPTIONS.md` for reference.

## Interview Process

The adaptive interview gathers:

### Core Understanding

- What are you building? (goal)
- Why are you building it? (context)
- Who will use it? (users)

### Requirements

- Core features (must-have)
- Nice-to-have features
- Technical constraints
- Performance requirements
- Security requirements

### Technical Details

- Technology stack
- Existing codebase or new project
- Testing approach
- Coverage targets

### Formal Properties

- Safety properties (what must never happen)
- Liveness properties (what must eventually happen)
- Invariants (what must always be true)
- Performance properties (time/resource bounds)

## Outputs

### 1. TASKS.md

Structured implementation tasks with:

- Unique IDs (TASK-001, TASK-002, ...)
- Complexity ratings (S, M, L, XL)
- Dependency graph (DAG)
- Properties to satisfy
- Files likely affected
- Acceptance criteria

Example:

```markdown
## TASK-001: Setup project structure
- **Complexity**: S
- **Dependencies**: []
- **Properties**: []
- **Files**: README.md, pyproject.toml
- **Description**: Create initial project structure
- **Acceptance Criteria**:
  - [ ] Project structure follows best practices
  - [ ] Dependencies documented
```

### 2. PROPERTIES.md

Formal properties with:

- Type (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
- Formal statement
- Rationale
- Priority
- Suggested observables

Example:

```markdown
## PROP-001: SAFETY
- **Statement**: Unauthenticated user must never access protected endpoints
- **Rationale**: Security: prevent unauthorized data access
- **Priority**: critical
- **Observables**: auth_failures, unauthorized_access_attempts
```

### 3. TEST-PLAN.md

Test strategy and cases:

- Testing approach (unit, integration, e2e)
- Coverage targets
- Specific test cases linked to tasks and properties
- Test steps and expected outcomes

Example:

```markdown
### TEST-001: Verify SAFETY property
- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-001
- **Description**: Test that unauthenticated users cannot access protected endpoints
- **Steps**:
  1. Attempt access without authentication
  2. Verify 401 response
- **Expected**: Access denied
```

## Architecture

### MULTI-TIER Design

```
┌─────────────────────────────┐
│  PRESENTATION (cli.py)      │  User interaction, output formatting
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  LOGIC (orchestrator.py)    │  Interview → Generate → Save
│  - interview.py             │
│  - tasks_generator.py       │
│  - properties_generator.py  │
│  - test_plan_generator.py   │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  DATA (filesystem)          │  Save markdown and JSON
└─────────────────────────────┘
```

## Living Plan Documents

Plans are living documents that track progress during implementation, not static artifacts.

### YAML Frontmatter

Every TASKS.md includes frontmatter for machine-readable status tracking:

```yaml
---
title: OAuth2 Authentication
status: active          # active | in_progress | completed | abandoned
created: 2026-02-18T14:30:00Z
updated: 2026-02-18T16:45:00Z
tasks_total: 5
tasks_completed: 0
complexity: M
---
```

### Checkbox Progress

Each acceptance criterion uses markdown checkboxes. wfc-implement updates these as tasks complete:

```markdown
## TASK-001: Setup project structure
- **Status**: completed
- **Acceptance Criteria**:
  - [x] Project structure follows best practices
  - [x] Dependencies documented

## TASK-002: Implement JWT auth
- **Status**: in_progress
- **Acceptance Criteria**:
  - [x] Token generation works
  - [ ] Token refresh implemented
  - [ ] Rate limiting on auth endpoints
```

### Status Lifecycle

```
active → in_progress → completed
                    ↘ abandoned (with reason)
```

- **active**: Plan created, not yet started
- **in_progress**: wfc-implement is executing tasks
- **completed**: All tasks done, tests passing, PR merged
- **abandoned**: Scope changed, plan no longer relevant (reason recorded)

### Divergence Tracking

When implementation diverges from the plan, wfc-implement records it:

```markdown
## Divergence Log

### TASK-003: Redis caching layer
- **Planned**: Use Redis Cluster with 3 nodes
- **Actual**: Switched to single Redis instance (sufficient for current scale)
- **Reason**: Over-engineered for <1000 req/s
- **Impact**: TASK-004 dependency removed (cluster config no longer needed)
```

### Knowledge Integration

Plans automatically search `docs/solutions/` (via wfc-compound) during generation:

```markdown
## TASK-005: Connection pool configuration
- **Known pitfall**: docs/solutions/performance-issues/redis-pool-exhaustion.md
  - Size pools relative to worker count, not static
  - Monitor utilization > 80%
```

## Integration with WFC

### Produces (consumed by wfc-implement, wfc-deepen, wfc-lfg)

- `plan/TASKS.md` → Task orchestration (living document)
- `plan/PROPERTIES.md` → TDD test requirements
- `plan/TEST-PLAN.md` → Test strategy

### Consumes

- `docs/solutions/` → Past solutions for pitfall warnings (via wfc-compound)
- `wfc-architecture` → Architecture analysis
- `wfc-security` → Threat model properties

## Configuration

```json
{
  "plan": {
    "output_dir": "./plan",
    "interview_mode": "adaptive",
    "task_complexity_model": "auto",
    "generate_diagram": true
  }
}
```

## What to Do

1. **If `$ARGUMENTS` contains `--skip-validation`**, set `skip_validation = true` and remove the flag from arguments
2. **If `$ARGUMENTS` is provided** (after flag removal), use it as output directory
3. **If no arguments**, use `./plan` as default output directory
4. **Run adaptive interview** using `AdaptiveInterviewer`
5. **Generate all files** using orchestrator (TASKS.md, PROPERTIES.md, TEST-PLAN.md)
6. **Run Plan Validation Pipeline** (unless `--skip-validation` was set)
7. **Display results** showing file paths and summary
8. **Record telemetry** for all operations

## Plan Validation Pipeline

After generating the draft plan (TASKS.md, PROPERTIES.md, TEST-PLAN.md), run a mandatory validation pipeline to ensure plan quality. This pipeline can only be bypassed with the `--skip-validation` flag.

### Pipeline Overview

```
Draft Plan → SHA-256 Hash → Validate Gate → Revise → Review Gate (loop until 8.5+) → Final Plan
```

### Step 1: Record Original Hash

Compute a SHA-256 hash of the draft plan content (concatenation of TASKS.md + PROPERTIES.md + TEST-PLAN.md in that order). This is the `original_hash` used for the audit trail.

```python
import hashlib
content = tasks_md + properties_md + test_plan_md
original_hash = hashlib.sha256(content.encode()).hexdigest()
```

### Step 2: Validate Gate

Invoke `/wfc-validate` on the generated draft plan. All plan content **must** be delimited with XML tags per PROP-009 prompt injection defense:

```
/wfc-validate
<plan-content>
[Full content of TASKS.md, PROPERTIES.md, TEST-PLAN.md concatenated]
</plan-content>
```

This produces a `VALIDATE.md` output with scored recommendations categorized as Must-Do, Should-Do, or informational.

### Step 3: Revision Mechanism

After validation produces its analysis, read the VALIDATE.md output and apply revisions:

1. **Must-Do** recommendations: Apply every Must-Do change to the draft TASKS.md and/or PROPERTIES.md. These are non-negotiable improvements identified by the analysis.
2. **Should-Do** recommendations: Apply if low-effort (can be done in under 5 minutes). Otherwise, note as deferred with a reason.
3. **Deferred** items: Record in revision log for future consideration.

Write a `revision-log.md` in the plan directory documenting what changed and why:

```markdown
# Revision Log

## Original Plan Hash
`<original_hash>` (SHA-256)

## Validate Score
<score>/10

## Revisions Applied

### Must-Do

1. **<change title>** - <description of change>
   - Source: Validate recommendation #N
   - File changed: TASKS.md | PROPERTIES.md | TEST-PLAN.md

### Should-Do

1. **<change title>** - <description>
   - Source: Validate recommendation #N
   - Status: Applied (low effort) | Deferred (high effort)

### Deferred

1. **<item>** - <reason for deferral>
   - Source: Validate recommendation #N
   - Reason: <explanation>

## Review Gate Results

| Round | Score | Action |
|-------|-------|--------|
| 1     | X.X   | Applied N findings |
| 2     | X.X   | Passed threshold |

## Final Plan Hash
`<final_hash>` (SHA-256)
```

### Step 4: Review Gate

Invoke `/wfc-review` on the revised plan using architecture and quality personas. Plan content **must** be delimited with XML tags per PROP-009 prompt injection defense:

```
/wfc-review
<plan-content>
[Full content of revised TASKS.md, PROPERTIES.md, TEST-PLAN.md]
</plan-content>
```

**Review Loop**: If the weighted consensus score is below 8.5/10, apply the review findings to the plan and re-invoke `/wfc-review`. Repeat until the score reaches 8.5 or higher. This threshold is the standard -- it is not optional.

### Step 5: Audit Trail

After the review gate passes (or validation is skipped), write a `plan-audit.json` file (timestamped) in the plan directory. The filename includes a timestamp for immutability (e.g., `plan-audit_20260215_103000.json`).

**Required schema for plan-audit_YYYYMMDD_HHMMSS.json:**

```json
{
  "hash_algorithm": "sha256",
  "original_hash": "<64-char hex SHA-256 of draft plan>",
  "validate_score": 7.8,
  "revision_count": 2,
  "review_score": 8.7,
  "final_hash": "<64-char hex SHA-256 of final plan>",
  "timestamp": "2026-02-15T10:30:00Z",
  "validated": true,
  "skipped": false
}
```

Field definitions:

- `hash_algorithm`: Always `"sha256"`
- `original_hash`: SHA-256 hash of the draft plan before any revisions
- `validate_score`: Numeric score from the validation analysis
- `revision_count`: Total number of revision rounds applied (validation revisions + review loop rounds)
- `review_score`: Final weighted consensus score from wfc-review (numeric, e.g. 8.7)
- `final_hash`: SHA-256 hash of the plan after all revisions are complete
- `timestamp`: ISO 8601 timestamp of when validation completed
- `validated`: `true` if the final review_score >= 8.5, `false` otherwise
- `skipped`: `true` if `--skip-validation` was used, `false` otherwise

### Step 6: History Update

Update HISTORY.md to record whether the plan was validated or skipped. Add a `- **Validated:** yes (score: X.X)` or `- **Validated:** skipped` entry to the plan's history record.

### Skip Validation Flag

If `--skip-validation` is passed as an argument:

1. Skip Steps 2-4 entirely (no Validate Gate, no Review Gate, no revision)
2. Still compute SHA-256 hashes (original_hash = final_hash since no changes were made)
3. Write `plan-audit_YYYYMMDD_HHMMSS.json` with `"skipped": true` and `"validated": false`
4. Do not generate `revision-log.md` (no revisions occurred)
5. Record `- **Validated:** skipped` in HISTORY.md

### Validation Pipeline Summary

| Step | Action | Output |
|------|--------|--------|
| 1 | SHA-256 hash of draft plan | `original_hash` |
| 2 | `/wfc-validate` with `<plan-content>` XML tags (PROP-009) | VALIDATE.md |
| 3 | Apply Must-Do + low-effort Should-Do revisions | revision-log.md, updated plan files |
| 4 | `/wfc-review` with `<plan-content>` XML tags (PROP-009), loop until >= 8.5 | Review consensus |
| 5 | Write plan-audit_YYYYMMDD_HHMMSS.json with all fields | plan-audit_YYYYMMDD_HHMMSS.json |
| 6 | Update HISTORY.md with validation status | HISTORY.md entry |

## Example Flow

```
User runs: /wfc-plan

[ADAPTIVE INTERVIEW]
Q: What are you trying to build?
A: REST API for user management

Q: What are the core features?
A: User CRUD, authentication, role-based access

Q: Security requirements?
A: JWT tokens, role-based authorization

[GENERATION]
Created TASKS.md (5 tasks)
Created PROPERTIES.md (3 properties: 1 SAFETY, 2 INVARIANT)
Created TEST-PLAN.md (12 test cases)

[PLAN VALIDATION PIPELINE]
SHA-256 hash recorded: a1b2c3...
Validate Gate: 7.8/10
  - Applied 2 Must-Do revisions
  - Applied 1 Should-Do revision (low effort)
  - Deferred 1 suggestion
Review Gate round 1: 8.1/10 - applying 2 findings
Review Gate round 2: 8.7/10 - PASSED
Wrote revision-log.md
Wrote plan-audit_YYYYMMDD_HHMMSS.json

[OUTPUT]
plans/plan_rest_api_20260215_103000/
  - TASKS.md
  - PROPERTIES.md
  - TEST-PLAN.md
  - interview-results.json
  - revision-log.md
  - plan-audit_20260215_103000.json

Next: Run `/wfc-implement plans/plan_rest_api_20260215_103000/TASKS.md`
```

## Philosophy

**ELEGANT**: Simple interview questions, clear task breakdown
**MULTI-TIER**: Clean separation of presentation, logic, and data
**PARALLEL**: Can generate all three files concurrently (future optimization)
