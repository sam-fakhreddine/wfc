# Formal Properties: WFC Validate Fixes

## PROP-001: SAFETY - Two-Phase Orchestration Must Not Pass In-Memory Data

- **Statement**: Orchestrator must never pass Python objects between agents; all communication via filesystem
- **Rationale**: Claude Code Task tool cannot receive in-memory objects, only prompts and file paths
- **Priority**: critical
- **Observables**: `agent_calls_with_objects`, `file_io_operations`
- **Related Tasks**: TASK-001, TASK-004
- **Validation**: Code review + integration test with mocked Task tool

## PROP-002: INVARIANT - Workspace State Always File-Based

- **Statement**: All agent state must be persisted to `.development/validate-{timestamp}/` workspace
- **Rationale**: Enables debugging, audit trails, and agent isolation
- **Priority**: critical
- **Observables**: `workspace_files_created`, `workspace_cleanup_success`
- **Related Tasks**: TASK-002
- **Validation**: Test that all agent outputs exist as files in workspace

## PROP-003: LIVENESS - Workspace Cleanup On Success

- **Statement**: Workspace must be cleaned up after successful validation, preserved on failure
- **Rationale**: Prevents disk space exhaustion while enabling post-mort Em debugging
- **Priority**: important
- **Observables**: `workspace_directories_count`, `disk_space_used`
- **Related Tasks**: TASK-002
- **Validation**: Test cleanup behavior in success/failure scenarios

## PROP-004: PERFORMANCE - Agent Prompts Under 5K Tokens Each

- **Statement**: Each agent prompt template must be < 5000 tokens when rendered
- **Rationale**: Keeps token costs manageable (target: 8K-22K total per skill)
- **Priority**: important
- **Observables**: `agent_prompt_tokens`, `total_validation_tokens`
- **Related Tasks**: TASK-003
- **Validation**: Token counting tests for all 4 agent templates

## PROP-005: INVARIANT - Task Specs Must Include Dependencies

- **Statement**: Task spec dict must include `depends_on` field tracking agent dependencies
- **Rationale**: Ensures Analyst runs after Cataloger, Fixer after Analyst, etc.
- **Priority**: critical
- **Observables**: `task_execution_order`, `dependency_violations`
- **Related Tasks**: TASK-004
- **Validation**: Unit test verifying task spec structure

## PROP-006: SAFETY - Result Finalization Must Validate Schemas

- **Statement**: finalize_remediation() must validate all JSON outputs against schemas before use
- **Rationale**: Prevents malformed agent outputs from causing orchestrator crashes
- **Priority**: critical
- **Observables**: `schema_validation_failures`, `invalid_json_errors`
- **Related Tasks**: TASK-005, TASK-006
- **Validation**: Test with malformed JSON files in workspace

## PROP-007: INVARIANT - Schema Validation Errors Must Be Actionable

- **Statement**: Schema validation errors must specify which field failed and why
- **Rationale**: Enables quick diagnosis of agent prompt issues
- **Priority**: important
- **Observables**: `schema_error_clarity_score`
- **Related Tasks**: TASK-006
- **Validation**: Manual review of error messages

## PROP-008: PERFORMANCE - Pattern Detection Under 5ms

- **Statement**: Pattern detection for Dimension 5 must complete in < 5 milliseconds
- **Rationale**: Prevents analyzer from becoming bottleneck (target: <100ms total)
- **Priority**: important
- **Observables**: `pattern_detection_duration_ms`
- **Related Tasks**: TASK-007
- **Validation**: Performance benchmark test with 10KB content

## PROP-009: SAFETY - Analyzer Must Not Use Hardcoded Scores

- **Statement**: _analyze_risks() must never return hardcoded score; must compute from content
- **Rationale**: Fixes critical Dimension 5 issue (false confidence)
- **Priority**: critical
- **Observables**: `hardcoded_score_violations`, `score_variance`
- **Related Tasks**: TASK-007, TASK-009
- **Validation**: Test that same content twice produces same score, different content produces different scores

## PROP-010: INVARIANT - Scoring Range Must Be 2-10

- **Statement**: Analyzer scores must be integers in range [2, 10], never hardcoded 8
- **Rationale**: Provides meaningful signal (2 = dangerous, 10 = excellent)
- **Priority**: critical
- **Observables**: `score_distribution`, `out_of_range_scores`
- **Related Tasks**: TASK-009
- **Validation**: Test scoring algorithm with edge cases

## PROP-011: INVARIANT - Recommendations Must Be Content-Specific

- **Statement**: Recommendations must reference actual patterns found/missing, not generic advice
- **Rationale**: Actionable guidance vs platitudes ("add try/except to X" not "improve error handling")
- **Priority**: important
- **Observables**: `recommendation_specificity_score`
- **Related Tasks**: TASK-010
- **Validation**: Manual review + string match tests (no "looks fine", "best practices")

## PROP-012: SAFETY - Dry-Run Must Never Modify Files

