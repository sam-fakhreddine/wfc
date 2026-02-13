---
name: wfc-pr-comments
description: Intelligent PR comment triage and fix system. Fetches PR review comments via gh CLI, evaluates each against architectural validity, scope, correctness, and codebase conventions, then fixes valid comments in parallel via subagents. Use when a PR has review comments to address. Triggers on "address PR comments", "fix PR feedback", "handle review comments", or explicit /wfc-pr-comments. Ideal for PRs with multiple review comments from humans or bots (Copilot, CodeRabbit, etc.). Not for creating PRs (use wfc-build) or code review (use wfc-review).
license: MIT
---

# WFC:PR-COMMENTS - Intelligent PR Comment Triage & Fix

**Fetch, triage, fix.** Automates addressing PR review comments from humans, Copilot, CodeRabbit, and other reviewers.

## What It Does

1. **Fetch** all PR comments via `gh` CLI
2. **Triage** each comment against 5 validity criteria
3. **Present** triage summary to user for approval
4. **Fix** valid comments in parallel (subagents by category)
5. **Commit & push** fixes to the PR branch

## Usage

```bash
# Auto-detect PR from current branch
/wfc-pr-comments

# Specific PR number
/wfc-pr-comments 42

# PR URL
/wfc-pr-comments https://github.com/owner/repo/pull/42
```

---

## Workflow

Follow these steps exactly in order.

### Step 1: DETECT PR

Determine which PR to work on:

1. If the user provided a PR number or URL as argument, use that.
2. Otherwise, auto-detect from the current branch:

```bash
gh pr view --json number,url,headRefName,baseRefName,title
```

If no PR is found, tell the user and stop.

Display: `PR #N: <title> (<head> -> <base>)`

### Step 2: FETCH COMMENTS

Fetch all review comments from the PR. Run these two `gh api` calls:

```bash
# Inline review comments (comments on specific lines of code)
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate

# Review-level comments (top-level review bodies)
gh api repos/{owner}/{repo}/pulls/{number}/reviews --paginate
```

Extract from each comment:
- `id` — unique identifier
- `user.login` — author
- `body` — comment text
- `path` — file being commented on
- `line` or `original_line` — line number
- `diff_hunk` — surrounding diff context
- `created_at` — timestamp

**Deduplication:** If two comments reference the same file + line + substantially identical message, treat them as one.

**Group by file** for display purposes.

If there are zero comments, tell the user and stop.

### Step 3: TRIAGE

This is the core intelligence. For each comment, evaluate 5 dimensions and assign a verdict.

**Read each file being commented on** before evaluating (use the Read tool).

#### Dimension 1: ARCHITECTURAL VALIDITY

Does this suggestion align with project patterns?
- Check existing conventions in the file and codebase
- Consider CLAUDE.md / PLANNING.md rules
- A suggestion that contradicts project conventions → lean toward SKIP

#### Dimension 2: SCOPE CHECK

Is this about code in this PR's diff, or asking for unrelated work?
- Comment about code changed in this PR → in scope
- Request for unrelated refactoring → out of scope → SKIP
- Feature request disguised as review comment → SKIP

#### Dimension 3: CORRECTNESS

Is the suggested fix actually correct?
- Would implementing it introduce bugs?
- Does it handle edge cases the reviewer may have missed?
- Is the reviewer wrong about the issue? If so → SKIP with explanation

#### Dimension 4: SEVERITY

- **Critical** (security, data loss, crashes) → always FIX
- **High** (bugs, logic errors) → FIX
- **Medium** (code quality, patterns) → FIX if valid
- **Low** (style, preferences) → FIX if trivial, SKIP if opinionated
- **Info** (questions, suggestions) → RESPOND only

#### Dimension 5: EFFORT vs VALUE

- **Trivial** (1-2 lines) → always FIX
- **Medium** (function-level) → FIX if high value
- **Large** (multi-file refactor) → SKIP, suggest follow-up issue

