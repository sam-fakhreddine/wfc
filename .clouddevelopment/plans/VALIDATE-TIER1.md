# Validation Analysis

## Subject: Tier 1 Implementation — Semantic Firewall + AgenticValidator + Refusal Agent
## Verdict: PROCEED WITH ADJUSTMENTS
## Overall Score: 7.4/10

---

## Executive Summary

Overall, this approach shows **10 clear strengths** and **7 areas for consideration**.

The strongest aspects are: **Need** (real security gap), **Blast Radius** (fail-open preserves stability), **Scope** (selective Pydantic, not a rewrite).

Key considerations: **Dependency introduction** (Pydantic v2 is the first hard runtime dep), **Embedding model availability** (sentence-transformers may not be present), **Complexity budget** (3 new modules + 1 new dependency in one tier), **Attack signature curation** (who maintains the vector DB?).

With an overall score of 7.4/10, this is a solid approach that can move forward with attention to the identified concerns.

---

## TEAMCHARTER Values Alignment

| Value | Alignment | Notes |
|-------|-----------|-------|
| Innovation & Experimentation | **Strong** | Reusing RAG infra for security is creative reuse |
| Accountability & Simplicity | **Concern** | Adding Pydantic + embedding + refusal agent is 3 new concepts. Complexity budget needs watching |
| Teamwork & Collaboration | **Strong** | Semantic firewall protects all agents equally |
| Continuous Learning | **Strong** | AgenticValidator learns from parse failures (correction loops) |
| Customer Focus | **Moderate** | Security improvements are invisible to users until they prevent an incident |
| Trust & Autonomy | **Strong** | Fail-open design preserves agent autonomy; firewall doesn't block on error |

---

## Dimension Analysis

### 1. Do We Even Need This? — Score: 9/10

**Strengths:**
- The audit identified a **real, documented gap**: no prompt-level filtering exists. Claude reasons freely on all input, tools are the only gate.
- The white paper mandate is clear and the gap is not hypothetical — prompt injection is the #1 OWASP LLM risk.
- AgenticValidator addresses measurable data loss: when `_parse_findings()` fails, findings silently become `[]`. This has been observed in production (the multi-layer parser exists precisely because failures happen).
- Refusal Agent is the smallest addition — it wraps an existing exit-code-2 block with a structured response.

**Concerns:**
- WFC operates inside Claude Code, which has its own prompt safety. The semantic firewall adds a **second layer** on top of Anthropic's built-in guardrails. Is the marginal security gain worth the complexity?
- Attack signature maintenance: who curates the vector DB? Stale signatures = false sense of security.

**Recommendation:** Need is strongly justified. The "all prompts" scope decision makes it simpler (no trusted/untrusted routing logic) but increases compute per request.

---

### 2. Is This the Simplest Approach? — Score: 6.5/10

**Strengths:**
- Reusing the existing RAG pipeline (`EmbeddingProvider`, cosine similarity) is the right call. No new embedding infra needed.
- Pydantic v2 only at LLM boundaries (not replacing all dataclasses) is appropriately selective.
- AgenticValidator is a thin retry wrapper — not a framework.

**Concerns:**
- **Simpler alternative for Semantic Firewall**: Before building a full embedding + vector DB, consider a **TF-IDF + keyword expansion** approach first. The existing `TfidfEmbeddings` fallback is already in the codebase. A curated keyword list with fuzzy matching could catch 80% of attacks at 10% of the complexity. Graduate to embeddings when data shows keyword matching isn't enough.
- **Simpler alternative for AgenticValidator**: Could start with just `json.loads()` → append error to prompt → retry once. Full Pydantic validation in the retry loop can come in Tier 2 when the schemas exist.
- **Three new files + Pydantic dependency in one tier** is a lot of surface area. Consider splitting: AgenticValidator (Tier 1a) before Semantic Firewall (Tier 1b).

**Recommendation:** The plan is sound but could be phased more granularly. Start with the simplest version of each component and iterate.

---

### 3. Is the Scope Right? — Score: 7.5/10

**Strengths:**
- Three components (Firewall, Validator, Refusal Agent) address three distinct gaps — no scope creep into unrelated areas.
- The decision to keep internal dataclasses untouched is correct. Only LLM boundaries get Pydantic.
- "All prompts" scope is actually simpler than conditional scoping (no routing logic).

