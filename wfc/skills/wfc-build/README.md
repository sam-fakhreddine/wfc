# WFC:BUILD - Intentional Vibe Coding

**"Vibe coding with guardrails"** - Fast iteration with WFC quality standards.

## Philosophy

### Vibe Coding

- ❌ Heavy upfront planning
- ❌ Formal documentation
- ❌ Slow iteration
- ✅ Just build and ship

### + WFC Guardrails

- ✅ Git worktrees (isolation)
- ✅ TDD workflow (tests first)
- ✅ Quality checks (formatters, linters)
- ✅ Consensus review (multi-agent)
- ✅ Auto-rollback (safety)

### = Intentional Vibe

**Fast enough to flow. Structured enough to ship.**

## Usage

```bash
# Interactive mode
/wfc-build

# With description
/wfc-build "add progressive doc loader"

# With context
/wfc-build "add OAuth2 authentication to FastAPI backend"
```

## Workflow

```
User: /wfc-build "add rate limiting"
    ↓
┌──────────────────────────────────────┐
│ ORCHESTRATOR (coordinates only)      │
│ - Quick adaptive interview (3-5 Q's) │
│ - Assess complexity                  │
│ - Decide: 1 agent or N agents?       │
└────────────┬─────────────────────────┘
             │
    ┌────────┴─────────┐
    │ Simple │ Complex │
    ↓        ↓
┌────────┐ ┌────────────────────┐
│1 Agent │ │N Agents (parallel) │
└───┬────┘ └─────┬──────────────┘
    │            │
    └─────┬──────┘
          ↓
    Each agent (isolated worktree):
    - TEST_FIRST → IMPLEMENT → REFACTOR
    - Quality check
    - Submit report
          ↓
┌─────────────────────────────────┐
│ ORCHESTRATOR (coordinates)      │
│ - Route through wfc-review      │
│ - Merge (or rollback)           │
└─────────────────────────────────┘
```

## Adaptive Interview

Unlike `wfc-plan`'s comprehensive interview, this is **3-5 questions max**:

1. **What are you building?**
   - Goal/feature description

2. **Which files should this touch?**
   - New files, modified files, directories

3. **Expected behavior?**
   - What should happen when complete?

4. **Tech stack/patterns?**
   - Languages, frameworks, patterns to follow

5. **Acceptance criteria?** (optional)
   - Auto-generated if not provided

## Complexity Assessment

Orchestrator decides: simple (1 agent) or complex (N agents)?

### Simple → 1 Subagent

**Indicators:**

- 1-2 files affected
- Single component
- Clear scope
- No complex keywords

**Examples:**

- "add a utility function"
- "create a doc loader"
- "fix a bug in auth.py"

**Flow:**

```
Spawn 1 subagent
    ↓
TDD workflow in worktree
    ↓
Quality + Review
    ↓
Merge
```

### Complex → N Subagents

**Indicators:**

- 3+ files affected
- Multiple components
- Keywords: "system", "refactor", "architecture"
- Multiple tech stacks

**Examples:**

- "add OAuth2 authentication" (backend + frontend + security)
- "refactor auth system" (multiple components)
- "build dashboard" (API + UI + charts)

**Flow:**

```
Decompose into subtasks
    ↓
Spawn N subagents (parallel)
    ↓
Each: TDD + Quality + Review
    ↓
Merge sequentially
```

## Orchestrator Delegation

**CRITICAL PRINCIPLE:** Orchestrator NEVER implements, ALWAYS delegates.

### Orchestrator Responsibilities

**DOES:**

- ✅ Ask clarifying questions
- ✅ Assess task complexity
- ✅ Decide: 1 or N agents?
- ✅ Spawn subagent(s) via Task tool
- ✅ Wait for completion
- ✅ Route through quality + review
- ✅ Coordinate merge/rollback

**NEVER DOES:**

- ❌ Write code
- ❌ Write tests
- ❌ Run formatters/linters
- ❌ Implement anything

### Subagent Responsibilities

**DOES:**

- ✅ TDD workflow (TEST → IMPLEMENT → REFACTOR)
- ✅ Run quality checks
- ✅ Submit report

**NEVER DOES:**

- ❌ Coordinate other agents
- ❌ Merge to main
- ❌ Run review

## TDD Workflow (Per Subagent)

Each subagent follows strict TDD in isolated worktree:

### 1. UNDERSTAND

- Read task spec from orchestrator
- Review existing files (if any)
- Understand expected behavior

### 2. TEST_FIRST (RED)

- Write tests BEFORE implementation
- Tests must cover acceptance criteria
- Run tests → they MUST FAIL

### 3. IMPLEMENT (GREEN)

- Write minimum code to pass tests
- Follow tech stack patterns
- Run tests → they MUST PASS

### 4. REFACTOR

- Clean up without changing behavior
- Maintain SOLID & DRY
- Run tests → still PASS

### 5. QUALITY_CHECK

- Run formatters (black, prettier, etc.)
- Run linters (ruff, eslint, etc.)
- Run all tests
- **BLOCKS if any check fails**

### 6. SUBMIT

- Verify all acceptance criteria met
- Produce agent report
- Return to orchestrator

## Integration with WFC

### Uses (Delegates To)

- **Git Worktrees** - Isolated environments per agent
- **Quality Checker** - Pre-review gates (wfc/skills/implement/quality_checker.py)
- **wfc-review** - Consensus review with expert personas
- **Merge Engine** - Auto-merge with rollback (wfc/skills/implement/merge_engine.py)

