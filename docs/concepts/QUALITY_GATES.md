# Quality Gates

## What Quality Gates Are

A quality gate is an automated check that runs against your code before it is considered ready for review or merge. WFC applies quality gates at two points in the workflow: immediately after a file is written (PostToolUse), and as an explicit step before the consensus review runs.

The goal is to catch formatting errors, linting violations, and type errors as early as possible — before they become review findings or, worse, reach production.

## When Gates Run

Quality gates are triggered by PostToolUse hooks. Every time Claude writes or edits a file, `file_checker.py` inspects the changed file and dispatches the appropriate language-specific checker. This means you see linting feedback on the file you just edited, not at the end of the session when there are dozens of files to fix.

In addition, `wfc-implement` runs a full quality gate pass after each agent completes its task, before the output is submitted to the consensus review.

## Trunk.io Integration

For projects that use Trunk, WFC integrates with Trunk.io as a universal quality checker. Trunk supports over 100 linting and formatting tools across all major languages and manages tool versioning automatically. When Trunk is available, WFC routes the quality gate through it to get consistent, version-pinned checks across the entire codebase.

Run the Trunk gate manually with:

```bash
make quality-check
```

## Language-Specific Checkers

When Trunk is not present, WFC falls back to language-specific checkers in `wfc/scripts/hooks/_checkers/`. Each checker is a thin wrapper that runs the standard toolchain for that language.

**Python** (`python.py`):

- `ruff` for fast linting and import sorting
- `pyright` for static type checking

**TypeScript / JavaScript** (`typescript.py`):

- `prettier` for formatting
- `eslint` for linting
- `tsc` for type checking

**Go** (`go.py`):

- `gofmt` for formatting
- `go vet` for suspicious constructs
- `golangci-lint` for comprehensive linting

## What Happens on Failure

When a quality gate fails, the result is surfaced as a structured message with the tool name, the specific violation, and the file and line number. The failing agent cannot submit its task output to the review stage until the violation is resolved.

This is a hard gate: a file with type errors or linting failures does not proceed to consensus review. The philosophy is that code quality is not a suggestion to be reviewed — it is a baseline that must be met before human attention is spent on higher-order concerns.

## Keeping Gates Fast

WFC applies gates only to changed files, not the entire codebase, for the PostToolUse path. The full-codebase gate (`make check-all`) is reserved for pre-commit and pre-PR checks. This keeps the per-edit feedback loop fast while ensuring the full suite runs before code is shared.
