# Formal Properties: Fix Review Findings

**Goal**: Ensure wfc-prompt-fixer and wfc-doctor skills are production-ready with comprehensive error handling, reliability, and correctness guarantees.

---

## PROP-001: SAFETY - File Operations Must Never Corrupt Data

- **Statement**: File I/O operations (read, write, copy, delete) must never leave filesystem in corrupt state (partial writes, orphaned files, permission errors causing data loss)
- **Rationale**: Critical: Users trust WFC to modify their prompts and configuration safely. Unhandled exceptions during file operations can corrupt workspaces, lose fixes, or delete important files.
- **Priority**: critical
- **Tasks**: TASK-001, TASK-002, TASK-018
- **Observables**: file_operation_failures, partial_writes_detected, workspace_corruption_events
- **Validation**:
  - All file operations wrapped in try/except with specific exception handling
  - Verification checks after critical operations (copy verification)
  - Cleanup operations use ignore_errors=True or catch all exceptions

---

## PROP-002: SAFETY - Workspaces Must Be Cleaned Up On Failure

- **Statement**: When prompt fixing fails (exception, agent error, user cancellation), workspace directories must be cleaned up unless debug mode enabled
- **Rationale**: Critical: Workspaces accumulate disk usage over time. 1000 failed runs = 1000 orphaned directories. In production, this leads to disk full errors.
- **Priority**: critical
- **Tasks**: TASK-001, TASK-002, TASK-018
- **Observables**: orphaned_workspaces_count, disk_usage_mb, cleanup_failures
- **Validation**:
  - try/finally blocks ensure cleanup runs even on exception
  - --keep-workspace flag explicitly disables cleanup for debugging
  - Cleanup failures logged but don't propagate exceptions

---

## PROP-003: SAFETY - User Input Must Be Validated Before Use

- **Statement**: All user-provided inputs (CLI args, glob patterns, file paths) must be validated before use to prevent injection, path traversal, DoS
- **Rationale**: Critical: Unvalidated glob patterns allow path traversal (`../../../../etc/**/*`), DoS (`/**/*` enumerates millions of files), and arbitrary file access. This is a security vulnerability.
- **Priority**: critical
- **Tasks**: TASK-007, TASK-008
- **Observables**: validation_rejections, path_traversal_attempts, dos_patterns_blocked
- **Validation**:
  - Glob patterns restricted to safe directories (wfc/, references/)
  - Patterns rejected if contain ".." or start with "/"
  - File count limit enforced (max 1000 matches)
  - CLI args checked for empty strings, invalid paths, mutually exclusive flags

---

## PROP-004: LIVENESS - Workspace Cleanup Must Eventually Complete

- **Statement**: Workspace cleanup operations must eventually complete (within 60 seconds) or fail gracefully, never hang indefinitely
- **Rationale**: Important: shutil.rmtree() on large directories or network filesystems can hang. Users must not wait forever for cleanup.
- **Priority**: important
- **Tasks**: TASK-001, TASK-002, TASK-018
- **Observables**: cleanup_duration_seconds, cleanup_timeouts, cleanup_success_rate
- **Validation**:
  - Cleanup operations have implicit timeout (shutil operations are bounded by directory size)
  - Use shutil.rmtree(ignore_errors=True) to avoid blocking on permission errors
  - Disk space checked before creation to avoid cleanup of huge directories

---

## PROP-005: LIVENESS - Agent Spawning Must Eventually Return Or Timeout

- **Statement**: All Task tool invocations (Analyzer, Fixer, Reporter) must eventually return a result or raise TimeoutError within configured limits
- **Rationale**: Critical: Agents can hang on malformed prompts, infinite loops, or API issues. Users must not wait indefinitely.
- **Priority**: critical
- **Tasks**: TASK-003, TASK-004, TASK-005
- **Observables**: agent_spawn_duration_seconds, agent_timeouts, agent_success_rate
- **Validation**:
  - Task tool calls include timeout parameter (e.g., 300 seconds for Analyzer)
  - Timeout errors caught and converted to actionable error messages
  - Partial results preserved if timeout occurs during batch processing

---

## PROP-006: INVARIANT - Agent Responses Must Match Expected Schema

- **Statement**: All agent responses (analysis.json, fix_result, report.md) must conform to expected schema before being used by orchestrator
- **Rationale**: Important: Agents can return malformed data due to prompt issues, API errors, or implementation bugs. Orchestrator must validate schema before accessing fields.
- **Priority**: important
- **Tasks**: TASK-003, TASK-004, TASK-005, TASK-009
- **Observables**: schema_validation_failures, missing_fields_detected, agent_response_errors
- **Validation**:
  - validate_analysis_schema() checks for required fields (grade, scores, issues)
  - validate_fix_result_schema() checks for required fields (fixed_prompt, changelog, validation)
  - Missing fields raise ValueError with clear error message
  - .get() with defaults used only for optional fields

