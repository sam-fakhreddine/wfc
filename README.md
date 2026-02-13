# WFC — MULTI-AGENT DEVELOPMENT FRAMEWORK

**VERSION:** 2.0.0
**PARADIGM:** LATE MODERN COMPUTING
**UPDATED:** 2026-02-12

---

```
┌─────────────────────────────────────────────────────────────────┐
│  WORLD FUCKING CLASS                                            │
│  56 Expert AI Agents • Parallel Execution • 92% Token Reduction│
└─────────────────────────────────────────────────────────────────┘
```

**STATUS:** PRODUCTION
**PLATFORM:** Agent Skills Standard
**LICENSE:** MIT

[Installation](#02-installation) • [Workflow](#01-the-workflow) • [Documentation](#07-documentation)

---

## 00. SYSTEM OVERVIEW

### Traditional Development Model

```
DEVELOPER [1]
    ↓
SEQUENTIAL EXECUTION
    ↓
SINGLE PERSPECTIVE
    ↓
LATE DISCOVERY OF CRITICAL ISSUES
```

### WFC Architecture

```
ENGINEERING TEAM [56 SPECIALISTS]
    ↓
PARALLEL TDD AGENTS [UP TO 5 CONCURRENT]
    ↓
MULTI-EXPERT CONSENSUS REVIEW
    ↓
SYSTEMATIC QUALITY ENFORCEMENT
```

**AGENT PANELS:**

| DOMAIN       | COUNT | SPECIALIZATIONS                              |
|:-------------|------:|:---------------------------------------------|
| ENGINEERING  |    11 | Python, Node, Go, Rust, React, iOS, Android  |
| SECURITY     |     8 | AppSec, PenTest, Cloud Security, Compliance  |
| ARCHITECTURE |     7 | Solutions, APIs, Microservices, Event-Driven |
| QUALITY      |    10 | Performance, Load Testing, Code Review, A11y |
| DATA         |     4 | SQL, NoSQL, Data Engineering, ML             |
| PRODUCT      |     3 | Developer Experience, Technical PM           |
| OPERATIONS   |     4 | SRE, Platform, DevOps, Observability         |
| DOMAIN       |     5 | Fintech, Healthcare, E-commerce, Gaming      |
| SPECIALISTS  |     4 | WCAG, Performance Optimization, i18n         |
| **TOTAL**    |**56** | **READY TO WORK**                            |

---

## 01. THE WORKFLOW

```
PHASE 1          PHASE 2              PHASE 3
───────────────  ─────────────────    ──────────────
PLANNING         IMPLEMENTATION       REVIEW
    ↓                ↓                    ↓
TASKS.md         5 TDD AGENTS         5 EXPERTS
PROPERTIES.md    PARALLEL             CONSENSUS
TEST-PLAN.md     WORKTREES            DECISION
    ↓                ↓                    ↓
EARS FORMAT      QUALITY GATES        APPROVE/REVISE
DAG STRUCTURE    AUTO MERGE           SCORE ≥ 7.0
```

### PHASE 1: PLANNING

**COMMAND:** `/wfc-plan`

**OUTPUT:**
- `TASKS.md` — Task breakdown with dependencies (DAG)
- `PROPERTIES.md` — Formal properties (SAFETY, LIVENESS, PERFORMANCE)
- `TEST-PLAN.md` — Complete test strategy

**STANDARD:** EARS format (Rolls-Royce/Airbus requirements methodology)

**FEATURES:**
- Property-based test derivation
- Dependency graph validation
- Complexity-based agent assignment

### PHASE 2: IMPLEMENTATION

**COMMAND:** `/wfc-implement`

**PROCESS:**

```
ORCHESTRATOR
    ├─ AGENT 1 [worktree-1] → TASK-001
    ├─ AGENT 2 [worktree-2] → TASK-002
    ├─ AGENT 3 [worktree-3] → TASK-003
    ├─ AGENT 4 [worktree-4] → TASK-004
    └─ AGENT 5 [worktree-5] → TASK-005

EACH AGENT WORKFLOW:
    UNDERSTAND
        ↓
    TEST FIRST [RED]
        ↓
    IMPLEMENT [GREEN]
        ↓
    REFACTOR
        ↓
    QUALITY CHECK [TRUNK.IO]
        ↓
    SUBMIT → REVIEW
```

**ISOLATION:** Git worktrees (parallel execution, zero contamination)
**QUALITY:** 100+ tools via Trunk.io universal checker
**OUTCOME:** Merge to main OR automatic rollback on failure

### PHASE 3: REVIEW

**COMMAND:** `/wfc-review`

**MECHANISM:**

```
INPUT: Code + Context + Properties
    ↓
SELECTOR: Auto-picks 5 from 56 experts
    ↓
REVIEW: Independent parallel analysis
    ↓
CONSENSUS: Weighted voting algorithm
    ↓
DECISION: [SCORE ≥ 7.0] + [NO CRITICALS] = SHIP
```

**WEIGHTING:**
- Security: 35%
- Code Review: 30%
- Performance: 20%
- Complexity: 15%

**SELECTION EXAMPLE:**

```
CONTEXT: OAuth2 + JWT Implementation

TECH: Python, FastAPI, PostgreSQL, Redis
FILES: auth_service.py, jwt_handler.py
PROPERTIES: SECURITY, SAFETY

SELECTED PANEL:
├─ APPSEC_SPECIALIST      [0.95] OAuth/JWT security
├─ BACKEND_PYTHON_SENIOR  [0.88] FastAPI patterns
├─ API_SECURITY_SPECIALIST[0.82] Token security
├─ DB_ARCHITECT_SQL       [0.72] Secure storage
└─ SRE_SPECIALIST         [0.61] Key rotation

DECISION: CONDITIONAL APPROVE
REQUIRED:
├─ Fix PII in JWT payload
└─ Add token rotation mechanism
```

---

## 02. INSTALLATION

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install.sh
```

**UNIVERSAL INSTALLER** — Auto-detects platform:

| PLATFORM      | INSTALL PATH              | STATUS |
|:--------------|:--------------------------|:-------|
| Claude Code   | `~/.claude/skills`        | ✓      |
| Kiro (AWS)    | `~/.kiro/skills`          | ✓      |
| OpenCode      | `~/.opencode/skills`      | ✓      |
| Cursor        | `~/.cursor/skills`        | ✓      |
| VS Code       | `~/.vscode/skills`        | ✓      |
| Codex         | `~/.codex/skills`         | ✓      |
| Antigravity   | `~/.antigravity/skills`   | ✓      |
| Goose         | `~/.config/goose/skills`  | ✓      |

**BRANDING MODES:**

```
SFW  [Safe For Work] → Workflow Champion      [Professional]
NSFW [Default]       → World Fucking Class    [No Bullshit]
```

[Branding Documentation](docs/BRANDING.md)

---

## 03. SKILL SUITE

| SKILL              | PURPOSE                       | OUTPUT                               |
|:-------------------|:------------------------------|:-------------------------------------|
| `wfc-vibe`         | Natural brainstorming mode    | Smooth transitions to planning       |
| `wfc-build`        | Quick feature builder         | Implemented feature on local main    |
| `wfc-plan`         | Structured task breakdown     | TASKS.md, PROPERTIES.md, TEST-PLAN.md|
| `wfc-implement`    | Parallel TDD execution        | Merged code or rollback              |
| `wfc-review`       | Multi-expert consensus        | Review report, score, decision       |
| `wfc-test`         | Property-based test generation| Test files with formal verification  |
| `wfc-security`     | STRIDE threat modeling        | THREAT-MODEL.md                      |
| `wfc-architecture` | C4 diagrams and ADRs          | ARCHITECTURE.md, diagrams            |
| `wfc-observe`      | Observability from properties | Metrics, alerts, dashboards          |
| `wfc-retro`        | AI-powered retrospectives     | Performance analysis, recommendations|
| `wfc-safeclaude`   | Safe command allowlist        | .claude/settings.local.json          |
| `wfc-isthissmart`  | Critical thinking advisor     | 7-dimension analysis                 |
| `wfc-newskill`     | Create new WFC skills         | Skill scaffolding                    |
| `wfc-safeguard`    | Real-time security hooks      | PreToolUse enforcement               |
| `wfc-rules`        | Custom enforcement rules      | Markdown-based rule enforcement      |
| `wfc-playground`   | Interactive HTML playgrounds  | Design/data/concept templates        |

---

## 04. TECHNICAL SPECIFICATIONS

### 4.1 Progressive Disclosure

```
TRADITIONAL CONTEXT LOADING:
├─ Initial load: ~43,000 tokens
├─ Load time: Slow
└─ Memory usage: High

WFC ARCHITECTURE:
├─ Initial load: ~3,400 tokens [92.1% reduction]
├─ Load time: Fast [10x improvement]
└─ Memory usage: Low [90% reduction]

MECHANISM:
LOAD SUMMARIES ONLY [IDs + descriptions]
    ↓
ON EXPERT SELECTION
    ↓
FETCH FULL PERSONA DETAILS
    ↓
CACHE FOR SESSION
```

### 4.2 EARS Requirements Format

Five templates for unambiguous, testable requirements:

| TYPE         | TEMPLATE                                      | USE CASE              |
|:-------------|:----------------------------------------------|:----------------------|
| UBIQUITOUS   | `The system shall <action>`                   | Always active         |
| EVENT_DRIVEN | `WHEN <trigger>, system shall <action>`       | Event response        |
| STATE_DRIVEN | `WHILE <state>, system shall <action>`        | Continuous condition  |
| OPTIONAL     | `WHERE <feature>, system shall <action>`      | Conditional capability|
| UNWANTED     | `IF <condition>, THEN system shall <action>`  | Constraint/prevention |

[EARS Documentation](docs/EARS.md)

### 4.3 Performance Metrics

| METRIC                    | VALUE  |
|:--------------------------|-------:|
| Expert personas           | 56     |
| Max parallel agents       | 5      |
| Token reduction           | 92%    |
| Quality tools (Trunk.io)  | 100+   |
| Platform support          | 8+     |
| Test coverage             | >80%   |

### 4.4 OWASP LLM Top 10 Coverage

WFC mitigates **9/9 applicable risks** from the [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/):

| Risk | Defense |
|---|---|
| Prompt Injection | 94% prompt surface reduction + JSON schema + real-time hook blocking |
| Sensitive Info Disclosure | Secret pattern detection + file path refs (not content) + prompt caps |
| Supply Chain | Hash-pinned uv.lock + zero runtime dependencies |
| Data Poisoning | Schema-validated personas + enabled gating + trusted sources only |
| Improper Output Handling | Confidence filtering + JSON parse fallback + path validation |
| Excessive Agency | PreToolUse hooks + tool allowlists + PR-only workflow |
| System Prompt Leakage | Ultra-minimal prompts (200 tokens) + no secrets in prompts |
| Misinformation | Multi-agent consensus (4-5 reviewers) + divergence detection |
| Unbounded Consumption | 150K token hard budget + adaptive condensing + model tiers |

Full analysis: [docs/OWASP_LLM_TOP10_MITIGATIONS.md](docs/OWASP_LLM_TOP10_MITIGATIONS.md)

### 4.5 SEE SOMETHING SAY SOMETHING

**OPERATIONAL PATTERN DETECTION**

WFC tracks errors in commands and code, learning patterns across sessions.

```
COMMAND ERROR DETECTED
    ↓
PATTERN RECOGNITION
    ↓
LOG TO REFLEXION.JSONL
    ↓
≥3 OCCURRENCES → AUTO-GENERATE OPS_TASKS.MD
    ↓
≥10 PATTERNS → RECOMMEND WFC-PLAN
```

**KNOWN PATTERNS:**
- Docker Compose `version:` field (obsolete since v1.27.0, 2020)
- pytest without `-v` flag (harder debugging)
- [Extensible pattern library]

**PURPOSE:** Systematic improvement through cross-session learning

---

## 05. EXAMPLE WORKFLOWS

### NEW FEATURE DEVELOPMENT

```bash
# STEP 1: Validate approach
/wfc-isthissmart "Add OAuth2 login with JWT tokens"

# STEP 2: Generate structured plan
/wfc-plan
# OUTPUT:
# ├─ TASKS.md       [5 tasks, dependencies mapped]
# ├─ PROPERTIES.md  [3 SAFETY, 2 INVARIANT properties]
# └─ TEST-PLAN.md   [12 test cases with EARS derivation]

# STEP 3: Execute with parallel agents
/wfc-implement
# PROCESS:
# ├─ Agent 1: TASK-001 [Setup]         [worktree-1]
# ├─ Agent 2: TASK-002 [OAuth flow]    [worktree-2]
# ├─ Agent 3: TASK-003 [JWT handler]   [worktree-3]
# ├─ Agent 4: TASK-004 [Token refresh] [worktree-4]
# └─ Agent 5: TASK-005 [Tests]         [worktree-5]
#
# EACH AGENT:
# └─ RED → GREEN → REFACTOR → QUALITY → REVIEW → MERGE

# STEP 4: Final verification
/wfc-review
# RESULT: ✓ APPROVED [8.5/10]
```

### SECURITY AUDIT

```bash
/wfc-security --stride
# GENERATES: THREAT-MODEL.md with STRIDE analysis

/wfc-review --properties SECURITY,SAFETY
# AUTO-SELECTS: APPSEC_SPECIALIST, PENTEST_SPECIALIST, etc.
```

### BUG FIX

```bash
/wfc-review affected-file.py
# Expert analysis of issue

# [Fix applied...]

/wfc-review
# Verify fix quality
```

---

## 06. PLATFORM COMPATIBILITY

**AGENT SKILLS STANDARD COMPLIANT**

WFC implements the [Agent Skills specification](https://agentskills.io) for universal compatibility.

**FEATURES:**
- Single source of truth (`~/.wfc/`)
- Symlink synchronization across platforms
- Progressive disclosure architecture
- Cross-platform configuration

**INSTALL MODES:**

```
SINGLE PLATFORM:   Copy to platform directory
MULTIPLE PLATFORMS: Symlink from ~/.wfc/ [RECOMMENDED]
CUSTOM SELECTION:   Choose specific platforms
```

[Installation Details](docs/UNIVERSAL_INSTALL.md)

---

## 07. DOCUMENTATION

### GETTING STARTED
- [Quick Start Guide](QUICKSTART.md)
- [Universal Installation](docs/UNIVERSAL_INSTALL.md)
- [Examples](docs/examples/)

### CORE CONCEPTS
- [Architecture](docs/ARCHITECTURE.md)
- [Persona Library](docs/PERSONAS.md)
- [EARS Requirements](docs/EARS.md)
- [Branding Modes](docs/BRANDING.md)

### CONFIGURATION
- [WFC Configuration](wfc/shared/config/wfc_config.py)
- [Quality Tools](wfc/skills/implement/quality_checker.py)

### CONTRIBUTING
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Creating Skills](docs/CREATING_SKILLS.md)

---

## 08. ARCHITECTURE PRINCIPLES

### SOLID
- **Single Responsibility:** Each module does one thing
- **Open/Closed:** Extend via new modules
- **Liskov Substitution:** All components work independently
- **Interface Segregation:** Small, focused classes
- **Dependency Inversion:** Manager composes specialized components

### DRY
- No duplication across codebase
- Shared infrastructure for all skills
- Reusable personas and patterns

### MULTI-TIER
- **Presentation tier:** CLI, Dashboard
- **Logic tier:** Orchestrator, Agents, Review
- **Data tier:** Telemetry, Git, Memory
- **Config tier:** WFCConfig

### PARALLEL
- True concurrent execution
- Independent subagents in isolated worktrees
- No context bleeding

### TOKEN-AWARE
- Every token counts
- 92% reduction through progressive disclosure
- Measured with benchmarks

---

## 09. ACKNOWLEDGMENTS

Built on [Claude Code](https://claude.ai/code)'s agent framework.

Inspired by ensemble methods in machine learning and the wisdom of diverse expert panels.

Special thanks to [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework) for pioneering multi-agent patterns and demonstrating the power of specialized personas working in concert. Their confidence-first approach and agent orchestration patterns heavily influenced WFC's architecture.

---

## 10. LICENSE

MIT License — see [LICENSE](LICENSE)

---

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ■ WORLD FUCKING CLASS ■                                       │
│                                                                 │
│  Complete workflow. Parallel execution. Expert consensus.      │
│                                                                 │
│  Get Started • Documentation                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

[Get Started](QUICKSTART.md) • [Documentation](docs/)
