---
name: wfc-export
description: Multi-platform skill export that converts WFC skills into formats compatible with other AI coding tools. Supports OpenCode, Codex, Gemini CLI, GitHub Copilot, Kiro CLI, Cursor, and Factory Droid. Reads WFC skill SKILL.md files and generates platform-specific configurations. Triggers on "export skills", "convert for copilot", "sync to opencode", or explicit /wfc-export. Ideal when adopting WFC skills in multi-tool teams. Not for internal WFC development.
license: MIT
---

# WFC:EXPORT - Multi-Platform Skill Export

**"WFC skills everywhere your team codes."**

## What It Does

Converts WFC skills into formats compatible with 7+ AI coding platforms, so teams using different tools all benefit from WFC's quality infrastructure.

1. **Scan** - Read all WFC skill SKILL.md files
2. **Convert** - Transform to target platform format
3. **Write** - Output platform-specific files
4. **Verify** - Validate generated configs

## Usage

```bash
# Export to specific platform
/wfc-export --to opencode
/wfc-export --to copilot
/wfc-export --to gemini
/wfc-export --to codex
/wfc-export --to kiro
/wfc-export --to cursor
/wfc-export --to droid

# Export all platforms
/wfc-export --all

# Export specific skills only
/wfc-export --to copilot --skills wfc-review,wfc-plan,wfc-build

# Dry run
/wfc-export --to opencode --dry-run

# Custom output directory
/wfc-export --to copilot --output ./exports/copilot/
```

## Supported Platforms

### OpenCode
**Output:** `~/.config/opencode/` or `.opencode/`
**Format:** `opencode.json` + skill directories + agent markdown files

```
.opencode/
├── opencode.json          # Tool config
├── skills/
│   ├── wfc-review/SKILL.md
│   ├── wfc-plan/SKILL.md
│   └── ...
└── agents/
    ├── security-reviewer.md
    └── ...
```

### GitHub Copilot
**Output:** `.github/`
**Format:** `.agent.md` files with Copilot frontmatter

```
.github/
├── copilot/
│   ├── wfc-review.agent.md    # Copilot agent format
│   ├── wfc-plan.agent.md
│   └── ...
└── copilot-mcp-config.json    # MCP server config
```

**Copilot Agent Format:**
```markdown
---
name: wfc-review
description: Five-agent consensus code review
tools: Bash, Read, Write, Glob, Grep
---

[SKILL.md content adapted for Copilot]
```

### Gemini CLI
**Output:** `.gemini/`
**Format:** TOML commands + skill directories

```
.gemini/
├── commands/
│   ├── wfc-review.toml
│   ├── wfc-plan.toml
│   └── ...
├── skills/
│   ├── wfc-review/SKILL.md
│   └── ...
└── settings.json              # MCP servers (stdio only)
```

### Codex
**Output:** `~/.codex/`
**Format:** Prompts + skills (descriptions truncated to 1024 chars)

```
~/.codex/
├── prompts/
│   ├── wfc-review.md
│   └── ...
└── skills/
    ├── wfc-review/SKILL.md
    └── ...
```

### Kiro CLI
**Output:** `.kiro/`
**Format:** JSON agent configs + prompt markdown + steering files

```
.kiro/
├── agents/
│   ├── wfc-review.json
│   ├── wfc-review-prompt.md
│   └── ...
├── skills/
│   ├── wfc-review/SKILL.md
│   └── ...
├── steering/
│   └── wfc-rules.md           # From CLAUDE.md
└── mcp.json                   # MCP servers (stdio only)
```

### Cursor
**Output:** `.cursor/`
**Format:** Rules + agent configs

```
.cursor/
├── rules/
│   ├── wfc-review.md
│   └── ...
└── agents/
    ├── wfc-review.json
    └── ...
```

### Factory Droid
**Output:** `~/.factory/`
**Format:** Tool-mapped configs (Bash→Execute, Write→Create, etc.)

## Conversion Rules

### Frontmatter Mapping

| WFC Field | Copilot | Gemini | Kiro | OpenCode |
|-----------|---------|--------|------|----------|
| name | name | command_name | agent_id | skill_name |
| description | description | description (truncated) | description | description |
| license | (dropped) | (dropped) | (dropped) | (dropped) |

### Content Adaptation

- **Progressive disclosure**: SKILL.md content preserved as-is (under 500 lines)
- **References**: Relative paths adjusted for target platform directory structure
- **WFC-specific sections**: Configuration, Integration sections preserved but marked as WFC-native
- **Tool references**: Mapped to platform equivalents where different

### What Gets Exported

| Component | Exported | Notes |
|-----------|----------|-------|
| SKILL.md | Yes | Core skill content |
| References | Yes | Supporting docs |
| Scripts | Platform-dependent | Only if platform supports execution |
| Templates | Yes | HTML playground templates |
| Reviewer prompts | Yes | As agent definitions |
| MCP servers | stdio only | HTTP MCP servers skipped |

### What Doesn't Get Exported

- Internal Python code (orchestrator.py, etc.)
- Test files
- Telemetry infrastructure
- WFC-specific CLI commands
- Git hooks

## Integration with WFC

### Consumed By
- CI/CD pipelines (export on release)
- Team onboarding (export for new developer's preferred tool)

### Produces
- Platform-specific config files
- Export manifest (which skills exported to which platforms)

## Configuration

```json
{
  "export": {
    "platforms": ["copilot", "gemini", "kiro", "opencode"],
    "skills": "all",
    "include_reviewers": true,
    "include_references": true,
    "output_base": "./exports"
  }
}
```

## Philosophy

**PORTABLE**: WFC skills work everywhere
**FAITHFUL**: Content preserved, only format changes
**SELECTIVE**: Export what matters, skip internals
**AUTOMATED**: One command to sync across platforms
