---
name: wfc-implement
description: >-
  Orchestrates PARALLEL execution of an existing TASKS.md implementation plan
  using isolated git worktrees. STRICT REQUIREMENTS: (1) TASKS.md file exists
  with 2+ parseable tasks, (2) valid non-bare git repo with clean working
  directory, (3) user intent is purely EXECUTION of existing plan. FLOW:
  Validates TASKS.md -> Creates worktrees -> Spawns one agent per task ->
  Requests TDD workflow -> Runs mocked review -> Creates GitHub PRs targeting
  develop branch. TRIGGERS: /wfc-implement, "run the plan", "execute TASKS.md",
  "implement the tasks in TASKS.md". PREREQUISITE: Run /wfc-plan first. This skill requires TASKS.md to exist.
  NOT FOR: missing TASKS.md (use wfc-plan),
  single-task runs, inline task lists, plan-then-implement requests, cyclic
  dependencies, dirty repos, main-branch targets, security-sensitive work.
license: MIT
---

# wfc-implement - Multi-Agent Parallel Implementation Orchestrator

## HARD STOP — Read This Before Anything Else

**Step 1: Locate TASKS.md.**

Check in this order:

1. The path passed as argument (if any)
2. `./TASKS.md`
3. `./plans/*/TASKS.md` (first match)

If TASKS.md is not found at any location:

```
ABORT: No TASKS.md found.
This skill requires an existing plan.
Next step: run /wfc-plan "<your feature description>" to generate one.
Do not attempt manual implementation. Do not continue.
```

Stop here. Do not read the rest of this skill.

---

## Resume Detection

Before doing anything else, check:

```bash
cat .wfc-progress/implement-progress.json 2>/dev/null
```

If the file exists and `tasks_pending` is non-empty:

- Tell the user: "Found incomplete wfc-implement run from [last_updated]. tasks_pending: [list]. Resume? (yes/no)"
- If yes: skip Phase 1 setup for completed tasks, proceed from first task in `tasks_pending`
- If no: delete `.wfc-progress/implement-progress.json` and start fresh

---

## EXECUTION CONTEXT: ORCHESTRATION MODE

You are running in **orchestration mode** with restricted tool access.

**Available tools:**

- ✅ Read, Grep, Glob (read TASKS.md, inspect code)
- ✅ Task (REQUIRED for spawning implementation agents)
- ✅ Bash (git worktree operations: add, list, remove, prune)

**NOT available:**

- ❌ Write, Edit, NotebookEdit (delegated to spawned agents)

**Your role:** Validate inputs, create worktrees, spawn Task agents, coordinate completion, create PRs.

---

## Preconditions (MUST validate before execution)

1. **TASKS.md exists** - See HARD STOP block above. If missing, ABORT. Do not proceed.
2. **2+ parseable tasks** - Parse TASKS.md. If < 2 tasks, STOP with error: "TASKS.md requires 2+ tasks. For single tasks, use direct implementation."
3. **No cyclic dependencies** - Build dependency graph from TASKS.md. If cycle detected (A→B→A), STOP with error: "Cyclic dependency detected. Fix TASKS.md."
4. **Clean working directory** - Run `git status --porcelain`. If output non-empty, STOP: "Uncommitted changes detected. Commit or stash before running."
5. **Non-bare git repo** - Verify `.git` exists and is not bare.

---

## Execution Flow

### Phase 1: Setup

```bash
# Create worktree directory
mkdir -p .worktrees

# For each task, create isolated worktree
# Pattern: .worktrees/TASK-XXX/ branched from develop
git worktree add .worktrees/TASK-001 -b claude/TASK-001 develop
```

**Worktree naming convention**: `.worktrees/<task-id>/`
**Branch naming convention**: `claude/<task-id>` branched from `develop`

### Phase 2: Spawn Agents

#### Step 2.0: Canary Gate

Before spawning all agents, check if any task in TASKS.md has `canary: true`.

If a canary task exists:

1. Spawn ONLY that task's agent first.
2. Wait for its `agent-report.json` to be written.
3. Check `agent-report.json` → `"status"` field.
4. If status is `"failed"`: STOP all remaining agents.
   Output: "Canary task [TASK-ID] failed. Fix the issue before running the full batch. Error: [error field from report]"
5. If status is `"success"`: print "[WFC] Canary passed. Launching remaining [N-1] agents in parallel." and continue.

If no canary task exists: proceed directly to spawning all agents in parallel.

For each task in dependency order (respecting topological sort):

```xml
<Task
  subagent_type="general-purpose"
  description="Implement TASK-001"
  prompt="
Task ID: TASK-001
Task Description: [from TASKS.md]
Worktree Path: .worktrees/TASK-001/
Branch: claude/TASK-001

Context Files (read these first):
- TASKS.md (your task definition)
- PROPERTIES.md (if exists at project root - contains system properties to preserve)
- TEST-PLAN.md (if exists at project root - contains test guidance)

TDD Workflow (REQUESTED but not enforceable):
1. Read existing code and context files
2. Write tests FIRST (detect test framework from project: pytest, jest, go test, etc.)
3. Implement minimum code to pass tests
4. Run tests - must PASS
5. Run quality checks if tooling detected (lint, format) - skip if not configured

Deliverables:
1. Implementation committed to worktree branch
2. Tests passing
3. Agent report (JSON format - see below)

Agent Report Format (write to .worktrees/TASK-001/agent-report.json):
{
  \"task_id\": \"TASK-001\",
  \"status\": \"success\" | \"failed\",
  \"files_changed\": [\"path/to/file1\", ...],
  \"tests_added\": 3,
  \"tests_passed\": 3,
  \"quality_checks\": \"passed\" | \"skipped\" | \"failed\",
  \"summary\": \"Brief description of changes made\",
  \"properties_addressed\": [\"PROP-001\", ...]
}

On failure, set status to \"failed\" and include \"error\" field with details.
"
/>
```

