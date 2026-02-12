# WFC Git Hooks & Telemetry Implementation

**Status**: ✅ **COMPLETE** (Phases 3 & 6)

This document describes the git hooks and telemetry implementation for WFC workflow enforcement and compliance tracking.

---

## Phase 3: Git Hooks Integration ✅

### Overview

WFC provides optional git hooks that warn about workflow violations using **soft enforcement** (warnings only, never blocks).

### Implemented Hooks

#### 1. pre-commit Hook

**File**: `wfc/wfc-tools/gitwork/hooks/pre_commit.py`

**Checks**:
- ⚠️ Warn if committing to protected branches (main/master/develop/production)
- ⚠️ Validate branch naming convention (feat/TASK-XXX-description)
- ⚠️ Detect sensitive files (.env, credentials, keys, tokens)

**Example Output**:
```bash
$ git commit -m "test"

⚠️  WARNING: Committing directly to 'main'
   Consider: git checkout -b feat/TASK-XXX-description

✅ Commit allowed (soft enforcement - 1 warnings)
```

**Enforcement**: Never blocks commits

---

#### 2. commit-msg Hook

**File**: `wfc/wfc-tools/gitwork/hooks/commit_msg.py`

**Checks**:
- ⚠️ Validate conventional commit format
- ⚠️ Check for TASK-XXX reference
- ⚠️ Suggest improvements

**Valid Formats**:
- `TASK-001: Add rate limiting` (preferred)
- `feat: add user authentication`
- `fix(api): resolve timeout`
- `chore: update dependencies`

**Example Output**:
```bash
$ git commit -m "Added feature"

⚠️  WARNING: Commit message doesn't follow convention
   Suggestion: Use: TASK-XXX: description OR feat/fix/chore: description

   Examples:
     - TASK-001: Add rate limiting to API
     - feat: add user authentication
     - fix(api): resolve timeout issue

✅ Commit allowed (soft enforcement - message format warning)
```

**Enforcement**: Never blocks commits

---

#### 3. pre-push Hook

**File**: `wfc/wfc-tools/gitwork/hooks/pre_push.py`

**Checks**:
- ⚠️ Warn if pushing to protected branches
- ⚠️ Warn about force pushes
- ⚠️ Log push telemetry

**Example Output**:
```bash
$ git push origin main

⚠️  WARNING: Pushing to protected branch 'main'
   Local branch: main
   Remote: git@github.com:user/repo.git

   Consider:
     1. Create a PR instead
     2. Use WFC PR workflow (default)
     3. Ensure you have permission to push to main

✅ Push allowed (soft enforcement - 1 warnings)
```

**Enforcement**: Never blocks pushes

---

### Hook Installer

**File**: `wfc/wfc-tools/gitwork/hooks/installer.py`

**Features**:
- Non-destructive installation (preserves existing hooks)
- Automatic wrapping of existing hooks
- Easy uninstall with restore

**CLI Commands**:

```bash
# Install all WFC hooks
python -m wfc.wfc_tools.gitwork.hooks.installer install

# Uninstall all WFC hooks
python -m wfc.wfc_tools.gitwork.hooks.installer uninstall

# Check hook status
python -m wfc.wfc_tools.gitwork.hooks.installer status
```

**Status Output**:
```
WFC Git Hooks Status
==================================================

Hook: pre-commit
  Installed:    ✅
  Executable:   ✅
  WFC-managed:  ✅

Hook: commit-msg
  Installed:    ✅
  Executable:   ✅
  WFC-managed:  ✅

Hook: pre-push
  Installed:    ✅
  Executable:   ✅
  WFC-managed:  ✅

Summary: 3/3 WFC hooks installed
```

---

### Hook Architecture

**Non-Destructive Wrapping**:

```bash
#!/bin/bash
# WFC-managed hook - installed by WFC Hook Installer
# To uninstall: wfc hooks uninstall

# Run WFC hook
"/usr/bin/python3" "/path/to/hook/script.py" "$@"
exit_code=$?

# WFC uses soft enforcement - always exit 0 to never block
exit 0

# Original hook preserved below
# ... (existing hook content) ...
```

