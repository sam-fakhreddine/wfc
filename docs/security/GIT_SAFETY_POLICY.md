# WFC Git Workflow Policy

**NEW PHILOSOPHY (v2.0):** WFC creates GitHub PRs by default for team review and collaboration.

This document outlines WFC's git workflow policy, representing a fundamental shift from local-only development to GitHub-integrated collaboration.

---

## The New Rule

### ✅ WFC DEFAULT WORKFLOW

WFC now follows industry-standard GitHub PR workflow:

1. **Agent Implementation** - Code implemented in isolated worktree
2. **Quality Checks** - Formatting, linting, tests pass
3. **Consensus Review** - Multi-agent expert review (APPROVED)
4. **Push to Remote** ⭐ **NEW** - Branch pushed to origin
5. **Create GitHub PR** ⭐ **NEW** - Draft PR created automatically
6. **User Reviews** - Review PR on GitHub, request changes if needed
7. **Merge via GitHub** - User or team merges PR when ready

### What Changed from v1.0?

| Old (v1.0) | New (v2.0) |
|------------|------------|
| ❌ Never push to remote | ✅ Push feature branches |
| ❌ Local merge only | ✅ GitHub PR creation |
| ❌ Manual PR creation | ✅ Automatic PR creation |
| ❌ No CI/CD integration | ✅ Full GitHub Actions support |
| ✅ User controls merge | ✅ User controls merge (via GitHub) |

---

## Why PR Workflow?

### Benefits

1. **Team Collaboration** - PRs enable code review by teammates
2. **CI/CD Integration** - GitHub Actions run on every PR
3. **Audit Trail** - All changes tracked in GitHub history
4. **Branch Protection** - Enforce required reviews, status checks
5. **Modern Workflow** - Industry standard practice
6. **Better Context** - PR descriptions preserve decision rationale
7. **Discussion** - Inline comments and conversations

### Still Safe

- WFC never pushes directly to `main`/`master`
- All changes go through PR review process
- User has final approval before merge
- Respects branch protection rules
- Easy to close PR if not ready

---

## WFC Can Do (NEW)

### ✅ Allowed Operations

| Operation | Description | Safety Level |
|-----------|-------------|--------------|
| `git push origin <branch>` | Push feature branches | ✅ Safe |
| `gh pr create` | Create GitHub PRs | ✅ Safe |
| `git checkout -b <branch>` | Create feature branches | ✅ Safe |
| `git commit` | Commit to feature branches | ✅ Safe |
| `git merge <branch>` (local) | Merge to local main (legacy mode) | ⚠️ Requires config |

### ⚠️ Protected Operations

| Operation | Status | Reason |
|-----------|--------|--------|
| `git push origin main` | ❌ BLOCKED | Never push directly to protected branches |
| `git push --force origin main` | ❌ BLOCKED | Never force push to protected branches |
| `git push --force <feature>` | ⚠️ REQUIRES EXPLICIT REQUEST | Destructive, use `--force-with-lease` instead |

---

## Configuration

### Default PR Workflow

```json
{
  "merge": {
    "strategy": "pr",
    "pr": {
      "enabled": true,
      "base_branch": "main",
      "draft": true,
      "auto_push": true
    }
  }
}
```

**What happens:**

1. Code passes quality checks
2. Branch pushed to `origin`
3. Draft PR created on GitHub
4. You review PR and merge when ready

### Legacy Direct Merge

If you prefer local-only workflow (solo projects, no CI/CD):

```json
{
  "merge": {
    "strategy": "direct"
  }
}
```

**What happens:**

1. Code passes quality checks
2. Merged to local `main` branch
3. You manually push when ready: `git push origin main`

---

## Requirements

### GitHub CLI Installation

PR workflow requires `gh` CLI installed and authenticated.

**Install:**

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install --id GitHub.cli
```

**Authenticate:**

```bash
gh auth login
```

### Verification

Check if ready for PR workflow:

```bash
gh auth status
```

Should show:

```
✓ Logged in to github.com as <username>
✓ Git operations for github.com configured to use ssh protocol.
✓ Token: *******************
```

---

## Workflow Examples

### Example 1: Feature Implementation (PR Workflow)

```bash
# WFC implements feature
wfc implement plan/TASKS.md

# WFC output:
# ✅ Task TASK-001 complete
# ✅ Quality checks passed
# ✅ Consensus review: APPROVED (8.5/10)
# ✅ Pushed branch: feat/TASK-001-add-auth
# ✅ Created PR #42: https://github.com/user/repo/pull/42

# You review PR on GitHub
# Request changes if needed
# Merge when ready
```

### Example 2: Legacy Local Workflow

```bash
# Set config to direct merge
echo '{"merge": {"strategy": "direct"}}' > wfc.config.json

# WFC implements feature
wfc implement plan/TASKS.md

# WFC output:
# ✅ Task TASK-001 complete
# ✅ Merged to local main
# ⚠️  Remember to push: git push origin main

# You review local changes
git log -1
git diff HEAD~1

# Push when ready
git push origin main
```

### Example 3: Create PR from Existing Branch

You can also create PRs for existing branches:

```bash
# Using gh CLI directly
gh pr create \
  --title "TASK-001: Add authentication" \
  --body "Implements user authentication system" \
  --base main \
  --draft

