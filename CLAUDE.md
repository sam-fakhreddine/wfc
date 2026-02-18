# CLAUDE.md

This file provides guidance to Claude Code when working with the WFC codebase.

## 🐍 Python Environment Rules

**CRITICAL**: This project uses **UV** for all Python operations.

### Required Commands

```bash
# All Python operations must use UV
uv run pytest                    # Run tests
uv run pytest -v                 # Run tests verbose
uv pip install -e ".[all]"       # Install WFC with all features
uv run python script.py          # Execute scripts
wfc validate                     # Validate skills (after install)
```

**NEVER use**:
- ❌ `python -m pytest`
- ❌ `pip install`
- ❌ `python script.py`

**ALWAYS use**:
- ✅ `uv run pytest`
- ✅ `uv pip install`
- ✅ `uv run python`

## 🎯 WFC Workflow (ALWAYS USE)

**CRITICAL**: Always use WFC skills for feature development. Never implement features manually.

### Complete Workflow

```
1. BA → 2. Validate → 3. Plan → 4. Deepen → 5. Build/Implement → 6. Review → 7. Compound → 8. User Pushes
```

#### Option Z: Full Auto (LFG)

```bash
/wfc-lfg "add rate limiting to API"
```

**Use when:**
- Feature scope is clear, you trust the pipeline
- Want zero human intervention between steps
- Well-understood codebase patterns

**What happens:**
1. Plan (quick interview → TASKS.md)
2. Deepen (parallel research enrichment)
3. Implement (parallel agents, TDD, quality gates)
4. Review (5-agent consensus, conditional activation)
5. Resolve findings automatically
6. Test suite + quality checks
7. Push branch + create PR with post-deploy validation plan
8. **STOP - PR created, user reviews on GitHub**

#### Option A: Quick Features (Intentional Vibe)

```bash
/wfc-build "add rate limiting to API"
```

**Use when:**
- Single feature, clear scope
- Want to iterate quickly
- "Just build this and ship"

**What happens:**
1. Quick adaptive interview (3-5 questions)
2. Orchestrator assesses complexity (1 agent or N agents)
3. Subagent(s) implement via TDD in isolated worktrees
4. Quality checks (formatters, linters, tests)
5. Consensus review (wfc-review with 5 expert personas)
6. Merge to local main (integration tests)
7. **STOP - User reviews and pushes manually**

#### Option B: Complex Features (Full Planning)

```bash
# Step 1: Gather and structure requirements
/wfc-ba

# Step 2: Validate requirements quality
/wfc-validate

# Step 3: Create structured plan from validated BA
/wfc-plan

# Step 3.5 (optional): Deepen plan with parallel research
/wfc-deepen

# Step 4: Execute plan with parallel agents
/wfc-implement

# Step 5: Final review (if not already done per-task)
/wfc-review

# Step 6 (after solving problems): Document solutions
/wfc-compound
```

**Use when:**
- Large feature with multiple tasks
- Complex dependencies
- Need formal properties (SAFETY, LIVENESS, etc.)

#### TEAMCHARTER-Validated Planning

**All plans go through TEAMCHARTER validation** to ensure alignment with core values (Innovation, Accountability, Teamwork, Learning, Customer Focus, Trust).

**Validated Plan Flow:**

```
1. Generate Plan (wfc-plan)
   ↓
2. Validate Review (7-dimension critique)
   ↓
3. Revise Plan (based on feedback)
   ↓
4. Code Review Loop (5 expert personas)
   ↓ (iterate until score >= 8.5)
5. Final Plan (ready for implementation)
```

**What happens:**
- Plan generator creates initial TASKS.md with values alignment
- Validate skill performs 7-dimension critique (complexity, risk, customer value, etc.)
- Plan is revised based on feedback
- Multi-agent code review validates quality (loops until 8.5+ weighted score)
- Final plan includes immutable audit trail showing validation was performed

**Governance Documents:**
- `wfc/references/TEAMCHARTER.md` - Values governance (human-readable)
- `wfc/references/teamcharter_values.json` - Machine-readable values schema

**Bypass (not recommended):**
```bash
# Skip validation (creates audit trail entry)
wfc plan --skip-validation
```

