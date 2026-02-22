# Test Plan: Diff Manifest Integration

## Testing Approach

**Strategy**: Test-Driven Development (TDD) with integration testing
**Coverage Target**: 95% for new code, 100% for critical paths
**Test Types**: Unit (existing), Integration (new), A/B comparison (validation)

---

## Unit Tests (Already Complete ✓)

### TEST-001: Diff manifest creation

- **Type**: unit
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Status**: ✓ COMPLETE (28/28 passing)
- **Files**:
  - `tests/orchestrators/review/test_diff_manifest.py`
  - `tests/orchestrators/review/test_diff_parser.py`
  - `tests/orchestrators/review/test_domain_tagger.py`

---

## Integration Tests (To Be Created)

### TEST-002: End-to-end review with manifests

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-001, PROP-003
- **Description**: Run complete review flow with `use_diff_manifest=True`
- **Steps**:
  1. Create ReviewOrchestrator with `use_diff_manifest=True`
  2. Run review on sample diff
  3. Verify all 5 reviewers complete successfully
  4. Verify findings are generated
  5. Compare finding counts to baseline
- **Expected**:
  - All reviewers complete without errors
  - Finding counts within ±15% of baseline
  - Consensus score calculated correctly

### TEST-003: Backward compatibility verification

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-001
- **Description**: Verify `use_diff_manifest=False` behaves identically to current implementation
- **Steps**:
  1. Run review with `use_diff_manifest=False`
  2. Compare output to baseline review
  3. Verify byte-for-byte identical prompts sent to reviewers
- **Expected**: Identical behavior to pre-manifest implementation

### TEST-004: Token reduction validation

- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-002
- **Description**: Measure actual token reduction in production-like scenario
- **Steps**:
  1. Run review on 3 sample commits (security, performance, correctness)
  2. Capture token metrics from logs
  3. Calculate reduction percentage
- **Expected**: ≥70% token reduction (target: 80%)

### TEST-005: All reviewers with manifests

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-004
- **Description**: Test each reviewer individually with manifest input
- **Steps**:
  1. For each reviewer (Security, Correctness, Performance, Maintainability, Reliability):
     - Build manifest for domain-relevant diff
     - Invoke reviewer with manifest
     - Verify findings generated
     - Check domain tagging worked correctly
- **Expected**: All 5 reviewers produce valid findings

### TEST-006: Graceful degradation on error

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-005
- **Description**: Test fallback behavior when manifest builder fails
- **Steps**:
  1. Mock diff_parser to raise exception
  2. Run review with `use_diff_manifest=True`
  3. Verify system falls back to full diff
  4. Verify review completes successfully
  5. Check error logged
- **Expected**:
  - No crash
  - Fallback to full diff
  - Warning logged
  - Review completes

---

## A/B Comparison Tests (Validation)

### TEST-007: Quality preservation validation

- **Type**: validation
- **Related Task**: TASK-004
- **Related Property**: PROP-003
- **Description**: A/B test manifests vs full diff on 20 real PRs
- **Steps**:
  1. Select 20 diverse PRs from git history
  2. Run reviews with `use_diff_manifest=False` (baseline)
  3. Run reviews with `use_diff_manifest=True` (experimental)
  4. Compare:
     - Finding counts per reviewer
     - Severity scores
     - Consensus scores
     - Missed findings (false negatives)
- **Expected**:
  - Finding counts: ±15% variance
  - Consensus scores: ±0.5 points
  - No critical findings missed

### TEST-008: Performance benchmarking

- **Type**: validation
- **Related Task**: TASK-003
- **Related Property**: PROP-002
- **Description**: Measure end-to-end performance improvement
- **Steps**:
  1. Benchmark review time with full diff (baseline)
  2. Benchmark review time with manifests
  3. Measure token processing time
  4. Calculate cost savings
- **Expected**:
  - Token reduction: ≥70%
  - Review time: 40-50% faster
  - Cost: ~80% reduction

---

## Rollout Validation (Phase Gates)

### TEST-009: 10% rollout validation

- **Type**: monitoring
- **Related Task**: TASK-006
- **Related Property**: PROP-003
- **Description**: Monitor first 10% of reviews using manifests
- **Metrics to Monitor**:
  - Error rate (target: <1%)
  - Finding count variance (target: ±15%)
  - Token reduction achieved (target: >70%)
  - Review completion rate (target: 100%)
- **Duration**: 24 hours
- **Success Criteria**: All metrics within targets

### TEST-010: 50% rollout validation

- **Type**: monitoring
- **Related Task**: TASK-006
- **Related Property**: PROP-003
- **Description**: Expand to 50% of reviews
- **Metrics to Monitor**: Same as TEST-009
- **Duration**: 48 hours
- **Success Criteria**: All metrics within targets

### TEST-011: 100% rollout validation

- **Type**: monitoring
- **Related Task**: TASK-006
- **Related Property**: PROP-003
- **Description**: Full rollout with continued monitoring
- **Metrics to Monitor**: Same as TEST-009
- **Duration**: 1 week
- **Success Criteria**: Stable performance, no rollback needed

---

## Test Data

**Sample Diffs** (for TEST-007):

- Security-heavy: Auth changes, crypto updates, secrets removal
- Performance-heavy: Query optimization, caching, N+1 fixes
- Correctness-heavy: Null safety, edge cases, error handling
- Mixed: Multi-domain changes
- Large: 500+ line diffs
- Small: <10 line diffs

**Test Fixtures**:

- `tests/fixtures/diffs/security_auth_change.diff`
- `tests/fixtures/diffs/performance_n_plus_1.diff`
- `tests/fixtures/diffs/correctness_null_check.diff`
- `tests/fixtures/diffs/large_refactor.diff`
- `tests/fixtures/diffs/small_bugfix.diff`

---

## Coverage Requirements

| Module | Target | Critical Paths |
|--------|--------|----------------|
| diff_manifest.py | 95% | build_diff_manifest(), format_manifest_for_reviewer() |
| diff_parser.py | 95% | parse_diff(),_finalize_hunk() |
| domain_tagger.py | 90% | tag_file_domains() |
| reviewer_engine.py (new code) | 100% | Manifest conditional logic |

---

## Rollback Criteria

Trigger immediate rollback if:

- Error rate >5% in any rollout phase
- Finding count variance >25% from baseline
- Token reduction <50% (indicates manifest not working)
- Any crash or data loss incident

**Rollback Procedure**:

1. Set `use_diff_manifest=False` globally
2. Restart review service
3. Verify reviews return to baseline behavior
4. Investigate root cause
5. Fix and re-test before retry
