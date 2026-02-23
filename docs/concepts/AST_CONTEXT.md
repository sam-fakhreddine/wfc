# AST Context - Supplemental Review Metrics

**Status**: Integrated (2026-02-22)
**Plan**: `plans/plan_ast_metrics_integration_20260222/`

## Overview

AST Context provides reviewers with **supplemental static analysis metrics** to guide their code review. It extracts actionable insights from Python code's Abstract Syntax Tree (AST) without replacing human judgment.

**Key Philosophy**: AST metrics are HINTS, not findings. Reviewers must verify all insights in actual code context.

## What It Does

Before reviewers analyze code, WFC runs lightweight AST analysis to extract:

1. **Cyclomatic Complexity** - McCabe complexity scores for functions
2. **Dangerous Patterns** - Calls to `eval`, `exec`, `compile`, `system`, etc.
3. **Import Analysis** - Detection of risky modules (`subprocess`, `os`, `pickle`)
4. **Nesting Depth** - Maximum nesting levels in functions
5. **Error Handling Coverage** - Functions with/without try/except blocks
6. **Hotspots** - Functions flagged for multiple issues

All metrics are written to `.wfc-review/.ast-context.json` before reviewers spawn.

## Token Efficiency

**97% token reduction** compared to sending full file content:

| Approach | Tokens per File | 20-File PR Total |
|----------|-----------------|------------------|
| Full file content | ~8000 | ~160,000 |
| AST metrics | ~200 | ~4,000 |
| **Savings** | **97%** | **156,000 tokens** |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Review Orchestrator                       │
│                                                              │
│  1. prepare_review(files) → task specs                      │
│  2. _run_ast_analysis(files) → .ast-context.json  ← NEW     │
│  3. spawn reviewers (5 parallel agents)                     │
│  4. finalize_review(responses) → consensus score            │
└─────────────────────────────────────────────────────────────┘
```

**Execution Order**:

1. Review request received with file list
2. AST analysis runs **BEFORE** reviewers spawn (fail-open)
3. Cache file `.ast-context.json` created
4. Reviewers reference cache during analysis
5. Review continues normally

## Cache Format

`.wfc-review/.ast-context.json`:

```json
{
  "files": [
    {
      "file": "path/to/file.py",
      "lines": 150,
      "complexity_budget": 45,
      "_note": "📍 Supplemental hints only. Review the full code, not just these flags.",
      "dangerous_imports": ["subprocess", "pickle"],
      "_imports_note": "⚠️  Verify actual usage. Presence ≠ vulnerability.",
      "hotspots": [
        {
          "line": 42,
          "function": "process_user_input",
          "issues": ["high_complexity:12", "dangerous_calls:eval", "missing_error_handling"]
        }
      ],
      "_hotspots_note": "💡 Suggested focus areas. Not exhaustive.",
      "complex_functions": [
        {"name": "calculate_score", "line": 78, "complexity": 11}
      ],
      "_complexity_note": "🔍 High complexity warrants deeper review."
    }
  ],
  "summary": {
    "parsed": 15,
    "failed": 0,
    "total_files": 15,
    "duration_ms": 42.3
  }
}
```

## Reviewer Integration

Each of the 5 reviewers receives domain-specific guidance in their PROMPT.md:

### Security Reviewer

- `dangerous_imports`: `subprocess`, `os`, `pickle`, `yaml`
- `dangerous_calls`: `eval`, `exec`, `compile`, `system`
- Focus: Injection attack surface, deserialization risks

### Correctness Reviewer

- `complex_functions`: High cyclomatic complexity
- `hotspots`: Deep nesting (potential edge case bugs)
- Focus: Logic complexity, state management

### Performance Reviewer

- `complex_functions`: Algorithmic complexity indicators
- `hotspots`: Deep nesting (potential O(n²) candidates)
- Focus: Time complexity, nested loops

### Maintainability Reviewer

- `complex_functions`: Functions >10 complexity (refactoring candidates)
- `hotspots`: Deep nesting >4 levels
- Focus: SOLID violations, code clarity

### Reliability Reviewer

- `hotspots`: Missing error handling on I/O operations
- `has_try_except`: Per-function error coverage
- Focus: Resource cleanup, error propagation

## Performance Characteristics

**Measured on WFC codebase** (311 Python files, 61,055 lines):

| Metric | Value |
|--------|-------|
| Average parse time | 1.27ms per file |
| 20-file PR overhead | <100ms |
| Total throughput | 154,555 lines/second |
| Review time overhead | <0.2% (vs 10-20s review) |

## Fail-Open Strategy

**AST analysis failures NEVER block code review:**

1. **Parse failures**: Logged to stderr, review continues
2. **Module crashes**: Exception caught, empty cache created
3. **Cache write errors**: Warning logged, reviewers proceed without AST

Example output on partial failure:

```
AST analysis completed in 45.2ms (18/20 files parsed, 2 failed)
WARNING: 2/20 (10.0%) files failed AST parsing - potential systemic issue
```

## Exclusions

Development artifacts are automatically excluded:

- `.worktrees/` - Git worktrees
- `.venv/`, `venv/`, `.virtualenv/` - Virtual environments
- `__pycache__/`, `*.pyc` - Python cache
- `.git/` - Git internals
- `node_modules/` - JavaScript dependencies

## Formal Properties (Verified in Tests)

**PROP-001** (INVARIANT): Language detection is deterministic
**PROP-002** (SAFETY): Parse failures don't block review (fail-open)
**PROP-003** (PERFORMANCE): AST overhead <5% of review time
**PROP-004** (LIVENESS): Cache file exists before reviewers spawn
**PROP-005** (INVARIANT): Reviewer prompts include disclaimers
**PROP-006** (SAFETY): Development artifacts excluded from analysis

All properties verified with 23 passing tests (100% property coverage).

## Extension Points

### Multi-Language Support

Currently Python-only. Extensible via `language_detection.py`:

```python
def get_language(file_path: Path) -> str:
    """Detect language from file extension."""
    if file_path.suffix == ".py":
        return "python"
    elif file_path.suffix in [".js", ".ts"]:
        return "javascript"  # Future: @typescript-eslint/parser
    elif file_path.suffix == ".go":
        return "go"  # Future: go/ast package
    # ...
