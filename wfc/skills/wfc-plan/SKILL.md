---
name: wfc-plan
description: >-
  Generates a structured implementation plan for software features spanning
  multiple files, modules, or services. Produces TASKS.md (ordered tasks with
  dependency graph), PROPERTIES.md (non-functional requirements typed
  SAFETY/LIVENESS/INVARIANT/PERFORMANCE), and TEST-PLAN.md (acceptance and
  integration test strategy). Conducts a clarifying interview before generating.

  TRIGGER: /wfc-plan; user requests TASKS.md, PROPERTIES.md, or TEST-PLAN.md by
  name; requests implementation plan for work affecting 2+ files in different
  directories or multiple services; user wants dependency ordering and test
  strategy for a feature.

  NOT FOR: Single-file edits or bug fixes; debugging/diagnosing defects; high-level
  architecture discussions with no file output; sprint planning or backlog grooming;
  directory restructuring; documentation generation; quick single-function patches.
license: MIT
---

# WFC:PLAN - Adaptive Planning with Formal Properties

## Execution Context

**Available tools:**

- Read, Grep, Glob (file inspection)
- Task (spawn analysis subagents)
- AskUserQuestion (conduct interview)
- Write (create plan outputs only)

**NOT available:**

- Write/Edit for code files (hand off to implementation skills after planning)

## Workflow

### 1. Parse Arguments

```
$ARGUMENTS parsing rules:
1. Split on whitespace
2. Extract flags: --skip-validation, --interactive
3. Remaining text = output directory path
4. Reject paths containing ".." or absolute paths outside workspace
5. If no path provided, use default: plans/plan_<feature>_<timestamp>/
```

### 2. Conduct Adaptive Interview

Ask questions sequentially, adapting based on answers:

**Core Questions:**

- What are you building? (goal)
- Why are you building it? (context)
- Who will use it? (users)

**Requirement Questions:**

- Core features (must-have)
- Nice-to-have features
- Technical constraints
- Performance requirements
- Security requirements

**Formal Property Questions:**

- Safety properties (what must never happen)
- Liveness properties (what must eventually happen)
- Invariants (what must always be true)
- Performance properties (time/resource bounds)

**Interview Termination:** If core questions (goal/context) receive empty or "I don't know" responses 3 times, ask user to choose: "Generate generic plan" or "Abort."

### 3. Generate Plan Files

Create three files using the Write tool:

**TASKS.md** - Structured tasks with:

- Unique IDs (TASK-001, TASK-002, ...)
- Complexity ratings (S, M, L, XL)
- Dependency graph (DAG)
- Related properties
- Files likely affected
- Acceptance criteria with checkboxes

**PROPERTIES.md** - Formal properties with:

