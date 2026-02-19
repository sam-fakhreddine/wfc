# Loki Mode Analysis: What WFC Should Adopt

**Date:** 2026-02-17 (revised against Five-Agent Consensus Engine v2.0)
**Source:** [github.com/sam-fakhreddine/loki-mode](https://github.com/sam-fakhreddine/loki-mode) (v5.48.1)
**WFC baseline:** Post-v2.0 rewrite -- 5 fixed reviewers with PROMPT.md/KNOWLEDGE.md, Consensus Score (CS) algorithm, SHA-256 fingerprint deduplication, two-tier RAG retrieval, drift detection, knowledge writer with promotion, emergency bypass with 24h expiry.

---

## Executive Summary

Loki Mode is a multi-agent autonomous system that takes a PRD to a deployed product. It shares DNA with WFC (multi-agent review, knowledge accumulation, progressive disclosure, token awareness) but diverges in philosophy: Loki optimizes for zero-human-intervention autonomy, WFC optimizes for human-in-the-loop quality with mathematical rigor (the CS formula).

WFC's v2.0 rewrite already addresses several ideas that were relevant in the v1 era. The old 56-persona dynamic-selection system has been replaced with 5 fixed reviewers (security, correctness, performance, maintainability, reliability), each with PROMPT.md + KNOWLEDGE.md. The old WeightedConsensus voting has been replaced with the CS algorithm (`CS = 0.5*R_bar + 0.3*R_bar*(k/n) + 0.2*R_max`) plus Minority Protection Rule. The old flat memory has been replaced with two-tier RAG retrieval (global + project-local) with drift detection, auto-append, and promotion.

This analysis identifies **six ideas worth adopting** (down from eight pre-v2.0, since two are now natively solved) and **five ideas to reject**. Each adoption recommendation includes the specific WFC v2.0 file that needs modification and how the idea interacts with the new architecture.

---

## What v2.0 Already Solved

Before listing new adoptions, it's important to acknowledge that the v2.0 rewrite natively addressed two ideas from the original analysis:

### Cross-Session Knowledge (was "Compound Learning")

**v1 gap:** `ReflexionMemory` was session-scoped. Learnings died when the session ended.

**v2.0 solution:** `KnowledgeWriter` (`wfc/scripts/knowledge/knowledge_writer.py`) extracts learnings from review findings and appends them to KNOWLEDGE.md. `promote_to_global()` copies high-value entries from project-local to `~/.wfc/knowledge/global/`. `KnowledgeRetriever` (`wfc/scripts/knowledge/retriever.py`) merges global and project-local knowledge at retrieval time. `DriftDetector` (`wfc/scripts/knowledge/drift_detector.py`) handles staleness, bloat, contradictions, and orphaned references.

**Remaining gap:** Loki's compound learning extracts structured solutions with YAML frontmatter (title, symptoms, root_cause, prevention, confidence). WFC's knowledge writer appends flat text entries. See Adoption #5 below for the remaining delta.

### Finding Deduplication (was partially implicit)

**v2.0 solution:** `Fingerprinter` (`wfc/scripts/skills/review/fingerprint.py`) deduplicates findings across reviewers using SHA-256 fingerprinting with +/-3 line tolerance. The `k` field (reviewer agreement count) feeds directly into the CS formula's agreement bonus term `0.3 * R_bar * (k/n)`.

---

## Ideas to Adopt

### 1. Anti-Sycophancy Devil's Advocate on Zero-Finding Consensus

**Source:** `skills/quality-gates.md` lines 3-4, inspired by CONSENSAGENT (ACL 2025)

**What Loki does:** When all 3 blind reviewers unanimously approve code with zero findings, Loki spawns an additional "Devil's Advocate" reviewer whose explicit job is to find problems. This addresses the well-documented sycophancy bias where LLMs tend to agree with each other.

**Why WFC still needs this despite v2.0:** The CS algorithm handles the case where findings exist -- it scores them, deduplicates them, applies MPR. But it has no defense against the case where **all 5 reviewers return zero findings**. When this happens, CS=0.0, tier="informational", and the review passes trivially. The Minority Protection Rule (MPR) cannot fire because there are no findings with R_max >= 8.5 to protect. This is the exact sycophancy gap: five reviewers independently concluding "looks fine" doesn't mean the code is fine.

**Integration point:** `wfc/scripts/skills/review/orchestrator.py`, in `finalize_review()` after `self.engine.parse_results(task_responses)`. When `len(all_findings) == 0` AND all 5 reviewers returned `score >= 8.0`, trigger a devil's advocate phase:

```python
# In finalize_review(), after collecting all_findings:
if not all_findings and all(r.score >= 8.0 for r in reviewer_results):
    # Spawn 6th reviewer with adversarial prompt
    advocate_task = self._build_devils_advocate_task(request)
    # Return task spec for caller to execute, then re-enter finalize
```

The devil's advocate prompt should receive only the diff (not the other reviews) and be instructed:

```
You are a Devil's Advocate. Five expert reviewers found zero issues in this
code. Your job is to find what they missed. Be adversarial. Look for:
- Assumptions nobody questioned (error paths, null states, concurrency)
- Edge cases that seem unlikely but would be catastrophic
- Subtle coupling or hidden dependencies that will break under change
- Security assumptions that hold today but not under adversarial input

If you find nothing, return []. That is a valid answer. But try hard first.
```

If the devil's advocate finds any finding with severity >= 7.0 and confidence >= 7.0, the review's CS should be recalculated with that finding included -- which will naturally push the tier above "informational."

**Effort:** Low. ~50 lines in `orchestrator.py` + one new prompt template.

**Impact:** High. Closes the zero-finding sycophancy gap that the CS algorithm cannot address by design.

---

### 2. Two-Stage Review: Spec Compliance Gate Before Quality Review

**Source:** `skills/quality-gates.md` lines 360-455, inspired by Superpowers (obra)

**What Loki does:** Review is split into two sequential stages. Stage 1 checks "does this implement what the spec requires?" with a single reviewer that explicitly does NOT evaluate code quality. Stage 2 runs the quality reviewers only if Stage 1 passes. This prevents quality-reviewing code that implements the wrong feature.

**Why WFC still needs this despite v2.0:** WFC's 5 fixed reviewers (security, correctness, performance, maintainability, reliability) all evaluate code quality from their domain perspective. None of them checks: "Does this diff actually implement what the task specification asked for?" The correctness reviewer checks logic, contracts, and edge cases *within the code*, but doesn't compare the code against the original task spec. A perfectly correct, secure, performant implementation of the wrong feature will pass all 5 reviewers.

**Integration point:** `wfc/scripts/skills/review/orchestrator.py`, as a new method `prepare_spec_check()` called before `prepare_review()`:

```python
def prepare_spec_check(self, request: ReviewRequest, task_spec: str) -> dict:
    """Phase 0: Build a spec compliance check task."""
    return {
        "reviewer_id": "spec-compliance",
        "reviewer_name": "Spec Compliance Gate",
        "prompt": self._build_spec_prompt(task_spec, request.files, request.diff_content),
        "temperature": 0.3,
        "relevant": True,
    }
```

The spec compliance reviewer checks:

1. All required features from the spec are present in the diff
2. No scope creep (no features added beyond what was asked)
3. Edge cases mentioned in the spec are handled
4. Tests verify the spec's acceptance criteria

If spec compliance fails, `finalize_review()` returns `ReviewResult(passed=False)` without running the 5-reviewer quality review at all. This saves tokens and prevents the misleading situation where quality review passes on the wrong implementation.

**Effort:** Medium. New reviewer prompt + gate logic in orchestrator + modification to `ReviewRequest` to carry the original task spec.

**Impact:** High. Prevents "wrong feature, great code" -- the one class of bug that domain-specific reviewers cannot catch.

---

### 3. Task-Aware RAG Retrieval Weights

**Source:** `memory/engine.py` lines 28-61, based on arXiv 2512.18746 (MemEvolve)

**What Loki does:** Different task types retrieve different memory types with different weights:

| Task Type | Episodic | Semantic | Skills | Anti-Patterns |
|-----------|----------|----------|--------|---------------|
| Exploration | 0.60 | 0.30 | 0.10 | 0.00 |
| Implementation | 0.15 | 0.50 | 0.35 | 0.00 |
| Debugging | 0.40 | 0.20 | 0.00 | 0.40 |
| Review | 0.30 | 0.50 | 0.00 | 0.20 |
| Refactoring | 0.25 | 0.45 | 0.30 | 0.00 |

MemEvolve found task-aware adaptation improves retrieval performance by 17% over static weights.

**Why WFC still needs this despite v2.0:** WFC's `KnowledgeRetriever` (`wfc/scripts/knowledge/retriever.py`) uses uniform scoring -- `retrieve()` queries both tiers with the same query and ranks by raw similarity score. It doesn't know whether the retrieval is for a security review (where "Incidents Prevented" and "Patterns Found" entries matter most) vs. a correctness review (where "False Positives to Avoid" matters more, to prevent noisy findings).

The KNOWLEDGE.md files already have the right sections: "Patterns Found," "False Positives to Avoid," "Incidents Prevented," "Repository-Specific Rules," "Codebase Context." These are effectively memory types. The retriever just needs to weight them differently per reviewer.

**Integration point:** `wfc/scripts/knowledge/retriever.py`, in `retrieve()`. Add a `reviewer_id`-to-section-weight mapping:

```python
REVIEWER_SECTION_WEIGHTS: dict[str, dict[str, float]] = {
    "security": {
        "Patterns Found": 0.35,
        "Incidents Prevented": 0.30,
        "False Positives to Avoid": 0.20,
        "Repository-Specific Rules": 0.10,
        "Codebase Context": 0.05,
    },
    "correctness": {
        "False Positives to Avoid": 0.35,
        "Patterns Found": 0.30,
        "Codebase Context": 0.20,
        "Repository-Specific Rules": 0.10,
        "Incidents Prevented": 0.05,
    },
    # ... performance, maintainability, reliability
}
```

After retrieval, multiply each result's score by the weight for its source section (detectable from the chunk's `source_section` or header context). This re-ranks results so that security reviewers see incidents and patterns first, while correctness reviewers see false positives first (reducing noise).

