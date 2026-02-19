# Configure WFC for Your Project

> Add WFC to an existing project. Takes about 10 minutes.

## 1. Copy a CLAUDE.md Template

CLAUDE.md tells Claude Code how to behave in your project. WFC ships three templates:

| Template | Use when |
|---|---|
| `docs/examples/CLAUDE.md.startup` | Small team, fast iteration, pre-PMF |
| `docs/examples/CLAUDE.md.enterprise` | Compliance requirements, strict quality gates |
| `docs/examples/CLAUDE.md.opensource` | Open source, community contributions |

Copy the one that fits:

```bash
# From the WFC repo, copy into your project root
cp /path/to/wfc/docs/examples/CLAUDE.md.startup /your-project/CLAUDE.md
```

Edit the template to add your tech stack, team conventions, and quality thresholds. The key section to customize:

```markdown
## Tech Stack

- **Backend**: Python 3.12, FastAPI
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Kubernetes
```

## 2. Configure Hooks in `.claude/settings.json`

Hooks give WFC real-time enforcement: auto-lint on file save, TDD reminders, and context monitoring.

Create or update `.claude/settings.json` in your project root:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python /path/to/wfc/wfc/scripts/hooks/pretooluse_hook.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python /path/to/wfc/wfc/scripts/hooks/file_checker.py"
          },
          {
            "type": "command",
            "command": "uv run python /path/to/wfc/wfc/scripts/hooks/tdd_enforcer.py"
          }
        ]
      },
      {
        "matcher": "Read|Write|Edit|Bash|Skill|Grep|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "uv run python /path/to/wfc/wfc/scripts/hooks/context_monitor.py"
          }
        ]
      }
    ]
  }
}
```

What each hook does:

- `pretooluse_hook.py` — blocks known security anti-patterns (13 patterns from `security.json`) before a tool runs
- `file_checker.py` — auto-lints Python/TypeScript/Go files after every write
- `tdd_enforcer.py` — reminds the agent to write tests before implementation
- `context_monitor.py` — tracks context window usage; warns before it fills

Hooks are fail-open: a hook crash never blocks your workflow.

## 3. Set Up Pre-commit

```bash
# In your project root
uv run pre-commit install
```

Verify it works:

```bash
uv run pre-commit run --all-files
```

This runs on every commit: trailing whitespace, YAML/JSON/TOML validation, secret detection, black, ruff, and shellcheck.

## 4. Configure the Git Workflow

WFC v3.0 targets `develop` as the integration branch. Set it up once:

```bash
# Create the develop branch if it does not exist
git checkout -b develop
git push -u origin develop

# (Optional) Set develop as default branch in GitHub:
# GitHub repo → Settings → Branches → Default branch → develop
```

From this point, WFC agents push `claude/*` branches and open PRs to `develop`. You promote `develop` to `main` on your release schedule.

If your project uses `main` as the integration branch and you do not want a `develop` branch, set this in your CLAUDE.md:

```markdown
## Git Workflow

Target branch: main
Agent branch prefix: claude/
```

## 5. Optional: Custom Enforcement Rules

Create `.wfc/rules/` in your project root to add project-specific enforcement rules in plain Markdown.

```bash
mkdir -p .wfc/rules
```

Example rule file `.wfc/rules/no-print-statements.md`:

```markdown
# No Print Statements in Production Code

**Pattern**: `print(` in any `.py` file outside `tests/`
**Action**: block
**Message**: Use the project logger instead of print statements.
  Replace with: `logger.info("...")`
```

Rules are evaluated by `pretooluse_hook.py` on every write. Use `/wfc-rules` inside Claude Code to generate and manage rules interactively.

## Verify Everything Works

```bash
make doctor
```

Then open Claude Code in your project and run:

```
/wfc-build "add a health check endpoint"
```

You should see the interview, TDD cycle, review, and a PR link.

## Full Reference

- Skills reference: [docs/skills/](../skills/)
- Hook system: `wfc/scripts/hooks/`
- Security patterns: `wfc/scripts/hooks/patterns/security.json`
- Git workflow details: [docs/workflow/](../workflow/)
