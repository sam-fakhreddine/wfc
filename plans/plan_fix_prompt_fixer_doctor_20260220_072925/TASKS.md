---
title: Fix wfc-prompt-fixer and wfc-doctor Review Findings
status: active
created: 2026-02-20T07:29:25Z
updated: 2026-02-20T07:32:00Z
tasks_total: 19
tasks_completed: 0
complexity: L
---

# Implementation Tasks: Fix Review Findings (CS=7.8)

**Goal**: Complete all TODO implementations and fix critical reliability/correctness issues identified in PR #46 consensus review.

**Context**: PR #46 introduced wfc-prompt-fixer and wfc-doctor skills with good architecture but incomplete implementation (10+ TODOs), missing error handling, no cleanup on failures, and inadequate test coverage. Review CS=7.8 (Important tier) blocks merge.

---

## TASK-001: Add comprehensive error handling to workspace.py

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-001, PROP-002, PROP-003]
- **Files**: wfc/skills/wfc-prompt-fixer/workspace.py
- **Description**: Wrap all file I/O operations (lines 72, 119-122, 128, 134-136, 142, 154, 178) in try/except blocks with specific exception handling for FileNotFoundError, PermissionError, OSError. Add custom WorkspaceError exception class.
- **Acceptance Criteria**:
  - [ ] Custom WorkspaceError exception class created in workspace.py
  - [ ] All shutil.copy() calls wrapped with try/except
  - [ ] All read_text()/write_text() calls wrapped with try/except
  - [ ] cleanup() method uses shutil.rmtree(workspace, ignore_errors=True) OR catches OSError
  - [ ] Error messages include actionable feedback (e.g., "Check file permissions")
  - [ ] Unit tests verify exception handling (test_workspace_error_handling.py)

---

## TASK-002: Implement try/finally cleanup in orchestrator

- **Complexity**: M
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-002, PROP-004]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py
- **Description**: Add try/finally blocks to fix_prompt() and fix_batch() methods (lines 48-112) to ensure workspace cleanup on exception. Add --keep-workspace debug flag.
- **Acceptance Criteria**:
  - [ ] fix_prompt() has try/finally block with workspace cleanup
  - [ ] fix_batch() has try/finally block for each prompt's workspace
  - [ ] CLI accepts --keep-workspace flag
  - [ ] Cleanup only skipped if --keep-workspace OR success
  - [ ] Unit tests verify cleanup on exception paths

---

## TASK-003A: Prototype agent spawning with Task tool (SPIKE)

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-005]
- **Files**: experiments/task_tool_spike.py (new)
- **Description**: 1-day spike to validate Task tool integration works as expected before full implementation. Create minimal prototype that spawns Analyzer agent with simple prompt, verifies response parsing, and validates timeout behavior.
- **Acceptance Criteria**:
  - [ ] Prototype script successfully calls Task tool with subagent_type="general-purpose"
  - [ ] Agent receives prompt and returns structured response
  - [ ] Timeout parameter works (test with 30s limit)
  - [ ] Response JSON parsing works
  - [ ] Document findings in experiments/task_tool_spike_results.md
  - [ ] Decision: proceed with full implementation OR pivot if blockers found

---

## TASK-003: Implement agent spawning via Task tool (Analyzer)

- **Complexity**: L
- **Dependencies**: [TASK-001, TASK-003A]
- **Properties**: [PROP-005, PROP-006]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:184-223
- **Description**: Replace TODO at line 199-200 with actual Task tool invocation to spawn Analyzer subagent. Pass workspace path and wfc_mode flag. Parse returned analysis.json. (Blocked on TASK-003A prototype validation)
- **Acceptance Criteria**:
  - [ ] _spawn_analyzer() uses Task tool with subagent_type="general-purpose"
  - [ ] Agent prompt loaded from agents/analyzer.md
  - [ ] Workspace path passed to agent via prompt context
  - [ ] wfc_mode flag enables WFC-specific antipattern checks
  - [ ] Returned analysis.json validated against expected schema (grade, scores, issues)
  - [ ] Integration test spawns real analyzer agent

---

## TASK-004: Implement agent spawning via Task tool (Fixer)

