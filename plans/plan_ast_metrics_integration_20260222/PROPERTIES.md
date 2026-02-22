# Formal Properties - AST Metrics Integration

## PROP-001: INVARIANT - Language detection must be deterministic

- **Statement**: `is_python(file_path)` must return the same result for the same file across multiple invocations
- **Rationale**: Consistency: reviewers must see the same set of analyzed files regardless of when analysis runs
- **Priority**: high
- **Observables**: `language_detection_consistency_ratio` (should be 1.0)
- **Verification**: Unit test calls `is_python()` 100x on same file, asserts all results identical

---

## PROP-002: SAFETY - Parse failures must not block review

- **Statement**: If AST parsing fails for any file, the review process must continue without that file's metrics
- **Rationale**: Availability: a malformed Python file or parser bug should not prevent code review
- **Priority**: critical
- **Observables**: `ast_parse_failures`, `reviews_blocked_by_ast_errors` (should be 0)
- **Verification**: Integration test with intentionally malformed Python file, assert review completes successfully

---

## PROP-003: PERFORMANCE - AST analysis overhead must be <5% of review time

- **Statement**: For a typical PR (5-20 files), AST analysis duration must be <100ms
- **Rationale**: Efficiency: reviewers should not wait for static analysis
- **Priority**: high
- **Observables**: `ast_analysis_duration_ms`, `review_total_duration_ms`
- **Verification**: Benchmark test on 20-file PR, assert `ast_analysis_duration_ms < 100`

---

## PROP-004: LIVENESS - AST cache file must exist before reviewers spawn

- **Statement**: `.wfc-review/.ast-context.json` must exist (even if empty) before any reviewer Task agent is invoked
- **Rationale**: Correctness: reviewers expect the file to be readable, missing file causes task failures
- **Priority**: critical
- **Observables**: `ast_cache_file_missing_errors` (should be 0)
- **Verification**: Integration test asserts `.ast-context.json` exists after orchestrator pre-phase, before reviewer spawn

---

## PROP-005: INVARIANT - Reviewer prompts must include AST disclaimers

- **Statement**: All 5 reviewer PROMPT.md files must contain the text "supplemental hints" and "Review the full code"
- **Rationale**: Safety: prevent reviewers from over-relying on automated metrics
- **Priority**: medium
- **Observables**: `reviewer_prompts_with_ast_disclaimers` (should be 5/5)
- **Verification**: Unit test greps all PROMPT.md files for required phrases

---

## PROP-006: SAFETY - AST analyzer must exclude development artifacts

- **Statement**: AST analysis must skip files in `.worktrees/`, `.venv/`, `__pycache__/`, and other non-production directories
- **Rationale**: Correctness: analyzing duplicate or generated code wastes time and pollutes metrics
- **Priority**: high
- **Observables**: `ast_analyzed_worktree_files` (should be 0)
- **Verification**: Integration test with worktree present, assert no worktree files in `.ast-context.json`

---

## Property Summary

| ID | Type | Priority | Verifiable |
|----|------|----------|------------|
| PROP-001 | INVARIANT | high | Unit test |
| PROP-002 | SAFETY | critical | Integration test |
| PROP-003 | PERFORMANCE | high | Benchmark |
| PROP-004 | LIVENESS | critical | Integration test |
| PROP-005 | INVARIANT | medium | Unit test |
| PROP-006 | SAFETY | high | Integration test |

**Critical properties (must verify before release):** PROP-002, PROP-004
