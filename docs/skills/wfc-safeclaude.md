# wfc-safeclaude

## What It Does

`wfc-safeclaude` scans a project to detect its language, frameworks, and toolchain, then proposes a categorized command allowlist and generates `.claude/settings.local.json`. It eliminates the repetitive approval prompts that slow down every new Claude Code session without resorting to YOLO mode, which removes all guardrails. Destructive commands, secret files, and force operations are never proposed — the allowlist is curated and project-specific.

## When to Use It

- You are setting up Claude Code on a new project and the constant approval prompts are adding friction
- You want to approve a curated set of safe commands once rather than one-by-one each session
- You are onboarding a team and want a consistent, reviewed allowlist committed to the repo
- You are in a production or shared environment and want strict read-only mode
- You want to add or remove individual commands from an existing allowlist

## Usage

```bash
/wfc-safeclaude
/wfc-safeclaude --show
/wfc-safeclaude --strict
/wfc-safeclaude --add "docker compose up"
/wfc-safeclaude --remove "rm -rf"
/wfc-safeclaude --reset
```

## Example

```
User: /wfc-safeclaude

Scanning project...
✅ Detected: Node.js + TypeScript + Jest + Docker + GitHub Actions

Proposed Allowlist:

Universal (38 commands)
  ✅ ls, cat, grep, find, wc, diff, pwd, env, stat, which

Git Read (5 commands)
  ✅ git status, git log, git diff, git show, git branch

Git Write (7 commands)
  ⚠️  git add, git commit, git push, git pull, git checkout

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
✅ 54 commands approved — no more approval prompts for this project
```

## Options

```bash
/wfc-safeclaude              # Scan project and generate allowlist interactively
/wfc-safeclaude --show       # Display the current allowlist
/wfc-safeclaude --strict     # Read-only mode: no git write, no build/CI commands
/wfc-safeclaude --add "cmd"  # Add a specific command to the allowlist
/wfc-safeclaude --remove "cmd" # Remove a specific command from the allowlist
/wfc-safeclaude --reset      # Clear allowlist and regenerate from scratch
```

In `--strict` mode, only universal safe commands and git read operations are included — suitable for production environments or shared codebases where write operations need manual approval.

## Integration

**Produces:**

- `.claude/settings.local.json` — project-specific command allowlist with file pattern rules

**Consumes:**

- Project files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Dockerfile`, `.github/workflows/`, and other toolchain signals

**Next step:** Commit `.claude/settings.local.json` to the repo so the allowlist is shared across the team. Run `/wfc-security` to audit the allowlist against security best practices if needed. wfc-implement agents will use the approved commands without friction once the allowlist is in place.