**Verdict per comment:** `FIX` | `SKIP (reason)` | `RESPOND (reply only)`

### Step 4: PRESENT TRIAGE TO USER

Display a markdown table summarizing the triage:

```
| # | File | Comment (summary) | Verdict | Reason |
|---|------|-------------------|---------|--------|
| 1 | security_hook.py:45 | Add lru_cache to pattern loading | FIX | Valid perf improvement, trivial |
| 2 | orchestrator.py:120 | Rewrite auth flow | SKIP | Out of scope for this PR |
| 3 | README.md:8 | Fix typo "teh" → "the" | FIX | Trivial |
| 4 | consensus.py:30 | Why not use dataclass? | RESPOND | Question, not actionable |
```

Then show summary counts:

```
Summary: 8 FIX, 2 SKIP, 1 RESPOND

Proceed with fixes?
```

**Use AskUserQuestion** to get approval. The user may:
- Approve as-is
- Override specific verdicts (e.g., "skip #1, fix #4")
- Cancel entirely

Apply any user overrides before proceeding.

### Step 5: CATEGORIZE & DELEGATE

Group all `FIX` comments into categories:

| Category | Examples |
|----------|----------|
| **Lint** | Unused imports, formatting, naming conventions |
| **Code Quality** | Caching, error handling, type safety, simplification |
| **Design** | Architecture changes, API modifications, patterns |
| **Docs** | Typos, missing docs, outdated comments |
| **Security** | Vulnerabilities, hardcoded secrets, input validation |

Spawn **1 subagent per category** via the Task tool (run in parallel).

Each subagent receives this prompt:

```
You are fixing PR review comments in category: {category}

PR: #{number} on branch {headRefName}
Repository root: {repo_root}

Comments to address:
{for each comment in this category:}
---
File: {path}:{line}
Comment by {author}: {body}
Diff context:
{diff_hunk}
---
{end for}

Instructions:
1. Read each file mentioned above
2. Apply the fix described in each comment
3. Verify the fix is correct — do not introduce regressions
4. Run relevant tests if they exist (use: uv run pytest {test_file} -v)
5. Do NOT fix anything not in the comment list above
6. Do NOT make unrelated improvements or refactors
```

For `RESPOND` comments: Do NOT spawn a subagent. Instead, after fixes are committed, use `gh api` to reply to the comment on GitHub with an explanation.

### Step 6: COMMIT & PUSH

After all fix subagents complete:

1. Check which files were modified: `git status`
2. Stage all fixed files (by name, not `git add -A`)
3. Create a single commit:

```
fix: address N PR review comments

- {file1}: {brief description of fix}
- {file2}: {brief description of fix}
...

Addresses comments on PR #{number}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

4. Push to the PR branch:

```bash
git push origin {headRefName}
```

### Step 7: REPORT

Display a final summary:

```
## PR Comment Fixes Complete

**PR:** #{number} — {title}
**Branch:** {headRefName}

### Fixed (N comments)
- {file}:{line} — {brief fix description}
- ...

### Skipped (N comments)
- {file}:{line} — {reason}
- ...

### Responded (N comments)
- {file}:{line} — {reply summary}
- ...

Pushed to {headRefName}. PR updated.
```

---

## Integration with WFC

### Fits After
- `wfc-build` or `wfc-implement` (which create PRs)
- Any workflow that pushes a branch and creates a PR

### Complements
- `wfc-review` — internal review BEFORE creating a PR
- `wfc-pr-comments` — external feedback AFTER PR is created

### Typical Flow
```
wfc-build → Push PR → Reviewers comment → /wfc-pr-comments → Push fixes → Merge
```

## Philosophy

**ELEGANT:** Single skill replaces manual comment-by-comment triage
**PARALLEL:** Fix subagents run concurrently by category
**TOKEN-AWARE:** Only reads files that have comments, not the entire codebase
**SAFE:** User approval gate before any fixes are applied
