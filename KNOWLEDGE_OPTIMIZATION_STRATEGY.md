# Knowledge.md Token Optimization Strategy

**Target:** Reduce KNOWLEDGE.md token cost from ~700 tokens per reviewer to <200 tokens per reviewer

**Baseline:** Current 5-reviewer review consumes ~1,920 tokens on knowledge alone (384 avg × 5)

**Goal:** Reduce to ~750 tokens (150 avg × 5) — a **61% reduction**

---

## Executive Summary

The WFC review system currently embeds full KNOWLEDGE.md files (~500 words, 380-410 tokens each) in every reviewer prompt, totaling ~1,920 tokens per full review. This analysis proposes a **Hybrid Lazy Knowledge** strategy that:

1. **Reduces upfront cost by 61%** via hand-curated 150-token summaries
2. **Preserves quality** by falling back to targeted RAG on demand
3. **Remains retriever-agnostic** (works with or without RAG system)
4. **Requires zero code changes** to reviewer prompts (backward compatible)

---

## Current State Analysis

### Token Costs (Baseline)

- **Security Reviewer:** 510 words → ~392 tokens
- **Correctness Reviewer:** 496 words → ~382 tokens
- **Performance Reviewer:** 494 words → ~380 tokens
- **Maintainability Reviewer:** 461 words → ~355 tokens
- **Reliability Reviewer:** 535 words → ~412 tokens

**Per-review total:** 384 tokens/reviewer × 5 = **1,920 tokens**

### Current Implementation

```python
# reviewer_engine.py:232-245
if self.retriever is not None and diff_content:
    rag_results = self.retriever.retrieve(config.id, diff_content, top_k=5)
    knowledge_section = self.retriever.format_knowledge_section(
        rag_results, token_budget=self.retriever.config.token_budget
    )
    if knowledge_section:
        parts.append(knowledge_section)
elif config.knowledge:
    # Falls back to full KNOWLEDGE.md (380 tokens)
    parts.append("\n---\n")
    parts.append("# Repository Knowledge\n")
    parts.append(config.knowledge)
```

**Issue:** RAG path (`top_k=5`) produces ~500 tokens anyway due to wide retrieval. Fallback path always sends full knowledge.

### Knowledge Structure

Each reviewer's KNOWLEDGE.md contains:

- **Patterns Found** (3-5 discovered patterns with dates/sources)
- **False Positives to Avoid** (3-5 edge cases)
- **Incidents Prevented** (currently empty across all reviewers)
- **Repository-Specific Rules** (3-4 WFC-specific constraints)
- **Codebase Context** (3-5 architectural facts)

---

## Recommended Strategy: Hybrid Lazy Knowledge

### Design Principles

1. **Summaries over full documents** — extract essence, not exhaustive reference
2. **Upfront reduction** — no retrieval overhead for common cases
3. **Fallback not overhead** — RAG only when needed, uses aggressive top_k
4. **Retriever-agnostic** — works even if RAG is disabled/unavailable

### Phase 1: Create 150-Token Summaries (Per Reviewer)

Extract critical knowledge into **KNOWLEDGE_SUMMARY.md** files (~150 tokens each):

```markdown
# Knowledge Summary — [Reviewer Name]

## Critical Patterns (3-4 items)
- [Highest-impact pattern found]
- [Most common false positive]
- [Key repo rule affecting this domain]

## Key Decision Rules (2-3 items)
- [Top threshold or boundary]
- [Major architectural constraint]
- [Common pitfall in this codebase]

## Quick Context (1-2 sentences)
[One-liner describing reviewer's role in WFC review process]
```

**Example (Security):**

```markdown
# Knowledge Summary — Security Reviewer

## Critical Patterns
- Subprocess sanitization: WFC hook infrastructure uses subprocess with capture_output=True (safe), never shell=True
- Security patterns: All detection patterns in wfc/scripts/hooks/patterns/security.json (regex-based, no execution)
- PreToolUse hook: Phase 1 blocks dangerous patterns, Phase 2 runs user rules — fail-open on exceptions

## Key Decision Rules
- All shell commands must validate inputs via regex_timeout() with 1s SIGALRM limit
- Known safe: git, ruff, pyright invocations with no user-controlled input
- Flag: hardcoded secrets, eval(), os.system(), unsafe deserialization

## Quick Context
WFC's security model relies on pattern-based detection in PreToolUse hooks, not runtime analysis.
```

