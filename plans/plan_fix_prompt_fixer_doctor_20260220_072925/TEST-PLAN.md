# Test Plan: Fix Review Findings

**Goal**: Achieve ≥85% test coverage for wfc-prompt-fixer and wfc-doctor with comprehensive functional, integration, and error path testing.

**Context**: Current test suite only validates file structure (6 structural tests). Review identified that identified bugs would not be caught. Need functional tests for orchestrators, error paths, edge cases, and full pipeline integration.

---

## Testing Approach

### Test Categories

1. **Unit Tests** (70% of tests)
   - Individual function/method testing
   - Mocked dependencies (filesystem, subprocess, Task tool)
   - Fast execution (< 1 second per test)
   - Focus: error handling, validation logic, edge cases

2. **Integration Tests** (25% of tests)
   - Multi-component workflows
   - Real filesystem operations (tmpdir fixtures)
   - Real subprocess calls (when safe)
   - Mocked external dependencies (Task tool for agents)
   - Medium execution (1-5 seconds per test)
   - Focus: orchestrator workflows, agent coordination

3. **End-to-End Tests** (5% of tests)
   - Full pipeline with real agents
   - Expensive (spawn actual Task tool agents)
   - Slow execution (30-60 seconds per test)
   - Run in CI only (not local dev)
   - Focus: production scenario validation

### Coverage Targets

