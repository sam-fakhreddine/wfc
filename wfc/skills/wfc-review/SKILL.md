---
name: wfc-consensus-review
description: Five-agent consensus code review using fixed expert reviewers (Security, Correctness, Performance, Maintainability, Reliability). Analyzes code via two-phase workflow (prepare tasks, finalize results), deduplicates findings with SHA-256 fingerprinting, and calculates a Consensus Score (CS) with Minority Protection Rule. Use when user requests code review, PR analysis, security assessment, or quality checks. Triggers on "review this code", "check for security issues", "analyze this PR", "is this code good", or explicit /wfc-consensus-review. Ideal for feature implementations, refactoring, API changes, and security-sensitive code. Not for simple typo fixes, documentation-only changes, or trivial updates.
license: MIT
---

# WFC:CONSENSUS-REVIEW - Five-Agent Consensus Code Review

Five fixed reviewers analyze code and a Consensus Score determines the decision.

## What It Does

1. **Security Reviewer** - Injection, auth/authz, OWASP Top 10
2. **Correctness Reviewer** - Logic bugs, edge cases, type safety
3. **Performance Reviewer** - Algorithmic efficiency, N+1 queries, memory
4. **Maintainability Reviewer** - Readability, naming, SOLID/DRY, complexity
5. **Reliability Reviewer** - Error handling, fault tolerance, graceful degradation
6. **Consensus Score (CS)** - Weighted formula with Minority Protection Rule

## Usage

```bash
# Review specific task
/wfc-consensus-review TASK-001

# Review files directly
/wfc-consensus-review path/to/code

# With properties
/wfc-consensus-review TASK-001 --properties PROP-001,PROP-002
```

## Two-Phase Workflow

### Phase 1: Prepare Review

```
orchestrator.prepare_review(request) -> 5 task specs
```

Builds prompts for each reviewer with file list, diff, properties, and knowledge context. Irrelevant reviewers (based on file extensions) are marked for skipping.

### Phase 2: Finalize Review

```
orchestrator.finalize_review(request, responses, output_dir) -> ReviewResult
```

1. Parse subagent responses into findings
2. Deduplicate findings across reviewers (SHA-256 fingerprinting with +/-3 line tolerance)
3. Calculate Consensus Score
4. Generate markdown report

## Consensus Score (CS) Formula

```
CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)
```

Where:

- **R_i** = (severity * confidence) / 10 for each deduplicated finding
- **R_bar** = mean of all R_i values
- **k** = total reviewer agreements (sum of per-finding reviewer counts)
- **n** = 5 (total reviewers)
- **R_max** = max(R_i) across all findings

## Decision Tiers

| Tier | CS Range | Action |
|------|----------|--------|
| Informational | CS < 4.0 | Log only, review passes |
| Moderate | 4.0 <= CS < 7.0 | Inline comment, review passes |
| Important | 7.0 <= CS < 9.0 | Block merge, review fails |
| Critical | CS >= 9.0 | Block + escalate, review fails |

## Minority Protection Rule (MPR)

Prevents a single critical finding from being diluted by many clean reviews:

```
IF R_max >= 8.5 AND k >= 1 AND finding is from security/reliability:
    CS_final = max(CS, 0.7 * R_max + 2.0)
```

## Finding Deduplication

Findings from different reviewers pointing to the same issue are merged:

- **Fingerprint**: SHA-256 of `file:normalized_line:category` (line tolerance +/-3)
- **Merge**: highest severity wins, all descriptions and remediations preserved
- **k tracking**: number of reviewers who flagged the same issue (increases CS)

## Output

### Review Report (REVIEW-TASK-XXX.md)