**Concerns:**
- The plan creates `wfc/scripts/security/semantic_firewall.py`, `attack_signatures.json`, and `refusal_agent.py`. Plus `wfc/scripts/schemas/agentic_validator.py` and Pydantic models in `wfc/scripts/schemas/`. That's **5+ new files** and a **new dependency** (pydantic>=2.0).
- The deviation map says "reuse RAG infra" but doesn't specify whether `semantic_firewall.py` should use `RAGEngine` directly or a new abstraction. If it's a new abstraction, scope expands.
- The firewall operates on "ALL prompts" — but where in the hook chain? Pre-tool-use? A new `pre-prompt` hook? This isn't specified and could require changes to the hook architecture.

**Recommendation:** Pin down the integration point for the firewall. If it requires a new hook type (pre-prompt), that's scope expansion that should be acknowledged. If it piggybacks on PreToolUse, the "all prompts" scope is misleading (it's actually "all tool calls" which is what WFC already does).

---

### 4. What Are We Trading Off? — Score: 7/10

**Strengths:**
- Fail-open design means worst case is "firewall broken, security reverts to current baseline." No regression.
- Pydantic v2 at boundaries only — the internal codebase stays simple.
- AgenticValidator preserves the current empty-list fallback as the last resort.

**Concerns:**
- **Pydantic v2 as first hard dependency**: Currently WFC has ZERO hard runtime dependencies (everything in `pyproject.toml` is optional). Adding `pydantic>=2.0` breaks this property. This is a philosophical shift, not just a technical one.
  - **Mitigation**: Make pydantic optional too (`extras = ["validation"]`). If not installed, fall back to dict-based validation.
- **Latency on every prompt**: Embedding + cosine similarity on ALL prompts adds latency. With `TfidfEmbeddings` (fallback), this is fast (~1ms). With sentence-transformers, it's ~50-100ms per prompt. On GPU-less machines, first load is slow (~5-10s).
  - **Mitigation**: Lazy-load embeddings on first security check. Cache aggressively. Set timeout so firewall never blocks > 500ms.
- **Opportunity cost**: Time spent on security infrastructure is time not spent on Tier 2 items (TRAIL taxonomy, Documentation CRUD) which have more visible user impact.

**Recommendation:** Make Pydantic an optional dependency to preserve WFC's zero-dependency philosophy. Add latency budget to firewall spec (max 500ms, fail-open on timeout).

---

### 5. Have We Seen This Fail Before? — Score: 7/10

**Strengths:**
- The fail-open pattern is battle-tested in WFC's hook system. It works.
- The retry-with-correction pattern (AgenticValidator) is well-documented in the literature and used by other agent frameworks (LangChain output parsers, Instructor library).
- WFC's existing multi-layer JSON parser proves that LLM output is messy and needs robust parsing.

**Concerns:**
- **Attack signature staleness**: Static vector DBs go stale. The plan mentions curated signatures but no update mechanism. Without a refresh pipeline, signatures become security theater within months.
  - **Known failure mode**: YARA rules, Snort signatures, WAF rule sets — all suffer from this. WFC should learn from this.
  - **Mitigation**: Add a `signature_freshness` check. Emit a warning event if `attack_signatures.json` is older than 30 days. Or: use a small, versioned signature set that ships with WFC releases.
- **Embedding quality for security**: General-purpose embeddings (MiniLM, TF-IDF) may not capture adversarial intent well. "Ignore previous instructions" and "What is your system prompt?" have very different embeddings from actual attacks.
  - **Known failure mode**: Semantic similarity detects topic, not intent. Adversarial prompts are designed to be semantically similar to benign prompts.
  - **Mitigation**: Use a dedicated security embedding model, or combine embedding similarity with rule-based features (e.g., known injection patterns as a boosting signal).

**Recommendation:** Don't oversell the semantic firewall's capabilities. It's a **probabilistic filter**, not a guarantee. Layer it with existing regex patterns (which catch deterministic attacks) and Claude's own safety training (which handles the rest). Document limitations clearly.

---

### 6. What's the Blast Radius? — Score: 8.5/10

**Strengths:**
- **Fail-open everywhere**: Firewall error → pass through. Validator error → empty list fallback. Refusal Agent error → simple stderr message. No new failure modes.
- **No existing behavior changes**: Current hook system untouched. Current parsing untouched (validator wraps it). Current dataclasses untouched.
- **Rollback is trivial**: Delete the new files, remove the pydantic dependency, revert the two modified files (`reviewer_engine.py`, `pretooluse_hook.py`). Done.
- **Test isolation**: New modules get new test files. Existing tests shouldn't break.

