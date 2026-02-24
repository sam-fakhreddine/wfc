# Validation Analysis

## Subject: Multi-Tenant WFC Service Architecture

## Verdict: 🟡 PROCEED WITH ADJUSTMENTS

## Overall Score: 6.9/10

---

## Executive Summary

Overall, this approach shows **12 clear strengths** and **17 areas for consideration**.

The strongest aspects are: **Need validation** (9/10), **Failure mode analysis** (8/10), and **Blast radius** (7/10).

Key considerations: **No demand evidence from users**, **Could be solved more simply**, **Opportunity cost not analyzed**, **Timeline lacks buffer for unknowns**, **MCP contradiction (local-first vs multi-tenant)**.

With an overall score of **6.9/10**, this is a solid technical approach that requires validation and simplification before proceeding. The architecture is sound, but we should build incrementally and validate demand first.

---

## Dimension Analysis

### 1. Do We Even Need This? — Score: 9/10

**Strengths:**

- Clear evidence of current pain: 50% failure rate under concurrent use documented
- Real use cases articulated: "One developer managing 6 projects" OR "teams of 10+ developers"
- Critical race conditions documented: 6 specific concurrency issues (M1-M6) map directly to failure modes

**Concerns:**

- Missing demand evidence: No mention of how many users are requesting this or hitting these limits
- Single-user optimization assumption not validated: Are current users actually bumping into this limit?
- No customer interviews cited: Would be stronger with "5 teams requested multi-tenant support"

**Recommendation:** Validate actual demand before proceeding. Survey current WFC users to see how many are managing multiple projects simultaneously. Check telemetry for actual corruption/collision events. If <5 users report issues, consider deferring this feature.

---

### 2. Is This the Simplest Approach? — Score: 6/10

**Strengths:**

- Incremental streams: Offers MCP-First (2 weeks), REST-First (4 weeks), Hybrid (6 weeks)
- Code reuse emphasized: 90% code reuse between MCP and REST interfaces
- Clear out-of-scope: Section 8 explicitly excludes complexity creep (live migration, multi-LLM, web dashboard)

**Concerns:**

- Could solve with simpler isolation: Many issues could be fixed with just project_id namespacing
- Three implementation paths creates complexity: MCP-First, REST-First, AND Hybrid = decision paralysis
- Heavy infrastructure: PostgreSQL + Redis + Celery/RQ + FastAPI for what is essentially "namespace worktrees and lock files"
- FileLock might be overkill: Could use simpler per-project KNOWLEDGE.md files instead

**Recommendation:** Build Tier 0 approach first - just add ProjectContext and FileLock without MCP/REST interfaces. Test if this solves 80% of the problem for 20% of the effort. Consider per-project KNOWLEDGE.md files (no locking needed) + namespaced worktrees.

---

### 3. Is the Scope Right? — Score: 7/10

**Strengths:**

- Well-structured MoSCoW: Clear MUST (M1-M6), SHOULD (S1-S4), COULD (C1-C3), WON'T (W1-W3)
- Phased approach: Three streams allow right-sizing scope to actual need
- Concrete acceptance criteria: Test 1-6 in Section 11 are measurable and specific

**Concerns:**

- M6 feels out of scope: "Choice of Interface (MCP OR REST OR Both)" is a deployment decision, not a multi-tenancy requirement
- Missing minimal viable scope: No clear "absolute minimum" defined
- SHOULD items blur into MUST: S2 (Shared Knowledge Base) appears essential to team value proposition
- 6 MUST requirements is ambitious for 2-week timeline (Stream 1)

**Recommendation:** Tighten scope with clearer MVP:

- **Phase 1 (MVP)**: M1 (isolation) + M2 (locking) + M5 (cleanup) only
- **Phase 2**: Add M3 (attribution) + M4 (rate limiting) if team adoption validates need
- **Phase 3**: Consider MCP/REST interfaces only after Phase 1/2 prove insufficient
- **Remove M6 from MUST**: Interface choice should be separate feature decision

---