**Benefits**:
- Preserves existing hooks (e.g., Claude Code hooks)
- Easy to uninstall (restores original)
- No conflicts with other tools

---

## Phase 6: Telemetry & Tracking ✅

### Overview

WFC telemetry tracks workflow compliance, PR creation, and hook violations for observability and metrics.

### New Event Types

**File**: `wfc/shared/telemetry_auto.py` (extended)

#### 1. PR Creation Events

**Event**: `pr_created`

**Data**:
```json
{
  "event": "pr_created",
  "timestamp": "2026-02-12T11:30:00",
  "task_id": "TASK-001",
  "pr_url": "https://github.com/user/repo/pull/42",
  "pr_number": 42,
  "branch": "feat/TASK-001-rate-limiting",
  "success": true,
  "pushed": true,
  "draft": true,
  "base_branch": "main",
  "review_score": 8.5
}
```

**Logged**: When PR is created via `merge_engine.create_pr()`

---

#### 2. Hook Warning Events

**Event**: `hook_warning`

**Data**:
```json
{
  "event": "hook_warning",
  "timestamp": "2026-02-12T11:25:00",
  "hook": "pre-commit",
  "violation": "direct_commit_to_protected",
  "branch": "main",
  "user_bypassed": false
}
```

**Violations Tracked**:
- `direct_commit_to_protected` - Committing to main/master
- `non_conventional_branch` - Invalid branch name
- `sensitive_files_staged` - Sensitive files in commit
- `non_conventional_commit` - Bad commit message format
- `push_to_protected` - Pushing to protected branch
- `force_push` - Force push detected

**Logged**: Automatically by git hooks

---

#### 3. Commit Events

**Event**: `commit_with_task`

**Data**:
```json
{
  "event": "commit_with_task",
  "timestamp": "2026-02-12T11:26:00",
  "hook": "commit-msg",
  "task_id": "TASK-001",
  "message": "TASK-001: Add rate limiting to API"
}
```

**Logged**: When commit includes TASK-XXX reference

---

### Telemetry API

#### Generic Event Logging

```python
from wfc.shared.telemetry_auto import log_event

# Log PR creation
log_event("pr_created", {
    "pr_url": "https://github.com/user/repo/pull/42",
    "task_id": "TASK-001",
    "success": True
})

# Log hook warning
log_event("hook_warning", {
    "hook": "pre-commit",
    "violation": "direct_commit_to_protected",
    "branch": "main"
})

# Log custom event
log_event("custom_event", {
    "data": "value"
})
```

#### Workflow Metrics

```python
from wfc.shared.telemetry_auto import get_workflow_metrics, print_workflow_metrics

# Get metrics programmatically
metrics = get_workflow_metrics(days=30)
print(f"PR success rate: {metrics['pr_creation_success_rate']:.1f}%")

# Print formatted metrics
print_workflow_metrics(days=30)
```

**Output**:
```
============================================================
📊 WFC WORKFLOW METRICS (Last 30 Days)
============================================================

PR Creation:
  Total PRs: 38
  Successful: 36
  Success Rate: 94.7%

Workflow Compliance:
  Direct Main Commits: 2 warnings
  Force Pushes: 0 warnings
  Conventional Commits: 36/40 (90.0%)

Recent Hook Warnings (5):
  - [pre-commit] direct_commit_to_protected
  - [commit-msg] non_conventional_commit
  - [pre-commit] sensitive_files_staged

============================================================
```

---

### Storage

**Location**: `~/.wfc/telemetry/`

**Files**:
- `session-YYYYMMDD-HHMMSS.jsonl` - Session metrics (tasks)
- `aggregate.json` - Aggregated task metrics
- `events.jsonl` - Generic events (NEW - hooks, PRs, etc.)

