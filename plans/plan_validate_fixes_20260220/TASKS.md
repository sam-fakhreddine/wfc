---
title: WFC Validate Skill Remediation Fixes
status: active
created: 2026-02-20T00:00:00Z
updated: 2026-02-20T00:00:00Z
tasks_total: 18
tasks_completed: 0
complexity: L
---

# Implementation Plan: WFC Validate Fixes

**Goal**: Implement 3 critical fixes to improve wfc-validate from 6.8/10 to 8.4/10

**Context**: VALIDATE.md analysis identified 3 blocking issues:

- Dimension 7 (2/10): SDK orchestration incompatible with Claude Code
- Dimension 5 (4/10): Analyzer returns hardcoded scores
- Dimension 6 (6/10): Batch operations lack safety mechanisms

**Total Effort**: 15-19 hours across 3 components

---

## Component 1: Dimension 7 - Claude Code Orchestration (6-8 hours)

### TASK-001: Create two-phase orchestrator skeleton

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-001, PROP-002]
- **Files**: `wfc/scripts/orchestrators/validate/orchestrator.py`
- **Description**: Create RemediationOrchestrator class with prepare/finalize phases following wfc-review pattern
- **Acceptance Criteria**:
  - [ ] `prepare_remediation_tasks()` method returns task specs
  - [ ] `finalize_remediation()` method reads workspace results
  - [ ] File-based state management in `.development/validate-{timestamp}/`
  - [ ] No in-memory data passing between agents
  - [ ] Follows exact pattern from `wfc/scripts/orchestrators/review/orchestrator.py`

### TASK-002: Implement workspace management

- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-003]
- **Files**: `wfc/scripts/orchestrators/validate/orchestrator.py`
- **Description**: Create workspace directory structure and file I/O utilities
- **Acceptance Criteria**:
  - [ ] Workspace created at `.development/validate-{timestamp}/`
  - [ ] Subdirectories: input/, cataloger/, analyst/, fixer/, validator/, report/
  - [ ] Metadata.json tracks workspace state
  - [ ] Cleanup on success, preserve on failure

### TASK-003: Create agent prompt templates

- **Complexity**: L
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-004]
- **Files**:
  - `wfc/skills/wfc-validate/agents/cataloger.md`
  - `wfc/skills/wfc-validate/agents/analyzer.md`
  - `wfc/skills/wfc-validate/agents/fixer.md`
  - `wfc/skills/wfc-validate/agents/validator.md`
- **Description**: Port agent prompts from SDK design to markdown templates with {workspace} placeholders
- **Acceptance Criteria**:
  - [ ] Cataloger template parses SKILL.md structure
  - [ ] Analyzer template uses rubric.json for scoring
  - [ ] Fixer template rewrites SKILL.md based on diagnosis
  - [ ] Validator template re-scores fixed SKILL.md
  - [ ] All templates < 5K tokens each

### TASK-004: Implement task spec generation

- **Complexity**: M
- **Dependencies**: [TASK-002, TASK-003]
- **Properties**: [PROP-005]
- **Files**: `wfc/scripts/orchestrators/validate/orchestrator.py`
- **Description**: Build task specs for Claude to execute via Task tool
- **Acceptance Criteria**:
  - [ ] Returns list of dicts with agent_id, prompt, output_file
  - [ ] Cataloger + Analyst always included
  - [ ] Fixer + Validator conditional (Grade < A only)
  - [ ] Dependencies tracked (Analyst depends on Cataloger)
  - [ ] Prompt templates loaded and placeholders filled

### TASK-005: Implement result finalization

- **Complexity**: M
- **Dependencies**: [TASK-004]
- **Properties**: [PROP-006]
- **Files**: `wfc/scripts/orchestrators/validate/orchestrator.py`
- **Description**: Read agent outputs from workspace, validate schemas, generate report
- **Acceptance Criteria**:
  - [ ] Reads catalog.json, analysis.json from workspace
  - [ ] Validates JSON schemas
  - [ ] Conditionally reads fixed-SKILL.md if Grade < A
  - [ ] Generates VALIDATE-REPORT.md
  - [ ] Returns structured result dict

### TASK-006: Add schema validation

- **Complexity**: S
- **Dependencies**: [TASK-005]
- **Properties**: [PROP-007]
- **Files**: `wfc/scripts/orchestrators/validate/schemas.py`
- **Description**: Define JSON schemas for all agent outputs
- **Acceptance Criteria**:
  - [ ] catalog_schema: sections, total_lines, has_examples
  - [ ] analysis_schema: grade, issues[], score
  - [ ] fix_result_schema: intent_preserved, scope_creep[], fixed_md
  - [ ] validation_schema: grade_before, grade_after, verdict
  - [ ] Schema validation raises clear errors

---

