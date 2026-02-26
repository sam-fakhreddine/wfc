---
name: wfc-safeguard
description: >
  Installs a write-time security pattern detector by modifying
  .claude/settings.json (DESTRUCTIVE — confirm intent before invoking).
  Registers a PreToolUse hook intercepting Write, Edit, and Bash calls,
  checking content against regex patterns for dangerous constructs.

  INVOKE when user explicitly wants to: install security hooks in
  .claude/settings.json; block dangerous code patterns at write time;
  register a PreToolUse hook for security linting; run /wfc-safeguard.

  PATTERN COVERAGE (JS/TS, Python, SQL, GitHub Actions YAML only):
  Blocks: eval(), new Function(), os.system(), subprocess shell=True,
  rm -rf on system/home paths, ${{ github.event.* }} in Actions run steps.
  Warns: .innerHTML, dangerouslySetInnerHTML, pickle.load(),
  child_process.exec, hardcoded secrets, raw SQL concatenation.

  Not for: auditing existing code (use wfc-security); security explanations;
  one-off file checks; GitHub Actions CI/CD setup; Go, Rust, Java, C/C++,
  Ruby, or PHP projects; removing or verifying existing hooks.

license: MIT
---

# WFC:SAFEGUARD - Write-Time Security Pattern Detection

Detects common dangerous code patterns as they are written, before the tool call completes.
This is lint-level detection via regex — it does not catch obfuscated, indirect, or runtime-evaluated patterns.

## Prerequisites

- Python 3.8+ available in PATH
- Write access to `.claude/settings.json` in the project root
- WFC hook scripts present at `wfc/scripts/hooks/` (see Key Files below)

**This skill modifies `.claude/settings.json`.** If the file already exists, the hook entry is merged idempotently — existing configuration is preserved. Running `/wfc-safeguard` twice does not install the hook twice.

## What It Detects

**Blocked (tool call prevented — exit code 2)**:

- `eval()` calls — Python and JavaScript (matches any use of `eval(`; does not distinguish argument type)
- `new Function()` — JavaScript dynamic code execution
- `os.system()` — Python command execution
- `subprocess` with `shell=True` — Python
- `rm -rf /`, `rm -rf /*`, `rm -rf ~/` — Bash destructive deletion on system/home paths
- `${{ github.event.* }}` in `run:` steps — GitHub Actions expression injection (YAML only, scoped to run steps)

**Warned (tool call proceeds — message to stderr)**:

- `.innerHTML` / `dangerouslySetInnerHTML` — JavaScript/TypeScript XSS risk
- `pickle.load()` — Python deserialization risk
- `child_process.exec` — JavaScript command injection risk
- Hardcoded string-literal secrets (`API_KEY = "..."