---

## PROP-007: INVARIANT - Retry Logic Must Have Bounded Attempts

- **Statement**: Fixer agent retry logic must have finite maximum attempts (2 retries) and exponential backoff to prevent infinite loops
- **Rationale**: Important: Unbounded retries can hang forever on persistent failures. Exponential backoff prevents thundering herd on transient failures.
- **Priority**: important
- **Tasks**: TASK-004
- **Observables**: retry_attempts, backoff_delays_seconds, max_retries_reached
- **Validation**:
  - max_retries=2 enforced (3 total attempts: original + 2 retries)
  - Backoff delay = min(2^attempt, 30) seconds
  - After max_retries, raise exception with clear error message

---

## PROP-008: PERFORMANCE - Batch Mode Must Process Prompts In Parallel

- **Statement**: When processing N prompts in batch mode, execution time must be ~O(1) not O(N) (i.e., 4 prompts in ~1x time via parallelism, not 4x sequential)
- **Rationale**: Important: Users expect batch mode to be fast. Sequential processing defeats the purpose of batch mode.
- **Priority**: important
- **Tasks**: TASK-006
- **Observables**: batch_duration_seconds, prompts_per_second, parallelism_factor
- **Validation**:
  - ThreadPoolExecutor with max_workers=batch_size (4)
  - Performance test: 4 prompts complete in ≤ 1.5x time of single prompt
  - Concurrency limits enforced (no more than batch_size parallel agents)

---

## PROP-009: INVARIANT - Workspace Names Must Be Globally Unique

- **Statement**: Workspace directory names must be globally unique across all invocations (timestamps, random components) to prevent collisions in parallel execution
- **Rationale**: Critical: Parallel batch processing with second-precision timestamps can create identical workspace names, causing file collisions and data corruption.
- **Priority**: critical
- **Tasks**: TASK-006
- **Observables**: workspace_name_collisions, uuid_generation_failures
- **Validation**:
  - Workspace names include microseconds: timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
  - Workspace names include random component: f"{timestamp}-{uuid.uuid4().hex[:8]}"
  - Collision probability < 1 in 1 billion for 1000 concurrent workspaces

---

## PROP-010: SAFETY - CLI Must Reject Invalid Arguments Before Execution

- **Statement**: CLI must validate all arguments (paths, flags, options) and raise actionable errors before orchestrator execution begins
- **Rationale**: Important: Invalid arguments detected late cause wasted work (workspace creation, agent spawning) before failing. Fail-fast principle.
- **Priority**: important
- **Tasks**: TASK-007, TASK-008
- **Observables**: cli_validation_failures, invalid_argument_errors
- **Validation**:
  - Empty path_args raises clear error immediately
  - Mutually exclusive flags (--wfc/--no-wfc) detected before Path creation
  - Invalid paths (ValueError, OSError) caught with try/except
  - File existence checked in non-batch mode before orchestrator init

---

## PROP-011: SAFETY - Glob Patterns Must Not Enumerate Entire Filesystem

- **Statement**: Glob patterns must be restricted to safe directories and have bounded match counts (max 1000) to prevent DoS and unauthorized file access
- **Rationale**: Critical: Unrestricted glob patterns are a security vulnerability. Pattern like `/**/*` can enumerate millions of files, hang the system, or access sensitive data.
- **Priority**: critical
- **Tasks**: TASK-008
- **Observables**: glob_matches_truncated, unsafe_patterns_rejected, glob_enumeration_time_seconds
- **Validation**:
  - Pattern whitelist: must start with wfc/, references/, ./wfc/, ./references/
  - Pattern blacklist: reject if contains ".." or starts with "/"
  - Recursion depth limit: max 2 levels of "**"
  - Match count limit: truncate to first 1000 with warning

---

## PROP-012: INVARIANT - Data Access Must Use Safe Patterns (No Bare Dict Access)

- **Statement**: All dictionary/object field access must use .get() with defaults OR explicit validation before bare access to prevent KeyError/AttributeError
- **Rationale**: Important: Agent responses, JSON parsing, and config loading can have missing fields. Bare access causes cryptic runtime errors.
- **Priority**: important
- **Tasks**: TASK-009, TASK-010
- **Observables**: key_errors_caught, attribute_errors_caught, validation_failures
- **Validation**:
  - analysis.get("grade", "UNKNOWN") with subsequent check if UNKNOWN
  - fix_result.get("changes", []) for optional fields
  - Schema validation functions called before bare access
  - Unit tests verify KeyError handling for all agent responses

---

## PROP-013: LIVENESS - Doctor Checks Must Eventually Complete Or Timeout

