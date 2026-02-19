---
name: wfc-gh-debug
description: GitHub Actions CI failure debugger. Fetches failing workflow run logs via gh CLI, identifies root causes across common failure categories (lint, tests, type errors, missing deps, secrets, infra), proposes targeted fixes, and optionally applies them. Use when CI checks are failing on a PR or branch. Triggers on "failing checks", "CI is red", "fix CI", "debug workflow", or explicit /wfc-gh-debug.
license: MIT
---

# WFC:GH-DEBUG — GitHub Actions Failure Debugger

**Fetch logs → Classify failure → Fix.** Systematic CI debugging without manual log spelunking.

## Usage

```bash
# Debug failing checks on current branch's PR
/wfc-gh-debug

# Debug specific PR
/wfc-gh-debug 42

# Debug specific workflow run
/wfc-gh-debug run 12345678

# Debug specific job
/wfc-gh-debug job 64062559122
```

---

## Workflow

### Step 1: DETECT TARGET

Determine what to debug:

1. If a run ID or job ID is provided, use it directly.
2. If a PR number is given, fetch its checks:
   ```bash
   gh pr checks {number} --repo {owner}/{repo}
   ```
3. If no argument, auto-detect from current branch:
   ```bash
   gh pr checks --repo {owner}/{repo}
   ```

Display all failing checks in a table:
```
| # | Job Name | Duration | Status | URL |
|---|----------|----------|--------|-----|
| 1 | Lint & Format Check | 10s | FAIL | ... |
| 2 | Run Tests | 20s | FAIL | ... |
```

If no failing checks found, report "All checks passing ✅" and stop.

### Step 2: FETCH LOGS

For each failing job, fetch logs via gh CLI:

```bash
gh run view {run_id} --repo {owner}/{repo} --job {job_id} --log 2>&1
```

**Extraction strategy:** Don't dump the entire log. Extract:
1. Lines matching `error|Error|FAILED|failed|Exit code [^0]|##\[error\]`
2. The last 50 lines (often contains the summary)
3. Any lines with file paths + line numbers (e.g., `file.py:42:`)

Fetch all failing jobs in parallel using multiple tool calls.

### Step 3: CLASSIFY FAILURE

Classify each failure into a category:

| Category | Signals | Common Fix |
|----------|---------|------------|
| **FORMAT** | `would reformat`, `black`, `prettier` | Run formatter, commit |
| **LINT** | `ruff`, `eslint`, `flake8`, `golangci` | Run linter with --fix |
| **TYPE** | `mypy`, `pyright`, `tsc`, `type error` | Fix type annotations |
| **TEST** | `FAILED`, `AssertionError`, `pytest` | Fix failing test or code |
| **IMPORT** | `ModuleNotFoundError`, `ImportError`, `cannot find module` | Install dep or fix import |
| **PERMISSION** | `permission denied`, `not executable`, `chmod` | Fix file permissions |
| **SECRET** | `secret`, `token`, `auth`, `401`, `403` | Check secrets configuration |
| **INFRA** | `docker`, `connection refused`, `timeout`, `OOMKilled` | Infrastructure issue, skip/retry |
| **SYNTAX** | `SyntaxError`, `parse error`, `unexpected token` | Fix syntax |
| **SKILL** | `skills-ref`, `validate`, `Agent Skills` | Fix skill frontmatter/format |

### Step 4: REPORT FINDINGS

Present a structured diagnosis:

```
## CI Failure Diagnosis — PR #42

### Job 1: Lint & Format Check ❌ (FORMAT)

**Root cause:** `black` would reformat `wfc/scripts/github/pr_threads.py`

**Evidence:**
  would reformat /home/runner/work/wfc/wfc/wfc/scripts/github/pr_threads.py
  1 file would be reformatted, 156 files would be left unchanged.

**Fix:** `uv run black wfc/scripts/github/pr_threads.py`
**Effort:** Trivial (auto-fixable)

---

### Job 2: Run Tests ❌ (FORMAT — same file)

**Root cause:** Same black formatting issue in test step.

**Fix:** Same as Job 1 — fixing once resolves both.
**Effort:** Trivial

---

## Summary
- 2 failures, 1 unique root cause
- All auto-fixable
- Estimated fix time: < 1 minute
```

