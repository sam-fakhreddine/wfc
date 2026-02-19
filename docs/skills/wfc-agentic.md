# wfc-agentic

## What It Does

Generates production-ready GitHub Agentic Workflow (gh-aw) Markdown files through an adaptive interview. It asks what you want to automate, which trigger should fire it, what the agent is allowed to write back, and which AI engine to use — then produces a `.github/workflows/<name>.md` file with correct frontmatter, safe-output configuration, and a natural-language prompt for the agent. The output compiles directly with `gh aw compile` and runs on GitHub Actions with strong security guardrails.

## When to Use It

- Automating issue triage, labeling, or analysis on new issues
- Creating a CI doctor that investigates failed workflow runs and opens bug reports
- Building a slash-command workflow (e.g., `/fix`) that lets contributors trigger AI fixes on PRs
- Setting up a scheduled report (weekly repo health, test coverage trends)
- Replacing repetitive manual tasks that follow a consistent decision process

## Usage

```bash
/wfc-agentic [description]
```

## Example

```bash
/wfc-agentic "triage new issues with labels and analysis comments"
```

Interview:

```
Q: What should trigger this workflow?
A: Whenever a new issue is opened or reopened

Q: What should the agent produce?
A: Apply labels and post a triage comment with root cause analysis

Q: Which AI engine?
A: Copilot (default)

Q: Any special tools needed?
A: GitHub API for reading issues and labels
```

Generated file (`.github/workflows/issue-triage.md`):

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
    max: 1

tools:
  github:
    toolsets: [issues]

timeout-minutes: 10
---

# Issue Triage

Analyze issue #${{ github.event.issue.number }} in ${{ github.repository }}.

1. Read the issue title, body, and any existing labels
2. Search for similar open or closed issues
3. Select appropriate labels from the repository's label set
4. Post a triage comment summarizing the issue category,
   reproduction likelihood, and suggested next steps
```

Next steps printed by the skill:

```
Compile with:  gh aw compile issue-triage
Review lock:   cat .github/workflows/issue-triage.lock.yml
Test locally:  gh aw run issue-triage
Commit both:   git add .github/workflows/issue-triage.{md,lock.yml}
```

## Options

| Argument | Description |
|----------|-------------|
| (none) | Fully guided interactive interview (5 questions) |
| `"description"` | Seed the interview with a description of what to automate |

**Supported trigger types:** `issues`, `pull_request`, `schedule` (daily/weekly/cron), `workflow_dispatch`, `slash_command`, `workflow_run`, `push`

**Supported AI engines:** `copilot` (default), `claude` (Anthropic), `codex` (OpenAI)

**Supported safe-outputs:** `create-issue`, `create-pull-request`, `add-comment`, `add-labels`, `push-to-pull-request-branch`, `noop`

**Prerequisites:** `gh` CLI v2.0.0+ and `gh extension install github/gh-aw`, plus the appropriate engine secret configured in your repository settings.

## Integration

**Produces:**

- `.github/workflows/<name>.md` — gh-aw Markdown workflow file (you commit this)
- Compile instructions for generating the corresponding `.lock.yml`

**Consumes:**

- User answers from the adaptive interview
- Description of what to automate (optional argument)

**Next step:** Compile the generated file with `gh aw compile <name>`, review the lock file, commit both files, and push. The workflow activates on its next trigger event. See `docs/workflow/AGENTIC_WORKFLOWS.md` for the full reference on frontmatter fields, tool configuration, and the gh-aw security model.
