# .clouddevelopment

Shared development workspace for Claude Code web sessions. Unlike `.development/` (gitignored, local-only), this directory is **tracked in the repo** so artifacts persist across cloud sessions.

## Structure

```
.clouddevelopment/
├── plans/        # Active plans, deviation maps, TASKS.md drafts
├── summaries/    # Session recaps, task completion notes
└── scratch/      # Temporary working files
```

## Usage

- Drop plans, audit maps, and migration artifacts here during Claude Code web sessions
- Files here are committed and pushed so the next session picks up where the last left off
- Keep it clean — archive or remove completed work periodically
