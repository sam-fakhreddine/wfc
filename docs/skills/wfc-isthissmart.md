# wfc-isthissmart

## What It Does

`wfc-isthissmart` is a quick sanity-check skill for ideas before you commit time to implementation. It gives you a lightweight, opinionated assessment of whether an idea is sound — covering feasibility, complexity, risk, and fit with existing patterns — without running the full 7-dimension analysis that `/wfc-validate` performs. Think of it as a fast gut-check you run before kicking off a plan.

## When to Use It

- You have an idea and want a quick second opinion before writing any code
- You want to know if an approach has obvious flaws or better alternatives
- You are choosing between two implementation strategies and want a structured take
- You want something lighter-weight than `/wfc-validate` — no formal properties, just a sanity check
- You are mid-conversation in wfc-vibe and want to pressure-test a direction before saying "let's build this"

Use `/wfc-validate` instead when you need a formal 7-dimension critique, complexity budget analysis, or TEAMCHARTER values alignment assessment.

## Usage

```bash
/wfc-isthissmart "use Redis for rate limiting"
/wfc-isthissmart "store user sessions in JWT instead of server-side"
/wfc-isthissmart
```

## Example

```bash
/wfc-isthissmart "cache all API responses in Redis with a 5-minute TTL"
```

Output:

```
Idea: Cache all API responses in Redis with a 5-minute TTL

Verdict: CAUTION — refine before building

  Feasibility:    sound — Redis TTL caching is well-understood
  Complexity:     medium — cache invalidation on writes, cold-start behavior
  Risk:           moderate — stale data served to users if writes bypass cache
  Fit:            partial — blanket TTL is a blunt instrument for mixed-read/write endpoints

Issues to address:
  - "All API responses" includes mutation endpoints (POST/PUT/DELETE).
    Caching those responses is almost never correct.
  - 5-minute TTL on user-specific data risks one user seeing another's cached response
    if cache keys don't include auth identity.
  - No invalidation strategy on write means stale reads are guaranteed after mutations.

Simpler alternative:
  Cache read-only endpoints only (GET /products, GET /categories).
  Key on URL + user ID. Invalidate on the relevant write events.

Recommended action: Narrow the scope to read-only, identity-keyed responses,
then run /wfc-validate if the approach still needs formal sign-off.
```

## Options

| Argument | Description |
|----------|-------------|
| `"idea"` | Freeform description of the idea or approach to evaluate |
| (none) | Prompts you to describe the idea interactively |

No flags are required. Pass your idea as a quoted string or describe it conversationally.

## Integration

**Produces:**

- An inline verdict (GOOD / CAUTION / BAD) with brief reasoning across feasibility, complexity, risk, and fit — delivered directly in the conversation, no file written

**Consumes:**

- Your description of the idea or approach being evaluated

**Next step:** If the idea gets a green light, proceed to `/wfc-build` (small, clear scope) or `/wfc-plan` (complex or multi-step). If the check surfaces concerns, refine the idea or run `/wfc-validate` for a deeper analysis.
