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
1. Plan → 2. Build/Implement → 3. Review → 4. User Pushes
```

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
# Step 1: Create structured plan
/wfc-plan

# Step 2: Execute plan with parallel agents
/wfc-implement

# Step 3: Final review (if not already done per-task)
/wfc-review
```

**Use when:**
- Large feature with multiple tasks
- Complex dependencies
- Need formal properties (SAFETY, LIVENESS, etc.)

### Git Workflow Policy (v2.0 - PR-First)

**Versioning:** Use autosemver for automatic semantic versioning (BREAKING CHANGES, feat:, fix:)

**NEW DEFAULT**: WFC creates GitHub PRs for team collaboration.

```
WFC workflow (NEW):
  Build/Plan → Implement → Quality → Review → Push Branch → Create GitHub PR
                                                                    ↓
                                                          [WFC STOPS HERE]
                                                                    ↓
                                            You review PR and merge via GitHub
```

**What Changed:**
- ✅ **NEW**: Pushes feature branches to remote
- ✅ **NEW**: Creates GitHub PRs automatically
- ✅ **UNCHANGED**: Never pushes to main/master
- ✅ **UNCHANGED**: User controls final merge (via GitHub)
- ✅ **LEGACY**: Direct local merge still available (config: `"merge.strategy": "direct"`)

**Why PR Workflow:**
- ✅ Team collaboration (PR reviews)
- ✅ CI/CD integration (GitHub Actions)
- ✅ Audit trail (GitHub history)
- ✅ Branch protection (required reviews)
- ✅ Modern workflow (industry standard)

### When to Use Which Skill

| Task | Skill | Why |
|------|-------|-----|
| Brainstorming | **default mode** | wfc-vibe: natural chat, transitions when ready |
| New feature (small) | `/wfc-build` | Intentional Vibe - fast iteration |
| New feature (large) | `/wfc-plan` + `/wfc-implement` | Structured approach |
| Code review | `/wfc-review` | Multi-agent consensus |
| Security audit | `/wfc-security` | STRIDE threat modeling |
| Architecture docs | `/wfc-architecture` | C4 diagrams + ADRs |
| Generate tests | `/wfc-test` | Property-based tests |
| Add monitoring | `/wfc-observe` | Observability from properties |
| Validate idea | `/wfc-isthissmart` | 7-dimension analysis |
| Security hooks | `/wfc-safeguard` | Real-time pattern enforcement |
| Custom rules | `/wfc-rules` | Markdown-based code standards |
| Visual exploration | `/wfc-playground` | Interactive HTML prototyping |
| Fix PR comments | `/wfc-pr-comments` | Triage & fix review feedback |
| Agentic workflows | `/wfc-agentic` | Generate gh-aw workflows |

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
│   ├── scripts/                  # Executable code
│   │   ├── personas/             # Persona system
│   │   │   ├── persona_executor.py       # Prepare subagent tasks
│   │   │   ├── persona_orchestrator.py   # Select personas
│   │   │   ├── token_manager.py          # Token optimization (99% reduction)
│   │   │   ├── ultra_minimal_prompts.py  # 200-token prompts
│   │   │   └── file_reference_prompts.py # File refs not content
│   │   ├── hooks/                # Hook infrastructure
│   │   │   ├── pretooluse_hook.py        # PreToolUse hook handler
│   │   │   ├── security_hook.py          # Security enforcement
│   │   │   ├── rule_engine.py            # Custom rule engine
│   │   │   ├── config_loader.py          # Hook configuration
│   │   │   ├── hook_state.py             # Hook state management
│   │   │   └── patterns/                 # Security patterns (JSON)
│   │   └── skills/               # Skill implementations
│   │       └── review/
│   │           ├── orchestrator.py       # Review workflow
│   │           ├── consensus.py          # Consensus algorithm
│   │           └── agents.py             # Agent logic
│   ├── references/               # Progressive disclosure docs
│   │   ├── personas/             # 56 expert personas (JSON)
│   │   ├── ARCHITECTURE.md
│   │   ├── TOKEN_MANAGEMENT.md
│   │   └── ULTRA_MINIMAL_RESULTS.md
│   └── assets/                   # Templates, configs
│       └── templates/
│           └── playground/       # HTML playground templates
│
├── ~/.claude/skills/wfc-*/      # Installed skills (Agent Skills compliant)
│   ├── wfc-review/               # Multi-agent consensus review
│   ├── wfc-plan/                 # Adaptive planning
│   ├── wfc-implement/            # Parallel implementation
│   ├── wfc-security/             # STRIDE threat analysis
│   ├── wfc-architecture/         # Architecture docs + C4 diagrams
│   ├── wfc-test/                 # Property-based test generation
│   ├── wfc-safeguard/            # Real-time security enforcement hooks
│   ├── wfc-rules/                # Markdown-based custom enforcement rules
│   ├── wfc-playground/           # Interactive HTML playground generator
│   ├── wfc-agentic/             # GitHub Agentic Workflows (gh-aw) generator
│   └── ... (18 total)
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
│   ├── benchmark_tokens.py       # Token usage benchmarks
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

