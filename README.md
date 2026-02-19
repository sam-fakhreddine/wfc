# WFC — AI-Powered Development Team in Your IDE

> **Ship better code, faster.** 5 specialist reviewers, parallel TDD agents, and real-time security enforcement—all in your IDE.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/status-production-green.svg)]()
[![Agent Skills](https://img.shields.io/badge/agent%20skills-standard-purple.svg)](https://agentskills.io)

**[Quick Start](#quick-start)** • **[Key Features](#-key-features)** • **[How It Works](#how-it-works)** • **[Installation](#installation)** • **[Documentation](docs/)**

---

## Why WFC?

**Traditional AI coding assistants give you one perspective.** WFC gives you an entire engineering team.

Instead of writing code alone, you orchestrate specialized AI agents that:
- **Build features in parallel** using TDD workflows in isolated git worktrees
- **Review your code** from 5 specialist perspectives with mathematical consensus scoring
- **Catch issues before production** with real-time security hooks and quality gates
- **Learn from patterns** across sessions to prevent recurring mistakes

**Result:** Production-quality code with systematic quality enforcement.

---

## 🚀 Key Features

### 1. Five-Agent Consensus Reviews

Every review runs 5 fixed specialist reviewers in parallel, then calculates a mathematically weighted Consensus Score (CS).

```bash
/wfc-review
```

**The 5 reviewers:**
| Reviewer | Focus |
|----------|-------|
| **Security** | OWASP Top 10, injection flaws, auth/authz, secrets |
| **Correctness** | Logic bugs, edge cases, type safety, contracts |
| **Performance** | Algorithmic complexity, N+1 queries, memory |
| **Maintainability** | Readability, SOLID/DRY, coupling, naming |
| **Reliability** | Error handling, fault tolerance, resource leaks |

**How scoring works:**
- Each finding gets a score: `R_i = (severity × confidence) / 10`
- Consensus Score: `CS = (0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)`
- Minority Protection Rule: if Security or Reliability raises a critical finding, CS is elevated regardless of consensus
- Findings are deduplicated via SHA-256 fingerprinting (±3 lines across reviewers)

**Decision tiers:**
```
CS < 4.0   → Informational (log only)
CS 4-7     → Moderate (inline comment)
CS 7-9     → Important (blocks merge)
CS ≥ 9.0   → Critical (block + escalate)
```

**Example output:**
```
✅ Overall Score: 8.2/10 - APPROVED

⚠️ Critical (3 reviewers agree):
   - SQL injection risk in user input [Security, Correctness, Reliability]
   - N+1 query detected on orders.user_id [Performance]

💡 Suggestions:
   - Consider caching for GET /api/products [Performance]
```

### 2. Parallel TDD Implementation

Execute multiple tasks simultaneously with isolated TDD agents.

```bash
/wfc-plan        # Generate structured task breakdown
/wfc-implement   # Execute with parallel agents
```

**How it works:**
- Each agent gets its own git worktree (zero contamination between tasks)
- Enforced RED → GREEN → REFACTOR workflow
- Universal quality gates (100+ tools via Trunk.io)
- Auto-merge on success, rollback on failure
- Consensus review before merging to main

**Real workflow:**
```
5 Agents in parallel:
├─ Agent 1: Setup auth system      [worktree-1]
├─ Agent 2: OAuth2 flow            [worktree-2]
├─ Agent 3: JWT token handler      [worktree-3]
├─ Agent 4: Token refresh logic    [worktree-4]
└─ Agent 5: Integration tests      [worktree-5]
    ↓
Quality checks → Consensus review → Merge → Integration tests → Main
```

### 3. Built-in Security & Best Practices

WFC mitigates **9/9** applicable OWASP LLM Top 10 risks:

- **Real-time security hooks** block dangerous operations before execution
- **Prompt injection defenses** with 94% attack surface reduction
- **Secret detection** prevents credential leaks
- **Supply chain controls** with hash-pinned dependencies
- **Multi-reviewer consensus** catches misinformation

[Full OWASP Analysis →](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)

### 4. 26 Specialized Skills

| Skill | What It Does | When To Use |
|-------|--------------|-------------|
| `wfc-build` | Quick feature builder with TDD | Single feature, need it fast |
| `wfc-review` | Five-reviewer consensus review | PR reviews, quality checks |
| `wfc-plan` | Structured task breakdown | Complex features, dependencies |
| `wfc-implement` | Parallel TDD execution | Execute structured plans |
| `wfc-security` | STRIDE threat modeling | Security audits, compliance |
| `wfc-test` | Property-based test generation | Comprehensive test coverage |
| `wfc-architecture` | C4 diagrams + ADRs | Document system design |
| `wfc-validate` | Critical thinking advisor | Validate approach before coding |

[See all 26 skills →](QUICKSTART.md#available-skills)

### 5. Progressive Disclosure Architecture

WFC loads only what's needed, when it's needed:

- **Skill prompts:** Compact metadata loaded at startup
- **Reviewer prompts:** Loaded per-review from `wfc/references/reviewers/{name}/PROMPT.md`
- **Knowledge base:** RAG-retrieved context per reviewer domain
- **Result:** Fast startup, low memory, full capability

---

## How It Works

### The Three-Phase Workflow

```
PHASE 1: PLANNING          PHASE 2: IMPLEMENTATION      PHASE 3: REVIEW
────────────────          ─────────────────────────    ───────────────
/wfc-plan                  /wfc-implement               /wfc-review
    ↓                          ↓                            ↓
TASKS.md                   Parallel Agents              5 Fixed Reviewers
PROPERTIES.md              TDD Workflows                Consensus Score
TEST-PLAN.md               Quality Gates                CS ≥ 7.0 to ship
```

**Phase 1: Smart Planning**
- Breaks features into tasks with dependency graphs (DAG)
- Defines formal properties (SAFETY, LIVENESS, PERFORMANCE)
- Creates comprehensive test strategy
- Uses EARS format (Rolls-Royce/Airbus requirements methodology)

**Phase 2: Parallel Execution**
- Up to 5 agents work simultaneously in isolated git worktrees
- Each follows strict TDD: TEST FIRST → IMPLEMENT → REFACTOR
- Universal quality checks with 100+ tools (Trunk.io)
- Automatic rollback if quality gates fail

**Phase 3: Expert Consensus**
- 5 specialist reviewers analyze in parallel
- Consensus Score with Minority Protection Rule
- Finding deduplication via SHA-256 fingerprinting
- Detailed feedback with severity and confidence levels

---

## Quick Start

### 1. Install (2 minutes)

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install.sh
```

The installer auto-detects your platform (Claude Code, Cursor, VS Code, Kiro, etc.) and sets everything up.

**Supported Platforms:** Claude Code • Kiro • OpenCode • Cursor • VS Code • Codex • Antigravity • Goose

### 2. Get Your First Review

```bash
# In your project
/wfc-review
```

That's it. WFC runs 5 specialist reviewers in parallel and returns findings with a Consensus Score.

### 3. Build a Feature

```bash
# Natural language works
"Hey Claude, use WFC to add OAuth2 login"

# Or explicit command
/wfc-build "add OAuth2 login with JWT tokens"
```

WFC will:
1. Interview you (3-5 quick questions)
2. Spawn TDD agents in isolated worktrees
3. Run quality checks and consensus review
4. Create a PR for you to review and merge

---

## Real-World Use Cases

### Use Case 1: PR Reviews with Confidence

**Before WFC:**
```
You: "Does this look good?"
AI: "Yes, looks fine!" ❌ (missed SQL injection)
```

**With WFC:**
```
You: /wfc-review

Security:       ⚠️ CRITICAL - SQL injection in line 42
Correctness:    ✅ Logic is sound
Performance:    ⚠️ N+1 query detected, add index
Maintainability:✅ Follows SOLID principles
Reliability:    ⚠️ Missing error handling for edge case

Consensus Score: 6.8/10 - CONDITIONAL APPROVE
Required fixes: SQL injection, N+1 query, error handling
```

### Use Case 2: Parallel Feature Development

**Task:** Add complete authentication system (OAuth2 + JWT + refresh tokens + tests)

```bash
/wfc-plan                    # Structured breakdown → TASKS.md
/wfc-implement --agents 5    # 5 agents working in parallel
```

5 agents work simultaneously—each with TDD, quality checks, and expert review built-in.

### Use Case 3: Security Audits

```bash
/wfc-security --stride       # STRIDE threat model
/wfc-review --properties SECURITY,SAFETY
```

WFC automatically: identifies attack vectors, checks OWASP Top 10, validates input sanitization, ensures secrets aren't hardcoded.

---

## Developer Benefits

### ⚡ **Faster Shipping**
- Parallel execution: up to 5 agents work simultaneously
- Smart planning: break complex features into parallelizable tasks
- Auto-merge: passing code goes straight to your branch

### 🛡️ **Better Quality**
- Five-reviewer consensus catches issues single reviewers miss
- 100+ quality tools run automatically (Trunk.io)
- TDD enforcement prevents "implement first, test later" technical debt

### 🔒 **Security Built-In**
- OWASP LLM Top 10 mitigations out of the box
- Real-time hooks block dangerous operations as you code
- Security specialist on every review with Minority Protection Rule

### 🧠 **Learn & Improve**
- RAG-powered knowledge base per reviewer domain
- Cross-session learning prevents recurring mistakes
- Detailed feedback explains the "why" behind every issue

### 🔧 **Framework Agnostic**
- Works with any language or framework
- Universal quality checker supports Python, JavaScript, Go, Rust, Java, and more
- Extensible with custom rules (`.wfc/rules/*.md`)

---

## Complete Skill Suite

### Core Development
- **`wfc-build`** — Quick feature builder with adaptive interview + TDD
- **`wfc-plan`** — Structured task breakdown with EARS requirements
- **`wfc-implement`** — Multi-agent parallel TDD execution engine
- **`wfc-review`** — Five-reviewer consensus code review

### Quality & Testing
- **`wfc-test`** — Property-based test generation from formal specs
- **`wfc-security`** — STRIDE threat modeling and security audits
- **`wfc-architecture`** — C4 diagrams and Architecture Decision Records
- **`wfc-observe`** — Generate observability from system properties

### Governance & Safety
- **`wfc-safeguard`** — Real-time security hooks (PreToolUse enforcement)
- **`wfc-rules`** — Custom code standards enforcement via Markdown rules
- **`wfc-safeclaude`** — Reduce approval prompts with safe command allowlist
- **`wfc-validate`** — Critical thinking advisor (7-dimension analysis)

### Workflow & Productivity
- **`wfc-vibe`** — Natural brainstorming mode with smooth transitions
- **`wfc-ba`** — Business analysis and requirements gathering
- **`wfc-retro`** — AI-powered retrospectives with metrics
- **`wfc-playground`** — Interactive HTML playgrounds for prototyping
- **`wfc-pr-comments`** — Triage and fix PR review feedback automatically
- **`wfc-sync`** — Discover patterns and sync project rules
- **`wfc-housekeeping`** — Remove dead code, stale branches, orphaned files
- **`wfc-newskill`** — Create custom WFC skills with scaffolding

[Full documentation →](QUICKSTART.md)

---

## Installation

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install.sh
```

**Supports:** Claude Code • Kiro • OpenCode • Cursor • VS Code • Codex • Antigravity • Goose

The installer:
1. Auto-detects your IDE/platform
2. Offers branding choice (SFW: "Workflow Champion" or NSFW: "World Fucking Class")
3. Installs all 26 skills to the correct location
4. Configures progressive disclosure and security hooks

**Restart your IDE** after installation to load the skills.

### Python Package (Optional)

For token optimization and CLI tools:

```bash
uv pip install -e ".[all]"
```

[Detailed installation guide →](docs/workflow/UNIVERSAL_INSTALL.md)

---

## Example Workflows

### Workflow 1: Quick Feature

```bash
"Hey Claude, add rate limiting to the API"
```

WFC will interview you (3-5 questions), spawn agents, implement with TDD, review, and create a PR.

### Workflow 2: Complex Feature with Planning

```bash
# Step 1: Validate approach
/wfc-validate "Add OAuth2 with JWT tokens and refresh flow"

# Step 2: Create structured plan
/wfc-plan
# Output: TASKS.md, PROPERTIES.md, TEST-PLAN.md

# Step 3: Execute in parallel
/wfc-implement --agents 5
# 5 agents work simultaneously, each with TDD workflow

# Step 4: Final review
/wfc-review
```

### Workflow 3: Security Audit

```bash
/wfc-security --stride
# Generates: THREAT-MODEL.md with attack vectors

/wfc-review --properties SECURITY,SAFETY
# Security reviewer's findings trigger Minority Protection Rule
```

### Workflow 4: PR Review

```bash
# Before merging any PR
/wfc-review

# Or review specific files
/wfc-review src/auth.py src/handlers.py
```

---

## Technical Highlights

### Five Fixed Specialist Reviewers

All reviews use the same 5 reviewers every time—no randomness, no selection:

| Reviewer | Located at |
|----------|------------|
| Security | `wfc/references/reviewers/security/PROMPT.md` |
| Correctness | `wfc/references/reviewers/correctness/PROMPT.md` |
| Performance | `wfc/references/reviewers/performance/PROMPT.md` |
| Maintainability | `wfc/references/reviewers/maintainability/PROMPT.md` |
| Reliability | `wfc/references/reviewers/reliability/PROMPT.md` |

Each reviewer has a `KNOWLEDGE.md` that grows via RAG-powered auto-append after each review.

### Consensus Score (CS) Algorithm

```
CS = (0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)

Where:
  R_i  = (severity × confidence) / 10  per deduplicated finding
  R̄    = mean of all R_i values
  k    = total reviewer agreements
  n    = 5 (total reviewers)
  R_max = max(R_i) across all findings

Minority Protection Rule:
  If R_max ≥ 8.5 from Security or Reliability:
    CS = max(CS, 0.7 × R_max + 2.0)
```

### EARS Requirements Format

WFC uses the aerospace industry's EARS format for unambiguous, testable requirements:

- **UBIQUITOUS:** `The system shall <action>`
- **EVENT_DRIVEN:** `WHEN <trigger>, system shall <action>`
- **STATE_DRIVEN:** `WHILE <state>, system shall <action>`
- **UNWANTED:** `IF <condition>, THEN system shall <action>`

[EARS documentation →](docs/reference/EARS.md)

### Key Metrics

- **5** fixed specialist reviewers
- **26** WFC skills
- **5** max parallel implementation agents
- **100+** quality tools (Trunk.io)
- **8+** platform support
- **>80%** test coverage

---

## Platform Compatibility

WFC implements the [Agent Skills specification](https://agentskills.io) for universal compatibility:

- **Claude Code** — Primary platform
- **Kiro** — AWS AI coding assistant
- **OpenCode** — OpenAI coding assistant
- **Cursor** — VS Code fork with AI
- **VS Code** — With AI extensions
- **Codex** — GitHub Copilot environment
- **Antigravity** — AI pair programmer
- **Goose** — CLI-based AI assistant

The installer handles everything automatically—just run `./install.sh`.

---

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** — Get running in 5 minutes
- **[Architecture Overview](docs/architecture/ARCHITECTURE.md)** — System design and principles
- **[Security Guide](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)** — OWASP LLM Top 10 coverage
- **[EARS Requirements](docs/reference/EARS.md)** — Requirements methodology
- **[Contributing Guide](CONTRIBUTING.md)** — How to contribute
- **[Examples](docs/examples/)** — Working examples and demos

---

## Architecture Principles

**ELEGANT** — Simplest solution wins, no over-engineering

**PARALLEL** — True concurrent execution with isolated agents

**MULTI-TIER** — Separation of presentation, logic, data, and config

**TOKEN-AWARE** — Progressive disclosure: load only what's needed

**SECURE** — OWASP LLM Top 10 mitigations built-in

**SOLID** — Single responsibility, open/closed, dependency inversion

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas:
- Improve reviewer prompts and knowledge bases
- Create custom skills
- Improve quality checkers
- Extend platform support
- Write documentation and examples

---

## Acknowledgments

Built on [Claude Code](https://claude.ai/code)'s agent framework.

Inspired by ensemble methods in machine learning and the wisdom of diverse expert panels.

Special thanks to [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework) for pioneering multi-agent patterns—their confidence-first approach and orchestration patterns heavily influenced WFC's architecture.

---

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**Ready to ship better code, faster?**

[Get Started →](QUICKSTART.md) • [Read the Docs →](docs/) • [See Examples →](docs/examples/)

</div>
