# WFC Command Reference

All commands available in WFC. Slash commands are invoked inside Claude Code; `make` and `wfc` commands run in your terminal.

---

## Slash Commands (Claude Code)

### Core Workflow

| Command | Description |
|---------|-------------|
| `/wfc-build "description"` | Quick feature — interview → TDD → review → PR |
| `/wfc-plan` | Structured planning — interview → TASKS.md + PROPERTIES.md + TEST-PLAN.md |
| `/wfc-implement path/to/TASKS.md` | Multi-agent parallel implementation from plan |
| `/wfc-lfg "description"` | Full auto pipeline — plan → deepen → implement → review → PR |
| `/wfc-deepen` | Deepen existing plan with parallel research |

### Review & Quality

| Command | Description |
|---------|-------------|
| `/wfc-review` | Five-agent consensus review (current code/diff) |
| `/wfc-review TASK-001` | Review specific task output |
| `/wfc-validate` | 7-dimension plan/idea validation |
| `/wfc-validate "idea"` | Validate a specific idea or approach |
| `/wfc-security` | STRIDE threat modeling |
| `/wfc-test` | Generate property-based tests from PROPERTIES.md |
| `/wfc-observe` | Generate observability instrumentation from properties |

### Planning & Analysis

| Command | Description |
|---------|-------------|
| `/wfc-ba` | Business analysis — structured requirements gathering |
| `/wfc-architecture` | Generate ARCHITECTURE.md + C4 diagrams |
| `/wfc-compound` | Document solved problem into `docs/solutions/` |
| `/wfc-isthissmart "idea"` | Quick sanity check before committing |

### Project Management

| Command | Description |
|---------|-------------|
| `/wfc-housekeeping` | Clean dead code, stale branches, orphaned files |
| `/wfc-gh-debug` | Debug failing GitHub Actions workflow |
| `/wfc-pr-comments` | Triage and fix PR review comments |
| `/wfc-sync` | Sync rules and patterns with codebase state |
| `/wfc-retro` | AI retrospective from telemetry data |

### Setup & Configuration

| Command | Description |
|---------|-------------|
| `/wfc-init` | Initialize WFC for a project (detect language, set up tools) |
| `/wfc-safeguard` | Install real-time security enforcement hooks |
| `/wfc-safeclaude` | Generate project-specific command allowlist |
| `/wfc-rules` | Create markdown-based custom enforcement rules |

### Creation & Export

| Command | Description |
|---------|-------------|
| `/wfc-newskill` | Create a new WFC skill (meta-skill) |
| `/wfc-export` | Export skills to other platforms (Copilot, Gemini, Cursor, etc.) |
| `/wfc-agentic` | Generate GitHub Agentic Workflow files |
| `/wfc-playground "description"` | Create interactive HTML playground |

### Brainstorming

| Command | Description |
|---------|-------------|
| `/wfc-vibe` | Natural brainstorm mode with smart WFC transitions |

### Standards

| Command | Description |
|---------|-------------|
| `/wfc-code-standards` | Apply language-agnostic coding standards |
| `/wfc-python` | Apply Python-specific standards (UV, black, ruff, typing) |

---

## Make Commands (Terminal)

### Setup

| Command | Description |
|---------|-------------|
| `make install` | Install WFC with all features (`uv pip install -e ".[all]"`) |
| `make dev` | Development environment (install + hooks) |
| `make doctor` | Comprehensive health checks |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (`uv run pytest`) |
| `make test-coverage` | Tests with coverage report |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter |
| `make format` | Format with black + ruff |
| `make check-all` | Tests + validate + lint |

### Validation

| Command | Description |
|---------|-------------|
| `make validate` | Validate all 30 WFC skills (Agent Skills compliance) |
| `make validate-xml` | Validate XML prompt generation |
| `make benchmark` | Token usage benchmarks |

### Local CI

| Command | Description |
|---------|-------------|
| `make act-pull` | First-run: pull Docker images for act (~5–15 min) |
| `make act-fast` | Run lint + validate locally (~2 min) |
| `make act-check` | Run full CI gate locally (~10 min) |
| `make pr` | Create PR (runs `act-fast` gate first) |
| `WFC_SKIP_ACT=1 make pr` | Emergency PR bypass (skips act gate) |

---

## UV Commands

Always use UV for Python operations. Never use bare `python` or `pip`.

| Command | Description |
|---------|-------------|
| `uv run pytest` | Run tests |
| `uv run pytest -v` | Run tests verbose |
| `uv run pytest tests/test_file.py` | Run specific test file |
| `uv pip install -e ".[all]"` | Install WFC with all features |
| `uv run python script.py` | Execute a Python script |
| `uv run pre-commit run --all-files` | Run all pre-commit hooks |
| `uv run pre-commit install` | Install pre-commit hooks |

---

## Helper Scripts

Route maintenance operations through helper scripts — never bare shell commands.

| Script | Command | Description |
|--------|---------|-------------|
| `bash scripts/housekeeping-git.sh branches` | | List git branches |
| `bash scripts/housekeeping-git.sh branch-age` | | Show branch ages |
| `bash scripts/housekeeping-git.sh worktrees` | | List worktrees |
| `bash scripts/housekeeping-git.sh all` | | Run all housekeeping |
| `bash scripts/wfc-tools.sh ls` | | List files |
| `bash scripts/wfc-tools.sh find-files <pattern>` | | Find files by pattern |
| `bash scripts/wfc-tools.sh replace <old> <new>` | | Bulk string replace |
| `bash scripts/wfc-tools.sh show-large-files` | | Show large files |

---

## Worktree Manager

Always use the manager — never bare `git worktree add`.

| Command | Description |
|---------|-------------|
| `bash wfc/gitwork/scripts/worktree-manager.sh create <name>` | Create isolated worktree |
| `bash wfc/gitwork/scripts/worktree-manager.sh cleanup` | Remove idle worktrees |
| `bash wfc/gitwork/scripts/worktree-manager.sh list` | List active worktrees |
