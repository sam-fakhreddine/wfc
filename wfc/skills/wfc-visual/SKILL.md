---
name: wfc-visual
description: Generate beautiful, self-contained HTML pages that visually explain systems, code changes, plans, and data. Combines visual-explainer's visualization engine (Mermaid.js, Chart.js, anime.js) with design system intelligence (96 palettes, 57 font pairings, 100 reasoning rules). Use when the user asks for a diagram, architecture overview, diff review, plan review, project recap, comparison table, or any visual explanation of technical concepts. Also use proactively when about to render a complex ASCII table (4+ rows or 3+ columns).
license: MIT
---

# WFC:VISUAL - Design-Intelligent Visual Explainer

Generate self-contained HTML files for technical diagrams, visualizations, and data tables. Always open the result in the browser. Never fall back to ASCII art when this skill is loaded.

**Proactive table rendering.** When you're about to present tabular data as an ASCII box-drawing table in the terminal (comparisons, audits, feature matrices, status reports, any structured rows/columns), generate an HTML page instead. The threshold: if the table has 4+ rows or 3+ columns, it belongs in the browser. Don't wait for the user to ask — render it as HTML automatically and tell them the file path. You can still include a brief text summary in the chat, but the table itself should be the HTML page.

## Commands

| Command | Purpose |
|---------|---------|
| `/wfc-visual` | Create an HTML diagram for any topic on demand |
| `/wfc-diff-review` | Visual code review with before/after panels, architecture diagrams, KPI dashboards |
| `/wfc-plan-review` | Compare implementation plan against actual codebase |
| `/wfc-project-recap` | Cognitive snapshot for context-switching between projects |
| `/wfc-fact-check` | Validate documentation claims against source code |

## Workflow

### 1. Think (5 seconds, not 5 minutes)

Before writing HTML, commit to a direction. Don't default to "dark theme with blue accents" every time.

**Who is looking?** A developer understanding a system? A PM seeing the big picture? A team reviewing a proposal? This shapes information density and visual complexity.

**What type of diagram?** Architecture, flowchart, sequence, data flow, schema/ER, state machine, mind map, data table, timeline, or dashboard. Each has distinct layout needs and rendering approaches (see Diagram Types below).

**What aesthetic?** Pick one and commit:
- Monochrome terminal (green/amber on black, monospace everything)
- Editorial (serif headlines, generous whitespace, muted palette)
- Blueprint (technical drawing feel, grid lines, precise)
- Neon dashboard (saturated accents on deep dark, glowing edges)
- Paper/ink (warm cream background, hand-drawn feel, sketchy borders)
- Hand-drawn / sketch (Mermaid `handDrawn` mode, wiggly lines, informal whiteboard feel)
- IDE-inspired (borrow a real color scheme: Dracula, Nord, Catppuccin, Solarized, Gruvbox, One Dark)
- Data-dense (small type, tight spacing, maximum information)
- Gradient mesh (bold gradients, glassmorphism, modern SaaS feel)

Vary the choice each time. If the last diagram was dark and technical, make the next one light and editorial. The swap test: if you replaced your styling with a generic dark theme and nobody would notice the difference, you haven't designed anything.

**Design System Intelligence.** For industry-specific or branded pages, consult `./references/design-intelligence.md` to select palettes, font pairings, and styles matched to the content domain. The reasoning rules help pick the right aesthetic for the context (healthcare gets calming cyans, fintech gets trust navy + gold, etc.).

### 2. Structure

**Read the reference template** before generating. Don't memorize it — read it each time to absorb the patterns.
- For text-heavy architecture overviews (card content matters more than topology): read `./templates/architecture.html`
- For flowcharts, sequence diagrams, ER, state machines, mind maps: read `./templates/mermaid-flowchart.html`
- For data tables, comparisons, audits, feature matrices: read `./templates/data-table.html`

**For CSS/layout patterns and SVG connectors**, read `./references/css-patterns.md`.

