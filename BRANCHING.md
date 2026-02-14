# Branching Strategy

Autonomous branching model for WFC. Designed so agents can ship code continuously while humans retain control over what reaches production.

---

## Branch Hierarchy

```
main ─── stable, tagged releases, protected
  └── develop ─── integration, CI-gated, auto-merge for agents
        ├── claude/TASK-XXX-slug ── agent branches (auto-merge to develop)
        ├── feat/TASK-XXX-slug ──── human branches (manual merge)
        ├── fix/TASK-XXX-slug ───── bugfixes
        ├── hotfix/TASK-XXX-slug ── emergency (targets main directly)
        └── rc/vX.Y.Z ── 24h soak ── main + tag
```

**main** is the release branch. Every commit on main is a tagged release that passed a 24-hour soak period. Branch protection rules prevent direct pushes, force pushes, and branch deletion.

**develop** is the integration branch. All feature work merges here first. CI runs on every push. If CI breaks, the offending merge is auto-reverted within minutes.

**Agent branches** (`claude/*`) are created and managed entirely by autonomous agents. They auto-merge to develop via squash once CI passes.

**Human branches** (`feat/*`, `fix/*`) follow standard PR review workflow with manual merge.

**Hotfix branches** (`hotfix/*`) are the only branches that target main directly, bypassing develop. Use sparingly for critical production fixes.

**Release candidates** (`rc/vX.Y.Z`) are cut from develop on a schedule, soak for 24 hours, then promote to main with a version tag.

---

## The Autonomous Loop

The full cycle from issue to production, step by step.

### Step 1: Human Creates a GitHub Issue

A human opens an issue and applies the `agent-ready` label. This label signals that the issue is well-defined enough for an autonomous agent to pick up. The issue body should include acceptance criteria, affected files or areas, and any constraints.

Issues without `agent-ready` remain in the normal human backlog.

### Step 2: Agent Dispatch (`agent-dispatch.yml`)

A cron-triggered workflow runs every 15 minutes. It queries GitHub for unassigned issues with the `agent-ready` label:

```
gh issue list --label agent-ready --assignee "" --state open --json number,title
```

For each issue found, the workflow:

1. Assigns the issue to the `wfc-bot` user to prevent double-pickup.
2. Triggers Claude Code on a self-hosted runner labeled `wfc-agent`.
3. Passes the issue number and title as workflow inputs.

If no self-hosted runner is available, the job queues until one comes online. The workflow processes one issue per dispatch cycle to avoid resource contention.

### Step 3: Agent Builds (`/wfc-build`)

On the runner, Claude Code checks out `develop`, creates a branch `claude/TASK-{issue_number}-{slug}`, and invokes `/wfc-build` with the issue description as input.

The build follows the standard WFC workflow:

1. **Adaptive interview** -- the agent resolves ambiguities from the issue body.
2. **TDD cycle** -- RED (write failing tests), GREEN (implement), REFACTOR (clean up).
3. **Quality gate** -- `make check-all` (lint, format, test, validate).
4. **Consensus review** -- `/wfc-review` with 5 expert personas.
5. **Push** -- the agent pushes the branch and opens a PR targeting `develop`.

The PR title follows the format: `feat: TASK-{number} {short description}`.

The agent comments on the original issue with a link to the PR, then closes the issue if the PR is opened successfully.

### Step 4: Auto-Merge for Agent PRs (`auto-merge-develop.yml`)

A workflow triggers on PR open events. If the PR:

- Targets `develop`
- Originates from a `claude/*` branch
- Has all CI checks passing

Then the workflow enables auto-merge with squash:

```
gh pr merge --auto --squash $PR_NUMBER
```

This means agent PRs merge to develop without human intervention, as long as CI is green. Human PRs (`feat/*`, `fix/*`) are not auto-merged and require manual review.

### Step 5: Develop Health Monitor (`develop-health.yml`)

A workflow triggers on every push to `develop`. It runs the full test suite, linting, and validation. If any check fails:

1. **Identify the offending commit** via `git bisect` or last-merge detection.
2. **Auto-revert** the merge commit that broke develop.
3. **Push the revert** directly to develop.
4. **Create a bug issue** referencing the reverted PR and the failure logs.
5. **Apply the `agent-ready` label** to the new bug issue so the agent can retry.

A loop guard prevents infinite revert cycles: if the commit being checked is itself a revert (message starts with `Revert "`), the workflow skips it and alerts maintainers instead.

### Step 6: Cut Release Candidate (`cut-rc.yml`)

A scheduled workflow runs every Friday at 18:00 UTC. It:

1. Reads the current version from `pyproject.toml` or the latest tag.
2. Bumps the version using autosemver (based on commit messages since last tag).
3. Creates a branch `rc/vX.Y.Z` from the current `develop` HEAD.
4. Opens a PR from `rc/vX.Y.Z` targeting `main`.
5. Labels the PR with `release-candidate`.

The PR description includes a changelog generated from commit messages since the last release.

If develop has no new commits since the last RC, the workflow exits without creating a new RC.

