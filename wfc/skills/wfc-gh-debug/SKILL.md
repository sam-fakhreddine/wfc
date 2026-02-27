---
name: wfc-gh-debug
description: >
  Diagnoses failing GitHub-native Actions workflow runs by analyzing logs via
  the `gh` CLI. Classifies root causes (lint, format, test, type, import,
  permission, secret, infra/runner) and proposes fixes. Applies fixes only
  after explicit user approval.

  Capabilities: fetches and analyzes logs from GitHub-hosted Actions runners;
  classifies failures into actionable categories; auto-generates fix commands
  for uv-managed Python and npm/TS projects; verifies fixes locally before
  pushing.

  Limitations: requires `uv` for Python verification (no pip/poetry fallback);
  cannot access third-party check logs (Vercel, Codecov) or external CI;
  cannot fix infrastructure failures; requires `gh` CLI authentication.

  Triggers: "GitHub Actions failed", "workflow run failed", "debug GitHub
  Actions logs", "why did my Actions run fail", /wfc-gh-debug.

  Not for: third-party status checks; external CI (Jenkins, GitLab, CircleCI);
  fork PRs with missing secrets; PR policy gates; flaky tests; green runs.
license: MIT
---

# WFC:GH-DEBUG — GitHub Actions Failure Debugger

**Fetch logs → Classify failure → Propose fix.** Systematic CI debugging for GitHub-native Actions.

## Prerequisites

Before execution, verify:

1. **Authentication**: `gh auth status` returns success
2. **Repository context**: Current directory is a git repository with GitHub remote
3. **Toolchain**: Project uses `uv` (Python) or `npm` (JS/TS) for verification steps

If prerequisites fail, report the issue and stop.

---

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

1. **Authentication check**: Run `gh auth status`. If this fails, report "GitHub CLI not authenticated" and stop.
2. **Target resolution** (in order of priority):
   - If `run {id}` provided → use run ID directly
   - If `job {id}` provided → use job ID directly
   - If PR number provided → fetch checks for that PR
   - If no argument → check if current branch has an open PR

3. **Fetch checks**:

   ```bash
   gh pr checks {number} --repo {owner}/{repo}
   ```

4. **Handle empty results**:
   - If command fails with permission error → Report "No access to repository" and stop
   - If no PR exists for current branch → Report "No open PR found for current branch" and stop
   - If all checks passing → Report "All checks passing ✅" and stop

5. **Display failing checks**:

```
| # | Job Name | Duration | Status | URL |
|---|----------|----------|--------|-----|
| 1 | Lint & Format Check | 10s | FAIL | ... |
| 2 | Run Tests | 20s | FAIL | ... |
```

**Important**: This skill only processes GitHub Actions workflow failures. If all failures are from third-party checks (Vercel, Codecov, external CI), report "Failures detected are from third-party checks not accessible via GitHub Actions logs" and stop.

### Step 2: FETCH LOGS

For each failing job, fetch logs via gh CLI:

```bash
gh run view {run_id} --repo {owner}/{repo} --log 2>&1
```

**Error handling**:

- If command returns empty output or 500 error → Classify as **INFRA** and report "Logs unavailable (runner infrastructure failure)"
- If command returns 403/404 → Report "No access to workflow logs" and stop

**Extraction strategy:** Don't dump the entire log. Extract:

1. Lines matching `error|Error|FAILED|failed|Exit code [^0]|##\[error\]`
2. The last 50 lines (often contains the summary)
3. Any lines with file paths + line numbers (e.g., `file.py:42:`)
4. **Path mapping**: Convert CI absolute paths (e.g., `/home/runner/work/repo/file.py`) to local paths (`./file.py`)

Fetch all failing jobs in parallel using multiple tool calls.

### Step 3: CLASSIFY FAILURE

Classify each failure into a category:

| Category | Signals | Common Fix | Approval Required? |
|----------|---------|------------|-------------------|
| **FORMAT** | `would reformat`, `black`, `prettier` | Run formatter, commit | Yes (show diff) |
| **LINT** | `ruff`, `eslint`, `flake8`, `golangci` | Run linter with --fix | Yes (show diff) |
| **SYNTAX** | `SyntaxError`, `parse error`, `unexpected token` | Fix syntax manually | Yes (code change) |
| **TYPE** | `mypy`, `pyright`, `tsc`, `type error` | Fix type annotations | Yes (code change) |
| **TEST** | `FAILED`, `AssertionError`, `pytest` | Fix failing test or code | Yes (code change) |
| **IMPORT** | `ModuleNotFoundError`, `ImportError`, `cannot find module` | Install dep or fix import | Yes (code/config change) |
| **PERMISSION** | `permission denied`, `not executable`, `chmod` | Fix file permissions | Yes (config change) |
| **SECRET** | `secret`, `token`, `auth`, `401`, `403` | Check secrets configuration | Yes (manual config) |
| **INFRA** | `docker`, `connection refused`, `timeout`, `OOMKilled`, `logs unavailable` | Infrastructure issue | N/A (cannot fix) |
| **SKILL** | `skills-ref`, `validate`, `Agent Skills` | Fix skill frontmatter | Yes (show fix) |