- **Statement**: Each doctor health check (skills, prompts, settings, hooks, precommit) must complete within 120 seconds or timeout with clear error
- **Rationale**: Important: Pre-commit can hang on broken hooks. Checks must not block forever.
- **Priority**: important
- **Tasks**: TASK-011, TASK-012, TASK-013, TASK-014
- **Observables**: check_duration_seconds, check_timeouts, check_success_rate
- **Validation**:
  - subprocess calls have explicit timeout=120 parameter
  - TimeoutExpired caught and converted to CheckResult with status="FAIL"
  - Partial results preserved if some checks timeout
  - Overall health check reports timeout details in issues list

---

## PROP-014: SAFETY - Subprocess Must Not Leave Zombie Processes

- **Statement**: When subprocess timeout expires, process and all children must be terminated explicitly (kill + wait) to prevent zombie accumulation
- **Rationale**: Important: subprocess.run() timeout doesn't kill child processes. Pre-commit spawns many children (black, ruff, etc.) which become zombies if parent times out.
- **Priority**: important
- **Tasks**: TASK-014
- **Observables**: zombie_processes_created, subprocess_kill_failures
- **Validation**:
  - Use subprocess.Popen instead of subprocess.run for explicit control
  - On TimeoutExpired: proc.kill() then proc.wait(timeout=5)
  - Process group termination if available (os.killpg)
  - Unit tests verify process cleanup on timeout

---

## PROP-015: PERFORMANCE - Subprocess Must Stream Output Not Buffer

- **Statement**: Long-running subprocess operations (pre-commit) must stream output line-by-line to console, not buffer in memory
- **Rationale**: Important: Buffering 100+ files worth of pre-commit output consumes excessive memory and provides no user feedback (appears hung)
- **Priority**: important
- **Tasks**: TASK-014
- **Observables**: subprocess_memory_usage_mb, output_streaming_enabled
- **Validation**:
  - Use subprocess.Popen with stdout=PIPE
  - Iterate over proc.stdout line-by-line: for line in proc.stdout: print(line, end='')
  - Memory usage stays constant regardless of output volume
  - User sees real-time progress (hook names as they run)

---

## PROP-016: INVARIANT - Code Must Have Consistent Documentation

- **Statement**: All public APIs must have comprehensive docstrings (Args, Returns, Raises). All magic numbers must be named constants with rationale comments.
- **Rationale**: Important: Maintainability and onboarding. Future developers need to understand why batch_size=4, max_retries=2, timeout=120.
- **Priority**: important
- **Tasks**: TASK-015, TASK-017
- **Observables**: docstring_coverage_percent, undocumented_magic_numbers
- **Validation**:
  - All public methods have Google-style docstrings
  - All numeric literals extracted to module constants
  - Constants have inline comments explaining rationale
  - Documentation linter (pydocstyle) passes

---

## PROP-017: INVARIANT - Test Coverage Must Exceed 75% For Critical Modules (85% Stretch Goal)

- **Statement**: Orchestrator and workspace modules must have ≥75% line coverage initially, with 85% as stretch goal. Coverage must include error paths, edge cases, and integration scenarios.
- **Rationale**: Critical: Review identified that bugs would not be caught by current structural-only tests. Functional tests are mandatory for production readiness. 75% initial target reduces timeline pressure while maintaining excellent coverage (12% → 75% = +63% improvement). 85% achievable incrementally.
- **Priority**: critical
- **Tasks**: TASK-016
- **Observables**: test_coverage_percent, untested_error_paths, integration_test_count
- **Validation**:
  - pytest-cov reports ≥75% coverage for orchestrator.py and workspace.py (initial), ≥85% (stretch)
  - All exception handlers have corresponding test cases
  - Edge cases tested (empty files, malformed JSON, permission errors, disk full)
  - Integration tests spawn real agents (not mocked Task tool)

---

## Property Summary

| Type | Count | Critical | Important |
|------|-------|----------|-----------|
| SAFETY | 6 | 4 | 2 |
| LIVENESS | 3 | 1 | 2 |
| INVARIANT | 6 | 1 | 5 |
| PERFORMANCE | 2 | 0 | 2 |
| **TOTAL** | **17** | **6** | **11** |

---

## Critical Properties (Must Satisfy Before Merge)

1. **PROP-001**: File operations never corrupt data
2. **PROP-002**: Workspaces cleaned up on failure
3. **PROP-003**: User input validated before use
4. **PROP-005**: Agent spawning returns or times out
5. **PROP-009**: Workspace names globally unique
6. **PROP-011**: Glob patterns restricted to safe directories
7. **PROP-017**: Test coverage ≥75% (85% stretch goal)

---

## Observable Metrics

All properties include suggested observables for runtime monitoring. These can be implemented in future via wfc-observe skill.

**Example observables**:

- `file_operation_failures` (counter): Tracks FileNotFoundError, PermissionError, OSError
- `agent_spawn_duration_seconds` (histogram): Distribution of agent execution times
- `workspace_name_collisions` (counter): Detects UUID collision (should be 0)
- `test_coverage_percent` (gauge): Current coverage from pytest-cov

These observables map to concrete metrics collectors once wfc-observe generates instrumentation.