### Step 7: Promote Release Candidate (`promote-rc.yml`)

A scheduled workflow runs every 6 hours. For each open PR labeled `release-candidate`:

1. Check if the PR has been open for at least 24 hours (soak period).
2. Check if all CI checks are green and have remained green throughout the soak.
3. If both conditions are met, merge the PR to main.
4. Tag the merge commit with `vX.Y.Z`.
5. Delete the `rc/vX.Y.Z` branch.

If CI fails at any point during the soak, the 24-hour clock resets. If the RC cannot pass CI for 72 hours, the workflow closes the PR and notifies maintainers.

### Step 8: Release and Publish (`release.yml` + `publish.yml`)

These workflows trigger on tag push events matching `v*.*.*`:

- **release.yml**: Creates a GitHub Release with auto-generated release notes.
- **publish.yml**: Builds and publishes the package to PyPI (or the configured registry).

Both are standard release workflows and are not specific to the autonomous loop.

---

## Branch Naming Conventions

| Pattern | Purpose | Target | Merge Method |
|---------|---------|--------|-------------|
| `claude/TASK-XXX-slug` | Agent-created feature or fix | develop | Auto-squash |
| `feat/TASK-XXX-slug` | Human-created feature | develop | Manual squash |
| `fix/TASK-XXX-slug` | Bugfix | develop | Manual squash |
| `hotfix/TASK-XXX-slug` | Emergency production fix | main | Manual merge |
| `rc/vX.Y.Z` | Release candidate | main | Auto-merge after soak |

Rules:

- `XXX` is the GitHub issue number, zero-padded to 3 digits (e.g., `TASK-007`).
- `slug` is a lowercase, hyphenated summary of the change (e.g., `add-rate-limiting`).
- Branch names must not exceed 100 characters.
- Hotfix branches must reference a severity-critical issue.

---

## Safety Mechanisms

Eight layers of protection ensure that autonomous agents cannot break production.

| Layer | Protection | Details |
|-------|-----------|---------|
| 1. Branch rulesets | No force push or delete on main + develop | GitHub branch protection rules. Require PR reviews for main. Require CI for both. |
| 2. CI gates | All PRs must pass lint, test, and validate | `make check-all` runs on every PR. No merge without green CI. |
| 3. Auto-revert + loop guard | develop self-heals on failure | Bad merges are reverted automatically. Revert commits are skipped to prevent infinite loops. |
| 4. RC soak (24h) | RC must be green for 24 continuous hours | Any CI failure during soak resets the clock. 72h timeout closes the RC. |
| 5. Merge engine rollback | Atomic revert on failed merges | WFC merge engine creates a rollback point before every merge. Failed merges revert to the rollback point. |
| 6. Develop-exists fallback | Falls back to main if develop is missing | If develop is accidentally deleted, agent dispatch and RC workflows fall back to main as the integration branch. |
| 7. Agent retry + stale detection | Max 2 retries; unassign stale after 2h | If an agent fails to open a PR within 2 hours, the issue is unassigned and returned to the backlog. Agents retry up to 2 times before escalating. |
| 8. Version tags + build-info | Every main merge is tagged + build metadata | A `.build-info.json` file is generated on every release with commit SHA, timestamp, version, and RC source branch. |

### Layer Details

**Layer 1 -- Branch Rulesets**

Configure in GitHub repository settings or via `gh api`:

```
main:
  - Require pull request reviews (1 reviewer minimum)
  - Require status checks to pass
  - No force push
  - No deletion
  - Restrict pushes to release automation only

develop:
  - Require status checks to pass
  - No force push
  - No deletion
  - Allow direct push from auto-revert workflow only
```

**Layer 3 -- Loop Guard**

The auto-revert workflow checks the commit message before acting:

```bash
LAST_MSG=$(git log -1 --format="%s" develop)
if [[ "$LAST_MSG" == Revert* ]]; then
  echo "Skipping: last commit is already a revert"
  # Notify maintainers instead of reverting again
  exit 0
fi
```

**Layer 7 -- Stale Detection**

The dispatch workflow tracks issue assignment timestamps. A separate cron job (every 30 minutes) checks for issues assigned to `wfc-bot` for more than 2 hours without a corresponding open PR. These issues are unassigned and re-labeled `agent-ready` with an `agent-retry` counter label. After 2 retries, the `agent-ready` label is removed and `needs-human` is applied.

**Layer 8 -- Build Info**

Generated on every tag push:

```json
{
  "version": "1.2.3",
  "commit": "abc1234def5678",
  "timestamp": "2026-02-14T18:00:00Z",
  "rc_branch": "rc/v1.2.3",
  "rc_soak_hours": 24.5,
  "develop_sha": "def5678abc1234"
}
```

---

## Configuration

### Default Behavior

Out of the box, WFC uses `develop` as the integration branch. All agent and feature branches target `develop`. Release candidates are cut from `develop` and promoted to `main`.

### Backward Compatibility

Projects that do not use a `develop` branch can configure WFC to target `main` directly. Set in `wfc.config.json`:

```json
{
  "branching": {
    "integration_branch": "main"
  }
}
```