## Component 2: Dimension 5 - Analyzer Content Analysis (2-3 hours)

### TASK-007: Implement pattern detection

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-008]
- **Files**: `wfc/skills/wfc-validate/analyzer.py`
- **Description**: Replace hardcoded _analyze_risks() with pattern detection logic
- **Acceptance Criteria**:
  - [ ] Detects 13 defensive programming patterns (try/except, timeout, retry, etc.)
  - [ ] Counts pattern occurrences in content
  - [ ] Returns pattern_counts dict
  - [ ] Execution time < 5ms

### TASK-008: Implement failure mode checking

- **Complexity**: M
- **Dependencies**: [TASK-007]
- **Properties**: [PROP-009]
- **Files**: `wfc/skills/wfc-validate/analyzer.py`
- **Description**: Check content against 11 known failure modes from codebase
- **Acceptance Criteria**:
  - [ ] Reads patterns from `wfc/scripts/hooks/patterns/security.json`
  - [ ] Checks for eval(), os.system(), shell=True, hardcoded secrets
  - [ ] Returns failure_modes dict (pattern: found boolean)
  - [ ] Execution time < 10ms

### TASK-009: Implement dynamic scoring algorithm

- **Complexity**: S
- **Dependencies**: [TASK-007, TASK-008]
- **Properties**: [PROP-010]
- **Files**: `wfc/skills/wfc-validate/analyzer.py`
- **Description**: Calculate score 2-10 based on detected patterns and failure modes
- **Acceptance Criteria**:
  - [ ] Base score: 4/10
  - [ ] +1 for each pattern category (max +6)
  - [ ] -2 for dangerous patterns (eval, shell injection)
  - [ ] -1 for missing critical patterns
  - [ ] Returns int score 2-10 (not hardcoded 8)

### TASK-010: Generate context-aware recommendations

- **Complexity**: M
- **Dependencies**: [TASK-009]
- **Properties**: [PROP-011]
- **Files**: `wfc/skills/wfc-validate/analyzer.py`
- **Description**: Generate specific, actionable recommendations based on missing patterns
- **Acceptance Criteria**:
  - [ ] Strengths list: specific patterns found
  - [ ] Concerns list: specific patterns missing
  - [ ] Recommendation: context-aware (not generic "looks fine")
  - [ ] Returns DimensionAnalysis with real data

---

## Component 3: Dimension 6 - Blast Radius Mitigations (6-8 hours)

### TASK-011: Implement dry-run mode

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-012]
- **Files**: `wfc/skills/wfc-prompt-fixer/orchestrator.py`
- **Description**: Add two-phase batch validation (validate all → apply changes)
- **Acceptance Criteria**:
  - [ ] `fix_batch()` accepts `dry_run` parameter (default: True)
  - [ ] Phase 1: Validate all prompts, collect results
  - [ ] Phase 2: Only apply if all pass safety gates
  - [ ] Returns BatchValidationResult before modifications
  - [ ] Abort if intent violations or scope creep threshold exceeded

### TASK-012: Add safety gates

- **Complexity**: M
- **Dependencies**: [TASK-011]
- **Properties**: [PROP-013]
- **Files**: `wfc/skills/wfc-prompt-fixer/orchestrator.py`
- **Description**: Implement abort conditions for batch operations
- **Acceptance Criteria**:
  - [ ] Intent preservation: 100% required (abort if any fail)
  - [ ] Scope creep threshold: >30% triggers abort
  - [ ] Validation failures: timeout/schema errors trigger abort
  - [ ] Returns clear abort reason if triggered

### TASK-013: Implement rollback checklist generator

- **Complexity**: M
- **Dependencies**: [TASK-011]
- **Properties**: [PROP-014]
- **Files**: `wfc/skills/wfc-prompt-fixer/orchestrator.py`
- **Description**: Generate rollback instructions after batch completion
- **Acceptance Criteria**:
  - [ ] Creates `.development/batch-rollbacks/rollback-{timestamp}.md`
  - [ ] Includes one-liner command to close all PRs
  - [ ] Lists all PR numbers and branch names
  - [ ] Manual revert instructions for merged PRs
  - [ ] Generated automatically after PR creation

### TASK-014: Implement batch summary report

- **Complexity**: M
- **Dependencies**: [TASK-011]
- **Properties**: [PROP-015]
- **Files**: `wfc/skills/wfc-prompt-fixer/orchestrator.py`
- **Description**: Generate consolidated summary for all processed prompts
- **Acceptance Criteria**:
  - [ ] Creates `.development/batch-summaries/summary-{timestamp}.md`
  - [ ] Table: skill | grade_before | grade_after | issues_resolved | scope_creep_count
  - [ ] Aggregated stats: X improved, Y unchanged, Z failed
  - [ ] Grade distribution before/after with delta
  - [ ] PR links and status

