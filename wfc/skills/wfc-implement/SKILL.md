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
- **Produces**: PR to develop branch, telemetry records, agent reports

## Post-Deploy Validation Plan

After all tasks are implemented and merged, the orchestrator generates a post-deploy validation plan included in the PR body.

### Generation Process

1. Collect all PROPERTIES.md entries for implemented tasks
2. Map each property to observable metrics:
   - SAFETY properties → error rate monitors, auth failure alerts
   - PERFORMANCE properties → latency P95/P99 thresholds, throughput baselines
   - LIVENESS properties → health check endpoints, heartbeat monitors
   - INVARIANT properties → data consistency checks, constraint validations
3. Generate validation plan section for PR body

### Validation Plan Format

```markdown
## Post-Deploy Monitoring & Validation

### Properties Validated
| Property | Type | Observable | Threshold |
|----------|------|-----------|-----------|
| PROP-001 | SAFETY | auth_failure_rate | < 0.1% |
| PROP-002 | PERFORMANCE | api_latency_p99 | < 200ms |

### Monitoring Queries
- `auth_failures{service="api"} / auth_total > 0.001`
- `histogram_quantile(0.99, api_latency) > 0.2`

### Validation Window
- Standard changes: 24 hours
- Data/auth changes: 72 hours
- Infrastructure changes: 1 week

### Rollback Criteria
- Any SAFETY property violation triggers immediate rollback
- PERFORMANCE degradation >20% from baseline triggers investigation
```

## Philosophy

**ELEGANT**: Simple agent logic, clear orchestration, no over-engineering
**MULTI-TIER**: Presentation/Logic/Data/Config cleanly separated
**PARALLEL**: Maximum concurrency where safe (agents, tasks, reviews)

## Git Workflow Policy (PR-First)

WFC creates feature branches, pushes them, and opens GitHub PRs for team review.

```
WFC workflow:
  Implement -> Quality -> Review -> Push Branch -> Create GitHub PR to develop
                                                        |
                                                  [WFC STOPS HERE]
                                                        |
                                      Auto-merge for claude/* branches
                                      Manual review for feat/* branches
```

Agent branches (claude/*) auto-merge to develop when CI passes. Human branches require manual review. Release candidates are cut from develop to main on a schedule.

**What WFC does:**
- Creates feature branches
- Pushes branches to remote
- Creates GitHub PRs targeting develop (draft by default)

**What WFC never does:**
- Push directly to main/master
- Force push
- Merge PRs to main (you decide when to cut releases)

**Legacy mode:** Set `"merge.strategy": "direct"` in wfc.config.json for local-only merge.

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
