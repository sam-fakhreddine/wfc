---
title: Diff Manifest Integration
status: active
created: 2026-02-20T20:00:00Z
updated: 2026-02-20T20:00:00Z
tasks_total: 6
tasks_completed: 0
complexity: M
---

# Implementation Tasks: Diff Manifest Integration

## TASK-001: Add feature flag to ReviewOrchestrator

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-001]
- **Files**: `wfc/scripts/orchestrators/review/orchestrator.py`
- **Description**: Add `use_diff_manifest` parameter to ReviewOrchestrator.**init**() with default False for backward compatibility
- **Acceptance Criteria**:
  - [ ] `use_diff_manifest` parameter added to **init**
  - [ ] Parameter stored as instance variable
  - [ ] Default value is False
  - [ ] Docstring updated

## TASK-002: Integrate manifest builder in reviewer_engine

- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-001, PROP-002]
- **Files**: `wfc/scripts/orchestrators/review/reviewer_engine.py`
- **Description**: Replace embedded diff logic (lines 255-260) with conditional manifest builder
- **Acceptance Criteria**:
  - [ ] Import diff_manifest module
  - [ ] Check `use_diff_manifest` flag in _build_task_prompt
  - [ ] If True: call build_diff_manifest() and format_manifest_for_reviewer()
  - [ ] If False: use existing embedded diff logic
  - [ ] Backward compatibility preserved

## TASK-003: Add token metrics logging

- **Complexity**: S
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-003]
- **Files**: `wfc/scripts/orchestrators/review/reviewer_engine.py`
- **Description**: Log token usage (before/after) when manifest is used
- **Acceptance Criteria**:
  - [ ] Calculate tokens for full diff
  - [ ] Calculate tokens for manifest
  - [ ] Log reduction percentage
  - [ ] Include in review metadata

## TASK-004: Add integration tests

- **Complexity**: M
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-004]
- **Files**: `tests/orchestrators/review/test_integration_manifest.py`
- **Description**: Test end-to-end review with manifests vs full diff
- **Acceptance Criteria**:
  - [ ] Test review with manifest enabled
  - [ ] Test review with manifest disabled
  - [ ] Compare finding counts (should be within ±15%)
  - [ ] Validate token reduction >70%
  - [ ] Test all 5 reviewers

## TASK-005: Update documentation

- **Complexity**: S
- **Dependencies**: [TASK-001, TASK-002]
- **Properties**: []
- **Files**: `CLAUDE.md`, `wfc/references/TOKEN_MANAGEMENT.md`
- **Description**: Document the diff manifest feature and usage
- **Acceptance Criteria**:
  - [ ] Update CLAUDE.md with feature flag usage
  - [ ] Update TOKEN_MANAGEMENT.md with implementation details
  - [ ] Add example of enabling diff manifests
  - [ ] Document token reduction metrics

## TASK-006: Create gradual rollout plan

- **Complexity**: S
- **Dependencies**: [TASK-004]
- **Properties**: [PROP-005]
- **Files**: `.development/ROLLOUT_PLAN.md`
- **Description**: Document phased rollout strategy (10% → 50% → 100%)
- **Acceptance Criteria**:
  - [ ] Define rollout phases
  - [ ] Specify metrics to monitor
  - [ ] Define success criteria per phase
  - [ ] Document rollback procedure
