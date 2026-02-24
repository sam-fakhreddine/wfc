# Test Plan: WFC Validate Fixes

## Overview

**Goal**: Achieve >85% test coverage across all 3 components with focus on critical properties

**Approach**: TDD-style (write tests first, then implementation)

**Test Types**:

- **Unit**: 28 tests (individual functions)
- **Integration**: 12 tests (component interactions)
- **E2E**: 4 tests (full workflows)
- **Total**: 44 tests

**Execution Time Target**: <10 seconds for full suite (no network calls)

---

## Test Suite 1: Orchestrator Tests (TASK-016)

**File**: `tests/test_validate_orchestrator.py`
**Coverage Target**: >85%
**Related Properties**: PROP-001, PROP-002, PROP-003, PROP-005, PROP-006, PROP-016

### TEST-001: Two-phase orchestration with mocked agents

- **Type**: integration
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **Description**: Verify prepare → Task tool → finalize flow without in-memory passing
- **Steps**:
  1. Call `prepare_remediation_tasks("test-skill")`
  2. Verify returns list of task specs
  3. Manually write mock agent outputs to workspace
  4. Call `finalize_remediation(task_responses)`
  5. Verify reads from workspace files, not task_responses
- **Expected**: No in-memory data passing, all communication via files

### TEST-002: Workspace creation and structure

- **Type**: unit
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Description**: Verify workspace directory structure is correct
- **Steps**:
  1. Create workspace for skill "test-skill"
  2. Check `.development/validate-{timestamp}/` exists
  3. Check subdirectories: input/, cataloger/, analyst/, fixer/, validator/, report/
  4. Check metadata.json created
- **Expected**: All directories exist, metadata tracks state

### TEST-003: Workspace cleanup on success

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-003
- **Description**: Verify workspace cleaned up after successful validation
- **Steps**:
  1. Run full orchestration (prepare → finalize)
  2. Simulate success (no errors)
  3. Check workspace directory deleted
- **Expected**: Workspace removed from filesystem

### TEST-004: Workspace preserved on failure

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-003
- **Description**: Verify workspace preserved when validation fails
- **Steps**:
  1. Run orchestration
  2. Simulate failure (schema validation error)
  3. Check workspace still exists
- **Expected**: Workspace preserved for debugging

### TEST-005: Task spec generation with dependencies

- **Type**: unit
- **Related Task**: TASK-004
- **Related Property**: PROP-005
- **Description**: Verify task specs include correct dependencies
- **Steps**:
  1. Call `prepare_remediation_tasks()`
  2. Parse returned list
  3. Check Cataloger has no dependencies
  4. Check Analyst depends_on: ["cataloger"]
  5. Check Fixer depends_on: ["analyst"]
- **Expected**: Dependency chain correct

### TEST-006: Grade A short-circuit

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-005
- **Description**: Verify Fixer/Validator skipped for Grade A skills
- **Steps**:
  1. Mock Analyst output with grade: "A"
  2. Call `prepare_rewrite_tasks()`
  3. Verify returns empty list (no Fixer task)
- **Expected**: Grade A skills skip rewrite phase

### TEST-007: Schema validation catches malformed JSON

- **Type**: unit
- **Related Task**: TASK-006
- **Related Property**: PROP-006
- **Description**: Verify schema validation rejects invalid agent outputs
- **Steps**:
  1. Write malformed catalog.json (missing required field)
  2. Call `finalize_remediation()`
  3. Check raises ValidationError with clear message
- **Expected**: Error specifies which field is invalid

### TEST-008: Schema validation accepts valid JSON

- **Type**: unit
- **Related Task**: TASK-006
- **Related Property**: PROP-006
- **Description**: Verify schema validation accepts correct agent outputs
- **Steps**:
  1. Write valid catalog.json, analysis.json to workspace
  2. Call `finalize_remediation()`
  3. Verify no validation errors
- **Expected**: Validation passes silently

### TEST-009: Agent prompt token counts

