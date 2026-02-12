# WFC Orchestrator Delegation - Implementation Pattern

This document demonstrates how WFC's implementation orchestrator delegates ALL work to subagents via Claude Code's Task tool, following the critical principle: **Orchestrator coordinates, NEVER implements**.

## Architecture Overview

```
User invokes /wfc-implement
        ↓
1. Orchestrator reads TASKS.md
   ├─ Parse task dependencies
   ├─ Build execution DAG
   └─ Identify parallelizable tasks
        ↓
2. ExecutionEngine spawns subagents (via Task tool)
   ├─ Subagent #1: Implements TASK-001 (TDD workflow)
   ├─ Subagent #2: Implements TASK-002 (TDD workflow)
   ├─ Subagent #3: Implements TASK-005 (TDD workflow)
   └─ Up to max_agents subagents in parallel
        ↓
3. Each subagent follows TDD workflow
   ├─ UNDERSTAND: Read task, properties, test plan
   ├─ TEST_FIRST: Write tests BEFORE implementation
   ├─ IMPLEMENT: Write code to pass tests
   ├─ REFACTOR: Clean up while keeping tests passing
   ├─ QUALITY_CHECK: Run formatters, linters, tests
   └─ SUBMIT: Produce AgentReport
        ↓
4. ExecutionEngine collects results
   ├─ Route each report through wfc-review
   ├─ Merge approved changes
   ├─ Rollback on integration test failure
   └─ Re-queue tasks if needed
```

## Critical Principle: Delegation Pattern

### ❌ WRONG: Orchestrator Does Work

```python
class ExecutionEngine:
    def execute(self):
        for task in self.orchestrator.get_next_tasks():
            # ❌ WRONG: Orchestrator executes agent code in-process
            agent = WFCAgent(task=task)
            report = agent.implement()  # Runs in same process
            self._process_report(report)
```

**Problems:**
- No true parallelism (just threads in same process)
- Context bleeding between agents
- Orchestrator doing implementation work
- Violates separation of concerns

### ✅ CORRECT: Orchestrator Delegates

```python
class ExecutionEngine:
    def execute(self):
        while not self._is_complete():
            # Spawn subagents via Task tool
            if len(self.active_subagents) < max_agents:
                task = self.orchestrator.get_next_task()
                if task:
                    self._spawn_subagent(task)  # Delegates to subprocess

            # Poll for completion
            for task_id, agent_id in self.active_subagents.items():
                report = self._wait_for_subagent(task_id, agent_id)
                if report:
                    self._process_report(report, task)
                    del self.active_subagents[task_id]
```

**Benefits:**
- ✅ True parallelism (separate subprocesses)
- ✅ Complete isolation (no context bleeding)
- ✅ Orchestrator only coordinates (never implements)
- ✅ Follows Claude Code best practices

## Implementation Details

### Step 1: Spawn Subagent

```python
def _spawn_subagent(self, task: Task) -> None:
    """
    Spawn subagent via Task tool to execute task implementation.

    CRITICAL: This method delegates to a subagent subprocess.
    It does NOT execute agent code in-process.
    """
    self.agent_counter += 1
    agent_id = f"agent-{self.agent_counter}"

    # Build prompt for subagent
    agent_prompt = self._build_agent_prompt(task, agent_id)

    # In production: Use Task tool like this:
    # Task(
    #     subagent_type="general-purpose",
    #     prompt=agent_prompt,
    #     model="sonnet",
    #     description=f"Implement {task.id}"
    # )

    # Track active subagent
    self.active_subagents[task.id] = agent_id
    self.orchestrator.in_progress[task.id] = task
```

### Step 2: Build Agent Prompt

```python
def _build_agent_prompt(self, task: Task, agent_id: str) -> str:
    """
    Build complete prompt for subagent Task tool invocation.

    Returns a prompt that instructs the subagent to:
    1. Understand the task
    2. Follow TDD workflow (TEST_FIRST → IMPLEMENT → REFACTOR)
    3. Run quality checks
    4. Submit agent report
    """
    prompt_parts = [
        f"You are {agent_id}, a WFC implementation agent.",
        f"Task ID: {task.id}",
        f"Task Description: {task.description}",
        "",
        "Follow the TDD workflow:",
        "1. UNDERSTAND - Read task, properties, test plan, existing code",
        "2. TEST_FIRST - Write tests BEFORE implementation",
        "3. IMPLEMENT - Write minimum code to pass tests",
        "4. REFACTOR - Clean up while keeping tests passing",
        "5. QUALITY_CHECK - Run formatters, linters, tests",
        "6. SUBMIT - Produce agent report",
        "",
        f"Properties to satisfy: {', '.join(task.properties)}",
        f"Acceptance criteria: {', '.join(task.acceptance_criteria)}",
    ]

    return "\n".join(prompt_parts)
```

### Step 3: Wait for Subagent Completion

```python
def _wait_for_subagent(self, task_id: str, agent_id: str) -> AgentReport:
    """
    Wait for subagent completion and retrieve report.

    In production, this would use TaskOutput tool to poll the subagent.
    """
    # In production: Poll TaskOutput tool
    # result = TaskOutput(task_id=agent_id, block=True, timeout=3600000)
    # return parse_agent_report(result)

    # For now, return mock report
    return AgentReport(
        agent_id=agent_id,
        task_id=task_id,
        status="success",
        branch=f"wfc-task-{task_id}",
        worktree_path=f".worktrees/{task_id}",
        commits=[...],
        properties_satisfied={},
        tests_passed=True,
        test_results={}
    )
```