| Module | Target | Current | Gap |
|--------|--------|---------|-----|
| wfc-prompt-fixer/orchestrator.py | 85% | ~10% | +75% |
| wfc-prompt-fixer/workspace.py | 90% | ~15% | +75% |
| wfc-prompt-fixer/cli.py | 80% | ~20% | +60% |
| wfc-doctor/orchestrator.py | 85% | ~10% | +75% |
| wfc-doctor/checks/*.py (all 5) | 85% | ~5% | +80% |
| **Overall** | **85%** | **~12%** | **+73%** |

### Test Framework

- **pytest**: Test runner and fixtures
- **pytest-cov**: Coverage reporting (target 85%)
- **pytest-mock**: Mocking framework for filesystem, subprocess, Task tool
- **hypothesis**: Property-based testing for validation logic
- **tmpdir**: Isolated filesystem for tests

---

## Test Cases by Task

### TASK-001: Error Handling in workspace.py (PROP-001, PROP-002, PROP-003)

#### TEST-001: workspace_creation_success

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **Description**: Verify workspace.create() succeeds with valid inputs
- **Steps**:
  1. Call workspace_manager.create(valid_prompt_path, wfc_mode=False)
  2. Verify workspace directory created
  3. Verify subdirectories exist (input/, 01-analyzer/, 02-fixer/, 03-reporter/)
  4. Verify prompt copied to input/prompt.md
  5. Verify metadata.json written
- **Expected**: Workspace structure complete, no exceptions

#### TEST-002: workspace_creation_file_not_found

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **Description**: Verify graceful error when prompt file missing
- **Steps**:
  1. Call workspace_manager.create(Path("/nonexistent/prompt.md"))
  2. Catch WorkspaceError
  3. Verify error message includes "file not found"
- **Expected**: WorkspaceError raised with actionable message

#### TEST-003: workspace_creation_permission_denied

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **Description**: Verify graceful error when permission denied
- **Steps**:
  1. Mock Path.mkdir to raise PermissionError
  2. Call workspace_manager.create(valid_prompt_path)
  3. Catch WorkspaceError
  4. Verify error message includes "permission denied"
- **Expected**: WorkspaceError with "Check file permissions" guidance

#### TEST-004: workspace_cleanup_success

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-002
- **Description**: Verify cleanup removes workspace directory
- **Steps**:
  1. Create workspace
  2. Call workspace_manager.cleanup(workspace_path)
  3. Verify workspace directory deleted
- **Expected**: Directory removed, no exceptions

#### TEST-005: workspace_cleanup_permission_error_ignored

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-002
- **Description**: Verify cleanup doesn't raise exception on permission error
- **Steps**:
  1. Create workspace
  2. Mock shutil.rmtree to raise PermissionError
  3. Call workspace_manager.cleanup(workspace_path)
  4. Verify no exception raised
- **Expected**: Cleanup returns normally (ignore_errors=True behavior)

#### TEST-006: read_text_operations_handle_unicode_error

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **Description**: Verify read operations handle non-UTF8 files
- **Steps**:
  1. Create file with binary content (not valid UTF-8)
  2. Call workspace_manager.read_fix(workspace)
  3. Catch WorkspaceError
  4. Verify error message includes "encoding"
- **Expected**: WorkspaceError with clear message

---

### TASK-002: Try/Finally Cleanup (PROP-002, PROP-004)

#### TEST-007: orchestrator_cleanup_on_analyzer_failure

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Description**: Verify workspace cleaned up if Analyzer agent fails
- **Steps**:
  1. Mock _spawn_analyzer to raise exception
  2. Call orchestrator.fix_prompt(valid_path)
  3. Catch exception
  4. Verify workspace directory deleted
- **Expected**: Workspace cleaned up despite exception

#### TEST-008: orchestrator_cleanup_on_fixer_failure

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Description**: Verify workspace cleaned up if Fixer agent fails
- **Steps**:
  1. Mock _spawn_fixer_with_retry to raise exception
  2. Call orchestrator.fix_prompt(valid_path)
  3. Catch exception
  4. Verify workspace directory deleted
- **Expected**: Workspace cleaned up despite exception

#### TEST-009: orchestrator_cleanup_preserved_with_keep_workspace_flag

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Description**: Verify --keep-workspace flag prevents cleanup
- **Steps**:
  1. Mock _spawn_analyzer to raise exception
  2. Call orchestrator.fix_prompt(valid_path, keep_workspace=True)
  3. Catch exception
  4. Verify workspace directory still exists
- **Expected**: Workspace preserved for debugging

---

### TASK-003/004/005: Agent Spawning (PROP-005, PROP-006)

#### TEST-010: analyzer_agent_spawned_with_correct_prompt

- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-005
- **Description**: Verify Analyzer agent spawned with correct configuration
- **Steps**:
  1. Mock Task tool to capture call parameters
  2. Call orchestrator._spawn_analyzer(workspace, wfc_mode=True)
  3. Verify Task tool called with subagent_type="general-purpose"
  4. Verify prompt loaded from agents/analyzer.md
  5. Verify workspace path included in prompt context
  6. Verify wfc_mode=True enables WFC-specific checks
- **Expected**: Task tool called correctly, returns mocked analysis

#### TEST-011: analyzer_response_schema_validation

- **Type**: unit
- **Related Task**: TASK-003, TASK-009
- **Related Property**: PROP-006
- **Description**: Verify analysis.json schema validated before use
- **Steps**:
  1. Mock Task tool to return invalid JSON (missing "grade" field)
  2. Call orchestrator._spawn_analyzer(workspace, wfc_mode=False)
  3. Catch ValueError
  4. Verify error message includes "missing required field: grade"
- **Expected**: Schema validation catches missing fields

#### TEST-012: fixer_retry_logic_with_exponential_backoff

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-007
- **Description**: Verify Fixer retries with exponential backoff
- **Steps**:
  1. Mock Task tool to fail validation on first 2 attempts, succeed on 3rd
  2. Mock time.sleep to track delays
  3. Call orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)
  4. Verify Task tool called 3 times
  5. Verify sleep delays: [2, 4] seconds (exponential backoff)
- **Expected**: Retry succeeds on 3rd attempt with correct backoff

#### TEST-013: fixer_max_retries_exceeded

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-007
- **Description**: Verify exception raised after max retries
- **Steps**:
  1. Mock Task tool to always fail validation
  2. Call orchestrator._spawn_fixer_with_retry(workspace, max_retries=2)
  3. Catch RuntimeError
  4. Verify error message includes "max retries exceeded"
  5. Verify Task tool called exactly 3 times (original + 2 retries)
- **Expected**: Exception after 3 attempts

#### TEST-014: reporter_full_pipeline

- **Type**: end-to-end
- **Related Task**: TASK-005
- **Related Property**: PROP-005
- **Description**: Verify full Analyzer → Fixer → Reporter pipeline
- **Steps**:
  1. Mock all 3 agents with realistic responses
  2. Call orchestrator.fix_prompt(valid_path, auto_pr=False)
  3. Verify FixResult returned with correct fields
  4. Verify report.md generated with all sections
  5. Verify workspace contains all expected files
- **Expected**: Full pipeline completes, report generated

---

### TASK-006: Parallel Batch Processing (PROP-008, PROP-009)

#### TEST-015: batch_parallel_execution_performance

- **Type**: integration
- **Related Task**: TASK-006
- **Related Property**: PROP-008
- **Description**: Verify batch mode processes 4 prompts in parallel
- **Steps**:
  1. Create 4 test prompt files
  2. Mock agents to sleep 5 seconds (simulate work)
  3. Measure time: orchestrator.fix_batch(pattern, wfc_mode=False)
  4. Verify total time < 8 seconds (not 20 seconds sequential)
  5. Verify 4 FixResults returned
- **Expected**: Parallel speedup confirmed (4x work in ~1.5x time)

#### TEST-016: batch_workspace_name_uniqueness

- **Type**: unit
- **Related Task**: TASK-006
- **Related Property**: PROP-009
- **Description**: Verify workspace names unique even in parallel
- **Steps**:
  1. Generate 1000 workspace names using datetime.now() + uuid
  2. Verify all names unique (no collisions)
  3. Verify names include microseconds: YYYYMMDD-HHMMSS-ffffff-XXXXXXXX
- **Expected**: 0 collisions in 1000 names

#### TEST-017: batch_partial_failure_handling

- **Type**: integration
- **Related Task**: TASK-006
- **Related Property**: PROP-002
- **Description**: Verify batch mode preserves partial results on failures
- **Steps**:
  1. Create 4 test prompts
  2. Mock agent to fail on prompts 2 and 4
  3. Call orchestrator.fix_batch(pattern)
  4. Verify 2 FixResults returned (prompts 1 and 3 succeeded)
  5. Verify failed prompts reported in output
  6. Verify workspaces cleaned up for all 4 prompts
- **Expected**: Partial results preserved, cleanup happens for all

---

### TASK-007: CLI Validation (PROP-003, PROP-010)

#### TEST-018: cli_empty_path_args

- **Type**: unit
- **Related Task**: TASK-007
- **Related Property**: PROP-010
- **Description**: Verify CLI rejects empty path arguments
- **Steps**:
  1. Call main(args=[""])
  2. Verify error printed: "Empty path provided"
  3. Verify exit code 1
- **Expected**: Clear error, early exit

#### TEST-019: cli_mutually_exclusive_flags

- **Type**: unit
- **Related Task**: TASK-007
- **Related Property**: PROP-010
- **Description**: Verify --wfc and --no-wfc mutually exclusive
- **Steps**:
  1. Call main(args=["path.md", "--wfc", "--no-wfc"])
  2. Verify error: "--wfc and --no-wfc are mutually exclusive"
  3. Verify exit code 1
- **Expected**: Validation error before orchestrator init

#### TEST-020: cli_invalid_path_characters

- **Type**: unit
- **Related Task**: TASK-007
- **Related Property**: PROP-003
- **Description**: Verify CLI handles invalid path characters
- **Steps**:
  1. Call main(args=["\x00invalid\npath.md"])
  2. Catch ValueError or OSError
  3. Verify error message includes "Invalid path"
- **Expected**: Graceful error handling

---

### TASK-008: Glob Validation (PROP-003, PROP-011)

#### TEST-021: glob_safe_pattern_accepted

- **Type**: unit
- **Related Task**: TASK-008
- **Related Property**: PROP-011
- **Description**: Verify safe glob patterns accepted
- **Steps**:
  1. Call orchestrator.fix_batch("wfc/skills/*/SKILL.md")
  2. Verify pattern processed (no validation error)