- **Complexity**: L
- **Dependencies**: [TASK-003]
- **Properties**: [PROP-005, PROP-006, PROP-007]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:225-261
- **Description**: Replace TODO at lines 242-243 with actual Task tool invocation to spawn Fixer subagent with retry logic (max 2 attempts). Implement exponential backoff between retries.
- **Acceptance Criteria**:
  - [ ] _spawn_fixer_with_retry() uses Task tool with subagent_type="general-purpose"
  - [ ] Agent prompt loaded from agents/fixer.md
  - [ ] Retry loop implements exponential backoff (2^attempt seconds, max 30s)
  - [ ] Validation results from fixer checked before returning
  - [ ] Returned fix_result validated against schema (fixed_prompt, changelog, unresolved, validation)
  - [ ] Integration test verifies retry logic on validation failure

---

## TASK-005: Implement agent spawning via Task tool (Reporter)

- **Complexity**: M
- **Dependencies**: [TASK-004]
- **Properties**: [PROP-005]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:263-318
- **Description**: Replace TODOs at lines 265, 291, 317-318 with actual Task tool invocation to spawn Reporter subagent. Handle both "no changes" and "changes applied" paths.
- **Acceptance Criteria**:
  - [ ] _skip_to_reporter() spawns Reporter with no-changes flag
  - [ ] _spawn_reporter() spawns Reporter with fix results
  - [ ] Agent prompt loaded from agents/reporter.md
  - [ ] Reporter generates markdown report with all sections
  - [ ] _create_pr() implemented to create branch, commit, push, gh pr create (if auto_pr=True)
  - [ ] Integration test verifies full pipeline (Analyzer → Fixer → Reporter)

---

## TASK-006: Implement parallel batch processing

- **Complexity**: L
- **Dependencies**: [TASK-005]
- **Properties**: [PROP-008, PROP-009]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:143-154
- **Description**: Replace TODO at line 147 with actual parallel execution using concurrent.futures.ThreadPoolExecutor (batch_size=4). Update workspace naming to include microseconds + random component.
- **Acceptance Criteria**:
  - [ ] fix_batch() uses ThreadPoolExecutor with max_workers=batch_size
  - [ ] Workspace naming includes microseconds: f"{timestamp}-{uuid.uuid4().hex[:8]}"
  - [ ] Failed prompts tracked separately from successful ones
  - [ ] Error handling preserves partial results (don't fail entire batch on single error)
  - [ ] Performance test verifies 4 prompts run in ~1x time (not 4x)

---

## TASK-007: Add input validation to CLI

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-003, PROP-010]
- **Files**: wfc/skills/wfc-prompt-fixer/cli.py:34-43
- **Description**: Validate path_args before creating Path object. Check for empty strings, mutually exclusive flags (--wfc/--no-wfc), file existence in non-batch mode, and path length limits.
- **Acceptance Criteria**:
  - [ ] Empty path_args raises clear error message
  - [ ] --wfc and --no-wfc mutually exclusive (error if both set)
  - [ ] Path().resolve() wrapped in try/except for invalid paths
  - [ ] File existence checked before processing (non-batch mode)
  - [ ] Unit tests verify all validation error paths

---

## TASK-008: Add glob pattern validation

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-003, PROP-010, PROP-011]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:131-136
- **Description**: Validate glob patterns in fix_batch() before passing to glob.glob(). Restrict to safe directories, prevent parent traversal, limit recursion depth, cap match count at 1000.
- **Acceptance Criteria**:
  - [ ] Pattern must start with safe prefix (wfc/, references/, ./wfc/, ./references/)
  - [ ] Pattern rejected if contains ".." or starts with "/"
  - [ ] Pattern rejected if more than 2 levels of "**" (recursive depth limit)
  - [ ] If matches > 1000 files, truncate to first 1000 with warning
  - [ ] Use pathlib.Path.glob() instead of glob.glob() for better path handling
  - [ ] Unit tests verify all validation rejections

---

## TASK-009: Fix unsafe dictionary access

- **Complexity**: S
- **Dependencies**: [TASK-003, TASK-004]
- **Properties**: [PROP-012]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:73,254,258
- **Description**: Replace analysis["grade"], fix_result["changes"], fix_result["verdict"] with .get() or explicit validation. Add schema validation for agent response dicts.
- **Acceptance Criteria**:
  - [ ] analysis.get("grade", "UNKNOWN") with validation if UNKNOWN
  - [ ] fix_result.get("changes", []) with default empty list
  - [ ] fix_result.get("verdict", "UNKNOWN") with validation
  - [ ] Add validate_analysis_schema() helper function
  - [ ] Add validate_fix_result_schema() helper function
  - [ ] Unit tests verify KeyError handling

