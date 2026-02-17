# Loki Mode Analysis: What WFC Should Adopt

**Date:** 2026-02-17
**Source:** [github.com/sam-fakhreddine/loki-mode](https://github.com/sam-fakhreddine/loki-mode) (v5.48.1)
**Purpose:** Identify concrete ideas from Loki Mode that would improve WFC's quality, intelligence, and developer experience.

---

## Executive Summary

Loki Mode is a multi-agent autonomous system that takes a PRD to a deployed product. It shares DNA with WFC (progressive disclosure, persona-based review, token awareness, parallel agents) but diverges in philosophy: Loki optimizes for zero-human-intervention autonomy, WFC optimizes for human-in-the-loop quality.

After reviewing the full codebase -- SKILL.md, memory engine, event bus, quality gates, compound learning, agent dispatch, context tracker, and skill modules -- eight ideas are worth integrating into WFC. Five ideas should be explicitly rejected.

---

## Ideas to Adopt

### 1. Anti-Sycophancy Devil's Advocate on Unanimous Approval

**Source:** `skills/quality-gates.md` lines 3-4, inspired by CONSENSAGENT (ACL 2025)

**What Loki does:** When all 3 blind reviewers unanimously approve code, Loki spawns an additional "Devil's Advocate" reviewer whose explicit job is to find problems. This addresses the well-documented sycophancy bias where LLMs tend to agree with each other.

**Why WFC needs this:** WFC's `WeightedConsensus` in `wfc/scripts/skills/review/consensus.py` requires all agents to score >= 7/10 and an overall weighted average >= 7.0. But if all 5 personas independently rate code 8+, it sails through. The unanimous agreement itself should be a signal -- real code almost always has something worth questioning.

**Integration point:** Add a devil's advocate trigger to the consensus algorithm. When all 5 persona scores are >= 8.0, spawn one additional persona with the system prompt:

```
You are a Devil's Advocate reviewer. The code under review has received
unanimous approval from 5 independent experts. Your job is to find the
problems they missed. Be adversarial. Look for:
- Assumptions everyone made but nobody questioned
- Edge cases that seem unlikely but would be catastrophic
- Subtle coupling or hidden dependencies
- Things that work today but will break under change
```

If the devil's advocate finds a Critical or High severity issue, the consensus reverts to FAIL regardless of the other scores.

**Effort:** Low. Single function addition to the consensus module.

**Impact:** High. Catches the exact class of bugs that slip through when everyone agrees.

---

### 2. Task-Aware Memory Retrieval Weights

**Source:** `memory/engine.py` lines 28-61, based on arXiv 2512.18746 (MemEvolve)

**What Loki does:** Different task types retrieve different memory types with different weights:

| Task Type | Episodic | Semantic | Skills | Anti-Patterns |
|-----------|----------|----------|--------|---------------|
| Exploration | 0.60 | 0.30 | 0.10 | 0.00 |
| Implementation | 0.15 | 0.50 | 0.35 | 0.00 |
| Debugging | 0.40 | 0.20 | 0.00 | 0.40 |
| Review | 0.30 | 0.50 | 0.00 | 0.20 |
| Refactoring | 0.25 | 0.45 | 0.30 | 0.00 |

The MemEvolve research found that task-aware adaptation improves retrieval performance by 17% over static weights. When debugging, you want anti-patterns (what went wrong before) at 40% weight. When implementing, you want semantic patterns (reusable solutions) at 50%. When exploring, you want episodic memory (what happened recently) at 60%.

**Why WFC needs this:** WFC's `ReflexionMemory` in `wfc/scripts/memory_manager.py` is session-scoped and uses flat retrieval -- no distinction between "I'm debugging" vs "I'm implementing a new feature." This means the memory system returns the same kind of results regardless of context.

**Integration point:** Add a task-type detection function (keyword matching on the current goal/phase, similar to Loki's `_detect_task_type` at `memory/engine.py:991-1066`) and apply weighted retrieval to the memory manager. The weight table above is the core of the change.

**Effort:** Medium. Requires adding task type detection and weighted scoring to the existing memory system.

**Impact:** High. Agents get contextually relevant memories instead of generic recall. Debugging agents see past failures; implementation agents see reusable patterns.

---

### 3. Two-Stage Review: Spec Compliance Then Code Quality

**Source:** `skills/quality-gates.md` lines 360-455, inspired by Superpowers (obra)

**What Loki does:** Review is split into two sequential stages:

1. **Stage 1 - Spec Compliance:** "Does this code implement what the spec requires?" One reviewer checks that all required features are present, no scope creep occurred, edge cases from the spec are handled, and tests verify spec requirements. This reviewer explicitly does NOT evaluate code quality.

2. **Stage 2 - Code Quality:** "Is this code well-written?" Three blind reviewers check readability, security, error handling, performance, and conventions. They explicitly do NOT re-check spec compliance.

Stage 1 must PASS before Stage 2 runs. If Stage 1 fails, the code goes back to implementation -- there is no point quality-reviewing code that implements the wrong feature.

**Why WFC needs this:** WFC's 5-persona review mixes spec compliance with code quality. A security persona might approve code that doesn't match the task specification because their focus is OWASP, not requirements traceability. This leads to "technically excellent code that solves the wrong problem" passing review.

**Integration point:** Add a spec-compliance gate to `wfc/scripts/skills/review/orchestrator.py` that runs before the persona-based review. One agent receives the original task specification and the diff, and checks only: "Does this implement what was asked? Does it implement ONLY what was asked?" If this gate fails, skip the 5-persona review entirely and return to implementation.

**Effort:** Medium. New gate in the review orchestrator, new prompt template.

**Impact:** High. Prevents the entire class of "wrong feature, great code" bugs that multi-persona review misses by design.

---

### 4. Complexity Auto-Detection for Workflow Scaling

**Source:** `SKILL.md` lines 241-250

**What Loki does:** Auto-detects project complexity and adjusts workflow depth:

| Tier | Files Changed | Phases Used | Review Depth |
|------|--------------|-------------|--------------|
| Simple | 1-2 files | 3 phases | Lightweight |
| Standard | 3-10 files | 6 phases | Full |
| Complex | 10+ files | 8 phases | Full + deepen-plan |

A simple UI text change doesn't need 8 SDLC phases, 7 quality gates, and 5 expert reviewers. A microservices refactor needs all of it.

**Why WFC needs this:** WFC offers `/wfc-build` (quick) vs `/wfc-plan` + `/wfc-implement` (full) but the user must choose. There is no auto-detection. This means either the user over-engineers simple tasks or under-engineers complex ones.

**Integration point:** Add complexity detection to the orchestrator in `wfc/skills/wfc-build/`. Before spawning agents, analyze the scope: count files affected, estimate number of modules touched, check for cross-cutting concerns (auth, database, API changes). Map to a complexity tier and adjust the number of agents, review depth, and quality gate strictness.

```
Simple:  1 agent, no consensus review, automated checks only
Standard: 1-3 agents, 3-persona review, full quality gates
Complex: 3-8 agents, 5-persona review, full gates + spec compliance stage
```

**Effort:** Medium. Detection heuristic + conditional logic in the orchestrator.

**Impact:** Medium-high. Eliminates both over-engineering (simple tasks) and under-engineering (complex tasks). Better resource usage.

---

### 5. Compound Learning: Cross-Project Solution Extraction

**Source:** `skills/compound-learning.md` lines 1-123

**What Loki does:** After a task passes verification, Loki evaluates whether the task produced a **novel insight** -- a bug with a non-obvious root cause, a solution that required multiple attempts, a reusable pattern, or a pitfall worth documenting. If so, it extracts a structured solution to `~/.loki/solutions/{category}/{slug}.md` with YAML frontmatter:

```yaml
---
title: "Connection pool exhaustion under load"
category: performance
tags: [database, pool, timeout, postgres]
symptoms:
  - "ECONNREFUSED on database queries under load"
root_cause: "Default pool size insufficient for concurrent requests"
prevention: "Set pool size to 2x expected concurrent connections"
confidence: 0.85
---
```

Before each new task, Loki searches these solutions by matching task keywords against tags and symptoms, then injects the top 3 relevant solutions (title + root_cause + prevention, under 500 tokens) into the agent's context.

**Why WFC needs this:** WFC's `ReflexionMemory` learns within a session. When the session ends, the learnings are gone. Loki's approach compounds knowledge across projects and sessions -- a bug fix learned in Project A prevents the same bug in Project B months later.

**Integration point:** Add a post-task evaluation step. After quality gates pass, a lightweight check determines if the solution was novel (required >1 attempt, involved non-obvious debugging, produced a reusable pattern). If novel, extract to `.development/solutions/{category}/` with the structured format above. During the REASON/planning phase of future tasks, search these solutions and inject relevant ones.

Seven fixed categories keep organization simple: security, performance, architecture, testing, debugging, deployment, general.

**Effort:** Medium. Post-task hook + retrieval function + storage format.

**Impact:** High over time. Knowledge compounds. The 50th project benefits from all 49 that came before it.

---

### 6. RARV Wrapper for All Agent Tasks

**Source:** `SKILL.md` lines 39-65

**What Loki does:** Every agent action follows Reason-Act-Reflect-Verify:

```
REASON: Read past mistakes. Check continuity log. Identify highest priority task.
   |
ACT: Execute task. Write code. Commit atomically.
   |
REFLECT: Log outcome. Update state. Identify what to do next.
   |
VERIFY: Run tests. Check build. Validate against spec.
   |
   +--[PASS]--> Extract learning if novel. Move to next task.
   +--[FAIL]--> Log to "Mistakes & Learnings". Retry with new approach.
               After 3 failures: simpler approach. After 5: dead-letter queue.
```

**Why WFC needs this:** WFC's per-agent workflow (UNDERSTAND -> TEST_FIRST -> IMPLEMENT -> REFACTOR -> QUALITY_CHECK -> SUBMIT) is implementation-focused. The RARV pattern adds two things WFC lacks: (a) consulting past failures before acting (REASON), and (b) structured reflection after every action (REFLECT), not just at task completion. The 3-failure escalation (try simpler approach) and 5-failure dead-letter queue are also pragmatic -- WFC currently has no defined behavior for repeated failures.

**Integration point:** Wrap the existing per-agent workflow in a RARV shell in `wfc/skills/wfc-implement/agent.py`:
- **REASON:** Before UNDERSTAND, search ReflexionMemory + compound solutions for relevant past failures.
- **REFLECT:** After QUALITY_CHECK, log the outcome (success/failure, what was learned, what was unexpected).
- **VERIFY:** Already exists via quality gates, but add the failure escalation ladder (3 attempts -> simplify, 5 attempts -> dead-letter and move on).

**Effort:** Low-medium. Wraps existing workflow rather than replacing it.

**Impact:** Medium. Systematic self-correction. Prevents agents from banging their head against the same wall.

---

### 7. File-Based Event Bus for Cross-Process Communication

**Source:** `events/bus.py`

**What Loki does:** A file-based event bus where events are JSON files written to `.loki/events/pending/` with `fcntl` file locking. Any process (Python, Node, Bash, VS Code extension) can emit events and subscribe. Events have types (state, memory, task, metric, error, session, command, user) and sources (cli, api, vscode, mcp, skill, hook, dashboard, memory, runner). Processed events move to an archive for replay/debugging.

Key design properties:
- Cross-language (JSON files, no shared memory)
- Survives crashes (file-based persistence)
- Supports replay (archived events)
- No external dependencies (no Redis, no message broker)
- Bounded growth (processed IDs pruned to last 1000)

**Why WFC needs this:** WFC has hooks (pre/post tool use) but no general-purpose event system. The hooks are reactive (triggered by tool calls) but there is no way for agents to communicate with each other, for the dashboard to subscribe to agent completions, or for MCP to react to state changes. An event bus would enable:
- Agent A completing a task and Agent B picking up the next one without orchestrator polling
- Real-time dashboard updates as agents work
- Hook-like behavior without being coupled to tool call lifecycle
- Audit trail of all system events

**Integration point:** Port the core event bus concept to `wfc/scripts/events/`. Keep it simple: emit/subscribe/archive with JSON files in `.development/events/`. Integrate with the existing hook system so hooks can emit events, and new subscribers can react to them.

**Effort:** Medium. The bus itself is ~400 lines. Integration with existing hooks and orchestrator is the real work.

**Impact:** Medium. Infrastructure investment that enables future capabilities (dashboard, multi-agent coordination, MCP integration, audit trails).

---

### 8. Chain-of-Verification (CoVe) for Critical Paths

**Source:** `skills/quality-gates.md` lines 24-204, based on arXiv 2309.11495

**What Loki does:** For code verification, implements a 4-step protocol:

1. **Draft:** Generate initial implementation.
2. **Plan:** Self-generate verification questions ("What claims did I make? What could be wrong?").
3. **Execute (Factored):** Answer each verification question INDEPENDENTLY, with NO access to the original implementation. The verifier sees only the claim being checked + minimal context (e.g., function signature, not the full code).
4. **Revise:** Incorporate corrections into the final output.

The critical insight is **factored execution**: without it, the model rationalizes its own mistakes ("Let me check my code... looks correct!"). With factored execution, the verifier reasons independently ("Given a function that takes X, null handling requires...") because it cannot see the original code.

The paper tested 4 variants and found Factor+Revise (factored execution + explicit cross-check step) works best for long-form code generation.

**Why WFC needs this:** WFC's reviewers see the full code context. This means they can (and do) rationalize issues rather than independently verifying claims. For security-critical or correctness-critical paths (authentication, payment processing, data migrations), factored verification would catch errors that full-context review misses.

**Integration point:** Add CoVe as an optional high-assurance review mode in `wfc/scripts/skills/review/`. For tasks tagged as security-critical or high-risk, decompose the implementation into verifiable claims, then verify each claim in a separate subagent that receives only the claim + function signature (not the full implementation). This runs before the standard persona-based review.

**Effort:** High. Requires claim decomposition, factored subagent dispatch, and result aggregation.

**Impact:** High for critical paths. This is the strongest verification technique in Loki's arsenal, backed by peer-reviewed research. Reserve it for high-risk changes where the cost of a missed bug is high.

---

## Ideas to Reject

### 1. 41 Hardcoded Agent Types Across 7 Swarms

**What Loki does:** Defines 41 agent types (eng-frontend, ops-devops, biz-marketing, etc.) organized into 7 swarms (Engineering, Operations, Business, Data, Product, Growth, Review).

**Why WFC should reject this:** WFC's 56 personas selected by semantic matching against file types, properties, and context is more flexible. Hardcoded agent types create rigid categories -- what happens when a task spans frontend + security + performance? Loki must pick from predefined types. WFC's orchestrator selects the 5 most relevant experts dynamically.

Additionally, many of Loki's agent types (biz-marketing, biz-sales, biz-legal, biz-hr, growth-hacker, growth-community) are outside the scope of a code quality tool. WFC is correctly focused on engineering excellence, not business operations.

**Risk of adopting:** Scope creep. Rigidity. Maintenance burden of 41 agent definitions.

---

### 2. "NEVER Ask, NEVER Wait, NEVER Stop" Autonomy Philosophy

**What Loki does:** Three absolute rules: never ask questions, never wait for confirmation, never stop working. The agent makes all decisions autonomously and keeps improving the codebase perpetually.

**Why WFC should reject this:** This philosophy requires `--dangerously-skip-permissions` and leads to unbounded autonomous execution. WFC's human-in-the-loop approach (review PRs before merge, user pushes manually, consensus review with human oversight) is fundamentally safer. The "never stop" rule in particular is a scope creep generator -- there is always another "improvement" to make, but each one risks introducing bugs.

The WFC philosophy of "stop when the task is done, let the human review and push" is more disciplined and produces higher-quality outcomes because it forces clear task boundaries.

**Risk of adopting:** Runaway agents making unbounded changes. Security incidents from autonomous deployment. Scope creep. User trust erosion.

---

### 3. `--dangerously-skip-permissions` as a Prerequisite

**What Loki does:** Requires Claude Code to run with all permissions disabled. This is a hard requirement for autonomous operation.

**Why WFC should reject this:** WFC's hook system (`pretooluse_hook.py`, `security_hook.py`, `rule_engine.py`) provides guardrails that work WITH the permission system, not against it. Hooks can enforce security patterns, validate file operations, and block dangerous actions while still allowing productive work. Disabling all permissions removes the safety net entirely.

**Risk of adopting:** Security vulnerabilities. Accidental destructive operations. Loss of the guardrail infrastructure that WFC has invested in building.

---

### 4. Enterprise Feature Sprawl (Dashboard/OIDC/RBAC/SIEM/Prometheus)

**What Loki does:** Includes TLS/HTTPS encryption, OIDC/SSO integration (Google, Azure AD, Okta), 4-tier RBAC, Prometheus metrics export, syslog forwarding for SIEM, SHA-256 audit trail integrity chains, and OpenClaw multi-agent coordination protocol.

**Why WFC should reject this:** These features are documented extensively but are largely aspirational configuration rather than battle-tested infrastructure. WFC should stay focused on its core competency: making code quality excellent through multi-agent review, TDD, and intelligent orchestration. Enterprise observability and access control are valid concerns but should be addressed through integration with existing tools (Prometheus, Grafana, existing SSO providers) rather than building them into the code quality framework itself.

**Risk of adopting:** Feature bloat. Maintenance burden. Distraction from core value proposition. Under-tested enterprise features creating false confidence.

---

### 5. Perpetual Improvement Mode

**What Loki does:** After completing the PRD, Loki enters an endless improvement loop: optimizing performance, adding test coverage, improving documentation, refactoring code smells, updating dependencies, enhancing UX, implementing A/B test learnings. It "keeps going until you stop it."

**Why WFC should reject this:** Unbounded improvement is the opposite of disciplined engineering. Each "improvement" carries risk: introducing bugs, changing behavior, breaking existing tests. WFC's defined task boundaries (plan -> implement -> review -> done) produce predictable outcomes. A clear stopping point forces prioritization: do the most important thing well, then stop. Endless polishing produces diminishing returns and increasing risk.

**Risk of adopting:** Scope creep. Unnecessary changes introducing bugs. Token/cost waste. Difficulty attributing regressions to specific "improvements."

---

## Implementation Priority Matrix

| Priority | Idea | Effort | Impact | Dependencies |
|----------|------|--------|--------|--------------|
| P0 | Anti-sycophancy devil's advocate | Low | High | None |
| P1 | Two-stage review (spec then quality) | Medium | High | None |
| P1 | Task-aware memory retrieval | Medium | High | None |
| P2 | Complexity auto-detection | Medium | Medium-High | None |
| P2 | RARV wrapper for agents | Low-Medium | Medium | Compound learning (P3) |
| P3 | Compound learning (cross-project) | Medium | High (over time) | None |
| P3 | File-based event bus | Medium | Medium | None |
| P4 | Chain-of-Verification (CoVe) | High | High (critical paths) | Two-stage review (P1) |

**Recommended sequencing:** P0 first (quick win), then P1 in parallel (both are independent), then P2, then P3/P4 as the system matures.

---

## Appendix: Source Files Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| `SKILL.md` | 266 | Core skill definition, RARV cycle, autonomy rules |
| `CLAUDE.md` | 370 | Developer guidelines, release workflow |
| `README.md` | 1003 | Full feature documentation |
| `memory/engine.py` | 1236 | 3-tier memory engine with task-aware retrieval |
| `events/bus.py` | 440 | File-based cross-process event bus |
| `skills/00-index.md` | 138 | Progressive disclosure module routing |
| `skills/quality-gates.md` | 539 | 7-gate system, CoVe, velocity-quality loop |
| `skills/compound-learning.md` | ~200 | Knowledge extraction and deepen-plan |
| `skills/agents.md` | ~150 | Agent dispatch and structured prompting |
| `autonomy/context-tracker.py` | 366 | Context window and cost tracking |