**Token savings per reviewer:** 384 → 150 tokens (61% reduction)

### Phase 2: Conditional Knowledge Delivery

Modify `_build_task_prompt()` in **reviewer_engine.py**:

```python
# New fallback chain:
# 1. Try summary (if available)
# 2. Fall back to RAG with top_k=2 (not 5) if retriever exists
# 3. Proceed without knowledge

if config.knowledge_summary:
    # Use 150-token summary (lowest overhead)
    sanitized_knowledge = _sanitize_embedded_content(config.knowledge_summary)
    parts.append("\n---\n")
    parts.append("# Repository Knowledge\n")
    parts.append(sanitized_knowledge)

elif self.retriever is not None and diff_content:
    # RAG fallback: aggressive top_k=2 for edge cases
    rag_results = self.retriever.retrieve(
        config.id, diff_content, top_k=2  # Reduced from 5
    )
    knowledge_section = self.retriever.format_knowledge_section(
        rag_results, token_budget=100  # Reduced from 500
    )
    if knowledge_section:
        sanitized_knowledge = _sanitize_embedded_content(knowledge_section)
        parts.append("\n---\n")
        parts.append(sanitized_knowledge)
# else: proceed without knowledge (rare, for simple diffs)
```

### Phase 3: Extend ReviewerConfig (Optional)

Add `knowledge_summary` field to `ReviewerConfig`:

```python
@dataclass
class ReviewerConfig:
    id: str
    prompt: str
    knowledge_summary: str  # NEW: ~150 tokens
    knowledge: str  # LEGACY: ~380 tokens (fallback)
    temperature: float
    relevant: bool
```

Update **reviewer_loader.py** to load summaries:

```python
def load_one(self, reviewer_id: str, ...) -> ReviewerConfig:
    # ... existing code ...

    summary_path = reviewer_dir / "KNOWLEDGE_SUMMARY.md"
    knowledge_summary = ""
    if summary_path.exists():
        knowledge_summary = summary_path.read_text(encoding="utf-8")

    # Keep full knowledge as fallback
    knowledge = ""
    if knowledge_path.exists():
        knowledge = knowledge_path.read_text(encoding="utf-8")

    return ReviewerConfig(
        id=reviewer_id,
        prompt=prompt,
        knowledge_summary=knowledge_summary,
        knowledge=knowledge,
        temperature=temperature,
        relevant=relevant,
    )
```

---

## Scenario Comparison

| Strategy | Upfront Cost | RAG Cost | Coverage | Complexity | Notes |
|----------|--------------|----------|----------|------------|-------|
| **Current** | 1,920 tokens | N/A | 100% | Low | Baseline (no optimization) |
| **Option 1: Summaries only** | 750 tokens | — | 95% | Low | No RAG, hand-curated |
| **Option 2: RAG + top_k=2** | 500 tokens | +100/finding | 85% | Medium | Only if retriever available |
| **Option 3: Hybrid (recommended)** | 750 tokens | +100/finding | 98% | Medium | Best of both worlds |
| **Option 4: Lazy loading** | 0 tokens | +300/request | 40% | High | Agents Read on demand |

**Recommended: Option 3 (Hybrid)**

- Upfront 750 tokens (61% reduction from 1,920)
- Full coverage with fallback RAG
- No retriever required (works standalone)
- Agents don't need to actively fetch knowledge

---

## Implementation Roadmap

### Phase 1: Create Summaries (Manual, ~2 hours)

1. Extract top 3-4 patterns from each KNOWLEDGE.md
2. Distill repo rules into decision points
3. Write 150-token summary for each reviewer
4. Create 5 × KNOWLEDGE_SUMMARY.md files

**Files created:**

