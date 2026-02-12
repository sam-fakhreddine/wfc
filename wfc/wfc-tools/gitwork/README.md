# wfc-tools/gitwork

Centralized Git API for all WFC skills.

## Why This Exists

No WFC skill runs raw git commands. Every branch, commit, merge, worktree, and rollback operation goes through gitwork. This ensures:

- **Uniform conventions** across all skills
- **Conservative defaults** (chore over feat)
- **Model routing** (Haiku for simple, Sonnet/Opus for complex)
- **Telemetry** at every operation
- **Safety** (validation, protection, rollback)

## API Operations

### branch.*
- `create(task_id, title, type)` - Create branch with type classification
- `delete(name, force)` - Safe branch deletion
- `list(filter, status)` - List branches
- `validate_name(name)` - Check naming convention

### commit.*
- `create(message, files, task_id, properties, type, scope)` - Conventional commits
- `validate_message(message)` - Check format
- `amend(message, files)` - Safe amend

### worktree.*
- `create(task_id, base_ref)` - Create isolated worktree
- `delete(task_id)` - Clean up worktree
- `list()` - List active worktrees
- `conflicts(task_id)` - Detect file overlaps

### merge.*
- `execute(task_id, branch)` - Merge with pre-flight checks
- `queue(task_id)` - Serialize merges
- `abort(task_id)` - Clean abort
- `validate(task_id)` - Check readiness

### rollback.*
- `revert(merge_sha)` - Atomic revert
- `verify()` - Check main is clean
- `plan(task_id, context)` - Generate PLAN.md

### history.*
- `search(pattern)` - Search commits
- `audit(since)` - Drift detection
- `blame(file)` - File changes
- `search_content(pattern)` - Secrets scanning

### hooks.*
- `install(hook_type)` - Install hooks
- `manage()` - List/enable/disable
- `wrap(hook_type, script)` - Wrap existing hooks

### semver.*
- `current()` - Get current version
- `calculate()` - Calculate from commits
- `bump(type)` - Bump version

## Model Routing

- **Haiku**: Simple operations (create, delete, list, validate)
- **Sonnet/Opus**: Complex operations (type classification, conflict resolution, search)

## Usage

```python
from wfc.wfc_tools.gitwork import branch, commit, worktree

# Create branch for task
result = branch.create(
    task_id="TASK-001",
    title="implement auth middleware",
    base_ref="main"
)
# Result: {"branch_name": "chore/TASK-001-implement-auth-middleware", ...}

# Create conventional commit
commit.create(
    message="implement JWT validation",
    files=["middleware/auth.py"],
    task_id="TASK-001",
    properties=["PROP-001"],
    type="feat",
    scope="auth"
)
# Result: "feat(auth): implement JWT validation [TASK-001] [PROP-001]"

# Create worktree
worktree.create(
    task_id="TASK-001",
    base_ref="main"
)
# Result: {" worktree_path": ".worktrees/wfc-TASK-001/", ...}
```

## Configuration

Located at `~/.claude/wfc-gitwork.config.json` or `<project>/wfc-gitwork.config.json`:

```json
{
  "branch": {
    "naming_pattern": "chore/TASK-{id}-{slug}",
    "protected_branches": ["main", "master", "develop"]
  },
  "commit": {
    "format": "conventional",
    "require_task_ref": true,
    "require_property_ref": false
  },
  "merge": {
    "strategy": "ff-only",
    "require_rebase": true
  },
  "model_routing": {
    "simple_ops": "haiku",
    "complex_ops": "sonnet"
  }
}
```

## Integration with WFC Skills

All WFC skills depend on gitwork:
- **wfc-implement** - Worktree, branch, commit, merge operations
- **wfc-architecture** - History audit, drift detection
- **wfc-security** - History search for secrets
- **wfc-consensus-review** - Implicit (code exists in branches)

## ELEGANT, MULTI-TIER, PARALLEL

- **ELEGANT**: Simple API, clear contracts, conservative defaults
- **MULTI-TIER**: Tool (API) separate from skills (consumers)
- **PARALLEL**: Queue serializes merges, but operations can run concurrently
