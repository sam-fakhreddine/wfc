# Phase 0: Deviation Map — WFC vs. White Paper Mandates

**Date**: 2026-02-19
**Auditor**: Lead Multi-Agent Systems Architect (Claude)
**Scope**: Full WFC repository audit against "Advanced Architectures for LLM-Driven Multi-Agent Systems"
**Constraint**: Maturity Override active — WFC superiority documented and preserved

---

## Executive Summary

WFC is a **production-mature** multi-agent orchestration framework with 830+ tests, 28 validated skills, and a mathematically grounded consensus review system. The audit found:

| Verdict | Count | Description |
|---------|-------|-------------|
| **WFC SUPERIOR** | 4 | WFC implementation exceeds white paper baseline |
| **PARTIAL COVERAGE** | 5 | Core concept exists but gaps remain |
| **NOT IMPLEMENTED** | 5 | White paper mandate has no WFC equivalent |
| **NOT APPLICABLE** | 1 | Mandate doesn't fit WFC's execution model |

**Critical finding**: WFC's strengths are in **algorithmic arbitration** (Phase 2), **fail-open resilience** (Phase 5), and **knowledge codification** (Phase 6). Its gaps are in **pre-reasoning security** (Phase 1), **schema-driven self-correction** (Phase 3), and **execution sandboxing** (Phase 4).

---

## Phase 1: Security Boundary Integration

### 1.1 Pre-Reasoning Semantic Firewall

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Deterministic filtering layer *before* the primary reasoning model | PreToolUse hook intercepts *after* reasoning, *before* tool execution |
| **Timing** | Pre-reasoning (prompt never reaches LLM) | Post-reasoning, pre-execution (LLM reasons freely, tools are gated) |
| **Mechanism** | Vector similarity against attack signature DB | Regex pattern matching against `security.json` (8 patterns) |

**Verdict**: `NOT IMPLEMENTED` — Fundamentally different architecture.

**Gap Analysis**:
- WFC has **no prompt-level filtering**. Claude's reasoning is unrestricted; only tool calls are intercepted.
- Security hook (`pretooluse_hook.py`) operates at the **tool boundary**, not the **prompt boundary**.
- Regex patterns catch known dangerous APIs (`eval()`, `os.system()`, `subprocess shell=True`, `rm -rf /`) but cannot detect semantic attacks, prompt injections, or obfuscated patterns.

**Maturity Override**: N/A — no WFC equivalent exists.

**Recommendation**: **IMPLEMENT**. Add a `SemanticFirewall` module that:
1. Embeds incoming prompts via a lightweight model
2. Compares against a curated attack signature vector DB
3. Routes high-similarity prompts to a deterministic Refusal Agent
4. Preserves WFC's existing tool-level hook as a **second defense layer**

**Files to create**:
- `wfc/scripts/security/semantic_firewall.py`
- `wfc/scripts/security/attack_signatures.json` (or vector DB)
- `wfc/scripts/security/refusal_agent.py`

---

### 1.2 Vector Similarity Verification

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Cosine similarity against adversarial embeddings | No embedding-based detection |
| **Infrastructure** | Embedding client + signature DB | RAG engine exists (`rag_engine.py`) but used for knowledge retrieval, not security |

**Verdict**: `NOT IMPLEMENTED`

**Gap Analysis**:
- WFC has a functional embedding pipeline in `wfc/scripts/knowledge/rag_engine.py` with `EmbeddingProvider` abstraction.
- This infrastructure could be **repurposed** for attack signature matching with minimal new code.
- The `KnowledgeRetriever` already does cosine similarity search — the same pattern applies to adversarial detection.

**Recommendation**: **IMPLEMENT** by extending existing RAG infrastructure. Reuse `EmbeddingProvider` for attack signature embeddings.

---

