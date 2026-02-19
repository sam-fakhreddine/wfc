---
applyTo: ".github/workflows/**/*.yml"
---
# GitHub Actions Workflow Review Rules — Defensive Programming Standard

## Critical (Block Merge)

### Security (DPS-8)

- `${{ github.event.issue.title }}` or similar user-controlled input injected directly into `run:` blocks — GitHub Actions script injection. Use environment variables instead
- Secrets printed to logs via `echo` — flag any `echo "${{ secrets.* }}"` pattern
- `permissions` block missing or overly broad (`contents: write` when only `read` needed) — least privilege required
- Any step that pushes to `main` directly outside `promote-rc.yml` — only RC promotion pushes to main
- Workflow tokens with write permissions that are not strictly necessary — scope down

### Pipeline Safety (DPS-10)

- Missing revert-loop guard: workflows triggered by `push` to `develop` MUST skip if actor is `github-actions[bot]` or commit message starts with `Revert`
- Missing concurrency group — parallel runs of the same workflow can cause race conditions
- No timeout on long-running steps — all `run:` blocks with external calls need `timeout-minutes:`
- Missing health/status check before deploying or promoting

### Error Handling (DPS-4)

- Steps that can fail without `continue-on-error: true` or explicit error handling
- `set -e` missing in multi-line shell scripts — silent failures on intermediate commands
- Missing error output capture (`2>&1`) on commands where failure diagnostics matter
- `|| true` used to suppress errors that should actually be handled

### Boundary Validation (DPS-1)

- Workflow inputs (`inputs.*`) used without validation or type checking
- Missing `default` values on optional workflow_dispatch inputs
- `jq` expressions that assume fields exist without `// null` or `// empty` fallbacks
- User-provided input sizes not bounded (could be used to create oversized branch names, etc.)

## Important (Warn)

### Retry and Timeout (DPS-5)

- External API calls (`gh api`, `curl`) without retry logic or `--retry` flag
- Steps calling external services without `timeout-minutes` — flag unbounded wait
- No backoff between retry attempts — can overwhelm external services

### Observability (DPS-6)

- Missing `echo` statements before long operations — silent workflows are hard to debug
- Cron schedules without comments explaining the timing
- Missing step names — unnamed steps are hard to identify in the Actions UI
- No summary output (`>> $GITHUB_STEP_SUMMARY`) for important results

### Configuration (DPS-9)

- Hardcoded values that should be inputs or env vars (branch names, version numbers, limits)
- Hardcoded branch name `main` where `develop` is the intended target for agent PRs
- Missing `--repo "${{ github.repository }}"` on `gh` commands — breaks on forks
- Environment-specific values without fallback defaults

### Idempotency (DPS-2)

- Workflows that create resources (branches, PRs, issues) without checking if they already exist
- Tag creation without checking if tag already exists — will fail on re-run
- `gh issue create` or `gh pr create` without deduplication guard — creates duplicates on re-trigger

### State Management (DPS-3)

- Job outputs used in later jobs without checking if the producing job was skipped
- `steps.*.outputs.*` accessed without verifying the step actually ran
- `PIPESTATUS[0]` used without `set -o pipefail` in the shell — exit code may be lost

## Style (Inform Only)

- Prefer `actions/checkout@v4` (pinned major version) over `@main` or unpinned
- Step `id` values should use kebab-case
- Long `jq` expressions should use `--jq` flag rather than piping to `jq`
- Workflow `name` should be descriptive and match the filename intent
- `gh pr merge` on agent branches should use `--auto --squash` for clean history