### 4. What Are We Trading Off? — Score: 5/10

**Strengths:**

- Risk table identifies some costs: PostgreSQL connection exhaustion, disk usage (500MB × 50), API cost spike
- Explicit exclusions: Section 8 (Out of Scope) acknowledges what's NOT being built
- Dependency list: New dependencies clearly enumerated (FastAPI, PostgreSQL, Redis, etc.)

**Concerns:**

- Missing opportunity cost analysis: No discussion of "what else could we build with 3-6 weeks instead?"
- Maintenance burden not quantified: PostgreSQL + Redis + background workers = ongoing operational overhead
- Backward compatibility break glossed over: W1 states "requires re-deployment" but doesn't quantify migration pain
- Team velocity impact unclear: Will maintaining MCP + REST interfaces slow down future feature development?
- No cost-benefit calculation: Solving 50% failure rate for how many users? What's the ROI?

**Recommendation:** Add explicit trade-off analysis section:

- Estimate maintenance cost (hours/week to operate PostgreSQL, monitor background tasks)
- Quantify migration pain for existing users
- List 3 alternative features that could be built in 3-6 weeks instead
- Define decision criteria: "Build this if >10 teams request it OR >5 solo devs report concurrent issues"

---

### 5. Have We Seen This Fail Before? — Score: 8/10

**Strengths:**

- Competitive analysis references: Kodus AI and GitHub Copilot patterns analyzed for gaps
- Risk table includes technical failures: FileLock cross-process issues, connection pool exhaustion
- Prior art validation: FastAPI + PostgreSQL acknowledged as "proven for multi-tenant SaaS"

**Concerns:**

- Missing anti-pattern analysis: No mention of noisy neighbor, tenant data leakage, shared schema debates
- MCP local-first contradiction: "MCP is local-first, not designed for multi-tenant" but then proposed for multi-project use
- No failure case studies: Would benefit from "Team X tried multi-tenant code review and failed because Y"

**Recommendation:** Add anti-pattern section:

