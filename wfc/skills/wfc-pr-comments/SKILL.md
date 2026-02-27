---
name: wfc-pr-comments
description: >-
  Resolves existing, unresolved inline PR review comments (threads attached to
  specific file lines). Fetches comments via gh CLI, triages each against
  project conventions and scope, presents triage table for user approval,
  then applies fixes via parallel subagents and resolves threads on GitHub.

  REQUIREMENTS: gh auth configured, uv installed, wfc/scripts/github/pr_threads.py
  present in repo root.

  ONLY processes inline thread comments where isResolved=false and isOutdated=false.
  Does NOT process: general PR body comments, resolved threads, or comments on
  deleted files.

  TRIGGER: "address inline PR comments", "fix code review feedback", "resolve
  open review threads", "respond to line comments on my PR", /wfc-pr-comments.
license: MIT
---

# WFC:PR-COMMENTS - Structured PR Comment Triage & Fix

Resolve inline code review comments from human and automated reviewers.

## What It Does

1. **Fetch** unresolved inline PR comments via `gh` CLI
2. **Triage** each comment against documented criteria
3. **Present** triage summary for user approval
4. **Fix** valid comments via parallel subagents (one per category)
5. **Commit & push** fixes to the PR branch
6. **Reply and resolve** addressed threads on GitHub

## Requirements

Before invoking this skill, verify:

- `gh auth status` returns authenticated
- `uv --version` succeeds
- `wfc/scripts/github/pr_threads.py` exists in repo root

If any requirement fails, inform user and stop.

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

1. If the user provided a PR number or URL as argument, parse it
2. Otherwise, auto-detect from current branch:

```bash
gh pr view --json number,url,headRefName,baseRefName,title,owner,name
```

If no PR is found, tell the user "No PR associated with current branch" and stop.

Extract from the response:

- `number` — PR number
- `url` — PR URL
- `headRefName` — source branch name
- `baseRefName` — target branch name
- `title` — PR title
- `owner` — repository owner (from `owner.login` in response)
- `name` — repository name (from `name` in response)

Display: `PR #N: <title> (<headRefName> -> <baseRefName>)`

### Step 2: FETCH UNRESOLVED COMMENTS

Fetch only **unresolved, non-outdated** inline review comments.

```bash
uv run python wfc/scripts/github/pr_threads.py fetch {owner} {name} {number} --json
```

**Expected output format**: JSON array of thread objects, each containing:

- `thread_id` — unique identifier (starts with "PRRT_")
- `path` — file path
- `line` — line number
- `body` — comment text
- `author` — commenter login
- `diff_hunk` — surrounding diff context
- `is_resolved` — boolean
- `is_outdated` — boolean

**Filtering rules**:

- Skip if `is_resolved` is `true`
- Skip if `is_outdated` is `true` (log these separately)
- Skip if `path` refers to a file that no longer exists (verify with `git ls-files`)

**Deduplication**: Treat two threads as duplicates if they reference the same `path` + `line` AND the `body` text is >80% similar (ignore whitespace). Keep only the first occurrence.

**If zero unresolved, non-outdated comments remain**: Display "All review threads are resolved or outdated" and stop.

**Display skipped threads**:

```
Skipped N outdated threads (code changed since comment):
- path:line - brief comment summary
```

### Step 3: TRIAGE

For each remaining comment, evaluate 5 dimensions and assign a verdict.

**Read each file being commented on** using the Read tool before evaluating.

#### Dimension 1: PATTERN ALIGNMENT

Does this suggestion align with visible project patterns?

- Check the file being commented on for existing conventions
- If CLAUDE.md exists, read it for project rules
- If PLANNING.md exists, read it for architectural guidance
- Suggestion contradicts visible patterns → lean toward SKIP with explanation

#### Dimension 2: SCOPE CHECK

Is this about code changed in this PR's diff?

- Comment about code in this PR → in scope
- Request for unrelated refactoring → SKIP (reason: "out of scope")
- Feature request disguised as review → SKIP (reason: "feature creep")

#### Dimension 3: CORRECTNESS

Is the suggested fix correct?

- Would implementing it introduce bugs? → SKIP (reason: "would introduce bugs")
- Does reviewer misunderstand the code? → SKIP (reason: "reviewer misunderstanding: ...")
- Fix requires more context than available → RESPOND with clarification request

#### Dimension 4: SEVERITY

Classify the issue type:

| Severity | Criteria | Default Action |
|----------|----------|----------------|
| **Critical** | Security vulnerability, data loss, crash | FIX |
| **High** | Bug, logic error, incorrect behavior | FIX |
| **Medium** | Code quality, missing error handling | FIX if effort ≤ Medium |
| **Low** | Style, naming, formatting | FIX if effort = Trivial |
| **Info** | Question, suggestion, clarification | RESPOND |

#### Dimension 5: EFFORT

Estimate implementation effort:

| Effort | Criteria | Action |
|--------|----------|--------|
| **Trivial** | 1-3 lines, single location | Always FIX |
| **Medium** | Single function or file, <20 lines | FIX if severity ≥ Medium |
| **Large** | Multiple files or >20 lines | SKIP, suggest follow-up issue |