### Phase 2.5: Write Progress Checkpoint

After all agents are spawned (not before), write:

```bash
mkdir -p .wfc-progress
cat > .wfc-progress/implement-progress.json << 'EOF'
{
  "skill": "wfc-implement",
  "started_at": "<ISO timestamp>",
  "tasks_total": <N>,
  "tasks_spawned": ["TASK-001", "TASK-002"],
  "tasks_pending": [],
  "last_updated": "<ISO timestamp>"
}
EOF
```

Update `tasks_pending` to remove a task ID when its agent-report.json is written.

---

### Phase 3: Collect Results

Wait for all spawned agents to complete. Track completion status per task.

**Synchronization**: All agents must complete before proceeding to merge phase.

### Phase 4: Mocked Review

**Current behavior**: Review is mocked. Auto-approve all completed tasks.

```
For each completed task:
  - Log: "TASK-XXX: Mock review PASSED"
  - No actual review invocation
```

**Future**: When wfc-consensus-review is implemented, this phase will invoke it.

### Phase 5: Create Pull Requests

For each successful task:

```bash
cd .worktrees/TASK-001
git push -u origin claude/TASK-001
gh pr create --base develop --title "TASK-001: [task summary]" --body-file .worktrees/TASK-001/pr-body.md --draft
```

**PR body template** (agent generates this):

```markdown
## Summary
[agent-report.json summary]

## Changes
- [list of files changed]

## Tests
- Added: X tests
- All passing: Yes

## Properties Addressed
- [list from agent-report.json]

---

## Post-Deploy Validation Template

> NOTE: Adapt these queries to your monitoring platform (Prometheus, Datadog, etc.)

| Property | Type | Suggested Metric | Threshold |
|----------|------|------------------|-----------|
| [from PROPERTIES.md] | [type] | [metric name] | [threshold] |

**Validation Window**: 24-72 hours depending on change scope

**Rollback Criteria**: Any SAFETY property violation
```

### Phase 6: Cleanup

On success:

```bash
git worktree remove .worktrees/TASK-001
```

On failure (orchestrator crash, partial completion):

```bash
# Manual recovery command
/wfc-implement --cleanup
# Removes all .worktrees/* directories
```

---

## Configuration

Default `wfc.config.json`:

```json
{
  "orchestration": {
    "max_parallel_agents": 5,
    "agent_timeout_seconds": 600
  },
  "worktree": {
    "directory": ".worktrees",
    "cleanup_on_success": true,
    "cleanup_on_failure": false
  },
  "git": {
    "branch_prefix": "claude",
    "target_branch": "develop",
    "pr_draft_by_default": true
  },
  "tdd": {
    "request_test_first": true,
    "require_tests_pass": true
  },
  "review": {
    "mode": "mocked",
    "mock_result": "approve"
  },
  "rollback": {
    "strategy": "report_only",
    "description": "Failed tasks are reported; no automatic retry. User decides next action."
  }
}
```

---

## Task File Formats

### TASKS.md Expected Structure

```markdown
# Implementation Plan

## TASK-001: Task Title
**Description**: What to implement
**Dependencies**: (none) | TASK-XXX, TASK-YYY
**Acceptance Criteria**:
- Criterion 1
- Criterion 2

## TASK-002: Another Task
...
```

### PROPERTIES.md Expected Structure (optional)

```markdown
# System Properties

## PROP-001: Property Name
**Type**: SAFETY | PERFORMANCE | LIVENESS | INVARIANT
**Description**: What this property guarantees
**Observable As**: How to measure (e.g., "error rate < 0.1%")
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| TASKS.md missing | STOP, suggest wfc-plan |
| < 2 tasks | STOP, error message |
| Cyclic dependencies | STOP, list cycle |
| Dirty working directory | STOP, suggest commit/stash |
| Agent timeout | Mark task failed, continue others |
| Test failure | Mark task failed, do not create PR |
| Push failure | Log error, continue others |
| PR creation failure | Log error, provide manual commands |

**Failed tasks**: Reported in final summary. No automatic retry. User must address and re-run.

---

## Final Output

After all phases complete, output:

```markdown
## wfc-implement Complete

**Tasks processed**: X
**Successful**: Y
**Failed**: Z

| Task | Status | PR |
|------|--------|-----|
| TASK-001 | ✅ Success | #123 |
| TASK-002 | ❌ Failed | - |

### Failed Tasks
- TASK-002: [error reason]

### Next Steps
1. Review created PRs
2. Address failed tasks manually or re-plan
3. Merge PRs after CI passes

### Cleanup
Run `/wfc-implement --cleanup` to remove worktrees
```

---

## Limitations

1. **TDD not enforced**: Cannot verify test-first ordering, only test existence and passage
2. **Review is mocked**: No actual code review occurs
3. **No auto-merge**: WFC creates PRs only; merging is external
4. **No parallel merge**: PRs created sequentially after all agents complete
5. **Single repo only**: Cannot span multiple repositories
6. **No resume**: Interrupted runs must be cleaned up and restarted

---

## Git Safety Policy

**WFC NEVER:**

- Pushes to main/master
- Force pushes
- Auto-merges PRs
- Modifies protected branches

**WFC ONLY:**

- Creates feature branches from develop
- Pushes to origin
- Creates draft PRs
