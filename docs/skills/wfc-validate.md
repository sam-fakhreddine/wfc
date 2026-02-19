# wfc-validate

## What It Does

Acts as an experienced staff engineer who asks "is this the right approach?" before you commit time and resources. It analyzes any plan, idea, or WFC artifact across 7 dimensions — need, simplicity, scope, trade-offs, known failure modes, blast radius, and timeline realism — and returns a scored report with a clear verdict. The goal is discerning but constructive feedback that surfaces risks and simpler alternatives without blocking good work.

## When to Use It

- Before starting implementation on a new plan or architecture decision
- After `/wfc-ba` to confirm the requirements document is solid enough to plan from
- When evaluating a proposed technology choice or approach
- When a task feels larger or riskier than expected and you want a second opinion
- As the second step in the full BA pipeline: `wfc-ba → wfc-validate → wfc-plan`

## Usage

```bash
/wfc-validate [subject] [options]
```

## Example

```bash
/wfc-validate "rewrite auth system in Rust"
```

Output excerpt from VALIDATE.md:

```markdown
# Validation Analysis

## Subject: Rewrite auth system in Rust
## Verdict: PROCEED WITH ADJUSTMENTS
## Overall Score: 7.5/10

---

## Dimension Analysis

### Do We Even Need This? — Score: 8/10
Strengths: Addresses documented latency issue; backed by profiler data
Concerns: Existing Go implementation could be optimized first
Recommendation: Need is justified, but validate assumptions with a benchmark

### Is This the Simplest Approach? — Score: 5/10
Concerns: Full rewrite introduces risk; incremental migration is available
Recommendation: Consider rewriting the hot path only (< 200 lines)

---

## Simpler Alternatives
- Benchmark Go auth with pprof before committing to a rewrite
- Rewrite only the token-verification path, not the full service

## Final Recommendation
Proceed after: running Go profiler, scoping to token-verification only,
and confirming rollback plan.
```

## Options

| Flag / Argument | Description |
|-----------------|-------------|
| (none) | Validates the current TASKS.md or most recent plan in context |
| `"idea"` | Freeform text to analyze (no artifact needed) |
| `--plan` | Explicitly target the current TASKS.md |
| `--architecture` | Explicitly target the current ARCHITECTURE.md |
| `--task TASK-NNN` | Validate a specific task within the plan |

## Integration

**Produces:**

- `VALIDATE.md` — 7-dimension analysis with per-dimension scores, simpler alternatives, and final verdict

**Verdict thresholds:**

- `PROCEED` — Overall score >= 8.5, no critical concerns
- `PROCEED WITH ADJUSTMENTS` — Score 7.0-8.4, address listed concerns first
- `RECONSIDER` — Score 5.0-6.9, explore alternatives before proceeding
- `DON'T PROCEED` — Score < 5.0 or any single dimension <= 4/10

**Consumes:**

- `TASKS.md` or `ARCHITECTURE.md` (when validating WFC artifacts)
- Freeform text (when validating ideas)
- `THREAT-MODEL.md` from `/wfc-security` (when validating security-sensitive plans)

**Next step:** Address any Must-Do revisions from the verdict, then proceed to `/wfc-plan` to generate implementation tasks.
