---
name: wfc-rules
description: >-
  Creates and edits markdown-based coding convention files (`.wfc/rules/*.md`)
  for the wfc PreToolUse hook system.

  Use this skill to CREATE or EDIT rule files that guide code generation style
  and patterns. Rules are plain markdown documents intended for LLM evaluation
  during tool calls (if wfc hook is registered and active).

  DISTINCT FROM:
  - Linters (ESLint, Ruff, Pylint): use those for syntax/AST-based enforcement
  - Formatters (Prettier, Black): use those for whitespace/formatting
  - Security shields (wfc-safeguard): use that for blocking dangerous code

  TRIGGERS: "create/edit a wfc rule file", "add convention to .wfc/rules/",
  "/wfc-rules"

  PREREQUISITE: Requires `.wfc/` directory and active PreToolUse hook. Rules
  created without these will be inert (no enforcement occurs).

  SCOPE: This skill ONLY writes to `.wfc/rules/*.md`. It does not modify
  `.wfc/config.*`, `.wfc/engine/`, or any files outside the rules directory.

license: MIT
---

# WFC:RULES - Markdown Convention Files

Creates and edits project-specific coding convention rules as markdown files in
`.wfc/rules/*.md`.

## What This Skill Does

- Creates new rule files at `.wfc/rules/<name>.md`
- Edits existing rule files
- Lists or describes current rules

## What This Skill Does NOT Do

- Install or configure the wfc toolchain
- Verify that rules will be evaluated (requires active PreToolUse hook)
- Enforce rules directly (rules are passive markdown files)
- Delete, move, or archive rule files
- Modify any files outside `.wfc/rules/`

## Before Creating Rules

1. Check that `.wfc/` directory exists in project root
2. If missing, warn user: "No .wfc/ directory found. Rules will be created but
   not evaluated unless wfc toolchain is installed."
3. If present, proceed with rule creation

## Rule File Format

Rule files are plain markdown. Structure for clarity:

```markdown
# Rule: [Short Name]

## Description
[What this rule enforces and why]

## Enforcement
[Specific guidance for the evaluating agent]

## Examples

### Correct
[Code example following the rule]

### Incorrect
[Code example violating the rule]
```

## Exclusions (Not For)

This skill is NOT for:

- **Security blocking**: preventing eval(), exec(), SQL injection, XSS — use
  `wfc-safeguard`
- **Linter configuration**: ESLint, Ruff, Pylint rules — edit their config files
- **Formatter configuration**: Prettier, Black, prettier — edit their config files
- **Git hooks**: pre-commit, husky — use git configuration
- **CI/CD rules**: branch protection, pipeline gates — use CI/CD configuration
- **Engine modification**: `.wfc/engine/`, `.wfc/config.*` — not supported
- **Projects without wfc**: rules will be inert without toolchain

## Routing Guidance

| Request Type | Use |
|--------------|-----|
| "Enforce named exports" | This skill |
| "Ban console.log" | This skill |
| "Prevent eval()" | wfc-safeguard |
| "Configure semicolons" | ESLint config |
| "Format with 2 spaces" | Prettier config |
| "Block direct main push" | Git/CI config |
