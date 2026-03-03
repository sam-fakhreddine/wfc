# Epic: Skill Architecture - Shared Conventions & DRY Refactor

> **Create as GitHub Issue when `gh` CLI is available:**
> `gh issue create --title "Epic: Skill Architecture - Shared Conventions & DRY Refactor" --body-file docs/issues/skill-architecture-epic.md`

## Context

After analyzing [agent-teams-lite](https://github.com/sam-fakhreddine/agent-teams-lite), we identified significant architectural improvements for how WFC skills are structured and distributed. This is a substantial refactor that warrants its own epic.

## Investigation Prompt for Agent

> **Objective:** Investigate and plan a refactor of the WFC skill architecture to reduce token overhead, eliminate duplication, and align with patterns proven by agent-teams-lite's `_shared/` convention system.
>
> **Phase 1: Audit Current State**
> 1. Read every `SKILL.md` in `wfc/skills/wfc-*/` and catalog repeated instruction blocks (patterns that appear in 3+ skills).
> 2. Measure token counts per skill using `tiktoken` — report min, max, median, total.
> 3. Identify which skills reference the same concepts: review protocol, TDD workflow, quality gates, token management, branching rules, EARS format, consensus scoring.
> 4. Map dependencies: which skills invoke other skills, and which shared context do they assume?
>
> **Phase 2: Design `_shared/` Convention System**
> 5. Propose a `wfc/skills/_shared/` directory with convention files that factor out repeated patterns. Use agent-teams-lite as a reference model — they have 3 convention files (`persistence-contract.md`, `engram-convention.md`, `openspec-convention.md`) that are referenced by all 9 skills.
> 6. For WFC, candidate shared conventions include:
>    - `review-protocol.md` — The 5-reviewer consensus review protocol, CS formula, MPR, dedup rules
>    - `tdd-workflow.md` — RED→GREEN→REFACTOR cycle, worktree isolation, quality gates
>    - `branch-policy.md` — `claude/*` branches, auto-merge to `develop`, never push to `main`
>    - `quality-gates.md` — Universal quality checker invocation, language-specific checkers
>    - `token-budget.md` — Progressive disclosure rules, token optimization strategy
>    - `ears-format.md` — EARS requirements notation reference
> 7. For each proposed convention file: estimate token savings across all skills that would reference it.
>
> **Phase 3: Reduce Per-Skill File Count**
> 8. Evaluate merging `CHECKLIST.md` content into `SKILL.md` (reducing from 3-4 files per skill to 1-2).
> 9. Evaluate whether `MOCK.md` needs to be in the installed skill set or can be test-only.
> 10. Propose a migration plan that maintains backward compatibility during the transition.
>
> **Phase 4: Token Impact Analysis**
> 11. Calculate projected token reduction: current total vs. post-refactor total.
> 12. Identify skills that could drop below 500 tokens with shared conventions.
> 13. Benchmark: load time before vs. after (using `wfc benchmark`).
>
> **Deliverables:**
> - `~/.wfc/projects/wfc/branches/develop/plans/skill-architecture-refactor/` containing:
>   - `AUDIT.md` — Current state analysis with token counts
>   - `DESIGN.md` — Proposed `_shared/` convention files with content outlines
>   - `MIGRATION.md` — Step-by-step migration plan
>   - `IMPACT.md` — Projected token savings and risk assessment

## Key Patterns from agent-teams-lite

1. **`_shared/` directory** with convention files referenced by all skills via relative path
2. **Single file per skill** (`SKILL.md` only) — no auxiliary files in the installed set
3. **Convention files as runtime includes** — the AI reads them when it reads the skill, creating a DRY include mechanism
4. **Skill-agnostic conventions** — the same shared files work across all platforms

## Acceptance Criteria

- [ ] `_shared/` directory created with 4-6 convention files
- [ ] All 31 skills updated to reference shared conventions instead of inline duplication
- [ ] Per-skill token count reduced by ≥30%
- [ ] `CHECKLIST.md` merged into `SKILL.md` where appropriate
- [ ] `make validate` passes with new structure
- [ ] Installer updated to copy `_shared/` alongside skills
- [ ] Token benchmark shows measurable improvement
