---
name: wfc-implement
description: Multi-agent parallel implementation engine that orchestrates multiple TDD-style agents in isolated git worktrees. Reads structured TASKS.md, assigns tasks to parallel agents, enforces test-first development, integrates consensus review, and auto-merges with rollback capability. Use when you have a structured plan (TASKS.md) ready to execute, or when implementing multiple related tasks in parallel. Triggers on "implement this plan", "execute these tasks", "start implementation", or explicit /wfc-implement. Ideal for executing wfc-plan outputs or any structured task list. Not for ad-hoc single features without planning.
license: MIT
---

# wfc-implement - Multi-Agent Parallel Implementation Engine

**Core skill #3** - Reads TASKS.md, orchestrates N agents in isolated worktrees, enforces TDD, routes through review, auto-merges, handles rollbacks.

## Status

🚧 **IN DEVELOPMENT**

- ✅ Shared infrastructure (config, telemetry, schemas, utils)
- ✅ Mock dependencies (wfc-plan, wfc-consensus-review)
- ✅ Orchestrator logic (task queue, dependency management)
- 🚧 Agent implementation (TDD workflow)
- 🚧 Merge engine (rebase, integration tests, rollback)
- 🚧 Dashboard (WebSocket, Mermaid visualization)
- 📋 CLI interface
- 📋 Full integration testing

## Architecture

### MULTI-TIER Design

```
┌─────────────────────────────┐
│  PRESENTATION TIER          │  CLI, Dashboard (future: Web UI, API)
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  LOGIC TIER                 │  Orchestrator, Agents, Merge Engine
│  - orchestrator.py          │  (Pure logic, no UI)
│  - agent.py                 │
│  - merge_engine.py          │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  DATA TIER                  │  Uses shared infrastructure
│  - WFCTelemetry             │  (Swappable storage)
│  - Git (worktrees)          │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  CONFIG TIER                │  WFCConfig
│  - wfc.config.json          │  (Global/project)
└─────────────────────────────┘
```

### PARALLEL Execution

```
Orchestrator
    ├── Agent 1 (worktree-1, TASK-001, sonnet)
    ├── Agent 2 (worktree-2, TASK-002, opus)
    ├── Agent 3 (worktree-3, TASK-005, sonnet)
    └── Agent N (worktree-N, TASK-XXX, haiku)
         ↓ (all work concurrently)
    Review (sequential per agent)
         ↓
    Merge (sequential, one at a time)
         ↓
    Integration Tests
         ↓ (pass/fail)
    Main Branch (or Rollback)
```

## Triggers

```bash
# Default: use TASKS.md in /plan
/wfc-implement

# Custom tasks file
/wfc-implement --tasks path/to/TASKS.md

# Override agent count
/wfc-implement --agents 5

# Override strategy
/wfc-implement --strategy smart

# Dry run (show plan, don't execute)
/wfc-implement --dry-run
```

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
  },
  "integration_tests": {
    "command": "pytest",
    "timeout_seconds": 300,
    "run_after_every_merge": true
  },
  "rollback": {
    "strategy": "re_queue",
    "max_rollback_retries": 2
  },
  "dashboard": {
    "enabled": true,
    "websocket_port": 9876
  }
}
```

## TDD Workflow (Per Agent)

```
1. UNDERSTAND
   - Read task definition
   - Read properties
   - Read test plan
   - Read existing code

2. TEST FIRST (RED)
   - Write tests BEFORE implementation
   - Tests cover acceptance criteria
   - Tests cover properties
   - Run tests → they FAIL

3. IMPLEMENT (GREEN)
   - Write minimum code to pass tests
   - Follow ELEGANT principles
   - Run tests → they PASS

4. REFACTOR
   - Clean up without changing behavior
   - Maintain SOLID & DRY
   - Run tests → still PASS

5. SUBMIT
   - Commit to worktree branch
   - Produce agent report
   - Route to wfc-consensus-review
```

## Dependencies

- **Consumes**: TASKS.md, PROPERTIES.md, TEST-PLAN.md (from wfc-plan)
- **Integrates**: wfc-consensus-review (for code review)
- **Produces**: Merged code on main, telemetry records, agent reports

## Philosophy

**ELEGANT**: Simple agent logic, clear orchestration, no over-engineering
**MULTI-TIER**: Presentation/Logic/Data/Config cleanly separated
**PARALLEL**: Maximum concurrency where safe (agents, tasks, reviews)

## Git Safety Policy

**CRITICAL:** WFC NEVER pushes to remote. User must push manually.

```
WFC workflow:
  Implement → Quality → Review → Merge to LOCAL main → Integration tests
                                        ↓
                                [WFC STOPS HERE]
                                        ↓
                             User reviews and pushes:
                                git push origin main
```

**Why:**
- ✅ User control before remote changes
- ✅ Review merged result before push
- ✅ Respects branch protection rules
- ✅ Easy to revert before push
- ✅ User decides: push, PR, or revert

See [GIT_SAFETY_POLICY.md](../../../docs/security/GIT_SAFETY_POLICY.md) for complete policy.

## Current Implementation Status

### ✅ Done
- Orchestrator (task queue, dependency management)
- Shared infrastructure (config, telemetry, schemas, utils)
- Mock dependencies (wfc-plan, wfc-consensus-review)

### 🚧 In Progress
- Agent TDD workflow
- Merge engine with rollback
- Dashboard

### 📋 TODO
- CLI interface
- Full integration tests
- Performance optimization
- Real wfc-plan and wfc-consensus-review integration
