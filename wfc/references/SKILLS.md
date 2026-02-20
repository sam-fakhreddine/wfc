# WFC Skills Reference

Complete reference for all 30 WFC skills. Use this when choosing which skill to invoke.

## Quick Decision

| If you want to… | Use |
|-----------------|-----|
| Chat, explore, brainstorm | Just talk (wfc-vibe activates automatically) |
| Build a single feature fast | `/wfc-build` |
| Build something large/complex | `/wfc-plan` → `/wfc-implement` |
| Go fully autonomous | `/wfc-lfg` |
| Review code | `/wfc-review` |
| Fix PR comments | `/wfc-pr-comments` |

---

## Planning & Requirements

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-vibe` | Default conversational mode | Natural brainstorming; detects when scope grows and suggests transitioning to planning |
| `wfc-ba` | `/wfc-ba` | Structured stakeholder interview → MoSCoW requirements → planner-ready BA doc |
| `wfc-validate` | `/wfc-validate` | 7-dimension critique: feasibility, complexity, risk, value, alternatives, assumptions, trade-offs |
| `wfc-plan` | `/wfc-plan` | Adaptive interview → TASKS.md + PROPERTIES.md + TEST-PLAN.md; TEAMCHARTER validation |
| `wfc-deepen` | `/wfc-deepen` | Post-plan parallel research: external best practices, codebase patterns, past solutions |

## Implementation

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-build` | `/wfc-build "feature"` | Quick adaptive interview → TDD subagent(s) → quality checks → review → PR |
| `wfc-implement` | `/wfc-implement` | Reads TASKS.md → parallel TDD agents in isolated worktrees → merge engine → PR |
| `wfc-lfg` | `/wfc-lfg "feature"` | Full autonomous pipeline: plan → deepen → implement → review → resolve → PR |
| `wfc-init` | `/wfc-init` | Detect project languages → set up formatters, linters, test frameworks |

## Review & Quality

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-review` | `/wfc-review` | 5-agent consensus (Security, Correctness, Performance, Maintainability, Reliability); CS algorithm with MPR |
| `wfc-test` | `/wfc-test` | Property-based test generation from PROPERTIES.md (SAFETY, LIVENESS, INVARIANT) |
| `wfc-security` | `/wfc-security` | STRIDE threat modeling; OWASP LLM Top 10; generates threat model + mitigations |
| `wfc-gh-debug` | `/wfc-gh-debug` | Fetch failing CI logs via gh CLI → root cause analysis → fix |
| `wfc-retro` | `/wfc-retro` | Analyse WFC telemetry → patterns, bottlenecks, agent performance trends |

## Knowledge & Documentation

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-compound` | `/wfc-compound` | Codify solved problems into `docs/solutions/`; before/after code + prevention guidance |
| `wfc-architecture` | `/wfc-architecture` | C4 diagrams (Mermaid) + Architecture Decision Records |
| `wfc-observe` | `/wfc-observe` | Map PROPERTIES.md → metrics collectors, alerts, dashboards |
| `wfc-housekeeping` | `/wfc-housekeeping` | Dead code, stale branches, orphaned files, unused imports — scan then cleanup |
| `wfc-claude-md` | `/wfc-claude-md` | Diagnose and fix CLAUDE.md files (5-agent pipeline; subtract-first rewrite) |

## Enforcement & Security

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-safeguard` | `/wfc-safeguard` | Install PreToolUse hooks for real-time pattern enforcement (eval, innerHTML, SQL injection, etc.) |
| `wfc-rules` | `/wfc-rules` | Markdown-based custom rule engine; drop `.wfc/rules/*.md` files to enforce patterns |
| `wfc-safeclaude` | `/wfc-safeclaude` | Generate project-specific Claude Code command allowlist |
| `wfc-sync` | `/wfc-sync` | Discover undocumented codebase patterns → update rules + project context |

## Workflow & Integrations

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-pr-comments` | `/wfc-pr-comments [PR#]` | Fetch unresolved PR threads → triage → parallel fix subagents → resolve threads |
| `wfc-agentic` | `/wfc-agentic` | Generate GitHub Agentic Workflows (gh-aw) from natural language |
| `wfc-export` | `/wfc-export` | Convert WFC skills to Copilot, Gemini CLI, OpenCode, Cursor, Kiro, Factory formats |
| `wfc-newskill` | `/wfc-newskill` | Structured interview → generate new WFC skill with SKILL.md + implementation |

## Standards

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `wfc-code-standards` | `/wfc-code-standards` | Language-agnostic Defensive Programming Standard (13 dimensions) |
| `wfc-python` | `/wfc-python` | Python 3.12+ specific standards (UV toolchain, black, full typing, PEP 562) |
| `wfc-playground` | `/wfc-playground` | Single-file interactive HTML playground; 3 templates (design, data-explorer, concept-map) |
| `wfc-isthissmart` | `/wfc-isthissmart` | Sanity-check a decision before committing |

---

## Typical Flows

### Small feature

```
/wfc-build "add rate limiting"
```

### Large feature

```
/wfc-ba → /wfc-validate → /wfc-plan → /wfc-deepen → /wfc-implement → /wfc-review
```

### Full autonomous

```
/wfc-lfg "add rate limiting"
```

### After PR is reviewed

```
/wfc-pr-comments 42
```

### After solving a hard problem

```
/wfc-compound
```