```markdown
# Review Report: TASK-001

**Status**: PASSED
**Consensus Score**: CS=3.50 (informational)
**Reviewers**: 5
**Findings**: 2

---

## Reviewer Summaries

### PASS: Security Reviewer
**Score**: 10.0/10
**Summary**: No security issues found.
**Findings**: 0

### PASS: Correctness Reviewer
**Score**: 8.5/10
**Summary**: Minor edge case.
**Findings**: 1

...

---

## Findings

### [MODERATE] src/auth.py:45
**Category**: validation
**Severity**: 5.0
**Confidence**: 7.0
**Reviewers**: correctness, reliability (k=2)
**R_i**: 3.50

**Description**: Missing input validation on user_id

**Remediation**:
- Add type check and bounds validation

---

## Summary

CS=3.50 (informational): 2 finding(s), review passed.
```

## Integration with WFC

### Called By

- `wfc-implement` - After agent completes TDD workflow

### Consumes

- Task files (from git worktree)
- PROPERTIES.md (formal properties to verify)
- Git diff content

### Produces

- Review report (REVIEW-{task_id}.md)
- Consensus Score decision (pass/fail with tier)
- Deduplicated findings with reviewer agreement counts

## Conditional Reviewer Activation

Reviewers are activated based on change characteristics, not just file extensions. This saves tokens on small changes and adds depth on risky ones.

### Tier 1: Lightweight Review (S complexity, <50 lines changed)

Only 2 reviewers run:

- **Correctness** (always)
- **Maintainability** (always)

**Triggers:** Single-file changes, typo fixes, small refactors, config changes.

### Tier 2: Standard Review (M complexity, 50-500 lines changed)

All 5 base reviewers run with relevance gating.

### Tier 3: Deep Review (L/XL complexity, >500 lines or risk signals)

All 5 base reviewers + conditional specialist agents:

| Signal Detected | Additional Agent | What It Checks |
|----------------|-----------------|----------------|
| Database migration files | **Schema Drift Detector** | Unrelated schema changes, migration safety |
| Database migration files | **Data Migration Expert** | ID mappings, swapped values, rollback safety |
| Auth/security changes | **Auth Deep Dive** | Token handling, session management, RBAC gaps |
| API endpoint changes | **API Contract Checker** | Breaking changes, versioning, backwards compat |
| Infrastructure/deploy | **Deploy Verification** | Go/No-Go checklist, rollback plan |

### Relevance Gate (File Extensions)

Each reviewer has domain-specific file extensions. Only relevant reviewers execute:

| Reviewer | Relevant Extensions |
|----------|-------------------|
| Security | .py, .js, .ts, .go, .java, .rb, .php, .rs |
| Correctness | .py, .js, .ts, .go, .java, .rb, .rs, .c, .cpp |
| Performance | .py, .js, .ts, .go, .java, .rs, .sql |
| Maintainability | * (always relevant) |
| Reliability | .py, .js, .ts, .go, .java, .rs |

### Signal Detection Rules

```
IF files include **/migrations/** OR **/migrate/** OR schema changes:
    → Activate Schema Drift Detector + Data Migration Expert

IF files include **/auth/** OR **/security/** OR JWT/token/session patterns:
    → Activate Auth Deep Dive

IF files include **/api/** OR **/routes/** OR **/endpoints/**:
    → Activate API Contract Checker

IF files include Dockerfile, docker-compose, k8s, terraform, CI configs:
    → Activate Deploy Verification
```

### Knowledge Search (Always-On)

Regardless of tier, the review always searches `docs/solutions/` for related past issues via wfc-compound's knowledge base. This surfaces known pitfalls before they become findings.

### Per-Project Configuration

Projects can customize which reviewers run via `wfc-review.local.md`:

```yaml
---
review_agents:
  - security
  - correctness
  - performance
  - maintainability
  - reliability
additional_agents:
  - schema-drift-detector
tier_overrides:
  always_deep: true  # Force Tier 3 for all reviews
---

# Optional: Review Context
Focus on Rails conventions and N+1 query detection.
```

## Philosophy

**ELEGANT**: Simple two-phase workflow, deterministic reviewer set
**MULTI-TIER**: Engine (logic) separated from CLI (presentation)
**PARALLEL**: 5 reviewers can run concurrently via Task tool
**TOKEN-AWARE**: Relevance gate skips irrelevant reviewers
