---
name: wfc-housekeeping
description: >
  Removes unreferenced content from a codebase: unused imports, stale git
  branches, orphaned files, and debug artifacts. Strictly limited to
  file-level deletion within source code — does not modify package
  manifests, lockfiles, or git history.

  Operates in scan-report-approve-execute cycle with mandatory test
  verification. All deletions require explicit user approval unless --safe
  flag is used (auto-fixes: unused imports in Python files only).

  Scope: Python .py files, git branches, worktrees, tracked temp files.
  Uses static analysis (ruff, grep); cannot detect dynamically accessed
  code (getattr, globals, plugin loaders).

  Triggers: "remove unused imports", "delete dead code", "prune stale
  branches", "clean up debug logs", /wfc-housekeeping.

  Not for: Refactoring logic; removing packages from pyproject.toml or
  package.json; npm prune / cargo prune; rewriting git history; secret
  detection; fixing tests; feature-flagged code.
license: MIT
---

# WFC:HOUSEKEEPING - Project Hygiene & Cleanup

Systematic cleanup with explicit safety guardrails and user approval gates.

## Scope

**What this skill does:**

- Removes unused import statements from Python source files
- Deletes merged/stale git branches (local and remote with approval)
- Removes orphaned files not referenced anywhere in the codebase
- Cleans debug artifacts: print statements, breakpoints, temp files

**What this skill does NOT do:**

- Modify `pyproject.toml`, `package.json`, `Cargo.toml`, or any package manifest
- Run package managers (`npm prune`, `pip-autoremove`, `cargo prune`)
- Rewrite git history or remove files from git history
- Detect secrets or credentials
- Fix failing tests
- Remove code accessed via dynamic patterns (getattr, globals, plugin loaders)

## Usage

```bash
# Full scan — all 5 domains
/wfc-housekeeping

# Specific domain
/wfc-housekeeping branches
/wfc-housekeeping dead-code
/wfc-housekeeping imports
/wfc-housekeeping files
/wfc-housekeeping dev-artifacts

# With flags
/wfc-housekeeping --safe          # Only unused imports (ruff --fix), no approval needed
/wfc-housekeeping --preview       # Scan and report only, don't fix anything
/wfc-housekeeping --aggressive    # Include borderline items (more approval prompts)

# Target specific path
/wfc-housekeeping dead-code wfc/scripts/
```

## The 5 Cleanup Domains

### 1. BRANCHES — Stale Branch Cleanup

**Scans:**

- Local branches merged into default branch
- Local branches with no remote tracking
- Remote branches merged into default branch
- Branches older than 30 days with no recent commits

**Detection:**

```bash
# Detect default branch
git remote show origin | grep 'HEAD branch' | cut -d':' -f2 | tr -d ' '

# List merged local branches (excluding default/current)
git branch --merged $(git remote show origin | grep 'HEAD branch' | cut -d':' -f2 | tr -d ' ') | grep -v -E '^\*|main|master|develop|trunk'

# List merged remote branches
git branch -r --merged origin/$(git remote show origin | grep 'HEAD branch' | cut -d':' -f2 | tr -d ' ') | grep -v -E 'main|master|develop|trunk|HEAD'

# List local branches with no remote
git branch -vv | grep ': gone]'

# Show branch age
git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/
```

**Auto-fix:** None. All branch deletions require approval.
**Approval required:** Delete any branch (local or remote).

**Safety:** NEVER delete the default branch, `develop`, or the current branch.

### 2. DEAD CODE — Unused Code Detection

**Scans:**

- Functions/classes with zero references outside their own file
- Commented-out code blocks (3+ consecutive commented lines)
- Unreachable code after return/raise/break/continue
- Empty `except: pass` blocks
- Unused variables (assigned but never read)

**Detection:**

```bash
# Find unused variables and redefined names
uv run ruff check --select F841,F811 .

# Find function/class definitions for manual reference check
grep -rn "^def \|^class " --include="*.py" .

# Find commented-out code blocks (3+ consecutive lines)
grep -Pzo '(\s*# [a-z].*\n){3,}' -r --include="*.py" .
```

**Manual verification required:** For each function/class found:

1. Search codebase for references: `grep -rn "function_name" --include="*.py" .`
2. Exclude definition file and `__init__.py` re-exports
3. Check for dynamic access patterns in same file: `getattr`, `globals()`, `__dict__`
4. If ANY dynamic pattern exists → mark as "UNSAFE: dynamic access"

**Auto-fix:** Remove unused imports only (via ruff --fix).
**Approval required:** Remove functions/classes, commented-out code, any code with dynamic access patterns.

**Safety:**

- NEVER remove code with `# TODO`, `# FIXME`, `# HACK` comments
- NEVER remove `__all__` exports or `__init__.py` re-exports
- NEVER remove code from files containing `getattr(`, `globals()`, or `__dict__[` without manual review
- NEVER assume test coverage is complete — warn user of coverage gaps