- **Expected**: Pattern accepted

#### TEST-022: glob_parent_traversal_rejected

- **Type**: unit
- **Related Task**: TASK-008
- **Related Property**: PROP-011
- **Description**: Verify ".." in pattern rejected
- **Steps**:
  1. Call orchestrator.fix_batch("../../../etc/**/*")
  2. Catch ValueError
  3. Verify error: "Pattern cannot contain '..'"
- **Expected**: Pattern rejected before glob.glob()

#### TEST-023: glob_root_path_rejected

- **Type**: unit
- **Related Task**: TASK-008
- **Related Property**: PROP-011
- **Description**: Verify absolute paths rejected
- **Steps**:
  1. Call orchestrator.fix_batch("/etc/**/*")
  2. Catch ValueError
  3. Verify error: "Pattern cannot start with '/'"
- **Expected**: Pattern rejected

#### TEST-024: glob_excessive_recursion_rejected

- **Type**: unit
- **Related Task**: TASK-008
- **Related Property**: PROP-011
- **Description**: Verify patterns with > 2 levels of "**" rejected
- **Steps**:
  1. Call orchestrator.fix_batch("**/**/**/*.md")
  2. Catch ValueError
  3. Verify error: "Glob pattern too complex (max 2 levels of **)"
- **Expected**: Pattern rejected