When `integration_branch` is set to `main`:

- Agent branches (`claude/*`) open PRs targeting `main` instead of `develop`.
- Auto-merge still applies for `claude/*` PRs.
- The RC workflow is disabled (no intermediate branch needed).
- The develop-health workflow is disabled.
- Branch protection on `main` should still require CI checks.

### Full Configuration Reference

```json
{
  "branching": {
    "integration_branch": "develop",
    "rc_schedule": "0 18 * * 5",
    "rc_soak_hours": 24,
    "rc_timeout_hours": 72,
    "agent_stale_hours": 2,
    "agent_max_retries": 2,
    "auto_merge_agent_prs": true,
    "auto_revert_on_failure": true
  }
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `integration_branch` | `"develop"` | Branch that receives all feature merges |
| `rc_schedule` | `"0 18 * * 5"` | Cron expression for RC cuts (default: Friday 18:00 UTC) |
| `rc_soak_hours` | `24` | Hours an RC must stay green before promotion |
| `rc_timeout_hours` | `72` | Hours before a failing RC is closed |
| `agent_stale_hours` | `2` | Hours before an unresponsive agent is unassigned |
| `agent_max_retries` | `2` | Maximum agent retries per issue |
| `auto_merge_agent_prs` | `true` | Enable auto-squash for `claude/*` PRs |
| `auto_revert_on_failure` | `true` | Enable auto-revert on develop CI failure |

---

## Self-Hosted Runner Setup

Agents run on self-hosted GitHub Actions runners with the `wfc-agent` label.

### Prerequisites

- **Claude Code CLI**: Installed and accessible in PATH.
- **ANTHROPIC_API_KEY**: Set as a repository secret or runner environment variable.
- **GitHub CLI** (`gh`): Authenticated with repo access (`gh auth login`).
- **UV**: Installed for Python operations.
- **Git**: Configured with a bot identity for commits.

### Setup Script

Reference: `scripts/setup-agent-runner.sh`

The script performs:

```bash
# 1. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
npm install -g @anthropic-ai/claude-code

# 2. Configure git identity
git config --global user.name "wfc-bot"
git config --global user.email "wfc-bot@users.noreply.github.com"

# 3. Authenticate GitHub CLI
echo "$GH_TOKEN" | gh auth login --with-token

# 4. Register as GitHub Actions runner
./config.sh \
  --url https://github.com/OWNER/REPO \
  --token $RUNNER_TOKEN \
  --labels wfc-agent \
  --name "wfc-agent-$(hostname)" \
  --unattended

# 5. Install and start as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### Runner Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB |
| Network | Outbound HTTPS | Outbound HTTPS |

### Security Notes

- The runner executes arbitrary Claude Code sessions. Isolate it from production infrastructure.
- Use ephemeral runners where possible (destroy after each job).
- Store `ANTHROPIC_API_KEY` as a GitHub Actions secret, not in the runner environment.
- Scope `GH_TOKEN` to the minimum permissions: `issues:write`, `pull-requests:write`, `contents:write`.

---

## SaaS Deployment

Production deployments should always source from `main`.

### Deployment Trigger

Deploy on one of:

- **Tag push**: Watch for tags matching `v*.*.*`. Every tag on main is a promoted, soak-tested release.
- **Build info**: Read `.build-info.json` from the main branch for deployment metadata (version, commit SHA, timestamp).

### Deployment Flow

```
RC merges to main
  -> Tag vX.Y.Z created
  -> release.yml creates GitHub Release
  -> publish.yml builds and publishes package
  -> Deploy pipeline triggers on tag (or webhook)
  -> Production updated
```

### Rollback

If a release causes issues in production:

1. Deploy the previous tag (`git checkout vX.Y.Z-1`).
2. Open a hotfix issue with `agent-ready` label if the fix is straightforward.
3. Or open a hotfix branch manually for complex fixes.
4. Hotfix merges to main directly, creating a new patch tag.

### Monitoring Releases

```bash
# Latest release
gh release view --repo OWNER/REPO

# All releases
gh release list --repo OWNER/REPO

# Build info for current main
gh api repos/OWNER/REPO/contents/.build-info.json \
  --jq '.content' | base64 -d | jq .
```

---

## Workflow Summary

```
                    GitHub Issue
                    (agent-ready label)
                         |
                         v
              agent-dispatch.yml (cron 15m)
                  assigns + triggers
                         |
                         v
                Claude Code on runner
              /wfc-build -> TDD -> review
                         |
                         v
               Push claude/TASK-XXX-slug
                    Open PR to develop
                         |
                         v
            auto-merge-develop.yml (squash)
                         |
                         v
               develop-health.yml (CI)
              pass: continue | fail: revert + bug issue
                         |
                         v
                cut-rc.yml (Friday 18:00 UTC)
              rc/vX.Y.Z branch -> PR to main
                         |
                         v
              promote-rc.yml (every 6h)
            24h green soak -> merge + tag
                         |
                         v
            release.yml + publish.yml (on tag)
                         |
                         v
                    Production
```