**Effort:** Medium. Requires the `KnowledgeChunker` to tag chunks with their source section, then weighted re-ranking in retriever.

**Impact:** Medium-high. Better signal-to-noise ratio per reviewer. Security reviewer gets past incidents, not codebase context. Correctness reviewer gets false positives to avoid, not incident war stories.

---

### 4. Complexity Auto-Detection for Review Depth Scaling

**Source:** `SKILL.md` lines 241-250

**What Loki does:** Auto-detects complexity and scales workflow depth: Simple (1-2 files, lightweight review), Standard (3-10 files, full review), Complex (10+ files, full review + deepen-plan).

**Why WFC needs this:** WFC's reviewer system always runs all 5 reviewers. The `ReviewerLoader` has a relevance gate (`_check_relevance()` in `reviewer_loader.py:217-240`) that skips reviewers whose domain doesn't match changed file extensions -- e.g., the performance reviewer is marked `relevant=False` for markdown-only changes. But there's no tier-level scaling. A 2-line typo fix in a README runs the same 5-reviewer pipeline as a 500-line auth refactor.

**Integration point:** `wfc/scripts/skills/review/orchestrator.py`, in `prepare_review()`. Count files and diff size, then map to a tier:

```python
def _detect_complexity(self, request: ReviewRequest) -> str:
    file_count = len(request.files)
    diff_lines = request.diff_content.count('\n') if request.diff_content else 0
    if file_count <= 2 and diff_lines < 50:
        return "simple"
    if file_count <= 10 and diff_lines < 500:
        return "standard"
    return "complex"
```

