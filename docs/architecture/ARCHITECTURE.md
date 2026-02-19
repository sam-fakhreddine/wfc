# WFC Architecture

## What WFC Does

WFC (World Fucking Class) is a multi-agent engineering system built on top of Claude Code. It takes a feature request or a task description and runs it through a structured pipeline: requirements gathering, parallel implementation by subagents, automated quality gates, five-agent consensus review, and a PR to your repository.

The goal is to close the gap between "good code written by a single AI" and "code that would survive a rigorous engineering review." WFC does this by making the review process multi-perspective, mathematical, and persistent — reviewers accumulate domain knowledge across every session.

## Core Components

### 1. Skills Layer

WFC exposes its capabilities through 30 Agent Skills installed at `~/.claude/skills/wfc-*/`. Each skill is a self-contained package with a `SKILL.md` that Claude loads on invocation. Skills follow the Agent Skills specification: hyphenated names, valid frontmatter, and XML prompt generation.

Key skills: `wfc-build` (quick features), `wfc-plan` + `wfc-implement` (structured complex work), `wfc-review` (standalone consensus review), `wfc-lfg` (fully autonomous end-to-end pipeline), `wfc-compound` (knowledge codification).

### 2. Review System

Five fixed specialist reviewers analyze every code change in parallel. Findings are deduplicated by SHA-256 fingerprint, scored by the Consensus Score algorithm, and routed to one of four decision tiers (Informational, Moderate, Important, Critical). See [REVIEW_SYSTEM.md](../concepts/REVIEW_SYSTEM.md) for the full specification.

```
ReviewOrchestrator
  ├── prepare_review() ─── 5 reviewer task specs (parallel)
  │     ReviewerLoader ──► wfc/references/reviewers/{name}/PROMPT.md
  │     KnowledgeRetriever ──► KNOWLEDGE.md (two-tier RAG)
  │
  └── finalize_review()
        ReviewerEngine.parse_results() ──► findings per reviewer
        Fingerprinter.deduplicate()    ──► SHA-256 dedup with ±3-line tolerance
        ConsensusScore.calculate()     ──► CS with Minority Protection Rule
        ──► REVIEW-{task_id}.md report
```

Source: `wfc/scripts/orchestrators/review/`

### 3. Quality Gates

Automated linting and type checking runs at two points: immediately after every file write (PostToolUse), and as a blocking gate before review. Language-specific checkers cover Python (ruff + pyright), TypeScript (prettier + eslint + tsc), and Go (gofmt + go vet + golangci-lint). Trunk.io integration provides a universal 100+ tool gate when available. See [QUALITY_GATES.md](../concepts/QUALITY_GATES.md).

### 4. Hook Infrastructure

PreToolUse hooks enforce 13 security patterns before tool calls execute (eval injection, hardcoded secrets, SQL concatenation, destructive shell commands, GitHub Actions injection, and more). PostToolUse hooks run auto-lint (`file_checker.py`), TDD reminders (`tdd_enforcer.py`), and context window monitoring (`context_monitor.py`). All hooks are fail-open: an internal hook error never blocks the workflow. See [HOOKS.md](../concepts/HOOKS.md).

Source: `wfc/scripts/hooks/`

### 5. Knowledge System

Each reviewer maintains a `KNOWLEDGE.md` file that accumulates learnings from past reviews. A two-tier RAG pipeline (embedding similarity + keyword fallback) retrieves relevant entries at review time. Findings above severity thresholds are auto-appended after each review. A drift detector flags stale (>90d), bloated (>50 entries), contradictory, and orphaned entries. See [KNOWLEDGE_SYSTEM.md](../concepts/KNOWLEDGE_SYSTEM.md).

Source: `wfc/scripts/knowledge/`
Reviewer knowledge files: `wfc/references/reviewers/{security,correctness,performance,maintainability,reliability}/KNOWLEDGE.md`

### 6. Git Operations

WFC manages branches, worktrees, and PRs through a controlled git layer. Worktrees are always provisioned through `wfc/gitwork/scripts/worktree-manager.sh` (never with bare `git worktree add`) to ensure environment bootstrap, `.gitignore` registration, and config propagation happen correctly. The default integration target is `develop`; main is protected and receives only release candidates.

Source: `wfc/gitwork/`

## Directory Layout

```
wfc/
├── scripts/
│   ├── orchestrators/
│   │   └── review/           # Review pipeline (orchestrator, engine, CS, fingerprint, CLI)
│   ├── hooks/                # PreToolUse + PostToolUse hook infrastructure
│   │   ├── patterns/         # security.json, github_actions.json
│   │   └── _checkers/        # python.py, typescript.py, go.py
│   └── knowledge/            # RAG engine, knowledge writer, drift detector
│
├── references/
│   └── reviewers/            # Per-reviewer PROMPT.md + KNOWLEDGE.md
│       ├── security/
│       ├── correctness/
│       ├── performance/
│       ├── maintainability/
│       └── reliability/
│
├── gitwork/                  # Git operations (worktree manager, worktree API)
│   ├── scripts/
│   └── api/
│
├── skills/                   # Agent Skills source packages (wfc-build/, wfc-plan/, etc.)
└── assets/                   # Templates (playground HTML, etc.)

~/.claude/skills/wfc-*/       # Installed skills (30 total, Agent Skills compliant)
```

## Request Lifecycle

A typical `wfc-build` invocation flows through the system as follows:

1. **Interview** — 3–5 adaptive questions establish scope and constraints.
2. **Orchestration** — complexity is assessed; one or more subagents are dispatched.
3. **Implementation** — each subagent follows TDD: write failing tests (RED), implement until green (GREEN), refactor (REFACTOR).
4. **Quality gate** — language-specific checkers run on all changed files; failures block progression.
5. **Review** — five specialist reviewers analyze the diff in parallel; CS is calculated.
6. **Decision** — CS tier determines whether the PR is created, blocked, or escalated.
7. **Knowledge update** — high-quality findings are appended to reviewer KNOWLEDGE.md files.
8. **PR** — branch is pushed to `claude/*` and a PR is opened to `develop`.

## Design Principles

**Fail-open**: Hooks, quality gates, and review infrastructure never block the workflow due to internal errors. Bugs in tooling surface as warnings, not hard stops.

**Mathematical scoring**: The Consensus Score removes subjectivity from the merge/block decision. The formula, thresholds, and Minority Protection Rule are fixed and auditable.

**Persistent learning**: Reviewers are not stateless. Knowledge accumulated from past reviews improves future analysis on the same codebase, with drift detection to keep the knowledge base healthy.

**Progressive disclosure**: Skills load only what they need. A `SKILL.md` under 500 lines handles the common case; reference documents and scripts are loaded on demand.
