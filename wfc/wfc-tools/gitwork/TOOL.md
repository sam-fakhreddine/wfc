# wfc-tools/gitwork - TOOL Documentation

## Tool vs Skill

**Tool**: Internal API for WFC skills (this)
**Skill**: User-facing slash command

gitwork is primarily a TOOL - all WFC skills call it. No user runs `/gitwork` commands directly.

## API Contract

All WFC skills MUST use gitwork for git operations. Never run raw git commands.

### Why?

- **Uniform conventions**: One place to change branch naming, commit format, etc.
- **Model routing**: Cost optimization (Haiku vs Sonnet/Opus)
- **Telemetry**: Track all git operations
- **Safety**: Validation, protection, rollback
- **Conservative defaults**: chore over feat

## Complete API Reference

See README.md for full API documentation.

## Integration Points

- **wfc:implement**: worktree.*, branch.*, commit.*, merge.*, rollback.*
- **wfc:architecture**: history.audit, history.blame
- **wfc:security**: history.search_content (secrets)
- **wfc:consensus-review**: Implicit (code in branches)

## Model Routing

Operations are routed to models based on complexity:

**Haiku** (mechanical):
- branch create/delete/list
- commit create/validate
- worktree create/delete/list
- merge abort
- hooks install
- semver current

**Sonnet/Opus** (reasoning):
- Type classification
- Conflict analysis
- Merge execution with checks
- Recovery plan generation
- Secrets scanning
- Semver calculation

## Configuration

Global: `~/.claude/wfc-gitwork.config.json`
Project: `<project>/wfc-gitwork.config.json`

See config.py for full schema.

## Telemetry

All operations logged in calling skill's telemetry file, not separate gitwork file.

Format:
```json
{
  "operation": "branch.create",
  "model": "haiku",
  "success": true,
  "duration_ms": 250
}
```

## ELEGANT Principles

- **Effective**: Does one thing well (git operations)
- **Lean**: Thin wrapper over git, not abstraction bloat
- **Essential**: Only operations actually needed by skills
- **Graceful**: Handles errors, provides recovery
- **Architected**: Clean API, SOLID principles
- **No complexity**: Simple, predictable behavior
- **Testable**: Every operation testable

## Usage Example

```python
from wfc.wfc_tools.gitwork import branch, commit, worktree, merge

# Create branch
result = branch.create("TASK-001", "implement auth", "main")
# -> {"branch_name": "chore/TASK-001-implement-auth", ...}

# Create worktree
worktree.create("TASK-001", "main")
# -> {"worktree_path": ".worktrees/wfc-TASK-001/", ...}

# Commit in worktree
commit.create(
    "implement JWT validation",
    files=["auth.py"],
    task_id="TASK-001",
    type="feat",
    scope="auth"
)
# -> "feat(auth): implement JWT validation [TASK-001]"

# Merge when ready
merge.execute("chore/TASK-001-implement-auth", strategy="ff-only")
```
