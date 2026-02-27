---
name: wfc-playground
description: >
  Generates a single, self-contained HTML file with inline CSS and vanilla
  JavaScript (no external dependencies, no CDNs, no build step). Use for
  throwaway visual experiments, algorithm visualization, or CSS explorations
  where all code is synthesized entirely by the LLM.

  TRIGGER: Invoke ONLY when the request explicitly requests a browser-openable,
  single-file, static HTML sandbox with zero external dependencies.

  DO NOT trigger for: requests mentioning React/Vue/Angular, CDN libraries
  (D3, Three.js, Chart.js), or production-ready output.

license: MIT
---

# WFC:PLAYGROUND — Static HTML Explorer Generator

## Not for

- Wave Function Collapse generation or any procedural/generative algorithm
- React, Vue, Svelte, Angular, or any framework-based component output
- Production dashboards, deployed UI, or any output shipped to end users
- Embeddable widgets, iframe content, or components integrated into existing pages
- Tools requiring live server-side connections (databases, APIs, OAuth, backend endpoints)
- CDN-loaded libraries, npm packages, or external JavaScript/CSS imports
- Multi-file projects or output requiring a build step or server
- Accessibility-compliant (WCAG) UI — generated output makes no a11y guarantees
- Coding sandboxes or REPL environments (CodePen/JSFiddle-style)
- Mobile-first or responsive layouts
- Dynamic client-side state viewers (localStorage, IndexedDB, SessionStorage inspectors)
- Self-referential requests to visualize this skill's own definition or code
- Requests with no discernible topic, data, design properties, or conceptual relationships

Synthesizes a single self-contained `.html` file for one-off visual exploration.
No files are read from disk. No external dependencies. No backend. No framework.

---

## Execution Steps

### Step 1 — Classify Request into One Pattern

Apply the first matching rule (evaluate in order):

| If request PRIMARILY involves… | Use pattern |
|---|---|
| Numeric/textual properties affecting appearance (color, spacing, typography, opacity) | **Design** |
| Structured records requiring filter/sort/search (JSON arrays, tables, data grids) | **Data** |
| Entities and their relationships (nodes, edges, graphs, dependencies, hierarchies) | **Concept** |

**Tie-breaking rules:**

1. If multiple patterns have equal signals, prioritize: **Concept > Data > Design**
2. If no pattern matches, return error comment: `<!-- ERROR: No matching pattern. Request must specify design properties, structured data, or entity relationships. -->`
3. Do NOT default to Design for unrelated requests.

**Rejection rule:**
If the request requires server-side execution, OAuth, or real-time network calls, abort and respond:
> "This request requires live backend connectivity. wfc-playground generates static UI only. Use a backend-capable skill."

**Mock data clarification:**
Requests to visualize *example* or *placeholder* data representing API responses ARE permitted. Only reject if the request requires actual network calls at runtime.

Record the chosen pattern in an HTML comment at the top of the output:

```html
<!-- Pattern: [Design|Data|Concept] -->
```

### Step 2 — Apply Pattern-Specific Rules

**All patterns:**

- Page `<title>` and visible `<h1>`: derived from user's topic string
- Seed data: use user-provided data verbatim (inline as JS `const`)
- If no data provided: use clearly labeled placeholder values with comment `// Placeholder data — replace with actual values`
- Dataset size limit: count top-level array elements only. If >500, truncate to 100 and inject:

  ```html
  <!-- WARNING: Input truncated to 100 items (original: N items) -->
  ```

**Design pattern:**

- Control mapping:
  | Property type | Control element |
  |---|---|
  | Color | `<input type="color">` |
  | Numeric range | `<input type="range" min="0" max="100">` |
  | Boolean toggle | `<input type="checkbox">` |
  | Short text | `<input type="text">` |
- If property has no clear mapping (e.g., "whimsy"), create a range input with labeled waypoints
- Output panel: display current CSS custom properties block:

  ```css
  :root { --property-name: value; }
  ```

**Data pattern:**

- View selection:
  | Input structure | Default view |
  |---|---|
  | Nested objects/arrays | Expandable JSON tree |
  | Flat array of objects | Sortable/filterable HTML `<table>` |
  | Neither | Raw `<pre>` text block |
- Output panel: display current filtered/visible data state as JSON

**Concept pattern:**

- Node positions: distribute evenly in a CSS Grid (initial); make nodes draggable via JS
- Relationship lines: SVG `<path>` elements positioned behind nodes, updated on drag
- Node content: display entity name; if entity has properties matching Design or Data types, render them inline (e.g., color swatch for color property)
- Layout: SVG layer (z-index: 0) + HTML node layer (z-index: 1)

### Step 3 — Generate Output File

Produce a single HTML file with this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[User Topic]</title>
  <style>
    /* [Pattern]-specific styles */
    /* All CSS inline here */
  </style>
</head>
<body>
  <h1>[User Topic]</h1>
  <!-- Pattern-specific UI controls -->
  <!-- Output panel -->
  <script>
    // [Pattern]-specific logic
    // Seed data
    // Interaction handlers
  </script>
</body>
</html>
```

**Quality requirements:**

- All code must run when file is opened directly in browser (file:// protocol)
- No `fetch()`, `XMLHttpRequest`, or external network calls
- No `import` statements (ES modules require server)
- All variables must be initialized before use
