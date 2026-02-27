---
name: wfc-export
description: >
  Exports WFC SKILL.md files to platform-specific configuration files. OUTPUT ONLY:
  WFC → external format. Cannot import or sync external configs back to WFC. Requires
  existing SKILL.md files with WFC frontmatter (name, description, license fields)
  in the current working directory.

  Supported platforms ONLY: copilot, cursor, gemini, kiro, opencode, codex, factory.

  Triggers: /wfc-export --to <platform>; /wfc-export --all; "export WFC skills to
  <platform>"; "generate <platform> config from WFC skills"; "convert SKILL.md to
  <platform> instructions".

  Not for: importing external configs to WFC; bidirectional sync; creating/editing
  SKILL.md files (use wfc-build); converting non-WFC files; unsupported platforms
  (Claude Code, Windsurf, Cline, Continue, Aider); lossless export to platforms with
  character limits without --allow-lossy; skills requiring HTTP MCP servers exported
  to stdio-only platforms; non-destructive merging with existing configs.
license: MIT
---

# WFC:EXPORT - Cross-Platform Skill Distribution

**"Same guardrails, whichever IDE your team opens."**

## What It Does

Translates WFC skill definitions into native configs for 7 AI coding platforms — one direction only.

1. **Inventory** - Scan current working directory for SKILL.md files with valid WFC frontmatter (name, description, license)
2. **Translate** - Map to target platform schema using tables below
3. **Emit** - Write platform-native config files (WARNING: overwrites existing files)
4. **Syntax-check** - Verify output is well-formed; does not guarantee platform schema compliance

## Usage

```bash
# Export to specific platform
/wfc-export --to copilot
/wfc-export --to cursor
/wfc-export --to gemini
/wfc-export --to codex
/wfc-export --to kiro
/wfc-export --to opencode
/wfc-export --to factory

# Export all platforms
/wfc-export --all

# Export specific skills only
/wfc-export --to copilot --skills wfc-review,wfc-plan,wfc-build

# Dry run (show what would be written)
/wfc-export --to opencode --dry-run

# Custom output directory (ignored for global-scope platforms: codex, opencode, factory)
/wfc-export --to copilot --output ./exports/copilot/

# Allow character limit truncation (required for Codex if descriptions >1024 chars)
/wfc-export --to codex --allow-lossy
```

**Valid --to values**: `copilot`, `cursor`, `gemini`, `codex`, `kiro`, `opencode`, `factory`

## Supported Platforms

### OpenCode

**Scope:** Global (`~/.config/opencode/`) — `--output` flag ignored
**Output:**

```
~/.config/opencode/
├── opencode.json
├── skills/
│   └── <skill-name>/SKILL.md
└── agents/
    └── <agent-name>.md
```

### GitHub Copilot

**Scope:** Project (`.github/`)
**Output:**

```
.github/
├── copilot/
│   └── <skill-name>.agent.md
└── copilot-mcp-config.json
```

**Copilot Agent Format:**

```markdown
---
name: <skill-name>
description: <truncated to 1024 chars if needed>
tools: Bash, Read, Write, Glob, Grep
---
[SKILL.md body content]
```

### Gemini CLI

**Scope:** Project (`.gemini/`)
**Output:**

```
.gemini/
├── commands/
│   └── <skill-name>.toml
├── skills/
│   └── <skill-name>/SKILL.md
└── settings.json
```

**Note:** HTTP MCP servers are stripped. Only stdio MCP servers included in settings.json.

### Codex

**Scope:** Global (`~/.codex/`) — `--output` flag ignored
**Output:**

```
~/.codex/
├── prompts/
│   └── <skill-name>.md
└── skills/
    └── <skill-name>/SKILL.md
```

**Constraint:** Descriptions truncated to 1024 characters. Requires `--allow-lossy` if source exceeds limit.

### Kiro CLI

**Scope:** Project (`.kiro/`)
**Output:**

```
.kiro/
├── agents/
│   ├── <skill-name>.json
│   └── <skill-name>-prompt.md
├── skills/
│   └── <skill-name>/SKILL.md
├── steering/
│   └── wfc-rules.md
└── mcp.json
```

**Note:** HTTP MCP servers are stripped. Only stdio MCP servers included in mcp.json.

### Cursor

**Scope:** Project (`.cursor/`)
**Output:**

```
.cursor/
├── rules/
│   └── <skill-name>.md
└── agents/
    └── <skill-name>.json
```

**Cursor Agent Schema:**

```json
{
  "name": "<skill-name>",
  "description": "<description text>",
  "instructions": "<path to rules/<skill-name>.md>"
}
```

### Factory Droid

**Scope:** Global (`~/.factory/`) — `--output` flag ignored
**Output:** Tool-mapped configs (Bash→Execute, Write→Create, Read→ReadFile)
**Status:** Partial support. Directory structure follows Codex pattern. Tool mapping applied to instruction text.

## Conversion Rules

### Frontmatter Mapping

| WFC Field | Copilot | Gemini | Kiro | OpenCode |
|-----------|---------|--------|------|----------|
| name | name | command_name | agent_id | skill_name |
| description | description | description | description | description |
| license | (dropped) | (dropped) | (dropped) | (dropped) |

### Content Adaptation

- **Body content**: Preserved verbatim (no truncation unless platform requires)
- **Line count**: Files >500 lines export with warning; no automatic summarization
- **References**: Markdown links adjusted for target directory structure; referenced files NOT copied
- **WFC-specific sections**: Configuration/Integration sections wrapped in `<!-- WFC-NATIVE --> ... <!-- /WFC-NATIVE -->`
- **Tool references**: Preserved verbatim. No automatic tool name mapping. Manual review required.

### What Gets Exported

| Component | Exported | Notes |
|-----------|----------|-------|
| SKILL.md body | Yes | Preserved verbatim |
| WFC frontmatter | Mapped | Per platform table |
| stdio MCP servers | Yes | Copilot, Gemini, Kiro only |
| HTTP MCP servers | No | Stripped with warning |

### What Doesn't Get Exported

- Internal Python code
- Test files
- Telemetry infrastructure
- WFC CLI commands
- Git hooks
- HTTP MCP server definitions (stripped)

## Configuration

Located in `.wfc/export.json` in project root:

```json
{
  "platforms": ["copilot", "gemini", "kiro", "opencode"],
  "skills": "all",
  "include_reviewers": true,
  "output_base": "./exports"
}
```

## Philosophy

**POLYGLOT**: Same guardrails, any supported AI coding tool
**FILTERED**: Ship the signal, drop the scaffolding
**ONE-SHOT**: Single invocation exports to every configured platform
**DESTRUCTIVE**: Overwrites existing target files without backup