**For pages with 4+ sections** (reviews, recaps, dashboards), also read `./references/responsive-nav.md` for section navigation with sticky sidebar TOC on desktop and horizontal scrollable bar on mobile.

**For design system intelligence** (industry palettes, font pairings, reasoning rules), read `./references/design-intelligence.md`.

**Choosing a rendering approach:**

| Diagram type | Approach | Why |
|---|---|---|
| Architecture (text-heavy) | CSS Grid cards + flow arrows | Rich card content (descriptions, code, tool lists) needs CSS control |
| Architecture (topology-focused) | **Mermaid** | Visible connections between components need automatic edge routing |
| Flowchart / pipeline | **Mermaid** | Automatic node positioning and edge routing; hand-drawn mode available |
| Sequence diagram | **Mermaid** | Lifelines, messages, and activation boxes need automatic layout |
| Data flow | **Mermaid** with edge labels | Connections and data descriptions need automatic edge routing |
| ER / schema diagram | **Mermaid** | Relationship lines between many entities need auto-routing |
| State machine | **Mermaid** | State transitions with labeled edges need automatic layout |
| Mind map | **Mermaid** | Hierarchical branching needs automatic positioning |
| Data table | HTML `<table>` | Semantic markup, accessibility, copy-paste behavior |
| Timeline | CSS (central line + cards) | Simple linear layout doesn't need a layout engine |
| Dashboard | CSS Grid + Chart.js | Card grid with embedded charts |

**Mermaid theming:** Always use `theme: 'base'` with custom `themeVariables` so colors match your page palette. Use `look: 'handDrawn'` for sketch aesthetic or `look: 'classic'` for clean lines. Use `layout: 'elk'` for complex graphs. Override Mermaid's SVG classes with CSS for pixel-perfect control. See `./references/libraries.md` for full theming guide.

**Mermaid zoom controls:** Always add zoom controls (+/-/reset buttons) to every `.mermaid-wrap` container. Complex diagrams render at small sizes and need zoom to be readable. Include Ctrl/Cmd+scroll zoom on the container. See the zoom controls pattern in `./references/css-patterns.md` and the reference template at `./templates/mermaid-flowchart.html`.

