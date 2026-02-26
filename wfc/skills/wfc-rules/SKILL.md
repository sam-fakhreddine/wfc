---
name: wfc-rules
description: >-
  Creates and manages project-specific coding convention rules (.wfc/rules/*.md)
  evaluated by the wfc PreToolUse hook during Claude tool calls.

  TRIGGERS: "create/add/edit/disable a wfc rule", "enforce a coding convention",
  "/wfc-rules". Requires wfc toolchain installed with PreToolUse hook registered.

  NOT FOR: security vulnerability controls — use wfc-safeguard (prefer
  wfc-safeguard when ambiguous); external linter/formatter config (ESLint,
  Ruff, Pylint); git lifecycle hooks (pre-commit, husky); CI/CD or branch
  protection rules; IAM/firewall/database access control; modifying wfc engine
  internals; projects without the wfc PreToolUse hook active.
license: MIT
---

# WFC:RULES - Markdown-Based Code Enforcement

Define project-specific coding convention rules as Markdown files. The wfc
PreToolUse hook evaluates these rules automatically when the hook is registered
and active.

**Scope**: This skill creates `.wfc/rules/*.md` files only. It does not
