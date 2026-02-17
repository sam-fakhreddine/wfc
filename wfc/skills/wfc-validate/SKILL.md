---
name: wfc-validate
description: Critical thinking advisor that analyzes plans, ideas, and technical approaches across 7 dimensions (feasibility, complexity, risk, value, alternatives, assumptions, trade-offs). Provides discerning but constructive feedback to ensure smart decisions before committing time and resources. Use when evaluating new features, architectural decisions, or technical approaches. Triggers on "is this a good idea", "should I do this", "analyze this approach", "what do you think of this plan", or explicit /wfc-validate. Ideal for architectural decisions, feature planning, and technology choices. Not for implementation details or code review.
license: MIT
---

# WFC:VALIDATE - Thoughtful Advisor

The experienced staff engineer who asks "is this the right approach?" before we commit.

## What It Does

Analyzes any WFC artifact (plan, architecture, idea) across 7 dimensions:

1. **Do We Even Need This?** - Real problem vs hypothetical
2. **Is This the Simplest Approach?** - Avoid over-engineering
3. **Is the Scope Right?** - Not too much, not too little
4. **What Are We Trading Off?** - Opportunity cost, maintenance burden
5. **Have We Seen This Fail Before?** - Anti-patterns, known failure modes
6. **What's the Blast Radius?** - Risk assessment, rollback plan
7. **Is the Timeline Realistic?** - Hidden dependencies, prototype first?

Returns balanced assessment with verdict: PROCEED, PROCEED WITH ADJUSTMENTS, RECONSIDER, or DON'T PROCEED.

## Usage

```bash
# Analyze current plan
/wfc-validate

# Analyze a freeform idea
/wfc-validate "rewrite auth system in Rust"

# Analyze specific artifact
/wfc-validate --plan
/wfc-validate --architecture
/wfc-validate --task TASK-005
```

## Output: VALIDATE.md

```markdown
# Validation Analysis

## Subject: Rewrite auth system in Rust
## Verdict: 🟡 PROCEED WITH ADJUSTMENTS
## Overall Score: 7.5/10

---

## Executive Summary

Overall, this approach shows 12 clear strengths and 8 areas for consideration.

The strongest aspects are: Blast Radius, Need, Simplicity.

Key considerations: Opportunity cost of other features, Integration risks, Consider using existing library.

With an overall score of 7.5/10, this is a solid approach that can move forward with attention to the identified concerns.

---

## Dimension Analysis

### Do We Even Need This? — Score: 8/10

**Strengths:**
- Addresses clear user need
- Backed by data/metrics

**Concerns:**
- Consider if existing solution could be improved instead

**Recommendation:** Need is justified, but validate assumptions

[... 6 more dimensions ...]

---

## Simpler Alternatives

- Start with a simpler MVP and iterate based on feedback
- Consider using existing solution (e.g., off-the-shelf library)
- Phase the implementation - deliver core value first

---

## Final Recommendation

Proceed, but address these key concerns first: Opportunity cost of other features; Integration risks may extend timeline; Consider using existing library
```

## Tone

**Discerning but constructive. Honest but not harsh.**

Not a naysayer - wants us to succeed with the best approach. Highlights both strengths and concerns. Suggests simpler alternatives when appropriate.

## Verdict Logic

- **🟢 PROCEED**: Overall score >= 8.5/10, no critical concerns
- **🟡 PROCEED WITH ADJUSTMENTS**: Score 7.0-8.4, address concerns first
- **🟠 RECONSIDER**: Score 5.0-6.9, explore alternatives
- **🔴 DON'T PROCEED**: Score < 5.0 or any dimension <= 4/10

## Integration with WFC

### Can Analyze
- `wfc-plan` outputs (TASKS.md, PROPERTIES.md)
- `wfc-architecture` outputs (ARCHITECTURE.md)
- `wfc-security` outputs (THREAT-MODEL.md)
- Freeform ideas (text input)

### Produces
- VALIDATE.md report
- Simpler alternatives
- Final recommendation

## Philosophy

**ELEGANT**: Simple 7-dimension framework, clear logic
**MULTI-TIER**: Analysis (logic) separated from presentation
**PARALLEL**: Can analyze multiple artifacts concurrently