**AI-generated illustrations (optional).** If [surf-cli](https://github.com/nicobailon/surf-cli) is available, you can generate images via Gemini and embed them in the page. Check availability with `which surf`. If available:

```bash
surf gemini "descriptive prompt" --generate-image /tmp/ve-img.png --aspect-ratio 16:9
IMG=$(base64 -w 0 /tmp/ve-img.png)
# <img src="data:image/png;base64,${IMG}" alt="descriptive alt text">
rm /tmp/ve-img.png
```

### 3. Style

Apply these principles to every diagram:

**Typography is the diagram.** Pick a distinctive font pairing from `./references/design-intelligence.md` or Google Fonts. Never use Inter, Roboto, Arial, or system-ui as the primary font. Load via `<link>` in `<head>`. Include a system font fallback.

**Color tells a story.** Use CSS custom properties for the full palette. Define at minimum: `--bg`, `--surface`, `--border`, `--text`, `--text-dim`, and 3-5 accent colors. Each accent should have a full and a dim variant. Support both themes with `prefers-color-scheme`.

**Industry-aware palettes.** When the content has a clear domain (healthcare, fintech, gaming, etc.), use the matching palette from `./references/design-intelligence.md` instead of picking colors arbitrarily. The 96 industry palettes are specifically tuned for their contexts.

**Surfaces whisper, they don't shout.** Build depth through subtle lightness shifts (2-4% between levels), not dramatic color changes. Borders should be low-opacity rgba — visible when you look, invisible when you don't.

**Backgrounds create atmosphere.** Don't use flat solid colors. Subtle gradients, faint grid patterns via CSS, or gentle radial glows behind focal areas. The background should feel like a space, not a void.

**Visual weight signals importance.** Not every section deserves equal visual treatment. Executive summaries and key metrics should dominate the viewport on load. Reference sections should be compact and stay out of the way. Use `<details>/<summary>` for sections that are useful but not primary.

**Animation earns its place.** Staggered fade-ins on page load guide the eye. Mix animation types by role: `fadeUp` for cards, `fadeScale` for KPIs, `drawIn` for SVG connectors, `countUp` for hero numbers. Always respect `prefers-reduced-motion`. See `./references/css-patterns.md` for all animation patterns.

### 4. Deliver

**Output location:** Write to `~/.agent/diagrams/`. Use a descriptive filename based on content. The directory persists across sessions.

**Open in browser:**
- macOS: `open ~/.agent/diagrams/filename.html`
- Linux: `xdg-open ~/.agent/diagrams/filename.html`

**Tell the user** the file path so they can re-open or share it.

## Diagram Types

### Architecture / System Diagrams
Two approaches depending on what matters more:

**Text-heavy overviews** (card content matters more than connections): CSS Grid with explicit row/column placement. Sections as rounded cards with colored borders and monospace labels. The reference template at `./templates/architecture.html` demonstrates this pattern.

**Topology-focused diagrams** (connections matter more than card content): **Use Mermaid.** A `graph TD` or `graph LR` with custom `themeVariables` produces proper diagrams with automatic edge routing.

### Flowcharts / Pipelines
**Use Mermaid.** Automatic node positioning and edge routing. Use `graph TD` for top-down or `graph LR` for left-right. Use `look: 'handDrawn'` for sketch aesthetic.

### Sequence Diagrams
**Use Mermaid.** Lifelines, messages, activation boxes, notes, and loops all need automatic layout.

### Data Flow Diagrams
**Use Mermaid.** Use `graph LR` or `graph TD` with edge labels for data descriptions.

### Schema / ER Diagrams
**Use Mermaid.** Use `erDiagram` syntax with entity attributes.

### State Machines / Decision Trees
**Use Mermaid.** Use `stateDiagram-v2` for states with labeled transitions.

**`stateDiagram-v2` label caveat:** Transition labels have a strict parser. If your labels need colons, parentheses, `<br/>`, or special characters, use `flowchart LR` instead with rounded nodes and quoted edge labels.

### Mind Maps
**Use Mermaid.** Use `mindmap` syntax for hierarchical branching.

### Data Tables / Comparisons / Audits
Use a real `<table>` element. The reference template at `./templates/data-table.html` demonstrates all patterns. Use proactively for any structured rows/columns.

### Timeline / Roadmap Views
Vertical or horizontal timeline with a central line (CSS pseudo-element).

### Dashboard / Metrics Overview
Card grid layout with hero numbers, sparklines, progress bars, and Chart.js for real charts.

## File Structure

Every diagram is a single self-contained `.html` file. No external assets except CDN links (fonts, optional libraries).

## Quality Checks

Before delivering, verify:
- **The squint test**: Blur your eyes. Can you still perceive hierarchy?
- **The swap test**: Would replacing your fonts and colors with a generic dark theme make this indistinguishable from a template? If yes, push the aesthetic further.
- **Both themes**: Toggle between light and dark mode. Both should look intentional.
- **Information completeness**: Does the diagram actually convey what the user asked for?
- **No overflow**: Resize the browser to different widths. No content should clip or escape.
- **Mermaid zoom controls**: Every `.mermaid-wrap` must have zoom controls.
- **File opens cleanly**: No console errors, no broken font loads, no layout shifts.

## UX Guidelines (from Design System)

Apply these to all generated HTML:
- Minimum 4.5:1 color contrast ratio for text
- Touch targets minimum 44x44px
- Animation duration 150-300ms for micro-interactions
- Use `transform`/`opacity` for animations, not `width`/`height`
- Minimum 16px body text
- Line height 1.5-1.75 for body text
- Respect `prefers-reduced-motion`
- Use SVG icons, never emoji as UI icons
- Semantic HTML with ARIA labels where needed
