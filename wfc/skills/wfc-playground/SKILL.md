---
name: wfc-playground
description: >
  Generates a single self-contained HTML file (inline CSS + JS, zero external
  dependencies, no build step) for throwaway visual exploration. All HTML is
  synthesized at generation time — no template files are read from disk.

  TRIGGER only when the explicit goal is a browser-openable, single-file,
  static HTML sandbox with no backend, no framework, and no deployment intent.
  Prefer explicit invocation via /wfc-playground.

  TRIGGER phrases (all must carry affirmative construction — negated forms do
  NOT trigger):
    - "create a self-contained HTML playground"
    - "build a throwaway visual explorer"
    - "single-file HTML sandbox"
    - "static HTML prototype"
    - /wfc-playground [topic]

  NOTE: "wfc" is legacy naming. This skill has no Wave Function Collapse
  functionality.
license: MIT
---

# WFC:PLAYGROUND — Static HTML Explorer Generator

## Not for

- Wave Function Collapse generation or any procedural/generative algorithm
- React, Vue, Svelte, Angular, or any framework-based component output
- Production dashboards, deployed UI, or any output shipped to end users
- Embeddable widgets, iframe content, or components integrated into existing pages
- Tools requiring live data connections (databases, APIs, OAuth, network requests)
- Multi-file projects, npm packages, or output requiring a build step or server
- Accessibility-compliant (WCAG) UI — generated output makes no a11y guarantees
- Coding sandboxes or REPL environments (CodePen/JSFiddle-style)
- Mobile-first or responsive layouts
- Any request phrased in the negative ("I do NOT want a playground") or as a
  meta-question about the skill itself

Synthesizes a single self-contained `.html` file for one-off visual exploration.
No files are read from disk. No external dependencies. No backend. No framework.

---

## Execution Steps

### Step 1 — Classify Request into One Pattern

Apply the first matching rule:

| If request mentions… | Use pattern |
|---|---|
| Color, spacing, typography, visual design properties | **Design** |
| JSON, tables, structured data, filtering, search | **Data** |
| Nodes, relationships, graphs, dependencies, concept links | **Concept** |
| None of the above, or ambiguous | **Design** (default — inject HTML comment noting assumption) |

If the request spans multiple patterns, use the pattern with the most matching
signals. Do not ask for clarification. Do not merge patterns. Record the chosen
pattern in an HTML comment at the top of the output file.

If the request implies live backend connectivity (database queries, API calls,
auth tokens), do not generate this skill's output. State: "This request requires
live data connectivity. wfc-playground generates static UI only. Use a
backend-capable skill."

### Step 2 — Apply Fixed Customization Rules

Customization is limited to the following variables. All other structure is fixed.

**All patterns:**

- Page `<title>` and visible heading: derived from user's topic string
- Seed data / default values: use any data provided by user verbatim (inline as
  JS const); if no data provided, use clearly labeled placeholder values
- If user provides a dataset larger than 500 items: truncate to first 100 items
  and inject a visible warning: `<!-- WARNING: input truncated to 100 items -->`

**Design pattern only:**

- Control types: map user's design properties to the nearest available control
  (color → `<input type="color">`, numeric → `<input type="range">`,
  toggle → `<input type="checkbox">`, text → `<input type="text">`)
- Output panel format: CSS custom properties block (`--property-name: value;`)

**Data pattern only:**

- Default view: JSON tree if input is nested; flat table if input is array of
  objects; raw text if neither
- Output panel format: current filtered/visible JSON state

**Concept pattern only:**

- Node positions: distribute evenly in a grid; user may drag to reposition
- Relationship lines: SV
