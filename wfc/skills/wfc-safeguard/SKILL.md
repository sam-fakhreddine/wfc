---
name: wfc-safeguard
description: >-
  Installs a PreToolUse hook into `.claude/settings.json` that intercepts
  Write/Edit/Bash tool calls and blocks or warns on dangerous code patterns
  BEFORE the tool executes. Uses regex-based detection only.

  TRIGGERS: "install the wfc-safeguard hook", "set up code guardrails",
  "block dangerous functions automatically", /wfc-safeguard.

  BLOCKS (prevents tool call): eval(), new Function(), os.system(),
  subprocess shell=True, rm -rf on system/home paths, github.event.*
  expressions in Actions run steps.

  WARNS (allows tool call): innerHTML, dangerouslySetInnerHTML,
  pickle.load(), child_process.exec.

  SCOPE: JS/TS, Python, Bash, GitHub Actions YAML only.

  LIMITATIONS: Cannot distinguish code from comments or strings — will block
  legitimate documentation containing blocked patterns. Regex-based only;
  does not catch obfuscated or indirect patterns.

  PREREQUISITES: Python 3.8+ available as `python3` command. Target file
  `.claude/settings.json` must be writable standard JSON (no comments).
license: MIT
---

# WFC:SAFEGUARD - Write-Time Security Pattern Detection

Intercepts dangerous code patterns before tool calls complete. This is a
lint-level regex detector — it does NOT perform AST analysis and will produce
false positives on comments, strings, and documentation containing blocked
patterns.

## Installation

This skill appends a PreToolUse hook entry to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 wfc/scripts/hooks/safeguard.py"
          }
        ]
      }
    ]
  }
}
```

**Merge behavior**: If `settings.json` exists, the hook is appended to any
existing PreToolUse hooks. Deduplication is NOT performed — running this skill
multiple times will add duplicate entries.

**File requirements**: `.claude/settings.json` must be standard JSON.
JSONC (with comments) is NOT supported and will cause corruption or parse
failures.

## Prerequisites Verification

Before installation, verify:

1. `python3` command exists in PATH
2. `wfc/scripts/hooks/safeguard.py` exists and is executable
3. `.claude/settings.json` is writable (or creatable)

If any prerequisite fails, abort installation and report the specific failure.

## What It Detects

### Blocked Patterns (exit code 2 — tool call prevented)

| Pattern | Languages | Notes |
|---------|-----------|-------|
| `eval(` | JS/TS, Python | Matches any use including in comments/strings |
| `new Function(` | JS/TS | Dynamic code execution |
| `os.system(` | Python | Command execution |
| `subprocess` with `shell=True` | Python | Shell injection vector |
| `rm -rf /`, `rm -rf /*`, `rm -rf ~/` | Bash | System destruction |
| `${{ github.event.* }}` in `run:` blocks | YAML | Actions expression injection |

### Warned Patterns (message to stderr — tool call proceeds)

| Pattern | Languages | Risk |
|---------|-----------|------|
| `.innerHTML` | JS/TS | XSS |
| `dangerouslySetInnerHTML` | React | XSS |
| `pickle.load(` | Python | Deserialization |
| `child_process.exec(` | Node.js | Command injection |

Note: Hardcoded secret detection is NOT included in this version due to high
false-positive rates. Use `wfc-security` for secret scanning.

## Known Limitations

1. **Context blindness**: Will block `# TODO: remove eval()` as if it were code
2. **No AST parsing**: Cannot detect indirect/obfuscated patterns
3. **No deduplication**: Re-running adds duplicate hooks
4. **No uninstall**: Removing hooks requires manual `settings.json` edit
5. **JSON only**: Cannot handle JSONC configuration files

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Hook fails silently | Verify `python3` in PATH; check script exists |
| False positives on docs | Expected behavior — disable hook to write docs |
| Duplicate hooks | Manually edit `settings.json` to remove extras |
| Can't modify settings | Check file permissions; ensure not read-only |
| JSON parse errors | Remove comments from `settings.json` |