```

### Custom Metrics

Add new visitors to `metrics_extractor.py`:

```python
class MyCustomVisitor(ast.NodeVisitor):
    """Extract domain-specific patterns."""
    def visit_ClassDef(self, node):
        # Custom analysis logic
        pass
```

### Per-Project Configuration

Future: `.wfc/ast-config.json`:

```json
{
  "exclude_patterns": ["**/migrations/*.py"],
  "complexity_threshold": 15,
  "dangerous_calls": ["custom_eval_wrapper"],
  "enabled": true
}
```

## Disclaimers and Caveats

**CRITICAL WARNINGS** (included in every cache file):

1. **Presence ≠ Vulnerability**: Importing `subprocess` doesn't mean command injection exists
2. **Complexity ≠ Bad Code**: High cyclomatic complexity may reflect necessary business logic
3. **Hotspots ≠ Findings**: AST flags are investigation starting points, not final verdicts
4. **Context Matters**: Reviewers must read actual code, not just rely on metrics

## Related Documentation

- [Review System](./REVIEW_SYSTEM.md) - Five-agent consensus review
- [Token Management](../references/TOKEN_MANAGEMENT.md) - Token optimization strategy
- [Test Plan](../../plans/plan_ast_metrics_integration_20260222/TEST-PLAN.md) - Comprehensive test coverage
- [Properties](../../plans/plan_ast_metrics_integration_20260222/PROPERTIES.md) - Formal correctness properties

## Implementation Status

✅ **Completed** (2026-02-22):

- Production AST analyzer (`wfc/scripts/ast_analyzer/`)
- Cache writer with fail-open error handling
- Orchestrator integration (pre-review phase)
- Reviewer prompt updates (5 files)
- Comprehensive test suite (23 tests, 100% property coverage)
- Telemetry integration (4 observability metrics)

**Total Implementation Time**: ~6 hours (vs 1.5 weeks planned)
**Reason for Speedup**: Manual implementation after discovering orchestrator bugs

## Usage

AST context is **automatic** - no user action required. When running `/wfc-review`, the system:

1. Detects Python files in changeset
2. Runs AST analysis (<100ms for typical PR)
3. Creates `.wfc-review/.ast-context.json`
4. Spawns reviewers with cache reference
5. Reviewers use metrics as supplemental guidance

Users never interact with AST metrics directly - they're consumed by reviewer agents.

## Troubleshooting

**Q: AST analysis failed for all files**
A: Check Python syntax errors. Review continues without AST context.

**Q: High parse failure rate (>10%)**
A: Systemic issue - check for invalid Python in codebase or excluded directories.

**Q: Reviewers not mentioning AST insights**
A: Expected - AST is supplemental. Reviewers prioritize actual code review.

**Q: Can I disable AST analysis?**
A: Not currently. Fail-open design means failures are silent and non-blocking.