# Or let WFC handle it (if it has PR data)
wfc pr create feat/TASK-001-add-auth
```

---

## Safety Guarantees

### What WFC Never Does

1. ❌ **Never** pushes directly to `main`/`master`
2. ❌ **Never** force-pushes to protected branches
3. ❌ **Never** bypasses branch protection rules
4. ❌ **Never** merges PRs automatically (you control merge)
5. ❌ **Never** pushes without passing quality checks
6. ❌ **Never** pushes sensitive files (`.env`, secrets, credentials)

### What You Control

1. ✅ **Review PR** before merging (always)
2. ✅ **Request changes** if needed
3. ✅ **Close PR** if you change your mind
4. ✅ **Revert PR** after merge if needed
5. ✅ **Choose workflow** (PR vs direct merge)
6. ✅ **Override config** per-project or globally

---

## Git Hooks Integration

WFC installs optional git hooks for workflow enforcement.

### Installation

```bash
# Install WFC git hooks
wfc hooks install

# Check status
wfc hooks status

# Uninstall
wfc hooks uninstall
```

### Hooks Installed

| Hook | Purpose | Enforcement |
|------|---------|-------------|
| `pre-commit` | Warn about direct commits to `main` | ⚠️ Warning only |
| `commit-msg` | Validate commit message format | ⚠️ Warning only |
| `pre-push` | Warn about pushing to protected branches | ⚠️ Warning only |

### Hook Behavior

**Soft Enforcement (Default):**

- Hooks **warn** but **don't block**
- Violations logged to telemetry
- Developer experience prioritized

**Example:**

```bash
git checkout main
touch test.txt
git add test.txt
git commit -m "test"

# Output:
# ⚠️  WARNING: Committing directly to main
# Consider: git checkout -b feat/TASK-XXX-description
# ✅ Commit successful
```

---

## Migration Guide

### From v1.0 to v2.0

If you're upgrading from WFC v1.0 (local-only workflow):

**Breaking Changes:**

1. Default workflow changed from `direct` to `pr`
2. Requires `gh` CLI installed and authenticated
3. Pushes to remote (previously never pushed)

**Migration Steps:**

#### Step 1: Install gh CLI

```bash
# macOS
brew install gh

# Ubuntu
sudo apt install gh

# Authenticate
gh auth login
```

#### Step 2: Update Config (Optional)

If you want to keep old behavior (local-only):

```bash
# Project-specific
cat > wfc.config.json << EOF
{
  "merge": {
    "strategy": "direct"
  }
}
EOF

# Or global
mkdir -p ~/.claude
cat > ~/.claude/wfc.config.json << EOF
{
  "merge": {
    "strategy": "direct"
  }
}
EOF
```

#### Step 3: Test PR Workflow

```bash
# Try new PR workflow
wfc implement test-task

# Check GitHub for new PR
gh pr list

# If good, nothing else needed!
```

#### Step 4: Install Hooks (Optional)

```bash
# Install git hooks for warnings
wfc hooks install
```

---

## Troubleshooting

### PR Creation Fails

**Error: `gh CLI not found`**

```bash
# Install gh CLI
brew install gh  # macOS
sudo apt install gh  # Ubuntu

# Authenticate
gh auth login
```

**Error: `gh not authenticated`**

```bash
gh auth login
# Follow prompts to authenticate
```

**Error: `Push failed`**

```bash
# Check remote exists
git remote -v

# Add remote if missing
git remote add origin https://github.com/user/repo.git

# Try manual push
git push -u origin <branch>
```

### Hooks Not Working

**Check installation:**

```bash
wfc hooks status
```

**Reinstall hooks:**

```bash
wfc hooks uninstall
wfc hooks install
```

---

## Workflow Enforcement

WFC tracks workflow compliance via telemetry.

### Metrics Tracked

- Direct commits to `main` (warning)
- Non-conventional commit messages (warning)
- Force pushes (warning)
- PR creation success rate
- Average PR review time

### Compliance Dashboard

```bash
# View workflow metrics
wfc metrics workflow

# Example output:
# Workflow Compliance (Last 30 Days)
# ===================================
# PR Creation Success: 95% (38/40)
# Direct Main Commits: 2 warnings
# Force Pushes: 0 warnings
# Conventional Commits: 90% (36/40)
```

---

## FAQ

### Q: Will WFC ever push without asking?

**A:** WFC pushes branches automatically in PR workflow (configurable via `merge.pr.auto_push`). It **never** pushes to protected branches (`main`/`master`).

### Q: Can I review before PR creation?

**A:** Yes! Set `merge.pr.auto_push: false` to review before push:

```json
{
  "merge": {
    "pr": {
      "auto_push": false
    }
  }
}
```

Then manually push when ready:

```bash
git push -u origin <branch>
wfc pr create <branch>
```

### Q: What if I don't have GitHub?

**A:** Use legacy direct merge workflow:

```json
{
  "merge": {
    "strategy": "direct"
  }
}
```

### Q: Can I use GitLab/Bitbucket?

**A:** Not yet. PR workflow currently supports GitHub only. Use direct merge for other platforms. GitLab/Bitbucket support planned for future release.

### Q: Are hooks required?

**A:** No. Hooks are optional and provide warnings only. You can disable them entirely:

```bash
wfc hooks uninstall
```

---

## Summary

### New Workflow (v2.0)

✅ **PR-first** - GitHub integration by default
✅ **Team collaboration** - Built for team development
✅ **CI/CD ready** - GitHub Actions run on PRs
✅ **Audit trail** - All changes tracked
✅ **User controlled** - You approve all merges
✅ **Backward compatible** - Legacy mode available

### Safety Unchanged

✅ **Never push to main** directly
✅ **Quality checks** before submission
✅ **Consensus review** by experts
✅ **User approval** required for merge
✅ **Easy rollback** - Just close the PR

---

**This is World Fucking Class.** 🚀