**Why TEAMCHARTER validation:**
- Prevents over-engineering through complexity budgets
- Ensures customer focus through dedicated interview questions
- Tracks Say:Do ratio (estimated vs. actual complexity)
- Enables retrospective learning through values alignment tracking

### Git Workflow Policy (v3.0 - Autonomous Branching)

**Versioning:** Use autosemver for automatic semantic versioning (BREAKING CHANGES, feat:, fix:)

**DEFAULT**: WFC targets `develop` as the integration branch. Release candidates are cut from develop to main on a schedule.

```
WFC autonomous loop:
  Issue (agent-ready) -> Agent Dispatch -> /wfc-build -> TDD -> Review
                                                                  |
                                                          Push claude/* branch
                                                                  |
                                                        PR to develop (auto-merge)
                                                                  |
                                                    develop-health.yml (self-healing)
                                                                  |
                                                  cut-rc.yml (Friday 18:00 UTC)
                                                                  |
                                                    rc/vX.Y.Z -> PR to main
                                                                  |
                                              promote-rc.yml (24h soak + green CI)
                                                                  |
                                                        Tag vX.Y.Z -> Release
```

**What Changed (v3.0):**
- NEW: `develop` is the default integration branch (not `main`)
- NEW: Agent branches use `claude/` prefix and auto-merge to develop
- NEW: Release candidates (rc/vX.Y.Z) soak 24h before promotion to main
- NEW: Self-healing on develop (auto-revert + bug issue on test failure)
- NEW: Autonomous dispatch via GitHub Issues + self-hosted runner
- UNCHANGED: Never pushes directly to main/master
- UNCHANGED: User controls final releases (via RC promotion)

**Why Autonomous Branching:**
- Agents ship features autonomously (weekends, nights)
- develop absorbs risk (main stays stable)
- RC soak period catches integration issues
- Self-healing prevents broken develop from blocking work
- Full audit trail via GitHub Issues, PRs, and tags

### When to Use Which Skill

| Task | Skill | Why |
|------|-------|-----|
| Brainstorming | **default mode** | wfc-vibe: natural chat, transitions when ready |
| New feature (small) | `/wfc-build` | Intentional Vibe - fast iteration |
| New feature (large) | `/wfc-plan` + `/wfc-implement` | Structured approach |
| Full auto pipeline | `/wfc-lfg` | Plan + deepen + implement + review + ship |
| Deepen a plan | `/wfc-deepen` | Post-plan parallel research enhancement |
| Document solution | `/wfc-compound` | Codify solved problems for team knowledge |
| Code review | `/wfc-review` | Multi-agent consensus (conditional activation) |
| Security audit | `/wfc-security` | STRIDE threat modeling |
| Architecture docs | `/wfc-architecture` | C4 diagrams + ADRs |
| Generate tests | `/wfc-test` | Property-based tests |
| Add monitoring | `/wfc-observe` | Observability from properties |
| Validate idea | `/wfc-validate` | 7-dimension analysis |
| Security hooks | `/wfc-safeguard` | Real-time pattern enforcement |
| Custom rules | `/wfc-rules` | Markdown-based code standards |
| Visual exploration | `/wfc-playground` | Interactive HTML prototyping |
| Fix PR comments | `/wfc-pr-comments` | Triage & fix review feedback |
| Sync rules | `/wfc-sync` | Discover patterns & sync rules |
| Agentic workflows | `/wfc-agentic` | Generate gh-aw workflows |
| Business analysis | `/wfc-ba` | Requirements gathering & BA docs |
| Export skills | `/wfc-export` | Multi-platform skill export (Copilot, Gemini, etc.) |

**Note:** wfc-vibe is the default conversational mode. Just chat naturally - when you're ready to implement, say "let's plan this" or "let's build this".

### Example Session

```bash
# User wants to add a feature
You: "Add rate limiting to the API"

# Claude uses WFC workflow:
/wfc-build "add rate limiting to API"

# Quick interview:
Q: Which endpoints?
A: All /api/* endpoints

Q: Rate limit?
A: 100 requests/minute per user

Q: Storage?
A: Redis

# Orchestrator spawns subagent → TDD → Quality → Review → Push + PR

# WFC output:
# ✅ Task complete
# ✅ Pushed branch: feat/TASK-001-rate-limiting
# ✅ Created PR #42: https://github.com/user/repo/pull/42

# YOU review the PR on GitHub:
# - Check code changes
# - Request changes if needed
# - Merge when ready

# LEGACY mode (if you set "merge.strategy": "direct"):
git log -1        # Review local merge
git diff HEAD~1
git push origin main  # Push when ready
```

