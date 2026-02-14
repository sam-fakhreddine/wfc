# WFC Code Analysis Report

**Date:** 2026-02-14
**Analyst:** Claude Code (Opus 4.6)
**Scope:** Full codebase — code quality, security, testing, architecture

---

## Summary

| Dimension | High | Medium | Low | Total |
|-----------|------|--------|-----|-------|
| Code Quality | 4 | 13 | 7 | 24 |
| Security | 3 | 5 | 9 | 17 |
| Test Suite | 3 | 5 | 3 | 11 |
| Architecture | 2 | 4 | 4 | 10 |
| **Totals** | **12** | **27** | **23** | **62** |

---

## High Severity

### H-01 — Shell Injection Risk in CLI

**Where:** `wfc/cli.py` — the `run_command()` utility function

**What:** Commands are passed as strings through a shell interpreter rather than as safe argument lists. Directory names discovered through filesystem scanning are interpolated directly into those strings.

**Why it matters:** If a maliciously named directory exists in the skills folder (e.g., one containing shell metacharacters), the shell would interpret and execute the embedded command. This is a well-known injection class (CWE-78) that can lead to arbitrary code execution.

**Fix needed:** Switch from shell string execution to list-based argument passing so the operating system treats each argument literally, not as a shell expression.

---

### H-02 — Core Implementation Engine Has Zero Test Coverage

**Where:** `tests/test_implement_e2e.py`, `tests/test_implement_integration.py`