- `wfc/skills/implement/orchestrator.py` - Task orchestration
- `wfc/skills/implement/agent.py` - TDD workflow
- `wfc/skills/implement/merge_engine.py` - Rollback & retry
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

### Token Management (99% Reduction)

**TokenBudgetManager** (`wfc/scripts/personas/token_manager.py`):
- Accurate token counting with tiktoken
- Smart file condensing when needed
- Budget: 150k total, 1k system prompt, 138k code files

**Ultra-Minimal Prompts** (`wfc/scripts/personas/ultra_minimal_prompts.py`):
- 200 tokens per persona (was 3000)
- No verbose backstories
- Trust LLM to be expert

**File Reference Architecture** (`wfc/scripts/personas/file_reference_prompts.py`):
- Send paths, not content
- Domain-focused guidance (what to look for)
- Non-prescriptive (no explicit grep patterns)

**Result**: 150k tokens → 1.5k tokens (99% reduction)

### Persona System

**PersonaReviewExecutor** (`wfc/scripts/personas/persona_executor.py`):
1. Builds persona-specific system prompts
2. Prepares task specifications
3. Returns them for Claude Code to execute via Task tool

**PersonaOrchestrator** (`wfc/scripts/personas/persona_orchestrator.py`):
- Selects 5 relevant experts from 56 reviewers
- Uses semantic matching (file types, properties, context)
- Diversity scoring ensures varied perspectives

**56 Expert Personas** (`wfc/references/personas/panels/`):
- Security specialists (AppSec, CloudSec, CryptoSec, etc.)
- Architecture experts (Distributed, Microservices, etc.)
- Performance specialists (Backend, Frontend, Database, etc.)
- Quality experts (Testing, Observability, Documentation, Silent Failure Hunter, Code Simplifier, etc.)

### Consensus Algorithm

**WeightedConsensus** (`wfc/scripts/skills/review/consensus.py`):
- Security: 35% (highest priority)
- Code Review: 30% (correctness)
- Performance: 20% (scalability)
- Complexity: 15% (maintainability)

**Rules**:
1. All agents must pass (score ≥ 7/10)
2. Overall score = weighted average
3. Any critical severity = automatic fail
4. Overall score ≥ 7.0 required to pass

### Agent Skills Compliance

All 17 WFC skills are Agent Skills compliant:
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
- Personas (logic) vs CLI (presentation)
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
- **NEVER** send full file content to personas
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

## 📊 Key Metrics

**Token Reduction**:
- Legacy: 150,000 tokens (full code content)
- WFC: 1,500 tokens (paths + ultra-minimal prompts)
- Reduction: 99%

**Persona Prompts**:
- Legacy: 3,000 tokens per persona
- WFC: 200 tokens per persona
- Reduction: 93%

**Agent Skills Compliance**:
- Valid skills: 17/17 (100%)
- XML generation: 17/17 (100%)

## 🔍 Quick Reference

### File Locations

**Token Management**: `wfc/scripts/personas/token_manager.py`
**Ultra-Minimal Prompts**: `wfc/scripts/personas/ultra_minimal_prompts.py`
**File References**: `wfc/scripts/personas/file_reference_prompts.py`
**Persona Executor**: `wfc/scripts/personas/persona_executor.py`
**Persona Orchestrator**: `wfc/scripts/personas/persona_orchestrator.py`
**Review Orchestrator**: `wfc/scripts/skills/review/orchestrator.py`
**Consensus Algorithm**: `wfc/scripts/skills/review/consensus.py`
**Hook Infrastructure**: `wfc/scripts/hooks/pretooluse_hook.py`
**Security Patterns**: `wfc/scripts/hooks/patterns/security.json`
**Architecture Designer**: `wfc/skills/wfc-plan/architecture_designer.py`
**Playground Templates**: `wfc/assets/templates/playground/`
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
- **docs/quality/** - Quality gates, personas (56 experts)
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
- **WFC Skills**: All 17 skills auto-installed via `install-universal.sh`

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
