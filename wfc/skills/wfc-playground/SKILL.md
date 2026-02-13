---
name: wfc-playground
description: Creates self-contained interactive HTML playgrounds for visual exploration of configurations, designs, and data. Generates single-file HTML with inline CSS/JS and no external dependencies. Use when you want to explore color palettes, test configurations, visualize data, or create interactive concept maps. Triggers on "create playground", "interactive explorer", "visual playground", or explicit /wfc-playground. Ideal for design exploration, data visualization, and interactive prototyping. Not for production UI components.
license: MIT
---

# WFC:PLAYGROUND - Interactive Playground Generator

Creates self-contained interactive HTML playgrounds for visual exploration.

## What It Does

1. **Selects template** based on request type (design, data, concept)
2. **Customizes** for the specific exploration need
3. **Generates** single self-contained .html file
4. **No dependencies** - inline CSS/JS, opens in any browser

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

## Templates

### Design Playground
Interactive controls for visual design exploration:
- Color pickers, sliders, toggles
- Live preview panel
- Generated CSS/config output
- Copy-to-clipboard

### Data Explorer
Interactive data visualization and manipulation:
- JSON tree view
- Filter/search
- Table/chart views
- Export options

### Concept Map
Interactive node-based exploration:
- Draggable nodes
- Relationship lines
- Zoom/pan
- Category coloring

## Output

Single `.html` file with:
- Left panel: Interactive controls
- Right panel: Live preview
- Bottom panel: Generated output with copy button
- No external dependencies (all inline)

## Architecture

```
User Request -> Template Selection -> Customization -> HTML Generation
```

Templates are in `wfc/assets/templates/playground/`:
- `design.html` - Design playground base
- `data-explorer.html` - Data exploration base
- `concept-map.html` - Concept mapping base

## Philosophy

**ELEGANT**: Single file, no dependencies
**PROGRESSIVE**: Template -> Customize -> Generate