- **Type**: unit
- **Related Task**: TASK-003
- **Related Property**: PROP-004
- **Description**: Verify all agent prompts under 5K tokens each
- **Steps**:
  1. Load all 4 agent templates (cataloger, analyzer, fixer, validator)
  2. Render with typical workspace path
  3. Count tokens using tiktoken
  4. Verify each < 5000 tokens
- **Expected**: Cataloger: <3K, Analyzer: <5K, Fixer: <5K, Validator: <5K

---

## Test Suite 2: Analyzer Tests (TASK-017)

**File**: `tests/test_validate_analyzer.py`
**Coverage Target**: >85%
**Related Properties**: PROP-008, PROP-009, PROP-010, PROP-011, PROP-017

### TEST-010: Pattern detection identifies all 13 patterns

- **Type**: unit
- **Related Task**: TASK-007
- **Related Property**: PROP-008
- **Description**: Verify pattern detection finds try/except, timeout, retry, etc.
- **Steps**:
  1. Create content with all 13 patterns
  2. Call `_detect_patterns(content)`
  3. Verify returns dict with 13 keys, counts > 0
- **Expected**: All patterns detected

### TEST-011: Pattern detection performance <5ms

- **Type**: performance
- **Related Task**: TASK-007
- **Related Property**: PROP-008
- **Description**: Verify pattern detection is fast
- **Steps**:
  1. Create 10KB content
  2. Time `_detect_patterns()` call
  3. Repeat 100 times, measure p99
- **Expected**: p99 < 5ms

### TEST-012: Failure mode detection from security.json

- **Type**: unit
- **Related Task**: TASK-008
- **Related Property**: PROP-009
- **Description**: Verify checks against known failure modes
- **Steps**:
  1. Create content with eval(), os.system(), shell=True
  2. Call `_check_failure_modes(content)`
  3. Verify returns dict with dangerous patterns flagged
- **Expected**: eval: True, os.system: True, shell: True

### TEST-013: No hardcoded scores (empty content)

- **Type**: unit
- **Related Task**: TASK-009
- **Related Property**: PROP-009
- **Description**: Verify empty content doesn't return hardcoded 8/10
- **Steps**:
  1. Call `_analyze_risks(subject="test", content="")`
  2. Check score != 8
  3. Verify score is low (≤4) for no patterns
- **Expected**: Score ≤4 (not 8)

### TEST-014: No hardcoded scores (different content, different scores)

- **Type**: unit
- **Related Task**: TASK-009
- **Related Property**: PROP-009
- **Description**: Verify different content produces different scores
- **Steps**:
  1. content_a = "no patterns"
  2. content_b = "try/except, timeout, retry, validation"
  3. score_a = `_analyze_risks(..., content_a).score`
  4. score_b = `_analyze_risks(..., content_b).score`
  5. Verify score_a != score_b and score_b > score_a
- **Expected**: Scores differ, better content scores higher

### TEST-015: Scoring range 2-10

- **Type**: unit
- **Related Task**: TASK-009
- **Related Property**: PROP-010
- **Description**: Verify scores are integers in [2, 10]
- **Steps**:
  1. Test with dangerous content (eval) → expect 2-3
  2. Test with no patterns → expect 4
  3. Test with some patterns → expect 5-7
  4. Test with comprehensive patterns → expect 9-10
- **Expected**: All scores in range [2, 10]

### TEST-016: Score distribution across range

- **Type**: integration
- **Related Task**: TASK-009
- **Related Property**: PROP-017
- **Description**: Verify scoring algorithm covers full 2-10 range
- **Steps**:
  1. Create test cases targeting scores 2, 4, 6, 8, 10
  2. Run analyzer on each
  3. Verify scores match expectations
- **Expected**: Can produce 2, 4, 6, 8, 10 with appropriate content

### TEST-017: Recommendations are content-specific