#### TEST-025: glob_match_count_truncation

- **Type**: integration
- **Related Task**: TASK-008
- **Related Property**: PROP-011
- **Description**: Verify match count capped at 1000
- **Steps**:
  1. Create directory with 1500 matching files
  2. Call orchestrator.fix_batch("test_dir/**/*.md")
  3. Verify warning printed: "Pattern matches 1500 files. Proceeding with first 1000."
  4. Verify only 1000 files processed
- **Expected**: Truncation prevents DoS

---

### TASK-011-014: Doctor Check Modules (PROP-013, PROP-014, PROP-015)

#### TEST-026: skills_checker_validates_count

- **Type**: integration
- **Related Task**: TASK-011
- **Related Property**: PROP-013
- **Description**: Verify SkillsChecker counts wfc-* skills correctly
- **Steps**:
  1. Mock Path.home() to return test directory
  2. Create 30 wfc-* skill directories
  3. Call skills_checker.check(auto_fix=False)
  4. Verify status="PASS" and issues=[]
- **Expected**: Count validation passes with 30 skills

#### TEST-027: skills_checker_detects_deprecated_fields

- **Type**: integration
- **Related Task**: TASK-011
- **Related Property**: PROP-013
- **Description**: Verify deprecated frontmatter fields detected
- **Steps**:
  1. Create SKILL.md with deprecated field "user-invocable: true"
  2. Call skills_checker.check(auto_fix=False)
  3. Verify status="WARN"
  4. Verify issues includes "deprecated field: user-invocable"
- **Expected**: Deprecated fields flagged

#### TEST-028: skills_checker_auto_fix_removes_deprecated

- **Type**: integration
- **Related Task**: TASK-011
- **Related Property**: PROP-013
- **Description**: Verify auto-fix removes deprecated fields
- **Steps**:
  1. Create SKILL.md with deprecated field
  2. Call skills_checker.check(auto_fix=True)
  3. Verify deprecated field removed from file
  4. Verify fixes_applied includes "Removed deprecated field: user-invocable"
- **Expected**: Auto-fix modifies file correctly

#### TEST-029: precommit_checker_subprocess_streaming

