# wfc-export

## What It Does

Converts WFC skill definitions into native configuration formats for 7 AI coding platforms: OpenCode, Codex, Gemini CLI, GitHub Copilot, Kiro CLI, Cursor, and Factory Droid. It reads each `SKILL.md`, maps frontmatter fields to the target platform's schema, adapts content for platform-specific constraints, and writes the output files in the correct directory structure. The same guardrails travel with the team regardless of which IDE they open.

## When to Use It

- Onboarding a team member who uses a different AI coding tool (Copilot, Cursor, Kiro)
- Syncing WFC skills to multiple platforms as part of a release pipeline
- Setting up a new project where the team uses a mix of AI tools
- Testing whether WFC prompts translate cleanly to another runtime
- Distributing updated skills after a WFC upgrade

## Usage

```bash
/wfc-export [options]
```

## Example

```bash
/wfc-export --to copilot --skills wfc-review,wfc-plan,wfc-build
```

Output structure:

```
.github/
└── copilot/
    ├── wfc-review.agent.md
    ├── wfc-plan.agent.md
    └── wfc-build.agent.md

# wfc-review.agent.md (excerpt):
---
name: wfc-review
description: Five-agent consensus code review with CS scoring
tools: Bash, Read, Write, Glob, Grep
---

[SKILL.md content adapted for Copilot runtime]
```

```bash
/wfc-export --to gemini --dry-run
```

Dry-run output:

```
Would write 26 skills to .gemini/
  .gemini/commands/wfc-review.toml
  .gemini/commands/wfc-plan.toml
  .gemini/skills/wfc-review/SKILL.md
  ... (24 more)
No files written (dry run).
```

## Options

| Flag | Description |
|------|-------------|
| `--to <platform>` | Target platform: `opencode`, `copilot`, `gemini`, `codex`, `kiro`, `cursor`, `droid` |
| `--all` | Export to all supported platforms simultaneously |
| `--skills <list>` | Comma-separated list of skills to export (default: all 26) |
| `--dry-run` | Print what would be written without creating files |
| `--output <dir>` | Override the default output directory for a platform |

**Platform output locations:**

| Platform | Default Output |
|----------|---------------|
| `opencode` | `.opencode/` |
| `copilot` | `.github/copilot/` |
| `gemini` | `.gemini/` |
| `codex` | `~/.codex/` |
| `kiro` | `.kiro/` |
| `cursor` | `.cursor/` |
| `droid` | `~/.factory/` |

## Integration

**Produces:**

- Platform-native config files (agent markdown, TOML commands, JSON configs)
- An export manifest listing which skills were exported to which platforms
- `copilot-mcp-config.json` / `mcp.json` for platforms that support MCP (stdio only)

**What is NOT exported:** Internal Python orchestration scripts, test files, telemetry infrastructure, WFC-specific CLI commands, git hooks.

**Consumes:**

- All `~/.claude/skills/wfc-*/SKILL.md` files (the canonical skill definitions)
- Supporting reference docs and HTML playground templates

**Next step:** Commit the generated config files into your project repository so team members on other tools pick them up automatically. Re-run after each WFC upgrade to keep platforms in sync.