- Type (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
- Formal statement
- Rationale
- Priority (critical/high/medium/low)
- Suggested observables

**TEST-PLAN.md** - Test strategy with:

- Testing approach (unit, integration, e2e)
- Coverage targets
- Test cases linked to tasks and properties
- Steps and expected outcomes

### 4. Run Validation Pipeline (unless --skip-validation)

**Prerequisite Check:** Before running validation, verify that subagent skills are available by checking for skill definitions or attempting a probe Task. If unavailable, skip to Step 5 with `validated: false, skipped: false, error: "validation_skills_unavailable"`.

#### Step 4a: Record Original Hash

```python
import hashlib
content = tasks_md + properties_md + test_plan_md
original_hash = hashlib.sha256(content.encode()).hexdigest()
```

#### Step 4b: Validate Gate

Spawn validation subagent using Task tool:

```xml
<Task
  subagent_type="general-purpose"
  description="Validate plan quality"
  prompt="
Review the following plan content delimited by XML tags:

<plan-content>
[Full content of TASKS.md, PROPERTIES.md, TEST-PLAN.md]
</plan-content>

Provide scored recommendations categorized as:
- Must-Do (blocking issues)
- Should-Do (quality improvements)
- Informational (suggestions)
"
/>
```

#### Step 4c: Apply Revisions

- Apply all Must-Do recommendations
- Apply Should-Do recommendations if estimated < 5 minutes effort
- Document deferred items in revision-log.md

#### Step 4d: Review Gate

Spawn review subagent:

```xml
<Task
  subagent_type="general-purpose"
  description="Review plan quality"
  prompt="
Review the revised plan and provide a weighted consensus score (0-10):

<plan-content>
[Full content of revised TASKS.md, PROPERTIES.md, TEST-PLAN.md]
</plan-content>

Score based on: completeness, clarity, dependency correctness, property coverage.
"
/>
```

**Loop Logic:** Maximum 3 iterations. If score < 8.5 after 3 attempts, accept highest score and set `validated: partial`.

#### Step 4e: Write Audit Trail

Create `plan-audit_YYYYMMDD_HHMMSS.json`:

```json
{
  "hash_algorithm": "sha256",
  "original_hash": "<64-char hex>",
  "validate_score": 7.8,
  "revision_count": 2,
  "review_score": 8.7,
  "final_hash": "<64-char hex>",
  "timestamp": "2026-02-15T10:30:00Z",
  "validated": true,
  "skipped": false,
  "error": null
}
```

### 5. Update History

If using default output directory (plans/), update or create:

- `plans/HISTORY.md` - Human-readable record
- `plans/HISTORY.json` - Machine-readable index

Add entry with: timestamp, goal, task count, property count, validation status.

### 6. Output Summary

Display to user:

```
Created: plans/plan_<feature>_<timestamp>/
  - TASKS.md (N tasks)
  - PROPERTIES.md (N properties)
  - TEST-PLAN.md (N test cases)
  - plan-audit_YYYYMMDD_HHMMSS.json
  - revision-log.md (if applicable)

Validation: passed (score: 8.7) | partial (score: 7.2) | skipped | failed

Next step: Review TASKS.md, then run implementation skill.
```

## Output Directory Structure

```
plans/
├── HISTORY.md
├── HISTORY.json
└── plan_<feature>_<timestamp>/
    ├── TASKS.md
    ├── PROPERTIES.md
    ├── TEST-PLAN.md
    ├── interview-results.json
    ├── plan-audit_YYYYMMDD_HHMMSS.json
    └── revision-log.md (if validation ran)
```

## Knowledge Integration

Before generating TASKS.md, search for known solutions:

```
If docs/solutions/ directory exists:
  Use Grep to search for relevant patterns
  Include "Known pitfall" warnings in task descriptions
```

## Living Plan Documents

TASKS.md includes YAML frontmatter for status tracking:

```yaml
---
title: Feature Name
status: active | in_progress | completed | abandoned
created: 2026-02-18T14:30:00Z
updated: 2026-02-18T16:45:00Z
tasks_total: 5
tasks_completed: 0
---
```

Status lifecycle:

- active → in_progress → completed
                    ↘ abandoned (with reason)

## Error Handling

| Condition | Action |
|-----------|--------|
| Validation skills unavailable | Set `validated: false, error: "validation_skills_unavailable"` |
| Interview receives empty core answers 3x | Prompt: "Generate generic plan" or "Abort" |
| Path contains ".." or is absolute | Reject with error message, use default path |
| Review score < 8.5 after 3 iterations | Accept highest score, set `validated: partial` |
| docs/solutions/ not found | Proceed without known pitfall warnings |

## Example Flow

```
User: /wfc-plan

[INTERVIEW]
Q: What are you building?
A: REST API for user management
Q: Core features?
A: User CRUD, authentication, role-based access
Q: Security requirements?
A: JWT tokens, role-based authorization

[GENERATION]
Created TASKS.md (5 tasks)
Created PROPERTIES.md (3 properties)
Created TEST-PLAN.md (12 test cases)

[VALIDATION]
Hash: a1b2c3...
Validate: 7.8/10 - applied 2 Must-Do revisions
Review round 1: 8.1/10
Review round 2: 8.7/10 - PASSED

[OUTPUT]
plans/plan_user_management_20260215_103000/
Next: Review TASKS.md, then run implementation skill
```