- **Type**: unit
- **Related Task**: TASK-010
- **Related Property**: PROP-011
- **Description**: Verify recommendations reference actual patterns, not generic advice
- **Steps**:
  1. content = "try/except but no timeout"
  2. result = `_analyze_risks(content=content)`
  3. Check strengths contains "try/except"
  4. Check concerns contains "timeout"
  5. Verify "looks fine" not in recommendation
- **Expected**: Specific patterns mentioned, no platitudes

### TEST-018: Generic phrases banned

- **Type**: unit
- **Related Task**: TASK-010
- **Related Property**: PROP-011
- **Description**: Verify generic phrases are never used
- **Steps**:
  1. Run analyzer on 10 different content samples
  2. For each result, check recommendation
  3. Assert "looks fine" not in recommendation
  4. Assert "best practices" not in recommendation
  5. Assert "acceptable" not in recommendation
- **Expected**: No generic platitudes in any recommendation

---

## Test Suite 3: Batch Safety Tests (TASK-018)

**File**: `tests/test_batch_safety.py`
**Coverage Target**: >85%
**Related Properties**: PROP-012, PROP-013, PROP-014, PROP-015, PROP-018

### TEST-019: Dry-run prevents file modifications

- **Type**: integration
- **Related Task**: TASK-011
- **Related Property**: PROP-012
- **Description**: Verify dry-run mode never modifies SKILL.md files
- **Steps**:
  1. Create 3 test SKILL.md files
  2. Record file hashes
  3. Call `fix_batch(patterns=["*.md"], dry_run=True)`
  4. Verify all file hashes unchanged
- **Expected**: 0 files modified

### TEST-020: Dry-run prevents PR creation

- **Type**: integration
- **Related Task**: TASK-011
- **Related Property**: PROP-012
- **Description**: Verify dry-run never creates PRs
- **Steps**:
  1. Mock `gh pr create` subprocess call
  2. Call `fix_batch(patterns=["*.md"], dry_run=True, auto_pr=True)`
  3. Verify `gh pr create` never called
- **Expected**: 0 PR creation calls

### TEST-021: Safety gate aborts on intent violation

- **Type**: integration
- **Related Task**: TASK-012
- **Related Property**: PROP-013
- **Description**: Verify batch aborts if any prompt fails intent check
- **Steps**:
  1. Mock 30 prompts, 1 with intent_preserved: False
  2. Call `fix_batch(patterns=["*.md"])`
  3. Verify returns BatchValidationResult with status: "ABORT"
  4. Verify reason: "Intent preservation failed"
- **Expected**: Abort with clear reason, 0 modifications

### TEST-022: Safety gate aborts on scope creep threshold

- **Type**: integration
- **Related Task**: TASK-012
- **Related Property**: PROP-013
- **Description**: Verify batch aborts if >30% have scope creep
- **Steps**:
  1. Mock 30 prompts, 10 with scope_creep: ["constraint"]
  2. Call `fix_batch(patterns=["*.md"])`
  3. Verify aborts (10/30 = 33% > 30%)
  4. Verify reason mentions scope creep threshold
- **Expected**: Abort at 33% scope creep

### TEST-023: Safety gate passes under threshold

- **Type**: integration
- **Related Task**: TASK-012
- **Related Property**: PROP-013
- **Description**: Verify batch proceeds if ≤30% scope creep
- **Steps**:
  1. Mock 30 prompts, 9 with scope_creep (30% exactly)
  2. Call `fix_batch(patterns=["*.md"], dry_run=True)`
  3. Verify returns BatchValidationResult with status: "DRY_RUN_SUCCESS"
- **Expected**: Passes validation gate

### TEST-024: Rollback checklist generated for 0 PRs

- **Type**: unit
- **Related Task**: TASK-013
- **Related Property**: PROP-014
- **Description**: Verify rollback checklist handles edge case of 0 PRs
- **Steps**:
  1. Call `generate_rollback_checklist(prs=[])`
  2. Verify creates rollback-{timestamp}.md
  3. Check content mentions "0 PRs created"