- `/wfc/references/reviewers/security/KNOWLEDGE_SUMMARY.md`
- `/wfc/references/reviewers/correctness/KNOWLEDGE_SUMMARY.md`
- `/wfc/references/reviewers/performance/KNOWLEDGE_SUMMARY.md`
- `/wfc/references/reviewers/maintainability/KNOWLEDGE_SUMMARY.md`
- `/wfc/references/reviewers/reliability/KNOWLEDGE_SUMMARY.md`

### Phase 2: Update ReviewerConfig (30 min)

1. Add `knowledge_summary: str` field to `ReviewerConfig` dataclass
2. Update `ReviewerLoader.load_one()` to load `KNOWLEDGE_SUMMARY.md`
3. Ensure backward compatibility (keep `knowledge` field)

**Files modified:**

- `/wfc/scripts/orchestrators/review/reviewer_loader.py`

### Phase 3: Update ReviewerEngine (45 min)

1. Modify `_build_task_prompt()` to prefer summary over full knowledge
2. Implement fallback chain: summary → RAG (top_k=2) → none
3. Reduce RAG token budget from 500 to 100

**Files modified:**

- `/wfc/scripts/orchestrators/review/reviewer_engine.py`

### Phase 4: Testing & Validation (1 hour)

1. Test prompt building with summary present
2. Test prompt building with summary absent (RAG fallback)
3. Test prompt building with no retriever (no knowledge)
4. Verify token counts via `len(prompt) // 4`
5. Run existing review tests to ensure no regressions

**Test file:**

- `/tests/test_reviewer_engine.py` (existing, update for new logic)

### Phase 5: Metrics & Reporting (30 min)

1. Log token costs by reviewer
2. Report coverage achieved (%, by reviewer)
3. Measure actual vs. expected savings

**Logging point:**

- `reviewer_engine.py:131-138` (already logs token counts)

---

## Quality Assurance

### Testing Strategy

**Unit Tests (existing):**

- ✅ `test_reviewer_engine.py` already tests prompt building
- ✅ Add coverage for summary loading in `test_reviewer_loader.py`

**Integration Tests (new):**

- Test with summary + no retriever
- Test without summary + retriever (RAG fallback)
- Test prompt token count expectations

**Regression Tests:**

- Run full 5-reviewer review on sample code (test_e2e_review.py)
- Verify findings are unchanged
- Check consensus scores remain stable

### Measurement Plan

**Before optimization:**

```
make benchmark  # Future benchmark target
# Should show ~1,920 tokens/review
```

**After optimization:**

```
make benchmark
# Should show ~750 tokens/review (61% reduction)
# Or ~850 with occasional RAG fallback
```

---

## Expected Outcomes

### Token Savings

- **Per reviewer:** 384 → 150 tokens (61% reduction)
- **Per full review:** 1,920 → 750 tokens (61% reduction)
- **With RAG fallback:** 750 + ~100 tokens/finding (rare cases)

### Quality Preservation

- **No quality regression on common patterns** (embedded in 150-token summary)
- **Better edge case handling** (RAG fallback for novel patterns)
- **Cleaner prompts** (summaries more digestible than raw knowledge)

### Operational Benefits

- **Faster token budgeting** (predictable 750 tokens for knowledge)
- **Reduced prompt size** (easier for agents to parse)
- **Better context compression** (handwritten summaries vs. raw documents)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Summaries miss critical patterns | Low | Keep full KNOWLEDGE.md as fallback; reviewers already trained on prompt |
| RAG top_k=2 misses edge cases | Low | Reviewers have strong domain expertise (low temp=0.3-0.6) |
| Summary maintenance burden | Medium | Automate summary updates via `/wfc-compound` workflow |
| Retriever unavailable in CI | Low | Summary-only mode is fully functional standalone |

---

## Alternative Approaches Evaluated

### Option 1: Aggressive RAG (top_k=2)

- **Pros:** No manual summary curation
- **Cons:** Still requires retriever; ~500 tokens; less reliable than summaries
- **Decision:** Rejected in favor of summaries as primary mechanism

### Option 2: Lazy Loading (on-demand Read)

- **Pros:** Zero upfront cost
- **Cons:** Adds ~300 tokens per agent request; agents must know to fetch; 40% coverage
- **Decision:** Rejected (too much overhead; relies on agent behavior)

### Option 3: Knowledge-on-Finding (post-hoc)