Tier effects on the review pipeline:

| Tier | Reviewers Run | Devil's Advocate | Spec Compliance |
|------|--------------|-----------------|-----------------|
| Simple | 2-3 (only relevant) | No | No |
| Standard | All 5 | If zero findings | Optional |
| Complex | All 5 | Always | Required |

For "simple" tier, skip irrelevant reviewers AND reduce the prompt size (no knowledge injection, shorter diff context). For "complex" tier, require spec compliance (Adoption #2) and always run devil's advocate (Adoption #1).

**Effort:** Low-medium. Detection heuristic + conditional logic to control which reviewers run.

**Impact:** Medium. Saves tokens on trivial changes. Adds rigor for complex changes. Better developer experience for small fixes.

---

### 5. Structured Solution Extraction (Compound Learning Delta)

**Source:** `skills/compound-learning.md` lines 1-123

**What Loki does:** After a task passes verification, evaluates whether a novel insight was produced, then extracts a structured solution with YAML frontmatter: title, category, tags, symptoms, root_cause, prevention, confidence.

**Why WFC still has a gap:** WFC's `KnowledgeWriter` appends flat text entries: `- [2026-02-16] Description (Source: initial-seed)`. This is sufficient for RAG retrieval but lacks the structured fields that make cross-project search effective. Loki's structured format enables searching by **symptoms** ("ECONNREFUSED under load" matches a future task that encounters the same symptom) and **root cause** (which clusters solutions by underlying problem, not surface-level description).

**Integration point:** `wfc/scripts/knowledge/knowledge_writer.py`, in `extract_learnings()`. For findings with `severity >= 9.0` (incidents prevented), additionally generate a structured solution file:

```python
def extract_solution(self, finding: dict, reviewer_id: str) -> dict:
    """Extract a structured solution from a high-severity finding."""
    return {
        "title": finding.get("description", "")[:100],
        "category": reviewer_id,  # maps to security, correctness, etc.
        "severity": finding.get("severity", 0.0),
        "root_cause": finding.get("description", ""),
        "prevention": finding.get("remediation", ""),
        "confidence": finding.get("confidence", 0.0) / 10.0,
        "date": date.today().isoformat(),
    }
```

Store structured solutions at `~/.wfc/knowledge/global/solutions/{category}/{slug}.yaml`. The `promote_to_global()` method already handles cross-project knowledge; this extends it with a richer format for high-value findings.

**Effort:** Low-medium. Extends existing `KnowledgeWriter` methods; adds YAML output alongside the existing flat text.

**Impact:** Medium over time. Compounds the value of `promote_to_global()` by making promoted solutions searchable by symptom and root cause, not just text similarity.

---

### 6. Chain-of-Verification (CoVe) for Security/Reliability Findings

**Source:** `skills/quality-gates.md` lines 24-204, based on arXiv 2309.11495

**What Loki does:** For code verification, implements factored execution: the verifier sees only the claim being checked + minimal context (function signature), NOT the original implementation. This prevents the verifier from rationalizing the author's mistakes.

**Why WFC needs this:** WFC's Minority Protection Rule (MPR) in `consensus_score.py:101-122` fires when `R_max >= 8.5` from a security or reliability reviewer. But MPR only amplifies the CS when it fires -- it doesn't independently verify the finding. The security reviewer might flag a false positive with severity 9.5, and MPR will dutifully escalate it. Conversely, the security reviewer might miss a real vulnerability, and MPR has nothing to amplify.

CoVe addresses both problems: when a security or reliability reviewer reports a finding with severity >= 8.0, decompose the finding into a verifiable claim ("This function accepts user input at line 42 and passes it to SQL at line 47 without sanitization") and verify that claim in a separate subagent that sees only the function signature and the claim -- NOT the full implementation and NOT the original reviewer's analysis.

**Integration point:** `wfc/scripts/skills/review/orchestrator.py`, in `finalize_review()`, after fingerprint deduplication and before CS calculation. For any finding where `severity >= 8.0` AND `reviewer_id in ("security", "reliability")`:

1. Extract the claim (description + file + line range)
2. Build a verification task with only the function signature and the claim
3. If the verifier confirms, keep the finding. If the verifier refutes, demote severity to the verifier's assessment.

This integrates cleanly with the existing MPR: verified findings still trigger MPR if `R_max >= 8.5`. But now MPR fires only on verified findings, reducing false escalations while maintaining the safety net for true critical issues.

**Effort:** High. Requires claim extraction, factored prompt construction, subagent dispatch, and result reintegration before CS calculation.

**Impact:** High for critical paths. Reduces false positives on security/reliability (saving developer time on non-issues) while increasing true positive confidence (MPR fires only on verified findings).

---

## Ideas to Reject

### 1. 41 Hardcoded Agent Types Across 7 Swarms

**What Loki does:** Defines 41 agent types (eng-frontend, ops-devops, biz-marketing, etc.) organized into 7 swarms (Engineering, Operations, Business, Data, Product, Growth, Review).

**Why WFC should reject this:** WFC v2.0 deliberately moved in the opposite direction -- from 56 dynamic personas to 5 fixed reviewers. The v2.0 design rationale (`REVIEW_V2.md:173`) states: "5 fixed reviewers (not dynamic selection): Deterministic, debuggable, no selection algorithm overhead." Adding 41 agent types would undo this hard-won simplification.

WFC's 5 fixed reviewers with KNOWLEDGE.md accumulation are more effective than 41 static definitions because they learn. The security reviewer that has seen 100 reviews of your codebase (via KNOWLEDGE.md entries) is better than a generic "eng-security" agent type that starts from zero each time.

Additionally, many of Loki's agent types (biz-marketing, biz-sales, biz-legal, biz-hr, growth-hacker, growth-community) are outside the scope of a code quality tool. WFC is correctly focused on engineering excellence, not business operations.

**Risk of adopting:** Undoes v2.0 simplification. Scope creep. Maintenance burden.

---

### 2. "NEVER Ask, NEVER Wait, NEVER Stop" Autonomy Philosophy

**What Loki does:** Three absolute rules: never ask questions, never wait for confirmation, never stop working. The agent makes all decisions autonomously and keeps improving the codebase perpetually.

**Why WFC should reject this:** WFC's v2.0 architecture deliberately includes human checkpoints: the emergency bypass mechanism (`emergency_bypass.py`) requires a human to provide a reason and identity (`--bypassed-by`). The 24-hour expiry forces periodic human re-evaluation. The append-only audit trail creates accountability. These are features, not limitations.

The "never stop" rule is also fundamentally incompatible with WFC's CS algorithm. The CS formula produces a deterministic score and tier for each review. "Never stop" would mean re-reviewing and re-modifying code indefinitely, which violates the mathematical precision that v2.0 was built to achieve.

**Risk of adopting:** Runaway agents. Security incidents from autonomous deployment. Scope creep. Undermines the emergency bypass audit trail.

---

### 3. `--dangerously-skip-permissions` as a Prerequisite

**What Loki does:** Requires Claude Code to run with all permissions disabled. This is a hard requirement for autonomous operation.

**Why WFC should reject this:** WFC's hook infrastructure (`pretooluse_hook.py`, `security_hook.py`, `rule_engine.py`) provides guardrails that work WITH the permission system. The security hook checks for `eval()`, `os.system()`, `subprocess` with `shell=True`, hardcoded secrets, and `rm -rf` on system paths. These checks run on every tool use. Disabling permissions disables this entire safety layer.

The v2.0 architecture reinforces this: the security reviewer's KNOWLEDGE.md (`wfc/reviewers/security/KNOWLEDGE.md`) documents that "security_hook.py silently passes on any internal exception (returns {}) to avoid blocking user workflow -- this fail-open behavior is intentional." The hooks were designed to be non-blocking but present. Removing them entirely is a different (and worse) tradeoff.

**Risk of adopting:** Disables WFC's hook-based security enforcement. Accidental destructive operations. Loss of the guardrail infrastructure.

---

### 4. Enterprise Feature Sprawl (Dashboard/OIDC/RBAC/SIEM/Prometheus) -- PARTIALLY REVISITED

**What Loki does:** Includes TLS/HTTPS encryption, OIDC/SSO integration, 4-tier RBAC, Prometheus metrics export, syslog forwarding for SIEM, SHA-256 audit trail integrity chains, and OpenClaw multi-agent coordination protocol.

**Original rejection:** Adding Prometheus, OIDC, and SIEM to a code review tool dilutes WFC's focus. Each core module does one thing well; enterprise features don't belong in the core.

**Revised position:** The rejection of enterprise features *in core* stands. However, Dashboard + Observability are being planned as **plugins** via a plugin system that keeps core untouched. The key principle: WFC **exposes** metrics and structured data; existing infrastructure (Prometheus, Grafana, SIEM) **consumes** them. OIDC/RBAC remain rejected until WFC becomes a multi-user service.

See: [ROADMAP-DASHBOARD-OBSERVABILITY.md](ROADMAP-DASHBOARD-OBSERVABILITY.md) for the full plugin-based roadmap.

**Risk of the original approach (rejected):** Feature bloat. Maintenance burden. Distraction from core value.
**Risk of the plugin approach (accepted):** Plugin system is new infrastructure; must ensure core never depends on plugins.

---

### 5. Perpetual Improvement Mode

**What Loki does:** After completing the PRD, enters an endless improvement loop: optimizing performance, adding test coverage, improving documentation, refactoring code smells, updating dependencies.

**Why WFC should reject this:** WFC v2.0 has clear stopping points built into the architecture. `finalize_review()` returns a `ReviewResult` with `passed: bool`. The CS algorithm produces a deterministic score. The emergency bypass has a 24-hour expiry. These are all boundaries -- they define when a task is done.

Perpetual improvement is also incompatible with the knowledge system. `DriftDetector` checks for staleness (entries older than 90 days), bloat (files with >50 entries), and orphaned references. An agent that "never stops improving" would constantly generate new knowledge entries, trigger bloat detection, and create a self-defeating cycle.

**Risk of adopting:** Scope creep. Bloated KNOWLEDGE.md files. Token/cost waste. Difficulty attributing regressions.

---

## Implementation Priority Matrix

| Priority | Idea | Effort | Impact | v2.0 Integration Point | Dependencies |
|----------|------|--------|--------|------------------------|--------------|
| P0 | Devil's advocate on zero findings | Low | High | `orchestrator.py:finalize_review()` | None |
| P1 | Spec compliance gate | Medium | High | `orchestrator.py` (new Phase 0) | Needs `task_spec` on `ReviewRequest` |
| P1 | Task-aware RAG weights | Medium | Medium-High | `retriever.py:retrieve()` + chunker section tags | None |
| P2 | Complexity auto-detection | Low-Medium | Medium | `orchestrator.py:prepare_review()` | Adoptions #1, #2 (for tier-conditional logic) |
| P2 | Structured solution extraction | Low-Medium | Medium (compounds) | `knowledge_writer.py:extract_learnings()` | None |
| P3 | Chain-of-Verification (CoVe) | High | High (critical paths) | `orchestrator.py:finalize_review()` before CS | None (but benefits from #1 for non-critical paths) |

**Recommended sequencing:** P0 first (quick win, ~50 lines). Then P1 in parallel (spec compliance and RAG weights are independent). Then P2 (complexity detection uses #1 and #2 conditionally). P3 last (CoVe is high-effort and only needed for critical paths).

**Token budget impact:** Adoptions #1 and #6 add subagent calls (devil's advocate and CoVe verifier). Adoption #4 reduces token usage for simple reviews. Net effect depends on the distribution of simple vs. complex reviews in practice.

---

## Appendix A: v2.0 Architecture Components Referenced

| Component | File | Role in Analysis |
|-----------|------|-----------------|
| `ReviewOrchestrator` | `wfc/scripts/skills/review/orchestrator.py` | Primary integration point for adoptions #1, #2, #4, #6 |
| `ConsensusScore` | `wfc/scripts/skills/review/consensus_score.py` | CS formula, MPR, tier classification |
| `Fingerprinter` | `wfc/scripts/skills/review/fingerprint.py` | SHA-256 dedup, already addresses Loki's dedup |
| `ReviewerEngine` | `wfc/scripts/skills/review/reviewer_engine.py` | Two-phase prepare/parse, 5 fixed reviewers |
| `ReviewerLoader` | `wfc/scripts/skills/review/reviewer_loader.py` | Relevance gate, temperature parsing |
| `KnowledgeRetriever` | `wfc/scripts/knowledge/retriever.py` | Two-tier RAG, integration point for #3 |
| `KnowledgeWriter` | `wfc/scripts/knowledge/knowledge_writer.py` | Auto-append + promotion, integration point for #5 |
| `DriftDetector` | `wfc/scripts/knowledge/drift_detector.py` | Staleness/bloat/contradiction/orphan checks |
| `EmergencyBypass` | `wfc/scripts/skills/review/emergency_bypass.py` | 24h expiry, audit trail |
| `REVIEW_V2.md` | `docs/architecture/REVIEW_V2.md` | Design rationale for v2.0 decisions |

## Appendix B: Loki Mode Source Files Reviewed

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

## Appendix C: What Changed From the Pre-v2.0 Analysis

| Original Idea | Status | Reason |
|---------------|--------|--------|
| Anti-sycophancy devil's advocate | **Kept, refined** | Now targets zero-finding gap in CS algorithm specifically |
| Task-aware memory retrieval | **Kept, refined** | Now maps to KNOWLEDGE.md section weights in `KnowledgeRetriever` |
| Two-stage spec compliance review | **Kept** | Still not addressed by v2.0's domain reviewers |
| Complexity auto-detection | **Kept, refined** | Now integrates with `ReviewerLoader` relevance gate |
| Compound learning | **Partially solved, delta kept** | `KnowledgeWriter` + promotion solves 70%; structured YAML is the remaining 30% |
| RARV wrapper | **Dropped** | v2.0's two-phase orchestrator (prepare/finalize) with knowledge injection covers the REASON phase; DriftDetector covers the REFLECT phase; the remaining value (failure escalation ladder) is too Loki-specific |
| File-based event bus | **Dropped** | WFC's hook system + the new orchestrator's two-phase design reduces the need; adding a full event bus is infrastructure without a current consumer |
| Chain-of-Verification (CoVe) | **Kept, refined** | Now specifically targets MPR-eligible findings (R_max >= 8.0 from security/reliability) to verify before CS amplification |
| Reject: 41 agent types | **Kept** | Strengthened by v2.0's deliberate move to 5 fixed reviewers |
| Reject: Never ask/wait/stop | **Kept** | Strengthened by v2.0's emergency bypass and deterministic CS |
| Reject: Skip permissions | **Kept** | Unchanged |
| Reject: Enterprise sprawl | **Kept** | Strengthened by v2.0's focused module design |
| Reject: Perpetual improvement | **Kept** | Strengthened by DriftDetector's bloat detection |