**Format**: JSONL (JSON Lines) for easy parsing and streaming

---

### Integration Points

#### 1. Merge Engine

**File**: `wfc/skills/implement/merge_engine.py`

```python
# Log PR creation telemetry
from wfc.shared.telemetry_auto import log_event

log_event("pr_created", {
    "task_id": task.id,
    "pr_url": pr_result.pr_url,
    "pr_number": pr_result.pr_number,
    "success": pr_result.success,
    # ... more data ...
})
```

**Location**: `create_pr()` method after PR creation

---

#### 2. Git Hooks

**Files**: All hook scripts (`pre_commit.py`, `commit_msg.py`, `pre_push.py`)

```python
def log_telemetry(event: str, data: Dict[str, Any]) -> None:
    """Log hook event to telemetry (if available)."""
    try:
        from wfc.shared.telemetry_auto import log_event
        log_event(event, data)
    except Exception:
        # Telemetry not available or failed - continue
        pass
```

**Error Handling**: Telemetry failures never break hooks

---

## Usage Examples

### Example 1: Install Hooks

```bash
# Install WFC hooks
cd /Users/samfakhreddine/repos/wfc
python -m wfc.wfc_tools.gitwork.hooks.installer install

# Output:
# ✅ Installed 3/3 hooks
```

---

### Example 2: Commit with Warning

```bash
# Try to commit to main
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test"

# Output:
# ⚠️  WARNING: Committing directly to 'main'
#    Consider: git checkout -b feat/TASK-XXX-description
#
# ⚠️  WARNING: Commit message doesn't follow convention
#    Suggestion: Use: TASK-XXX: description OR feat/fix/chore: description
#
# ✅ Commit allowed (soft enforcement - 2 warnings)
```

**Telemetry Logged**:
```json
{"event": "hook_warning", "violation": "direct_commit_to_protected", ...}
{"event": "hook_warning", "violation": "non_conventional_commit", ...}
```

---

### Example 3: View Workflow Metrics

```bash
# View workflow metrics
python -m wfc.shared.telemetry_auto workflow

# Or programmatically:
python3 << EOF
from wfc.shared.telemetry_auto import print_workflow_metrics
print_workflow_metrics(days=30)
EOF
```

---

### Example 4: PR Creation with Telemetry

```python
# In WFC implementation
from wfc.skills.implement.merge_engine import MergeEngine

merge_engine = MergeEngine(project_root, config)

# Create PR
result = merge_engine.create_pr(
    task=task,
    branch="feat/TASK-001-rate-limiting",
    worktree_path=Path(".worktrees/task-001"),
    review_report={"overall_score": 8.5}
)

# Telemetry automatically logged:
# {
#   "event": "pr_created",
#   "task_id": "TASK-001",
#   "pr_url": "...",
#   "success": true,
#   "review_score": 8.5
# }
```

---

## Testing

### Manual Hook Testing

```bash
# Install hooks
python -m wfc.wfc_tools.gitwork.hooks.installer install

# Test pre-commit
git checkout main
touch test.txt
git add test.txt
git commit -m "test"  # Should warn but allow

# Test commit-msg
git checkout -b test
git commit -m "bad message"  # Should warn but allow

# Test pre-push
git push origin main  # Should warn but allow

# Uninstall
python -m wfc.wfc_tools.gitwork.hooks.installer uninstall
```

---

### Telemetry Testing

```bash
# Generate test events
python3 << EOF
from wfc.shared.telemetry_auto import log_event

# Log test PR creation
log_event("pr_created", {
    "pr_url": "https://github.com/test/repo/pull/1",
    "task_id": "TASK-TEST",
    "success": True
})

# Log test hook warning
log_event("hook_warning", {
    "hook": "pre-commit",
    "violation": "direct_commit_to_protected",
    "branch": "main"
})
EOF

# View metrics
python3 -c "from wfc.shared.telemetry_auto import print_workflow_metrics; print_workflow_metrics()"
```

---

## Files Created/Modified