- **Expected**: Checklist generated even for 0 PRs

### TEST-025: Rollback checklist generated for 30 PRs

- **Type**: unit
- **Related Task**: TASK-013
- **Related Property**: PROP-014
- **Description**: Verify rollback checklist handles large batches
- **Steps**:
  1. Create list of 30 PR objects
  2. Call `generate_rollback_checklist(prs=pr_list)`
  3. Verify checklist includes all 30 PR numbers
  4. Verify one-liner command includes all 30
- **Expected**: Complete checklist with all PRs

### TEST-026: Rollback checklist includes one-liner

- **Type**: unit
- **Related Task**: TASK-013
- **Related Property**: PROP-014
- **Description**: Verify rollback checklist has executable command
- **Steps**:
  1. Generate checklist with 5 PRs
  2. Extract one-liner command
  3. Verify format: `gh pr list --label "batch-..." | xargs ...`
  4. Verify command is copy-pasteable
- **Expected**: Executable shell command present

### TEST-027: Batch summary includes all prompts

- **Type**: integration
- **Related Task**: TASK-014
- **Related Property**: PROP-015
- **Description**: Verify summary aggregates all 30 prompts, not subset
- **Steps**:
  1. Run batch with 30 prompts
  2. Generate summary report
  3. Count table rows
  4. Verify 30 rows (one per prompt)
- **Expected**: Table has 30 rows

### TEST-028: Batch summary shows grade distribution

- **Type**: unit
- **Related Task**: TASK-014
- **Related Property**: PROP-015
- **Description**: Verify summary includes before/after/delta grade distribution
- **Steps**:
  1. Mock batch results: 5 A→A, 10 B→A, 8 C→B, 5 D→C, 2 F→D
  2. Generate summary
  3. Check grade distribution table
  4. Verify delta column shows: A(+10), B(-2), C(-3), D(-3), F(-2)
- **Expected**: Correct before/after/delta distribution

### TEST-029: Batch summary shows aggregated stats

- **Type**: unit
- **Related Task**: TASK-014
- **Related Property**: PROP-015
- **Description**: Verify summary shows X improved, Y unchanged, Z failed
- **Steps**:
  1. Mock results: 20 improved, 8 unchanged, 2 failed
  2. Generate summary
  3. Check stats section
  4. Verify shows "20 improved, 8 unchanged, 2 failed"
- **Expected**: Correct aggregated stats

### TEST-030: Atomic semantics (all-or-nothing)

- **Type**: integration
- **Related Task**: TASK-018
- **Related Property**: PROP-018
- **Description**: Verify 1 failure in batch of 30 prevents all modifications
- **Steps**:
  1. Mock 30 prompts, 29 pass validation, 1 fails
  2. Call `fix_batch(patterns=["*.md"])`
  3. Verify aborts before any modifications
  4. Check 0 files modified
- **Expected**: Atomic behavior, 0 modifications

---

## Test Suite 4: End-to-End Tests

**File**: `tests/test_e2e_validate.py`
**Coverage Target**: Critical workflows only

### TEST-031: E2E Grade A short-circuit

- **Type**: e2e
- **Related Tasks**: TASK-001 to TASK-006
- **Related Properties**: PROP-001, PROP-002, PROP-005
- **Description**: Full workflow for skill that scores Grade A
- **Steps**:
  1. Create test SKILL.md with excellent structure
  2. Run full orchestration (prepare → mock agents → finalize)
  3. Mock Cataloger: clean structure
  4. Mock Analyst: grade A
  5. Verify Fixer never invoked
  6. Verify report shows "No rewrite needed"
- **Expected**: Full workflow completes, skips Fixer

### TEST-032: E2E Grade C with rewrite

