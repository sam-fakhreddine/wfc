# wfc-code-standards

## What It Does

`wfc-code-standards` defines the universal Defensive Programming Standard (DPS) that applies to every WFC project regardless of language. It codifies 13 engineering dimensions — from three-tier architecture and SOLID principles through error contracts, retry/timeout policies, structured logging, concurrency safety, and testing philosophy — into a single reference that all language-specific skills (such as `wfc-python`) inherit and extend. It is not invoked directly by users; it is referenced by agents during build, implementation, and review.

## When to Use It

- You are onboarding to the WFC codebase and want to understand what "done" means for any feature
- A code review flagged a DPS violation and you want to understand the standard behind it
- You are authoring a new language-specific skill and need the universal baseline to inherit from
- You are setting acceptance criteria for a task and want the DPS Definition of Done checklist
- You are reviewing code in any language and need a comprehensive violation checklist

This skill is a reference, not a workflow trigger. It is consumed by `wfc-build`, `wfc-implement`, `wfc-review`, and language-specific skills automatically.

## Usage

```bash
# Not user-invocable as a workflow. Referenced by agents and other skills.
# To apply these standards explicitly in a review:
/wfc-review          # The 5 specialist reviewers enforce DPS automatically

# To understand what you need to satisfy before marking a task done:
# See the Agent Pre-Completion Checklist inside this skill's SKILL.md
```

## Example

An agent completing a feature would walk through the 11-item pre-completion checklist before declaring done:

```
Agent self-check before submitting TASK-007:

 1. TESTS PASS       — ✅ Full suite: 847 tests passing, new tests assert behavior
 2. UNHAPPY PATHS    — ✅ Invalid input, timeout, duplicate call, partial failure covered
 3. BOUNDARIES       — ✅ All API params validated with Pydantic at entry point
 4. TIMEOUTS         — ✅ All httpx calls have timeout=30
 5. ERRORS TALK      — ✅ Structured errors with code + message + correlationId
 6. NO SECRETS LEAK  — ✅ Grep confirms no API keys in logs or error responses
 7. STATE IS GUARDED — ✅ Order status transitions validated via TRANSITIONS map
 8. IDEMPOTENT       — ✅ Upsert pattern, dedup on idempotency key
 9. SIMPLE           — ✅ No abstractions added beyond what the task requires
10. CLEAN DIFF       — ✅ Diff contains only changes requested in TASK-007
11. DEBTS DOCUMENTED — ✅ One FIXME with explanation; proper fix noted for TASK-012
```

## Options

No arguments required. This skill is a passive reference consumed by other skills.

The 13 DPS dimensions it defines:

| Dimension | DPS Code |
|-----------|----------|
| Boundary validation | DPS-1 |
| Idempotency | DPS-2 |
| State management | DPS-3 |
| Error contracts | DPS-4 |
| Retry and timeout | DPS-5 |
| Observability (structured logging + metrics) | DPS-6 |
| Concurrency safety | DPS-7 |
| Security (least privilege, parameterized queries) | DPS-8 |
| Configuration (fail-fast startup, env validation) | DPS-9 |
| Infrastructure (health checks, graceful shutdown, DLQ) | DPS-10 |
| Negative test coverage | DPS-11 |
| Architecture (three-tier, functional core/imperative shell) | — |
| Dependency management (lock files, CVE scanning) | — |

## Integration

**Produces:**

- The universal Definition of Done (DPS-0) applied to every feature
- The 11-item Agent Pre-Completion Checklist agents run before submitting work
- The Code Review Checklist used by all 5 wfc-review specialist reviewers

**Consumes:**

- Nothing at runtime — this skill is a static reference loaded by agents on demand

**Next step:** Language-specific skills (`wfc-python`, and others) inherit these standards and add tooling-specific enforcement. All DPS dimensions are validated automatically by the 5-reviewer consensus in `/wfc-review`.
