# wfc-pr-comments

## What It Does

`wfc-pr-comments` automates the process of addressing PR review feedback. It fetches all unresolved review threads from a pull request via the GitHub CLI, evaluates each comment against five dimensions (architectural validity, scope, correctness, severity, and effort-vs-value), presents a triage table for your approval, then fixes valid comments in parallel using category-specific subagents. After pushing fixes, it resolves each addressed thread on GitHub so the PR shows a clean review state.

## When to Use It

- After a PR receives review comments from humans, Copilot, CodeRabbit, or other bots
- When there are multiple review threads and you want to triage them systematically rather than one at a time
- When you want to reject out-of-scope or incorrect suggestions with documented reasoning rather than silently ignoring them
- As the standard step between "PR created" and "ready to merge"

## Usage

```bash
# Auto-detect PR from current branch
/wfc-pr-comments

# Specific PR number
/wfc-pr-comments 42

# PR URL
/wfc-pr-comments https://github.com/owner/repo/pull/42
```

## Example

```
PR #42: Add rate limiting to API endpoints (feat/rate-limiting -> develop)

Fetching unresolved review threads...
Found 5 unresolved threads.

## Triage Results

| # | File | Comment | Verdict | Reason |
|---|------|---------|---------|--------|
| 1 | middleware/rate_limit.py:45 | Add lru_cache to pattern loading | FIX | Valid perf improvement, trivial |
| 2 | orchestrator.py:120 | Rewrite entire auth flow | SKIP | Out of scope for this PR |
| 3 | README.md:8 | Fix typo "teh" → "the" | FIX | Trivial |
| 4 | consensus.py:30 | Why not use dataclass? | RESPOND | Question, not actionable |
| 5 | rate_limit.py:80 | Missing error handling for Redis timeout | FIX | Bug, high severity |

Summary: 3 FIX, 1 SKIP, 1 RESPOND

Proceed with fixes? [y/n]: y

Spawning fix agents (parallel)...
  [Code Quality] fixing rate_limit.py:45 (lru_cache)
  [Docs] fixing README.md:8 (typo)
  [Code Quality] fixing rate_limit.py:80 (Redis error handling)

✅ All fixes applied. Running auto-lint...
✅ Committing: "fix: address 3 PR review comments"
✅ Pushed to feat/rate-limiting

Resolving threads on GitHub...
  ✅ Thread 1 resolved — "Fixed in a3f92c1: added @lru_cache to load_patterns()"
  ✅ Thread 3 resolved — "Fixed in a3f92c1: corrected typo"
  ✅ Thread 5 resolved — "Fixed in a3f92c1: added try/except for Redis ConnectionError"
  ℹ Thread 2 left open (SKIP — out of scope)
  ✅ Thread 4 replied — explained the dataclass tradeoff, left to reviewer
```

## Options

- **PR number or URL** — Specify which PR to process. If omitted, auto-detects from the current branch.
- **User overrides** — During the triage approval step, you can override individual verdicts (e.g., "skip #1, fix #4") before fixes are applied.

The triage step always requires explicit approval before any code changes are made.

## Integration

**Produces:**

- Code fixes committed and pushed to the PR branch
- GitHub review threads marked resolved with commit reference messages
- Replies posted to RESPOND threads explaining the reasoning

**Consumes:**

- GitHub PR review threads (fetched via `gh` CLI + GraphQL)
- Source files referenced in each comment (read before triaging)
- Test suite (subagents run relevant tests after applying fixes)

**Next step:** If CI checks are still failing after addressing review comments, use `/wfc-gh-debug` to diagnose and fix the workflow failures before merging.
