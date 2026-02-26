---
name: wfc-rules
description: >
  Creates and manages project-specific coding convention rules for the wfc
  rule engine. Rules are .wfc/rules/*.md files with YAML frontmatter,
  evaluated by the wfc PreToolUse hook during Claude tool calls.

  USE when user explicitly asks to: create, add, edit, or disable a wfc rule;
  enforce a non-security coding convention (naming, required imports, file
  structure, comment format, or style-choice bans); or invoke /wfc-rules.
  REQUIRES wfc toolchain installed and PreToolUse hook registered.

  Not for: security controls (eval, innerHTML, hardcoded secrets, injection
  — use wfc-safeguard; prefer wfc-safeguard when ambiguous); linter/formatter
  config (ESLint, Prettier, Ruff); git hooks (pre-commit, husky); CI/CD
  enforcement (GitHub Actions, branch protection); infrastructure rules (IAM,
  firewall); wfc engine internals; projects without wfc installed.
license: MIT
---

# WFC:RULES - Markdown-Based Code Enforcement

Define project-specific coding convention rules as Markdown files. The wfc
PreToolUse hook evaluates these rules automatically when the hook is registered
and active.

**Scope**: This skill creates `.wfc/rules/*.md` files only. It does not
