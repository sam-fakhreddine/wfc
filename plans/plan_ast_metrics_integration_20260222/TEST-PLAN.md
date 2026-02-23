# Test Plan - AST Metrics Integration

## Testing Approach

### Test Pyramid

- **Unit tests (60%)**: Individual component validation (metrics_extractor, cache_writer, language_detection)
- **Integration tests (30%)**: End-to-end review orchestrator with AST pre-phase
- **Benchmark tests (10%)**: Performance validation (<100ms for 20 files)

### Coverage Targets

- **Line coverage**: >85% for all `wfc/scripts/ast_analyzer/` modules
- **Branch coverage**: >75% for error handling paths (parse failures, missing files)
- **Property coverage**: 100% (all 6 PROP-* verified)

---

## Unit Tests

### TEST-001: Verify PROP-001 (language detection determinism)

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-001
- **File**: `tests/test_language_detection.py`
- **Description**: Call `is_python()` 100 times on the same file, assert all results are identical
- **Steps**:
  1. Create test file `test.py` with valid Python code
  2. Call `is_python(Path("test.py"))` 100 times
  3. Assert all 100 results are `True`
  4. Repeat with `test.js` file, assert all 100 results are `False`
- **Expected**: 100/100 identical results for both files

---

### TEST-002: Verify metrics extraction on valid Python file

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: none
- **File**: `tests/test_ast_metrics_extractor.py`
- **Description**: Parse a known Python file and verify extracted metrics match expected values
- **Steps**:
  1. Create `sample.py` with 2 functions, 1 class, complexity 5
  2. Call `analyze_file(Path("sample.py"))`
  3. Assert `metrics.functions == 2`, `metrics.classes == 1`
  4. Assert complexity budget matches expected value
- **Expected**: Metrics match manual analysis

---

### TEST-003: Verify metrics extractor handles invalid Python gracefully

- **Type**: unit
- **Related Task**: TASK-001
- **Related Property**: PROP-002
- **File**: `tests/test_ast_metrics_extractor.py`
- **Description**: Parse malformed Python file and assert exception is caught, not raised
- **Steps**:
  1. Create `invalid.py` with syntax errors (e.g., `def foo(`)
  2. Call `analyze_file(Path("invalid.py"))`
  3. Assert function returns `None` or error dict, does not raise exception
- **Expected**: No exception raised, graceful failure

---

### TEST-004: Verify cache writer creates correct JSON schema

- **Type**: unit
- **Related Task**: TASK-002
- **Related Property**: none
- **File**: `tests/test_ast_cache_writer.py`
- **Description**: Write AST cache for 3 Python files and validate JSON structure
- **Steps**:
  1. Create 3 test Python files with known metrics
  2. Call `write_ast_cache(files, output_path)`
  3. Read output JSON, assert schema matches:
     - `files` array with 3 entries
     - Each entry has `file`, `lines`, `complexity_budget` keys
     - `summary` has `total_files`, `parsed`, `failed`, `duration_ms`
- **Expected**: JSON schema is valid and complete

---

### TEST-005: Verify cache writer skips non-Python files

- **Type**: unit
- **Related Task**: TASK-002
- **Related Property**: none
- **File**: `tests/test_ast_cache_writer.py`
- **Description**: Pass mixed file types (Python + JS + Markdown) and assert only Python files analyzed
- **Steps**:
  1. Create test files: `test.py`, `test.js`, `README.md`
  2. Call `write_ast_cache([test.py, test.js, README.md], output)`
  3. Read output JSON, assert `files` array has only 1 entry (test.py)
- **Expected**: Only Python files in output

---

### TEST-006: Verify PROP-005 (reviewer prompts include disclaimers)

- **Type**: unit
- **Related Task**: TASK-004
- **Related Property**: PROP-005
- **File**: `tests/test_reviewer_prompts.py`
- **Description**: Grep all 5 reviewer PROMPT.md files for required AST disclaimer text
- **Steps**:
  1. Read `wfc/references/reviewers/{security,correctness,performance,maintainability,reliability}/PROMPT.md`
  2. Assert each contains "supplemental hints"
  3. Assert each contains "Review the full code"
- **Expected**: All 5 prompts pass assertion

---

## Integration Tests

### TEST-007: Verify PROP-002 (parse failure doesn't block review)

- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-002
- **File**: `tests/test_orchestrator_integration.py`
- **Description**: Run full review with intentionally malformed Python file, assert review completes
- **Steps**:
  1. Create git branch with 2 files: `valid.py` (good), `invalid.py` (syntax error)
  2. Invoke `ReviewOrchestrator.run()`
  3. Assert AST pre-phase logs warning about `invalid.py` parse failure
  4. Assert review completes successfully with consensus score
  5. Assert `.ast-context.json` contains only `valid.py` metrics
- **Expected**: Review succeeds, invalid file skipped

---

### TEST-008: Verify PROP-004 (AST cache exists before reviewers spawn)

- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-004
- **File**: `tests/test_orchestrator_integration.py`
- **Description**: Verify `.ast-context.json` file exists after AST pre-phase, before first reviewer Task call
- **Steps**:
  1. Mock `Task` tool to capture when reviewers are spawned
  2. Run `ReviewOrchestrator.run()` on test PR
  3. In the mock, assert `.wfc-review/.ast-context.json` exists and is readable
- **Expected**: File exists before any reviewer spawns

---

### TEST-009: Verify PROP-006 (worktrees excluded from analysis)

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-006
- **File**: `tests/test_ast_cache_writer.py`
- **Description**: Create a git worktree with Python files, run AST analysis, assert worktree files not included
- **Steps**:
  1. Create main repo with `main.py`
  2. Create worktree at `.worktrees/test-branch/` with `worktree.py`
  3. Run `write_ast_cache()` on all Python files in repo
  4. Assert output JSON contains `main.py` but not `worktree.py`
- **Expected**: Worktree files excluded

---

### TEST-010: End-to-end review with AST context

- **Type**: integration
- **Related Task**: TASK-003, TASK-004
- **Related Property**: none
- **File**: `tests/test_orchestrator_integration.py`
- **Description**: Run full review on real PR and verify reviewers receive AST context
- **Steps**:
  1. Create test PR with 5 Python files (mix of simple and complex)
  2. Run `ReviewOrchestrator.run()`
  3. Assert `.ast-context.json` created with 5 file entries
  4. Mock reviewer Task agents, capture their prompts
  5. Assert prompts mention `.ast-context.json` file reference
  6. Assert review completes with consensus score
- **Expected**: Full review uses AST context successfully

---

## Benchmark Tests

### TEST-011: Verify PROP-003 (AST analysis <100ms for 20 files)

- **Type**: benchmark
- **Related Task**: TASK-002
- **Related Property**: PROP-003
- **File**: `tests/test_ast_performance.py`
- **Description**: Benchmark AST analysis on 20 Python files, assert duration <100ms
- **Steps**:
  1. Create 20 test Python files (mix of sizes: 50-500 lines)
  2. Call `write_ast_cache(files, output)` with timing
  3. Assert duration <100ms
  4. Repeat 10 times, assert P95 <100ms
- **Expected**: P95 duration <100ms

---

### TEST-012: Measure token savings with AST context

- **Type**: benchmark
- **Related Task**: none
- **Related Property**: none
- **File**: `tests/test_ast_performance.py`
- **Description**: Compare token usage of sending full file vs AST summary to reviewers
- **Steps**:
  1. Take real WFC file (e.g., `agent.py`, 1468 lines)
  2. Count tokens for full file content (~8000 tokens)
  3. Count tokens for AST summary JSON (~200 tokens)
  4. Assert token reduction >90%
- **Expected**: >90% token reduction

---

## Property Verification Matrix

| Property | Test ID | Type | Status |
|----------|---------|------|--------|
| PROP-001 | TEST-001 | unit | pending |
| PROP-002 | TEST-003, TEST-007 | unit + integration | pending |
| PROP-003 | TEST-011 | benchmark | pending |
| PROP-004 | TEST-008 | integration | pending |
| PROP-005 | TEST-006 | unit | pending |
| PROP-006 | TEST-009 | integration | pending |

---

## Test Execution Plan

### Phase 1: Unit Tests (TASK-005)

Run all unit tests in isolation:

```bash
uv run pytest tests/test_ast_metrics_extractor.py -v
uv run pytest tests/test_ast_cache_writer.py -v
uv run pytest tests/test_language_detection.py -v
uv run pytest tests/test_reviewer_prompts.py -v
```

### Phase 2: Integration Tests (TASK-005)

Run orchestrator integration tests:

```bash
uv run pytest tests/test_orchestrator_integration.py -v
```

### Phase 3: Benchmarks (TASK-005)

Run performance benchmarks:

```bash
uv run pytest tests/test_ast_performance.py -v --benchmark
```

### Phase 4: Full Suite (CI)

Run all tests together:

```bash
make test  # runs full pytest suite
```

---

## Test Data

### Sample Python Files

**valid_simple.py** (complexity 3):

```python
def add(a, b):
    return a + b

def subtract(a, b):
    if a > b:
        return a - b
    else:
        return b - a
```

**valid_complex.py** (complexity 12):

```python
import subprocess

def process_user_input(data):
    if not data:
        return None

    for item in data:
        if item.startswith("cmd_"):
            subprocess.run(item[4:], shell=True)  # Dangerous call
        elif item == "special":
            for nested in range(10):
                if nested % 2 == 0:
                    print(nested)
    return True
```

**invalid_syntax.py** (malformed):

```python
def foo(
    # Missing closing paren and body
```

---

## Success Criteria

- [ ] All 12 tests pass with `uv run pytest tests/test_ast_*.py -v`
- [ ] All 6 properties verified (PROP-001 through PROP-006)
- [ ] Line coverage >85% for `wfc/scripts/ast_analyzer/`
- [ ] Benchmark TEST-011 shows <100ms for 20 files
- [ ] No regressions in existing wfc-review tests
