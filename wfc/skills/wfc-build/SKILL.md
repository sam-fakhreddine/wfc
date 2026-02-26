---
name: wfc-build
description: Intentional Vibe coding - quick adaptive interview, then delegate to subagent(s) for TDD implementation with quality checks and consensus review. Orchestrator asks clarifying questions, assesses complexity (1 agent vs multi-agent), spawns subagents via Task tool, and coordinates review/merge. Perfect for "just build this" requests without heavy upfront planning. Still uses git worktrees, quality gates, and consensus review. Not for large multi-component features (use /wfc-plan + /wfc-implement).
license: MIT
---

# WFC:BUILD - Intentional Vibe Coding

⚠️ **EXECUTION CONTEXT: ORCHESTRATION MODE**

You are running in **orchestration mode** with restricted tool access.

**Available tools:**

- ✅ Read, Grep, Glob (file inspection only)
- ✅ Task (REQUIRED for all implementation work)
- ✅ AskUserQuestion (clarification)
- ✅ Bash (coordination only: git status, worktree list)

**NOT available in this context:**

- ❌ Write (use Task → spawn implementation subagent)
- ❌ Edit (use Task → spawn implementation subagent)
- ❌ NotebookEdit (use Task → spawn implementation subagent)

**Critical constraint:** Every line of code written MUST be written by a subagent spawned via Task tool. No exceptions.

---

## Quick Start: Spawn Implementation Subagent

Use this template:

```xml
<Task
  subagent_type="general-purpose"
  description="Implement [feature name]"
  prompt="
You are implementing: [detailed feature description]

Files to create/modify:
- [list specific files]

Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Follow TDD workflow:
1. Write tests FIRST (RED phase)
2. Implement minimum code to pass tests (GREEN phase)
3. Refactor while keeping tests passing (REFACTOR phase)
4. Run quality checks (formatters, linters, tests)

Deliverables:
- Working implementation
- Passing tests
- Quality checks passing
"
/>
```

---

**"Vibe coding with guardrails"** - Quick iteration with WFC quality standards.

## What It Does

Simplified workflow that skips formal planning but maintains all WFC quality infrastructure:

1. **Adaptive Interview** - Quick clarifying questions (not full wfc-plan)
2. **Complexity Assessment** - Orchestrator decides: 1 agent or multi-agent?
3. **Subagent Delegation** - Spawn subagent(s) via Task tool (orchestrator NEVER implements)
4. **TDD Workflow** - Each subagent follows TEST → IMPLEMENT → REFACTOR
5. **Quality Gates** - Formatters, linters, tests (pre-review)
6. **Consensus Review** - Route through wfc-review
7. **Auto-Merge** - Merge to develop via PR (or rollback on failure)

## Usage

```bash
# Default: orchestrator asks clarifying questions
/wfc-build

# With description
/wfc-build "add progressive doc loader"

# With context
/wfc-build "add OAuth2 authentication to FastAPI backend"
```

## "Intentional Vibe" Philosophy

**Vibe Coding:**

- Fast iteration
- Minimal planning
- Just ship it

**+ WFC Guardrails:**

- Git worktrees (isolation)
- TDD workflow (tests first)
- Quality checks (formatters, linters)
- Consensus review (multi-agent)
- Auto-rollback (safety)

**= Intentional Vibe:**

- Quick enough to flow
- Structured enough to be safe
- Professional enough to ship

## Adaptive Interview

Orchestrator asks 3-5 quick questions:

```
Q1: What are you building?
A: Progressive documentation loader

Q2: Which files should this touch?
A: New files in wfc/shared/ and scripts/docs/

Q3: Expected behavior?
A: Load doc summaries, fetch full content on-demand

Q4: Tech stack?
A: Python, similar to persona_loader.py pattern
```

Then orchestrator assesses complexity and spawns subagent(s).

## Complexity Assessment

Orchestrator decides based on scope:

### Simple Task → 1 Subagent

**Examples:**

- "add a utility function"
- "create a doc loader"
- "fix a bug"
- "add a new endpoint"

**Flow:**

```
Spawn 1 subagent via Task tool
    ↓
Subagent implements in worktree (TDD)
    ↓
Quality check → Review → Merge
```

### Complex Task → N Subagents

**Examples:**

- "add OAuth2 authentication" (backend + frontend + security)
- "build a dashboard" (API + UI + charts)
- "refactor auth system" (multiple components)

**Flow:**

```
Spawn N subagents via Task tool (parallel)
    ↓
Subagent 1: Backend API (worktree-1)
Subagent 2: Frontend UI (worktree-2)
Subagent 3: Security validation (worktree-3)
    ↓
Each: TDD → Quality → Review
    ↓
Merge sequentially
```

## Orchestrator Responsibilities

**What orchestrator DOES:**

- ✅ Ask clarifying questions
- ✅ Assess task complexity
- ✅ Decide: 1 agent or N agents?
- ✅ Spawn subagent(s) via Task tool
- ✅ Wait for subagent completion
- ✅ Route through quality + review
- ✅ Coordinate merge/rollback

**What orchestrator NEVER DOES:**

- ❌ Write code
- ❌ Write tests
- ❌ Run formatters/linters
- ❌ Implement anything

**Critical Principle:** Orchestrator coordinates, NEVER implements.

## Subagent Workflow (Per Agent)

Each subagent follows TDD in isolated worktree:

```
1. UNDERSTAND
   - Read orchestrator's task spec
   - Review related files
   - Understand context

2. TEST_FIRST (RED)
   - Write tests BEFORE code
   - Run tests → FAIL

3. IMPLEMENT (GREEN)
   - Write minimum code to pass
   - Run tests → PASS

4. REFACTOR
   - Clean up code
   - Run tests → still PASS

5. QUALITY_CHECK
   - Run formatters (black, prettier, etc.)
   - Run linters (ruff, eslint, etc.)
   - Run tests
   - Blocks if checks fail

6. SUBMIT
   - Produce agent report
   - Return to orchestrator
```

## Architecture

```
User: /wfc-build "add doc loader"
    ↓
┌─────────────────────────────────────┐
│  ORCHESTRATOR (coordinates only)    │
│  - Ask clarifying questions         │
│  - Assess complexity                │
│  - Decide: 1 or N agents?           │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │  Simple  │ Complex │
    ↓          ↓
┌───────┐  ┌──────────────────────┐
│ 1 Sub │  │ N Subagents (parallel)│
│ agent │  │ - Agent 1 (backend)  │
│       │  │ - Agent 2 (frontend) │
│       │  │ - Agent 3 (security) │
└───┬───┘  └──────────┬───────────┘
    │                 │
    └────────┬────────┘
             ↓
    Each agent (isolated):
    - Git worktree
    - TDD workflow
    - Quality check
    - Submit report
             ↓
┌────────────────────────────────┐
│  ORCHESTRATOR (coordinates)    │
│  - Wait for completion         │
│  - Route through wfc-review    │
│  - Merge (or rollback)         │
└────────────────────────────────┘
```

## Integration with WFC

### Uses (delegates to)

- **Git worktrees** - Isolated implementation environments
- **Quality checker** - Pre-review gates (formatters, linters, tests)
- **wfc-review** - Consensus review with expert personas
- **Merge engine** - Auto-merge with rollback capability

### Produces

- PR targeting develop branch (auto-merge for agent branches)
- Agent reports (telemetry)
- Review reports

### Skips

- Formal TASKS.md generation
- Multi-tier planning
- Property formalization (uses lightweight acceptance criteria instead)

## When to Use

### Use wfc-build when

- ✅ Single feature or small addition
- ✅ Want to iterate quickly
- ✅ Scope is clear from description
- ✅ "Just build this and ship it"

### Use wfc-plan + wfc-implement when

- ✅ Large feature with multiple tasks
- ✅ Complex dependencies
- ✅ Need formal properties (SAFETY, LIVENESS, etc.)
- ✅ Multi-week effort

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

## Example Session

```
User: /wfc-build "add rate limiting to API"

Orchestrator:
  Q: What's the main goal?
  A: Prevent API abuse, 100 requests/minute per user

  Q: Which endpoints?
  A: All /api/* endpoints

  Q: Tech stack?
  A: FastAPI, Redis for rate limit storage

  Q: Expected behavior on limit exceeded?
  A: Return 429 Too Many Requests

Orchestrator: Assessing complexity...
  → SIMPLE task (single component)
  → Spawning 1 subagent

Subagent-1 (worktree-1):
  ✅ TEST_FIRST: Write rate limit tests
  ✅ IMPLEMENT: Add FastAPI middleware + Redis client
  ✅ REFACTOR: Extract config, clean up
  ✅ QUALITY_CHECK: black, ruff, pytest → PASS
  ✅ SUBMIT: Agent report ready

Orchestrator:
  ✅ Route to wfc-review (5 personas)
  ✅ Consensus: APPROVED (8.5/10)
  ✅ Merge to main
  ✅ Integration tests: PASS

Done! ✅ Rate limiting added to API
```

## Post-Deploy Validation Plan

**REQUIRED** in every PR created by wfc-build. The orchestrator must generate a `## Post-Deploy Monitoring & Validation` section in the PR body.

### What Gets Generated

```markdown
## Post-Deploy Monitoring & Validation

### Metrics to Watch
- [specific metrics relevant to the change]

### Healthy Signals
- [what "working correctly" looks like]

### Failure Triggers
- [what indicates a problem]

### Log Queries
- [specific log searches to run]

### Validation Window
- Duration: [24h for standard, 72h for data/auth changes]
- Escalation: [who to contact if metrics degrade]

### Rollback Criteria
- [specific conditions that warrant rollback]
```

### How It Works

1. Orchestrator analyzes the implemented changes (files modified, endpoints added, etc.)
2. Maps changes to observable metrics (response times, error rates, throughput)
3. Generates monitoring plan based on change type:
   - **API changes**: Response time P95/P99, error rate, throughput
   - **Database changes**: Query latency, connection pool usage, migration status
   - **Auth changes**: Login success rate, token validation failures, session count
   - **UI changes**: Core Web Vitals, JS error rate, render time
4. Includes plan in PR body alongside review summary

### Integration with wfc-observe

If PROPERTIES.md exists, the validation plan also maps formal properties to runtime observables using wfc-observe patterns.

## Philosophy

**ELEGANT:** Simple orchestration, clear delegation, no over-engineering
**INTENTIONAL:** Vibe coding + WFC guardrails = professional quality
**DELEGATED:** Orchestrator NEVER implements, ALWAYS delegates

## Git Workflow Policy (PR-First)

WFC creates feature branches, pushes them, and opens GitHub PRs for team review.

```
WFC workflow:
  Build -> Quality -> Review -> Push Branch -> Create GitHub PR to develop
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

---

**This is Intentional Vibe.** 🎯

Fast enough to flow. Structured enough to ship. Safe enough to trust.
