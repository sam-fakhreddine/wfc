# WFC Installation

> Get WFC installed and validated in under 5 minutes.

## Prerequisites

1. **Claude Code CLI** — [Install from Anthropic](https://docs.anthropic.com/en/docs/claude-code)
2. **Python 3.12+** — `python3 --version`
3. **UV** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. **GitHub CLI** — `brew install gh && gh auth login`

## Install WFC

```bash
# 1. Clone the repository
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc

# 2. Install WFC (UV is required — never use pip directly)
uv pip install -e ".[all]"

# 3. Verify the CLI is available
wfc validate
```

## Install Skills

Skills are the slash commands you invoke inside Claude Code (e.g. `/wfc-build`).

```bash
# Install all 30 skills to ~/.claude/skills/wfc-*/
bash install-universal.sh

# Alternative via Make
make install
```

The installer auto-detects Claude Code and copies skills into `~/.claude/skills/`.

## Validate Setup

```bash
make doctor
```

Green output looks like this:

```
WFC Doctor - Comprehensive Health Check
========================================
[OK] Python 3.12+ found
[OK] UV available
[OK] WFC package installed
[OK] wfc CLI available
[OK] 30 skills found in ~/.claude/skills/wfc-*/
[OK] Pre-commit hooks configured
[OK] GitHub CLI (gh) available
========================================
All checks passed. WFC is healthy.
```

If any check shows `[FAIL]`, follow the printed remedy before continuing.

## What Got Installed

| Location | What |
|---|---|
| `~/.claude/skills/wfc-*/` | 30 skill packages (wfc-build, wfc-plan, wfc-review, ...) |
| `wfc/` | Python package with review engine, hooks, and orchestrators |
| `.claude/settings.json` | Hook configuration for auto-lint and context monitoring |

## Next Step

Run your first feature build: [FIRST_WORKFLOW.md](./FIRST_WORKFLOW.md)

For adding WFC to an existing project: [CONFIGURE.md](./CONFIGURE.md)
