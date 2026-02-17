# WFC — AI-Powered Development Team in Your IDE

> **Ship better code, faster.** 56 expert AI agents work in parallel to build, review, and secure your code—while you stay in flow.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/status-production-green.svg)]()
[![Agent Skills](https://img.shields.io/badge/agent%20skills-standard-purple.svg)](https://agentskills.io)

**[Quick Start](#quick-start)** • **[Key Features](#-key-features)** • **[How It Works](#how-it-works)** • **[Installation](#installation)** • **[Documentation](docs/)**

---

## Why WFC?

**Traditional AI coding assistants give you one perspective.** WFC gives you an entire engineering team.

Instead of writing code alone, you orchestrate 56 specialized AI agents who:
- **Build features in parallel** using TDD workflows in isolated environments
- **Review your code** from security, performance, architecture, and quality perspectives
- **Catch issues before production** with multi-expert consensus (not just one opinion)
- **Learn from patterns** across sessions to prevent recurring mistakes

**Result:** Production-quality code with systematic quality enforcement, delivered faster.

---

## 🚀 Key Features

### 1. Multi-Agent Consensus Reviews

Get your code reviewed by 5 specialized experts—automatically selected from a pool of 56.

```bash
/wfc-review
```

**What happens:**
- Automatically detects your tech stack (Python? React? Go?)
- Selects 5 relevant experts (e.g., AppSec, Backend Engineer, Performance Tester)
- Runs parallel independent reviews with weighted consensus
- Returns actionable feedback with severity scoring

**Example Output:**
```
✅ Overall Score: 8.5/10 - APPROVED

✅ Consensus (4/5 agree):
   - Clean architecture, well-structured
   - Database queries optimized
   - Security best practices followed

⚠️ Critical Issues:
   - SQL injection risk in user input (AppSec Specialist)
   - Missing index on orders.user_id (DB Architect)

💡 Unique Insights:
   - Consider caching for GET requests (Performance Tester)
```

### 2. Parallel TDD Implementation

Execute multiple tasks simultaneously with isolated TDD agents.

```bash
/wfc-plan        # Generate structured task breakdown
/wfc-implement   # Execute with parallel agents
```

**How it works:**
- Each agent gets its own git worktree (zero contamination)
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
Quality checks → Review → Merge → Integration tests → Main
```

### 3. Built-in Security & Best Practices

WFC mitigates **9/9** applicable OWASP LLM Top 10 risks:

- **Real-time security hooks** block dangerous operations before execution
- **Prompt injection defenses** with 94% attack surface reduction
- **Secret detection** prevents credential leaks
- **Supply chain controls** with hash-pinned dependencies
- **Multi-agent consensus** detects misinformation

[Full OWASP Analysis →](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)

### 4. 17 Specialized Skills

| Skill | What It Does | When To Use |
|-------|--------------|-------------|
| `wfc-build` | Quick feature builder with TDD | Single feature, need it fast |
| `wfc-review` | Multi-expert consensus review | PR reviews, quality checks |
| `wfc-plan` | Structured task breakdown | Complex features, dependencies |
| `wfc-implement` | Parallel TDD execution | Execute structured plans |
| `wfc-security` | STRIDE threat modeling | Security audits, compliance |
| `wfc-test` | Property-based test generation | Comprehensive test coverage |
| `wfc-architecture` | C4 diagrams + ADRs | Document system design |
| `wfc-validate` | Critical thinking advisor | Validate approach before coding |

[See all 19 skills →](QUICKSTART.md#available-skills)

### 5. 92% Faster with Progressive Disclosure

WFC uses progressive disclosure architecture to load only what you need:

- **Traditional context loading:** 43,000 tokens, slow
- **WFC:** 3,400 tokens, 10x faster, 90% less memory

Only full persona details are fetched when experts are selected. Everything else stays lazy-loaded.

---

## How It Works

### The Three-Phase Workflow

```
PHASE 1: PLANNING          PHASE 2: IMPLEMENTATION      PHASE 3: REVIEW
────────────────          ─────────────────────────    ───────────────
/wfc-plan                  /wfc-implement               /wfc-review
    ↓                          ↓                            ↓
TASKS.md                   5 Parallel Agents            5 Expert Reviews
PROPERTIES.md              TDD Workflows                Consensus Decision
TEST-PLAN.md               Quality Gates                Score ≥ 7.0 to ship
```

**Phase 1: Smart Planning**
- Breaks features into tasks with dependency graphs (DAG)
- Defines formal properties (SAFETY, LIVENESS, PERFORMANCE)
- Creates comprehensive test strategy
- Uses EARS format (Rolls-Royce/Airbus requirements methodology)

**Phase 2: Parallel Execution**
- Up to 5 agents work simultaneously in isolated git worktrees
- Each follows strict TDD: TEST FIRST → IMPLEMENT → REFACTOR
- Universal quality checks with 100+ tools
- Automatic rollback if quality gates fail

**Phase 3: Expert Consensus**
- Auto-selects 5 most relevant experts from 56-person panel
- Weighted scoring: Security 35%, Code Review 30%, Performance 20%, Complexity 15%
- All experts must pass (≥7/10), no critical issues
- Detailed feedback with severity levels

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

That's it. WFC will analyze your code and return expert feedback from 5 specialized reviewers.

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
3. Run quality checks and expert reviews
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

Security Expert: ⚠️ CRITICAL - SQL injection in line 42
Backend Expert: ✅ Logic is sound
Performance Expert: ⚠️ N+1 query detected, add index
Architecture Expert: ✅ Follows SOLID principles
Code Reviewer: ⚠️ Missing error handling for edge case

Overall: 6.8/10 - CONDITIONAL APPROVE
Required fixes: SQL injection, N+1 query, error handling
```

### Use Case 2: Parallel Feature Development

**Task:** Add complete authentication system (OAuth2 + JWT + refresh tokens + tests)

**Traditional approach:** 4-8 hours sequential work

**With WFC:**
```bash
/wfc-plan                    # 2 minutes - structured breakdown
/wfc-implement --agents 5    # 45 minutes - 5 agents working in parallel
```

5 agents work simultaneously:
- Agent 1: Database schema + migrations
- Agent 2: OAuth2 authorization flow
- Agent 3: JWT token generation/validation
- Agent 4: Refresh token rotation
- Agent 5: Integration tests + security tests

All with TDD, quality checks, and expert reviews built-in.

### Use Case 3: Security Audits

```bash
/wfc-security --stride       # STRIDE threat model
/wfc-review --properties SECURITY,SAFETY
```

WFC automatically:
- Identifies attack vectors
- Reviews authentication/authorization
- Checks for common vulnerabilities (OWASP Top 10)
- Validates input sanitization
- Ensures secrets aren't hardcoded

---

## Developer Benefits

### ⚡ **Faster Shipping**
- Parallel execution: 5 agents work simultaneously
- Smart planning: Break complex features into parallelizable tasks
- Auto-merge: Passing code goes straight to your branch

### 🛡️ **Better Quality**
- Multi-expert consensus catches issues single reviewers miss
- 100+ quality tools run automatically (Trunk.io)
- TDD enforcement prevents "implement first, test later" technical debt

### 🔒 **Security Built-In**
- OWASP LLM Top 10 mitigations out of the box
- Real-time hooks block dangerous operations
- Security experts on every review

### 🧠 **Learn & Improve**
- Cross-session learning prevents recurring mistakes
- Pattern detection suggests systematic improvements
- Detailed feedback explains the "why" behind issues

### 🔧 **Framework Agnostic**
- Works with any language or framework
- Universal quality checker supports Python, JavaScript, Go, Rust, Java, etc.
- Extensible with custom personas and rules

---

## Complete Skill Suite

### Core Development
- **`wfc-build`** — Quick feature builder with adaptive interview + TDD
- **`wfc-plan`** — Structured task breakdown with EARS requirements
- **`wfc-implement`** — Multi-agent parallel TDD execution engine
- **`wfc-review`** — Multi-expert consensus code review

### Quality & Testing
- **`wfc-test`** — Property-based test generation from formal specs
- **`wfc-security`** — STRIDE threat modeling and security audits
- **`wfc-architecture`** — C4 diagrams and Architecture Decision Records
- **`wfc-observe`** — Generate observability from system properties

### Governance & Safety
- **`wfc-safeguard`** — Real-time security hooks (PreToolUse enforcement)
- **`wfc-rules`** — Custom code standards enforcement
- **`wfc-safeclaude`** — Reduce approval prompts with safe command allowlist
- **`wfc-validate`** — Critical thinking advisor (7-dimension analysis)

### Workflow & Productivity
- **`wfc-vibe`** — Natural brainstorming mode with smooth transitions
- **`wfc-retro`** — AI-powered retrospectives with metrics
- **`wfc-playground`** — Interactive HTML playgrounds for prototyping
- **`wfc-pr-comments`** — Triage & fix PR review feedback automatically
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
3. Installs all 19 skills to the correct location
4. Sets up progressive disclosure (92% token reduction)

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
# Auto-selects security experts for focused review
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

### 56 Expert Personas

| Domain | Count | Examples |
|--------|-------|----------|
| **Engineering** | 11 | Python, Node, Go, Rust, React, iOS, Android |
| **Security** | 8 | AppSec, PenTest, Cloud Security, Compliance |
| **Architecture** | 7 | Solutions, APIs, Microservices, Event-Driven |
| **Quality** | 10 | Performance, Load Testing, Code Review, A11y |
| **Data** | 4 | SQL, NoSQL, Data Engineering, ML |
| **Product** | 3 | Developer Experience, Technical PM |
| **Operations** | 4 | SRE, Platform, DevOps, Observability |
| **Domain** | 5 | Fintech, Healthcare, E-commerce, Gaming |
| **Specialists** | 4 | WCAG, Performance Optimization, i18n |

[Full persona library →](docs/quality/PERSONAS.md)

### Progressive Disclosure Architecture

- **Traditional loading:** 43,000 tokens, slow startup
- **WFC:** 3,400 tokens (92% reduction), 10x faster
- **How:** Load summaries first, fetch details only when needed
- **Result:** 90% less memory usage, instant startup

### EARS Requirements Format

WFC uses the aerospace industry's EARS (Easy Approach to Requirements Syntax) for unambiguous, testable requirements:

- **UBIQUITOUS:** `The system shall <action>`
- **EVENT_DRIVEN:** `WHEN <trigger>, system shall <action>`
- **STATE_DRIVEN:** `WHILE <state>, system shall <action>`
- **OPTIONAL:** `WHERE <feature>, system shall <action>`
- **UNWANTED:** `IF <condition>, THEN system shall <action>`

[EARS documentation →](docs/reference/EARS.md)

### Performance Metrics

- **56** expert personas
- **5** max parallel agents
- **92%** token reduction
- **100+** quality tools (Trunk.io)
- **8+** platform support
- **>80%** test coverage

---

## Platform Compatibility

WFC implements the [Agent Skills specification](https://agentskills.io) for universal compatibility across AI coding assistants:

**Supported Platforms:**
- **Claude Code** — Primary platform
- **Kiro** — AWS AI coding assistant
- **OpenCode** — OpenAI coding assistant
- **Cursor** — VS Code fork with AI
- **VS Code** — With AI extensions
- **Codex** — GitHub Copilot environment
- **Antigravity** — AI pair programmer
- **Goose** — CLI-based AI assistant

The installer handles everything automatically—just run `./install.sh` and it detects your setup.

---

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** — Get running in 5 minutes
- **[Architecture Overview](docs/architecture/ARCHITECTURE.md)** — System design and principles
- **[Persona Library](docs/quality/PERSONAS.md)** — All 56 expert reviewers
- **[Security Guide](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)** — OWASP LLM Top 10 coverage
- **[EARS Requirements](docs/reference/EARS.md)** — Requirements methodology
- **[Contributing Guide](CONTRIBUTING.md)** — How to contribute
- **[Examples](docs/examples/)** — Working examples and demos

---

## Architecture Principles

**ELEGANT** — Simplest solution wins, no over-engineering

**PARALLEL** — True concurrent execution with isolated agents

**MULTI-TIER** — Separation of presentation, logic, data, and config

**TOKEN-AWARE** — 92% reduction through progressive disclosure

**SECURE** — OWASP LLM Top 10 mitigations built-in

**SOLID** — Single responsibility, open/closed, dependency inversion

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas:
- Add new expert personas
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