### Step 4: Process Report

```python
def _process_report(self, report: AgentReport, task: Task) -> None:
    """
    Process agent report.

    Orchestrator coordinates review and merge,
    but does NOT implement anything itself.
    """
    if report.status == "failed":
        self.orchestrator.mark_task_failed(task.id)
        return

    # Route through review (delegates to wfc-review)
    review_passed = self._review(report)

    if not review_passed:
        self.orchestrator.mark_task_failed(task.id)
        return

    # Merge (delegates to merge engine)
    merge_result = self.merge_engine.merge(
        task_id=task.id,
        branch=report.branch,
        worktree_path=Path(report.worktree_path)
    )

    # Track results
    if merge_result.integration_tests_passed:
        self.orchestrator.mark_task_complete(task.id, report.to_dict())
    else:
        self.orchestrator.mark_task_failed(task.id)
        self.orchestrator.rollback_count += 1
```

## Execution Flow Example

```
User: /wfc-implement

Orchestrator:
  - Read TASKS.md (5 tasks)
  - Build dependency graph
  - Max agents: 3

ExecutionEngine.execute():
  [Iteration 1]
  - TASK-001 has no dependencies → spawn subagent-1
  - TASK-002 has no dependencies → spawn subagent-2
  - TASK-003 depends on TASK-001 → wait
  - active_subagents: {TASK-001: agent-1, TASK-002: agent-2}

  [Iteration 2]
  - Wait for subagent-1 completion → got report
  - Process report-1 → review → merge → success
  - TASK-003 unblocked → spawn subagent-3
  - active_subagents: {TASK-002: agent-2, TASK-003: agent-3}

  [Iteration 3]
  - Wait for subagent-2 completion → got report
  - Process report-2 → review → merge → success
  - TASK-005 has no dependencies → spawn subagent-4
  - active_subagents: {TASK-003: agent-3, TASK-005: agent-4}

  [Iteration 4]
  - Wait for subagent-3 completion → got report
  - Process report-3 → review → merge → integration tests failed!
  - Rollback TASK-003
  - Re-queue TASK-003 for retry
  - active_subagents: {TASK-005: agent-4}

  [Iteration 5]
  - Wait for subagent-4 completion → got report
  - Process report-4 → review → merge → success
  - TASK-003 retry → spawn subagent-5
  - active_subagents: {TASK-003: agent-5}

  [Iteration 6]
  - Wait for subagent-5 completion → got report
  - Process report-5 → review → merge → success
  - active_subagents: {}
  - All tasks complete ✅
```

## Key Benefits

### ✅ True Parallelism
Multiple subagents run simultaneously in separate subprocesses, not threads.

### ✅ Complete Isolation
Each subagent has its own:
- Context window
- System prompt
- Worktree (isolated git environment)
- No visibility into other agents' work

### ✅ Orchestrator Never Implements
Orchestrator ONLY:
- Reads task definitions
- Spawns subagents
- Waits for completion
- Processes reports
- Coordinates review and merge

Orchestrator NEVER:
- Writes code
- Runs tests
- Does implementation work

### ✅ Automatic Rollback
If integration tests fail after merge, automatic rollback and re-queue.

### ✅ Dependency Management
Tasks with dependencies wait until blockers complete.

### ✅ Model Selection
Each subagent can use different model based on task complexity:
- Simple tasks → Haiku (fast, cheap)
- Complex tasks → Opus (thorough)
- Balanced → Sonnet

## Comparison: Orchestrator vs Subagent Responsibilities

| Responsibility | Orchestrator | Subagent |
|----------------|-------------|----------|
| Read TASKS.md | ✅ Yes | ❌ No |
| Parse dependencies | ✅ Yes | ❌ No |
| Spawn subagents | ✅ Yes | ❌ No |
| Write tests | ❌ No | ✅ Yes |
| Write code | ❌ No | ✅ Yes |
| Run tests | ❌ No | ✅ Yes |
| Run quality checks | ❌ No | ✅ Yes |
| Produce report | ❌ No | ✅ Yes |
| Route to review | ✅ Yes | ❌ No |
| Merge changes | ✅ Yes | ❌ No |
| Rollback on failure | ✅ Yes | ❌ No |

## Configuration

```json
{
  "orchestration": {
    "agent_strategy": "smart",
    "max_agents": 5
  },
  "worktree": {
    "directory": ".worktrees",
    "cleanup_on_success": true
  },
  "tdd": {
    "enforce_test_first": true,
    "require_all_properties_tested": true
  },
  "merge": {
    "auto_merge": true,
    "require_rebase": true
  }
}
```

## Next Steps

1. **Integration**: Wire up real Task tool calls (replace mock implementation)
2. **Testing**: Create integration tests for orchestrator delegation
3. **Documentation**: Add more examples for different task types
4. **Dashboard**: Add real-time visualization of subagent progress

---

**Architecture Status**: ✅ Correct implementation following delegation principle

**Critical Principle**: Orchestrator coordinates, NEVER implements.

Based on: https://code.claude.com/docs/en/sub-agents
