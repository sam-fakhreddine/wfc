---
title: AST Metrics Integration for WFC Review
status: active
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
tasks_total: 7
tasks_completed: 0
complexity: M
---

## Overview

Integrate AST-based static analysis into wfc-review to provide reviewers with supplemental context. Metrics are extracted before reviewer agents spawn, cached to a shared file, and included as guidance (not directives) in reviewer prompts.

**Key Constraints:**

- Python-only initially (extensible to multi-language later)
- <100ms overhead for typical PR (5-20 files)
- Fail-open if parsing fails (log warning, continue review)
- Metrics are supplemental hints, not replacement for code review

**Success Criteria:**

- 97% token reduction (8000 → 200 tokens per file) with better context
- Zero false negatives (parsing failures don't block reviews)
- Reviewers receive actionable hotspot guidance

---

## TASK-001: Move AST extractor from .development to wfc/scripts/ast_analyzer

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-001]
- **Files**:
  - `.development/ast_metrics_extractor.py` → `wfc/scripts/ast_analyzer/metrics_extractor.py`
  - New: `wfc/scripts/ast_analyzer/__init__.py`
  - New: `wfc/scripts/ast_analyzer/language_detection.py`
- **Description**: Promote the prototype AST metrics extractor to production code under `wfc/scripts/ast_analyzer/`. Add proper imports, docstrings, and type hints. Create `language_detection.py` to identify Python files (extensible for future languages).
- **Acceptance Criteria**:
  - [ ] `wfc/scripts/ast_analyzer/metrics_extractor.py` exists with same logic as prototype
  - [ ] `language_detection.py` provides `is_python(file_path: Path) -> bool`
  - [ ] All code passes `make format` and `make check-all`
  - [ ] No regression in .development prototype (keep for reference)

---

## TASK-002: Create AST cache writer for shared reviewer context

- **Complexity**: S
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-002, PROP-003]
- **Files**:
  - New: `wfc/scripts/ast_analyzer/cache_writer.py`
- **Description**: Create a module that analyzes changed files (via `git diff --name-only`), extracts AST metrics for Python files only, and writes results to `.wfc-review/.ast-context.json`. This file is shared across all reviewer agents. If parsing fails for a file, log warning and skip (fail-open).
- **Acceptance Criteria**:
  - [ ] `write_ast_cache(changed_files: List[Path], output_path: Path) -> Dict` function exists
  - [ ] Filters files to Python-only using `language_detection.is_python()`
  - [ ] Writes JSON with schema: `{"files": [{"file": "path", "metrics": {...}}, ...]}`
  - [ ] Parse failures logged to stderr, do not raise exceptions
  - [ ] Excludes `.worktrees/`, `.venv/`, `__pycache__/` from analysis
  - [ ] Returns parse summary: `{"parsed": N, "failed": M, "duration_ms": X}`

---

## TASK-003: Integrate AST analysis into review orchestrator pre-phase

- **Complexity**: M
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-004]
- **Files**:
  - `wfc/scripts/orchestrators/review/orchestrator.py`
- **Description**: Add a pre-review phase to `orchestrator.py` that runs AST analysis before spawning reviewer agents. This phase:
  1. Gets changed files from git
  2. Calls `cache_writer.write_ast_cache()` to generate `.wfc-review/.ast-context.json`
  3. Measures and logs duration
  4. Continues even if AST analysis fails entirely (fail-open)

Integration point: After review directory setup, before reviewer Task agent spawns.

- **Acceptance Criteria**:
  - [ ] New method `_run_ast_analysis()` in `ReviewOrchestrator` class
  - [ ] Called before `_spawn_reviewers()` method
  - [ ] Logs "AST analysis completed in Xms (N files parsed, M failed)"
  - [ ] If AST analysis crashes, logs error and continues to reviewer spawn
  - [ ] Telemetry tracks AST phase duration separately
  - [ ] Logs warning if >10% of files fail to parse (potential systemic issue)
  - [ ] Telemetry includes `cache_file_size_bytes` for monitoring growth

---

## TASK-004: Update reviewer prompts to include AST context file reference

- **Complexity**: S
- **Dependencies**: [TASK-003]
- **Properties**: [PROP-005]
- **Files**:
  - `wfc/references/reviewers/security/PROMPT.md`
  - `wfc/references/reviewers/correctness/PROMPT.md`
  - `wfc/references/reviewers/performance/PROMPT.md`
  - `wfc/references/reviewers/maintainability/PROMPT.md`
  - `wfc/references/reviewers/reliability/PROMPT.md`
- **Description**: Add a brief note to each reviewer's PROMPT.md instructing them to read `.wfc-review/.ast-context.json` for supplemental context. Emphasize that metrics are **starting points for investigation**, not directives. Include example of what the JSON contains and how to use it.
- **Acceptance Criteria**:
  - [ ] All 5 reviewer prompts mention `.ast-context.json`
  - [ ] Prompts include strong disclaimer: "AST metrics are starting points for investigation. Review the full code and apply your expertise."
  - [ ] Prompts include caveat: "High complexity doesn't mean bad code — investigate context before concluding"
  - [ ] Prompts include caveat: "Metrics may miss domain-specific considerations — apply your expertise"
  - [ ] Prompts explain JSON schema briefly (file path, complexity, hotspots, dangerous imports)
  - [ ] Security reviewer told to focus on `dangerous_imports` and `hotspots` with security issues
  - [ ] Performance reviewer told to focus on `complex_functions` and `max_nesting`