### TASK-015: Add CLI flags for batch mode

- **Complexity**: S
- **Dependencies**: [TASK-011]
- **Properties**: []
- **Files**: `wfc/skills/wfc-prompt-fixer/cli.py`
- **Description**: Add --dry-run, --no-dry-run, --force flags
- **Acceptance Criteria**:
  - [ ] --dry-run: Force dry-run even if default changes
  - [ ] --no-dry-run: Skip dry-run and apply immediately (dangerous)
  - [ ] --force: Skip safety gates (very dangerous, warn user)
  - [ ] Help text explains each flag's impact

---

## Component 4: Testing & Integration (3-4 hours)

### TASK-016: Add orchestrator tests

- **Complexity**: L
- **Dependencies**: [TASK-001, TASK-002, TASK-003, TASK-004, TASK-005]
- **Properties**: [PROP-016]
- **Files**: `tests/test_validate_orchestrator.py`
- **Description**: Test two-phase orchestrator with mocked agents
- **Acceptance Criteria**:
  - [ ] Test prepare_remediation_tasks() returns correct specs
  - [ ] Test workspace creation and cleanup
  - [ ] Test finalize_remediation() with mock outputs
  - [ ] Test Grade A short-circuit (skip Fixer)
  - [ ] Test error handling (missing files, invalid JSON)
  - [ ] Coverage: >85%

### TASK-017: Add analyzer tests

- **Complexity**: M
- **Dependencies**: [TASK-007, TASK-008, TASK-009, TASK-010]
- **Properties**: [PROP-017]
- **Files**: `tests/test_validate_analyzer.py`
- **Description**: Test pattern detection and scoring
- **Acceptance Criteria**:
  - [ ] Test content with no error handling → score ≤4/10
  - [ ] Test content with try/except → score 5-7/10
  - [ ] Test content with comprehensive patterns → score ≥9/10
  - [ ] Test dangerous patterns → score <4/10 with warnings
  - [ ] Test recommendations are specific (not generic)
  - [ ] Coverage: >85%

### TASK-018: Add batch safety tests

- **Complexity**: M
- **Dependencies**: [TASK-011, TASK-012, TASK-013, TASK-014]
- **Properties**: [PROP-018]
- **Files**: `tests/test_batch_safety.py`
- **Description**: Test dry-run mode, safety gates, rollback generation
- **Acceptance Criteria**:
  - [ ] Test dry-run prevents modifications
  - [ ] Test safety gates abort correctly
  - [ ] Test rollback checklist generation
  - [ ] Test batch summary report format
  - [ ] Test atomic semantics (all-or-nothing)
  - [ ] Coverage: >85%

---

## Task Dependencies (DAG)

```
TASK-001 (orchestrator skeleton)
  ├── TASK-002 (workspace management)
  │   └── TASK-004 (task spec generation)
  │       └── TASK-005 (result finalization)
  │           └── TASK-006 (schema validation)
  └── TASK-003 (agent templates)
      └── TASK-004 (task spec generation)

TASK-007 (pattern detection)
  └── TASK-008 (failure modes)
      └── TASK-009 (dynamic scoring)
          └── TASK-010 (recommendations)

TASK-011 (dry-run mode)
  ├── TASK-012 (safety gates)
  ├── TASK-013 (rollback checklist)
  ├── TASK-014 (batch summary)
  └── TASK-015 (CLI flags)

TASK-001-006 → TASK-016 (orchestrator tests)
TASK-007-010 → TASK-017 (analyzer tests)
TASK-011-015 → TASK-018 (batch safety tests)
```

---

## Implementation Phases

**Phase 1 (6-8 hours)**: Component 1 (Dimension 7)

- TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006

**Phase 2 (2-3 hours)**: Component 2 (Dimension 5)

- TASK-007 → TASK-008 → TASK-009 → TASK-010

**Phase 3 (6-8 hours)**: Component 3 (Dimension 6)

- TASK-011 → TASK-012, TASK-013, TASK-014 (parallel) → TASK-015

**Phase 4 (3-4 hours)**: Testing

- TASK-016, TASK-017, TASK-018 (can run in parallel)

**Total: 17-23 hours** (fits within 15-19h estimate with parallelization)

---

## Critical Path

```
TASK-001 (M: 2h) → TASK-002 (M: 2h) → TASK-003 (L: 3h) → TASK-004 (M: 2h) → TASK-005 (M: 2h) → TASK-016 (L: 3h)
Total: 14 hours sequential (longest path)
```

With parallelization:

- Phase 2 (TASK-007-010) can run concurrently with Phase 1
- Phase 3 (TASK-011-015) can run after Phase 1
- Phase 4 tests can run in parallel

**Wall clock time: ~12-14 hours** with 2 parallel work streams