**Verdict per comment**: `FIX` | `SKIP (reason)` | `RESPOND (clarification needed)`

**Special case**: If a comment is phrased as a question but implies a necessary code change (e.g., "Should this be case-sensitive?" in a context where case-sensitivity matters), ask the user during approval: "This question may require a code change. Fix or respond only?"

### Step 4: PRESENT TRIAGE TO USER

Display a markdown table:

```
| # | File | Comment (summary) | Verdict | Reason |
|---|------|-------------------|---------|--------|
| 1 | security_hook.py:45 | Add lru_cache to pattern loading | FIX | Valid perf improvement, trivial effort |
| 2 | orchestrator.py:120 | Rewrite auth flow | SKIP | Out of scope for this PR |
| 3 | README.md:8 | Fix typo "teh" → "the" | FIX | Trivial |
| 4 | consensus.py:30 | Why not use dataclass? | RESPOND | Question, not actionable request |
```

Summary counts:

```
Summary: 8 FIX, 2 SKIP, 1 RESPOND
```

**Use AskUserQuestion** with options:

- "Proceed with all fixes"
- "Modify verdicts first" (user specifies changes)
- "Cancel"

Apply any user overrides before proceeding.

### Step 5: CATEGORIZE & DELEGATE

Group all `FIX` comments into exactly one category each:

| Category | Criteria |
|----------|----------|
| **Lint** | Unused imports, formatting, naming conventions (no logic change) |
| **Code Quality** | Error handling, type safety, simplification, performance (non-security) |
| **Design** | API changes, pattern refactoring, architectural tweaks |
| **Docs** | Typos, missing/outdated comments, docstring fixes |
| **Security** | Vulnerabilities, input validation, hardcoded secrets |

**Category conflict rule**: If a comment fits multiple categories, prioritize in order: Security > Design > Code Quality > Lint > Docs.

Spawn **1 subagent per category that has comments** using the Task tool (run in parallel).

Each subagent receives this prompt:

```
You are fixing PR review comments in category: {category}

PR: #{number} on branch {headRefName}
Repository root: {repo_root}

Comments to address:
{for each comment in this category:}
---
File: {path}:{line}
Thread ID: {thread_id}
Comment by {author}: {body}
Diff context:
{diff_hunk}
---
{end for}

Instructions:
1. Read each file mentioned above using the Read tool
2. Apply the fix described in each comment
3. Verify the fix:
   a. Syntax is valid (no parse errors)
   b. Existing tests still pass (if test file exists: `uv run pytest tests/ -v -k "{test_pattern}"`)
   c. Fix directly addresses the comment
4. Run auto-formatting on every modified file:
   - Python: `uv run ruff check --fix {file}` then `uv run black {file}`
   - TypeScript/JS: `npx prettier --write {file}` (if node_modules exists)
   - Go: `gofmt -w {file}` (if go.mod exists)
   If formatting tools are not installed, report warning and continue.
5. Do NOT fix anything not in the comment list above
6. Do NOT make unrelated improvements or refactors
7. Report which files were modified and a one-line summary of each fix
```

**Note**: If `{test_pattern}` is unknown, use the file path to guess: `tests/test_{filename}.py` or `tests/{filename}_test.py`.

### Step 6: COMMIT & PUSH

After all fix subagents complete:

1. List modified files: `git status --porcelain`
2. For each file shown:
   - If status is `M` (modified) or `A` (added): `git add {path}`
   - If status is `??` (untracked): Check if created by subagent. If yes and it's a helper/test file related to fixes, `git add {path}`. If unrelated, skip.
3. Create commit:

```
fix: address N PR review comments

- {file1}: {one-line fix description}
- {file2}: {one-line fix description}
...

Addresses comments on PR #{number}

Co-Authored-By: Claude <noreply@anthropic.com>
```

1. Push: `git push origin {headRefName}`

### Step 7: RESOLVE THREADS

Build a JSON manifest for all triaged threads:

```json
[
  {
    "thread_id": "PRRT_...",
    "message": "Fixed in {short_sha}: {one-line description}",
    "action": "fixed"
  }
]
```

**Action values**:

- `fixed` — Code was changed, post message and resolve thread
- `responded` — No code change, post explanation and resolve thread
- `skip` — No code change, post explanation but DO NOT resolve (leave for human)

Run bulk resolution:

```bash
uv run python wfc/scripts/github/pr_threads.py bulk-resolve {owner} {name} manifest.json
```

**Error handling**: If the script reports partial failure (some threads failed), display which threads failed and their error messages. Do not report complete success.

### Step 8: REPORT

Display final summary:

```
## PR Comment Fixes Complete

**PR:** #{number} — {title}
**Branch:** {headRefName}
**Commit:** {short_sha}

### Fixed (N comments)
- {path}:{line} — {fix description}
- ...

### Skipped (N comments)
- {path}:{line} — {reason}
- ...

### Responded (N comments)
- {path}:{line} — {reply summary}
- ...

Pushed to {headRefName}. PR updated.
```
