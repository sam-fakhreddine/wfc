# wfc-housekeeping

## What It Does

`wfc-housekeeping` performs systematic project hygiene across five domains: stale branches, dead code, unused imports, orphaned files, and development artifacts. It always runs analysis first and presents a categorized findings table before touching anything. You review and approve each cleanup category, then parallel subagents execute the approved changes with test validation after each domain. If any cleanup causes a test failure, that change is rolled back automatically.

## When to Use It

- Periodically (e.g., before a release or at the start of a sprint) to reduce accumulated technical debt
- After a long feature development period when merged branches, debug prints, and unused imports have accumulated
- Before onboarding new contributors to ensure the codebase is in clean, navigable shape
- When a reviewer or CI tool flags code quality issues that are spread across many files

## Usage

```bash
# Full scan across all 5 domains
/wfc-housekeeping

# Scan a specific domain only
/wfc-housekeeping branches
/wfc-housekeeping dead-code
/wfc-housekeeping imports
/wfc-housekeeping files
/wfc-housekeeping dev-artifacts

# Scan and report without fixing anything
/wfc-housekeeping --preview

# Apply only auto-fixable items without approval prompts
/wfc-housekeeping --safe

# Include borderline items (more approval prompts)
/wfc-housekeeping --aggressive

# Target a specific path
/wfc-housekeeping dead-code wfc/scripts/
```

## Example

```
## Housekeeping Report

### Branches (4 items)
| # | Item                              | Severity | Safety       | Action |
|---|-----------------------------------|----------|--------------|--------|
| 1 | feat/old-rate-limiter (merged)    | low      | auto-fix     | DELETE |
| 2 | fix/stale-pr (merged, remote)     | low      | approval     | DELETE |
| 3 | entire/checkpoints/v1 (local)     | info     | —            | KEPT (3x since 2026-02-01) |
| 4 | claude/experiment (no remote)     | medium   | approval     | DELETE? |

### Dead Code (2 items)
| # | Item                                      | Severity | Safety   | Action |
|---|-------------------------------------------|----------|----------|--------|
| 5 | wfc/old_module.py:deprecated_func() (0 refs) | medium | approval | REMOVE |
| 6 | 3 commented-out blocks in scripts/        | low      | approval | REMOVE |

### Imports (8 items)
| # | Item                                  | Severity | Safety   | Action |
|---|---------------------------------------|----------|----------|--------|
| 7 | 8 unused imports across 5 files       | low      | auto-fix | FIX    |

### Dev Artifacts (2 items)
| # | Item                          | Severity | Safety   | Action |
|---|-------------------------------|----------|----------|--------|
| 8 | 2 orphaned worktrees          | low      | auto-fix | PRUNE  |
| 9 | 14 TODOs across codebase      | info     | —        | REPORT |

Summary: 9 items — 4 auto-fix, 3 approval-required, 1 previously kept, 1 info-only

Proceed with cleanup? [y/n]: y

Executing (parallel agents)...
  [Branches] Deleted feat/old-rate-limiter, fix/stale-pr
  [Imports]  Fixed 8 unused imports via ruff --fix
  [Files]    Pruned 2 orphaned worktrees

Running test suite...
✅ 424 passed — no regressions

## Housekeeping Complete
  Cleaned: 4 items | Skipped: 2 (user kept) | Info: 3 TODOs (no action)
```

Items you choose to keep are stored in `.development/housekeeping/keep-list.json` and shown with their history on subsequent runs so you can change your mind at any time.

## Options

| Flag | Description |
|------|-------------|
| `--preview` | Scan and report only, apply nothing |
| `--safe` | Auto-fix only, skip approval prompts |
| `--aggressive` | Include borderline candidates |
| `--show-kept` | Display the current keep list |
| `--clear-kept` | Reset the keep list |
| `--forget "<item>"` | Remove one item from the keep list |

Protected items that are never touched: `main`, `develop`, the current branch, `.development/plans/`, `.development/summaries/`.

## Integration

**Produces:**

- Cleaned codebase (fewer branches, imports, dead code, orphaned files)
- Updated `.development/housekeeping/keep-list.json` reflecting user decisions
- Optional housekeeping summary saved to `.development/summaries/`

**Consumes:**

- Git history (branch analysis via `git branch --merged`)
- Ruff and black (import cleanup and lint analysis)
- Full test suite (regression verification after each domain)

**Next step:** After housekeeping, commit the cleanup changes on a dedicated branch and open a PR via `/wfc-build` or push directly. Use `/wfc-sync` if you want to update rule documentation to match the cleaned-up codebase.
