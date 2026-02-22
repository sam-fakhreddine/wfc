---
title: Multi-Tenant WFC Properties
created: 2026-02-21
total_properties: 15
---

# Formal Properties - Multi-Tenant WFC

This document defines the formal properties that the multi-tenant WFC implementation MUST satisfy. Properties are extracted from requirements M1-M6 and non-functional requirements in BA-multi-tenant-wfc.md.

## SAFETY Properties (must never happen)

### PROP-S001: No Cross-Project Worktree Contamination

- **Statement**: Two projects with the same task_id MUST NEVER share worktree paths
- **Rationale**: Prevents worktree branch collisions, data mixing, and Git state corruption across projects
- **Priority**: CRITICAL
- **Acceptance Metric**: 100 concurrent reviews with identical task_id across 6 different projects → 0% collision rate
- **Related Requirements**: M1 (Project Isolation)
- **Related Tasks**: TASK-001a (ProjectContext dataclass), TASK-001b (worktree namespacing)
- **Observable**: `worktree_collision_count` (target: 0)
- **Test**: Create worktrees `.worktrees/proj1/wfc-test` and `.worktrees/proj2/wfc-test` concurrently → both succeed

### PROP-S002: No Knowledge Base Corruption

- **Statement**: Concurrent writes to KNOWLEDGE.md MUST NEVER produce corrupted data (invalid JSON/Markdown, garbled text)
- **Rationale**: Corrupted knowledge degrades review quality and prevents future reviews from learning
- **Priority**: CRITICAL
- **Acceptance Metric**: 100 concurrent writes to shared KNOWLEDGE.md → 0% corruption (all entries are valid JSON/Markdown)
- **Related Requirements**: M2 (Concurrent Access Safety)
- **Related Tasks**: TASK-002a (FileLock implementation), TASK-002b (atomic writes)
- **Observable**: `knowledge_corruption_events` (target: 0)
- **Test**: Parse KNOWLEDGE.md after 100 concurrent appends → 100% valid entries

### PROP-S003: No Report File Overwrites

- **Statement**: Concurrent reviews with same task_id from different projects MUST NEVER overwrite each other's REVIEW-*.md files
- **Rationale**: Report overwrites cause data loss and incorrect audit trails
- **Priority**: CRITICAL
- **Acceptance Metric**: 10 concurrent reviews with task_id="test" across 10 projects → 10 distinct report files exist
- **Related Requirements**: M1 (Project Isolation)
- **Related Tasks**: TASK-001c (output directory namespacing)
- **Observable**: `report_overwrite_count` (target: 0)
- **Test**: Generate reports to `~/.wfc/output/{project_id}/REVIEW-{task_id}.md` → verify all exist

### PROP-S004: No Metrics Contamination

- **Statement**: Telemetry metrics from different projects MUST NEVER be written to the same file
- **Rationale**: Prevents confusion in metrics analysis and incorrect aggregation
- **Priority**: HIGH
- **Acceptance Metric**: 6 concurrent reviews from 6 projects → 6 separate metrics files in `~/.wfc/metrics/{project_id}/`
- **Related Requirements**: M1 (Project Isolation)
- **Related Tasks**: TASK-001d (telemetry namespacing)
- **Observable**: `metrics_contamination_count` (target: 0)
- **Test**: Each project writes to its own metrics directory → verify separation

### PROP-S005: No API Rate Limit Breaches

- **Statement**: The token bucket MUST PREVENT Anthropic API 429 errors under maximum load (50 concurrent reviews)
- **Rationale**: 429 errors cause review failures and degrade user experience
- **Priority**: HIGH
- **Acceptance Metric**: 50 concurrent reviews → 0 Anthropic 429 errors observed
- **Related Requirements**: M4 (API Rate Limiting)
- **Related Tasks**: TASK-004a (TokenBucket class), TASK-004b (queue management)
- **Observable**: `api_rate_limit_breaches` (target: 0)
- **Test**: Spawn 50 concurrent reviews → token bucket queues requests → all complete successfully

