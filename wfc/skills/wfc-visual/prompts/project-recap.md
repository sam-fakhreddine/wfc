---
description: Generate a visual HTML project recap — rebuild mental model of a project's current state, recent decisions, and cognitive debt hotspots
skill: wfc-visual
---
Generate a comprehensive visual project recap as a self-contained HTML page.

Follow the wfc-visual skill workflow. Read the reference template, CSS patterns, and mermaid theming references before generating. Use a warm editorial or paper/ink aesthetic. Consult `./references/design-intelligence.md` for palette and font selection.

**Time window** — determine the recency window from `$1`:
- Shorthand like `2w`, `30d`, `3m`: parse to git's `--since` format
- No argument: default to `2w` (2 weeks)

**Data gathering phase:**
1. **Project identity.** Read README.md, CHANGELOG.md, package.json / pyproject.toml for name, version, dependencies.
2. **Recent activity.** `git log --oneline --since=<window>`, `git log --stat --since=<window>`, `git shortlog -sn --since=<window>`.
3. **Current state.** `git status`, stale branches, TODO/FIXME comments, progress docs.
4. **Decision context.** Commit messages, conversation history, plan docs, ADRs.
5. **Architecture scan.** Key source files, entry points, public API, frequently changed files.

**Verification checkpoint** — produce a structured fact sheet before generating HTML. Cite sources for every claim.

**Diagram structure:**
1. **Project identity** — current-state summary, version, elevator pitch.
2. **Architecture snapshot** — Mermaid diagram of system as-is. Zoom controls. *Visual: hero depth.*
3. **Recent activity** — human-readable narrative grouped by theme, timeline visualization.
4. **Decision log** — key design decisions from the time window with rationale.
5. **State of things** — KPI cards: working/in-progress/broken/blocked counts.
6. **Mental model essentials** — key invariants, non-obvious coupling, gotchas, naming conventions.
7. **Cognitive debt hotspots** — amber-tinted cards with severity indicators for areas with weak understanding.
8. **Next steps** — inferred from activity, TODOs, momentum direction.

Include responsive section navigation. Use warm visual language: muted blues/greens for architecture, amber for cognitive debt, green/blue/amber/red for state-of-things. Write to `~/.agent/diagrams/` and open in browser.

Ultrathink.

$@
