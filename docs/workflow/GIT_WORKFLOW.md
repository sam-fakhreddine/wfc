# Git Workflow v3.0 — Autonomous Develop-First Branching

WFC uses a develop-first branching model where agents ship autonomously to `develop`
and humans control when stable code promotes to `main`.

---

## The Model

- **`develop`** — the integration branch. All agents and most human work lands here.
  CI runs on every merge; failures trigger automatic revert + bug issue.
- **`main`** — the stable/released branch. Only release candidates promote here after
  a 24-hour soak period. Agents never touch `main` directly.

This separation means `main` is always releasable and `develop` absorbs risk.

---

## Branch Types

### `claude/*` — Agent branches

Created by WFC agents during `/wfc-build`, `/wfc-implement`, or `/wfc-lfg` runs.

- Named automatically: `claude/TASK-001-add-rate-limiting-1738000000`
- Always target `develop` (never `main`)
- Auto-merge when CI passes (no human approval required)
- Cleaned up after merge

### `feat/*` and `fix/*` — Human branches

Created by developers for intentional feature or bug-fix work.

- Require PR review before merging to `develop`
- Follow conventional commit naming: `feat/add-redis-cache`, `fix/null-pointer-on-login`
- Open a PR to `develop`, not to `main`

### `rc/vX.Y.Z` — Release candidates

Cut from `develop` automatically on a schedule (Friday 18:00 UTC via `cut-rc.yml`).

- Soak for 24 hours with green CI before they can promote to `main`
- You decide when to merge the RC PR to `main` — WFC never merges it for you
- Once merged, `promote-rc.yml` tags `vX.Y.Z` and creates a release

---

## Why `develop` Rejects Direct Pushes

The `develop` branch has a required status check: **"Fast Validation"**. This means
you cannot push commits directly to `develop`, even from a local merge:

```bash
# This will fail:
git checkout develop
git merge origin/main --no-edit
git push origin develop
# remote: error: GH006: Protected branch, required status checks failed
```

You must route all changes through a PR:

```bash
# Create a branch from the merged state
git checkout -b claude/my-branch
git push origin HEAD          # push the branch (no protection on branches)
gh pr create --base develop   # open PR — CI runs — auto-merges
```

---

## The Autonomous Loop

```
Issue (agent-ready) -> Agent Dispatch -> /wfc-build -> TDD -> Review
                                                               |
                                                     Push claude/* branch
                                                               |
                                                   PR to develop (auto-merge)
                                                               |
                                                 develop-health.yml (self-healing)
                                                               |
                                               cut-rc.yml (Friday 18:00 UTC)
                                                               |
                                                 rc/vX.Y.Z -> PR to main
                                                               |
                                           promote-rc.yml (24h soak + green CI)
                                                               |
                                                     Tag vX.Y.Z -> Release
```

Agents run this loop without human intervention. You review releases, not individual
feature PRs (unless you want to).

---

## Self-Healing on `develop`

`develop-health.yml` runs the full test suite after every merge. If tests fail:

1. The failing commit is automatically reverted
2. A bug issue is opened with the failure details and commit reference
3. `develop` returns to a green state
4. The agent that caused the failure is notified via the issue

This means a broken agent branch never leaves `develop` broken for long.

---

## RC Soak Period

Release candidates must stay green for 24 continuous hours before they can merge to
`main`. The `promote-rc.yml` workflow enforces this:

- Checks CI status every 30 minutes during the soak
- Any failure resets the 24-hour clock
- After 24 hours of green, it posts a "ready to promote" comment on the RC PR
- You merge the PR manually — WFC never auto-merges to `main`

---

## User Controls Releases

WFC is fully autonomous up to the RC PR. From there, you decide:

- Review the RC PR on GitHub
- Merge when you're confident
- Or close it to skip the release (a new RC will be cut next Friday)

---

## Conflict Resolution: Merging `main` into `develop`

If `main` gets ahead of `develop` (e.g., after a hotfix), use this pattern:

```bash
# 1. Pull latest and merge main into develop locally
git checkout develop
git pull origin develop
git merge origin/main --no-edit

# 2. Route through a branch (develop rejects direct pushes)
git checkout -b claude/merge-main-into-develop-$(date +%s)
git push origin HEAD

# 3. Open PR to develop
gh pr create --base develop --title "chore: sync main -> develop" \
  --body "Conflict resolution merge from main into develop."
```

CI will run on the PR, it will auto-merge, and `develop` will be back in sync.

---

## Quick Reference

| Branch | Who creates it | Target | Merge method |
|--------|----------------|--------|--------------|
| `claude/*` | WFC agents | `develop` | Auto (CI) |
| `feat/*` | Humans | `develop` | PR review |
| `fix/*` | Humans | `develop` | PR review |
| `rc/vX.Y.Z` | `cut-rc.yml` | `main` | Manual (you) |

**Never push directly to `develop` or `main`.** Always use a branch + PR.

See also: `docs/security/GIT_SAFETY_POLICY.md` for protected-branch enforcement rules.