---

## TASK-010: Fix wfc_mode detection logic bug

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-012]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py:177-182
- **Description**: Fix YAML frontmatter detection to verify closing "---" delimiter and prevent false positives. Add @lru_cache for performance. Limit file read to 10KB max.
- **Acceptance Criteria**:
  - [ ] Verify closing delimiter: content.find("\n---\n", 4) != -1
  - [ ] Check "name:" is between opening/closing delimiters
  - [ ] Use limited file read: with open(path) as f: f.read(10000)
  - [ ] Add @lru_cache(maxsize=128) decorator for memoization
  - [ ] Handle UnicodeDecodeError gracefully (return False)
  - [ ] Unit tests verify edge cases (missing delimiter, name in code block, binary files)

---

## TASK-011: Implement doctor check modules (SkillsChecker)

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-013]
- **Files**: wfc/skills/wfc-doctor/checks/skills_check.py:36-38
- **Description**: Replace TODOs with actual validation logic: run skills-ref validate, count wfc-* skills (should be 30), validate frontmatter format, check for deprecated fields.
- **Acceptance Criteria**:
  - [ ] Run `skills-ref validate` via subprocess if installed
  - [ ] Count skills in ~/.claude/skills/wfc-* (glob pattern)
  - [ ] Validate expected count is 30 (warn if mismatch)
  - [ ] Parse YAML frontmatter from SKILL.md files
  - [ ] Check for deprecated fields (user-invocable, disable-model-invocation, argument-hint)
  - [ ] Auto-fix: remove deprecated fields if --fix flag set
  - [ ] Unit tests with mock filesystem

---

## TASK-012: Implement doctor check modules (PromptsChecker)

