---
name: wfc-safeclaude
description: Project-specific command allowlist generator that creates safe, curated approval settings for Claude Code. Scans project to identify commonly-used commands (git, npm, pytest, etc.), categorizes by risk level, and generates optimized settings.json configuration. Eliminates constant approval prompts without enabling dangerous YOLO mode. Use when setting up new projects or reducing approval friction. Triggers on "reduce approval prompts", "generate safe commands", "create allowlist", or explicit /wfc-safeclaude. Ideal for project onboarding and developer experience. Not for bypassing security controls.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--show or --strict or --add "command"]
---

# WFC:SAFECLAUDE - Safe Command Allowlist Generator

Eliminates repetitive approval prompts without compromising safety.

## The Problem

Every new Claude Code session in a new project means approving `ls`, `cat`, `grep`, `git status`, `npm test` one by one. It's friction that adds zero safety value. But YOLO mode removes ALL guardrails.

**safeclaude** finds the middle ground: project-specific allowlists.

## What It Does

1. **Scans** project (language, frameworks, toolchain, structure)
2. **Proposes** categorized allowlist (universal, git, language-specific, build/CI)
3. **User reviews** and approves/modifies categories
4. **Generates** `.claude/settings.local.json`

## Usage

```bash
# Scan and generate allowlist
/wfc-safeclaude

# Show current allowlist
/wfc-safeclaude --show

# Strict mode (read-only only)
/wfc-safeclaude --strict

# Add specific command
/wfc-safeclaude --add "docker compose up"

# Remove command
/wfc-safeclaude --remove "rm -rf"

# Reset and regenerate
/wfc-safeclaude --reset
```

## Detection

| Signal | Allows |
|--------|--------|
| `package.json` | npm, node, npx |
| `package-lock.json` | npm (not yarn/pnpm) |
| `pyproject.toml` | python, pip, pytest |
| `Cargo.toml` | cargo, rustc, rustfmt |
| `go.mod` | go, go test, go build |
| `Dockerfile` | docker (read/inspect only) |
| `.github/workflows/` | gh CLI |
| `jest.config.*` | npm test with jest |

## Categories

### Universal (always safe)
```
ls, cat, grep, find, wc, diff, pwd, env, stat, which
```

### Git Read (always safe)
```
git status, git log, git diff, git show, git branch
```

### Git Write (approved per project)
```
git add, git commit, git push, git pull, git checkout
```

### Language-Specific (detected)
```
npm install, npm test, python, pytest, cargo build, go test
```

### Build/CI (detected)
```
npm run build, docker ps, docker logs, gh
```

### File Patterns
- **Source dirs**: `src/**`, `lib/**` (read/write)
- **Config dirs**: `.github/**` (read-only)
- **Generated**: `node_modules/**`, `dist/**` (read-only)
- **Never write**: `.env`, `.env.*`

## Strict Mode

```bash
/wfc-safeclaude --strict
```

Generates **read-only** allowlist:
- Universal safe commands ✅
- Git read commands ✅
- Language read commands ✅
- NO git write ❌
- NO build/CI ❌
- NO file write patterns ❌

Use for: production environments, shared codebases, auditing.

## Output

**`.claude/settings.local.json`**:
```json
{
  "allowedCommands": [
    "ls", "cat", "grep", "git status", "npm test"
  ],
  "filePatterns": {
    "allowed": ["src/**", "tests/**"],
    "readonly": [".github/**", ".env"]
  },
  "generated_by": "wfc-safeclaude",
  "version": "1.0.0"
}
```

## Safety Guarantees

**Never proposed**:
- Destructive commands (`rm -rf`, `git reset --hard`)
- Secret writes (`.env` always read-only)
- Generated dir writes (`node_modules`, `dist`)
- Force operations (`git push --force`)

**Always read-only**:
- Environment files
- Config directories
- Generated/build artifacts

## Example Session

```
User: /wfc-safeclaude

🔍 Scanning project...
✅ Detected: Node.js + TypeScript + Jest + Docker + GitHub Actions

📋 Proposed Allowlist:

Universal (38 commands)
  ✅ ls, cat, grep, find, git status, ...

Git Write (7 commands)
  ⚠️  git add, git commit, git push, ...

Language (5 commands)
  ✅ npm install, npm test, npm run, node, npx

Build/CI (4 commands)
  ✅ npm run build, docker ps, docker logs, gh

File Patterns
  ✅ src/**, tests/** (read/write)
  🔒 .github/**, .env (read-only)
  🔒 node_modules/**, dist/** (read-only)

Approve? (y/n/modify): y

✅ Generated .claude/settings.local.json
✅ 54 commands approved
✅ No more approval prompts for this project
```

## Integration

Works with WFC skills:
- **wfc-implement** - Agents use approved commands without friction
- **wfc-security** - Audit current allowlist vs best practices
- **wfc-architecture** - Detect commands needed by architecture

## Philosophy

**ELEGANT**: Simple scanning, clear categories, explicit approval
**MULTI-TIER**: Scanner → Generator → Settings (clean separation)
**PARALLEL**: Can scan multiple projects concurrently