---

## LIVENESS Properties (must eventually happen)

### PROP-L001: Orphaned Worktrees Must Be Cleaned

- **Statement**: All worktrees older than 24h with no active process MUST EVENTUALLY be deleted
- **Rationale**: Prevents disk space leaks and resource exhaustion
- **Priority**: HIGH
- **Acceptance Metric**: Crash 10 reviews mid-execution → 24h later → 0 orphan worktrees remain on disk
- **Related Requirements**: M5 (Guaranteed Resource Cleanup)
- **Related Tasks**: TASK-005a (orphan detection), TASK-005b (background cleanup task)
- **Observable**: `orphan_worktree_count` (target: 0 after 24h)
- **Test**: Kill 10 review processes → wait 24h → verify cleanup task removed all worktrees

### PROP-L002: Reviews Must Eventually Complete or Fail

- **Statement**: Every submitted review request MUST EVENTUALLY reach a terminal state (completed or failed), never stuck indefinitely
- **Rationale**: Prevents resource starvation and indefinite waiting
- **Priority**: HIGH
- **Acceptance Metric**: 100 review requests → 100% reach terminal state within 30 minutes
- **Related Requirements**: M5 (Guaranteed Resource Cleanup)
- **Related Tasks**: TASK-005c (timeout handling), TASK-005d (error propagation)
- **Observable**: `stuck_review_count` (target: 0)
- **Test**: Submit review with unreachable repo → fails within timeout (5 min)

### PROP-L003: Database State Must Be Consistent

- **Statement**: If a review job is persisted to PostgreSQL, its state MUST EVENTUALLY reflect the actual execution status (no stale "in_progress" after completion)
- **Rationale**: Stale state causes crash recovery to resume already-completed jobs
- **Priority**: MEDIUM
- **Acceptance Metric**: Query database after 100 reviews → 0 jobs stuck in "in_progress" with completed worktrees deleted
- **Related Requirements**: S1 (Crash Recovery)
- **Related Tasks**: TASK-006a (job state management), TASK-006b (state synchronization)
- **Observable**: `stale_job_count` (target: 0)
- **Test**: Complete review → verify database state updated to "completed"

---

## INVARIANT Properties (must always be true)

### PROP-I001: Developer Attribution Always Present

- **Statement**: Every review record in the database MUST ALWAYS have a non-empty developer_id field
- **Rationale**: Audit trail requires attribution for compliance and accountability
- **Priority**: HIGH
- **Acceptance Metric**: Database query `SELECT COUNT(*) FROM reviews WHERE developer_id IS NULL OR developer_id = ''` returns 0
- **Related Requirements**: M3 (Developer Attribution)
- **Related Tasks**: TASK-003a (orchestrator tagging), TASK-003b (knowledge_writer tagging), TASK-003c (git author override)
- **Observable**: `unattributed_review_count` (target: 0)
- **Test**: Submit review via API with X-API-Key: alice → database shows developer_id="alice"

### PROP-I002: Git Commits Always Attributed to Correct Developer

- **Statement**: All git commits created in worktrees MUST ALWAYS have GIT_AUTHOR_NAME and GIT_AUTHOR_EMAIL set to the requesting developer's credentials
- **Rationale**: Git history must reflect actual developer for audit and attribution
- **Priority**: HIGH
- **Acceptance Metric**: 100 reviews by 10 developers → 100% of commits have correct author metadata
- **Related Requirements**: M3 (Developer Attribution)
- **Related Tasks**: TASK-003c (worktree-manager.sh env override)
- **Observable**: `git_author_mismatch_count` (target: 0)
- **Test**: Alice triggers review → `git log` shows author="Alice <alice@example.com>"

### PROP-I003: Worktree Paths Always Unique

