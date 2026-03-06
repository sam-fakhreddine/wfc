---
description: Generate a visual HTML plan review — current codebase state vs. proposed implementation plan
skill: wfc-visual
---
Generate a comprehensive visual plan review as a self-contained HTML page, comparing the current codebase against a proposed implementation plan.

Follow the wfc-visual skill workflow. Read the reference template, CSS patterns, and mermaid theming references before generating. Use a blueprint/editorial aesthetic with current-state vs. planned-state panels. Consult `./references/design-intelligence.md` for palette and font selection.

**Inputs:**
- Plan file: `$1` (path to a markdown plan, spec, or RFC document)
- Codebase: `$2` if provided, otherwise the current working directory

**Data gathering phase** — read and cross-reference these before generating:

1. **Read the plan file in full.** Extract: problem statement, proposed changes, rejected alternatives, scope boundaries.
2. **Read every file the plan references.** Also read files that import or depend on those files.
3. **Map the blast radius.** Identify imports, tests, config files, public API surface.
4. **Cross-reference plan vs. code.** Verify file/function/type references exist and behavior matches.

**Verification checkpoint** — produce a structured fact sheet before generating HTML. Cite sources for every claim.

**Diagram structure:**
1. **Plan summary** — intuition + scope. *Visual: hero depth, 20-24px type.*
2. **Impact dashboard** — files to modify/create/delete, lines estimated, test coverage, completeness indicator.
3. **Current architecture** — Mermaid diagram of affected subsystem today. Zoom controls.
4. **Planned architecture** — Mermaid diagram after plan. Same node names/layout as current. Highlight new/removed/changed.
5. **Change-by-change breakdown** — side-by-side current vs. planned with rationale. Flag discrepancies.
6. **Dependency & ripple analysis** — callers, importers, downstream effects. Color: green (covered), amber (not mentioned), red (missed).
7. **Risk assessment** — edge cases, assumptions, ordering risks, rollback complexity, cognitive complexity.
8. **Plan review** — Good/Bad/Ugly/Questions with colored cards.
9. **Understanding gaps** — rationale gaps + cognitive complexity flags roll-up.

Include responsive section navigation. Use current-vs-planned visual language: blue for current, green/purple for planned, amber for concerns, red for gaps. Write to `~/.agent/diagrams/` and open in browser.

Ultrathink.

$@