### 3. IMPORTS — Import Optimization

**Scans:**

- Unused imports
- Duplicate imports
- Import ordering (stdlib → third-party → local)

**Detection:**

```bash
# Check import issues
uv run ruff check --select F401,F811,I001 .

# Preview fixes
uv run ruff check --select F401,F811,I001 --fix --diff .
```

**Auto-fix:** All import issues (ruff is authoritative).
**Warning:** Ruff cannot detect imports used for side effects or dynamically accessed symbols. Review changes.

### 4. FILES — Orphaned & Redundant Files

**Scans:**

- `.pyc` files and `__pycache__` directories tracked by git
- Empty `__init__.py` files
- Temporary files (`.tmp`, `.bak`, `.swp`, `.orig`)
- Large files tracked by git (>1MB)

**Detection:**

```bash
# Find .pyc and __pycache__ tracked by git
git ls-files '*.pyc' '__pycache__'

# Find empty files
find . -name '*.py' -empty -not -path './.git/*'

# Find large files
find . -size +1M -not -path './.git/*' -not -path './node_modules/*' -not -path './.venv/*'

# Find temp files
git ls-files '*.tmp' '*.bak' '*.swp' '*.orig'
```

**NOTE:** This skill does NOT detect duplicate files (same content, different locations) — no reliable detection method is available.

**Auto-fix:** Remove `.pyc` files, `__pycache__` dirs, temp files.
**Approval required:** Remove empty `__init__.py`, orphaned files, large files.

### 5. DEV ARTIFACTS — Development Leftovers

**Scans:**

- Orphaned worktree directories
- Debug print statements (`print(`) in non-test Python files
- `breakpoint()` calls in non-test Python files
- Hardcoded `localhost`/`127.0.0.1` URLs in non-test files

**Test file definition:** Files matching `tests/**`, `test_*.py`, `*_test.py`, or `conftest.py`.

**Detection:**

```bash
# Orphaned worktrees
git worktree list --porcelain | grep 'prunable'

# Debug statements (Python only)
uv run ruff check --select T201,T203 .

# Hardcoded localhost in non-test files
grep -rn "localhost\|127.0.0.1" --include="*.py" . | grep -v -E "tests/|test_|_test\.py|conftest\.py"
```

**Auto-fix:** Prune orphaned worktrees.
**Approval required:** Remove debug statements, hardcoded URLs.

**Preserved (NEVER clean):**

- `.development/plans/`
- `.development/summaries/`

## Keep List — Persistent Memory

Items marked to **keep** are stored in `.development/housekeeping/keep-list.json`.

### Setup

```bash
# Create directory if missing
mkdir -p .development/housekeeping
```

### Keep List Format

```json
{
  "kept_items": [
    {
      "item": "feat/long-running-feature",
      "domain": "branches",
      "reason": "User chose to keep",
      "kept_on": "2026-02-15",
      "runs_kept": 1
    }
  ]
}
```

### Behavior

1. **On scan**: Read `.development/housekeeping/keep-list.json` (create directory/file if missing)
2. **On report**: Mark kept items with `KEPT (Nx since DATE)`
3. **On approval**: Update keep list when user chooses keep/delete
4. **On write**: Use atomic write (write to temp file, then rename) to prevent race conditions

## Workflow

### Step 0: SETUP

```bash
# Ensure keep list directory exists
mkdir -p .development/housekeeping

# Load keep list
cat .development/housekeeping/keep-list.json 2>/dev/null || echo '{"kept_items": []}'
```

### Step 1: SCAN

Run scanners for selected domains. Record:

- Domain, Item, Severity, Safety (auto-fix/approval), Keep status

### Step 2: REPORT

Present findings as table with kept items marked:

```markdown
## Housekeeping Report

### Branches (4 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 1 | feat/old-feature (merged, local) | low | approval | DELETE? |
| 2 | feat/long-running (local) | info | — | KEPT (3x since 2026-02-15) |

**Summary:** 4 items — 0 auto-fix, 3 approval-required, 1 previously kept
```

### Step 3: APPROVE

Prompt user: "Apply approved cleanups? (yes/skip #N/keep #N/preview)"

If non-interactive environment (no TTY) and no `--safe` flag: **Exit with error** rather than hang.

After approval:

- Update keep list with user choices
- Write atomically to prevent race conditions

### Step 4: EXECUTE

Process domains **sequentially** (parallel execution requires Task tool availability):

1. Apply approved changes for each domain
2. Run full test suite after all changes applied
3. If tests fail, report failure and offer rollback

**NOTE:** This skill runs the **full test suite**, not affected-only tests. Use `--preview` to scan without executing if the full suite is too slow.

### Step 5: VERIFY

After execution:

```bash
uv run pytest
```

If tests fail:

1. Report: "Tests failed after cleanup. Rolling back."
2. Discard all uncommitted changes: `git restore .`
3. Re-present approval prompt excluding the item(s) that caused failure
