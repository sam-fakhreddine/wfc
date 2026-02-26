# WFC — World Fucking Class

Multi-agent code review, planning, and implementation framework for Claude Code.

**YOU ARE WORKING ON THE WFC CODEBASE ITSELF.**
This is the repository that BUILDS WFC skills and orchestrators.
Do not confuse working ON WFC with working WITH WFC.

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
wfc/                         # Repo — source code only
├── scripts/orchestrators/   # Python orchestration (review, build, vibe)
├── scripts/hooks/           # PreToolUse/PostToolUse infrastructure
├── scripts/knowledge/       # RAG knowledge system
├── references/reviewers/    # 5 reviewer PROMPT.md + KNOWLEDGE.md (file I/O, NOT Python imports)
├── gitwork/                 # git operations via worktree-manager.sh
└── skills/                  # Agent Skills packages

~/.claude/skills/wfc-*/      # 33 installed skills

~/.wfc/projects/{repo}/branches/{branch}/   # Dev artifacts (Documentation is Infrastructure)
├── plans/                   # Timestamped plan directories
├── reviews/                 # wfc-review artifacts
├── ba/                      # Business analysis documents
├── experiments/             # Spikes, proofs-of-concept, explorations
└── docs/                    # All generated documentation
```

**Review:** 5 fixed reviewers (Security, Correctness, Performance, Maintainability, Reliability). NOT dynamically selected, NOT 56 personas.
CS formula: `(0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)`. MPR: if R_max ≥ 8.5 from Security/Reliability → CS elevated.

## Absolute Rules

- **MULTI-AGENT ANALYSIS:** For complex analysis tasks (validation, review, planning), ALWAYS use Task tool to spawn parallel subagents. Never analyze sequentially in main context. Each dimension/concern gets its own agent.
- **Branching:** ALWAYS branch from `develop`. Never branch from `main` or feature branches.
- **Skills:** Hyphenated names only (`wfc-review` not `wfc:review`). No invalid frontmatter. `make validate` before commit.
- **Code:** `make format` before commit. `make check-all` before PR. Never commit failing tests. Never skip pre-commit hooks.
- **Worktrees:** `bash wfc/gitwork/scripts/worktree-manager.sh create <name>`. Never bare `git worktree add`.
- **Knowledge:** `/wfc-compound` after solving non-trivial problems (>15 min).
- **Workspace:** All dev artifacts in `~/.wfc/projects/{repo}/branches/{branch}/` — plans, reviews, ba, experiments, docs. Never commit dev artifacts to the repo. **Documentation is Infrastructure** — never discard generated docs; store them in `~/.wfc`.
- **Experiments:** Spikes and proofs-of-concept go to `~/.wfc/projects/{repo}/branches/{branch}/experiments/`. Never in the repo root or `.development/`.
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
