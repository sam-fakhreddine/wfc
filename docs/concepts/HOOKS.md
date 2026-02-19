# Hook Infrastructure

## Overview

WFC installs two categories of hooks into Claude Code's hook system: PreToolUse hooks that intercept tool calls before they execute, and PostToolUse hooks that react after a tool completes. Together they provide real-time security enforcement, automatic code quality checks, TDD guidance, and context window monitoring — all without requiring you to run separate commands.

The hook entry points are registered in `.claude/settings.json` and dispatched through Python scripts in `wfc/scripts/hooks/`.

## PreToolUse: Security Enforcement

The PreToolUse hook (`pretooluse_hook.py`) runs before every Bash or file-write tool call. It checks the incoming tool input against a set of security patterns and either blocks the call (exit code 2) or warns and allows it (exit code 0).

Patterns are defined in two JSON files:

- `wfc/scripts/hooks/patterns/security.json` — general code security patterns
- `wfc/scripts/hooks/patterns/github_actions.json` — GitHub Actions-specific patterns

The current pattern set covers 13 threats across both files:

| Pattern ID | What It Catches | Action |
|---|---|---|
| `eval-injection` | `eval()` calls in Python/JavaScript | Block |
| `new-function` | `new Function()` in JavaScript | Block |
| `inner-html` | `.innerHTML =` and `dangerouslySetInnerHTML` | Warn |
| `pickle-untrusted` | `pickle.loads()` deserialization | Warn |
| `os-system` | `os.system()` command execution | Block |
| `subprocess-shell` | `subprocess` with `shell=True` | Block |
| `child-process-exec` | `child_process.exec()` | Warn |
| `rm-rf-root` | `rm -rf /` on system paths | Block |
| `rm-rf-home` | `rm -rf ~/` or `$HOME` | Block |
| `hardcoded-secret` | API_KEY, PASSWORD, SECRET_KEY literals | Warn |
| `sql-concatenation` | SQL strings built via `+` with user input | Warn |
| `gha-script-injection` | `${{ github.event.* }}` in Actions `run:` blocks | Block |
| `gha-pull-request-target` | `pull_request_target:` trigger (secrets exposure) | Warn |

When a block pattern fires, the tool call is cancelled and the reason is written to stderr so Claude can see why and choose an alternative approach.

## PostToolUse Hooks

Three PostToolUse hooks run after file edits and Bash commands complete.

**`file_checker.py` — Auto-Lint on Save**

After every file write or edit, this hook detects the file's language and dispatches the appropriate quality checker (ruff/pyright for Python, prettier/eslint/tsc for TypeScript, gofmt/go vet for Go). Violations are surfaced immediately as structured feedback, before they accumulate into a larger problem at review time.

**`tdd_enforcer.py` — TDD Reminders**

When the hook detects that implementation code has been written without a corresponding test file change, it emits a reminder to follow the RED-GREEN-REFACTOR cycle. This is a soft nudge, not a hard block — it keeps TDD front-of-mind during implementation without interrupting flow.

**`context_monitor.py` — Context Window Tracking**

After larger tool calls, this hook checks the current context window usage and emits a warning when usage approaches the limit. This prevents silent context truncation, which can cause agents to lose earlier decisions or instructions without realizing it.

## Fail-Open Design

All hooks are designed to fail open. If a hook raises an unhandled exception — due to a missing dependency, a malformed pattern file, or any other internal error — the hook exits with code 0 and logs a warning. A bug in the hook system must never block Claude's workflow.

This is enforced at the top level of `pretooluse_hook.py`: the entire `_run()` function is wrapped in a try/except that catches all exceptions and exits 0 with a warning log before propagating.

## Session-Scoped Deduplication

The PreToolUse hook tracks which warnings it has already issued in the current session. If the same pattern fires on the same file path a second time, the hook does not emit another warning. This prevents warning fatigue on repeated edits to the same file while still ensuring the first occurrence is surfaced.