### 1.3 Refusal Agent Routing

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Deterministic bypass of primary LLM on threat detection | Hook exits with code 2 (block) + stderr reason |
| **Response** | Refusal Agent generates safe response | No agent — just a blocking exit code |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
- WFC's hook system **does block** dangerous tool calls (exit code 2).
- But there's no structured "Refusal Agent" that explains the block, suggests alternatives, or logs the incident with full context.
- The block reason is a simple string on stderr, not a structured response.

**WFC Strength to Preserve**: The fail-open design (`exit 0` on hook errors) is superior to the white paper's implicit fail-closed assumption. A hook bug must never block the user's workflow. **Retain this.**

**Recommendation**: **ENHANCE**. Add a `RefusalAgent` that:
1. Receives the blocked tool call context
2. Generates a structured explanation (why blocked, what to do instead)
3. Logs to observability bus (`emit_event("security.refusal", ...)`)
4. Preserves fail-open: if RefusalAgent itself fails, fall back to simple stderr message

---

## Phase 2: Orchestration Topology

### 2.1 Hierarchical Supervisor

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Primary orchestrator delegates to subagents in isolated contexts | ReviewOrchestrator + WFCOrchestrator delegate via Claude Code Task tool |
| **Isolation** | Strictly isolated context windows | Each subagent gets independent prompt, no shared state |
| **Hierarchy** | Macro-intent analysis → task decomposition | Two-phase: prepare_review_tasks() → finalize_review() |

**Verdict**: `WFC SUPERIOR`

**Justification**:
- WFC's **two-phase orchestration** (prepare → finalize) is cleaner than a monolithic supervisor. The orchestrator never reasons about code — it builds task specs and scores results.
- **ReviewOrchestrator** delegates to 5 specialist reviewers with domain-specific prompts + knowledge. Each reviewer is truly isolated (no cross-reviewer contamination).
- **WFCOrchestrator** manages a DAG-validated task graph with topological ordering, confidence gating (>=90% proceed, 70-89% ask, <70% stop), and per-task worktree isolation.
- **Model routing** (`ModelRouter`) selects optimal model per reviewer based on diff size and reviewer domain — a cost optimization the white paper doesn't address.

**Retain**: Full orchestration topology. No changes needed.

---

### 2.2 Fan-Out/Gather Arbitration

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Replace probabilistic LLM summarization with algorithmic arbitration | Consensus Score (CS) algorithm — fully deterministic |
| **Algorithm** | Majority voting, confidence-weighted, or SMT solver | CS = (0.5 * R_bar) + (0.3 * R_bar * k/n) + (0.2 * R_max) |
| **Tie-breaking** | Not specified | Minority Protection Rule (MPR): single critical finding can override consensus |

**Verdict**: `WFC SUPERIOR`

**Justification**:
The white paper proposes three arbitration algorithms. WFC implements a **hybrid that outperforms all three**:

1. **vs. Majority Voting** (Algorithm 1): WFC's CS formula uses continuous severity/confidence scores, not binary votes. A 9.5-severity finding from one reviewer outweighs five 3.0-severity findings — majority voting can't express this.

2. **vs. Confidence-Weighted** (Algorithm 2): WFC incorporates confidence via `R_i = (severity * confidence) / 10` but adds **agreement weighting** (`k/n` term) and **peak detection** (`R_max` term). This is strictly more expressive.

3. **vs. SMT Solver** (Algorithm 3): Overkill for code review. WFC's approach is O(n) computation vs. NP-hard SMT solving, with zero external dependencies.

**Additional WFC strengths not in the white paper**:
- **SHA-256 fingerprint deduplication** with ±3-line tolerance merges cross-reviewer findings
- **MPR (Minority Protection Rule)**: If `R_max >= 8.5` from security/reliability, CS is elevated to `max(CS, 0.7 * R_max + 2.0)` — prevents critical findings from being diluted by benign consensus
- **3-layer finding validation**: Structural verification → LLM cross-check → historical pattern match, with weight mapping (VERIFIED=1.0, UNVERIFIED=0.5, DISPUTED=0.2, HISTORICALLY_REJECTED=0.0)
- **Conditional activation**: Reviewers marked `relevant=False` can be skipped, saving tokens

