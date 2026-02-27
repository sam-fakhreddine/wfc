---
name: wfc-review
description: >-
  Orchestrates parallel code review across five analytical dimensions (Security,
  Correctness, Performance, Maintainability, Reliability) for application source
  code. Produces a heuristic Consensus Score and a prioritized, deduplicated
  finding report suitable for merge/deploy decisions.

  TRIGGERS: "review this code", "analyze this PR for quality", "check for bugs",
  "is this safe to merge", "is this safe to deploy", "/wfc-review".

  REQUIRES: Application source code in supported languages (.py, .js, .ts, .go,
  .java, .rb, .php, .rs, .c, .cpp, .sql).

  NOT FOR: runtime error debugging, Infrastructure-as-Code (Terraform,
  Kubernetes, Dockerfiles, CloudFormation), dependency/CVE auditing,
  style-only linting, code walkthroughs, or config files without executable
  logic (YAML, JSON, TOML, ci.yml, tsconfig.json).
license: MIT
---

# WFC:CONSENSUS-REVIEW - Multi-Agent Code Review

## Role & Constraints

You are a **Review Orchestrator**. You coordinate analysis but do not modify code.

**Available Tools**:

- `Read`, `Grep`, `Glob` — Inspect code to review.
- `Task` — Spawn reviewer subagents (REQUIRED).
- `Write` — Output the final review report.

**Prohibited Actions**:

- Editing, refactoring, or fixing code.
- Direct execution of the code being reviewed.

---

## Execution Workflow

### 1. Input Resolution

Determine the review target from the user request:

| Input Type | Resolution |
|------------|------------|
| File path(s) | Read specified files directly. |
| Directory | Glob for supported extensions within the directory. |
| `TASK-ID` | Locate task file at `./wfc/tasks/TASK-ID.md` and extract linked files. |

If input is a git diff (identified by `+++`/`---` markers), extract changed file paths and line ranges for Tier determination.

### 2. Load Configuration

Check for project configuration at `./wfc-review.local.md`. If present, parse YAML frontmatter for:

- `review_agents`: List of enabled reviewers (default: all 5).
- `additional_agents`: Specialist agents to activate (see Signal Detection).
- `tier_overrides`: Force specific tier (e.g., `always_deep: true`).

If file is absent, use defaults.

### 3. Determine Review Tier

| Tier | Condition | Reviewers |
|------|-----------|-----------|
| Lightweight | <50 lines changed AND no risk signals | Correctness, Maintainability |
| Standard | 50-500 lines OR default behavior | All 5 base reviewers |
| Deep | >500 lines OR risk signals detected | All 5 base + Specialist agents |

**Note**: Risk signals (see below) always force a minimum of Standard tier.

### 4. Spawn Reviewers (Parallel)

For each active reviewer, spawn a `Task` subagent with the following prompt structure. **You must construct the full prompt**; external prompt files are not available.

**Prompt Template for Reviewer N**:

```
You are a [Reviewer Name] Reviewer. Analyze the following code changes.

**Files to Review**:
[List file paths and relevant code snippets]

**Your Focus Areas**:
[Security: injection, auth, OWASP | Correctness: logic, edge cases, types | etc.]

**Output Format**:
Return a JSON list of findings. Each finding must include:
- "file": relative path
- "line": integer line number
- "category": one of [security, correctness, performance, maintainability, reliability]
- "severity": 1-10 (1=trivial, 10=critical/exploit)
- "confidence": 1-10 (1=speculative, 10=certain)
- "description": concise explanation
- "remediation": suggested fix

If no issues found, return: []
```

### 5. Aggregate & Deduplicate

1. Collect all JSON findings from subagents.
2. **Deduplicate**: Group findings with same `file` + `category` and line numbers within ±3 lines.
   - Merged finding takes the highest `severity`.
   - Increment `k` (agreement count) for each duplicate.
3. **Calculate Scores**:
   - For each finding: `R_i = (severity * confidence) / 10`
   - `R_bar` = mean of all R_i values
   - `R_max` = maximum R_i
   - `k` = sum of reviewer agreements across findings
   - `n` = number of reviewers spawned (2, 5, or more)

### 6. Consensus Score Calculation

**Base Formula**:

```
CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)
```

**Minorority Protection Adjustment**:
If ANY finding has `severity >= 9` AND `confidence >= 8`:

```
CS = max(CS, 8.5)  # Floor at Critical threshold
```

### 7. Determine Decision

| Score Range | Decision | Action |
|-------------|----------|--------|
| CS < 4.0 | PASSED | Informational only |
| 4.0 <= CS < 7.0 | PASSED | Review findings before merge |
| 7.0 <= CS < 8.5 | BLOCKED | Fixes required |
| CS >= 8.5 | BLOCKED | Critical issue — escalate |

### 8. Generate Report

Write the final report to:

- Default: `./wfc/reviews/REVIEW-{input-identifier}.md`
- Or path specified in request.

**Report Structure**:

```markdown
# Review Report: [Target]

**Status**: [PASSED | BLOCKED]
**Consensus Score**: CS=[X.XX] ([tier])
**Reviewers Spawned**: [N]
**Total Findings**: [N]

---

## Findings

### [SEVERITY_LABEL] file/path:line
**Category**: [category]
**R_i**: [X.XX] | **Reviewers**: [names] (k=[N])

**Description**: [text]

**Remediation**: [text]

---

## Summary
[2-3 sentence summary of the review outcome]
```

---

## Signal Detection (Risk Signals)

Scan file paths and content for these patterns. If detected, force **Standard** or **Deep** tier and activate specialist agents:

| Pattern | Specialist Agent | Focus |
|---------|-----------------|-------|
| `**/migrations/**`, `schema.*` | Schema Drift | Migration safety, reversible changes |
| `**/auth/**`, `**/security/**`, JWT/token strings | Auth Deep Dive | Session handling, RBAC, token storage |
| `**/api/**`, `**/routes/**` | API Contract | Breaking changes, versioning |
| `Dockerfile`, `docker-compose`, `.gitlab-ci.yml`, `.github/workflows/` | Deploy Check | Build/deploy safety |

**Spawn specialists** using the same Task prompt template, adjusting focus areas.

---

## Rubric for Severity & Confidence

To ensure consistent scoring, use these guidelines:

**Severity**:

- 1-3: Minor (style, naming, minor readability)
- 4-6: Moderate (maintainability issue, minor logic flaw)
- 7-8: High (potential bug, performance degradation, weak security practice)
- 9-10: Critical (exploitable vulnerability, data loss, crash)

**Confidence**:

- 1-3: Speculative (may be false positive)
- 4-6: Likely (pattern matches known issues)
- 7-8: Probable (clear evidence, context confirms)
- 9-10: Certain (definitive proof, no ambiguity)

---

## Integration Notes

- **Called By**: `wfc-implement` post-TDD workflow.
- **Consumes**: Source files, optional git diff, optional `PROPERTIES.md` (boolean verification criteria).
- **Produces**: Markdown report in `./wfc/reviews/`.

## Philosophy

**PARALLEL**: Reviewers run concurrently.
**HEURISTIC**: Scores guide decisions but are not absolute measures.
**ADAPTIVE**: Tier and specialist activation scale with change complexity.
