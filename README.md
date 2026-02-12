<div align="center">

<img src="assets/logo-championship-belt.jpg" alt="WFC Championship Belt" width="700">

# WFC

**Multi-Agent Development Framework**

[![License: MIT](https://img.shields.io/badge/License-MIT-1a1a1a.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-0652DD.svg)](https://www.python.org/downloads/)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Standard-d63031.svg)](https://agentskills.io)

**54 Expert AI Agents** • **Parallel Execution** • **EARS Requirements** • **92% Token Reduction**

[Quick Start](#installation) • [Workflow](#workflow) • [Documentation](#documentation)

</div>

---

## Overview

**Traditional Development**
- One developer
- One perspective
- Sequential execution
- Critical issues discovered late

**WFC Solution**
- Complete engineering team
- 54 specialized experts
- Parallel TDD agents
- Multi-expert consensus review

---

## Workflow

<div align="center">
<img src="assets/workflow-diagram.svg" alt="WFC Workflow" width="800">
</div>

### ■ Phase 1: Planning

**Command:** `/wfc-plan`

**Generates:**
- `TASKS.md` - Task breakdown with dependencies
- `PROPERTIES.md` - Formal properties (SAFETY, LIVENESS, PERFORMANCE)
- `TEST-PLAN.md` - Complete test strategy

**Features:**
- EARS format requirements (Rolls-Royce/Airbus standard)
- Dependency graph (DAG)
- Property-based test derivation

### ■ Phase 2: Implementation

**Command:** `/wfc-implement`

**Executes:**
- Up to 5 parallel TDD agents
- Isolated git worktrees
- Quality gates (linting, formatting, tests)
- Automatic merge or rollback

**Each Agent:**
```
Understand → Test First → Implement → Refactor → Quality Check → Submit
```

### ■ Phase 3: Review

**Command:** `/wfc-review`

**Process:**
- Auto-selects 5 relevant experts from 54 personas
- Independent parallel review (no anchoring bias)
- Weighted consensus algorithm
- Decision: Score ≥7.0 + no criticals = Ship

---

## Installation

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install-universal.sh
```

**Installer detects and installs to:**

| Platform | Path | Status |
|----------|------|--------|
| Claude Code | `~/.claude/skills` | ✓ |
| Kiro (AWS) | `~/.kiro/skills` | ✓ |
| OpenCode | `~/.opencode/skills` | ✓ |
| Cursor | `~/.cursor/skills` | ✓ |
| VS Code | `~/.vscode/skills` | ✓ |
| Codex | `~/.codex/skills` | ✓ |
| Antigravity | `~/.antigravity/skills` | ✓ |
| Goose | `~/.config/goose/skills` | ✓ |

**Branding modes:**
```
SFW  (Safe For Work) → Workflow Champion      [Professional]
NSFW (Default)       → World Fucking Class    [No Bullshit]
```

[Branding Details](docs/BRANDING.md)

---

## Key Features

<table width="100%">
<tr>
<td width="25%" align="center">
<img src="assets/icons/parallel-execution.svg" width="64" height="64" alt="Parallel">
<br><strong>Parallel Execution</strong>
<br>Up to 5 agents, isolated worktrees
</td>
<td width="25%" align="center">
<img src="assets/icons/smart-selection.svg" width="64" height="64" alt="Smart">
<br><strong>Smart Selection</strong>
<br>Auto-picks 5 from 54 experts
</td>
<td width="25%" align="center">
<img src="assets/icons/token-reduction.svg" width="64" height="64" alt="Tokens">
<br><strong>92% Token Reduction</strong>
<br>Progressive disclosure
</td>
<td width="25%" align="center">
<img src="assets/icons/platform-compatibility.svg" width="64" height="64" alt="Platform">
<br><strong>8+ Platforms</strong>
<br>Agent Skills standard
</td>
</tr>
</table>

---

## Expert Panels

| Panel | Count | Examples |
|-------|------:|----------|
| **Engineering** | 11 | Python, Node, Go, Rust, React, iOS, Android |
| **Security** | 8 | AppSec, PenTest, Cloud Security, Compliance |
| **Architecture** | 7 | Solutions, APIs, Microservices, Event-Driven |
| **Quality** | 8 | Performance, Load Testing, Code Review, A11y |
| **Data** | 4 | SQL, NoSQL, Data Engineering, ML |
| **Product** | 3 | Developer Experience, Technical PM |
| **Operations** | 4 | SRE, Platform, DevOps, Observability |
| **Domain** | 5 | Fintech, Healthcare, E-commerce, Gaming |
| **Specialists** | 4 | WCAG, Performance Optimization, i18n |
| **TOTAL** | **54** | **Ready to work** |

[Complete Persona Library →](docs/PERSONAS.md)

---

## Smart Selection Algorithm

**Example: OAuth2 + JWT Implementation**

```
Input Analysis:
├─ Tech stack: Python, FastAPI, PostgreSQL, Redis
├─ Files: auth_service.py, jwt_handler.py
├─ Properties: SECURITY, SAFETY
└─ Complexity: Large

Selected Panel (Top 5):
├─ 1. APPSEC_SPECIALIST      (0.95) - OAuth/JWT security
├─ 2. BACKEND_PYTHON_SENIOR  (0.88) - FastAPI patterns
├─ 3. API_SECURITY_SPECIALIST(0.82) - Token security
├─ 4. DB_ARCHITECT_SQL       (0.72) - Secure storage
└─ 5. SRE_SPECIALIST         (0.61) - Key rotation

Consensus Decision: CONDITIONAL APPROVE
Required Actions:
├─ Fix PII in JWT payload
└─ Add token rotation mechanism
```

---

## Complete Skill Suite

| Skill | Purpose |
|-------|---------|
| `wfc-plan` | Structured task breakdown with EARS format |
| `wfc-implement` | Parallel TDD implementation engine |
| `wfc-review` | Multi-expert consensus review |
| `wfc-test` | Property-based test generation |
| `wfc-security` | STRIDE threat modeling |
| `wfc-architecture` | C4 diagrams and ADRs |
| `wfc-observe` | Observability from properties |
| `wfc-retro` | AI-powered retrospectives |
| `wfc-safeclaude` | Safe command allowlist |
| `wfc-isthissmart` | Critical thinking advisor |
| `wfc-newskill` | Create new WFC skills |

---

## Example Workflows

### New Feature Development

```bash
# Step 1: Validate approach
/wfc-isthissmart "Add OAuth2 login with JWT tokens"

# Step 2: Generate structured plan
/wfc-plan

# Output:
# ├─ TASKS.md       (5 tasks, dependencies mapped)
# ├─ PROPERTIES.md  (3 SAFETY, 2 INVARIANT properties)
# └─ TEST-PLAN.md   (12 test cases with EARS derivation)

# Step 3: Execute with parallel agents
/wfc-implement

# Process:
# ├─ Agent 1: TASK-001 (Setup)           [worktree-1]
# ├─ Agent 2: TASK-002 (OAuth flow)      [worktree-2]
# ├─ Agent 3: TASK-003 (JWT handler)     [worktree-3]
# ├─ Agent 4: TASK-004 (Token refresh)   [worktree-4]
# └─ Agent 5: TASK-005 (Tests)           [worktree-5]
#
# Each agent:
# └─ RED → GREEN → REFACTOR → QUALITY → REVIEW → MERGE

# Step 4: Final verification
/wfc-review

# Result: ✓ APPROVED (8.5/10)
```

### Security Audit

```bash
/wfc-security --stride
# Generates: THREAT-MODEL.md with STRIDE analysis

/wfc-review --properties SECURITY,SAFETY
# Auto-selects: APPSEC_SPECIALIST, PENTEST_SPECIALIST, etc.
```

### Bug Fix

```bash
/wfc-review affected-file.py
# Expert analysis of issue

# Fix applied...

/wfc-review
# Verify fix quality
```

---

## Technical Specifications

### Progressive Disclosure

| Metric | Traditional | WFC | Savings |
|--------|------------:|----:|--------:|
| Initial context | ~43K tokens | ~3.4K tokens | **92.1%** |
| Load time | Slow | Fast | **10x** |
| Memory usage | High | Low | **90%** |

**Mechanism:**
```
Load summaries only (IDs + descriptions)
    ↓
On expert selection
    ↓
Fetch full persona details
    ↓
Cache for session
```

### EARS Requirements Format

Five templates for unambiguous, testable requirements:

| Type | Template | Use Case |
|------|----------|----------|
| **UBIQUITOUS** | `The system shall <action>` | Always active |
| **EVENT_DRIVEN** | `WHEN <trigger>, system shall <action>` | Event response |
| **STATE_DRIVEN** | `WHILE <state>, system shall <action>` | Continuous condition |
| **OPTIONAL** | `WHERE <feature>, system shall <action>` | Conditional capability |
| **UNWANTED** | `IF <condition>, THEN system shall <action>` | Constraint/prevention |

[EARS Documentation →](docs/EARS.md)

### Performance Metrics

| Metric | Value |
|--------|------:|
| Expert personas | 54 |
| Max parallel agents | 5 |
| Token reduction | 92% |
| Quality tools | 100+ (via Trunk.io) |
| Platform support | 8+ |

---

## Platform Compatibility

**Agent Skills Standard Compliant**

WFC implements the [Agent Skills specification](https://agentskills.io) for universal compatibility.

**Features:**
- Single source of truth (`~/.wfc/`)
- Symlink synchronization
- Progressive disclosure
- Cross-platform configuration

**Install modes:**
```
Single platform:   Copy to platform directory
Multiple platforms: Symlink from ~/.wfc/ (recommended)
Custom selection:   Choose specific platforms
```

[Installation Details →](docs/UNIVERSAL_INSTALL.md)

---

## Documentation

### Getting Started
- [Quick Start Guide](QUICKSTART.md)
- [Universal Installation](docs/UNIVERSAL_INSTALL.md)
- [Examples](docs/examples/)

### Core Concepts
- [Architecture](docs/ARCHITECTURE.md)
- [Persona Library](docs/PERSONAS.md)
- [EARS Requirements](docs/EARS.md)
- [Branding Modes](docs/BRANDING.md)

### Configuration
- [WFC Configuration](wfc/shared/config/wfc_config.py)
- [Quality Tools](wfc/skills/implement/quality_checker.py)

### Contributing
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Creating Skills](docs/CREATING_SKILLS.md)

---

## Acknowledgments

Built on [Claude Code](https://claude.ai/code)'s agent framework.

Inspired by ensemble methods in machine learning and the wisdom of diverse expert panels.

Special thanks to [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework) for pioneering multi-agent patterns and demonstrating the power of specialized personas working in concert. Their confidence-first approach and agent orchestration patterns heavily influenced WFC's architecture.

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**■ WORLD FUCKING CLASS ■**

*Complete workflow. Parallel execution. Expert consensus.*

[Get Started](QUICKSTART.md) • [Documentation](docs/) • [GitHub](https://github.com/sam-fakhreddine/wfc)

</div>
