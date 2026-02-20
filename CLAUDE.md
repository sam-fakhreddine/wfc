# WFC — World Fucking Class

Multi-agent code review, planning, and implementation framework for Claude Code.
**Never implement features manually — always use WFC skills.**

## Python Environment

```bash
uv run pytest              # tests
uv pip install -e ".[all]" # install
uv run python script.py    # scripts
```

Never: `python -m pytest` · `pip install` · `python script.py`

## Workflow

```
/wfc-lfg "feature"    # Full auto: plan → implement → review → PR
/wfc-build "feature"  # Quick single feature (adaptive interview)
/wfc-plan             # Structured planning for large features
/wfc-implement        # Execute TASKS.md with parallel TDD agents
/wfc-review           # 5-agent consensus review
/wfc-ba               # Business analysis / requirements
/wfc-compound         # Codify a solved problem into docs/solutions/
/wfc-pr-comments      # Triage and fix PR review comments
```

**Branch policy:** Agents push `claude/*` → auto-merge PR to `develop`. Never push directly to `main`.

## Commands

```bash
make install          # install WFC
make test             # run all tests
make format           # black + ruff
make check-all        # tests + validate + lint
make validate         # Agent Skills compliance check
make act-fast         # local CI gate (~2 min)
make pr               # create PR (runs act-fast first)
uv run pytest tests/test_file.py -v  # single test file
```

## Architecture

```
wfc/
├── scripts/orchestrators/   # review, build, claude_md pipelines
├── scripts/hooks/           # PreToolUse/PostToolUse infrastructure
├── scripts/knowledge/       # RAG knowledge system
├── references/reviewers/    # 5 reviewer PROMPT.md + KNOWLEDGE.md
├── gitwork/                 # git operations (worktree-manager.sh)
└── skills/                  # Agent Skills packages

~/.claude/skills/wfc-*/      # 30 installed skills
```

**Review:** 5 fixed reviewers (Security, Correctness, Performance, Maintainability, Reliability).
CS formula: `(0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)`. MPR: if R_max ≥ 8.5 from Security/Reliability → CS elevated.

## Absolute Rules

- **Skills:** Hyphenated names only (`wfc-review` not `wfc:review`). No invalid frontmatter. `make validate` before commit.
- **Code:** `make format` before commit. `make check-all` before PR. Never commit failing tests. Never skip pre-commit hooks.
- **Worktrees:** `bash wfc/gitwork/scripts/worktree-manager.sh create <name>`. Never bare `git worktree add`.
- **Knowledge:** `/wfc-compound` after solving non-trivial problems (>15 min).
- **Workspace:** Dev artifacts in `.development/` (gitignored). Never commit summaries or scratch notes.
- **Tokens:** Never send full file content to reviewers. Always use file reference architecture.

## Context Files

- `wfc/references/SKILLS.md` — full skill reference (30 skills, decision guide, typical flows)
- `docs/workflow/WFC_IMPLEMENTATION.md` — wfc-implement TDD architecture, agent workflow, key files
- `wfc/references/TEAMCHARTER.md` — values governance, plan validation
- `wfc/references/TOKEN_MANAGEMENT.md` — token optimization strategy
- `PLANNING.md` — architectural decisions and absolute rules
- `docs/README.md` — full documentation index
- `.devcontainer/` — devcontainer setup (firewall, tools, workspace layout)