- **Statement**: At any point in time, no two active worktrees MUST have the same filesystem path
- **Rationale**: Filesystem collisions cause data corruption and review failures
- **Priority**: CRITICAL
- **Acceptance Metric**: 50 concurrent reviews → 50 unique worktree paths (no duplicates)
- **Related Requirements**: M1 (Project Isolation)
- **Related Tasks**: TASK-001b (worktree namespacing)
- **Observable**: `duplicate_worktree_path_count` (target: 0)
- **Test**: Generate worktree paths for all active reviews → verify uniqueness via set comparison

### PROP-I004: Code Reuse Between Interfaces

- **Statement**: MCP and REST interfaces MUST ALWAYS call the same orchestrator functions (90% code reuse, no duplicated business logic)
- **Rationale**: Prevents drift in behavior between interfaces and reduces maintenance burden
- **Priority**: MEDIUM
- **Acceptance Metric**: Static analysis shows MCP and REST both import and call `wfc.scripts.orchestrators.review.orchestrator.run_review()`
- **Related Requirements**: M6 (Choice of Interface)
- **Related Tasks**: TASK-007a (ReviewInterface abstraction), TASK-007b (MCP adapter), TASK-007c (REST adapter)
- **Observable**: `duplicated_logic_loc` (lines of code duplicated between interfaces, target: <10%)
- **Test**: Review MCP and REST codebases → verify both delegate to shared orchestrators

---

## PERFORMANCE Properties (bounded time/resources)

### PROP-P001: MCP Latency Overhead Bounded

- **Statement**: MCP review latency MUST BE < 500ms overhead compared to direct Claude Code session
- **Rationale**: Developer experience degrades with high latency; local MCP should be near-instant
- **Priority**: HIGH
- **Acceptance Metric**: Benchmark: `time @wfc review code` (MCP) - `time wfc-review` (direct) < 500ms
- **Related Requirements**: Non-functional (Latency MCP < 500ms overhead)
- **Related Tasks**: TASK-008a (MCP server optimization), TASK-008b (resource caching)
- **Observable**: `mcp_latency_p95` (target: <500ms)
- **Test**: Run 100 reviews via MCP → measure p95 latency overhead → verify < 500ms

### PROP-P002: REST API Latency Overhead Bounded

- **Statement**: REST API review latency MUST BE < 2s overhead compared to direct Claude Code session (excluding network time)
- **Rationale**: API should add minimal processing overhead beyond network latency
- **Priority**: MEDIUM
- **Acceptance Metric**: Benchmark: `curl POST /v1/review` server-side processing time < 2s
- **Related Requirements**: Non-functional (Latency REST API < 2s overhead)
- **Related Tasks**: TASK-008c (FastAPI optimization), TASK-008d (database query optimization)
- **Observable**: `rest_api_latency_p95` (target: <2s)
- **Test**: Measure server-side processing time (excluding network) → verify < 2s

### PROP-P003: Concurrent Review Capacity

- **Statement**: The system MUST support 50 concurrent reviews (10 devs × 5 agents) with 100% success rate
- **Rationale**: Defines maximum load for team deployment
- **Priority**: HIGH
- **Acceptance Metric**: Load test: 50 concurrent POST /v1/review → 100% success rate, 0 timeouts
- **Related Requirements**: Non-functional (Concurrent Reviews = 50)
- **Related Tasks**: TASK-009a (worker pool sizing), TASK-009b (connection pool tuning)
- **Observable**: `concurrent_review_capacity` (target: 50)
- **Test**: Spawn 50 concurrent reviews → all complete within 15 minutes

---

## Property Summary Table

