# OpenCode — WFC Integration

## Setup

After running the WFC installer, add the WFC agent to your OpenCode configuration.

### 1. Edit `~/.config/opencode/opencode.json`

Add the following to your `agents` section:

```json
{
  "agents": {
    "wfc": {
      "name": "WFC Development Team",
      "description": "Multi-agent code review, planning, and implementation",
      "skills_dir": "~/.config/opencode/skills"
    }
  }
}
```

### 2. Available Commands

- `/wfc-review` — 5-agent consensus code review
- `/wfc-build "feature"` — Quick feature builder with TDD
- `/wfc-plan` — Structured task breakdown
- `/wfc-implement` — Parallel TDD execution
- `/wfc-security` — STRIDE threat modeling

### 3. Usage

Select the `wfc` agent when you want to use WFC skills, then invoke commands normally.
Switch back to your default agent for regular coding tasks.
