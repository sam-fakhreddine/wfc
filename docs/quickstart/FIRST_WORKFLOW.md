# Your First WFC Workflow

> A complete `/wfc-build` session from prompt to PR. Takes about 5 minutes to read; the real thing takes 10-15 minutes to run.

## The Command

Open Claude Code in your project directory and type:

```
/wfc-build "add rate limiting to the API"
```

## Step 1: Adaptive Interview

WFC asks 3-5 scoping questions before writing a single line of code.

```
WFC: Which endpoints need rate limiting?
You: All /api/* endpoints

WFC: What is the limit per user?
You: 100 requests per minute

WFC: What storage backend should track counts?
You: Redis

WFC: Should limit violations return 429 or silently drop?
You: Return 429 with a Retry-After header
```

WFC uses these answers to scope the implementation precisely. It will not over-build.

## Step 2: Implementation Agent Spawns

WFC assesses complexity (Medium → 1 agent) and dispatches the agent to an isolated git worktree routed through `worktree-manager.sh`. You see:

```
[WFC] Complexity: Medium
[WFC] Dispatching 1 agent to worktree: claude/rate-limiting-1738000000
[WFC] Agent started. TDD cycle beginning...
```

## Step 3: TDD Cycle

The agent works RED → GREEN → REFACTOR:

```
[Agent] RED   - Writing failing tests for RateLimiter class
[Agent] RED   - Writing failing tests for 429 middleware
[Agent] GREEN - Implementing RateLimiter (Redis sliding window)
[Agent] GREEN - Implementing rate limit middleware
[Agent] REFACTOR - Extracting config to settings, removing duplication
[Agent] QUALITY - Running ruff + pyright... PASS
[Agent] TESTS  - 14/14 passing
```

## Step 4: Five-Agent Consensus Review

Five specialist reviewers run in parallel against the diff:

```
[WFC Review] Security     - Checking for header injection, bypass vectors
[WFC Review] Correctness  - Verifying sliding window math, edge cases
[WFC Review] Performance  - Analysing Redis call frequency, N+1 patterns
[WFC Review] Maintainability - SOLID compliance, naming, test coverage
[WFC Review] Reliability  - Redis failure path, race conditions under load

Consensus Score (CS): 2.1 / 10
Decision: INFORMATIONAL - no blocking issues

Findings (2):
  [INFO] Consider adding jitter to Retry-After to prevent thundering herd
  [INFO] Document the sliding window algorithm in a docstring
```

CS below 4.0 means no blockers. The agent notes the informational findings in the PR description.

## Step 5: Branch and PR Created

```
[WFC] Merging to integration branch: develop
[WFC] Branch: claude/rate-limiting-1738000000
[WFC] Creating PR...

PR created: https://github.com/your-org/your-repo/pull/47
  Title: feat: add Redis-backed rate limiting to /api/* endpoints
  Base:  develop
  CS:    2.1 (no blockers)
  Tests: 14 passing
```

## Step 6: You Review on GitHub

WFC stops here. Open the PR link in your browser:

- Read the diff
- Check the test coverage summary in the PR body
- Request changes or approve
- Merge when satisfied

WFC never merges to `main` autonomously. You hold that decision.

## What You Got

- A working rate limiter with Redis backing
- 14 tests covering happy path, limit breach, and Redis failure
- A 5-specialist code review with no blocking findings
- A PR targeting `develop` ready for your review

## Key Principles

- WFC stops at PR creation. You merge.
- The `develop` branch is the integration target. `main` is for releases.
- Every feature gets a 5-agent review before a PR is opened.

## Next Step

Configure WFC for your own project: [CONFIGURE.md](./CONFIGURE.md)
