# wfc-safeguard

## What It Does

`wfc-safeguard` installs a PreToolUse hook into your project's `.claude/settings.json` that intercepts every Write, Edit, and Bash tool call in real time. It checks code against 13 built-in security patterns and either blocks dangerous actions outright or warns before proceeding. This prevents common vulnerabilities — injection attacks, hardcoded secrets, XSS vectors — from ever entering the codebase.

## When to Use It

- When starting a new project that will handle user input, secrets, or shell commands
- After cloning a project without existing security guardrails
- Before shipping any feature that touches authentication, file I/O, or external commands
- As a complement to `wfc-review` (prevention before post-hoc detection)

## Usage

```bash
/wfc-safeguard
```

## Example

After invoking `/wfc-safeguard`, the hook is active for all subsequent tool calls in the session:

```python
# Claude writes this to a file:
result = eval(user_input)
```

```
[BLOCKED] eval() injection detected in app/utils.py
Pattern: eval() injection (Python, JavaScript)
Action: eval() executes arbitrary code. Use ast.literal_eval() for safe
        expression evaluation, or parse input explicitly.
Tool call cancelled.
```

For warned patterns (action allowed with notice):

```python
element.innerHTML = userComment
```

```
[WARN] .innerHTML XSS risk in ui/renderer.js
Pattern: innerHTML / dangerouslySetInnerHTML XSS risk
Use textContent or DOMPurify to sanitize before assignment.
```

Warnings are deduplicated per file + pattern for the session — you see each warning once.

## Options

No arguments required. The hook is installed project-wide and activates automatically on every tool call.

**Blocked patterns (action prevented):**

- `eval()` — Python and JavaScript
- `new Function()` — JavaScript code execution
- `os.system()` — Python command injection
- `subprocess` with `shell=True` — Python shell injection
- `rm -rf /` on system paths — destructive Bash
- `rm -rf ~/` on home directory — destructive Bash
- `${{ github.event.* }}` in GitHub Actions YAML — script injection

**Warned patterns (action proceeds with notice):**

- `.innerHTML` / `dangerouslySetInnerHTML` — XSS risk
- `pickle.load()` — deserialization risk
- `child_process.exec` — JavaScript command injection
- Hardcoded secrets (`API_KEY = "..."`, etc.)
- SQL string concatenation
- `pull_request_target` in GitHub Actions

**Custom patterns** can be added as JSON files in `wfc/scripts/hooks/patterns/`.

## Integration

**Produces:** Active PreToolUse hook entry in `.claude/settings.json`

**Consumes:** Every Write, Edit, and Bash tool call made during the session

**Next step:** Use `/wfc-rules` to layer project-specific enforcement on top of the built-in security patterns, or `/wfc-security` for a deep STRIDE threat model audit of existing code.
