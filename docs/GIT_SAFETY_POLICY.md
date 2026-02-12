# WFC Git Safety Policy

**CRITICAL PRINCIPLE:** WFC NEVER pushes to remote repositories. User must manually push after review.

## The Rule

### ❌ WFC NEVER DOES

- `git push` to any remote
- `git push --force` to any remote
- `git push origin main`
- `git push origin <branch>`
- Any automatic remote pushing

### ✅ WFC ONLY DOES

- `git merge` to **local main**
- `git commit` in worktrees
- `git rebase` in worktrees
- `git revert` for rollback (local only)

## Why This Rule Exists

1. **User Control** - User has final say before code goes to remote
2. **Review Opportunity** - User can inspect merged result before push
3. **Branch Protection** - Respects branch protection rules (PRs, etc.)
4. **Safety Net** - Easy to undo local operations before push
5. **Multi-Environment** - User controls which remote and when

## WFC Workflow

```
WFC builds/implements
    ↓
Quality checks pass
    ↓
Consensus review: APPROVED
    ↓
WFC merges to LOCAL main
    ↓
Integration tests pass
    ↓
[WFC STOPS HERE] ← User reviews local result
    ↓
User manually: git push origin main
```

## Modes and Safety

| Mode | Builds Code | Merges Local | Pushes Remote |
|------|-------------|--------------|---------------|
| `wfc-build` | ✅ Via subagent | ✅ After review | ❌ NEVER |
| `wfc-implement` | ✅ Via subagents | ✅ After review | ❌ NEVER |
| `wfc-plan` | ❌ Only plans | ❌ No merge | ❌ NEVER |
| `wfc-review` | ❌ Only reviews | ❌ No merge | ❌ NEVER |

## Review Requirements

WFC only merges to local main if:

1. **Quality checks pass** - Formatters, linters, tests
2. **Consensus review APPROVED** - Multi-agent review passes
3. **Integration tests pass** - Tests pass on local main after merge
4. **No critical issues** - No security vulnerabilities, data loss risks

If any fail:
- Automatic rollback (local revert)
- Worktree preserved for investigation
- User notified of failure

## User Push Workflow

After WFC merges locally, user decides:

### Option 1: Push Immediately
```bash
git push origin main
```

### Option 2: Review First
```bash
# Review what was merged
git log --oneline -5
git diff origin/main

# If good:
git push origin main

# If not good:
git revert HEAD  # Undo WFC's merge
```

### Option 3: Create PR
```bash
# Push to feature branch instead
git checkout -b feature/wfc-implemented
git cherry-pick main  # Take WFC's merge
git push origin feature/wfc-implemented

# Then create PR via GitHub/GitLab
```

## Safety Mechanisms

### 1. Consensus Review Gating

Merge only happens if `wfc-review` returns:
```json
{
  "consensus": {
    "passed": true,
    "overall_score": 8.5,
    "decision": "APPROVED"
  }
}
```

### 2. Integration Test Gating

Merge only happens if integration tests pass on local main:
```python
test_passed, duration, failed_tests, output = self._run_integration_tests()

if not test_passed:
    self._rollback(merge_sha, result)  # Revert local merge
    result.status = MergeStatus.ROLLED_BACK
```

### 3. Automatic Rollback

If merge breaks main locally:
- Immediate `git revert <merge_sha>`
- Main restored to passing state
- Worktree preserved for investigation
- Task re-queued for retry (if retryable)

### 4. Worktree Isolation

All agent work happens in isolated worktrees:
```
.worktrees/
├── task-001/  # Agent 1 works here (isolated)
├── task-002/  # Agent 2 works here (isolated)
└── task-003/  # Agent 3 works here (isolated)

main/          # Only touched after review passes
```

## Configuration

No configuration can override this rule. The following setting does NOT exist:

```json
{
  "merge": {
    "auto_push": false  // This setting doesn't exist - push is NEVER automatic
  }
}
```

## Error Messages

If user somehow triggers push behavior:

```
❌ ERROR: WFC does not push to remote repositories

This is a safety principle.

After WFC merges to local main, YOU must decide when to push:
  git push origin main

This gives you a chance to:
  1. Review the merged result
  2. Run additional tests
  3. Create a PR instead of direct push
  4. Revert if you change your mind
```

## Comparison: CI/CD vs WFC

| System | Builds | Tests | Merges | Pushes |
|--------|--------|-------|--------|--------|
| **GitHub Actions** | ✅ | ✅ | ✅ | ✅ Auto-push |
| **Jenkins** | ✅ | ✅ | ✅ | ✅ Auto-push |
| **WFC** | ✅ | ✅ | ✅ | ❌ **User pushes** |

**Why different?**
- CI/CD runs on remote servers (already in GitHub)
- WFC runs locally (user's machine)
- Local changes = user control before remote

## Enforcement

This rule is enforced by:

1. **No push code** - Codebase has zero `git push` calls in orchestrators/merge engines
2. **Documentation** - All docs emphasize user push
3. **Error handling** - If push attempted, error and block
4. **Code review** - Any PR adding auto-push will be rejected

## Exception: NONE

There are **NO exceptions** to this rule.

Even if:
- User requests it
- Tests pass
- Review approves
- Configuration enables it

**WFC NEVER pushes to remote.**

## Summary

```
┌──────────────────────────────────────┐
│  WFC's Responsibility                │
│  - Build code (via subagents)        │
│  - Run quality checks                │
│  - Get consensus review              │
│  - Merge to LOCAL main               │
│  - Run integration tests             │
│  - Rollback if tests fail            │
└──────────────────────────────────────┘
                 ↓
        [WFC STOPS HERE]
                 ↓
┌──────────────────────────────────────┐
│  User's Responsibility               │
│  - Review merged result              │
│  - Decide: push, PR, or revert       │
│  - git push origin main              │
└──────────────────────────────────────┘
```

---

**CRITICAL:** WFC coordinates. User controls remote.

This is **World Fucking Class** safety. 🏆