### New Files (Phase 3)

| File | Lines | Purpose |
|------|-------|---------|
| `wfc/wfc-tools/gitwork/hooks/__init__.py` | 15 | Hook exports |
| `wfc/wfc-tools/gitwork/hooks/pre_commit.py` | 220 | Pre-commit hook |
| `wfc/wfc-tools/gitwork/hooks/commit_msg.py` | 140 | Commit-msg hook |
| `wfc/wfc-tools/gitwork/hooks/pre_push.py` | 150 | Pre-push hook |
| `wfc/wfc-tools/gitwork/hooks/installer.py` | 350 | Hook installer/manager |

**Total**: ~875 lines

---

### Modified Files (Phase 6)

| File | Lines Added | Purpose |
|------|-------------|---------|
| `wfc/shared/telemetry_auto.py` | +150 | Generic event logging + workflow metrics |
| `wfc/skills/implement/merge_engine.py` | +30 | PR creation telemetry |

**Total**: ~180 lines

---

## Configuration

### Enable/Disable Workflow Enforcement

```json
// wfc.config.json
{
  "workflow_enforcement": {
    "enabled": true,           // Enable enforcement
    "mode": "warning",         // "warning" or "strict" (future)
    "track_violations": true,  // Log to telemetry
    "protected_branches": ["main", "master"],
    "require_wfc_origin": false
  }
}
```

### Disable Specific Hooks

Hooks can be individually disabled by uninstalling:

```bash
# Uninstall specific hook
python -m wfc.wfc_tools.gitwork.hooks.installer uninstall --hook pre-commit

# Or remove executable permission
chmod -x .git/hooks/pre-commit
```

---

## Telemetry Privacy

**Local Only**: All telemetry stored locally in `~/.wfc/telemetry/`
**No External Services**: Never sent to external servers
**User Controlled**: User can delete telemetry files anytime
**Graceful Degradation**: Telemetry failures never break workflows

---

## Future Enhancements

### Strict Enforcement Mode

```json
{
  "workflow_enforcement": {
    "mode": "strict"  // Block violations instead of warn
  }
}
```

**Status**: Not implemented (soft enforcement only)

---

### Metrics Dashboard

```bash
# View comprehensive dashboard
wfc metrics workflow

# Export metrics
wfc metrics export --format json --output metrics.json
```

**Status**: CLI commands planned but not implemented

---

### Hook Customization

```json
{
  "hooks": {
    "pre-commit": {
      "check_branch_name": true,
      "check_sensitive_files": true,
      "protected_branches": ["main", "master", "production"]
    }
  }
}
```

**Status**: Hooks currently use hardcoded config

---

## Summary

### Phase 3: Git Hooks ✅

**What Works**:
- ✅ 3 git hooks (pre-commit, commit-msg, pre-push)
- ✅ Soft enforcement (warnings only)
- ✅ Non-destructive installation
- ✅ Telemetry integration
- ✅ Hook status checking

**Not Implemented**:
- ⚠️ Strict enforcement mode
- ⚠️ Hook customization via config
- ⚠️ `wfc hooks` CLI command

---

### Phase 6: Telemetry ✅

**What Works**:
- ✅ Generic event logging (`log_event`)
- ✅ PR creation tracking
- ✅ Hook violation tracking
- ✅ Workflow metrics (`get_workflow_metrics`)
- ✅ Metrics display (`print_workflow_metrics`)
- ✅ Events stored in `~/.wfc/telemetry/events.jsonl`

**Not Implemented**:
- ⚠️ `wfc metrics workflow` CLI command
- ⚠️ Metrics export functionality
- ⚠️ Metrics visualization

---

## Total Implementation

**Lines of Code**: ~1,055 lines
**Files Created**: 5 (hooks) + 1 (doc)
**Files Modified**: 2 (telemetry + merge_engine)
**Test Coverage**: Manual testing documented
**Status**: ✅ **COMPLETE**

---

**This is World Fucking Class.** 🚀