Group duplicate root causes — if 3 jobs all fail for the same reason, say so clearly.

### Step 5: FIX

Ask the user if they want fixes applied:
- **Auto-fixable** (FORMAT, LINT): Apply immediately, no approval needed
- **Code fixes** (TEST, TYPE, SYNTAX, IMPORT): Show the fix, ask for approval
- **Config fixes** (SECRET, PERMISSION, SKILL): Explain the fix, require explicit approval
- **Infra issues** (INFRA): Cannot auto-fix — explain and suggest manual action

**For FORMAT fixes:**
```bash
# Python
uv run black {file}
uv run ruff check --fix {file}

# TypeScript/JS
npx prettier --write {file}

# Go
gofmt -w {file}
```

**For SKILL fixes:**
Read the failing skill file, check against Agent Skills spec:
- Valid frontmatter fields only: `name`, `description`, `license`
- Name uses hyphens only, no colons
- Run `wfc validate` after fixing

**For PERMISSION fixes:**
```bash
chmod +x {script}
git add {script}
git update-index --chmod=+x {script}
```

**For TEST fixes:**
Read the failing test + source file, understand the failure, apply targeted fix.

**For IMPORT fixes:**
Check if the module exists in `pyproject.toml` / `package.json`. If missing, suggest adding it. If import path is wrong, fix it.

### Step 6: VERIFY & PUSH

After applying fixes:

1. Run the equivalent check locally:
   ```bash
   # FORMAT
   uv run black --check wfc/
   uv run ruff check .

   # TESTS
   uv run pytest {failing_test_file} -v

   # SKILLS
   wfc validate
   ```

2. If local check passes:
   ```bash
   git add {fixed_files}
   git commit -m "fix: resolve CI failures — {brief description}

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   git push
   ```

3. Optionally watch CI re-run:
   ```bash
   gh pr checks {pr_number} --watch --repo {owner}/{repo}
   ```

### Step 7: REPORT

```
## CI Fix Complete

**Fixed:** 2 jobs (FORMAT — black formatting on pr_threads.py)
**Committed:** abc1234
**Pushed:** origin/branch-name

CI re-triggered. Watch progress:
  gh pr checks 42 --watch
```

---

## Common Failure Patterns

### Black/Prettier formatting
```bash
# Identify
uv run black --check wfc/

# Fix
uv run black wfc/
```

### Ruff lint errors
```bash
# Identify + auto-fix
uv run ruff check --fix .

# Check remaining (need manual fix)
uv run ruff check .
```

### Failing tests after refactor
Look for:
- Import path changes (renamed module, moved file)
- API signature changes (added/removed parameter)
- Mock targets that no longer exist

### Agent Skills compliance
```bash
# Validate all skills
wfc validate

# Check specific skill
skills-ref validate ~/.claude/skills/wfc-foo/SKILL.md
```

Common issues:
- Invalid frontmatter fields (`user-invocable`, `argument-hint`, `disable-model-invocation`)
- Colons in skill names (`wfc:foo` → `wfc-foo`)
- Missing required fields

### Missing dependencies in CI
Check `pyproject.toml` `[project.dependencies]` — if a new import was added but not declared, CI will fail with `ModuleNotFoundError` while local works (because local has the dev install).

---

## Integration with WFC

### Triggered by
- Failing PR checks noticed during `/wfc-pr-comments`
- User reports CI is red
- After `/wfc-build` or `/wfc-implement` pushes a branch

### Typical Flow
```
wfc-build → Push PR → CI fails → /wfc-gh-debug → Fix → CI green → Merge
```

### Complements
- `/wfc-pr-comments` — fixes review comments; `/wfc-gh-debug` fixes CI
- `/wfc-review` — catches issues before CI; `/wfc-gh-debug` fixes what slips through

## Philosophy

**ELEGANT:** One command diagnoses + fixes CI without log spelunking
**PARALLEL:** Fetch all failing job logs simultaneously
**PROGRESSIVE:** Auto-fix trivial issues, ask for approval on code changes
**TOKEN-AWARE:** Extract relevant log lines only, not full 10MB logs
