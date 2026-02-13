---
name: wfc-safeguard
description: Real-time security enforcement via PreToolUse hooks. Detects dangerous patterns (eval, innerHTML, os.system, hardcoded secrets, SQL injection, GitHub Actions injection) as code is written. Installs hooks into project's .claude/settings.json for automatic enforcement. Use when setting up security guardrails for a project. Triggers on "add security hooks", "enable security scanning", "protect against injection", or explicit /wfc-safeguard. Ideal for security-conscious development. Not for deep security audits (use wfc-security instead).
license: MIT
---

# WFC:SAFEGUARD - Real-Time Security Enforcement

Catches dangerous code patterns in real time as they are written, before they reach your codebase.

## What It Does

WFC Safeguard installs a PreToolUse hook that intercepts every Write, Edit, and Bash tool call. It checks the content against a curated set of security patterns and either blocks the action (for critical issues) or warns (for potential risks).

### Pattern Categories

**Blocked (action prevented)**:
- `eval()` injection (Python, JavaScript)
- `new Function()` code execution (JavaScript)
- `os.system()` command injection (Python)
- `subprocess` with `shell=True` (Python)
- `rm -rf /` on system paths (Bash)
- `rm -rf ~/` on home directory (Bash)
- GitHub Actions script injection via `${{ github.event.* }}` (YAML)

**Warned (action allowed with notice)**:
- `.innerHTML` / `dangerouslySetInnerHTML` XSS risk (JavaScript/TypeScript)
- `pickle.load()` deserialization risk (Python)
- `child_process.exec` command injection (JavaScript)
- Hardcoded secrets (`API_KEY = "..."`, etc.)
- SQL string concatenation
- `pull_request_target` in GitHub Actions

## Usage

```bash
# Enable security hooks for current project
/wfc-safeguard

# The hook is installed as a PreToolUse hook in .claude/settings.json
# It runs automatically on every tool invocation
```

### How It Works

1. Claude Code invokes a tool (Write, Edit, Bash)
2. The PreToolUse hook receives the tool name and input as JSON on stdin
3. Security patterns are checked against the content
4. **Block**: Exit code 2 prevents the tool call, reason shown to user
5. **Warn**: Warning printed to stderr, tool call proceeds
6. **Pass**: No output, tool call proceeds normally

### Session-Scoped Deduplication

Warnings are shown once per file + pattern combination per session. If you already saw a warning about `pickle.load` in `data_loader.py`, you will not see it again until a new session.

## Adding Custom Patterns

Add new pattern files to `wfc/scripts/hooks/patterns/` as JSON:

```json
{
  "patterns": [
    {
      "id": "my-pattern-id",
      "pattern": "regex_pattern_here",
      "description": "Human-readable description",
      "action": "block",
      "event": "file",
      "languages": ["python", "javascript"]
    }
  ]
}
```

### Pattern Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier for the pattern |
| `pattern` | Yes | Regular expression to match against content |
| `description` | Yes | Human-readable explanation of the risk |
| `action` | Yes | `block` (prevent) or `warn` (allow with notice) |
| `event` | Yes | `file` (Write/Edit tools) or `bash` (Bash tool) |
| `languages` | No | List of languages this applies to (by file extension) |
| `file_patterns` | No | Glob patterns for file paths (e.g., `.github/workflows/*.yml`) |

### Supported Languages

python, javascript, typescript, go, rust, java

### File Extension Mapping

| Extension | Language |
|-----------|----------|
| `.py` | python |
| `.js`, `.jsx` | javascript |
| `.ts`, `.tsx` | typescript |
| `.go` | go |
| `.rs` | rust |
| `.java` | java |

## Architecture

```
Claude Code Tool Call
        |
        v
pretooluse_hook.py (main dispatcher)
        |
        v
security_hook.py (pattern checker)
        |           |
        v           v
patterns/*.json   hook_state.py (dedup)
```

### Key Files

- `wfc/scripts/hooks/pretooluse_hook.py` - Main entry point
- `wfc/scripts/hooks/security_hook.py` - Pattern matching engine
- `wfc/scripts/hooks/hook_state.py` - Session state for deduplication
- `wfc/scripts/hooks/patterns/security.json` - Core security patterns
- `wfc/scripts/hooks/patterns/github_actions.json` - CI/CD patterns

## Integration with WFC

- **wfc-security**: Deep STRIDE analysis (audit). Safeguard is real-time prevention.
- **wfc-rules**: Custom project rules. Safeguard is built-in security patterns.
- **wfc-review**: Consensus review catches issues post-hoc. Safeguard prevents them.

## Safety Guarantees

- Hook bugs NEVER block the user (all errors caught, exit 0)
- Patterns use compiled, cached regexes for performance
- State files auto-expire after 24 hours
- No external dependencies required