- **Type**: integration
- **Related Task**: TASK-014
- **Related Property**: PROP-015
- **Description**: Verify pre-commit output streamed line-by-line
- **Steps**:
  1. Mock subprocess.Popen to yield output lines
  2. Capture stdout during precommit_checker.check()
  3. Verify each line printed immediately (not buffered)
  4. Verify memory usage constant (no buffering)
- **Expected**: Streaming output confirmed

#### TEST-030: precommit_checker_timeout_kills_process

- **Type**: integration
- **Related Task**: TASK-014
- **Related Property**: PROP-014
- **Description**: Verify subprocess killed on timeout
- **Steps**:
  1. Mock subprocess.Popen to hang (never return)
  2. Call precommit_checker.check() with timeout=5
  3. Verify proc.kill() called after 5 seconds
  4. Verify proc.wait(timeout=5) called
  5. Verify CheckResult includes "timed out after 5s"
- **Expected**: Process terminated, no zombies

---

### TASK-016: Functional Tests (PROP-017)

#### TEST-031: end_to_end_single_prompt_fix

- **Type**: end-to-end
- **Related Task**: TASK-016
- **Related Property**: PROP-017
- **Description**: Full pipeline with real agents (expensive, CI only)
- **Steps**:
  1. Create test prompt with known issues (vague spec, decorative role)
  2. Call orchestrator.fix_prompt(test_path) with real Task tool
  3. Wait for Analyzer, Fixer, Reporter agents to complete
  4. Verify FixResult returned
  5. Verify report.md contains improvements
  6. Verify fixed prompt different from original
- **Expected**: Real agents produce valid output (30-60s execution)

#### TEST-032: end_to_end_doctor_health_check

- **Type**: end-to-end
- **Related Task**: TASK-016
- **Related Property**: PROP-017
- **Description**: Full doctor check with real checks (medium expensive)
- **Steps**:
  1. Setup test environment (install skills, configure settings)
  2. Call doctor_orchestrator.run_health_check(auto_fix=False)
  3. Verify all 5 checks complete
  4. Verify report.md generated
  5. Verify no timeouts
- **Expected**: All checks run successfully (10-20s execution)

---

### TASK-018: Disk Space Check (PROP-004)

#### TEST-033: workspace_creation_disk_space_check

- **Type**: unit
- **Related Task**: TASK-018
- **Related Property**: PROP-004
- **Description**: Verify workspace creation checks disk space
- **Steps**:
  1. Mock shutil.disk_usage to return low space (500MB free)
  2. Call workspace_manager.create(valid_path)
  3. Catch RuntimeError
  4. Verify error: "Insufficient disk space: 0.49GB available"
- **Expected**: Creation fails before any file operations

#### TEST-034: workspace_copy_verification

- **Type**: unit
- **Related Task**: TASK-018
- **Related Property**: PROP-001
- **Description**: Verify file copy verification detects partial writes
- **Steps**:
  1. Mock shutil.copy to create file with wrong size
  2. Call workspace_manager.create(valid_path)
  3. Catch RuntimeError
  4. Verify error: "Copy verification failed: size mismatch"
- **Expected**: Partial copy detected and rejected

---

## Coverage Strategy

### High-Priority Coverage Areas

1. **Error paths** (most gaps in current coverage)
   - All exception handlers tested
   - All validation rejection paths tested
   - All timeout scenarios tested

2. **Edge cases** (often missed)
   - Empty files, malformed JSON, binary files
   - Extremely large files (> 10MB)
   - Unicode/encoding issues
   - Permission denied, disk full
   - Race conditions (file deleted between check and use)

3. **Integration scenarios** (complex workflows)
   - Full agent pipeline (Analyzer → Fixer → Reporter)
   - Batch processing with mixed success/failure
   - Doctor checks with various invalid states
   - CLI with all flag combinations

### Coverage Measurement