**What:** All tests for the multi-agent parallel implementation engine (the project's flagship feature) fail because they import from a module path that doesn't exist. The skill directory uses hyphens (`wfc-implement`) but Python import statements use dots and cannot resolve hyphenated directory names.

**Why it matters:** The implementation engine — agent orchestration, merge with rollback, TDD workflow, task parsing — is completely untested in practice. Any regression or bug in this system would go undetected. This undermines the project's claim of ">80% coverage" for the implementation system.

**Fix needed:** Either rename the directory to use underscores or use Python's `importlib` for dynamic imports (which `test_plugin_integration.py` already does successfully as a reference).

---

### H-03 — Split Git Tooling Across Two Incompatible Directories

**Where:** `wfc/wfc-tools/gitwork/` and `wfc/wfc_tools/gitwork/`

**What:** Git operations are split across two directories — one hyphenated (not importable by Python) containing the bulk of git APIs (branch, commit, merge, rollback, worktree), and one underscored (importable) containing PR operations and git hooks. They are not duplicates; they are two halves of the same system living in incompatible locations.

**Why it matters:** Developers working on git operations have to know which half lives where. The hyphenated directory cannot be imported normally, so any code that needs both PR operations AND branch management has to use workarounds. Missing `__init__.py` files in the importable directory compound this — some imports may work by accident in development but fail in production.

**Fix needed:** Merge both directories into a single `wfc_tools/` package with proper Python package structure throughout.

---

### H-04 — Git Hook Installer Allows Arbitrary File Writes

**Where:** `wfc/wfc-tools/gitwork/api/hooks.py`

**What:** The hook installation function accepts a hook type name and script content with no validation. The hook type is used directly as a file path component, and the script content is written as-is with executable permissions.

**Why it matters:** A path traversal in the hook type (e.g., `../../.profile`) would write an executable file anywhere the user has permissions, not just inside `.git/hooks/`. Since the script content is also unvalidated, this is effectively an arbitrary file write primitive with execute permissions.

**Fix needed:** Validate the hook type against a whitelist of known git hook names. Reject any input containing path separators or parent directory references.

---

### H-05 — Fragile Runtime Import Path Manipulation

**Where:** 11 files across the codebase

**What:** Eleven files use `sys.path.insert()` to add `~/.claude/skills/wfc` to the Python import path at runtime so they can import modules from the installed skills location.

**Why it matters:** This creates location-dependent code that breaks if the user has a non-standard home directory, hasn't run the installer, or runs in a container with a different filesystem layout. It also makes import ordering unpredictable — different modules can shadow each other depending on which `sys.path.insert` runs first. This is the single most pervasive structural issue in the codebase.

**Fix needed:** Restructure the package so all imports use standard Python package paths. Use editable installs during development instead of runtime path manipulation.

---

### H-06 — Safety Property Tests Can Pass Without Asserting Anything

**Where:** `tests/test_build_orchestrator.py`, `tests/test_build_integration.py`

**What:** Eight tests that verify critical safety properties (quality gates always run, consensus review always happens, TDD is enforced) wrap their assertions in `if` conditionals. If the result dictionary doesn't contain the expected key, the assertion is skipped and the test passes.

**Why it matters:** These tests are supposed to guarantee that safety-critical properties hold. If they silently pass when the property can't even be checked, you get false confidence — the CI pipeline shows green, but no property was actually verified. This defeats the purpose of having safety property tests.

**Fix needed:** Make assertions unconditional. If the expected data is missing, the test should fail — not skip silently.

---

### H-07 — Two Separate Implementations Per Skill

**Where:** `wfc/scripts/skills/` vs `wfc/skills/wfc-*/`

**What:** Three skills (build, review, vibe) have implementations in two different locations. The versions in `wfc/scripts/skills/` are what tests import and validate. The versions in `wfc/skills/wfc-*/` are what gets installed and what users actually run. In some cases these are completely different classes with different behavior.

**Why it matters:** Tests pass against one implementation while users run a different one. Changes to the installed version won't cause test failures, and changes to the tested version won't affect what users experience. This breaks the fundamental promise of testing — that passing tests mean production code works.

**Fix needed:** Establish one canonical location per skill. Have tests and installations reference the same code.

---

### H-08 — Skill Name Mismatch Between Directory and Metadata

**Where:** `wfc/skills/wfc-review/SKILL.md`

**What:** The review skill's directory is named `wfc-review` but its frontmatter metadata declares the name as `wfc-consensus-review`. This is the only skill in the system where these two don't match.

**Why it matters:** The Agent Skills validation system, the installer script, and the documentation all reference skills by name. When the directory name and the declared name disagree, any system that looks up skills by one method will fail to find them by the other. Documentation tells users to invoke `/wfc-review` while the skill itself expects `/wfc-consensus-review`.

**Fix needed:** Align the frontmatter name with the directory name (or vice versa).

---

## Medium Severity

### M-01 — Boolean Logic Bug in Token Manager

**Where:** `wfc/scripts/personas/token_manager.py`

**What:** A conditional check for docstring markers has an operator precedence error. One of the two string checks applies regardless of whether the code is inside a function, causing incorrect docstring detection at the module level.

**Why it matters:** The token manager is responsible for condensing Python files to fit within token budgets. Incorrect docstring detection means some files may be condensed incorrectly — either keeping content that should be removed or removing content that should be kept. This affects the quality of code context sent to review personas.

---

### M-02 — Confidence Scores Are Artificially Inflated

**Where:** `wfc/scripts/confidence_checker.py`

**What:** The dependency assessment function always returns "clear" regardless of whether dependencies are actually resolvable. This contributes 15 points that are always awarded to every confidence score.

**Why it matters:** The confidence checker is designed to decide whether an agent should proceed (>=90%), ask for guidance (70-89%), or stop (<70%). Inflated scores mean agents proceed confidently when they shouldn't, potentially producing low-quality implementations on tasks with unresolved dependencies.

---

### M-03 — Review Agents Are Hardcoded Stubs

**Where:** `wfc/scripts/skills/review/agents.py`

**What:** All four review agents (Code Review, Security, Performance, Complexity) return hardcoded scores without performing any analysis. The scores are always 8.5, 9.0, 8.0, and 9.5 respectively.

**Why it matters:** The consensus review system is marketed as a multi-agent quality gate where diverse expert perspectives catch issues. If the agents never actually analyze code, the consensus is meaningless — every review passes with the same predetermined scores. The quality gate is a formality, not a safeguard.

---

### M-04 — Duplicate Prompt Template Code

**Where:** `wfc/scripts/personas/token_manager.py`, `wfc/scripts/personas/ultra_minimal_prompts.py`

**What:** Nearly identical prompt templates exist in two separate files. Both define how to construct ultra-minimal persona prompts, but they're maintained independently.

**Why it matters:** When a prompt template needs updating, both locations must be changed in sync. Forgetting one creates inconsistent persona behavior. This is a classic DRY (Don't Repeat Yourself) violation that increases maintenance burden.

---

### M-05 — Predictable Temp File Enables Local Attacks

**Where:** `wfc/scripts/hooks/hook_state.py`

**What:** Hook state is stored in a temp file with a predictable name based on the parent process ID. Any local user can predict the filename.

**Why it matters:** An attacker with local access could create a symbolic link at the predicted path pointing to a sensitive file. When the hook writes its state data, it would overwrite the target of the symlink instead. This is a classic symlink attack (CWE-377) that could corrupt arbitrary files.

---

### M-06 — Git Commands Accept Unsanitized Arguments

**Where:** `wfc/wfc-tools/gitwork/api/branch.py`, `commit.py`, `worktree.py`

**What:** Branch names, task IDs, and file paths are passed to git commands without validation. No checks prevent arguments starting with dashes (interpreted as flags by git) or containing path traversal sequences.

**Why it matters:** A task ID containing `../` could create worktrees outside the expected directory. A branch name starting with `-` could be interpreted as a git flag rather than a ref name. While the risk is lower than shell injection (these use list-based subprocess calls), git-specific argument injection is a known attack class.

---

### M-07 — Test Command From Config File Can Execute Arbitrary Code

**Where:** `wfc/skills/wfc-implement/merge_engine.py`

**What:** The integration test command is read from a project-local config file and executed. Anyone who can modify this config file controls what command the merge engine runs.

**Why it matters:** In a team repository, a malicious contributor could submit a PR that modifies the config file to execute arbitrary code whenever the merge engine runs integration tests. Since this runs in the context of the WFC agent (which may have broad filesystem access), the blast radius could be significant.

---

### M-08 — Security Bypasses Are Silent

**Where:** `wfc/scripts/hooks/pretooluse_hook.py`, `security_hook.py`, `rule_engine.py`

**What:** All three security hook layers catch all exceptions and silently allow the action to proceed. No logging, metrics, or alerts are generated when a bypass occurs.

**Why it matters:** If a bug or crafted input causes the security hook to crash, the action is allowed without anyone knowing the security check was skipped. In a security system, silent failures are the most dangerous kind — you can't fix what you can't see. Adding even basic logging would transform this from a blind spot into a detectable event.

---

### M-09 — User-Controlled Regex Patterns Can Hang the System

**Where:** `wfc/scripts/hooks/security_hook.py`

**What:** Security patterns from JSON config files and user-defined rule files are compiled and executed as regular expressions. No validation prevents patterns that cause catastrophic backtracking (ReDoS).

**Why it matters:** A carefully crafted regex can cause the pattern matcher to take exponential time, effectively hanging the security hook process. Combined with the fail-open architecture (M-08), the hook process would eventually be killed and the security check bypassed entirely. This creates an attacker-controllable security bypass.

---

### M-10 — Hardcoded Version String

**Where:** `wfc/cli.py`

**What:** The version is hardcoded as `"0.1.0"` in the CLI, duplicating the version in `pyproject.toml`.

**Why it matters:** When the version is bumped in `pyproject.toml`, the CLI will still report the old version unless someone remembers to update it separately. Users and CI pipelines relying on `wfc --version` will get stale information.

---

### M-11 — CLI Violates Its Own UV Rules

**Where:** `wfc/cli.py`

**What:** The project's own CLAUDE.md mandates using `uv run pytest` and `uv run python` for all Python operations, but the CLI uses bare `pytest` and `python` in its commands.

**Why it matters:** Inconsistency between rules and practice erodes trust in the project's standards. If the project's own tooling doesn't follow its own rules, contributors won't either.

---

### M-12 — Main CI Workflow Ignores UV

**Where:** `.github/workflows/ci.yml`

**What:** The main CI workflow uses `pip install` instead of `uv`, while other workflows (`validate.yml`, `quick-check.yml`) correctly use UV.

**Why it matters:** Different dependency resolution between `pip` and `uv` can produce different installed packages, meaning CI may test against a different environment than local development. This can cause "works on my machine" problems in both directions.

---

### M-13 — Contradictory Git Workflow Documentation

**Where:** CLAUDE.md vs SKILL.md files for `wfc-build` and `wfc-implement`

**What:** CLAUDE.md describes a PR-First workflow where WFC pushes branches and creates GitHub PRs. The SKILL.md files explicitly state "WFC NEVER pushes to remote. User must push manually."

**Why it matters:** Contributors and users reading different documents will have opposite expectations about what WFC does with their code. This is especially dangerous because it involves pushing code to remote repositories — getting this wrong could expose unfinished work or bypass review processes.

---

### M-14 — Type Annotations Lie About Nullability

**Where:** `wfc/shared/telemetry_auto.py`, `wfc/scripts/cloud_execution.py`, `wfc/skills/wfc-architecture/c4_generator.py`

**What:** Dataclass fields declare types like `List[str]` but have `None` as default values. The type annotation says "this is always a list" when it can actually be `None`.

**Why it matters:** Type checkers, IDE autocompletion, and developers reading the code will assume these fields are always lists and call list methods on them without None checks. This leads to `AttributeError: 'NoneType' has no attribute 'append'` at runtime — a category of bug that type annotations are supposed to prevent.

---

### M-15 — Telemetry Data Split Across Two Systems

**Where:** `wfc/shared/telemetry/wfc_telemetry.py`, `wfc/shared/telemetry_auto.py`

**What:** Two independent telemetry systems write to different directories (`~/.claude/metrics/` and `~/.wfc/telemetry/`), each with their own API.

**Why it matters:** Anyone trying to analyze WFC usage patterns has to know about both systems and merge data from two locations. Code that writes to one system won't appear in queries against the other. This also doubles the maintenance surface — bug fixes and feature additions need to happen in two places.

---

### M-16 — Infinite Recursion Risk in Task Graph

**Where:** `wfc/shared/schemas/task_schema.py`

**What:** The dependency level computation uses recursion with no cycle detection. A `validate_dag()` method exists but is not called automatically before computing levels.

**Why it matters:** If a task graph accidentally contains a cycle (Task A depends on Task B which depends on Task A), the level computation will recurse until Python hits its recursion limit and crashes. Since tasks are defined by users in TASKS.md files, malformed input shouldn't crash the system.

---

### M-17 — Build Orchestrator Returns a Placeholder

**Where:** `wfc/scripts/skills/build/orchestrator.py`

**What:** The implementation execution method returns a hardcoded dictionary with `"status": "placeholder"` — it never routes to the actual implementation engine.

**Why it matters:** The wfc-build skill claims to implement features via TDD with quality gates, but the underlying orchestrator produces fake results. Tests validate the placeholder behavior, which means the test suite confirms the system does nothing — and reports that as passing.

---

### M-18 — Config Merge Has Shared Reference Bug

**Where:** `wfc/shared/config/wfc_config.py`

**What:** The configuration deep merge uses a shallow copy. Mutable values like lists in the base config are shared by reference with the merged result.

**Why it matters:** Modifying a list in the merged config would also modify the base config (and vice versa). In a system with three config tiers (defaults, global, project), this kind of cross-contamination can cause settings to "leak" between tiers in unpredictable ways.

---

### M-19 — Home Directory Baked in at Import Time

**Where:** `wfc/shared/config/wfc_config.py`

**What:** Default paths using `Path.home()` are evaluated once when the module is first imported and stored as class-level constants.

**Why it matters:** In testing environments where `HOME` is overridden after import (common in CI), the config system will use the original home directory, not the test one. This makes config-related tests unreliable and can cause tests to read/write files in the real user directory instead of the test sandbox.

---

### M-20 — Tautological Test Assertion

**Where:** `tests/test_hooks.py`

**What:** An assertion checks `"WARNING" not in output or "WARNING" in output` — which is logically always true regardless of whether WARNING appears or not.

**Why it matters:** This test can never fail. It occupies a slot in the test suite that should be verifying actual behavior, giving false coverage statistics.

---

### M-21 — Persona Selection Tests Never Run Under Pytest

**Where:** `wfc/personas/tests/test_persona_selection.py`

**What:** This 337-line test file uses a custom runner with `print()` output and a `run_all_tests()` main function instead of pytest conventions. Its 7 tests are never collected by `pytest`.

**Why it matters:** The persona selection algorithm is a critical component (choosing which 5 of 56 experts review code), but its tests are invisible to the CI pipeline. Regressions in persona selection would go undetected.

---

### M-22 — E2E Test Uses Return Values Instead of Assertions

**Where:** `wfc/tests/test_implement_e2e.py`

**What:** The `test_full_pipeline()` function returns `True` or `False` instead of using `assert` statements. Pytest collects it as a test but never considers a `return False` as a failure.

**Why it matters:** This test exists in the test suite and appears in coverage reports, but it can never fail. A complete regression of the pipeline would still show this test as passing.

---

## Low Severity

### L-01 — Unused `skip_quality` Parameter
`wfc/cli.py` — The parameter is accepted and warned about but never passed to the orchestrator. Dead parameter that confuses the API surface.

### L-02 — Hardcoded Alternative Suggestions
`wfc/scripts/confidence_checker.py` — The alternatives generator always returns the same two generic suggestions regardless of task context. Makes the confidence system's guidance less useful.

### L-03 — Inconsistent Default Model Names
`wfc/scripts/personas/token_manager.py` — Default model name doesn't match the config system's model name. No functional impact since the tokenizer backend is the same, but inconsistency is confusing.

### L-04 — Dead Conditional in Branding
`wfc/shared/branding.py` — The `format_header` method has identical branches for SFW and NSFW modes. The conditional serves no purpose.

### L-05 — Windows Incompatibility in Telemetry
`wfc/shared/telemetry/wfc_telemetry.py` — Uses a Unix-only module (`fcntl`) at the top level, making the entire telemetry module fail to import on Windows.

### L-06 — Inconsistent Serialization Patterns
Multiple files — Some classes use `to_dict()`/`from_dict()`, others use `dataclasses.asdict()`. Consumers must know which pattern each class uses.

### L-07 — God-Method in CLI
`wfc/cli.py` — The `cmd_implement` function is 161 lines handling parsing, configuration, dry-run display, orchestration, result display, and error handling. Should be decomposed.

### L-08 — Race Condition in File I/O
`wfc/shared/file_io.py` — A check-then-open pattern creates a window where the file could be deleted between the existence check and the open call. Relevant in multi-agent parallel execution.

### L-09 — Git Hooks Never Block Anything
`wfc/wfc_tools/gitwork/hooks/*.py` — All hooks exit with success regardless of what they find. Commits with secrets, pushes to protected branches, and invalid messages are warned but never prevented.

### L-10 — Hardcoded Protected Branch List
`wfc/wfc-tools/gitwork/api/branch.py` — Protected branches are a fixed list with no project-level configuration. Custom branch protection strategies aren't supported.

### L-11 — Subprocess Output Leaks to Terminal
`wfc/wfc-tools/gitwork/api/commit.py`, `wfc/skills/wfc-implement/agent.py` — Some subprocess calls don't capture output, potentially exposing internal paths and operations to the user's terminal.

### L-12 — No Path Sanitization in File I/O
`wfc/shared/file_io.py` — Paths with `..` components pass through without canonicalization. Could allow reading files outside intended directories.

### L-13 — Installer Uses Unchecked `rm -rf`
`install-universal.sh` — Variables used in recursive delete operations aren't validated against path traversal sequences.

### L-14 — Config Poisoning Through Shared Repos
`wfc/wfc-tools/gitwork/config.py` — Reads config from a project-local file. A malicious contributor could commit a config that alters merge strategy or injects commands into the test runner.

### L-15 — Incomplete Security Pattern Coverage
`wfc/scripts/hooks/patterns/security.json` — Patterns don't catch multi-line subprocess calls, split `rm` flags, `os.popen()`, `yaml.load()` without SafeLoader, or encoded secrets.

### L-16 — Hardcoded Developer Path
`tests/multi-flavor-test.sh` — Contains `/home/sambou/repos/wfc` — a specific developer's home directory path that makes the script non-portable.

### L-17 — Dormant Bug in Docker Test Config
`tests/conftest_docker.py` — References `pytest.root.nodeid` which doesn't exist in the pytest API. Currently dormant because the file isn't auto-loaded.

### L-18 — Silent Config Fallback at Import Time
`wfc/scripts/personas/persona_orchestrator.py` — Config loading in a module-level try/except silently uses a fallback with no way to detect the failure at runtime.

### L-19 — Thread-Unsafe Global Singletons
`wfc/shared/branding.py`, `wfc/shared/telemetry_auto.py` — Use global variables for singletons, making tests unreliable (state persists between tests) and unsafe in concurrent scenarios.

### L-20 — Missing Package Init Files
`wfc_tools/`, `wfc_tools/gitwork/`, and 6 skill directories — Missing `__init__.py` files. The skill directories are prompt-only (harmless), but `wfc_tools/` is actually imported and needs them for reliable package resolution.

### L-21 — Smoke Test That Asserts True
`tests/test_implement_integration.py` — A smoke test exists solely as `assert True`. If imports fail, the test isn't collected at all — the assertion itself verifies nothing.

### L-22 — Tests Validate Markdown, Not Code
`tests/test_build_cli.py` — Named `TestCLIInterface` but all 11 tests parse SKILL.md text content. No CLI interface is tested.

### L-23 — Tests Verify Their Own Setup
`tests/test_implement_e2e.py` — Several tests construct data objects and then assert the values they just set. No actual merge, rollback, or retry logic is exercised.

---

## What's Working Well

1. **Token management architecture** — 99% reduction from 150k to 1.5k tokens through file references, ultra-minimal prompts, and progressive disclosure is a genuine innovation
2. **Dataclass discipline** — Clean value objects throughout the codebase
3. **Subprocess safety** — The vast majority of subprocess calls use safe list-based arguments
4. **Force push protection** — PR operations block force pushes to protected branches
5. **No hardcoded secrets** — Clean codebase with no credentials
6. **Strong plugin integration tests** — `test_plugin_integration.py` at 791 lines is an excellent reference for how to write good tests in this codebase
7. **Progressive disclosure pattern** — Load only what's needed when it's needed
8. **Configuration layering** — Clean three-tier config system
9. **Comprehensive DevContainer** — Multi-stage Docker build with cross-distro testing
10. **Intentional fail-open hooks** — Design prevents hook bugs from blocking workflow (needs logging though)

---

## Recommended Fix Order

### Do First (High Impact)
1. Fix broken test imports for implementation engine (H-02) — recovers 18+ tests instantly
2. Consolidate `wfc-tools/` and `wfc_tools/` into one package (H-03)
3. Remove `shell=True` from CLI (H-01)
4. Make safety property test assertions unconditional (H-06)

### Do Soon (Medium Impact)
5. Pick one canonical location per skill, remove duplicates (H-07)
6. Add logging to security hook fail-open paths (M-08)
7. Validate hook type against whitelist (H-04)
8. Fix operator precedence bug in token manager (M-01)
9. Update CI workflow to use UV (M-12)
10. Align SKILL.md docs with PR-First workflow (M-13)

### Do When Convenient (Cleanup)
11. Fix review skill naming mismatch (H-08)
12. Replace stub review agents or document as stubs (M-03)
13. Consolidate telemetry systems (M-15)
14. Fix type annotations in dataclasses (M-14)
15. Convert persona tests to pytest (M-21)
16. Remove hardcoded developer path from test script (L-16)
