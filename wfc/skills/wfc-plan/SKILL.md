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
│   └── interview-results.json
├── plan_caching_layer_20260211_150135/
│   ├── TASKS.md
│   ├── PROPERTIES.md
│   ├── TEST-PLAN.md
│   └── interview-results.json
└── plan_user_dashboard_20260212_091523/
    ├── TASKS.md
    ├── PROPERTIES.md
    ├── TEST-PLAN.md
    └── interview-results.json
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

## plan_caching_layer_20260211_150135
- **Created:** 2026-02-11T15:01:35
- **Goal:** Implement caching layer for API
- **Context:** Reduce database load and improve response times
- **Directory:** `plans/plan_caching_layer_20260211_150135`
- **Tasks:** 3
- **Properties:** 2
- **Tests:** 8
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

## Integration with WFC

### Produces (consumed by wfc-implement)
- `plan/TASKS.md` → Task orchestration
- `plan/PROPERTIES.md` → TDD test requirements
- `plan/TEST-PLAN.md` → Test strategy

### Consumes (future)
- `wfc-architecture` for architecture analysis
- `wfc-security` for threat model properties

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

1. **If `$ARGUMENTS` is provided**, use it as output directory
2. **If no arguments**, use `./plan` as default output directory
3. **Run adaptive interview** using `AdaptiveInterviewer`
4. **Generate all files** using orchestrator
5. **Display results** showing file paths and summary
6. **Record telemetry** for all operations

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
✅ Created TASKS.md (5 tasks)
✅ Created PROPERTIES.md (3 properties: 1 SAFETY, 2 INVARIANT)
✅ Created TEST-PLAN.md (12 test cases)

[OUTPUT]
📁 ./plan/
  - TASKS.md
  - PROPERTIES.md
  - TEST-PLAN.md
  - interview-results.json

Next: Run `/wfc-implement ./plan/TASKS.md`
```

## Philosophy

**ELEGANT**: Simple interview questions, clear task breakdown
**MULTI-TIER**: Clean separation of presentation, logic, and data
**PARALLEL**: Can generate all three files concurrently (future optimization)
