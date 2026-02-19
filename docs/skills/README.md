# WFC Skills — Selection Guide

Not sure which skill to run? Use this guide.

---

## By Goal

| Goal | Recommended Skill | Alternative |
|------|------------------|-------------|
| Quick feature, clear scope | `/wfc-build` | `/wfc-lfg` (fully automated) |
| Complex feature, multiple tasks | `/wfc-plan` + `/wfc-implement` | `/wfc-lfg` |
| Full auto pipeline, no hand-holding | `/wfc-lfg` | `/wfc-build` |
| Code review on existing code or PR | `/wfc-review` | Part of `/wfc-build` automatically |
| Security audit | `/wfc-security` | `/wfc-review` (includes security reviewer) |
| Architecture documentation | `/wfc-architecture` | `/wfc-plan` (includes architecture design phase) |
| Generate tests | `/wfc-test` | TDD is built into `/wfc-build` and `/wfc-implement` |
| Add monitoring / observability | `/wfc-observe` | Post-deploy plan is generated automatically by `/wfc-build` |
| Validate an idea or plan | `/wfc-validate` | Called automatically inside `/wfc-plan` |
| Fix PR comments | `/wfc-pr-comments` | Manual |
| Brainstorm / explore ideas | Default chat (wfc-vibe mode) | `/wfc-ba` |
| Business analysis and requirements | `/wfc-ba` | `/wfc-plan` (includes adaptive interview) |
| Export skills to other AI tools | `/wfc-export` | Manual |
| Debug CI failures | `/wfc-gh-debug` | Manual |
| Project cleanup and housekeeping | `/wfc-housekeeping` | Manual |
| Initialize a new project | `/wfc-init` | `/wfc-plan` |
| Document a solved problem | `/wfc-compound` | Manual |
| Deepen an existing plan with research | `/wfc-deepen` | Run after `/wfc-plan`, before `/wfc-implement` |

---

## By Phase

### Planning

Start here when scope is unclear or the feature is large.

| Skill | What it does |
|-------|-------------|
| `/wfc-ba` | Gather requirements through structured business analysis interview |
| `/wfc-validate` | Score a plan across 7 dimensions before committing to it |
| `/wfc-plan` | Run adaptive interview, produce TASKS.md + PROPERTIES.md + TEST-PLAN.md |
| `/wfc-deepen` | Enrich an existing plan with parallel research (codebase patterns, best practices, CVEs) |
| `/wfc-architecture` | Generate C4 diagrams and Architecture Decision Records |
| `/wfc-security` | STRIDE threat model — run before implementing security-sensitive features |

### Implementation

Run after planning (or skip planning with `/wfc-build` for small features).

| Skill | What it does |
|-------|-------------|
| `/wfc-build` | Intentional Vibe — short interview, then TDD implementation with quality gates and review |
| `/wfc-implement` | Multi-agent parallel implementation from a TASKS.md file |
| `/wfc-lfg` | Full auto: plan + deepen + implement + review + resolve + PR, zero hand-offs |
| `/wfc-test` | Generate property-based tests for a module or task |

### Review

Automatically called by `/wfc-build`, `/wfc-implement`, and `/wfc-lfg`. Invoke directly when reviewing manually.

| Skill | What it does |
|-------|-------------|
| `/wfc-review` | 5-agent consensus review (Security, Correctness, Performance, Maintainability, Reliability) |
| `/wfc-safeguard` | Real-time hook-based security enforcement (PreToolUse patterns) |
| `/wfc-rules` | Markdown-based custom code standards enforcement |
| `/wfc-pr-comments` | Triage and fix review feedback on an open PR |

### Knowledge

Run after you solve a problem, or when syncing rules across the codebase.

| Skill | What it does |
|-------|-------------|
| `/wfc-compound` | Document a solved problem into `docs/solutions/` for future search |
| `/wfc-sync` | Discover patterns in the codebase and sync them into WFC rules |
| `/wfc-observe` | Map formal properties to runtime metrics and monitoring queries |
