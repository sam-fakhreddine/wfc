---
name: wfc-housekeeping
description: Systematic project hygiene — clean dead code, stale branches, orphaned files, unused imports, and development artifacts. Runs analysis first, presents findings for approval, then executes cleanup with full test validation. Use for periodic maintenance, pre-release cleanup, or technical debt reduction.
license: MIT
---

# WFC:HOUSEKEEPING - Project Hygiene & Cleanup

**Keep the codebase World Fucking Class.** Systematic cleanup with safety guardrails.

## What It Does

1. **Scan** - Analyze the codebase for cleanup opportunities across 5 domains
2. **Report** - Present categorized findings with severity and safety ratings
3. **Approve** - User reviews and selects which cleanups to apply
4. **Execute** - Apply cleanups in parallel (safe categories) with test validation
5. **Verify** - Run full test suite to confirm no regressions

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
/wfc-housekeeping --safe          # Only auto-fixable items (no approval needed)
/wfc-housekeeping --preview       # Scan and report only, don't fix anything
/wfc-housekeeping --aggressive    # Include borderline items (more approval prompts)

# Target specific path
/wfc-housekeeping dead-code wfc/scripts/
```

## The 5 Cleanup Domains

### 1. BRANCHES — Stale Branch Cleanup

**Scans:**

- Local branches merged into main/develop
- Local branches with no remote tracking
- Remote branches merged into main/develop
- Branches older than 30 days with no recent commits

**Commands to run:**

```bash
# List merged local branches (excluding main/develop/current)
git branch --merged main | grep -v -E '^\*|main|develop'

# List merged remote branches
git branch -r --merged origin/main | grep -v -E 'main|develop|HEAD'

# List local branches with no remote
git branch -vv | grep ': gone]'

# Show branch age (last commit date)
git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/
```

**Auto-fix:** Delete local merged branches.
**Approval required:** Delete remote branches, delete unmerged branches.

**Safety:** NEVER delete `main`, `develop`, or the current branch.

### 2. DEAD CODE — Unused Code Detection

**Scans:**

- Functions/classes with zero references outside their own file
- Commented-out code blocks (3+ consecutive commented lines)
- Unreachable code after return/raise/break/continue
- Empty `except: pass` blocks
- Unused variables (assigned but never read)

**How to detect:**

For each Python function/class definition found via Grep:

1. Search the entire codebase for references to that name
2. Exclude the definition file itself and `__init__.py` re-exports
3. If zero external references → candidate for removal

```bash
# Find all function definitions
uv run ruff check --select F841,F811 .  # Unused variables, redefined

# Find commented-out code blocks
# Grep for 3+ consecutive lines starting with #(space)(lowercase/import/def/class/if/for/return)
```

**Auto-fix:** Remove unused imports (ruff --fix), remove empty `except: pass`.
**Approval required:** Remove functions/classes, remove commented-out code.

**Safety:**

- NEVER remove code with `# TODO`, `# FIXME`, `# HACK` comments (intentional)
- NEVER remove `__all__` exports or `__init__.py` re-exports
- NEVER remove test fixtures/utilities (check `tests/` and `conftest.py` usage)
- If ANY usage path exists, prompt user

### 3. IMPORTS — Import Optimization

**Scans:**

- Unused imports
- Duplicate imports
- Import ordering (stdlib → third-party → local)
- Star imports (`from x import *`)

**Commands:**

```bash
# Ruff handles all of this
uv run ruff check --select F401,F811,I001,F403 .
uv run ruff check --select F401,F811,I001,F403 --fix --diff .  # Preview fixes
```

**Auto-fix:** All import issues (ruff is authoritative here).

### 4. FILES — Orphaned & Redundant Files

**Scans:**

- `.pyc` files and `__pycache__` directories not in `.gitignore`
- Empty `__init__.py` files that serve no purpose
- Duplicate files (same content, different locations)
- Files not imported/referenced anywhere
- Temporary files (`.tmp`, `.bak`, `.swp`, `.orig`)
- Large files that shouldn't be in version control (>1MB)

**Detection:**

```bash
# Find .pyc and __pycache__ tracked by git
git ls-files '*.pyc' '__pycache__'

# Find empty files
find . -name '*.py' -empty -not -path './.git/*'

# Find large files
find . -size +1M -not -path './.git/*' -not -path './node_modules/*'

# Find temp files
git ls-files '*.tmp' '*.bak' '*.swp' '*.orig'
```

