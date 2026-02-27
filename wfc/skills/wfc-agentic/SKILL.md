---
name: wfc-agentic
description: >
  Generates Markdown-based `.gh-aw.md` workflow files for the `gh-aw` CLI extension,
  specifically for AI-driven automation compiled via `gh aw compile`.
  
  Invoke when: User explicitly requests "gh-aw", ".gh-aw.md" files, "safe-outputs",
  or mentions `gh aw compile`. Also triggers on: "create an agentic workflow for
  GitHub" when context implies AI agent execution (Copilot, Claude) rather than
  standard CI/CD.
  
  Format: Markdown files with YAML frontmatter defining triggers, permissions, tools,
  and safe-outputs. The agent prompt (natural language instructions) is written in
  the Markdown body. Output is consumed by `gh aw compile` to generate a lock file.
license: MIT
---

# WFC:AGENTIC - GitHub Agentic Workflow Generator

Generate production-ready `.gh-aw.md` workflow files from natural language descriptions.

## What It Does

1. **Targeted Clarification** — Asks 0-3 questions to resolve missing requirements (trigger type, engine, output type). Proceeds with defaults if unclear after 3 questions.
2. **Workflow Generation** — Creates a `.gh-aw.md` file with valid YAML frontmatter and agent instructions.
3. **Safe-Output Design** — Configures sandboxed write operations (issues, PRs, comments) with explicit per-run limits.
4. **Validation Guidance** — Provides `gh aw compile` and `gh aw run` commands for testing.

## File Naming Convention

- **Generated file**: `.github/workflows/<name>.gh-aw.md` (e.g., `issue-triage.gh-aw.md`)
- **Compile command**: `gh aw compile <name>` (uses the stem, not the extension)
- **Test command**: `gh aw run <name> --dry-run`

## Workflow: How This Skill Operates

User Request
    │
    ▼
Parse Intent
    │  - Extract: trigger, engine, outputs, tools
    │  - Identify missing requirements
    │
    ▼
Clarification Loop (max 3 questions)
    │  - Only ask what's truly unspecified
    │  - Skip if initial request is complete
    │  - Proceed with defaults if still ambiguous
    │
    ▼
Generate {name}.gh-aw.md
    │  - Valid YAML frontmatter (see reference below)
    │  - Natural language agent prompt
    │  - Comments noting any assumptions
    │
    ▼
Output Compile & Test Instructions

```

**Default Assumptions** (used when unspecified):
- Engine: `copilot`
- Permissions: `read-all`
- Network: `defaults`
- Timeout: `15` minutes
- Tools: `github: { toolsets: [issues] }`

## Quick Reference: gh-aw Frontmatter Schema

```yaml
---
description: |
  Brief description of what this workflow does.

on:
  # Exactly one trigger type is required.
  # Use standard GitHub Actions YAML syntax:

  issues:
    types: [opened, reopened]
  pull_request:
    types: [opened, synchronize]
  schedule:
    - cron: "0 9 * * 1"    # Every Monday 9am UTC (5-field cron only)
  workflow_dispatch: {}
  slash_command:
    name: fix              # Triggers on /fix in comments
  workflow_run:
    workflows: ["CI"]
    types: [completed]

# Optional: reaction emoji when triggered (e.g., eyes, rocket, +1)
reaction: eyes

# Permissions: always start minimal
permissions: read-all

# Engine: copilot (default), claude, or openai
engine: copilot

# Network access: defaults (standard GitHub endpoints)
network: defaults

# Tools available to the agent
tools:
  github:
    toolsets: [issues]     # Options: [issues], [pull_requests], [repos], [all]
    lockdown: false        # Set true to block 3rd-party repo access
  web-fetch: {}            # Enable URL fetching
  bash: true               # WARNING: may conflict with read-all permissions
  edit: {}                 # Enable file editing
  cache-memory: true       # Persist memory across runs

# Safe outputs (per-run limits enforced)
safe-outputs:
  create-issue:
    title-prefix: "[Auto]"
    labels: [automation]
    max: 3                 # Max 3 issues created per run
  create-pull-request:
    draft: true
    labels: [automation]
    max: 1
  add-comment:
    max: 5
  add-labels:
    max: 10
  push-to-pull-request-branch: {}
  noop:
    max: 1

timeout-minutes: 15
---

# Workflow Title

