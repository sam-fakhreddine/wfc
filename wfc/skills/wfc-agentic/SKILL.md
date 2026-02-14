---
name: wfc-agentic
description: Generate GitHub Agentic Workflows (gh-aw) from natural language. Converts WFC task descriptions into gh-aw Markdown workflow files with proper frontmatter (triggers, permissions, safe-outputs, tools, engine selection) ready for compilation with `gh aw compile`. Supports all gh-aw engines (Copilot, Claude Code, Codex), trigger types (schedule, issues, PRs, slash commands, workflow_run), safe-output types (create-issue, create-pull-request, add-comment, push-to-pull-request-branch), and tool configurations (github MCP, web-fetch, bash, cache-memory). Use when creating CI/CD automation, issue triage bots, PR review workflows, documentation updaters, or any event-driven agentic task. Triggers on "create agentic workflow", "add gh-aw workflow", "automate with GitHub Actions agent", or explicit /wfc-agentic. Not for traditional GitHub Actions YAML authoring or non-agentic workflows.
license: MIT
---

# WFC:AGENTIC - GitHub Agentic Workflow Generator

Generate production-ready [GitHub Agentic Workflows](https://github.com/github/gh-aw) from natural language descriptions.

## What It Does

1. **Adaptive Interview** - Asks what to automate, triggers, engine preference, output types
2. **Workflow Generation** - Creates `.md` workflow file with proper gh-aw frontmatter
3. **Safe-Output Design** - Configures sandboxed write operations (issues, PRs, comments)
4. **Prompt Engineering** - Writes the natural language instructions for the AI agent
5. **Validation Guidance** - Instructions for compiling and testing with `gh aw compile`

## Usage

```bash
# Interactive mode - guided workflow creation
/wfc-agentic

# With description
/wfc-agentic "triage new issues with labels and analysis comments"

# With specific intent
/wfc-agentic "fix failing CI checks on PRs when someone comments /fix"
```

## Quick Reference: gh-aw Workflow Format

A gh-aw workflow is a Markdown file in `.github/workflows/` with YAML frontmatter:

```markdown
---
description: |
  What this workflow does (required for compiled workflows)

on:
  # Event triggers (same concepts as GitHub Actions)
  issues:
    types: [opened, reopened]
  schedule:
    - cron: "0 9 * * 1"
  workflow_dispatch:
  slash_command:
    name: fix
  workflow_run:
    workflows: ["CI"]
    types: [completed]

# Optional: reaction emoji shown when triggered
reaction: eyes

# Permissions (always start minimal)
permissions: read-all

# Engine selection
engine: claude          # or: copilot (default), codex

# Network access
network: defaults       # or: specific allowed domains

# Tools available to the agent
tools:
  github:
    toolsets: [all]     # or: [repos, issues, pull_requests]
    lockdown: false     # allow reading 3rd-party data in public repos
  web-fetch:            # enable URL fetching
  bash: true            # or: ["npm *", "python *"] for restricted
  edit:                 # enable file editing
  cache-memory: true    # persistent memory across runs

# Safe outputs - sandboxed write operations
safe-outputs:
  create-issue:
    title-prefix: "${{ github.workflow }}"
    labels: [automation]
    max: 3
  create-pull-request:
    draft: true
    labels: [automation]
  add-comment:
    max: 1
  add-labels:
    max: 5
  push-to-pull-request-branch:

# Timeout
timeout-minutes: 15
---

# Workflow Title

Natural language instructions for the AI agent go here.
Uses ${{ github.event.* }} template variables for context.
```

## gh-aw Architecture

```
Markdown Workflow (.md)
        │
        ▼
  gh aw compile        ← Generates lock file
        │
        ▼
Lock File (.lock.yml)  ← Standard GitHub Actions YAML
        │
        ▼
GitHub Actions Runner
        │
        ├── Activation Job     ← Permission checks
        ├── Agent Job          ← AI agent runs here (sandboxed)
        │   ├── MCP Gateway    ← Tool access (GitHub, safe-outputs)
        │   ├── AWF Firewall   ← Network isolation
        │   └── Safe Outputs   ← Structured write operations
        ├── Detection Job      ← Threat detection on outputs
        ├── Safe Outputs Job   ← Executes approved writes
        ├── Cache Memory Job   ← Persists agent memory
        └── Conclusion Job     ← Status reporting
```

### Key Security Properties

- **Agent is read-only** - Cannot directly write to repo
- **Safe outputs are sanitized** - All writes go through validation
- **Threat detection** - Second AI reviews agent outputs before execution
- **Network isolation** - Firewall restricts external access
- **SHA-pinned dependencies** - Supply chain protection

## Trigger Types

| Trigger | YAML | Use Case |
|---------|------|----------|
| Issue events | `issues: [opened, reopened]` | Triage, labeling |
| PR events | `pull_request: [opened, synchronize]` | Code review, CI fix |
| Scheduled | `schedule: daily` or `cron: "0 9 * * 1"` | Reports, maintenance |
| Manual | `workflow_dispatch:` | On-demand tasks |
| Slash command | `slash_command: { name: fix }` | `/fix` in comments |
| Workflow run | `workflow_run: { workflows: [CI] }` | CI failure analysis |
| Push | `push: { branches: [main] }` | Post-merge tasks |

## Engine Selection

| Engine | Key | Best For |
|--------|-----|----------|
| `copilot` | `COPILOT_GITHUB_TOKEN` | Default, GitHub-native |
| `claude` | `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` | Complex reasoning, code changes |
| `codex` | `OPENAI_API_KEY` | OpenAI integration |

## Safe Output Types

| Output | Purpose | Key Options |
|--------|---------|-------------|
| `create-issue` | Open new issues | `title-prefix`, `labels`, `max` |
| `create-pull-request` | Open PRs with code changes | `draft`, `labels`, `max` |
| `add-comment` | Comment on issues/PRs | `max` |
| `add-labels` | Apply labels | `max` |
| `push-to-pull-request-branch` | Push to existing PR | - |
| `noop` | Log "no action needed" | `max: 1` |

## Tool Configuration

| Tool | Purpose | Config |
|------|---------|--------|
| `github` | GitHub API via MCP | `toolsets`, `lockdown` |
| `web-fetch` | Fetch URLs | enabled/disabled |
| `bash` | Shell commands | `true` or allow-list |
| `edit` | File editing | enabled/disabled |
| `cache-memory` | Persistent storage | `true`/`false` |

## Template Variables

Available in the workflow body via `${{ }}` syntax:

- `${{ github.repository }}` - Owner/repo
- `${{ github.actor }}` - Triggering user
- `${{ github.event.issue.number }}` - Issue number
- `${{ github.event.pull_request.number }}` - PR number
- `${{ github.event.comment.body }}` - Comment text
- `${{ github.event.workflow_run.id }}` - Failed run ID
- `${{ github.event.workflow_run.conclusion }}` - Run result
- `${{ github.workflow }}` - Workflow name
- `${{ needs.activation.outputs.text }}` - Slash command args

## Example Workflows

### Issue Triage (Event-Triggered)

```markdown
---
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
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

if: ${{ github.event.workflow_run.conclusion == 'failure' }}

permissions: read-all
network: defaults

safe-outputs:
  create-issue:
    title-prefix: "${{ github.workflow }}"
    labels: [automation, ci]
  add-comment:

tools:
  cache-memory: true
  web-fetch:

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
on:
  slash_command:
    name: pr-fix
  reaction: eyes

permissions: read-all
network: defaults
engine: claude

safe-outputs:
  push-to-pull-request-branch:
  add-comment:

tools:
  bash: true
  web-fetch:

timeout-minutes: 20
---

# PR Fix

Fix failing checks on PR #${{ github.event.issue.number }}.

1. Read the PR and its comments
2. Analyze failing CI check logs
3. Identify root cause and implement fix
4. Run tests and formatters
5. Push fix to the PR branch
6. Comment with summary of changes
```

### Weekly Report (Scheduled)

```markdown
---
on:
  schedule: weekly

permissions: read-all
network: defaults

safe-outputs:
  create-issue:
    title-prefix: "${{ github.workflow }}"
    labels: [report]
    max: 1

tools:
  github:
    toolsets: [all]

timeout-minutes: 15
---

# Weekly Repository Report

Generate a weekly status report for ${{ github.repository }}.

1. List PRs merged this week
2. List new issues opened and closed
3. Summarize contributor activity
4. Highlight any CI failures or security alerts
5. Create an issue with the formatted report
```

## Workflow: How This Skill Operates

```
User Request
    │
    ▼
Adaptive Interview (3-5 questions)
    │  - What to automate?
    │  - What triggers it?
    │  - What should it output?
    │  - Which AI engine?
    │  - Any special tools needed?
    │
    ▼
Generate Workflow (.md file)
    │  - Frontmatter (triggers, permissions, tools, safe-outputs)
    │  - Natural language prompt (agent instructions)
    │
    ▼
Place in .github/workflows/
    │
    ▼
Compile Instructions
    │  - gh aw compile <workflow-name>
    │  - Review generated .lock.yml
    │  - Test with: gh aw run <workflow-name>
    │
    ▼
User Reviews & Commits
```

## Prerequisites

- **gh CLI** v2.0.0+ installed
- **gh-aw extension**: `gh extension install github/gh-aw`
- **Engine secret** configured in repo settings:
  - Copilot: `COPILOT_GITHUB_TOKEN`
  - Claude: `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN`
  - Codex: `OPENAI_API_KEY`

## Best Practices

1. **Start with `permissions: read-all`** - Only the safe-outputs job gets write access
2. **Use `network: defaults`** - Unless your workflow needs specific external domains
3. **Set reasonable timeouts** - 10-15 min for analysis, 20-30 min for code changes
4. **Prefer `create-issue` over `add-comment`** for long reports - Issues are searchable
5. **Use `cache-memory: true`** for workflows that benefit from cross-run learning
6. **Add `reaction: eyes`** for event-triggered workflows - Gives users immediate feedback
7. **Use `draft: true`** for auto-created PRs - Let humans review before merge
8. **Keep prompts specific** - Tell the agent exactly what to analyze and what format to output

---

**This is World Fucking Class.** Built on [GitHub Agentic Workflows](https://github.com/github/gh-aw).
