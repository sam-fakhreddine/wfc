# Validation Analysis

## Subject: AST Metrics Integration for WFC Review

## Verdict: 🟡 PROCEED WITH ADJUSTMENTS

## Overall Score: 8.3/10

---

## Executive Summary

Overall, this approach shows **15 clear strengths** and **10 areas for consideration**.

The strongest aspects are: **Necessity (9/10)**, **Risk (9/10)**, **Anti-patterns (8.5/10)**, **Simplicity (8.5/10)**.

Key considerations: Add observability task, Two-phase rollout recommended, Reviewer prompt iteration may extend timeline, Monitor for over-reliance on metrics.

With an overall score of **8.3/10**, this is a solid approach that can move forward with attention to the identified concerns.

---

## Dimension Analysis

### 1. Do We Even Need This? — Score: 9/10

**Strengths:**

- **Proven value**: 97% token reduction (8000 → 200 tokens) is measured, not hypothetical
- **Real pain point**: Reviewers currently lack structured context about code complexity and hotspots
- **Working prototype**: Already demonstrates feasibility and value on actual WFC codebase
- **Performance validated**: <100ms overhead measured on 311 files confirms negligible impact

**Concerns:**

- Current reviewer system already works (5 reviewers produce consensus scores without AST metrics)
- No evidence presented that review quality is currently *suffering* without this

**Recommendation:** Strong necessity — the 97% token reduction alone justifies this, especially given WFC's token-aware philosophy.

---

### 2. Is This the Simplest Approach? — Score: 8.5/10

**Strengths:**

- **Built-in stdlib**: Uses Python's `ast` module, not external dependencies (tree-sitter)
- **Shared cache**: Single `.ast-context.json` file vs. per-reviewer parsing
- **Fail-open**: Errors don't break workflows
- **Defer complexity**: Python-only first, not attempting multi-language immediately

**Concerns:**

- Could be even simpler: why not just pass cyclomatic complexity to reviewers as a single number?
- Shared JSON file introduces file I/O coordination (could use in-memory passing instead)

**Recommendation:** Very simple for what it accomplishes, though marginal simplifications exist.

---

### 3. Is the Scope Right? — Score: 7.5/10

**Strengths:**

- **6 tasks**: Well-decomposed, clear boundaries
- **Python-only**: Correctly defers multi-language complexity
- **Production + tests + docs**: Complete implementation, not just feature code
- **Validation pipeline**: Includes quality gates

**Concerns:**

- **Missing: reviewer feedback loop**: No task for iterating on prompt changes based on actual review quality
- **Missing: observability**: No logging/metrics for tracking adoption or impact
- **Slightly large**: Could split into two phases: (1) core functionality, (2) reviewer integration

**Recommendation:** Scope is 85% right — add observability task, consider two-phase rollout.

---

### 4. What Are We Trading Off? — Score: 8/10

**Strengths:**

- **Clear cost/benefit**: 97% token savings vs. new module maintenance is strong ROI
- **Bounded complexity**: <100ms overhead is a hard constraint
- **Measurable metrics**: Formal properties (complexity, nesting) are objective
- **Non-blocking**: Fail-open design means low risk of introducing friction

**Concerns:**

- **Maintenance burden**: Every new Python version could break `ast` compatibility
- **Over-reliance risk**: Reviewers might defer judgment to metrics ("complexity is 15, must be bad")
- **Opportunity cost**: Could this effort improve reviewer prompts instead (higher leverage)?

**Recommendation:** Trade-offs are acceptable given token savings, but monitor reviewer behavior for over-reliance.

---

### 5. Have We Seen This Fail Before? — Score: 8.5/10

**Strengths:**

- **Fail-open design**: Avoids "linter blocks PR" anti-pattern
- **Metrics as hints**: Explicit disclaimers prevent "cargo cult metrics"
- **Performance budget**: <100ms prevents "death by 1000 cuts" overhead accumulation
- **Python-only scope**: Avoids "multi-language parser hell"

**Concerns:**

- **Novelty factor**: AST metrics in LLM review prompts is relatively unexplored — could reviewers hallucinate more?
- **JSON schema drift**: Shared cache file could become a versioning/compatibility headache over time

**Recommendation:** Anti-patterns are well-addressed, but watch for unexpected LLM behavior when interpreting metrics.

**Warnings:**

- Monitor for reviewers inventing false correlations (e.g., "complexity 12 always means bug")
- Validate that disclaimers prevent over-reliance (might need stronger framing)
- Plan for cache schema evolution (versioning strategy)

---

### 6. What's the Blast Radius? — Score: 9/10

**Strengths:**