Natural language instructions for the AI agent.
Use ${{ github.event.* }} variables for context.
```

## Trigger Syntax Reference

| Trigger Type | Valid YAML Syntax |
|--------------|-------------------|
| Issue events | `issues: { types: [opened, reopened] }` |
| PR events | `pull_request: { types: [opened, synchronize] }` |
| Scheduled | `schedule: [{ cron: "0 9 * * 1" }]` — 5-field UTC cron only |
| Manual | `workflow_dispatch: {}` |
| Slash command | `slash_command: { name: fix }` — triggers on `/fix` |
| Workflow run | `workflow_run: { workflows: ["CI"], types: [completed] }` |
| Push | `push: { branches: [main] }` |

**Common Errors**:

- ❌ `schedule: daily` — Invalid, use cron syntax
- ❌ `schedule: weekly` — Invalid, use cron syntax
- ❌ `workflow_run: { workflows: CI }` — Invalid, must be array `["CI"]`

## Template Variables

| Variable | Description | Example Use |
|----------|-------------|-------------|
| `${{ github.repository }}` | Owner/repo | `owner/repo` |
| `${{ github.actor }}` | Triggering user | `monalisa` |
| `${{ github.event.issue.number }}` | Issue number | `42` |
| `${{ github.event.pull_request.number }}` | PR number | `7` |
| `${{ github.event.comment.body }}` | Comment text | Full comment text |
| `${{ github.event.workflow_run.id }}` | Failed run ID | `1234567890` |
| `${{ github.event.workflow_run.conclusion }}` | Run result | `failure`, `success` |
| `${{ github.workflow }}` | Workflow name | `CI Doctor` |
| `${{ needs.activation.outputs.text }}` | Slash command args after command | `/fix the tests` → `the tests` |

**Slash Command Example**:

```markdown
---
on:
  slash_command:
    name: fix
---

# Fix Issues

Fix the following: ${{ needs.activation.outputs.text }}
```

## Engine Configuration

| Engine | Key | Secret Required | Notes |
|--------|-----|-----------------|-------|
| `copilot` | COPILOT_GITHUB_TOKEN | GitHub-native default | |
| `claude` | ANTHROPIC_API_KEY | Complex reasoning, code changes | |
| `openai` | OPENAI_API_KEY | OpenAI GPT models | |

**Note**: `codex` is deprecated. Use `openai` for OpenAI integration.

## Safe Output Types

| Output | Purpose | Required Fields |
|--------|---------|-----------------|
| `create-issue` | Open new issues | `max` (required), `title-prefix`, `labels` |
| `create-pull-request` | Open PRs | `max` (required), `draft`, `labels` |
| `add-comment` | Comment on issues/PRs | `max` (required) |
| `add-labels` | Apply labels | `max` (required) |
| `push-to-pull-request-branch` | Push to existing PR | `{}` |
| `noop` | Log "no action needed" | `max: 1` |

**`max` is enforced per single workflow run invocation.**

## Example Workflows

### Issue Triage (Event-Triggered)

```markdown
---
description: Triage new issues with labels and analysis
on:
  issues:
    types: [opened, reopened]
reaction: eyes
permissions: read-all
network: defaults
safe-outputs:
  add-labels:
    max: 5
  add-comment:
    max: 1
tools:
  github:
    toolsets: [issues]
timeout-minutes: 10
---

# Issue Triage

Analyze issue #${{ github.event.issue.number }} in ${{ github.repository }}.

1. Read the issue content
2. Search for similar existing issues
3. Select appropriate labels from the repository's label set
4. Add a triage comment with analysis and suggested next steps
```

### CI Doctor (Workflow Run Trigger)

```markdown
---
description: Investigate CI failures and create reports
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
permissions: read-all
network: defaults
safe-outputs:
  create-issue:
    title-prefix: "[CI-Failure]"
    labels: [automation, ci]
    max: 1
tools:
  cache-memory: true
  web-fetch: {}
timeout-minutes: 10
---

# CI Failure Doctor

Investigate failed workflow run ${{ github.event.workflow_run.id }}.

1. Get workflow details and list failed jobs
2. Retrieve and analyze error logs
3. Check memory for similar past failures
4. Identify root cause and recommend fixes
5. Create an issue with investigation report
```

### PR Fix (Slash Command)

```markdown
---
description: Fix issues in PRs via slash command
on:
  slash_command:
    name: pr-fix
reaction: eyes
permissions: read-all
network: defaults
engine: claude
safe-outputs:
  push-to-pull-request-branch: {}
  add-comment:
    max: 1
tools:
  bash: true
  web-fetch: {}
timeout-minutes: 20
---

# PR Fix

Fix issues in PR #${{ github.event.issue.number }}.

User request: ${{ needs.activation
