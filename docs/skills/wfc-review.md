# wfc-review

## What It Does

`wfc-review` runs five fixed specialist reviewers in parallel — Security, Correctness, Performance, Maintainability, and Reliability — then calculates a Consensus Score (CS) using a weighted formula with a Minority Protection Rule. Findings from multiple reviewers pointing to the same code location are deduplicated via SHA-256 fingerprinting. The result is a `REVIEW-{task_id}.md` report and a pass/fail decision based on the CS tier. For small changes, only 2 reviewers run (Tier 1); for large or risky changes, specialist agents are added on top of the base 5 (Tier 3).

## When to Use It

- You want an objective quality gate on code before merging
- You are reviewing an existing PR or diff manually
- A feature touches auth, database migrations, or API contracts (Tier 3 activates automatically)
- You want to catch security issues before they reach production
- `wfc-build` or `wfc-implement` already called this automatically, but you want a fresh pass

Not needed for documentation-only changes or trivial typo fixes.

## Usage

```bash
/wfc-review TASK-001
/wfc-review path/to/code
/wfc-review TASK-001 --properties PROP-001,PROP-002
```

## Example

```
User: /wfc-review TASK-002

Activating reviewers for TASK-002 (M complexity, 180 lines changed)...
  Tier 2: Standard Review — all 5 base reviewers

Security Reviewer:       PASS  — No injection or auth issues found
Correctness Reviewer:    WARN  — Missing null check on user_id at auth.py:45
Performance Reviewer:    PASS  — No N+1 queries detected
Maintainability Reviewer: PASS — Good SOLID adherence
Reliability Reviewer:    WARN  — No timeout on external HTTP call at client.py:88

[DEDUPLICATION]
  2 findings (0 duplicates across reviewers)

[CONSENSUS SCORE]
  R_1 = (5.0 * 7.0) / 10 = 3.50  (null check, Correctness)
  R_2 = (6.0 * 8.0) / 10 = 4.80  (missing timeout, Reliability)
  CS = (0.5 * 4.15) + (0.3 * 4.15 * 2/5) + (0.2 * 4.80) = 3.54

Decision: MODERATE (CS = 3.54) — inline comments added, review passes

Output: REVIEW-TASK-002.md
```

## Options

```bash
/wfc-review TASK-001                      # Review by task ID
/wfc-review path/to/code                  # Review files directly
/wfc-review TASK-001 --properties PROP-001,PROP-002   # Include specific properties
```

No flags are needed to control which tier runs — tier selection is automatic based on change size and risk signals (auth files, migrations, API routes, infra configs).

## Integration

**Produces:**

- `REVIEW-{task_id}.md` — full report with per-reviewer summaries and deduplicated findings
- Consensus Score and decision tier (Informational / Moderate / Important / Critical)

**Consumes:**

- Task files from the git worktree or specified path
- `PROPERTIES.md` — formal properties to verify against
- Git diff content
- `docs/solutions/` — searched for known past issues related to the code under review

**Decision tiers:**

| Tier | CS Range | Result |
|------|----------|--------|
| Informational | CS < 4.0 | Review passes |
| Moderate | 4.0 - 6.9 | Review passes, inline comments added |
| Important | 7.0 - 8.9 | Review fails, merge blocked |
| Critical | CS >= 9.0 | Review fails, merge blocked, escalation triggered |

**Next step:** Fix any Important or Critical findings, then re-run `/wfc-review` or push a corrected commit. Run `/wfc-compound` if the root cause was non-trivial and worth documenting.
