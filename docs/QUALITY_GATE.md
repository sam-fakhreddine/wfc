# WFC Quality Gate

**Pre-review quality checks for implementation agents**

## Purpose

The Quality Gate catches simple issues **before** expensive multi-agent review:
- **Token-efficient**: Fix linting locally, not in review comments
- **Fast feedback**: Agents get immediate feedback vs waiting for review
- **Quality enforcement**: All code meets minimum standards
- **Review focus**: Reviewers focus on logic, architecture, security - not code style

## Workflow Integration

```
Implementation Agent
    ↓
    Writes code
    ↓
    Runs tests (TDD)
    ↓
┌───────────────────────┐
│  QUALITY GATE         │  ← NEW: Pre-review checks
│  ✅ Formatting        │
│  ✅ Linting           │
│  ✅ Tests             │
│  ✅ Type checking     │
└───────────────────────┘
    ↓ (only if all pass)
wfc-review (Multi-agent consensus)
    ↓
Merge to main
```

## Quality Checks

### 1. Python Formatting (black)

**What**: Ensures consistent code style
**Tool**: `black --check --line-length=100`
**Fix**: `black --line-length=100 <files>` or `make format`
**Rationale**: Don't waste review tokens on "add space here"

### 2. Python Linting (ruff)

**What**: Catches common bugs, unused imports, complexity issues
**Tool**: `ruff check --line-length=100`
**Fix**: `ruff check --fix <files>` or `make lint --fix`
**Rationale**: Fix before review, not during

### 3. Tests (pytest)

**What**: Ensures tests pass
**Tool**: `pytest -v`
**Fix**: Fix failing tests
**Rationale**: Don't send broken code to review

### 4. Type Checking (mypy) - Optional

**What**: Checks type hints
**Tool**: `mypy`
**Fix**: Add/fix type annotations
**Rationale**: Catch type errors early

## Usage

### Command Line

```bash
# Check specific files
wfc quality-check file1.py file2.py

# Check all Python files
make quality-check-all

# Skip tests (fast check)
wfc quality-check --no-tests file.py

# Include type checking
wfc quality-check --type-check file.py

# JSON output (for automation)
wfc quality-check --json file.py
```

### Python API

```python
from wfc.scripts.quality_checker import QualityChecker

checker = QualityChecker(
    files=["src/module.py", "src/utils.py"],
    run_tests=True,
    run_type_check=False
)

report = checker.check_all()

if report.passed:
    # Send to review
    call_wfc_review()
else:
    # Show fixes
    print(report)
```

### Integration in wfc-implement

The quality gate is **automatically enforced** by wfc-implement:

```python
# In agent workflow (pseudocode)
def agent_workflow(task):
    # 1-4. Understand, test-first, implement, refactor
    code_files = implement_task(task)

    # 5. Quality gate (NEW)
    checker = QualityChecker(files=code_files)
    report = checker.check_all()

    if not report.passed:
        print(report)
        return "FIX_REQUIRED", report

    # 6. Send to review (only if quality gate passed)
    return send_to_review(code_files)
```

## Example Output

### Success

```
============================================================
WFC QUALITY CHECK REPORT
============================================================

✅ Python Formatting (black)
   All 3 Python files formatted correctly

✅ Python Linting (ruff)
   All 3 Python files pass linting

✅ Tests (pytest)
   All tests passed (2 test files)

============================================================
✅ ALL CHECKS PASSED - Ready for review
============================================================
```

### Failure with Fixes

```
============================================================
WFC QUALITY CHECK REPORT
============================================================

❌ Python Formatting (black)
   3 files need formatting
   Fix: black --line-length=100 <files> (or: make format)

❌ Python Linting (ruff)
   5 linting errors found
   Details: src/module.py:15:1: F401 'os' imported but unused
            src/utils.py:42:80: E501 line too long (92 > 100)
   Fix: ruff check --fix <files> (or: make lint --fix)

✅ Tests (pytest)
   All tests passed (2 test files)

============================================================
❌ CHECKS FAILED - Fix issues before review
============================================================
```

## Configuration

### pyproject.toml

```toml
[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### Skip Checks (Not Recommended)

In special cases, you can skip checks:

```bash
# Skip all quality checks (NOT RECOMMENDED)
wfc-implement --skip-quality-check

# Skip specific checks
wfc quality-check --no-tests file.py
```

**Warning**: Skipping quality checks defeats the purpose. Only use for:
- Generated code that doesn't need style enforcement
- Emergency hotfixes (but fix afterward)
- Experimental code in feature branches

## ROI Analysis

### Without Quality Gate

```
Agent implements → Sends to review
    ↓
5 personas review (5 x 2000 tokens = 10k tokens)
    ↓
Review finds: "Code not formatted, unused import on line 42"
    ↓
Agent fixes → Re-review (another 10k tokens)
    ↓
Total: 20k tokens, 2 review cycles
```

### With Quality Gate

```
Agent implements → Quality gate (local, free)
    ↓
Finds: "Code not formatted, unused import on line 42"
    ↓
Agent fixes (immediately, locally)
    ↓
Quality gate passes → Sends to review
    ↓
5 personas review (5 x 2000 tokens = 10k tokens)
    ↓
Review focuses on: logic, architecture, security
    ↓
Total: 10k tokens, 1 review cycle
```

**Savings**: 50% tokens, 50% time, higher quality reviews

## Best Practices

1. **Run locally before commit**
   ```bash
   make quality-check
   ```

2. **Fix automatically when possible**
   ```bash
   make format  # Auto-fix formatting
   make lint --fix  # Auto-fix linting
   ```

3. **Integrate in pre-commit hooks**
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: wfc-quality-check
         entry: wfc quality-check
   ```

4. **Run in CI/CD**
   ```yaml
   # .github/workflows/validate.yml
   - name: Quality Check
     run: make quality-check-all
   ```

## Philosophy

**ELEGANT**: Simple checks, clear fixes
**MULTI-TIER**: Quality checks (local) separated from review (multi-agent)
**TOKEN-AWARE**: Fix locally (free) not in review (expensive)

---

**This is World Fucking Class.** 🚀
