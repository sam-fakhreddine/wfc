# WFC Integration Tests

Comprehensive integration and end-to-end tests for wfc-implement.

## Test Structure

```
tests/
├── conftest.py                      # PyTest configuration and fixtures
├── test_implement_integration.py   # Component integration tests
├── test_implement_e2e.py           # End-to-end workflow tests
└── README.md                       # This file
```

## Test Coverage

### Integration Tests (`test_implement_integration.py`)

Tests individual components and their integration:

1. **Confidence Checking (TASK-003)**
   - High confidence tasks (≥90%) → proceed
   - Medium confidence tasks (70-89%) → ask questions
   - Low confidence tasks (<70%) → stop

2. **Memory System (TASK-004)**
   - Reflexion logging (mistakes, fixes, rules)
   - Workflow metrics logging (tokens, time, success)
   - Similar error search (keyword matching)
   - Historical token averages

3. **Token Management (TASK-009)**
   - Default budgets (S=200, M=1000, L=2500, XL=5000)
   - Usage tracking and warnings (80% threshold)
   - Budget exceeded detection
   - Historical optimization (20% buffer)

4. **Quality Checker (TASK-001)**
   - Trunk.io result parsing
   - Issue classification
   - Fixable vs non-fixable issues

5. **Failure Severity (User Feedback)**
   - WARNING (don't block)
   - ERROR (block but retryable)
   - CRITICAL (immediate failure)

### End-to-End Tests (`test_implement_e2e.py`)

Tests the complete workflow:

1. **Basic Workflow**
   - TASKS.md parsing
   - Simple task execution
   - Git repository integration

2. **Quality Gate Integration**
   - Quality checks block submission on failure
   - Quality checks allow submission on success

3. **Confidence Workflow**
   - High confidence proceeds to implementation
   - Low confidence stops and asks questions

4. **Memory System Workflow**
   - Past errors inform current work
   - Similar mistake prevention

5. **Rollback Scenarios**
   - Merge rollback on integration test failure
   - Worktree preservation for investigation
   - Max retry limit (2 retries for ERROR severity)

6. **Parallel Execution**
   - Dependency ordering (topological sort)
   - Max agents capacity (default: 5)

7. **TDD Workflow**
   - All 6 phases defined (UNDERSTAND → TEST_FIRST → IMPLEMENT → REFACTOR → QUALITY_CHECK → SUBMIT)

## Running Tests

### Run all tests

```bash
pytest tests/
```

### Run integration tests only

```bash
pytest tests/test_implement_integration.py -v
```

### Run end-to-end tests only

```bash
pytest tests/test_implement_e2e.py -v
```

### Run with coverage

```bash
pytest tests/ --cov=wfc --cov-report=html --cov-report=term
```

### Run specific test

```bash
pytest tests/test_implement_integration.py::TestConfidenceChecker::test_high_confidence_task -v
```

### Run marked tests

```bash
# Integration tests only
pytest tests/ -m integration

# End-to-end tests only
pytest tests/ -m e2e

# Skip slow tests
pytest tests/ -m "not slow"
```

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `project_root` - Project root directory
- `wfc_scripts_dir` - WFC scripts directory
- `wfc_skills_dir` - WFC skills directory
- `sample_task_simple` - Simple task for testing
- `sample_task_complex` - Complex task for testing
- `sample_task_vague` - Vague task (low confidence)

## Test Markers

Custom pytest markers:

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Slow tests (> 1 second)

## Coverage Goals

**Target**: >80% code coverage

### Current Coverage Areas

- ✅ Confidence checking
- ✅ Memory system (reflexion + metrics)
- ✅ Token management (budgets + warnings)
- ✅ Quality checking (Trunk.io integration)
- ✅ Failure severity classification
- ✅ Rollback scenarios
- ✅ Dependency ordering
- ✅ TDD workflow phases

### Not Yet Covered

- Full orchestrator workflow (complex, requires mocks)
- Real Claude Code Task tool integration (requires API)
- Actual merge operations (requires real git operations)
- Dashboard WebSocket (optional, Phase 4)

## Philosophy

**ELEGANT**: Tests are clear, focused, and maintainable
**COMPREHENSIVE**: Cover all critical paths and edge cases
**FAST**: Most tests run in milliseconds (< 1s)
**ISOLATED**: Tests don't depend on external state

## CI Integration

Tests are run automatically in CI:

```bash
# In Makefile
make test          # Run all tests
make test-coverage # Run with coverage report
```

## Debugging Tests

### Verbose output

```bash
pytest tests/ -v
```

### Show print statements

```bash
pytest tests/ -s
```

### Drop into debugger on failure

```bash
pytest tests/ --pdb
```

### Show local variables on failure

```bash
pytest tests/ -l
```

## Adding New Tests

1. Create test file in `tests/` with `test_` prefix
2. Import components from `wfc/`
3. Use fixtures from `conftest.py`
4. Add markers if appropriate
5. Run tests to verify
6. Update this README with new coverage

## This is World Fucking Class. 🚀
