# GitHub Agentic Workflows Integration

WFC integrates with [GitHub Agentic Workflows (gh-aw)](https://github.com/github/gh-aw), GitHub's system for running AI coding agents in GitHub Actions using natural language Markdown files instead of complex YAML.

## Overview

GitHub Agentic Workflows let you describe automation goals in plain Markdown, then compile them into standard GitHub Actions workflows that run AI agents (Copilot, Claude Code, or Codex) with strong security guardrails.

**WFC adds**: The `/wfc-agentic` skill generates production-ready gh-aw workflow files through an adaptive interview process, ensuring proper frontmatter configuration, safe-output design, and well-crafted agent prompts.

## How gh-aw Works

```
Markdown (.md)  →  gh aw compile  →  Lock File (.lock.yml)  →  GitHub Actions
     ↑                                                              │
  You write this                                    AI agent runs here
  (natural language)                                (sandboxed, read-only)
                                                           │
                                                    Safe Outputs
                                                    (validated writes)
```

### Security Model

The agent itself **never gets direct write access**. All writes go through safe-outputs:

1. **Agent Job** - Runs in a sandboxed container with read-only repo access
2. **Detection Job** - A second AI reviews the agent's outputs for threats
3. **Safe Outputs Job** - Executes approved writes (issues, PRs, comments)

This means even a fully compromised agent cannot modify your repository directly.

## Quick Start

### Prerequisites

```bash
# Install gh-aw CLI extension
gh extension install github/gh-aw

# Configure engine secret (pick one)
# Copilot: Set COPILOT_GITHUB_TOKEN in repo secrets
# Claude:  Set ANTHROPIC_API_KEY in repo secrets
# Codex:   Set OPENAI_API_KEY in repo secrets
```

### Create a Workflow

```bash
# Using WFC skill (recommended)
/wfc-agentic "triage new issues with labels and analysis"

# Or manually create .github/workflows/issue-triage.md
```

### Compile and Deploy

```bash
# Compile markdown to GitHub Actions YAML
gh aw compile issue-triage

# Verify the generated lock file
cat .github/workflows/issue-triage.lock.yml

# Commit both files
git add .github/workflows/issue-triage.md .github/workflows/issue-triage.lock.yml
git commit -m "feat: add issue triage agentic workflow"
git push
```

## Workflow Format Reference

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Recommended | What the workflow does (shown in GH UI) |
| `on` | Yes | Event triggers |
| `permissions` | Yes | GitHub token permissions (use `read-all`) |
| `engine` | No | AI engine: `copilot` (default), `claude`, `codex` |
| `network` | No | Network access: `defaults` or specific domains |
| `tools` | No | Available tools (github, bash, web-fetch, etc.) |
| `safe-outputs` | Yes | Sandboxed write operations |
| `timeout-minutes` | Recommended | Max execution time |
| `reaction` | No | Emoji reaction on trigger (e.g., `eyes`) |
| `if` | No | Conditional execution |

### Trigger Types

```yaml
# Event-based
on:
  issues:
    types: [opened, reopened]
  pull_request:
    types: [opened, synchronize]

# Scheduled
on:
  schedule: daily              # Friendly format
  schedule:
    - cron: "0 9 * * 1-5"     # Standard cron

# Manual
on:
  workflow_dispatch:

# Slash command (comment-triggered)
on:
  slash_command:
    name: fix

# Chained (after another workflow)
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

### Engine Configuration

```yaml
# GitHub Copilot (default)
engine: copilot
# Secret: COPILOT_GITHUB_TOKEN

# Anthropic Claude Code
engine: claude
# Secret: ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN

# OpenAI Codex
engine: codex
# Secret: OPENAI_API_KEY
```

### Safe Outputs

```yaml
safe-outputs:
  # Create GitHub issues
  create-issue:
    title-prefix: "${{ github.workflow }}"
    labels: [automation, triage]
    max: 3

  # Create pull requests
  create-pull-request:
    draft: true
    labels: [automation]
    max: 1

  # Comment on issues/PRs
  add-comment:
    max: 1

  # Apply labels
  add-labels:
    max: 5

  # Push to existing PR branch
  push-to-pull-request-branch:

  # Log "no action needed"
  noop:
    max: 1
```

### Tool Configuration

```yaml
tools:
  # GitHub API via MCP Server
  github:
    toolsets: [all]              # or: [repos, issues, pull_requests]
    lockdown: false              # allow 3rd-party data in public repos
    allowed:                     # specific tools only
      - search_issues
      - get_pull_request

  # URL fetching
  web-fetch:

  # Shell commands
  bash: true                     # unrestricted (sandboxed)
  bash:
    - "npm *"                    # restricted to specific commands
    - "python *"

  # File editing
  edit:

  # Persistent memory across runs
  cache-memory: true
```

## Sample Workflows from Agentics

The [githubnext/agentics](https://github.com/githubnext/agentics) repository provides a curated collection of reusable workflows:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| Issue Triage | `issues: [opened]` | Label and analyze new issues |
| CI Doctor | `workflow_run: [completed]` | Investigate CI failures |
| PR Fix | `/pr-fix` slash command | Fix failing PR checks |
| Code Simplifier | `schedule: daily` | Simplify recently modified code |
| Documentation Update | `schedule: weekly` | Keep docs in sync with code |
| Test Coverage Improver | `schedule: daily` | Add tests to under-tested areas |
| Contribution Checker | `pull_request: [opened]` | Check PR against guidelines |
| Weekly Research | `schedule: weekly` | Collect industry trends |
| Backlog Burner | `schedule: daily` | Work through issue backlog |
| Daily Plan | `schedule: daily` | Update planning issues |

## WFC + gh-aw Synergies

| WFC Feature | gh-aw Equivalent | Integration |
|-------------|-------------------|-------------|
| `wfc-review` | CI-triggered review | Run WFC review as agentic workflow on PR events |
| `wfc-security` | Security audit workflow | Scheduled STRIDE analysis via gh-aw |
| `wfc-test` | Test improver | Daily test coverage improvement workflow |
| `wfc-implement` | PR fix / backlog burner | Agentic implementation from issues |
| `wfc-pr-comments` | PR fix | Fix review feedback automatically |

## CLI Reference

```bash
# Install/upgrade
gh extension install github/gh-aw
gh extension upgrade github/gh-aw
gh aw upgrade          # Upgrade engine version

# Workflow management
gh aw compile           # Compile all workflows
gh aw compile <name>    # Compile specific workflow
gh aw compile --validate # Compile with validation

# Maintenance
gh aw fix --write      # Apply codemods for breaking changes
gh aw update           # Update added workflows

# Debugging
gh aw logs <name>      # View workflow logs
gh aw audit <run-id>   # Audit a specific run

# Running
gh aw run <name>       # Manually trigger a workflow
```

## Resources

- [gh-aw Documentation](https://github.github.io/gh-aw/)
- [gh-aw Repository](https://github.com/github/gh-aw)
- [Sample Workflows (Agentics)](https://github.com/githubnext/agentics)
- [GitHub Blog: Agentic Workflows](https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/)
- [GitHub Changelog: Tech Preview](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/)