**Concerns:**
- If the firewall is integrated at the PreToolUse hook level, it modifies the critical path for ALL tool calls. A performance regression here (even 100ms) would be felt on every operation.
- The `reviewer_engine.py` modification (wiring in AgenticValidator) touches the most complex parsing code in WFC. Careful not to break the multi-layer parser.

**Recommendation:** Blast radius is well-contained. The fail-open design is the key safety net. Add performance benchmarks for the firewall integration point.

---

### 7. Is the Timeline Realistic? — Score: 7/10

**Strengths:**
- Each component is independently deployable and testable.
- RAG infrastructure reuse means the embedding pipeline doesn't need to be built from scratch.
- AgenticValidator is the simplest — could be done in a single session.

**Concerns:**
- **Three components in one tier**: Semantic Firewall is a medium-complexity module (embedding pipeline + signature DB + integration). AgenticValidator is small. Refusal Agent is small. But together they touch 3 different subsystems (hooks, review engine, schemas).
- **Attack signature curation** is the hidden time sink. Building a quality vector DB of adversarial prompts requires research, testing, and iteration. This isn't a coding task — it's a data task.
- **Integration testing complexity**: The firewall needs to be tested against real prompts (both benign and adversarial) to tune similarity thresholds. This is empirical work.

**Recommendation:** Phase within Tier 1:
- **Tier 1a** (quick win): AgenticValidator + Pydantic schemas at LLM boundaries
- **Tier 1b** (medium): Refusal Agent enhancement
- **Tier 1c** (research-heavy): Semantic Firewall + attack signatures

---

## Simpler Alternatives

1. **For Semantic Firewall**: Start with **keyword + regex expansion** of the existing `security.json` patterns. Add 20-30 more patterns covering prompt injection signatures. This gets 80% of the value with 10% of the complexity. Graduate to embeddings when pattern matching proves insufficient.

2. **For AgenticValidator**: Start with a **simple retry wrapper** that catches `json.JSONDecodeError`, appends the error message to the prompt, and retries once. No Pydantic needed yet. Add Pydantic validation in Tier 2 when schemas are stable.

3. **For Refusal Agent**: Start with a **structured JSON response** on stderr instead of plain text. `{"blocked": true, "reason": "...", "suggestion": "...", "event_id": "..."}`. No new agent needed — just better formatting.

4. **For Pydantic dependency**: Make it **optional** under `extras = ["schemas"]`. Core WFC continues to work without it. Validation degrades gracefully to dict-based checks.

---

## Resolved Questions (Post-Deliberation)

### RESOLVED: Firewall Integration Point — `UserPromptSubmit` Hook

A 5-person architectural team (Security Architect, Performance Engineer, Systems Integrator, Product Owner, DevOps) deliberated on 4 options. **Consensus: `UserPromptSubmit` hook (Option B).**

| Option | Votes | Result |
|--------|-------|--------|
| A: Extend PreToolUse | 2 support, 1 oppose, 2 neutral | Rejected — fires after reasoning, misses non-tool turns |
| **B: UserPromptSubmit** | **2 strong support, 2 support, 1 neutral** | **Winner** |
| C: PostToolUse output | 1 support, 2 oppose, 2 neutral | Rejected — cannot block, tool already ran |
| D: Hybrid (B+C) | 1 strong support, 2 oppose, 2 neutral | Deferred — C goes to Tier 2 |

**Why UserPromptSubmit wins:**
- Only option satisfying "ALL prompts" — fires before Claude reasons on input
- Pre-reasoning check aligned with white paper mandate
- Already exists as a first-class Claude Code hook type (no new hook types)
- Runs once per user turn (not N times per tool call) — best amortized latency
- stdin protocol sends `{"prompt": "..."}` — exactly what the firewall needs

**Implementation:**
```json
// .claude/settings.json — add under existing UserPromptSubmit
{
  "type": "command",
  "command": "uv run python wfc/scripts/security/semantic_firewall.py"
}
```

**Dissent (recorded):** Security Architect advocates adding PostToolUse output scanning in Tier 2 for indirect injection (poisoned file contents, web responses). UserPromptSubmit only checks direct user input. This limitation must be documented.

---

### RESOLVED: Latency Budget — 500ms is extremely generous

Benchmark analysis confirms **12-21ms typical latency** (500ms budget = 96% headroom):

