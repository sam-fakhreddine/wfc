# WFC:IMPLEMENT - Multi-Agent Parallel Implementation Engine

**Complete Guide**

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Workflow](#workflow)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

**wfc-implement** is a multi-agent parallel implementation engine that orchestrates N agents in isolated git worktrees, enforces TDD workflow, integrates quality gates and consensus review, and auto-merges with rollback capability.

### Key Capabilities

- **Multi-Agent Orchestration**: Run up to 5 agents in parallel (configurable)
- **TDD Enforcement**: RED-GREEN-REFACTOR cycle (UNDERSTAND → TEST_FIRST → IMPLEMENT → REFACTOR → QUALITY_CHECK → SUBMIT)
- **Universal Quality Gate**: Trunk.io integration (100+ tools for all languages)
- **Intelligent Confidence Checking**: Assess confidence before implementation (SuperClaude pattern)
- **Cross-Session Learning**: ReflexionMemory pattern (learn from past mistakes)
- **Token Budget Optimization**: Historical learning, complexity-based budgets
- **Automatic Rollback**: Main branch always passing, worktrees preserved on failure
- **Failure Severity Classification**: WARNING (don't block), ERROR (block but retryable), CRITICAL (immediate failure)

### Status

✅ **PHASE 1 COMPLETE** - Core Functionality (100%)
✅ **PHASE 2 COMPLETE** - Intelligence (100%)
✅ **PHASE 3 COMPLETE** - Polish (100%)

**Ready for production use** with Phase 4 (Dashboard) as optional enhancement.

---

## Architecture

### Multi-Tier Design

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
│  - quality_checker.py       │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  DATA TIER                  │  Uses shared infrastructure
│  - WFCTelemetry             │  (Swappable storage)
│  - Git (worktrees)          │
│  - Memory (reflexion.jsonl) │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│  CONFIG TIER                │  WFCConfig
│  - wfc.config.json          │  (Global/project)
└─────────────────────────────┘
```

### Parallel Execution Flow

```
Orchestrator
    ├── Agent 1 (worktree-1, TASK-001, sonnet)
    ├── Agent 2 (worktree-2, TASK-002, opus)
    ├── Agent 3 (worktree-3, TASK-005, sonnet)
    └── Agent N (worktree-N, TASK-XXX, haiku)
         ↓ (all work concurrently)
    Confidence Check (BEFORE starting work)
         ├── ≥90%: Proceed
         ├── 70-89%: Ask questions
         └── <70%: STOP
         ↓
    Memory Search (learn from past mistakes)
         ↓
    TDD Workflow (6 phases)
         ├── UNDERSTAND
         ├── TEST_FIRST (RED)
         ├── IMPLEMENT (GREEN)
         ├── REFACTOR
         ├── QUALITY_CHECK
         └── SUBMIT
         ↓
    Quality Gate (Trunk.io or language-specific)
         ├── Formatting (black, prettier)
         ├── Linting (ruff, eslint)
         ├── Tests (pytest, jest)
         └── Type checking (mypy, optional)
         ↓ (only if all pass)
    Review (sequential per agent)
         ↓
    Merge (sequential, one at a time)
         ├── Rebase on main
         ├── Re-run tests
         ├── Merge to main
         └── Integration tests
         ↓ (pass/fail)
    Main Branch (or Rollback)
```

---

## Features

### 1. TDD Workflow (TASK-002)

Complete RED-GREEN-REFACTOR cycle with 6 phases:

**UNDERSTAND**

- Read task definition from TASKS.md
- Read properties from PROPERTIES.md
- Assess confidence (≥90% to proceed)
- Search for similar past errors
- Read existing code

**TEST_FIRST (RED)**

- Write tests BEFORE implementation
- Tests cover acceptance criteria
- Tests cover formal properties
- Run tests → they FAIL (RED phase)

**IMPLEMENT (GREEN)**

- Write minimum code to pass tests
- Follow ELEGANT principles
- Run tests → they PASS (GREEN phase)

**REFACTOR**

- Clean up without changing behavior
- Maintain SOLID & DRY principles
- Run tests → still PASS

**QUALITY_CHECK**

- Run Trunk.io universal checker (all languages)
- Falls back to language-specific tools if Trunk unavailable
- Blocks submission if checks fail
- Reports fixable issues with commands

**SUBMIT**

- Verify quality check passed (BLOCKS if failed)
- Final verification of acceptance criteria
- Produce agent report
- Route to wfc-consensus-review

### 2. Universal Quality Gate (TASK-001)

**Philosophy**: Don't waste multi-agent review on formatting

- **Trunk.io Integration**: 100+ tools for all languages
- **Automatic Fallback**: Python-specific tools if Trunk unavailable
- **Severity Classification**: WARNING (don't block), ERROR (block), CRITICAL (fail)
- **Token Savings**: 50%+ reduction (fix locally, not in review)

**Checks**:

1. Formatting (black, prettier, etc.)
2. Linting (ruff, eslint, etc.)
3. Tests (pytest, jest, etc.)
4. Type checking (mypy, optional)

### 3. Confidence Checking (TASK-003)

**SuperClaude Pattern**: Assess confidence BEFORE implementation

**Scoring** (0-100):

- Clear requirements: 30 points
- Has examples: 20 points
- Understands architecture: 20 points
- Knows dependencies: 15 points
- Can verify success: 15 points

**Decision**:

- **≥90%**: Proceed with implementation
- **70-89%**: Present alternatives, ask clarifying questions
- **<70%**: STOP - Investigate more, ask user for guidance

**ROI**: Prevents 25-250x token waste from wrong-direction work

### 4. Memory System (TASK-004)

**ReflexionMemory Pattern**: Cross-session learning

**Files**:

- `wfc/memory/reflexion.jsonl` - Error learning (task, mistake, evidence, fix, rule)
- `wfc/memory/workflow_metrics.jsonl` - Performance metrics (tokens, time, success)

**Features**:

- Log errors and fixes for future reference
- Search past errors before starting work
- Suggest solutions from similar past mistakes
- Privacy-safe (no secrets logged)

### 5. Token Budget Optimization (TASK-009)

**Complexity-Based Budgets**:

- **S (Simple)**: 200 tokens (small changes, bug fixes)
- **M (Medium)**: 1,000 tokens (features, moderate complexity)
- **L (Large)**: 2,500 tokens (complex features, refactoring)
- **XL (Extra Large)**: 5,000 tokens (major features, architecture)

**Features**:

- Usage tracking and warnings (80% threshold)
- Budget exceeded alerts
- Historical optimization (20% buffer above average)
- Integrates with workflow_metrics.jsonl

### 6. Merge Engine with Rollback (TASK-005)

**Safety Guarantees**: Main branch always passing

**Workflow**:

1. Rebase agent branch on main
2. Re-run tests after rebase
3. Merge to main if tests pass
4. Run integration tests
5. Rollback if integration tests fail

**Rollback Strategy**:

- Automatic rollback on failure
- Worktree preserved for investigation
- Recovery plan generated (PLAN-{task_id}.md)
- Re-queue task (max 2 retries for ERROR severity)

**Failure Severity**:

- **WARNING**: Don't block submission (e.g., linting warnings)
- **ERROR**: Block but retryable (e.g., test failures)
- **CRITICAL**: Immediate failure (e.g., security vulnerabilities)

### 7. CLI Interface (TASK-007)

```bash
# Default: use TASKS.md in /plan
wfc implement

# Custom tasks file
wfc implement --tasks path/to/TASKS.md

# Override agent count (default: 5)
wfc implement --agents 8

# Dry run (show plan without executing)
wfc implement --dry-run

# Skip quality checks (with warning)
wfc implement --skip-quality
```

---

## Installation

### Prerequisites

- Python >=3.12
- Git
- Claude Code
- (Recommended) Trunk.io: `curl https://get.trunk.io -fsSL | bash`

### Install WFC

```bash
# Clone repository
git clone https://github.com/yourusername/wfc.git
cd wfc

# Install with all features
uv pip install -e ".[all]"

# Or install with specific features
uv pip install -e ".[tokens,dev]"
```

### Verify Installation

```bash
# Run health checks
make doctor

# Should report:
# ✅ WFC is healthy!
```

---

## Usage

### 1. Create a Plan

Use `wfc plan` to create structured TASKS.md:

```bash
wfc plan
```

This generates:

- `plan/TASKS.md` - Implementation tasks with dependencies
- `plan/PROPERTIES.md` - Formal properties (SAFETY, LIVENESS, etc.)
- `plan/TEST-PLAN.md` - Test specifications

**Architecture Design Phase**: The planner now includes an architecture designer (`wfc/skills/wfc-plan/architecture_designer.py`) that evaluates trade-offs, selects patterns, and produces architecture decision records (ADRs) before tasks are generated. This gives implementation agents clear architectural boundaries and constraints to work within.

### 2. Execute Implementation

```bash
wfc implement --tasks plan/TASKS.md
```

### 3. Monitor Progress

Watch real-time output:

```
🚀 WFC Implement - Multi-Agent Parallel Implementation
===========================================================

📋 Loaded 8 tasks from plan/TASKS.md
📊 Execution plan:
   Level 1: TASK-001, TASK-003, TASK-007 (3 tasks in parallel)
   Level 2: TASK-002, TASK-005 (2 tasks in parallel)
   Level 3: TASK-004, TASK-009 (2 tasks in parallel)
   Level 4: TASK-008 (1 task)

🔄 Starting Level 1 (3 agents)...
   ✅ TASK-001: Universal Quality Checker (45s, 2,450 tokens)
   ✅ TASK-003: Confidence Checking (38s, 2,100 tokens)
   ✅ TASK-007: CLI Interface (52s, 2,850 tokens)

🔄 Starting Level 2 (2 agents)...
   ✅ TASK-002: Agent TDD Workflow (78s, 4,200 tokens)
   ✅ TASK-005: Merge Engine with Rollback (65s, 3,900 tokens)

...

===========================================================
✅ Implementation complete!
   Completed: 8 tasks
   Failed: 0 tasks
   Duration: 5m 23s
   Total tokens: 25,450

All tasks merged to main branch successfully.
This is World Fucking Class. 🚀
```

### 4. Handle Failures

If a task fails:

```
❌ TASK-006 failed: Integration tests failed
   Severity: ERROR (retryable)
   Worktree preserved: /worktrees/wfc-TASK-006
   Recovery plan: /plan/PLAN-TASK-006.md

   Options:
   1. Investigate: cd /worktrees/wfc-TASK-006
   2. Retry: wfc implement --retry TASK-006
   3. Skip: wfc implement --skip TASK-006
```

---

## Workflow

### Agent Workflow (Per Task)

```python
class AgentPhase(Enum):
    UNDERSTAND = "understand"
    TEST_FIRST = "test_first"
    IMPLEMENT = "implement"
    REFACTOR = "refactor"
    QUALITY_CHECK = "quality_check"
    SUBMIT = "submit"
```

Each agent follows this workflow:

1. **UNDERSTAND** (30-60s)
   - Read task, properties, existing code
   - Assess confidence (must be ≥90%)
   - Search for similar past errors
   - Create understanding of problem

2. **TEST_FIRST** (20-40s)
   - Write tests covering acceptance criteria
   - Write property-based tests
   - Run tests → verify they FAIL (RED)

3. **IMPLEMENT** (40-90s)
   - Write minimum code to pass tests
   - Run tests → verify they PASS (GREEN)
   - No over-engineering

4. **REFACTOR** (20-40s)
   - Clean up code
   - Apply SOLID & DRY principles
   - Run tests → verify still PASS

5. **QUALITY_CHECK** (10-20s)
   - Run Trunk.io or fallback checks
   - Block if checks fail
   - Report fixable issues

6. **SUBMIT** (10-20s)
   - Verify quality passed
   - Verify acceptance criteria met
   - Generate agent report
   - Route to consensus review

**Total**: ~2-5 minutes per task (depending on complexity)

---

## Configuration

### Global Config (`~/.wfc/wfc.config.json`)

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
  "quality": {
    "use_trunk": true,
    "fallback_to_language_specific": true,
    "fail_on_warnings": false
  },
  "confidence": {
    "min_score_to_proceed": 90,
    "ask_questions_above": 70
  },
  "tokens": {
    "enable_budgets": true,
    "warn_at_percentage": 80,
    "use_historical_optimization": true
  }
}
```

### Project Config (`wfc.config.json`)

Override global settings per project:

```json
{
  "orchestration": {
    "max_agents": 3
  },
  "quality": {
    "use_trunk": false,
    "python_formatter": "ruff format"
  }
}
```

---

## Testing

### Run Integration Tests

```bash
# All tests
make test

# Integration tests only
pytest tests/test_implement_integration.py -v

# End-to-end tests only
pytest tests/test_implement_e2e.py -v

# With coverage
make test-coverage
```

### Test Coverage

**Current**: >80% coverage

**Areas Covered**:

- ✅ Confidence checking (3 tests)
- ✅ Memory system (5 tests)
- ✅ Token management (3 tests)
- ✅ Quality gate (4 tests)
- ✅ Rollback scenarios (3 tests)
- ✅ Parallel execution (2 tests)
- ✅ TDD workflow (1 test)

**Total**: 22 comprehensive tests

---

## Troubleshooting

### Agent Stuck in UNDERSTAND Phase

**Symptom**: Agent confidence < 70%

**Solution**:

```bash
# Check confidence assessment
cat .wfc/telemetry.jsonl | grep confidence_assessment | tail -1 | jq

# Clarify requirements in TASKS.md
# Add more acceptance criteria
# Provide examples or similar code references
```

### Quality Check Failing

**Symptom**: "Quality check failed: 5 issues found"

**Solution**:

```bash
# Run Trunk.io manually
trunk check --fix

# Or use language-specific tools
make format  # black + ruff
make lint    # ruff check
```

### Integration Tests Failing After Merge

**Symptom**: "Rolled back TASK-006: integration tests failed"

**Solution**:

```bash
# Investigate worktree
cd /worktrees/wfc-TASK-006

# Run tests manually
pytest -v

# Check rollback was clean
git log --oneline | head -5

# Review recovery plan
cat /plan/PLAN-TASK-006.md
```

### Token Budget Exceeded

**Symptom**: "⚠️ BUDGET EXCEEDED: 110% (1,100/1,000 tokens)"

**Solution**:

- Task may be more complex than classified
- Consider breaking into subtasks
- Increase budget for task complexity
- Review historical averages: `cat wfc/memory/workflow_metrics.jsonl | grep complexity`

### Worktree Conflicts

**Symptom**: "Failed to create worktree: already exists"

**Solution**:

```bash
# List worktrees
git worktree list

# Remove stale worktree
git worktree remove /worktrees/wfc-TASK-XXX

# Or prune all stale worktrees
git worktree prune
```

---

## Advanced Usage

### Retry Failed Task

```bash
wfc implement --retry TASK-006
```

### Skip Failed Task

```bash
wfc implement --skip TASK-006
```

### Override Agent Model

```bash
# Use Opus for all agents (slower, higher quality)
wfc implement --model opus

# Use Haiku for all agents (faster, lower cost)
wfc implement --model haiku
```

### Custom Integration Tests

```json
{
  "integration_tests": {
    "command": "npm run test:integration && npm run test:e2e",
    "timeout_seconds": 600
  }
}
```

---

## Philosophy

**ELEGANT**: Simple agent logic, clear orchestration, no over-engineering

**MULTI-TIER**: Presentation/Logic/Data/Config cleanly separated

**PARALLEL**: Maximum safe concurrency (agents, tasks, reviews)

**CONFIDENCE-FIRST**: Assess before acting (prevent wrong-direction work)

**CROSS-SESSION-LEARNING**: Learn from mistakes, optimize over time

**TOKEN-AWARE**: Optimize for token efficiency at every layer

**TEST-FIRST**: TDD workflow enforced (RED-GREEN-REFACTOR)

**SAFETY**: Rollback on failure, preserve evidence, main always passing

---

## Credits

Built with the SuperClaude Framework patterns:

- **ReflexionMemory**: Cross-session learning from mistakes
- **Confidence-First**: Assess before implementation
- **Token Budgets**: Historical optimization
- **PROJECT_INDEX.json**: Machine-readable structure

**This is World Fucking Class.** 🚀
