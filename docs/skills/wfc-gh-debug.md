# wfc-gh-debug

## What It Does

`wfc-gh-debug` diagnoses failing GitHub Actions checks without requiring manual log spelunking. It fetches logs from all failing jobs via the GitHub CLI, classifies each failure into a known category (format, lint, type errors, test failures, missing dependencies, permission issues, secrets configuration, infrastructure, syntax errors, or Agent Skills compliance), and either auto-fixes trivial issues immediately or proposes targeted fixes for approval before applying them.

## When to Use It

- When CI checks are red on a PR and you need to identify the root cause quickly
- After `/wfc-build` or `/wfc-implement` pushes a branch and CI fails
- When multiple jobs fail for the same underlying reason (one fix resolves all)
- When a formatting or linting failure in CI would be trivial to auto-fix locally

## Usage

```bash
# Debug failing checks on current branch's PR
/wfc-gh-debug

# Debug specific PR number
/wfc-gh-debug 42

# Debug specific workflow run by run ID
/wfc-gh-debug run 12345678

# Debug specific job by job ID
/wfc-gh-debug job 64062559122
```

## Example

```
Detecting failing checks on PR #42...

| # | Job Name              | Duration | Status |
|---|-----------------------|----------|--------|
| 1 | Lint & Format Check   | 10s      | FAIL   |
| 2 | Run Tests             | 20s      | FAIL   |

Fetching logs (parallel)...

## CI Failure Diagnosis — PR #42

### Job 1: Lint & Format Check (FORMAT)

Root cause: `black` would reformat `wfc/scripts/github/pr_threads.py`

Evidence:
  would reformat /home/runner/work/wfc/wfc/wfc/scripts/github/pr_threads.py
  1 file would be reformatted, 156 files would be left unchanged.

Fix: `uv run black wfc/scripts/github/pr_threads.py`
Effort: Trivial (auto-fixable)

### Job 2: Run Tests (FORMAT — same file)

Root cause: Same black formatting issue causes test step to abort early.
Fix: Same as Job 1 — fixing once resolves both.

Summary: 2 failures, 1 unique root cause. All auto-fixable.

Applying fix...
✅ uv run black wfc/scripts/github/pr_threads.py
✅ uv run black --check wfc/ (passes)

Committing: "fix: resolve CI failures — black formatting on pr_threads.py"
Pushed to origin/feat/rate-limiting

Watch CI: gh pr checks 42 --watch
```

## Options

- **No argument** — Auto-detects failing checks from the current branch's PR
- **`<PR number>`** — Target a specific PR
- **`run <run_id>`** — Target a specific workflow run by ID
- **`job <job_id>`** — Target a specific job by ID

**Fix approval policy:**

- FORMAT and LINT failures: auto-fixed immediately without prompting
- TEST, TYPE, SYNTAX, IMPORT fixes: shown to user for approval before applying
- SECRET, PERMISSION, SKILL config fixes: require explicit approval
- INFRA issues: cannot be auto-fixed — diagnosis and manual action recommended

## Integration

**Produces:**

- Targeted fixes committed and pushed to the branch
- Diagnosis report listing root cause per job with evidence from the log
- Optionally: a `gh pr checks --watch` command to monitor the re-triggered CI run

**Consumes:**

- GitHub Actions workflow logs (fetched via `gh run view --log`)
- Source files identified in error output
- Local quality tools: `uv run black`, `uv run ruff`, `uv run pytest`, `wfc validate`

**Next step:** Once CI is green, return to `/wfc-pr-comments` to finish addressing any open review threads, or proceed to merge if the PR is already approved.