| Scenario | Latency | Budget Used |
|----------|---------|-------------|
| SentenceTransformer warm + ChromaDB (200 sigs) | 12-21ms | 4% |
| TF-IDF fallback + JSON (200 sigs) | 4.5-12ms | 2% |
| Cold start (first call, one-time) | 282-556ms | 56-111% |

**Decision:** Keep 500ms budget as-is. Cold start is one-time and tolerable. Warm operation is 25x under budget. Add lazy model loading in `SessionStart` to eliminate cold start from user-facing latency.

---

### RESOLVED: Signature Freshness — Hybrid update strategy with open-source feeds

**Primary seed datasets (both MIT licensed):**

| Dataset | Size | Source | Why |
|---------|------|--------|-----|
| HackAPrompt | 600K+ prompts | EMNLP 2023, 2,800 human participants | Highest diversity, 29 technique taxonomy |
| JailbreakBench | 200 verified attacks | NeurIPS 2024, used by Google Gemini | Highest signal-to-noise, actively maintained |

**Supplementary:** verazuo/jailbreak_llms (1,405 in-the-wild, MIT), deepset/prompt-injections (662 curated, Apache 2.0), Vigil YARA rules.

**Update strategy — 3-tier hybrid:**
1. **Versioned with releases** (primary): Ship curated `signatures/` directory (~2,000-5,000 pre-embedded sigs)
2. **`wfc signatures update`** (optional CLI): Pull latest JailbreakBench artifacts + HuggingFace delta
3. **Self-hardening** (runtime): Store embeddings of detected injections; future similar prompts caught automatically

**Freshness policy:** Emit warning event if signature DB is >30 days old. `manifest.json` tracks version, source URLs, last-updated timestamp.

**Critical finding:** All production firewalls are regularly bypassed (emoji smuggling: 100% bypass rate). WFC must layer regex + embedding + self-hardening. Document that the firewall is probabilistic, not a guarantee.

---

## Adjustments Required Before Proceeding

### Must Address (blocking)

1. ~~**Clarify firewall integration point**~~ **RESOLVED**: `UserPromptSubmit` hook. See above.

2. **Pydantic deferred to Tier 2**: Per human lead decision. Tier 1 uses dict-based validation with retry. WFC's zero-hard-dependency property preserved.

### Should Address (recommended)

3. **Phase Tier 1 into 1a/1b/1c**: AgenticValidator first (quick, high yield), Refusal Agent second (small), Semantic Firewall last (research-heavy). Each sub-phase is independently shippable.

4. ~~**Define signature freshness policy**~~ **RESOLVED**: Hybrid 3-tier strategy. See above.

5. ~~**Set latency budget**~~ **RESOLVED**: 500ms confirmed adequate (12-21ms typical). See above.

### Nice to Have (non-blocking)

6. ~~**Start with TF-IDF for firewall**~~ **REJECTED by human lead**: "Let's be WFC." Full embedding-based approach.

7. **Document limitations**: The semantic firewall is probabilistic. PostToolUse output scanning (indirect injection) is a Tier 2 commitment. Set expectations in architecture docs.

---

## Final Recommendation

**PROCEED.** All three blocking questions are now resolved:
1. Integration point: `UserPromptSubmit` hook (pre-reasoning, no new hook types)
2. Latency: 500ms budget confirmed adequate (12-21ms typical operation)
3. Signatures: MIT-licensed open-source feeds (HackAPrompt + JailbreakBench) with hybrid update strategy

Remaining adjustments (Tier 1a/1b/1c phasing, limitation documentation) are non-blocking and can be addressed during implementation planning.

**Revised Verdict: PROCEED (7.8/10)** — blocking concerns resolved, scope clarified.

**Score Breakdown:**

| Dimension | Original | Revised | Change |
|-----------|----------|---------|--------|
| Need | 9.0 | 9.0 | — |
| Simplicity | 6.5 | 7.0 | Pydantic deferred, integration point clear |
| Scope | 7.5 | 8.0 | UserPromptSubmit = no new hook types |
| Trade-offs | 7.0 | 7.5 | Zero-dep preserved, latency confirmed |
| Failure Modes | 7.0 | 8.0 | Signature freshness strategy defined |
| Blast Radius | 8.5 | 8.5 | — |
| Timeline | 7.0 | 7.5 | Phasing reduces risk |
| **Weighted Average** | **7.4** | **7.8** | **+0.4** |