- **Limited blast radius**: AST errors → skip metrics, review continues (doesn't break workflows)
- **Observable failures**: Performance regression would be immediately visible in review duration
- **Testable integration**: 12 tests + 6 properties + integration tests catch issues early
- **Rollback path**: Can disable AST phase with single flag or revert commit

**Concerns:**

- **Silent degradation**: If AST parsing silently fails often, reviewers lose context without knowing
- **Cache corruption**: Malformed JSON could cause cascading failures (though try/except should catch)

**Recommendation:** Risk is very low — fail-open design contains blast radius effectively.

---

### 7. Is the Timeline Realistic? — Score: 8/10

**Strengths:**

- **Working prototype**: Already 50% done (extractor exists, benchmarked)
- **Clear integration point**: `orchestrator.py` pre-phase is well-defined
- **Test strategy**: 12 tests + 6 properties is concrete and achievable
- **Performance proven**: <100ms budget already validated

**Concerns:**

- **Reviewer prompt iteration**: Might need 2-3 rounds of tuning based on real review quality
- **Unknown unknowns**: Git worktrees, submodules, edge cases could surface during integration
- **~1 week estimate**: Feasible for core work, but prompt tuning + validation might extend to 1.5 weeks

**Recommendation:** Timeline is realistic for 90% of work, but pad for prompt iteration and edge cases.

**Risks:**

- Reviewer prompts might need significant rewording (not just appending metrics)
- Cache file format might need adjustments after real-world usage
- Integration with hook system (PreToolUse) might reveal unexpected dependencies

---

## Simpler Alternatives

Though the score is 8.3/10 (solid), here are simpler approaches if the team wants to de-risk:

1. **Just McCabe complexity**: Extract only cyclomatic complexity score per file, skip dangerous calls/nesting/LoC. Simpler extractor, simpler prompts, 90% of token savings.

2. **In-memory only, no cache**: Parse AST once in orchestrator, pass dict to reviewers, skip `.ast-context.json` file entirely. Eliminates file I/O coordination and cache corruption risk.

3. **Single reviewer experiment**: Apply AST metrics to Security reviewer only (highest value for dangerous calls). Validate impact before rolling out to all 5 reviewers. Smaller blast radius, faster iteration.

---

## Final Recommendation

**Proceed with implementation**, but make these adjustments:

1. **Add observability task (TASK-007)**: Log AST metrics usage (parsing time, cache hits, error rate) to track impact and identify silent failures
2. **Two-phase rollout**: Phase 1 (TASK-001 through TASK-003: core AST extraction + tests), Phase 2 (TASK-004 through TASK-006: reviewer integration + prompt tuning + docs)
3. **Stronger disclaimers**: Frame metrics as "starting points for investigation" not "authoritative judgments"
4. **Pad timeline**: Budget 1.5 weeks instead of 1 week to account for prompt iteration and edge case handling

The **97% token reduction** and working prototype provide strong evidence of value. The fail-open design and limited scope minimize risk. Primary concerns are reviewer over-reliance (addressable via prompt framing) and timeline padding for prompt tuning.

---

## Must-Do Recommendations

1. **Add TASK-007: Observability & Monitoring**
   - Add logging to `cache_writer.py`: track parsing time, success/failure rate, file count
   - Add telemetry to orchestrator: track AST phase duration, cache file size
   - Log to `.wfc-review/ast-analysis.log` for debugging

2. **Update TASK-003 acceptance criteria**
   - Add: "Logs warning if >10% of files fail to parse (potential systemic issue)"
   - Add: "Telemetry includes cache_file_size_bytes for monitoring growth"

3. **Update TASK-004 with stronger framing**
   - Change disclaimer from "supplemental hints" to "starting points for investigation"
   - Add: "High complexity doesn't mean bad code — investigate context before concluding"
   - Add: "Metrics may miss domain-specific considerations — apply your expertise"

---

## Should-Do Recommendations

1. **Split into two phases** (low effort)
   - Phase 1: TASK-001, TASK-002, TASK-003, TASK-005 (core functionality + tests)
   - Phase 2: TASK-004, TASK-006 (reviewer integration + docs)
   - Allows testing AST extraction independently before reviewer integration

2. **Add cache schema versioning** (medium effort)
   - Include `"schema_version": "1.0"` in `.ast-context.json`
   - Allows future schema evolution without breaking existing reviewers

3. **Pad timeline to 1.5 weeks** (low effort)
   - Account for reviewer prompt iteration (2-3 rounds likely)
   - Buffer for git edge cases (submodules, worktrees, sparse checkouts)

---

## Deferred Recommendations

1. **Multi-language support** (high effort, deferred correctly)
   - Current plan correctly defers to future work
   - Validate value with Python-only first

2. **Call graph analysis** (high effort, not critical)
   - "What calls this function" is valuable but adds complexity
   - Defer until AST metrics prove valuable

3. **In-memory cache instead of file** (medium effort, marginal benefit)
   - Current file-based cache is simple and debuggable
   - In-memory would be faster but harder to inspect

---

## Score Breakdown

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Necessity | 9/10 | 2x | 18 |
| Simplicity | 8.5/10 | 2x | 17 |
| Scope | 7.5/10 | 1x | 7.5 |
| Trade-offs | 8/10 | 1x | 8 |
| Anti-patterns | 8.5/10 | 1x | 8.5 |
| Risk | 9/10 | 1x | 9 |
| Feasibility | 8/10 | 1x | 8 |
| **Total** | | | **76/9 = 8.3** |

**Verdict: 🟡 PROCEED WITH ADJUSTMENTS**