- **Statement**: fix_batch(dry_run=True) must never write to SKILL.md files or create PRs
- **Rationale**: Prevents accidental modifications during validation phase
- **Priority**: critical
- **Observables**: `file_modifications_in_dry_run`, `pr_creations_in_dry_run`
- **Related Tasks**: TASK-011
- **Validation**: Test dry-run leaves filesystem unchanged

## PROP-013: SAFETY - Safety Gates Must Abort on Critical Violations

- **Statement**: Batch must abort if any intent preservation fails OR >30% scope creep detected
- **Rationale**: Prevents cascading failures (27/30 partial success scenario)
- **Priority**: critical
- **Observables**: `batch_aborts`, `safety_gate_triggers`
- **Related Tasks**: TASK-012
- **Validation**: Test that violations trigger abort with clear reason

## PROP-014: LIVENESS - Rollback Checklist Must Be Generated

- **Statement**: Rollback checklist must be created after every batch operation (success or failure)
- **Rationale**: Enables 10-second rollback vs 30-minute manual revert
- **Priority**: important
- **Observables**: `rollback_checklists_created`, `pr_rollback_success_rate`
- **Related Tasks**: TASK-013
- **Validation**: Test checklist generation with 0, 1, 30 PRs

## PROP-015: INVARIANT - Batch Summary Must Aggregate All Prompts

- **Statement**: Batch summary must include grade changes for ALL processed prompts, not subset
- **Rationale**: Single consolidated view (vs 32 scattered reports)
- **Priority**: important
- **Observables**: `summary_completeness_score`
- **Related Tasks**: TASK-014
- **Validation**: Test summary includes all 30 prompts when batch processes 30

## PROP-016: INVARIANT - Orchestrator Tests Must Mock Agent Responses

- **Statement**: Tests must not spawn real Task tool agents; use mocked JSON files in workspace
- **Rationale**: Fast, deterministic testing without Claude API calls
- **Priority**: important
- **Observables**: `test_execution_time`, `api_calls_during_tests`
- **Related Tasks**: TASK-016
- **Validation**: Test suite runs in < 5 seconds with no network calls

## PROP-017: INVARIANT - Analyzer Tests Must Cover Score Range

- **Statement**: Tests must verify scores from 2/10 (dangerous) to 10/10 (excellent)
- **Rationale**: Ensures scoring algorithm works across full range, not just middle values
- **Priority**: important
- **Observables**: `test_score_coverage`
- **Related Tasks**: TASK-017
- **Validation**: Test cases for scores 2, 4, 6, 8, 10

## PROP-018: SAFETY - Batch Safety Tests Must Verify Atomic Semantics

- **Statement**: Tests must verify all-or-nothing behavior (abort early prevents partial success)
- **Rationale**: Validates fix for Dimension 6 (27/30 partial failure scenario)
- **Priority**: critical
- **Observables**: `atomic_batch_test_coverage`
- **Related Tasks**: TASK-018
- **Validation**: Test that 1 failure in batch of 30 aborts all, modifies 0 files

---

## Property Summary

| Type | Count | Critical | Important |
|------|-------|----------|-----------|
| SAFETY | 7 | 6 | 1 |
| INVARIANT | 8 | 3 | 5 |
| LIVENESS | 2 | 0 | 2 |
| PERFORMANCE | 2 | 0 | 2 |
| **TOTAL** | **19** | **9** | **10** |

---

## Observable Metrics

All properties define observables for monitoring:

**Orchestrator Health:**

- `agent_calls_with_objects` (PROP-001): Must be 0
- `workspace_files_created` (PROP-002): 4-6 files per run
- `workspace_cleanup_success` (PROP-003): >95%
- `agent_prompt_tokens` (PROP-004): <5K per agent
- `schema_validation_failures` (PROP-006): <1% of runs

**Analyzer Quality:**

- `hardcoded_score_violations` (PROP-009): Must be 0
- `score_distribution` (PROP-010): Normal distribution 2-10
- `pattern_detection_duration_ms` (PROP-008): <5ms p99
- `recommendation_specificity_score` (PROP-011): Manual audit

**Batch Safety:**

- `file_modifications_in_dry_run` (PROP-012): Must be 0
- `batch_aborts` (PROP-013): >0 when violations occur
- `rollback_checklists_created` (PROP-014): 100% of batches
- `pr_rollback_success_rate` (PROP-014): >99%

**Testing Coverage:**

- `test_execution_time` (PROP-016): <5 seconds
- `atomic_batch_test_coverage` (PROP-018): >85%
- `test_score_coverage` (PROP-017): Covers 2, 4, 6, 8, 10

---

## Critical Path Properties

Must be validated first (block implementation if failing):

1. **PROP-001** (SAFETY): Two-phase orchestration - blocks TASK-001
2. **PROP-009** (SAFETY): No hardcoded scores - blocks TASK-007
3. **PROP-012** (SAFETY): Dry-run never modifies - blocks TASK-011
4. **PROP-013** (SAFETY): Safety gates abort - blocks TASK-012
5. **PROP-018** (SAFETY): Atomic semantics - blocks TASK-018

All other properties can be validated incrementally.