```bash
# Run tests with coverage
uv run pytest --cov=wfc/skills/wfc-prompt-fixer --cov=wfc/skills/wfc-doctor --cov-report=html --cov-report=term-missing

# Coverage targets per module
wfc/skills/wfc-prompt-fixer/orchestrator.py: 85%
wfc/skills/wfc-prompt-fixer/workspace.py: 90%
wfc/skills/wfc-prompt-fixer/cli.py: 80%
wfc/skills/wfc-doctor/orchestrator.py: 85%
wfc/skills/wfc-doctor/checks/skills_check.py: 85%
wfc/skills/wfc-doctor/checks/prompts_check.py: 85%
wfc/skills/wfc-doctor/checks/settings_check.py: 85%
wfc/skills/wfc-doctor/checks/hooks_check.py: 85%
wfc/skills/wfc-doctor/checks/precommit_check.py: 85%
```

### Uncovered Lines Strategy

For lines that can't be covered (defensive programming, unreachable code):

- Add `# pragma: no cover` comment with explanation
- Justify why line is unreachable
- Example: `raise AssertionError("Should never happen")  # pragma: no cover`

---

## Test Data Management

### Fixtures (conftest.py)

```python
@pytest.fixture
def tmp_workspace(tmp_path):
    """Temporary workspace for tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
def sample_prompt(tmp_path):
    """Sample prompt file with known issues."""
    prompt_path = tmp_path / "test_prompt.md"
    prompt_path.write_text("""
---
name: test-prompt
---
# Test Prompt
You are a helpful assistant. Please help me.
""")
    return prompt_path

@pytest.fixture
def mock_task_tool(mocker):
    """Mock Task tool for agent spawning."""
    return mocker.patch('wfc.skills.wfc_prompt_fixer.orchestrator.Task')
```

### Test Data Files

```
tests/
├── fixtures/
│   ├── prompts/
│   │   ├── valid_prompt.md
│   │   ├── invalid_frontmatter.md
│   │   ├── binary_file.dat
│   │   └── large_prompt.md (1MB)
│   ├── skills/
│   │   ├── valid_skill/SKILL.md
│   │   ├── deprecated_fields_skill/SKILL.md
│   │   └── missing_frontmatter_skill/SKILL.md
│   └── agent_responses/
│       ├── analysis_valid.json
│       ├── analysis_missing_grade.json
│       └── fix_result_valid.json
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    - name: Install dependencies
      run: uv pip install -e ".[test]"
    - name: Run unit tests
      run: uv run pytest tests/ -m "not e2e" --cov --cov-report=xml
    - name: Run integration tests
      run: uv run pytest tests/ -m "not e2e" --cov-append
    - name: Run E2E tests (expensive)
      run: uv run pytest tests/ -m "e2e" --cov-append
    - name: Check coverage threshold
      run: |
        coverage=$(uv run coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
        if (( $(echo "$coverage < 85" | bc -l) )); then
          echo "Coverage $coverage% below threshold 85%"
          exit 1
        fi
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, mocked dependencies)
    integration: Integration tests (medium speed, real filesystem)
    e2e: End-to-end tests (slow, real agents)
    slow: Tests that take > 5 seconds
```

### Local Development

```bash
# Fast feedback loop (unit only)
uv run pytest -m unit

# Medium feedback loop (unit + integration)
uv run pytest -m "not e2e"

# Full test suite (before PR)
uv run pytest --cov
```

---

## Test Summary

| Category | Count | Coverage Target |
|----------|-------|-----------------|
| Unit Tests | 24 | 70% of all tests |
| Integration Tests | 8 | 25% of all tests |
| End-to-End Tests | 2 | 5% of all tests |
| **Total** | **34** | **≥85% line coverage** |

**Execution Time Estimates**:

- Unit tests: ~5 seconds total
- Integration tests: ~30 seconds total
- E2E tests: ~90 seconds total (CI only)
- **Total CI time**: ~2 minutes

**Gap to Close**: Current 12% → Target 85% = **+73% coverage** = **~250 new lines of test code**