**Retain**: Full CS algorithm, fingerprinting, MPR, and finding validation. No changes needed.

---

## Phase 3: State Management & Artifact Governance

### 3.1 Context Compression (Observation Masking)

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Rolling window preserving reasoning tokens, replacing old observations with placeholders | Context window monitoring with tiered warnings (80/90/95%) |
| **Mechanism** | Deterministic observation masking | Token budgets per complexity (S=200, M=1K, L=2.5K, XL=5K) |
| **Cross-session** | Not specified | Reflexion memory (append-only JSONL), but not queried at task start |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
- WFC **monitors** context usage but doesn't **compress** it.
- `context_monitor.py` warns at thresholds but doesn't implement rolling windows or observation masking.
- Token budgets exist per task complexity but don't dynamically adjust based on context pressure.
- Knowledge retrieval respects token budgets (500 tokens default, truncates to fit).
- Diff truncation at 50K chars exists but is a hard cutoff, not a compression algorithm.

**WFC Strength to Preserve**: The tiered warning system (80% prepare, 90% mandatory handoff, 95% critical) is pragmatic for Claude Code's session model. The white paper's rolling window assumes a long-running agent loop — WFC's sessions are shorter-lived.

**Recommendation**: **ENHANCE** with lightweight observation masking:
1. For long-running sessions (>80% context), summarize completed task results into compact state tokens
2. Add `ObservationMasker` that replaces verbose tool outputs with structured summaries
3. Preserve reasoning chain tokens (decisions, rationale) while compressing environmental data (file contents, test output)

---

### 3.2 Strict Schema Adherence (Pydantic/Zod/TypeChat)

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | All LLM outputs validated by Pydantic schemas | Pure Python dataclasses with `.to_dict()` / `.from_dict()` |
| **Enforcement** | Validation errors trigger re-prompting | Parse failures → empty list fallback (fail-open) |
| **Coverage** | All foundational model returns | Core types fully typed, but no runtime validation |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
WFC uses **comprehensive dataclasses** for all core types:
- `ConsensusScoreResult`, `DeduplicatedFinding`, `ValidatedFinding`
- `MergeResult`, `AgentReport`, `TokenBudget`, `ReflexionEntry`
- `BypassRecord`, `ReviewerConfig`, `ObservabilityEvent`

These are well-structured but **not validated at construction time**. A `DeduplicatedFinding` with `severity=-1.0` would be accepted silently.

**WFC Strength to Preserve**: The ELEGANT philosophy of using dataclasses over Pydantic is deliberate — it avoids Pydantic's import overhead, keeps the dependency graph minimal, and matches WFC's "simplest solution wins" ethos. For **internal** data structures, this is appropriate.

