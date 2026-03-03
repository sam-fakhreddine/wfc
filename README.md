# WFC — AI-Powered Development Team in Your IDE

> **Ship better code, faster.** 5 specialist reviewers, parallel TDD agents, and real-time security enforcement — all in your IDE.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agent%20skills-standard-purple.svg)](https://agentskills.io)

---

## Install (2 minutes)

```bash
git clone https://github.com/sam-fakhreddine/wfc.git
cd wfc
./install.sh
```

The installer auto-detects your platform and sets everything up.

**Supports:** Claude Code · Kiro · OpenCode · Cursor · VS Code · Codex · Antigravity · Goose

**Targeted install:** `./install.sh --agent claude` (skip the menu)

---

## Get Started

```bash
# Review your code with 5 specialist agents
/wfc-review

# Build a feature with TDD
/wfc-build "add OAuth2 login with JWT tokens"

# Full auto: plan → implement → review → PR
/wfc-lfg "add rate limiting to the API"
```

---

## How It Works

WFC orchestrates specialized AI agents across three phases:

```
PLANNING               IMPLEMENTATION           REVIEW
/wfc-plan              /wfc-implement           /wfc-review
    ↓                      ↓                       ↓
TASKS.md               Parallel Agents          5 Specialist Reviewers
Dependency Graph       TDD in Git Worktrees     Consensus Score ≥ 7.0
```

### Five-Agent Consensus Reviews

Every review runs 5 fixed specialist reviewers in parallel:

| Reviewer | Focus |
|----------|-------|
| **Security** | OWASP Top 10, injection, auth/authz, secrets |
| **Correctness** | Logic bugs, edge cases, type safety |
| **Performance** | Algorithmic complexity, N+1 queries, memory |
| **Maintainability** | Readability, SOLID/DRY, coupling |
| **Reliability** | Error handling, fault tolerance, resource leaks |

**Consensus Score:** `CS = (0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)`

**Minority Protection Rule:** If Security or Reliability raises a critical finding (≥8.5), the score is elevated regardless of consensus.

### Parallel TDD Implementation

Up to 5 agents work simultaneously in isolated git worktrees:

```
├─ Agent 1: Auth system         [worktree-1]
├─ Agent 2: OAuth2 flow         [worktree-2]
├─ Agent 3: JWT handler         [worktree-3]
├─ Agent 4: Token refresh       [worktree-4]
└─ Agent 5: Integration tests   [worktree-5]
    ↓
Quality gates → Consensus review → Merge
```

Each agent follows strict TDD: **test first → implement → refactor**.

---

## Skills

### Core Development

| Skill | What It Does |
|-------|-------------|
| `/wfc-lfg` | Full auto: plan → implement → review → PR |
| `/wfc-build` | Quick feature with adaptive interview + TDD |
| `/wfc-plan` | Structured task breakdown with dependency graphs |
| `/wfc-implement` | Multi-agent parallel TDD execution |
| `/wfc-review` | Five-reviewer consensus code review |

### Quality & Security

| Skill | What It Does |
|-------|-------------|
| `/wfc-test` | Property-based test generation |
| `/wfc-security` | STRIDE threat modeling |
| `/wfc-validate` | Critical thinking advisor (7 dimensions) |
| `/wfc-safeguard` | Real-time security hooks |

### Productivity

| Skill | What It Does |
|-------|-------------|
| `/wfc-ba` | Business analysis & requirements |
| `/wfc-vibe` | Natural brainstorming mode |
| `/wfc-pr-comments` | Triage and fix PR review feedback |
| `/wfc-architecture` | C4 diagrams + ADRs |
| `/wfc-retro` | AI-powered retrospectives |

[See all skills →](QUICKSTART.md#available-skills)

---

## Security

WFC mitigates **9/9** applicable OWASP LLM Top 10 risks:

- Real-time security hooks block dangerous operations before execution
- Prompt injection defenses with 94% attack surface reduction
- Secret detection prevents credential leaks
- Multi-reviewer consensus catches misinformation

[Full OWASP analysis →](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)

---

## Platform Config Templates

After installation, configure your platform's orchestrator using the templates in [`examples/`](examples/):

| Platform | Config File | Template |
|----------|-------------|----------|
| Claude Code | `~/.claude/CLAUDE.md` | [`examples/claude-code/CLAUDE.md`](examples/claude-code/CLAUDE.md) |
| Kiro | `~/.kiro/KIRO.md` | [`examples/kiro/KIRO.md`](examples/kiro/KIRO.md) |
| Cursor | `.cursorrules` | [`examples/cursor/.cursorrules`](examples/cursor/.cursorrules) |
| VS Code | `copilot-instructions.md` | [`examples/vscode/copilot-instructions.md`](examples/vscode/copilot-instructions.md) |
| OpenCode | `opencode.json` | [`examples/opencode/`](examples/opencode/) |

---

## Documentation

- **[Quick Start](QUICKSTART.md)** — Full onboarding guide
- **[Architecture](docs/architecture/ARCHITECTURE.md)** — System design
- **[Security](docs/security/OWASP_LLM_TOP10_MITIGATIONS.md)** — OWASP coverage
- **[Contributing](CONTRIBUTING.md)** — How to contribute
- **[All docs](docs/)** — Full documentation index

---

## Python Package (Optional)

For the CLI, token optimization, and validation tools:

```bash
uv pip install -e ".[all]"
wfc validate --all     # validate skills
wfc test               # run test suite
```

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE)
