# wfc-playground

## What It Does

`wfc-playground` generates self-contained interactive HTML files for visual exploration of designs, data, and system concepts. Each output is a single `.html` file with all CSS and JavaScript inlined — no external dependencies, no build step, and no server required. Open it in any browser and start exploring. Three templates cover the main use cases: design exploration (color, typography, spacing), data visualization (JSON trees, tables, filters), and concept mapping (draggable node graphs).

## When to Use It

- When exploring color palettes, typography scales, or spacing systems before committing to a design
- When you want to inspect or navigate a JSON API response interactively
- When mapping relationships between system components, features, or concepts for a planning session
- When prototyping a UI concept quickly without setting up a project or framework
- Not for production UI components — use your project's component library for those

## Usage

```bash
# Design exploration
/wfc-playground "color palette explorer"
/wfc-playground "typography scale playground"
/wfc-playground "spacing system visualizer"

# Data exploration
/wfc-playground "JSON data explorer"
/wfc-playground "API response viewer"
/wfc-playground "query builder"

# Concept exploration
/wfc-playground "system architecture map"
/wfc-playground "feature dependency graph"
/wfc-playground "concept relationship explorer"
```

## Example

```
/wfc-playground "color palette explorer"

Selecting template: design
Customizing for color palette exploration...
Generating playground.html...

✅ Created: color-palette-explorer.html (38KB, no dependencies)

Open in browser:
  open color-palette-explorer.html
```

The generated file contains:

- Left panel: Color pickers and sliders for hue, saturation, lightness
- Right panel: Live preview of the palette applied to sample UI elements
- Bottom panel: Generated CSS custom properties with a copy-to-clipboard button

For a concept map:

```
/wfc-playground "WFC skill dependency graph"

Selecting template: concept-map
Generating wfc-skill-dependency-graph.html...

✅ Created: wfc-skill-dependency-graph.html (52KB)

The graph is interactive:
  - Drag nodes to rearrange
  - Click nodes to highlight connections
  - Scroll to zoom, drag canvas to pan
  - Color-coded by category
```

## Options

The argument describes what you want to explore. `wfc-playground` selects the appropriate template automatically based on keywords in your description:

- Keywords like "color", "typography", "design", "spacing", "visual" → **Design template**
- Keywords like "data", "JSON", "API", "table", "explorer", "query" → **Data Explorer template**
- Keywords like "map", "graph", "architecture", "relationship", "concept", "dependency" → **Concept Map template**

No flags required. The output file is named based on your description.

## Integration

**Produces:** A single self-contained `.html` file, saved in the current directory (or `.development/scratch/` if you prefer to keep it local-only)

**Consumes:** Your natural-language description of the exploration goal; base templates from `wfc/assets/templates/playground/` (`design.html`, `data-explorer.html`, `concept-map.html`)

**Next step:** Use the playground output in planning discussions, design reviews, or as a throwaway prototype. When you're ready to build a production version, use `/wfc-build` or `/wfc-plan` + `/wfc-implement`.