**Auto-fix:** Remove `.pyc` files, `__pycache__` dirs, temp files.
**Approval required:** Remove empty `__init__.py`, orphaned files, large files.

### 5. DEV ARTIFACTS — Development Leftovers

**Scans:**

- Orphaned worktree directories (`.worktrees/`)
- Debug print statements (`print(`, `console.log(`, `debugger`)
- Hardcoded `localhost`/`127.0.0.1` URLs outside of tests
- `breakpoint()` calls
- Files with `TODO` or `FIXME` (report only, don't remove)

**Preserved (NEVER clean):**

- `.development/plans/` — Plan history is valuable project context. Never delete.
- `.development/summaries/` — Session summaries are kept for reference.

**Detection:**

```bash
# Orphaned worktrees
git worktree list --porcelain | grep 'prunable'

# Debug statements in Python files (excluding tests)
uv run ruff check --select T201,T203 .  # print statements, pdb
```

**Auto-fix:** Prune orphaned worktrees.
**Approval required:** Remove debug statements, TODO/FIXME items (report only).
**Never touch:** `.development/plans/`, `.development/summaries/`.

## Keep List — Persistent Memory

Items the user chose to **keep** in previous runs are stored in `.development/housekeeping/keep-list.json`. This file persists across sessions and is consulted every run.

### Keep List Format

```json
{
  "kept_items": [
    {
      "item": "entire/checkpoints/v1",
      "domain": "branches",
      "reason": "User chose to keep",
      "kept_on": "2026-02-15",
      "runs_kept": 1
    },
    {
      "item": "wfc/scripts/old_helper.py",
      "domain": "dead-code",
      "reason": "Still referenced in docs",
      "kept_on": "2026-02-14",
      "runs_kept": 3
    }
  ]
}
```

### How It Works

1. **On scan**: After finding cleanup candidates, read `.development/housekeeping/keep-list.json`
2. **On report**: Items on the keep list get a special marker in the table: `KEPT (2x)` showing how many times they've been kept. These items are **still shown** — the user can always change their mind and delete them.
3. **On approval**: When the user says "keep" for an item, add/update it in the keep list with today's date and increment `runs_kept`.
4. **On delete**: When the user deletes a previously-kept item, remove it from the keep list.

### Keep List in Reports

Previously-kept items appear with context so the user remembers why:

```markdown
### Branches (4 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 1 | feat/old-feature (merged, local) | low | auto-fix | DELETE |
| 2 | fix/stale-pr (merged, remote) | low | approval | DELETE |
| 3 | entire/checkpoints/v1 (local) | info | — | KEPT (3x since 2026-02-15) |
| 4 | claude/experiment (no remote) | medium | approval | DELETE? |
```

The `KEPT (3x since 2026-02-15)` marker tells the user: "you've seen this 3 times and chosen to keep it each time, first on Feb 15th." This is informational — the user can still override and delete it.

### Managing the Keep List

```bash
# View what's on the keep list
/wfc-housekeeping --show-kept

# Clear the keep list (start fresh)
/wfc-housekeeping --clear-kept

# Remove a specific item from the keep list
/wfc-housekeeping --forget "entire/checkpoints/v1"
```

## Workflow

### Step 0: LOAD KEEP LIST

Before scanning, read `.development/housekeeping/keep-list.json` if it exists. If the file doesn't exist, start with an empty keep list.

```bash
# Check for keep list
cat .development/housekeeping/keep-list.json 2>/dev/null || echo '{"kept_items": []}'
```

### Step 1: SCAN

Run all applicable scanners. For each finding, record:

- **Domain**: branches | dead-code | imports | files | dev-artifacts
- **Item**: What was found (file path, branch name, function name)
- **Severity**: critical | high | medium | low | info
- **Safety**: auto-fix | approval-required
- **Effort**: Size of change (lines affected)
- **Keep status**: Check if item is on the keep list

### Step 2: REPORT

Present findings as a categorized table. Items on the keep list are marked with their history:

```markdown
## Housekeeping Report

### Branches (4 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 1 | feat/old-feature (merged, local) | low | auto-fix | DELETE |
| 2 | fix/stale-pr (merged, remote) | low | approval | DELETE |
| 3 | entire/checkpoints/v1 (local) | info | — | KEPT (2x since 2026-02-15) |
| 4 | claude/experiment (no remote) | medium | approval | DELETE? |

### Dead Code (2 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 5 | wfc/old_module.py:deprecated_func() (0 refs) | medium | approval | REMOVE |
| 6 | 3 commented-out blocks in scripts/ | low | approval | REMOVE |

### Imports (8 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 7 | 8 unused imports across 5 files | low | auto-fix | FIX |

### Files (1 item)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 8 | 2 .pyc files tracked by git | low | auto-fix | REMOVE |

### Dev Artifacts (2 items)
| # | Item | Severity | Safety | Action |
|---|------|----------|--------|--------|
| 9 | 2 orphaned worktrees | low | auto-fix | PRUNE |
| 10 | 14 TODOs across codebase | info | — | REPORT |

---

**Summary:** 10 items found — 4 auto-fix, 4 approval-required, 1 previously kept, 1 info-only

Proceed with cleanup?
```

### Step 3: APPROVE

Use **AskUserQuestion** to get user approval:

- "Apply all auto-fixes + approved items?"
- User can override individual items (e.g., "skip #4, fix #5, delete #3")
- `--safe` mode: skip this step, only apply auto-fix items
- `--preview` mode: stop here, don't apply anything

**After approval:**

- Items the user chose to **keep** → add/update in keep list (increment `runs_kept`, update date)
- Items the user chose to **delete** that were on the keep list → remove from keep list
- Write updated keep list to `.development/housekeeping/keep-list.json`

### Step 4: EXECUTE

Apply approved cleanups. Parallelize by domain using Task tool subagents:

- **Branches agent**: Deletes approved branches (local first, then remote)
- **Code agent**: Removes dead code, fixes imports (runs `uv run ruff check --fix`)
- **Files agent**: Removes orphaned files, cleans dev artifacts, prunes worktrees

Each agent:

1. Applies its changes
2. Runs `uv run pytest` on affected test files
3. Reports what was changed

### Step 5: VERIFY

After all agents complete:

```bash
# Run full test suite
uv run pytest --tb=short -q

# Run linters
uv run ruff check .
uv run black --check .

# Verify git status is clean (only expected changes)
git status
```

If tests fail → **rollback** the offending change and report which cleanup caused the failure.

### Step 6: REPORT

Display final summary:

```markdown
## Housekeeping Complete

**Cleaned:** 8 items
**Skipped:** 2 items
**Info:** 1 item

### Changes Applied
- Deleted 3 local merged branches
- Deleted 1 remote merged branch
- Fixed 8 unused imports (ruff --fix)
- Removed 2 .pyc files from tracking
- Pruned 2 orphaned worktrees

### Skipped
- entire/checkpoints/v1 — user chose to keep
- claude/experiment — user chose to keep

### Info (no action taken)
- 14 TODOs across codebase (run /wfc-housekeeping --type todo for details)

### Verification
- Tests: 424 passed, 9 failed (pre-existing)
- Lint: clean
- Format: clean

No regressions introduced.
```

## Git Safety

**CRITICAL:** Same rules as all WFC skills.

- NEVER force-push
- NEVER delete `main` or `develop`
- NEVER delete the current branch
- NEVER delete remote branches without explicit user approval
- NEVER commit cleanup changes without test verification
- All branch deletions are logged for audit

## Integration with WFC

### Complements

- `/wfc-retro` — Retro can recommend running housekeeping
- `/wfc-build` / `/wfc-implement` — Run housekeeping before starting new features
- `/wfc-pr-comments` — Reviewers may request cleanup

### Produces

- Clean codebase (fewer files, cleaner imports, no dead branches)
- Housekeeping report (optional: save to `.development/summaries/`)

### Consumes

- Git history (branch analysis)
- Ruff/black (import and lint analysis)
- Test suite (verification)

## Configuration

```json
{
  "housekeeping": {
    "branch_age_threshold_days": 30,
    "preserve_dev_plans": true,
    "preserve_dev_summaries": true,
    "max_file_size_mb": 1,
    "auto_fix_imports": true,
    "auto_prune_worktrees": true,
    "protected_branches": ["main", "develop"],
    "excluded_paths": [".git", "node_modules", ".venv"],
    "report_todos": true
  }
}
```

## Philosophy

**ELEGANT**: Simple scan → report → approve → execute flow
**MULTI-TIER**: Scanners (logic) separated from reporting (presentation)
**PARALLEL**: Domain agents run concurrently during execution
**SAFE**: User approval gate, test verification, rollback on failure