- **Complexity**: M
- **Dependencies**: [TASK-011]
- **Properties**: [PROP-013]
- **Files**: wfc/skills/wfc-doctor/checks/prompts_check.py:28-30
- **Description**: Replace TODOs with delegation to wfc-prompt-fixer in batch mode. Parse results and extract grade distribution.
- **Acceptance Criteria**:
  - [ ] Call `wfc-prompt-fixer --batch --wfc wfc/skills/*/SKILL.md` via subprocess
  - [ ] Also check wfc/references/reviewers/*/PROMPT.md
  - [ ] Parse output to extract grade distribution (count of A/B/C/D/F)
  - [ ] Flag prompts with grade < B as issues
  - [ ] Auto-fix: apply fixes if --fix flag set (call with --auto-pr)
  - [ ] Unit tests with mocked wfc-prompt-fixer output

---

## TASK-013: Implement doctor check modules (SettingsChecker)

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-013]
- **Files**: wfc/skills/wfc-doctor/checks/settings_check.py:37-39
- **Description**: Replace TODOs with validation logic for ~/.claude/settings.json: validate hook matchers (reject "Task" in context_monitor), check permission modes, detect common misconfigurations.
- **Acceptance Criteria**:
  - [ ] Validate JSON syntax with split read/parse for better errors
  - [ ] Check hook matchers: "Task" should NOT be in context_monitor matcher
  - [ ] Validate permission_mode exists and is valid value
  - [ ] Auto-fix: correct common matcher errors (remove "Task")
  - [ ] Auto-fix: fix JSON syntax if possible
  - [ ] Unit tests with various invalid settings.json files

---

## TASK-014: Improve subprocess handling in PrecommitChecker

- **Complexity**: M
- **Dependencies**: []
- **Properties**: [PROP-014, PROP-015]
- **Files**: wfc/skills/wfc-doctor/checks/precommit_check.py:44-58
- **Description**: Replace subprocess.run with Popen for streaming output. Add explicit proc.kill() and proc.wait() on timeout. Include stderr in issue messages.
- **Acceptance Criteria**:
  - [ ] Use subprocess.Popen instead of subprocess.run
  - [ ] Stream output line-by-line to console (print(line, end=''))
  - [ ] On TimeoutExpired: proc.kill() then proc.wait(timeout=5)
  - [ ] Capture stderr and include in issue message (first 200 chars)
  - [ ] Better parsing of pre-commit output (parse hook failures)
  - [ ] Unit tests with mocked subprocess

---

## TASK-015: Move CheckResult to types.py module

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-016]
- **Files**: wfc/skills/wfc-doctor/types.py (new), wfc/skills/wfc-doctor/orchestrator.py, wfc/skills/wfc-doctor/checks/*.py
- **Description**: Eliminate TYPE_CHECKING circular import pattern by moving CheckResult and HealthCheckResult dataclasses to dedicated types.py module.
- **Acceptance Criteria**:
  - [ ] Create wfc/skills/wfc-doctor/types.py
  - [ ] Move CheckResult dataclass to types.py
  - [ ] Move HealthCheckResult dataclass to types.py
  - [ ] Update orchestrator.py to import from .types
  - [ ] Update all 5 check modules to import from .types (remove TYPE_CHECKING)
  - [ ] All tests pass with new import structure

---

## TASK-016: Add comprehensive functional tests

- **Complexity**: L
- **Dependencies**: [TASK-001, TASK-002, TASK-003, TASK-004, TASK-005]
- **Properties**: [PROP-017]
- **Files**: tests/test_prompt_fixer_functional.py (new), tests/test_doctor_functional.py (new)
- **Description**: Expand test coverage beyond structural tests to include functional tests for orchestrators, error paths, edge cases (empty files, malformed JSON, large files).
- **Acceptance Criteria**:
  - [ ] Test orchestrator.fix_prompt() full pipeline with mocked agents
  - [ ] Test orchestrator.fix_batch() parallel execution
  - [ ] Test workspace error handling (missing files, permission errors)
  - [ ] Test CLI validation (empty args, invalid paths, mutually exclusive flags)
  - [ ] Test glob pattern validation (all rejection cases)
  - [ ] Test doctor check modules with various invalid inputs
  - [ ] Test cleanup on exception paths
  - [ ] Coverage target: 85%+ for orchestrator and workspace modules

---

## TASK-017: Add docstrings and magic number constants

- **Complexity**: S
- **Dependencies**: []
- **Properties**: [PROP-016]
- **Files**: wfc/skills/wfc-prompt-fixer/orchestrator.py, wfc/skills/wfc-doctor/orchestrator.py
- **Description**: Add comprehensive docstrings to all public methods. Extract magic numbers (4 for batch_size, 2 for max_retries, 120 for subprocess timeout) to named constants.
- **Acceptance Criteria**:
  - [ ] All public methods have Google-style docstrings with Args/Returns/Raises
  - [ ] Private methods have minimal docstrings explaining purpose
  - [ ] Extract constants: DEFAULT_BATCH_SIZE = 4, MAX_FIXER_RETRIES = 2, PRECOMMIT_TIMEOUT = 120
  - [ ] Constants include rationale comments (e.g., "# Optimal parallelism for 200k token budget")
  - [ ] Complex methods (_spawn_fixer_with_retry, fix_batch) have Examples section in docstring

---

## TASK-018: Add disk space check and verification

- **Complexity**: S
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-004]
- **Files**: wfc/skills/wfc-prompt-fixer/workspace.py:48-82
- **Description**: Add disk space check before workspace creation (require 1GB free). Add post-copy verification for shutil.copy() to detect partial writes.
- **Acceptance Criteria**:
  - [ ] Check shutil.disk_usage() before create() (require 1GB free)
  - [ ] Raise RuntimeError with clear message if insufficient space
  - [ ] After shutil.copy(), verify dest.stat().st_size == src.stat().st_size
  - [ ] Raise RuntimeError if copy verification fails
  - [ ] Unit tests mock disk_usage to test low-space condition
  - [ ] Unit tests verify copy verification logic

---

## Task Dependency Graph

```
TASK-003A (prototype spike) [independent, must run first]

TASK-001 (error handling)
    ├── TASK-002 (try/finally cleanup)
    ├── TASK-003 (Analyzer agent) ← TASK-003A
    │   └── TASK-004 (Fixer agent)
    │       └── TASK-005 (Reporter agent)
    │           └── TASK-006 (parallel batch)
    ├── TASK-016 (functional tests)
    └── TASK-018 (disk space check)

TASK-007 (CLI validation) [independent]
TASK-008 (glob validation) [independent]
TASK-009 (dict access) ← TASK-003, TASK-004
TASK-010 (wfc_mode detection) [independent]

TASK-011 (SkillsChecker)
    └── TASK-012 (PromptsChecker)

TASK-013 (SettingsChecker) [independent]
TASK-014 (PrecommitChecker) [independent]
TASK-015 (types.py refactor) [independent]
TASK-017 (docstrings) [independent]
```

## Implementation Order (Recommended)

**Phase 0: Risk Reduction (De-risk unknowns)**
0. TASK-003A (prototype agent spawning - 1 day spike)

**Phase 1: Foundation (Error Handling & Validation)**

1. TASK-001 (error handling workspace.py)
2. TASK-007 (CLI validation)
3. TASK-008 (glob validation)
4. TASK-010 (wfc_mode detection)
5. TASK-015 (types.py refactor)

**Phase 2: Core Features (Agent Spawning)**
6. TASK-002 (try/finally cleanup)
7. TASK-003 (Analyzer agent)
8. TASK-009 (dict access - now that agents return data)
9. TASK-004 (Fixer agent)
10. TASK-005 (Reporter agent + PR creation)

**Phase 3: Advanced Features (Parallelism & Checks)**
11. TASK-006 (parallel batch)
12. TASK-011 (SkillsChecker)
13. TASK-012 (PromptsChecker)
14. TASK-013 (SettingsChecker)
15. TASK-014 (PrecommitChecker)

**Phase 4: Polish (Tests & Documentation)**
16. TASK-016 (functional tests)
17. TASK-017 (docstrings)
18. TASK-018 (disk space check)

---

## PR Phasing Strategy (Recommended)

For faster feedback cycles and incremental merge, consider splitting into 3 PRs:

### PR #1: Foundation (Review Unblock) - ~20 hours

**Goal**: Fix critical reliability issues, unblock merge
**Tasks**: TASK-003A, TASK-001, TASK-002, TASK-007, TASK-008, TASK-010, TASK-015
**Benefits**:

- Addresses 50% of review findings (error handling, input validation, cleanup)
- Provides stable foundation for features
- Unblocks other work that depends on these skills
- Small PR = faster review cycle

### PR #2: Core Features (Agent Spawning) - ~30 hours

**Goal**: Complete agent spawning implementation
**Tasks**: TASK-003, TASK-004, TASK-005, TASK-009
**Benefits**:

- Delivers core functionality (3-agent pipeline works end-to-end)
- Builds on stable foundation from PR #1
- Isolated scope = easier to review agent integration

### PR #3: Complete (Advanced + Tests) - ~25 hours

**Goal**: Add parallel batch, doctor checks, comprehensive tests
**Tasks**: TASK-006, TASK-011, TASK-012, TASK-013, TASK-014, TASK-016, TASK-017, TASK-018
**Benefits**:

- Completes all review findings
- Reaches 75-85% test coverage
- Performance optimizations (parallel batch) on proven foundation

**Trade-offs**: 3x PR overhead (CI runs, review time, merge conflicts) vs faster feedback

---

## Complexity Summary

- **S (Small)**: 7 tasks (1-2 hours each) - includes TASK-003A spike
- **M (Medium)**: 8 tasks (3-4 hours each)
- **L (Large)**: 4 tasks (5-8 hours each)

**Total Estimated Effort**: ~68-83 hours (2-3 weeks for 1 developer, including 1-day spike)

---

## Files Affected

**New Files**:

- tests/test_prompt_fixer_functional.py
- tests/test_doctor_functional.py
- tests/test_workspace_error_handling.py
- wfc/skills/wfc-doctor/types.py

**Modified Files**:

- wfc/skills/wfc-prompt-fixer/workspace.py
- wfc/skills/wfc-prompt-fixer/orchestrator.py
- wfc/skills/wfc-prompt-fixer/cli.py
- wfc/skills/wfc-doctor/orchestrator.py
- wfc/skills/wfc-doctor/checks/skills_check.py
- wfc/skills/wfc-doctor/checks/prompts_check.py
- wfc/skills/wfc-doctor/checks/settings_check.py
- wfc/skills/wfc-doctor/checks/hooks_check.py
- wfc/skills/wfc-doctor/checks/precommit_check.py
- tests/test_prompt_fixer.py
- tests/test_doctor.py
