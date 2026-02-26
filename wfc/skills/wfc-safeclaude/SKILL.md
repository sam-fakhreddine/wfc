---
name: wfc-safeclaude
description: >-
  Scans the current project and writes .claude/settings.local.json to
  pre-approve low-risk commands by risk category, reducing per-command approval
  prompts without enabling unrestricted execution mode.

  TRIGGERS: "reduce Claude Code approval prompts", "generate a command
  allowlist", "set up auto-approve rules for this project", "/wfc-safeclaude".

  NOT FOR: disabling all Claude Code security prompts or enabling YOLO mode;
  shell command recommendations unrelated to Claude Code permissions; network,
  IP, or infrastructure allowlists; settings files outside .claude/; production
  or shared CI/CD environments; security audits of existing allowlists;
  commands on the permanent denylist (rm -rf, git push --force, curl | bash).
license: MIT
---

# WFC:SAFECLAUDE - Safe Command Allowlist Generator

Generates a project-specific Claude Code command allowlist to reduce repetitive
approval prompts for pre-vetted low-risk commands, without disabling all guardrails.

## The Problem

Every new Claude Code session in a new project means approving `ls`, `cat`, `grep`,
`git status`, `npm test` one by one. It's friction that adds zero safety value.
But unrestricted execution mode removes ALL guardrails.

**safeclaude** finds the middle ground: a project-specific, user-reviewed allowlist.

## What It Does

1. **Scans** the project for known ecosystem signals (language, frameworks, toolchain)
2. **Proposes** categorized command sets for user review
3. **User explicitly approves or modifies** each category before any file is written
4. **Writes** `.claude/settings.local.json` using only `allowedTools` keys supported by Claude Code

**Important**: This skill writes a configuration file. Whether Claude Code honors the
file depends on your Claude Code version. Verify the generated file is recognized before
assuming approvals are active.

## Usage

```bash
# Scan and generate allowlist (interactive, requires explicit approval)
/wfc-safeclaude

# Show current allowlist (outputs "No allowlist found" if file absent)
/wfc-safeclaude --show

# Strict mode: read-only commands only — use for shared or sensitive projects
/wfc-safeclaude --strict

# Add a specific command (validated against permanent denylist before writing)
/wfc-safeclaude --add "docker ps"

# Remove a command (exact-match only; reports error if command not found)
/wfc-safeclaude --remove "npm run build"

# Delete existing settings.local.json and regenerate from scratch (destructive — manual edits are lost)
/wfc-safeclaude --reset
```

## Detection

The scanner checks for the following files at git root (or CW