| ID | Type | Priority | Metric | Related Requirements |
|----|------|----------|--------|---------------------|
| PROP-S001 | SAFETY | CRITICAL | 0% collision rate | M1 |
| PROP-S002 | SAFETY | CRITICAL | 0% corruption | M2 |
| PROP-S003 | SAFETY | CRITICAL | 0% overwrites | M1 |
| PROP-S004 | SAFETY | HIGH | 0% contamination | M1 |
| PROP-S005 | SAFETY | HIGH | 0 rate limit errors | M4 |
| PROP-L001 | LIVENESS | HIGH | 0 orphans after 24h | M5 |
| PROP-L002 | LIVENESS | HIGH | 100% terminal state | M5 |
| PROP-L003 | LIVENESS | MEDIUM | 0 stale jobs | S1 |
| PROP-I001 | INVARIANT | HIGH | 0 unattributed reviews | M3 |
| PROP-I002 | INVARIANT | HIGH | 0 author mismatches | M3 |
| PROP-I003 | INVARIANT | CRITICAL | 0 duplicate paths | M1 |
| PROP-I004 | INVARIANT | MEDIUM | >90% code reuse | M6 |
| PROP-P001 | PERFORMANCE | HIGH | <500ms MCP latency | NFR |
| PROP-P002 | PERFORMANCE | MEDIUM | <2s REST latency | NFR |
| PROP-P003 | PERFORMANCE | HIGH | 50 concurrent reviews | NFR |

---

## Observable Metrics

All properties map to observable metrics that can be measured in production:

**Safety Metrics**:

- `worktree_collision_count`: Number of worktree path collisions detected
- `knowledge_corruption_events`: Number of invalid KNOWLEDGE.md entries
- `report_overwrite_count`: Number of report file overwrites detected
- `metrics_contamination_count`: Number of cross-project metrics writes
- `api_rate_limit_breaches`: Number of Anthropic 429 errors received

**Liveness Metrics**:

- `orphan_worktree_count`: Number of worktrees older than 24h
- `stuck_review_count`: Number of reviews not in terminal state after timeout
- `stale_job_count`: Number of database jobs with inconsistent state

**Invariant Metrics**:

- `unattributed_review_count`: Number of reviews without developer_id
- `git_author_mismatch_count`: Number of commits with incorrect author
- `duplicate_worktree_path_count`: Number of duplicate filesystem paths
- `duplicated_logic_loc`: Lines of code duplicated between MCP/REST

**Performance Metrics**:

- `mcp_latency_p95`: 95th percentile MCP overhead in milliseconds
- `rest_api_latency_p95`: 95th percentile REST API overhead in milliseconds
- `concurrent_review_capacity`: Maximum concurrent reviews with 100% success

---

## Test Cases

Each property has corresponding test cases defined in the BA acceptance criteria:

| Property | Test Case | Location in BA |
|----------|-----------|----------------|
| PROP-S001, PROP-S003 | Test 1: Concurrent Project Reviews | Section 11, Test 1 |
| PROP-S005 | Test 2: Rate Limiting Under Load | Section 11, Test 2 |
| PROP-L001, PROP-L002 | Test 3: Crash Recovery | Section 11, Test 3 |
| PROP-I001, PROP-I002 | Test 4: Developer Isolation | Section 11, Test 4 |
| PROP-P001 | Test 5: MCP Local Speed | Section 11, Test 5 |
| PROP-S002 | Test 6: Shared Knowledge Base | Section 11, Test 6 |

---

## Verification Strategy

**Pre-deployment** (CI/CD pipeline):

1. Unit tests verify individual properties in isolation
2. Integration tests verify property interactions
3. Load tests verify performance properties under stress

**Post-deployment** (production monitoring):

1. Prometheus metrics track all observables
2. Alerts fire when any metric exceeds threshold
3. Weekly property validation report generated

**Continuous validation**:

1. Scheduled tests run nightly against production data
2. Property violations logged and escalated
3. Monthly property audit review with team

---

## References

- **BA Document**: ba/BA-multi-tenant-wfc.md
- **Requirements**: M1-M6 (MUST), S1-S4 (SHOULD), C1-C3 (COULD)
- **Non-Functional Requirements**: Section 5, Table (9 metrics)
- **Acceptance Criteria**: Section 11, Tests 1-6
- **Success Metrics**: Section 12 (deployment, adoption, performance)
