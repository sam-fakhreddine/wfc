# WFC — World Fucking Class

Multi-agent code review, planning, and implementation framework for Claude Code.

**YOU ARE WORKING ON THE WFC CODEBASE ITSELF.**
This is the repository that BUILDS WFC skills and orchestrators.
Do not confuse working ON WFC with working WITH WFC.

**Never implement features manually — always use WFC skills.**

---

## 🚀 WFC2 Platform Transformation (Active)

**Branch**: `feat/wfc2-platform` (long-running, started 2026-02-22)

**Vision**: Transform WFC from CLI tool → **Centralized AI Development Platform**

- Single source of truth for all development artifacts (plans, reviews, BAs, tests)
- Living documentation engine (auto-generated from actual work)
- Team dashboard (visualize AI agent activity)
- Multi-agent collaboration hub

**Roadmap**: See `.github/WFC2-ROADMAP.md`
**BA Document**: See `ba/BA-mcp-gateway-integration.md`

### WFC2 Development Rules

- **Branch from**: `feat/wfc2-platform` (not develop)
- **Sub-feature pattern**: `feat/wfc2-{feature-name}` (e.g., `feat/wfc2-artifact-storage`)
- **Merge to**: `feat/wfc2-platform` first, then periodically to `develop`
- **Backward compatibility**: CRITICAL - existing MCP/REST clients must work unchanged
- **Testing**: 85% coverage minimum, integration tests required
- **Performance targets**: Auth < 5ms, artifacts < 50ms, search < 200ms

### WFC2 Phase 1 Priorities (Current)

1. **M-000**: Central artifact storage (SQLite/PostgreSQL)
2. **M-001**: Unified authentication gateway
3. **M-002**: Per-project rate limiting (all transports)
4. **M-003**: Request normalization layer
5. **M-004**: Unified observability pipeline
6. **M-005**: Living documentation API (search, timeline, insights)

**When working on WFC2**: Always check `.github/WFC2-ROADMAP.md` for current status.

---

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

- **MULTI-AGENT ANALYSIS:** For complex analysis tasks (validation, review, planning), ALWAYS use Task tool to spawn parallel subagents. Never analyze sequentially in main context. Each dimension/concern gets its own agent.
- **Branching (WFC2):** For WFC2 work, branch from `feat/wfc2-platform`. For other work, branch from `develop`. Never branch from `main`.
- **Branching (General):** ALWAYS branch from `develop` (or `feat/wfc2-platform` for WFC2). Never branch from `main` or feature branches.
- **Skills:** Hyphenated names only (`wfc-review` not `wfc:review`). No invalid frontmatter. `make validate` before commit.
- **Code:** `make format` before commit. `make check-all` before PR. Never commit failing tests. Never skip pre-commit hooks.
- **Worktrees:** `bash wfc/gitwork/scripts/worktree-manager.sh create <name>`. Never bare `git worktree add`.
- **Knowledge:** `/wfc-compound` after solving non-trivial problems (>15 min).
- **Workspace:** Dev artifacts in `.development/` (gitignored). Never commit summaries or scratch notes.
- **Tokens:** Never send full file content to reviewers. Always use file reference architecture.
- **Parallel Execution:** Use parallel Task calls in single message when agents are independent. Follow PARALLEL principle from WFC philosophy.

## Context Files

- `wfc/references/SKILLS.md` — full skill reference (30 skills, decision guide, typical flows)
- `docs/workflow/WFC_IMPLEMENTATION.md` — wfc-implement TDD architecture, agent workflow, key files
- `wfc/references/TEAMCHARTER.md` — values governance, plan validation
- `wfc/references/TOKEN_MANAGEMENT.md` — token optimization strategy
- `PLANNING.md` — architectural decisions and absolute rules
- `docs/README.md` — full documentation index
- `.devcontainer/` — devcontainer setup (firewall, tools, workspace layout)