**Recommendation**: **SELECTIVE IMPLEMENTATION**:
1. Add Pydantic models **only at LLM output boundaries** (where subagent responses are parsed into findings)
2. Keep internal dataclasses as-is (they're correct and performant)
3. Create `wfc/scripts/schemas/` with Pydantic models for: `ReviewerOutput`, `AgentOutput`, `DocumentationPayload`
4. Wire validation into `ReviewerEngine.parse_results()` and `ExecutionEngine._collect_report()`

---

### 3.3 Self-Correction Loops

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Catch validation errors → feed back to LLM as correction prompt | No feedback loop — malformed output → fallback to empty/default |
| **Retries** | Max N attempts with schema error in prompt | Task-level retries exist (max_retries=2) but for execution failures, not parse failures |

**Verdict**: `NOT IMPLEMENTED` (at the schema level)

**Gap Analysis**:
- WFC has **task-level retries** (MergeEngine retries on ERROR severity).
- WFC has **multi-layer JSON parsing** (raw_decode → regex → markdown code blocks → simple object).
- But when all parsing fails, WFC returns `[]` — it does NOT re-prompt the LLM with "fix your JSON."
- The 3-layer finding validator **downgrades confidence** on disputed findings (weight 0.2) but doesn't re-ask the reviewer.

**Recommendation**: **IMPLEMENT** the `AgenticValidator` pattern from Module B:
1. Wrap LLM output parsing in a retry loop (max 3 attempts)
2. On `ValidationError`, append the exact error to the prompt: `[SYSTEM CORRECTION]: Fix these schema errors: {error_json}`
3. Apply to `ReviewerEngine.parse_results()` and `ExecutionEngine._collect_report()`
4. Preserve fail-open: after max retries, fall back to current behavior (empty list)

**Files to create/modify**:
- `wfc/scripts/schemas/agentic_validator.py` (new)
- `wfc/scripts/orchestrators/review/reviewer_engine.py` (modify `_parse_findings()`)

---

## Phase 4: Protocol & Execution Boundaries

### 4.1 Protocol Standardization (MCP / A2A)

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **MCP** | Client-server API bridging | Not implemented — uses Claude Code Task tool natively |
| **A2A** | Decentralized peer-to-peer via agent.json cards | Not implemented — centralized orchestrator model |
| **Discovery** | `/.well-known/agent.json` | No agent discovery mechanism |

**Verdict**: `NOT APPLICABLE` (with caveat)

**Justification**:
WFC is designed as a **Claude Code extension**, not a standalone multi-agent platform. Its agents are spawned via Claude Code's `Task` tool, which handles:
- Context isolation (each subagent gets a fresh context window)
- Communication (JSON task specs in, text responses out)
- Lifecycle management (subagent creation, execution, result collection)

Adding MCP/A2A would introduce:
- External dependencies (MCP server, A2A resolver)
- Network overhead (HTTP/SSE vs. in-process Task tool)
- Complexity without clear benefit for the current use case

**However**: If WFC ever needs to coordinate with **external agent frameworks** (e.g., LangGraph, CrewAI, AutoGen), MCP/A2A becomes necessary.

**Recommendation**: **DEFER** to a future phase. If needed:
1. Create `wfc/protocols/agent_card.py` with A2A `agent.json` template (Module A)
2. Expose WFC's review orchestrator as an MCP server
3. Keep internal communication via Task tool (performance-critical path)

---

### 4.2 Execution Sandboxing (WASM)

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | WASM sandbox (Pyodide) for untrusted code | Git worktrees for filesystem isolation (not security boundary) |
| **Network** | Zero default network access | DevContainer firewall (audit mode by default — allows everything) |
| **Filesystem** | Ephemeral | Worktrees persist until cleanup |

**Verdict**: `NOT IMPLEMENTED`

**Gap Analysis**:
- **Worktrees** (`worktree-manager.sh`) provide filesystem isolation between parallel agents but are NOT security boundaries. Same user, same permissions, same host OS.
- **DevContainer firewall** (`init-firewall.sh`) has enforce mode with whitelist, but defaults to audit mode (allow-all).
- **No WASM runtime** — all code executes on the host.
- **No process isolation** — no seccomp, AppArmor, or capability dropping.

**WFC Strength to Preserve**: Worktree-based isolation is pragmatic for code review (agents can't accidentally modify each other's files). This is a correct architectural choice for WFC's domain.

**Recommendation**: **SELECTIVE IMPLEMENTATION**:
1. For **WFC's core use case** (code review, implementation), worktrees are sufficient. No WASM needed.
2. For **untrusted code execution** (if WFC ever evaluates user-submitted code), add WASM sandbox:
   - `wfc/scripts/security/wasm_sandbox.py` wrapping Pyodide
   - Zero network access, ephemeral filesystem, timeout enforcement
3. **Immediately**: Change DevContainer firewall default from `audit` to `enforce`. Audit mode provides no security.

---

## Phase 5: Exception Handling & Recovery

### 5.1 TRAIL Taxonomy Logging

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Classify failures: E = R (Reasoning) ∪ P (Planning) ∪ S (System) | `FailureSeverity` enum: WARNING, ERROR, CRITICAL |
| **Loop detection** | Infinite loops → Planning (P) error → max-iteration abort | Confidence gating (<70% → STOP) prevents loops; max_retries=2 on merge |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
- WFC classifies failure **severity** (how bad) but not failure **type** (why it happened).
- A test failure and a network timeout both produce `FailureSeverity.ERROR` — but one is Reasoning and the other is System.
- The observability bus (`emit_event()`) logs events but doesn't classify them into R/P/S taxonomy.
- Infinite loop prevention exists via confidence gating and max_retries, but isn't labeled as Planning errors.

**WFC Strength to Preserve**: The severity-based classification (WARNING doesn't block, ERROR blocks but retries, CRITICAL stops immediately) is more **actionable** than R/P/S for WFC's workflow. An operator cares about "can I retry?" more than "was this a reasoning error?"

**Recommendation**: **ENHANCE** (don't replace):
1. Add `FailureType` enum: `REASONING`, `PLANNING`, `SYSTEM` alongside existing `FailureSeverity`
2. Classify in `MergeEngine._classify_test_failure()`:
   - Test assertion failures → REASONING
   - Dependency resolution failures → PLANNING
   - Network/filesystem/timeout → SYSTEM
3. Log to observability bus: `emit_event("failure.classified", payload={"severity": ..., "type": ...})`
4. Use for analytics: "80% of retries are REASONING errors → improve reviewer prompts"

---

### 5.2 SagaLLM Transactional Rollbacks

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Saga pattern: T1,T2,...,Tn with compensating C1,C2,...,Cn | Atomic merge/rollback in MergeEngine |
| **Compensation** | LLM-generated compensating transactions | Git revert (deterministic, not LLM-generated) |
| **Validation** | Pydantic validation of Ci before execution | N/A — git revert is always safe |

**Verdict**: `WFC SUPERIOR`

**Justification**:
WFC's MergeEngine implements a **deterministic Saga** that is more reliable than the white paper's LLM-generated compensating transactions:

1. **Atomic merge/rollback**: Either fully merged or fully reverted. No partial states.
2. **Git revert** is a mathematically correct inverse operation — no LLM hallucination risk.
3. **Worktree preservation**: Failed merges keep the worktree for investigation (the white paper doesn't address forensics).
4. **Severity classification**: Determines if failure is retryable (ERROR) or permanent (CRITICAL).
5. **Recovery plan generation**: Sets `recovery_plan_generated=True` for downstream handling.

The white paper's approach of **LLM-generating compensating transactions** introduces a second failure mode: the compensation itself could be wrong. WFC avoids this by using deterministic git operations.

**Additional WFC strength**: **Emergency Bypass** with immutable audit trail (24h expiry, append-only `BYPASS-AUDIT.json`, records CS at bypass time). The white paper has no equivalent.

**Retain**: Full MergeEngine + EmergencyBypass. No changes needed.

---

### 5.3 Rollback Validation

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Pydantic validation of compensating transactions before execution | Git revert doesn't need validation (deterministic) |
| **Risk** | LLM-generated rollback could corrupt state | Zero risk — git revert is always correct |

**Verdict**: `WFC SUPERIOR`

**Justification**: By using deterministic git operations instead of LLM-generated compensating transactions, WFC eliminates the entire class of "secondary state corruption" that the white paper warns about. Validating the rollback is unnecessary when the rollback is a mathematical inverse.

**Retain**: No changes needed.

---

## Phase 6: Autonomous Documentation Hand-off

### 6.1 Structured CRUD Generation

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Agents emit `DocumentationCRUDPayload` JSON | wfc-compound emits structured markdown with YAML frontmatter |
| **Schema** | Pydantic model with target_file, action, content, rationale | Category-based routing with auto-detected filenames |
| **Actions** | CREATE, UPDATE, DELETE, APPEND | CREATE only (new solution docs) |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
- wfc-compound generates **well-structured documentation** with:
  - YAML frontmatter (title, module, component, tags, category, severity, status, root_cause)
  - Problem/Root Cause/Solution/Prevention sections
  - Auto-categorization (10 categories: build-errors, test-failures, runtime-errors, etc.)
- But it only supports **CREATE** — no UPDATE, DELETE, or APPEND to existing docs.
- No formal `DocumentationCRUDPayload` schema — the compound skill assembles markdown directly.
- No separation of "reasoning agent" vs. "documentation agent" — wfc-compound does both.

**WFC Strength to Preserve**: The two-phase architecture (5 parallel research subagents → single assembly) is more efficient than the white paper's single-agent CRUD approach. Parallel research + centralized writing prevents conflicting documentation.

**Recommendation**: **ENHANCE**:
1. Add `DocumentationCRUDPayload` Pydantic model (Module F) as the intermediate format
2. Extend actions: UPDATE (modify existing section), APPEND (add to existing doc), DELETE (remove stale docs)
3. Route payload to a dedicated `DocumentationAgent` that has exclusive write permissions to `docs/`
4. Reasoning agents emit payloads but **never write files directly**

---

### 6.2 Documentation Agent Handoff

| Dimension | White Paper Mandate | WFC Current State |
|-----------|-------------------|-------------------|
| **Concept** | Reasoning agents must NOT write docs; emit JSON → Documentation Agent writes | wfc-compound research subagents return TEXT → orchestrator writes ONE file |
| **Permissions** | Documentation Agent has exclusive `/docs` write access | No permission separation |

**Verdict**: `PARTIAL COVERAGE`

**Gap Analysis**:
- wfc-compound's Phase 1 subagents **correctly** return text only (no file writes).
- But the orchestrator (Phase 2) writes directly — there's no dedicated Documentation Agent with exclusive permissions.
- No audit trail of what was written, by whom, or why.

**WFC Strength to Preserve**: The parallel research → centralized write pattern already achieves the white paper's goal of preventing conflicting documentation. The only gap is formalization.

**Recommendation**: **FORMALIZE**:
1. Create `wfc/scripts/agents/documentation_agent.py` that:
   - Accepts `DocumentationCRUDPayload` as input
   - Validates payload via Pydantic
   - Executes CRUD operations on `docs/` and `docs/solutions/`
   - Logs all operations to observability bus
2. Modify wfc-compound to emit payload instead of writing directly
3. Add `workflow_id` and `generating_agent` tracing fields

---

## Consolidated Deviation Matrix

| # | Phase | Mandate | WFC Status | Verdict | Action |
|---|-------|---------|------------|---------|--------|
| 1.1 | Security | Pre-Reasoning Semantic Firewall | No prompt filtering | `NOT IMPLEMENTED` | **Implement** |
| 1.2 | Security | Vector Similarity Verification | No embedding-based detection | `NOT IMPLEMENTED` | **Implement** (reuse RAG infra) |
| 1.3 | Security | Refusal Agent Routing | Hook blocks but no structured response | `PARTIAL` | **Enhance** |
| 2.1 | Orchestration | Hierarchical Supervisor | Two-phase orchestrator + DAG | `WFC SUPERIOR` | **Retain** |
| 2.2 | Orchestration | Fan-Out/Gather Arbitration | CS algorithm + MPR + fingerprinting | `WFC SUPERIOR` | **Retain** |
| 3.1 | State | Context Compression | Token budgets + monitoring, no compression | `PARTIAL` | **Enhance** |
| 3.2 | State | Strict Schema Adherence | Dataclasses (no runtime validation) | `PARTIAL` | **Selective Pydantic at LLM boundaries** |
| 3.3 | State | Self-Correction Loops | No schema-driven re-prompting | `NOT IMPLEMENTED` | **Implement** (AgenticValidator) |
| 4.1 | Protocol | MCP / A2A Standardization | Claude Code Task tool (native) | `NOT APPLICABLE` | **Defer** |
| 4.2 | Protocol | WASM Execution Sandbox | Git worktrees (not security boundary) | `NOT IMPLEMENTED` | **Selective** (only if untrusted code) |
| 5.1 | Exception | TRAIL Taxonomy | Severity only, no type classification | `PARTIAL` | **Enhance** (add FailureType) |
| 5.2 | Exception | SagaLLM Rollbacks | Deterministic git revert (no LLM risk) | `WFC SUPERIOR` | **Retain** |
| 5.3 | Exception | Rollback Validation | Git revert = mathematically correct | `WFC SUPERIOR` | **Retain** |
| 6.1 | Docs | Structured CRUD Generation | CREATE only, no formal payload | `PARTIAL` | **Enhance** |
| 6.2 | Docs | Documentation Agent Handoff | Orchestrator writes directly | `PARTIAL` | **Formalize** |

---

## Recommended Implementation Priority

### Tier 1: High Impact, Clear Value (Phases 1 + 3.3)
1. **Semantic Firewall** (1.1 + 1.2) — Addresses a real security gap. Reuse existing RAG infrastructure.
2. **AgenticValidator / Self-Correction** (3.3) — Low effort, high yield. Reduces silent data loss from parse failures.
3. **Refusal Agent** (1.3) — Small addition to existing hook system.

### Tier 2: Structural Improvements (Phases 3.2 + 5.1 + 6)
4. **Pydantic at LLM boundaries** (3.2) — Selective, preserves ELEGANT philosophy.
5. **TRAIL failure classification** (5.1) — Enhances observability without changing behavior.
6. **Documentation CRUD + Agent** (6.1 + 6.2) — Formalizes existing pattern.

### Tier 3: Context Management (Phase 3.1)
7. **Observation Masking** (3.1) — Useful for long sessions, but WFC's session model is short-lived.

### Tier 4: Deferred (Phase 4)
8. **MCP/A2A** (4.1) — Only if cross-framework coordination is needed.
9. **WASM Sandbox** (4.2) — Only if WFC evaluates untrusted code.

---

## Preserved WFC Superiorities (Do Not Regress)

These implementations **must not be modified** during migration:

| Component | Why Superior | Key File |
|-----------|-------------|----------|
| CS Algorithm + MPR | Mathematically grounded, O(n), no external deps | `consensus_score.py` |
| SHA-256 Fingerprinting | Deterministic dedup with ±3-line tolerance | `fingerprint.py` |
| 3-Layer Finding Validation | Structural → Cross-check → Historical | `finding_validator.py` |
| Atomic MergeEngine | Deterministic git revert, no LLM hallucination risk | `merge_engine.py` |
| Emergency Bypass | 24h expiry, append-only audit, CS recorded | `emergency_bypass.py` |
| Fail-Open Hook Design | Hook bugs never block user workflow | `pretooluse_hook.py` |
| Two-Phase Orchestration | Prepare specs → Score results (no monolithic supervisor) | `orchestrator.py` |
| Model Router | Cost-optimized model selection per reviewer + diff size | `model_router.py` |
| wfc-compound Parallel Research | 5 subagents → centralized assembly (no conflicts) | `wfc-compound/SKILL.md` |
| Observability Event Bus | Direct-dispatch, provider isolation, thread-safe | `events.py` |

---

## Gate: Human Lead Approval Required

**This deviation map requires human lead approval before proceeding to Phase 1 implementation.**

Questions for the human lead:
1. Do you agree with the 4 "WFC SUPERIOR" verdicts? Any you want re-evaluated?
2. Is the Tier 1-4 priority ordering correct for your roadmap?
3. Should Phase 4.1 (MCP/A2A) be deferred or pulled into an earlier tier?
4. Is there a preference for Pydantic v1 or v2 for the schema boundary work?
5. Should the semantic firewall operate on ALL prompts or only on external/untrusted inputs?
