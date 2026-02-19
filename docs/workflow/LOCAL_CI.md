# Local CI

Run GitHub Actions workflows locally before pushing, so you catch
failures on your machine instead of in the CI queue.

## What is act?

[act](https://github.com/nektos/act) is a tool that runs GitHub Actions
workflows locally using Docker containers. WFC uses it to gate PR
creation: `make pr` runs a fast act check before calling `gh pr create`.

## Prerequisites

- **Docker Desktop** — running and healthy (`docker info` should succeed)
- **act CLI** — `brew install act`

Verify both:

```bash
docker info --format '{{.ServerVersion}}'   # should print a version
act --version                               # should print act version
```

## First-Run: Pull Docker Images

act needs Docker images that mirror the GitHub-hosted runners. The first
pull takes 5-15 minutes; after that the images are cached locally.

```bash
make act-pull
```

Run this once after cloning. You only need to re-run it when the runner
image changes (rare).

## The Gate: make pr

`make pr` is the standard way to open a pull request in WFC. It runs the
fast act check before creating the PR:

```text
make pr
  └── scripts/act-check.sh --fast   # lint + validate (~2 min)
       └── gh pr create             # only if act passes
```

If act fails, the PR is not created. Fix the failures, then run
`make pr` again.

## Commands

| Command | What it does | Time |
| --- | --- | --- |
| `make act-pull` | Pull Docker runner images (first-run setup) | 5-15 min |
| `make act-fast` | Run lint + validate workflows only | ~2 min |
| `make act-check` | Run all CI workflows (full gate) | ~10 min |
| `make pr` | Run fast gate, then create PR if green | ~2 min + PR |

## Full vs Fast Check

**Fast** (`make act-fast`, `make pr`): runs lint and skill validation
only. Catches the most common failures quickly.

**Full** (`make act-check`): runs all workflows. Use this before merging
or when you want confidence that the complete CI suite passes.

## Emergency Bypass

If Docker is unavailable or act is broken, you can skip the act gate:

```bash
WFC_SKIP_ACT=1 make pr
```

This skips the local check and creates the PR directly. Use sparingly -
the remote CI still runs and will catch failures.

## Local Secrets (.act.secrets)

To inject secrets into act runs (e.g. `ANTHROPIC_API_KEY` for
integration tests), create `.act.secrets` in the repo root:

```text
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
```

This file is gitignored. act reads it automatically. Never commit it.

## Troubleshooting

### Docker not running

```text
Error: Cannot connect to the Docker daemon
```

Start Docker Desktop and wait for it to show "running", then retry.

### Timeout on first image pull

The default timeout may be too short for large images on slow
connections. Increase it in `.actrc` or run `make act-pull` manually
before `make pr`.

### macOS: gtimeout not found

`act-check.sh` uses `gtimeout` (from `coreutils`) for the pull timeout.
Install it:

```bash
brew install coreutils
```

### act workflow mismatch

If a workflow uses a GitHub-only feature that act does not support, the
step may be skipped or fail differently than on GitHub. Check the act
output for `[skipped]` annotations.
