---
description: Generate a visual HTML diff review — before/after architecture comparison with code review analysis
skill: wfc-visual
---
Generate a comprehensive visual diff review as a self-contained HTML page.

Follow the wfc-visual skill workflow. Read the reference template, CSS patterns, and mermaid theming references before generating. Use a GitHub-diff-inspired aesthetic with red/green before/after panels, but vary fonts and palette from previous diagrams. Consult `./references/design-intelligence.md` for palette selection.

**Scope detection** — determine what to diff based on `$1`:
- Branch name (e.g. `main`, `develop`): working tree vs that branch
- Commit hash: that specific commit's diff (`git show <hash>`)
- `HEAD`: uncommitted changes only (`git diff` and `git diff --staged`)
- PR number (e.g. `#42`): `gh pr diff 42`
- Range (e.g. `abc123..def456`): diff between two commits
- No argument: default to `main`

**Data gathering phase** — run these first to understand the full scope:
- `git diff --stat <ref>` for file-level overview
- `git diff --name-status <ref> --` for new/modified/deleted files (separate src from tests)
- Line counts: compare key files between `<ref>` and working tree
- New public API surface: grep added lines for exported symbols, public functions, classes, interfaces
- Feature inventory: grep for new actions, keybindings, config fields, event types on both sides
- Read all changed files in full — include surrounding code paths needed to validate behavior
- Check whether `CHANGELOG.md` has an entry for these changes
- Check whether `README.md` or `docs/*.md` need updates
- Reconstruct decision rationale from conversation, progress docs, commit messages

**Verification checkpoint** — before generating HTML, produce a structured fact sheet of every claim you will present:
- Every quantitative figure: line counts, file counts, function counts, test counts
- Every function, type, and module name you will reference
- Every behavior description: what code does, what changed, before vs. after
- For each, cite the source: the git command output or file:line
Verify each claim. If unverifiable, mark as uncertain.

**Diagram structure** — the page should include:
1. **Executive summary** — lead with the *intuition*: why do these changes exist? *Visual: hero depth, 20-24px type, accent-tinted background.*
2. **KPI dashboard** — lines added/removed, files changed, new modules, test counts. Include CHANGELOG/docs housekeeping indicators.
3. **Module architecture** — Mermaid dependency graph with zoom controls (+/-/reset, Ctrl/Cmd+scroll, drag-to-pan).
4. **Major feature comparisons** — side-by-side before/after panels. Overflow prevention: `min-width: 0` on grid/flex children.
5. **Flow diagrams** — Mermaid for new lifecycle/pipeline/interaction patterns. Same zoom controls.
6. **File map** — full tree with color-coded new/modified/deleted. Consider `<details>` collapsed by default.
7. **Test coverage** — before/after test file counts and coverage.
8. **Code review** — Good/Bad/Ugly/Questions analysis with colored left-border cards.
9. **Decision log** — for each design choice: decision, rationale, alternatives, confidence level (green/blue/amber borders).
10. **Re-entry context** — key invariants, non-obvious coupling, gotchas, follow-up work. Consider `<details>` collapsed.

Include responsive section navigation. Use diff-style visual language: red for removed, green for added, yellow for modified, blue for context. Write to `~/.agent/diagrams/` and open in browser.

Ultrathink.

$@