---

## TASK-005: Add tests for AST analyzer components

- **Complexity**: M
- **Dependencies**: [TASK-001, TASK-002]
- **Properties**: [PROP-006]
- **Files**:
  - New: `tests/test_ast_metrics_extractor.py`
  - New: `tests/test_ast_cache_writer.py`
  - New: `tests/test_language_detection.py`
- **Description**: Create unit tests for AST analyzer components. Test both happy path (successful parsing) and failure modes (invalid Python, missing files, unsupported languages).
- **Acceptance Criteria**:
  - [ ] Test `metrics_extractor.analyze_file()` on valid Python file
  - [ ] Test `metrics_extractor.analyze_file()` on invalid Python (should fail gracefully)
  - [ ] Test `cache_writer.write_ast_cache()` creates correct JSON schema
  - [ ] Test cache writer skips non-Python files
  - [ ] Test cache writer logs warnings on parse failures
  - [ ] Test `language_detection.is_python()` returns True for .py files
  - [ ] All tests pass with `uv run pytest tests/test_ast_*.py -v`

---

## TASK-006: Add documentation and update SKILLS.md reference

- **Complexity**: S
- **Dependencies**: [TASK-005]
- **Properties**: []
- **Files**:
  - New: `docs/concepts/AST_CONTEXT.md`
  - `wfc/references/SKILLS.md`
- **Description**: Document the AST metrics feature for future maintainers and users. Explain what metrics are extracted, where they're cached, how reviewers use them, and how to extend to new languages.
- **Acceptance Criteria**:
  - [ ] `docs/concepts/AST_CONTEXT.md` created with:
    - Overview of AST integration
    - Metrics extracted (complexity, nesting, dangerous calls)
    - Performance characteristics (<100ms for typical PR)
    - Fail-open behavior on parse errors
    - Future multi-language extension plan
  - [ ] `SKILLS.md` updated to mention AST context in wfc-review section
  - [ ] Document passes `make check-all` (markdownlint)

---

## TASK-007: Add observability and monitoring for AST analysis

- **Complexity**: S
- **Dependencies**: [TASK-002, TASK-003]
- **Properties**: []
- **Files**:
  - `wfc/scripts/ast_analyzer/cache_writer.py`
  - `wfc/scripts/orchestrators/review/orchestrator.py`
  - New: `.wfc-review/ast-analysis.log`
- **Description**: Add logging and telemetry to track AST metrics usage, parsing performance, and failure rates. This enables monitoring for silent degradation and helps identify systemic issues (e.g., many files failing to parse).
- **Acceptance Criteria**:
  - [ ] `cache_writer.py` logs parsing time per file to `ast-analysis.log`
  - [ ] Orchestrator logs summary: "AST analysis: X files parsed, Y failed, Z ms total"
  - [ ] Telemetry includes `cache_file_size_bytes` for monitoring growth
  - [ ] Log file includes timestamps, file paths, success/failure status
  - [ ] Warning logged if >10% of files fail to parse (potential systemic issue)

---

## Implementation Notes

### Architecture

```
Review Orchestrator
  ↓
1. Setup review directory (.wfc-review/)
2. Get changed files (git diff --name-only)
3. Run AST analysis → .ast-context.json
  ↓
4. Spawn 5 reviewer agents (parallel)
  ↓
5. Reviewers read .ast-context.json for supplemental hints
  ↓
6. Consensus scoring (existing logic)
```

### AST Context JSON Schema

```json
{
  "files": [
    {
      "file": "wfc/skills/wfc-implement/agent.py",
      "lines": 1468,
      "complexity_budget": 124,
      "_note": "📍 Supplemental hints only. Review the full code, not just these flags.",
      "dangerous_imports": ["subprocess"],
      "_imports_note": "⚠️  Verify actual usage. Presence ≠ vulnerability.",
      "hotspots": [
        {"line": 346, "function": "_phase_test_first", "issues": ["dangerous_calls:self._execute_claude_task"]}
      ],
      "_hotspots_note": "💡 Suggested focus areas. Not exhaustive.",
      "complex_functions": [
        {"name": "_phase_submit", "line": 603, "complexity": 10}
      ],
      "_complexity_note": "🔍 High complexity warrants deeper review."
    }
  ],
  "summary": {
    "total_files": 5,
    "parsed": 5,
    "failed": 0,
    "duration_ms": 42
  }
}
```

### Performance Budget

- **Target**: <100ms for 20 files
- **Measured**: 1.27ms per file average (from benchmark)
- **Margin**: 8x safety factor

### Fail-Open Strategy

If AST analysis fails:

1. Log warning to stderr
2. Create empty `.ast-context.json`: `{"files": [], "summary": {"error": "..."}}`
3. Continue to reviewer spawn
4. Reviewers proceed without AST hints (graceful degradation)

### Future Extensions

- **Multi-language support**: Add parsers for JS/TS (esprima), Go (go/ast), Rust (syn)
- **Call graph analysis**: Track function dependencies across files
- **Data flow tracking**: Follow user input → dangerous sinks
- **Caching**: Store AST results per-commit to avoid re-parsing unchanged files