### Absolute Rules

**DO:**
- ✅ Use `/wfc-build` for single features
- ✅ Use `/wfc-plan` + `/wfc-implement` for complex work
- ✅ Use `/wfc-review` for all code reviews
- ✅ Review PRs on GitHub before merging
- ✅ Install gh CLI for PR workflow: `brew install gh && gh auth login`
- ✅ Use legacy mode if needed: config `"merge.strategy": "direct"`

**DON'T:**
- ❌ Implement features manually without WFC
- ❌ Skip quality checks
- ❌ Skip consensus review
- ❌ Let WFC push to main/master (it won't - PRs only)
- ❌ Force push without understanding changes
- ❌ Commit task summaries, dev logs, or scratch notes to the repo

### Development Workspace

**`.development/`** is the local-only workspace (gitignored). All dev artifacts go here:

```
.development/
├── summaries/    # Task completion summaries, session recaps
├── plans/        # Working plans, TASKS.md drafts, properties, test plans
├── backups/      # File backups, old versions before rewrites
└── scratch/      # Temporary notes, experiments, one-off scripts
```

**Rule:** Never commit development artifacts (summaries, progress logs, scratch notes) to the repo. Keep them in `.development/` where they stay local and organized.

## 📂 Project Structure

**Current Architecture**: Agent Skills compliant multi-agent review system

```
WFC - World Fucking Class
│
├── wfc/                          # Main package
│   ├── reviewers/                # 5 fixed specialist reviewers
│   │   ├── security/             # PROMPT.md + KNOWLEDGE.md
│   │   ├── correctness/
│   │   ├── performance/
│   │   ├── maintainability/
│   │   └── reliability/
│   ├── scripts/                  # Executable code
│   │   ├── skills/               # Skill implementations
│   │   │   └── review/
│   │   │       ├── orchestrator.py       # Two-phase review workflow
│   │   │       ├── reviewer_engine.py    # Prepare tasks + parse results
│   │   │       ├── reviewer_loader.py    # Load reviewer configs
│   │   │       ├── consensus_score.py    # CS algorithm + MPR
│   │   │       ├── fingerprint.py        # SHA-256 finding dedup
│   │   │       ├── emergency_bypass.py   # 24h bypass with audit trail
│   │   │       └── cli.py               # CLI interface
│   │   ├── knowledge/            # RAG-powered knowledge system
│   │   │   ├── rag_engine.py            # Embedding + retrieval
│   │   │   ├── retriever.py             # Two-tier knowledge retrieval
│   │   │   ├── knowledge_writer.py      # Auto-append to KNOWLEDGE.md
│   │   │   ├── drift_detector.py        # Staleness/bloat/contradiction detection
│   │   │   └── embedding_provider.py    # Embedding abstraction
│   │   ├── hooks/                # Hook infrastructure
│   │   │   ├── pretooluse_hook.py        # PreToolUse hook handler
│   │   │   ├── security_hook.py          # Security enforcement
│   │   │   ├── rule_engine.py            # Custom rule engine
│   │   │   ├── config_loader.py          # Hook configuration
│   │   │   ├── hook_state.py             # Hook state management
│   │   │   ├── file_checker.py           # PostToolUse auto-lint dispatcher
│   │   │   ├── tdd_enforcer.py           # PostToolUse TDD reminders
│   │   │   ├── context_monitor.py        # PostToolUse context window tracking
│   │   │   ├── _util.py                  # Shared hook utilities
│   │   │   ├── _checkers/               # Language-specific quality checkers
│   │   │   │   ├── python.py            # ruff + pyright
│   │   │   │   ├── typescript.py        # prettier + eslint + tsc
│   │   │   │   └── go.py                # gofmt + go vet + golangci-lint
│   │   │   └── patterns/                 # Security patterns (JSON)
│   │   └── benchmark/            # Review benchmark dataset
│   │       └── review_benchmark.py      # Precision/recall/F1 metrics
│   ├── references/               # Progressive disclosure docs
│   │   ├── ARCHITECTURE.md
│   │   ├── TOKEN_MANAGEMENT.md
│   │   └── ULTRA_MINIMAL_RESULTS.md
│   └── assets/                   # Templates, configs
│       └── templates/
│           └── playground/       # HTML playground templates
│
├── ~/.claude/skills/wfc-*/      # Installed skills (Agent Skills compliant)
│   ├── wfc-review/               # Multi-agent consensus review (conditional activation)
│   ├── wfc-plan/                 # Adaptive planning (living documents)
│   ├── wfc-implement/            # Parallel implementation (post-deploy validation)
│   ├── wfc-compound/             # Knowledge codification (docs/solutions/)
│   ├── wfc-deepen/               # Post-plan research enhancement
│   ├── wfc-lfg/                  # Autonomous end-to-end pipeline
│   ├── wfc-export/               # Multi-platform skill export
│   ├── wfc-security/             # STRIDE threat analysis
│   ├── wfc-architecture/         # Architecture docs + C4 diagrams
│   ├── wfc-test/                 # Property-based test generation
│   ├── wfc-safeguard/            # Real-time security enforcement hooks
│   ├── wfc-rules/                # Markdown-based custom enforcement rules
│   ├── wfc-playground/           # Interactive HTML playground generator
│   ├── wfc-sync/                # Rule/pattern discovery & sync
│   ├── wfc-agentic/             # GitHub Agentic Workflows (gh-aw) generator
│   ├── wfc-ba/                  # Business analysis & requirements gathering
│   └── ... (28 total)
│
├── docs/                         # Documentation (organized by topic)
│   ├── architecture/             # System design, planning
│   ├── security/                 # OWASP, hooks, git safety
│   ├── workflow/                 # Install, PR workflow, build, implementation
│   ├── quality/                  # Quality gates, personas
│   ├── reference/                # Compliance, registries, EARS
│   └── examples/                 # Working demos
│
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
│   └── pre-commit.sh             # Pre-commit validation
│
├── Makefile                      # Development tasks
├── pyproject.toml                # Package configuration
└── PLANNING.md                   # Architecture & absolute rules
```

## 🔧 Development Workflow

### Essential Commands

```bash
# Setup
make install          # Install WFC with all features
make dev              # Development environment (install + hooks)
make doctor           # Run comprehensive health checks

# Testing
make test             # Run all tests
make test-coverage    # Tests with coverage report

# Validation
make validate         # Validate all WFC skills (Agent Skills compliance)
make validate-xml     # Validate XML prompt generation

# Code Quality
make lint             # Run ruff linter
make format           # Format code with black + ruff
make check-all        # Run tests + validate + lint
make quality-check    # Run Trunk.io universal quality checks

# Benchmarks
make benchmark        # Token usage benchmarks (proves 99% reduction)

# Pre-commit
make pre-commit       # Install pre-commit hooks

# WFC Commands
wfc implement                    # Multi-agent parallel implementation
wfc implement --dry-run          # Show plan without executing
wfc implement --agents 8         # Override agent count
wfc review TASK-001              # Consensus code review
wfc plan                         # Create structured plan
wfc test                         # Generate property-based tests
wfc security                     # STRIDE threat analysis
wfc architecture                 # Architecture docs + C4 diagrams
```

## 🚀 WFC:IMPLEMENT - Multi-Agent Parallel Implementation

**Status**: ✅ **COMPLETE** (Phase 1-3: 100%)

wfc-implement is a production-ready multi-agent parallel implementation engine.

### Quick Usage

```bash
# Create a plan
wfc plan

# Execute implementation
wfc implement --tasks plan/TASKS.md

# Dry run (show plan without executing)
wfc implement --dry-run
```

### Features

**Core** (Phase 1):
- ✅ **Universal Quality Gate** (Trunk.io - 100+ tools for all languages)
- ✅ **Complete TDD Workflow** (RED-GREEN-REFACTOR)
- ✅ **Merge Engine with Rollback** (main always passing)
- ✅ **CLI Interface** (dry-run, agent control, progress display)

**Intelligence** (Phase 2):
- ✅ **Confidence Checking** (≥90% proceed, 70-89% ask, <70% stop)
- ✅ **Memory System** (ReflexionMemory - learn from past mistakes)
- ✅ **Token Budgets** (S=200, M=1K, L=2.5K, XL=5K tokens)

**Polish** (Phase 3):
- ✅ **PROJECT_INDEX.json** (machine-readable structure)
- ✅ **make doctor** (comprehensive health checks)
- ✅ **Integration Tests** (>80% coverage, 22 tests)
- ✅ **Complete Documentation** (docs/workflow/WFC_IMPLEMENTATION.md)

### Architecture

```
Orchestrator → N Agents (parallel) → Quality Gate → Review → Merge → Integration Tests
```

**Workflow per Agent**:
1. UNDERSTAND (confidence check, memory search)
2. TEST_FIRST (RED phase - tests fail)
3. IMPLEMENT (GREEN phase - tests pass)
4. REFACTOR (clean up, maintain SOLID)
5. QUALITY_CHECK (Trunk.io or language-specific)
6. SUBMIT (route to consensus review)

### Key Files

- `wfc/skills/wfc-implement/orchestrator.py` - Task orchestration
- `wfc/skills/wfc-implement/agent.py` - TDD workflow
- `wfc/skills/wfc-implement/merge_engine.py` - Rollback & retry
- `wfc/scripts/confidence_checker.py` - Confidence-first pattern
- `wfc/scripts/memory_manager.py` - Cross-session learning
- `wfc/scripts/token_manager.py` - Budget optimization
- `wfc/scripts/universal_quality_checker.py` - Trunk.io integration
- `docs/workflow/WFC_IMPLEMENTATION.md` - Complete guide

### Testing

```bash
# Run integration tests
pytest tests/test_implement_integration.py -v

# Run end-to-end tests
pytest tests/test_implement_e2e.py -v

# All tests with coverage
make test-coverage
```

**Coverage**: >80% (22 tests covering all critical paths)

## 🎯 Core Architecture

### Five-Agent Consensus Review (v2.0)

**Architecture**: 5 fixed specialist reviewers with mathematical consensus scoring.

```
ReviewOrchestrator (orchestrator.py)
  ├── prepare_review(request) → 5 task specs
  │     └── ReviewerEngine.prepare_review_tasks()
  │           └── ReviewerLoader (loads from wfc/reviewers/{name}/PROMPT.md)
  │                 └── KnowledgeRetriever (optional, two-tier RAG)
  │
  └── finalize_review(request, responses, output_dir) → ReviewResult
        ├── ReviewerEngine.parse_results() → findings per reviewer
        ├── Fingerprinter.deduplicate() → DeduplicatedFindings
        ├── ConsensusScore.calculate() → CS with MPR
        └── Generate REVIEW-{task_id}.md report
```

**5 Reviewers** (`wfc/reviewers/{name}/PROMPT.md + KNOWLEDGE.md`):
- **Security**: OWASP/CWE taxonomy, hostile threat modeling
- **Correctness**: Edge cases, contract verification, type safety
- **Performance**: Big-O analysis, N+1 detection, memory profiling
- **Maintainability**: SOLID, DRY, coupling/cohesion, readability
- **Reliability**: Concurrency, error handling, chaos scenarios, resource leaks

### Consensus Score (CS) Algorithm

**Formula**: `CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)`

Where:
- `R_i = (severity * confidence) / 10` per deduplicated finding
- `R_bar` = mean of all R_i values
- `k` = total reviewer agreements (sum of duplicate counts)
- `n` = 5 (total reviewers)
- `R_max` = max(R_i) across all findings

**Decision Tiers**:
- Informational: CS < 4.0 (log only)
- Moderate: 4.0 ≤ CS < 7.0 (inline comment)
- Important: 7.0 ≤ CS < 9.0 (block merge)
- Critical: CS ≥ 9.0 (block + escalate)

**Minority Protection Rule (MPR)**: If R_max ≥ 8.5 from a security/reliability reviewer, CS is elevated to `max(CS, 0.7 * R_max + 2.0)`.

**Finding Deduplication**: SHA-256 fingerprint on `{file}:{line_start // 3}:{category}` — merges findings within ±3 lines across reviewers.

### Knowledge System (RAG-Powered)

- **KNOWLEDGE.md** per reviewer: Human-readable learning entries
- **RAG Pipeline**: Two-tier retrieval (embedding + keyword fallback)
- **Auto-Append**: `knowledge_writer.py` adds new findings after reviews
- **Drift Detection**: Detects stale (>90d), bloated (>50), contradictory, and orphaned entries

### Emergency Bypass

- 24-hour expiry with mandatory reason
- Append-only `BYPASS-AUDIT.json` audit trail
- Records CS at time of bypass for accountability

### Agent Skills Compliance

All 28 WFC skills are Agent Skills compliant:
- Valid frontmatter (only: name, description, license)
- Hyphenated names (wfc-review, not wfc-review)
- Comprehensive descriptions
- XML prompt generation
- Progressive disclosure pattern

**Validation**: `make validate` (uses skills-ref)

## 🚀 WFC Philosophy

### ELEGANT
- Simplest solution wins
- No over-engineering
- Clear, readable code

### MULTI-TIER
- Logic separated from presentation
- Reviewers (logic) vs CLI (presentation)
- Progressive disclosure (load on demand)

### PARALLEL
- True concurrent execution
- Independent subagents
- No context bleeding

### PROGRESSIVE
- Load only what's needed when needed
- SKILL.md first (< 500 lines)
- References on demand
- Scripts when executed

### TOKEN-AWARE
- Every token counts
- Measure with benchmarks
- 99% reduction target

### COMPLIANT
- Agent Skills spec enforced
- Validated with skills-ref
- XML prompts work

## ⚠️ Absolute Rules

### Token Management
- **NEVER** send full file content to reviewers
- **ALWAYS** use file reference architecture
- **ALWAYS** measure token usage with `make benchmark`
- **NEVER** exceed token budgets without justification

### Agent Skills Compliance
- **NEVER** use colons in skill names (use hyphens: `wfc-review` not `wfc-review`)
- **NEVER** include invalid frontmatter fields (`user-invocable`, `disable-model-invocation`, `argument-hint`)
- **ALWAYS** validate with skills-ref before commit (`make validate`)
- **ALWAYS** generate valid XML prompts

### Code Quality
- **ALWAYS** run `make format` before commit
- **ALWAYS** run `make check-all` before PR
- **NEVER** commit failing tests
- **NEVER** skip pre-commit hooks

### Development Workflow
- **ALWAYS** use UV for Python operations
- **ALWAYS** use Make for common tasks
- **NEVER** bypass pre-commit validation
- **ALWAYS** update tests when changing code

### Worktree Management
- **NEVER** call `git worktree add` directly — use `worktree-manager.sh`
- **ALWAYS** use the script: `bash wfc/wfc-tools/gitwork/scripts/worktree-manager.sh create <name>`
- **WHY**: Raw `git worktree add` skips .env copying, .gitignore setup, and config sync
- **ALWAYS** clean up worktrees after work: `worktree-manager.sh cleanup`

### Knowledge Codification
- **ALWAYS** run `/wfc-compound` after solving non-trivial problems
- **NEVER** skip documenting solutions that took >15 minutes to find
- **ALWAYS** include code examples (before/after) and prevention steps

## 📊 Key Metrics

**Review System**:
- 5 fixed specialist reviewers (replaced 56-persona selection system)
- CS algorithm with mathematical consensus scoring
- Minority Protection Rule for security/reliability findings
- Finding deduplication via SHA-256 fingerprinting

**Test Coverage**:
- Full suite: 830+ tests passing
- Review system: ~200 tests (engine, fingerprint, CS, CLI, E2E, benchmark)

**Agent Skills Compliance**:
- Valid skills: 28/28 (100%)
- XML generation: 28/28 (100%)

## 🔍 Quick Reference

### File Locations

**Review Orchestrator**: `wfc/scripts/skills/review/orchestrator.py`
**Reviewer Engine**: `wfc/scripts/skills/review/reviewer_engine.py`
**Consensus Score**: `wfc/scripts/skills/review/consensus_score.py`
**Fingerprinter**: `wfc/scripts/skills/review/fingerprint.py`
**Emergency Bypass**: `wfc/scripts/skills/review/emergency_bypass.py`
**Review CLI**: `wfc/scripts/skills/review/cli.py`
**Knowledge System**: `wfc/scripts/knowledge/`
**Drift Detector**: `wfc/scripts/knowledge/drift_detector.py`
**Reviewer Prompts**: `wfc/reviewers/{security,correctness,performance,maintainability,reliability}/PROMPT.md`
**Hook Infrastructure**: `wfc/scripts/hooks/pretooluse_hook.py`
**Security Patterns**: `wfc/scripts/hooks/patterns/security.json`
**Architecture Designer**: `wfc/skills/wfc-plan/architecture_designer.py`
**Playground Templates**: `wfc/assets/templates/playground/`
**Worktree Manager**: `wfc/wfc-tools/gitwork/scripts/worktree-manager.sh`
**Worktree API**: `wfc/wfc_tools/gitwork/api/worktree.py`
**Knowledge Codification**: `wfc/skills/wfc-compound/SKILL.md`
**Autonomous Pipeline**: `wfc/skills/wfc-lfg/SKILL.md`
**Plan Deepening**: `wfc/skills/wfc-deepen/SKILL.md`
**Multi-Platform Export**: `wfc/skills/wfc-export/SKILL.md`
**Installed Skills**: `~/.claude/skills/wfc-*/`

### Testing

**Run all tests**: `make test`
**Run with coverage**: `make test-coverage`
**Test specific file**: `uv run pytest tests/test_file.py -v`

### Validation

**Validate all skills**: `make validate`
**Validate XML prompts**: `make validate-xml`
**Run benchmarks**: `make benchmark`

### Code Quality

**Lint**: `make lint`
**Format**: `make format`
**Check all**: `make check-all`

## 📚 Documentation

Documentation is organized by topic in `docs/` (see `docs/README.md` for full index):

- **QUICKSTART.md** - Get started in 5 minutes
- **docs/architecture/** - System design, planning, progressive disclosure
- **docs/security/** - OWASP LLM Top 10, git safety, hooks & telemetry
- **CONTRIBUTING.md** - How to contribute
- **docs/workflow/** - PR workflow, install, build, implementation
- **docs/quality/** - Quality gates, review benchmarks
- **docs/reference/** - Agent Skills compliance, registries, EARS, Claude integration
- **docs/examples/** - Working demos and examples
- **wfc/references/TOKEN_MANAGEMENT.md** - Token optimization
- **wfc/references/ULTRA_MINIMAL_RESULTS.md** - Performance data

## 🐳 DevContainer

WFC ships a batteries-included devcontainer for end users. Drop `.devcontainer/` into any project for a full secure dev environment with WFC pre-installed.

### Quick Start

```bash
# Option A: Interactive setup (guided)
bash .devcontainer/setup.sh

# Option B: VS Code (recommended)
# 1. Copy .devcontainer/ into your project root
# 2. cp .devcontainer/.env.example .devcontainer/.env
# 3. Edit .env with your ANTHROPIC_AUTH_TOKEN
# 4. Open in VS Code → F1 → "Dev Containers: Reopen in Container"

# Option C: Docker CLI
cd .devcontainer && docker compose build && docker compose up -d
```

### What's Included

- **Python 3.12** + UV, black, ruff, pytest, mypy, pre-commit
- **Node.js LTS** + pnpm, bun, typescript, vite, eslint, prettier, tailwindcss
- **AI Tools**: Claude Code CLI, Kiro CLI, OpenCode CLI, Entire CLI (session recording)
- **GitHub CLI** (`gh`) for WFC PR workflow
- **Docker-in-Docker** (docker-ce-cli, docker-compose-plugin)
- **Dev Tools**: ripgrep, fd, fzf, bat, exa, tmux, htop, Oh My Zsh, Starship
- **Database Clients**: postgresql-client, redis-tools
- **Firewall**: iptables-based audit/enforce modes
- **VS Code Extensions**: Python, ruff, black, ESLint, Prettier, Docker, Copilot, GitLens
- **WFC Skills**: All 28 skills auto-installed via `install-universal.sh`

### Workspace Layout

```
/workspace/
├── app/        # Your project (mounted from host)
├── repos/
│   └── wfc/    # WFC framework (cloned automatically)
└── tmp/        # Persistent scratch space
```

### Firewall

```bash
# Audit mode (default): logs all traffic, doesn't block
FIREWALL_MODE=audit

# Enforce mode: blocks non-whitelisted traffic
FIREWALL_MODE=enforce

# View audit logs inside container
sudo tail -f /var/log/kern.log | grep FW-AUDIT
```

---

**This is World Fucking Class.** 🚀