### Produces

- Merged code on main branch
- Agent reports (telemetry)
- Review reports

### Skips

- Formal TASKS.md generation
- Full PROPERTIES.md (uses lightweight criteria instead)
- Multi-tier planning process

## When to Use

| Scenario | Use This |
|----------|----------|
| Small feature, clear scope | ✅ wfc-build |
| Single component | ✅ wfc-build |
| "Just build this and ship" | ✅ wfc-build |
| Large feature, many tasks | ❌ wfc-plan + wfc-implement |
| Complex dependencies | ❌ wfc-plan + wfc-implement |
| Formal properties needed | ❌ wfc-plan + wfc-implement |

## Example Session

```
$ /wfc-build "add rate limiting to API"

🎯 WFC:BUILD - Intentional Vibe Interview

Goal: add rate limiting to API

Q2: Which files/directories should this affect?
→ backend/middleware/rate_limiter.py, backend/config.py

Q3: What's the expected behavior?
→ Limit to 100 requests/minute per user, return 429 on exceeded

Q4: Tech stack/patterns to follow?
→ FastAPI middleware, Redis for storage

Q5: Acceptance criteria (optional, press Enter to auto-generate)
→ [Enter]

🔍 Assessing complexity...
   Complexity: SIMPLE
   Estimated agents: 1

🚀 Spawning 1 subagent...

📋 Task breakdown:
   Single agent will:
   - Implement: add rate limiting to API
   - Affect: backend/middleware/rate_limiter.py, backend/config.py
   - Follow: FastAPI middleware, Redis for storage

🤖 Subagent instructions prepared
   → Follow TDD workflow (TEST → IMPLEMENT → REFACTOR)
   → Run quality checks (formatters, linters, tests)
   → Submit report when complete

⏳ Waiting for subagent to complete...

[Subagent works in worktree-1]
   ✅ TEST_FIRST: tests/test_rate_limiter.py
   ✅ IMPLEMENT: RateLimiterMiddleware + Redis client
   ✅ REFACTOR: Extract config, clean imports
   ✅ QUALITY_CHECK: black, ruff, pytest → PASS
   ✅ SUBMIT: Report ready

[Orchestrator routes to wfc-review]
   ✅ 5 personas: BACKEND_PYTHON, APPSEC, PERF, CODE_REVIEWER, REDIS_SPECIALIST
   ✅ Consensus: APPROVED (8.7/10)

[Orchestrator merges]
   ✅ Rebase onto main
   ✅ Integration tests: PASS
   ✅ Merge complete

============================================================
✅ BUILD COMPLETE
============================================================
Rate limiting added to API
Review: 8.7/10 (APPROVED)
Files: 2 created/modified
Tests: 5 added (all passing)
```

## Configuration

```json
{
  "build": {
    "interview_questions": 5,
    "complexity_threshold": "auto",
    "max_agents": 3,
    "enforce_tdd": true,
    "require_quality_check": true,
    "require_review": true
  }
}
```

## Architecture

### File Structure

```
wfc/skills/build/
├── SKILL.md            # Skill definition
├── README.md           # This file
├── __init__.py         # Package init
├── cli.py              # CLI entry point
└── orchestrator.py     # Orchestrator + interview + assessment
```

### Key Classes

- **`BuildOrchestrator`** - Main coordinator (NEVER implements)
- **`AdaptiveInterviewer`** - Quick 3-5 question interview
- **`ComplexityAssessor`** - Decide 1 agent vs N agents
- **`BuildSpec`** - Task specification from interview

## Comparison: wfc-build vs wfc-plan

| Feature | wfc-build | wfc-plan + wfc-implement |
|---------|-----------|--------------------------|
| **Interview** | 3-5 questions | Comprehensive |
| **Planning** | Lightweight | Formal TASKS.md |
| **Properties** | Acceptance criteria | SAFETY, LIVENESS, etc. |
| **Agents** | 1 or auto-N | Planned N with DAG |
| **Speed** | Fast (Intentional Vibe) | Thorough |
| **Use Case** | Single feature | Large multi-task effort |

## Benefits

### ✅ Fast Iteration

Skip heavy planning, start building quickly.

### ✅ Still Safe

TDD + quality checks + consensus review = production-ready.

### ✅ Intelligent Delegation

Orchestrator assesses complexity, spawns right number of agents.

### ✅ Isolation

Each agent works in isolated worktree, no conflicts.

### ✅ Auto-Quality

Formatters, linters, tests enforced before review.

### ✅ Consensus Review

Multi-agent review ensures quality from multiple perspectives.

### ✅ Auto-Rollback

Integration test failures trigger automatic rollback.

## Philosophy Summary

**Intentional Vibe** = The sweet spot between:

| Too Loose | Intentional Vibe | Too Formal |
|-----------|------------------|------------|
| No tests | ✅ TDD workflow | Test plans |
| No review | ✅ Consensus review | Design docs |
| Cowboy coding | ✅ Quality checks | RFCs |
| No isolation | ✅ Git worktrees | Staging envs |
| YOLO | ✅ Auto-rollback | Manual gates |

**Fast enough to flow. Structured enough to ship.**

---

**This is Intentional Vibe.** 🎯

Vibe coding + WFC guardrails = Professional quality.
