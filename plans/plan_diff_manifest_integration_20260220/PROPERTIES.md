# Formal Properties: Diff Manifest Integration

## PROP-001: SAFETY - Backward Compatibility

- **Statement**: When `use_diff_manifest=False`, review behavior must be identical to current implementation
- **Rationale**: Existing reviews must not be affected during rollout
- **Priority**: critical
- **Observables**: review_findings_count, review_scores, token_usage
- **Verification**: Integration tests comparing manifest=False vs baseline

## PROP-002: PERFORMANCE - Token Reduction

- **Statement**: When `use_diff_manifest=True`, token usage must be reduced by ≥70% compared to full diff
- **Rationale**: Primary goal is 80% token reduction (validated at 87.6%)
- **Priority**: high
- **Observables**: tokens_before, tokens_after, reduction_percentage
- **Verification**: Token counting in reviewer_engine logs

## PROP-003: INVARIANT - Quality Preservation

- **Statement**: Finding counts with manifests must be within ±15% of full diff findings
- **Rationale**: Token optimization must not sacrifice review quality
- **Priority**: critical
- **Observables**: findings_with_manifest, findings_with_full_diff, finding_delta
- **Verification**: A/B testing on 20 sample diffs

## PROP-004: LIVENESS - All Reviewers Supported

- **Statement**: All 5 reviewers (Security, Correctness, Performance, Maintainability, Reliability) must successfully process manifests
- **Rationale**: Feature must work across all reviewer domains
- **Priority**: high
- **Observables**: reviewer_success_rate, domain_coverage
- **Verification**: Integration tests for each reviewer type

## PROP-005: SAFETY - Graceful Degradation

- **Statement**: If manifest builder fails, system must fall back to full diff without crashing
- **Rationale**: Feature should fail-safe, not fail-hard
- **Priority**: high
- **Observables**: manifest_build_errors, fallback_count
- **Verification**: Error injection tests