- How will you prevent noisy neighbor (one project's 50-agent review starving others)?
- Research PostgreSQL row-level security failures or cross-tenant data leaks
- Clarify MCP appropriateness: If "MCP server crashes lose state", is it suitable for multi-project concurrent use?
- Specify PostgreSQL approach: per-tenant schemas vs shared schema with tenant_id column

---

### 6. What's the Blast Radius? — Score: 7/10

**Strengths:**

- Risk impact matrix: Likelihood × Impact for 9 specific risks
- Mitigation strategies documented: Each risk has concrete mitigation (e.g., "Set max_connections=100")
- Rollback acknowledged: PostgreSQL schema migration includes "rollback capability"

**Concerns:**

- No blast radius quantification: If REST API goes down, does it take down all 10 developers?
- Single point of failure: PostgreSQL + Redis as centralized state = higher blast radius than current distributed model
- Data loss scenarios underspecified: What happens if PostgreSQL crashes mid-review?
- Cascading failure not addressed: If Anthropic API is slow, will token bucket cause all reviews to queue and timeout?

**Recommendation:** Add blast radius analysis:

- **Current state**: Session crash affects 1 developer (blast radius = 1)
- **MCP-First**: MCP server crash affects 1 developer with 6 projects (blast radius = 6)
- **REST-First**: API crash affects all 10 developers (blast radius = 10)
- Add circuit breaker pattern to prevent cascading failures
- Document "how to revert to single-tenant WFC" rollback plan

---

### 7. Is the Timeline Realistic? — Score: 6/10

**Strengths:**

- Three timeline options: 2 weeks (MCP), 4 weeks (REST), 6 weeks (Hybrid) - acknowledges uncertainty
- Week-by-week breakdown: Streams 1-3 detail what happens each week
- Acceptance criteria testable: Section 11 tests can validate if timeline was met

**Concerns:**

- MCP-First "2 weeks" seems aggressive: Week 1 touches 8 files + Week 2 creates MCP server + testing
- No buffer for unknowns: Assumes no blockers (FileLock issues, MCP protocol problems, schema design debates)
- Dependencies not sequenced: "Week 3: REST interface" includes "Deploy to AWS ECS" - DevOps could add weeks
- Testing time missing: Load testing 50 concurrent requests - when does this happen?
- "3-6 weeks" is 100% variance: Signals high uncertainty

**Recommendation:** Add realistic timeline with buffers:

- **MCP-First**: 3 weeks (not 2) - add Week 3 for integration testing, load testing, bug fixes
- **REST-First**: 6 weeks (not 4) - add 2 weeks for DevOps (PostgreSQL provisioning, AWS deployment)
- **Hybrid**: 8 weeks (not 3-6) - sum of MCP + REST with 1-week integration buffer
- **Prototype phase**: Add 1-week spike to validate FileLock, MCP protocol, PostgreSQL schema
- **Decision gate**: After Week 1 (Tier 0 isolation), re-assess if full MCP/REST is needed

---

## Simpler Alternatives

### Tier 0: Minimal Isolation (1 week)

Just add ProjectContext + FileLock + namespaced worktrees from Week 1 of Stream 1. Test if this solves 80% of the problem:

- `.worktrees/{project_id}/wfc-{task_id}` (no collisions)
- Per-project KNOWLEDGE.md: `~/.wfc/knowledge/{project_id}/reviewers/` (no locking needed)
- Per-project metrics: `~/.wfc/metrics/{project_id}/`

**Decision gate**: If Tier 0 solves the problem, STOP HERE. Only proceed if insufficient.

### Alternative to FileLock: Append-Only Pattern

Instead of locking shared KNOWLEDGE.md, use append-only log pattern:

- Each review writes to `KNOWLEDGE-{project_id}-{timestamp}.jsonl`
- Background aggregator merges into canonical KNOWLEDGE.md periodically
- No locking needed, simpler failure modes

### Alternative to MCP+REST: Pick ONE

Don't build both interfaces. Validate which use case is real:

- If solo dev use case only: MCP-First (2-3 weeks)
- If team use case only: REST-First (4-6 weeks)
- Do NOT build Hybrid unless user validation proves both are needed

---

## Final Recommendation

**🟡 PROCEED WITH ADJUSTMENTS**

This BA document is technically sound and well-structured, but needs validation and simplification before implementation:

### STOP - Validate First (1 week)

1. **Survey current users**: Are ≥5 users managing multiple projects or hitting concurrent limits?
2. **Check telemetry**: Any actual corruption/collision events logged?
3. **Build Tier 0 MVP**: Just ProjectContext + FileLock + namespaced worktrees (Week 1 only)
4. **Test Tier 0**: Run 6 concurrent reviews - does this solve 80% of the problem?

**Decision gate**: If Tier 0 solves the problem OR <5 users report demand → STOP HERE

### IF Validated - Proceed Carefully (6-10 weeks)

1. **Prototype critical unknowns** (Week 2):
   - FileLock cross-process testing
   - MCP server with 6 concurrent projects
   - PostgreSQL schema design
   - Token bucket preventing 429 errors

2. **Choose ONE stream** (not all three):
   - MCP-First OR REST-First (based on validated use case)
   - Do NOT build Hybrid unless both proven necessary

3. **Add realistic buffers**:
   - MCP-First: 3 weeks (not 2)
   - REST-First: 6 weeks (not 4)
   - Include DevOps, testing, bug fixes

### Critical Questions to Answer Before Coding

1. **Demand**: How many users requested this? (Need ≥5)
2. **Simplicity**: Can ProjectContext + FileLock alone solve this?
3. **Scope**: Is M6 (interface choice) really part of multi-tenancy?
4. **Trade-offs**: What's the maintenance cost of PostgreSQL + Redis?
5. **Failure**: Why MCP if it's "not designed for multi-tenant"?
6. **Blast radius**: How to prevent REST API crash from affecting all devs?
7. **Timeline**: Where's the time for DevOps, testing, prototyping?

**Address these concerns, then proceed with confidence.**
