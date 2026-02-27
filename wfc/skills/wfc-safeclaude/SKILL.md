---
name: wfc-safeclaude
description: >-
  Generates a .claude/settings.local.json file to pre-approve specific low-risk
  commands (e.g., ls, cat, git status, npm test) based on detected project
  tooling. Reduces repetitive approval prompts while maintaining safety guardrails.

  TRIGGERS: "/wfc-safeclaude", "whitelist safe commands for Claude", "create
  command allowlist for this project", "reduce permission prompts for specific
  commands", "configure local auto-approve for safe operations".

  NOT FOR: "YOLO mode or disabling all security prompts", "global Claude Code
  settings", "executing or running the commands themselves", "CI/CD pipeline
  configuration", "network firewall rules or IP allowlists", "bare git
  repositories or non-versioned directories", "preserving manually-edited
  settings files", "commands semantically equivalent to denylisted operations
  (rm with recursive/force flags, git push with force variants, curl/wget piped
  to shell)", "projects outside the current working directory scope".
license: MIT
---

# WFC:SAFECLAUDE - Safe Command Allowlist Generator

Generates a `.claude/settings.local.json` file to reduce repetitive approval
prompts for pre-vetted commands, without disabling safety guardrails.

## What This Skill Does

1. **Detects project tooling** by checking for common manifest files in the
   current working directory (see Detection section below)
2. **Proposes commands** grouped by category for user review
3. **Requires explicit approval** via clear affirmative response before writing
4. **Writes settings.local.json** with an `allowedTools` array of approved commands

## What This Skill Does NOT Do

- Disable all approval prompts or enable unrestricted execution mode
- Modify global Claude Code configuration
- Execute or test any commands
- Preserve existing manual edits to settings.local.json (use `--show` to backup first)
- Work in bare git repositories or directories without version control

## Usage

```bash
# Scan and generate allowlist (interactive - requires your approval)
/wfc-safeclaude

# Show current allowlist (outputs "No allowlist found" if file absent)
/wfc-safeclaude --show

# Strict mode: only commands that query state without modifying files
# Allowed: ls, cat, git status, git log, npm list
# Blocked: npm install, git checkout, npm run build, any file writes
/wfc-safeclaude --strict

# Add a specific command (prompts for approval, checks against denylist)
/wfc-safeclaude --add "docker ps"

# Remove a command (requires exact character-for-character match)
/wfc-safeclaude --remove "npm run build"

# Delete existing settings.local.json and regenerate (destroys manual edits)
/wfc-safeclaude --reset
```

## Detection

The scanner checks for these manifest files in the current working directory:

| File Detected | Commands Proposed |
|---------------|-------------------|
| package.json | npm, npx, node (not npm install by default) |
| requirements.txt, pyproject.toml | python, pip, pipenv |
| Cargo.toml | cargo |
| go.mod | go |
| Makefile | make |
| docker-compose.yml, Dockerfile | docker, docker-compose |
| .git directory | git status, git log, git diff, git branch |

If no manifest files are found, proposes a minimal safe set: `ls`, `cat`, `head`, `tail`, `grep`, `find`.

## Command Categories

Commands are proposed in these fixed categories:

1. **Read-only filesystem**: ls, cat, head, tail, grep, find, tree
2. **Version control (query only)**: git status, git log, git diff, git branch
3. **Package managers (query only)**: npm list, pip list, cargo tree
4. **Build tools**: npm run build, make, cargo build (excluded in --strict)
5. **Test runners**: npm test, pytest, cargo test (excluded in --strict)
6. **Containers**: docker ps, docker logs, docker-compose ps

## Approval Protocol

After proposing commands, the skill asks: "Approve these categories? Respond with 'approved' or request modifications."

Valid approvals:

- "approved"
- "I approve"
- "yes, approved"

Not valid (skill will re-prompt):

- "ok"
- "sure"
- "go ahead"
- "looks good"

To modify: "Approved, but remove docker commands" or "Add npm run lint to build tools"

## Permanent Denylist

These command patterns are always blocked, regardless of user request:

- `rm` with any combination of `-r`, `-R`, `-f`, `-i`, `-I` flags
- `git push` with `--force`, `--force-with-lease`, `-f` flags
- `curl | bash`, `curl | sh`, `wget | bash`, `wget | sh` patterns
- `sudo` in any form
- `chmod -R 777`
- `dd` with disk device targets

The denylist uses pattern matching: commands matching these patterns will be rejected even with different flag ordering or additional arguments.

## File Write Behavior

- **Default**: Completely overwrites existing `.claude/settings.local.json`
- **`--add`**: Overwrites the `allowedTools` key only; preserves other keys
- **`--reset`**: Deletes file, then runs interactive generation workflow

Always use `--show` to backup manual edits before any modification.

## Output Format

Writes JSON in this structure:

```json
{
  "allowedTools": ["ls", "cat", "git status", "npm test"]
}
```

Note: Claude Code support for this file varies by version. After generation,
observe whether approval prompts decrease in subsequent commands to verify
the file is recognized.