**Flaky test detection**: If failure occurs in only 1 matrix shard and shows timeout/connection/intermittent signals, flag as **Potential Flaky Test** and recommend re-run via `gh run rerun {run_id}` before attempting code changes.

### Step 4: REPORT FINDINGS

Present a structured diagnosis:

```
## CI Failure Diagnosis — PR #42

### Job 1: Lint & Format Check ❌ (FORMAT)

**Root cause:** `black` would reformat `wfc/scripts/github/pr_threads.py`

**Evidence:**
  would reformat /home/runner/work/wfc/wfc/wfc/scripts/github/pr_threads.py
  1 file would be reformatted, 156 files would be left unchanged.

**Proposed fix:** `uv run black wfc/scripts/github/pr_threads.py`
**Approval required:** Yes (will show diff before committing)

---

### Job 2: Run Tests ❌ (FORMAT — same file)

**Root cause:** Same black formatting issue in test step.

**Proposed fix:** Same as Job 1 — fixing once resolves both.
**Approval required:** Yes

---

## Summary
- 2 failures, 1 unique root cause
- All auto-fixable with approval
- Estimated fix time: < 1 minute
```

Group duplicate root causes — if 3 jobs all fail for the same reason, say so clearly.

**Fork PR detection**: If logs show `fatal: could not read Username` for submodules, classify as **PERMISSION (Fork Context)** and report: "Fork PR lacks access to private submodules/secrets. Requires workflow approval or secrets inheritance configuration."

### Step 5: PROPOSE FIX

**CRITICAL**: This skill does NOT apply fixes automatically. Always show the proposed fix and wait for explicit user approval.

**For all fixable categories**:

1. Show the exact commands to run
2. Show expected impact (files modified, tests affected)
3. Ask: "Apply this fix? (yes/no)"

**Fix commands by category**:

**FORMAT**:

```bash
# Python
uv run black {file}
uv run ruff check --fix {file}

# TypeScript/JS
npx prettier --write {file}

# Go
gofmt -w {file}
```

**LINT**:

```bash
uv run ruff check --fix {file}
# or
npx eslint --fix {file}
```

**SKILL**:
Read the failing skill file, check against Agent Skills spec:

- Valid frontmatter fields only: `name`, `description`, `license`
- Name uses hyphens only, no colons
- Run `wfc validate` after fixing

**PERMISSION**:

```bash
chmod +x {script}
git add {script}
git update-index --chmod=+x {script}
```

**TEST**:

- Read the failing test file completely (not just error snippets)
- Read the source file being tested
- Propose targeted fix with explanation of why test failed

**IMPORT**:

- Check if module exists in `pyproject.toml` / `package.json`
- If missing external dependency → propose adding to dependencies
- If local import path wrong → propose path correction
- **Distinguish**: Local modules (e.g., `from lib.utils`) vs external packages (e.g., `import requests`)

**INFRA** (cannot fix):
Report infrastructure issue and suggest manual action:

- Runner timeout/OOM → "Increase runner resources or optimize build"
- Docker/connection issues → "Check network configuration or retry"
- Offer to re-run: `gh run rerun {run_id}`

### Step 6: VERIFY & PUSH (After User Approval)

After user approves fix:

1. **Apply the fix** using the proposed commands
2. **Verify file modification**:

   ```bash
   git diff --quiet {file}
   ```

   If no changes detected, report "Fix command did not modify file" and stop.

3. **Run local verification** (toolchain-dependent):

   **For `uv` projects**:

   ```bash
   # FORMAT
   uv run black --check wfc/
   uv run ruff check .

   # TESTS
   uv run pytest {failing_test_file} -v

   # SKILLS
   wfc validate
   ```

   **For npm projects**:

   ```bash
   npx prettier --check .
   npx eslint .
   npm test
   ```

   **For other toolchains**: Report "Local verification not configured for this toolchain. Proceed with commit?"

4. **If verification passes**:

   ```bash
   git add {fixed_files}
   git commit -m "fix: resolve CI failures — {brief description}

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   git push
   ```

5. **Optionally watch CI re-run**:

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

**Context requirement**: Read full test file and source file before proposing fix.

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