- **Type**: e2e
- **Related Tasks**: TASK-001 to TASK-006
- **Related Properties**: PROP-001, PROP-002, PROP-006
- **Description**: Full workflow for skill needing improvements
- **Steps**:
  1. Create test SKILL.md with issues
  2. Run full orchestration
  3. Mock Cataloger: finds issues
  4. Mock Analyst: grade C
  5. Mock Fixer: produces improved SKILL.md
  6. Mock Validator: grade B (improved)
  7. Verify report shows before/after grades
- **Expected**: Full workflow with rewrite path

### TEST-033: E2E Dry-run batch of 5 skills

- **Type**: e2e
- **Related Tasks**: TASK-011 to TASK-015
- **Related Properties**: PROP-012, PROP-013
- **Description**: Batch dry-run workflow
- **Steps**:
  1. Create 5 test SKILL.md files
  2. Run `fix_batch(patterns=["test/*.md"], dry_run=True)`
  3. Verify validation phase completes
  4. Verify no files modified
  5. Verify batch summary generated
  6. Verify rollback checklist NOT generated (dry-run only)
- **Expected**: Validation only, no modifications

### TEST-034: E2E Batch apply with safety gates

- **Type**: e2e
- **Related Tasks**: TASK-011 to TASK-015
- **Related Properties**: PROP-013, PROP-014, PROP-015
- **Description**: Full batch workflow with modifications
- **Steps**:
  1. Create 5 test SKILL.md files (all pass validation)
  2. Run `fix_batch(patterns=["test/*.md"], dry_run=False, auto_pr=False)`
  3. Verify validation phase passes
  4. Verify safety gates pass (no intent violations, <30% scope creep)
  5. Verify files modified
  6. Verify batch summary generated
  7. Verify rollback checklist generated
- **Expected**: Full batch workflow completes

---

## Test Execution Plan

### Phase 1: Unit Tests (28 tests)

Run during development:

```bash
uv run pytest tests/test_validate_orchestrator.py -k "unit" -v
uv run pytest tests/test_validate_analyzer.py -k "unit" -v
uv run pytest tests/test_batch_safety.py -k "unit" -v
```

**Expected time**: <3 seconds

### Phase 2: Integration Tests (12 tests)

Run before commit:

```bash
uv run pytest tests/ -k "integration" -v
```

**Expected time**: <5 seconds

### Phase 3: E2E Tests (4 tests)

Run before PR:

```bash
uv run pytest tests/test_e2e_validate.py -v
```

**Expected time**: <2 seconds

### Full Suite (44 tests)

CI/CD pipeline:

```bash
uv run pytest tests/ --cov=wfc --cov-report=term-missing --cov-fail-under=85
```

**Expected time**: <10 seconds
**Coverage target**: >85%

---

## Test Data & Fixtures

**Fixtures** (`tests/conftest.py`):

- `mock_workspace`: Temporary workspace with structure
- `mock_skill_md`: Sample SKILL.md files (good/bad/excellent)
- `mock_agent_outputs`: Valid JSON outputs for all 4 agents
- `mock_batch_results`: 30 prompt validation results

**Test Data** (`tests/data/`):

- `skill-grade-a.md`: Excellent SKILL.md (should score A)
- `skill-grade-c.md`: Mediocre SKILL.md (should score C)
- `skill-grade-f.md`: Broken SKILL.md (should score F)
- `catalog-valid.json`: Valid cataloger output
- `analysis-valid.json`: Valid analyzer output

---

## Coverage Gaps & Exclusions

**Not Tested** (acceptable gaps):

- Actual Task tool calls (mocked instead)
- Network operations (gh pr create mocked)
- Filesystem edge cases (disk full, permissions) - too environment-specific

**Explicitly Tested**:

- All happy paths
- All error paths
- All safety properties (PROP-001, 009, 012, 013, 018)
- Performance properties (PROP-004, 008)
- Boundary conditions (0 PRs, 30 PRs, Grade A, Grade F)

---

## Success Criteria

✅ All 44 tests passing
✅ >85% line coverage
✅ <10 second execution time
✅ All 9 critical properties validated
✅ No mocked test uses real API calls
✅ Fixtures enable deterministic testing
