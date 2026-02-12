# WFC-BUILD FORMAL PROPERTIES

**PROJECT:** wfc-build - Streamlined Feature Builder
**GENERATED:** 2026-02-12

---

## PROPERTY CLASSIFICATION

| TYPE        | COUNT | PRIORITY DISTRIBUTION           |
|:------------|------:|:--------------------------------|
| SAFETY      |     3 | CRITICAL: 3                     |
| LIVENESS    |     2 | HIGH: 2                         |
| INVARIANT   |     2 | HIGH: 1, MEDIUM: 1              |
| PERFORMANCE |     2 | MEDIUM: 2                       |
| **TOTAL**   | **9** |                                 |

---

## SAFETY PROPERTIES

### PROP-001: NEVER bypass quality gates

**TYPE:** SAFETY
**PRIORITY:** CRITICAL
**STATEMENT:** Even "quick builds" must pass all quality checks (formatting, linting, tests)
**RATIONALE:** Quality cannot be compromised for speed
**OBSERVABLES:** `quality_gate_bypassed` (must be 0)

---

### PROP-002: NEVER skip consensus review

**TYPE:** SAFETY
**PRIORITY:** CRITICAL
**STATEMENT:** All code must go through multi-agent consensus review
**RATIONALE:** Review catches errors before merge
**OBSERVABLES:** `review_skipped` (must be 0)

---

### PROP-003: NEVER auto-push to remote

**TYPE:** SAFETY
**PRIORITY:** CRITICAL
**STATEMENT:** Merge to local main only, user pushes manually
**RATIONALE:** Respects WFC git safety policy
**OBSERVABLES:** `git_push_attempted` (must be 0)

---

## LIVENESS PROPERTIES

### PROP-004: ALWAYS complete or fail gracefully

**TYPE:** LIVENESS
**PRIORITY:** HIGH
**STATEMENT:** Workflow must complete or fail with actionable feedback
**RATIONALE:** No hanging state
**OBSERVABLES:** `workflow_incomplete` (should be 0)

---

### PROP-005: ALWAYS provide actionable feedback

**TYPE:** LIVENESS
**PRIORITY:** HIGH
**STATEMENT:** Failures include why and how to fix
**RATIONALE:** User can take next steps
**OBSERVABLES:** `feedback_quality_score`

---

## INVARIANT PROPERTIES

### PROP-006: Interview responses determine complexity

**TYPE:** INVARIANT
**PRIORITY:** HIGH
**STATEMENT:** Complexity (S/M/L/XL) is deterministic function of answers
**RATIONALE:** Automatic resource allocation
**MAPPING:**
- S (1 agent): Single file, <50 LOC
- M (1-2 agents): 2-3 files, 50-200 LOC
- L (2-3 agents): 4-10 files, 200-500 LOC
- XL (3-5 agents): >10 files, >500 LOC
**OBSERVABLES:** `complexity_determinism_score`

---

### PROP-007: TDD workflow enforced

**TYPE:** INVARIANT
**PRIORITY:** HIGH
**STATEMENT:** RED → GREEN → REFACTOR always followed
**RATIONALE:** Tests ensure correctness
**OBSERVABLES:** `tdd_violations` (should be 0)

---

## PERFORMANCE PROPERTIES

### PROP-008: Interview completes in <30 seconds

**TYPE:** PERFORMANCE
**PRIORITY:** MEDIUM
**STATEMENT:** Max 5 questions, adaptive flow, <30s total
**RATIONALE:** "Quick build" must be quick
**TARGETS:** P50 <10s, P95 <20s, P99 <30s
**OBSERVABLES:** `interview_duration_ms`

---

### PROP-009: 50% faster than wfc-plan + wfc-implement

**TYPE:** PERFORMANCE
**PRIORITY:** MEDIUM
**STATEMENT:** For S/M tasks, wfc-build ≤ 50% of full workflow time
**RATIONALE:** Justify using wfc-build
**BENCHMARK:**
- S: 7.5 min vs 15 min (50% faster)
- M: 15 min vs 30 min (50% faster)
**OBSERVABLES:** `build_duration_ms`