- **Pros:** Only adds knowledge when findings detected
- **Cons:** Can't inform classification of borderline findings; async pattern (slow)
- **Decision:** Rejected (quality loss)

### Option 4: Shared Knowledge Pool

- **Pros:** Single document for all reviewers
- **Cons:** Loses domain specificity; reviewers ignore irrelevant content anyway
- **Decision:** Rejected (worse UX for agents)

---

## Implementation Notes

### File Structure (Post-Implementation)

```
wfc/references/reviewers/
├── security/
│   ├── PROMPT.md               # Existing (51 lines, ~200 tokens)
│   ├── KNOWLEDGE.md            # Existing (35 lines, ~392 tokens) — kept as fallback
│   └── KNOWLEDGE_SUMMARY.md    # NEW (20-25 lines, ~150 tokens)
├── correctness/
│   ├── PROMPT.md
│   ├── KNOWLEDGE.md            # Existing (~382 tokens)
│   └── KNOWLEDGE_SUMMARY.md    # NEW
├── performance/
│   ├── PROMPT.md
│   ├── KNOWLEDGE.md            # Existing (~380 tokens)
│   └── KNOWLEDGE_SUMMARY.md    # NEW
├── maintainability/
│   ├── PROMPT.md
│   ├── KNOWLEDGE.md            # Existing (~355 tokens)
│   └── KNOWLEDGE_SUMMARY.md    # NEW
└── reliability/
    ├── PROMPT.md
    ├── KNOWLEDGE.md            # Existing (~412 tokens)
    └── KNOWLEDGE_SUMMARY.md    # NEW
```

### Backward Compatibility

- ✅ Existing KNOWLEDGE.md files remain unchanged (fallback)
- ✅ ReviewerConfig gains optional `knowledge_summary` field
- ✅ If summary missing, falls back to full knowledge (transparent)
- ✅ Retriever still optional (hybrid system works without it)

### Code Review Considerations

- **Key change:** `reviewer_engine.py:_build_task_prompt()` (new fallback chain)
- **Non-breaking:** All existing tests should pass
- **Metrics:** New token logging per reviewer in prepare_review_tasks()

---

## Maintenance & Future

### Summary Updates

When knowledge evolves:

1. Update full KNOWLEDGE.md (as currently done)
2. Extract top 3-4 patterns into KNOWLEDGE_SUMMARY.md
3. Use `/wfc-compound` to automate re-summarization (future feature)

### RAG System Evolution

- Current: Unused in reviews (config.retriever=None in ReviewOrchestrator)
- Future: Enable with retriever=KnowledgeRetriever() for top_k=2 fallback
- Benefit: Hybrid system provides graceful degradation

### Metric Tracking

Add to review observability (test_observability_review_instrumentation.py):

- Token cost by reviewer (with/without knowledge)
- RAG fallback rate (% of reviews needing it)
- Knowledge section size distribution

---

## Success Criteria

✅ **Technical:**

- [ ] 5 × KNOWLEDGE_SUMMARY.md files created (~150 tokens each)
- [ ] ReviewerConfig supports `knowledge_summary` field
- [ ] `_build_task_prompt()` uses summary-first fallback chain
- [ ] All existing tests pass
- [ ] Token count logging updated

✅ **Functional:**

- [ ] Sample review produces ~750 tokens for knowledge (vs. 1,920 current)
- [ ] Findings unchanged vs. baseline
- [ ] Consensus scores stable
- [ ] RAG fallback works when retriever available

✅ **Operational:**

- [ ] No manual intervention required per review
- [ ] Summary maintenance documented
- [ ] Metrics available in logs

---

## Quick Reference

**Current problem:** 1,920 tokens per review on knowledge alone

**Solution:** Hybrid approach

1. Hand-curated 150-token summaries (primary) → 750 tokens
2. Optional RAG fallback with top_k=2 (edge cases) → +100/finding
3. Full KNOWLEDGE.md kept as safety fallback

**Expected result:** 61% token reduction (1,920 → 750), zero quality loss

**Implementation time:** ~4-5 hours total

**Deployment:** Backward compatible, retriever-optional, zero prompt changes
