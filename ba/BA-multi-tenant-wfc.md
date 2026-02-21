# Business Analysis: Multi-Tenant WFC Service Architecture

## 1. Executive Summary

Transform WFC from a single-user, single-project tool into a production-grade multi-tenant service supporting concurrent reviews across multiple projects and development teams. This enables **one developer managing 6 projects** OR **teams of 10+ developers** sharing infrastructure, with reliability improvements addressing 6 critical race conditions currently preventing concurrent use.

**Impact**: Production-ready WFC for teams, 99% reduction in resource conflicts, full audit trail, shared knowledge base, and choice of deployment models (MCP for solo devs, REST API for teams, or hybrid).

**Timeline**: 3-6 weeks depending on chosen architecture stream.

---

## 2. Current State

### System Architecture

WFC is optimized for **one developer, one project, one session**:

- **Execution model**: Claude Code session-scoped
- **Project detection**: `Path.cwd()` (current working directory)
- **State management**: In-memory, process exit cleans up
- **Worktrees**: `.worktrees/wfc-{task_id}` (no namespacing)
- **Metrics**: All projects write to same `~/.wfc/telemetry/` directory
- **Knowledge base**: Shared `KNOWLEDGE.md` files with no locking

### Critical Files Referenced

**Core orchestrators** (will be reused):

- `wfc/scripts/orchestrators/review/orchestrator.py` - Review coordination
- `wfc/scripts/orchestrators/review/reviewer_engine.py` - Reviewer execution
- `wfc/scripts/orchestrators/review/consensus_score.py` - CS calculation

**Infrastructure requiring changes**:

- `wfc/shared/config/wfc_config.py` - Configuration system
- `wfc/gitwork/api/worktree.py` - Worktree management
- `wfc/shared/file_io.py` - File I/O operations
- `wfc/scripts/knowledge/knowledge_writer.py` - Knowledge persistence
- `wfc/shared/telemetry_auto.py` - Metrics collection

### Failure Modes Under Concurrent Use

Testing scenario: 2 projects running `/wfc-review` simultaneously

- **Result**: 50% failure rate (worktree branch collision)
- **Data corruption**: KNOWLEDGE.md becomes garbled
- **Report overwrites**: `REVIEW-task-123.md` from both projects collide
- **No attribution**: Can't distinguish "Project A findings" from "Project B findings"

---

## 3. Requirements

### MUST (Non-Negotiable)

**M1: Project Isolation**

- Every project gets unique namespace for worktrees, reports, metrics
- Two projects with same task_id must not collide
- **Acceptance**: 6 concurrent reviews complete successfully with 0 collisions
- **Files touched**: `wfc_config.py`, `worktree.py`, `orchestrator.py`, `telemetry_auto.py`

**M2: Concurrent Access Safety**

- File writes to shared resources (KNOWLEDGE.md) must be atomic
- No data corruption under concurrent writes from 10+ processes
- **Acceptance**: 100 concurrent reviews → 0 corrupted knowledge entries
- **Files touched**: `file_io.py` (add FileLock)

**M3: Developer Attribution**

- Every review/finding must be tagged with developer_id
- Audit trail: "who reviewed what, when"
- **Acceptance**: Database query returns correct developer for each review
- **Files touched**: `orchestrator.py`, `knowledge_writer.py`, `worktree-manager.sh`

**M4: API Rate Limiting**

- Token bucket pattern to prevent Anthropic API rate limit (429 errors)
- Fair allocation: 10 devs × 5 agents each = managed queue
- **Acceptance**: 50 concurrent API calls → 0 rate limit errors
- **Files touched**: `executor.py` (add TokenBucket class)

**M5: Guaranteed Resource Cleanup**

- Worktrees deleted even on service crash
- Orphan detection: delete worktrees >24h old
- **Acceptance**: Crash test → no orphaned worktrees after 24h
- **Files touched**: `worktree.py` (context manager + background task)

**M6: Choice of Interface (MCP OR REST OR Both)**

- Solo developer can use MCP (local, low latency)
- Team can use REST API (shared knowledge, RBAC, audit)
- Hybrid: MCP delegates to REST for team features
- **Acceptance**: Both interfaces call same orchestrators (90% code reuse)
- **New directories**: `wfc/mcp/`, `wfc/api/`

### SHOULD (Valuable, Deferrable)

**S1: Crash Recovery**

- REST API persists job state to PostgreSQL
- Service restart resumes in-flight reviews
- **Acceptance**: Kill service mid-review → restart → review completes

**S2: Shared Knowledge Base**

- Team knowledge aggregated across all developers' reviews
- Per-project knowledge branches optional
- **Acceptance**: Dev Alice's findings improve Dev Bob's next review

**S3: WebSocket Progress Streaming**

- Real-time review progress updates
- Client sees "3/5 reviewers completed"
- **Acceptance**: WebSocket client receives progress events during review

**S4: RBAC (Role-Based Access Control)**

- Alice can access projects 1-6, Bob can access projects 7-12
- Roles: admin, reviewer, viewer
- **Acceptance**: API returns 403 when Alice tries to access Bob's project

### COULD (Future Iteration)

**C1: Multi-Region Deployment**

- REST API deployed to multiple AWS regions
- Worktree pools distributed geographically
- **Deferred**: Single-region deployment sufficient for MVP

**C2: Review History Dashboard**

- Web UI showing all reviews across all projects
- Filtering by developer, project, consensus score
- **Deferred**: CLI/API sufficient for MVP

**C3: GitHub App Integration**

- Automatic review on PR open (no manual trigger)
- Review status as GitHub Check
- **Deferred**: Manual invocation sufficient for MVP

### WON'T (Explicit Exclusion)

**W1: Live Migration from Single-Tenant to Multi-Tenant**

- **Reason**: Clean deployment preferred over migration
- **Impact**: Existing users must re-register projects

**W2: Support for Non-Claude LLMs**

- **Reason**: WFC is Claude-specific (reviewer prompts, consensus algorithm)
- **Impact**: Anthropic API only

**W3: Self-Hosted MCP Server for Teams**

- **Reason**: MCP is local-first; REST API is correct choice for teams
- **Impact**: Teams must use REST API, not shared MCP server

---

## 4. Integration Seams

### Input From

- **Claude Code sessions** (MCP interface) → WFC MCP server → orchestrators
- **HTTP clients** (REST interface) → WFC API → orchestrators
- **CI/CD pipelines** (GitHub Actions, GitLab CI) → REST API
- **User configuration** → `wfc.config.json`, API key headers

### Output To

- **Orchestrators** → Database (PostgreSQL: projects, reviews, developers)
- **Orchestrators** → Knowledge files (KNOWLEDGE.md with file locking)
- **API** → HTTP clients (JSON responses)
- **MCP** → Claude Code (MCP tool results)
- **Audit log** → PostgreSQL reviews table (developer_id, timestamp, findings)

### Files Touched (Existing)

**Tier 1 - Project Isolation** (Week 1):

1. `wfc/shared/config/wfc_config.py` - Add `ProjectContext` dataclass
2. `wfc/gitwork/api/worktree.py` - Namespace worktrees: `.worktrees/{project_id}/wfc-{task_id}`
3. `wfc/scripts/orchestrators/review/orchestrator.py` - Accept `ProjectContext` parameter
4. `wfc/shared/file_io.py` - Add `FileLock` to `append_text()`
5. `wfc/shared/telemetry_auto.py` - Scope metrics to `~/.wfc/metrics/{project_id}/`

**Tier 2 - Developer Attribution** (Week 1):
6. `wfc/gitwork/scripts/worktree-manager.sh` - Override GIT_AUTHOR_NAME/EMAIL env vars
7. `wfc/scripts/knowledge/knowledge_writer.py` - Tag entries with developer_id

**Tier 3 - Resource Management** (Week 3):
8. `wfc/skills/wfc-implement/executor.py` - Add `TokenBucket` rate limiting

### New Files (Created)

**MCP Interface** (Phase 2A - Week 2):

- `wfc/mcp/server.py` - MCP server implementation
- `wfc/mcp/resources.py` - review://, knowledge:// URIs
- `wfc/mcp/tools.py` - review_code, generate_plan tools

**REST Interface** (Phase 2B - Weeks 2-4):

- `wfc/api/main.py` - FastAPI application
- `wfc/api/routes/review.py` - POST /v1/review endpoint
- `wfc/api/routes/plan.py` - POST /v1/plan endpoint
- `wfc/api/routes/projects.py` - GET /v1/projects endpoint
- `wfc/api/models.py` - Pydantic request/response schemas
- `wfc/api/state.py` - PostgreSQL ORM (SQLAlchemy models)
- `wfc/api/auth.py` - API key validation
- `wfc/api/rbac.py` - Role-based access control
- `wfc/api/background.py` - Orphan cleanup task (Celery/RQ)
- `wfc/api/websocket.py` - Real-time progress updates
- `wfc/api/audit.py` - Audit trail logging

**Shared Core** (Both interfaces use):

- `wfc/shared/resource_pool.py` - `WorktreePool`, `TokenBucket` classes
- `wfc/shared/interfaces.py` - `ReviewInterface` abstract base class

---

## 5. Non-Functional Requirements

| Requirement | Target | Measurement |
|---|---|---|
| **Concurrent Reviews** | 50 simultaneous (10 devs × 5 agents) | Load test: 50 concurrent POST /v1/review → 100% success rate |
| **Worktree Collision Rate** | 0% (zero collisions) | 100 concurrent reviews with same task_id → 0 failures |
| **Knowledge Corruption Rate** | 0% (zero corruption) | 100 concurrent writes to KNOWLEDGE.md → valid JSON/Markdown |
| **API Rate Limit Breaches** | 0 (no 429 errors) | 50 concurrent reviews → token bucket prevents Anthropic 429s |
| **Orphaned Worktrees** | 0 after 24h | Crash 10 reviews mid-execution → 24h later → 0 orphans on disk |
| **Latency (MCP)** | <500ms overhead | Local MCP review vs current session → <500ms difference |
| **Latency (REST API)** | <2s overhead | REST API review vs current session → <2s difference (network included) |
| **Database Uptime** | 99.9% (REST API only) | PostgreSQL availability over 30 days |
| **Horizontal Scaling** | 3-5 worker processes | Worker pool handles 50 concurrent reviews without queue backup |

### Compatibility Constraints

- **Python**: 3.12+ (for modern typing, async features)
- **Claude API**: Existing Anthropic SDK (no changes)
- **Claude Code**: Native MCP protocol (JSON-RPC 2.0)
- **Git**: Worktree API (git 2.25+)
- **Backward compatibility**: Existing WFC skills/orchestrators must work unmodified

### Dependencies (New)

**MCP Interface**:

- `mcp` (Anthropic MCP SDK) - required
- `httpx` (for MCP → REST delegation) - optional

**REST API**:

- `fastapi` - required
- `uvicorn` - required
- `sqlalchemy` - required (PostgreSQL ORM)
- `redis` - required (job queue, caching)
- `python-multipart` - required (file uploads)
- `celery` or `rq` - required (background tasks)
- `filelock` - required (KNOWLEDGE.md locking)
- `pydantic` v2 - required (request/response validation)

**Database**:

- PostgreSQL 14+ - required (for REST API)
- Redis 6+ - required (for REST API job queue)

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **FileLock doesn't work across processes** | Low | High | Use `fcntl.flock()` on Unix (tested), fallback to advisory locking |
| **PostgreSQL connection pool exhausted** | Medium | High | Set max_connections=100, worker pool max=5 (bounded concurrency) |
| **Token bucket causes starvation** | Low | Medium | Implement priority queue (admin > reviewer > viewer) |
| **MCP server crashes lose state** | High | Medium | Acceptable for solo dev use; REST API persists state to DB |
| **Developer adoption of API vs MCP** | Medium | Low | Hybrid approach: both available, developers choose based on need |
| **Worktree disk usage (500MB × 50 concurrent)** | Medium | Medium | Orphan cleanup task (24h TTL), alert when disk >80% full |
| **Anthropic API cost spike** | Medium | High | Token bucket + quota alerts (notify team when >90% monthly quota) |
| **PostgreSQL schema migration** | Low | Medium | Use Alembic for versioned migrations, rollback capability |
| **Network partitions (REST API)** | Low | High | Retry with exponential backoff, circuit breaker pattern |
| **SSH key isolation failure** | Low | High | Override GIT_SSH_COMMAND in worktree-manager.sh, test with 2 devs |

---

## 7. Prior Art

### Competitive Analysis

**Kodus AI** (reference):

- Finding validation: 4-layer pipeline (structural, LLM cross-check, historical, confidence scoring)
- Deduplication: Fingerprint-based with ±3-line tolerance
- **Adopt**: Multi-layer validation pattern
- **Gap**: Kodus doesn't support multi-tenant; WFC will

**GitHub Copilot Enterprise**:

- Shared knowledge base across organization
- Per-repository access control
- **Adopt**: RBAC pattern, shared knowledge
- **Gap**: Copilot doesn't do consensus review; WFC's 5-agent model is unique

**FastAPI + PostgreSQL** (stack choice):

- Proven for multi-tenant SaaS applications
- Native async support (Python async/await)
- **Adopt**: FastAPI for REST API, PostgreSQL for audit/RBAC
- **Prior art**: Hundreds of production FastAPI deployments at scale

**MCP Protocol** (Anthropic):

- Native Claude Code integration
- Resource discovery, tool introspection
- **Adopt**: MCP for solo dev use case (local, low latency)
- **Limitation**: MCP is local-first, not designed for multi-tenant

---

## 8. Out of Scope

**NOT included in this feature**:

1. **Live migration of existing WFC data**
   - Users must re-register projects manually
   - Historical reviews not imported

2. **Multi-LLM support** (OpenAI, Gemini, etc.)
   - WFC remains Claude-specific
   - Reviewer prompts assume Claude model family

3. **Web dashboard UI**
   - API-only for MVP
   - Future: React/Vue dashboard as separate project

4. **GitHub App with auto-review on PR open**
   - Manual invocation only for MVP
   - Future: GitHub App in Phase 5

5. **Distributed tracing (OpenTelemetry)**
   - Structured logging only for MVP
   - Future: Add OTEL spans if needed

6. **Multi-region deployment**
   - Single region (AWS us-east-1 or equivalent)
   - Future: Global deployment if customer demand

7. **Self-hosted MCP server for teams**
   - MCP is local-only by design
   - Teams use REST API, not shared MCP

8. **Backwards compatibility with WFC v1.x**
   - Clean break: requires re-deployment
   - Migration guide provided

---

## 9. Glossary

**ProjectContext**: Dataclass containing project_id, repo_path, worktree_dir, metrics_dir, output_dir. Threads through all orchestrators to enforce project isolation.

**Multi-tenant**: One service instance serves multiple projects and/or developers with guaranteed isolation.

**Worktree**: Git feature allowing multiple working directories from same repository. WFC creates temporary worktrees for parallel task execution.

**Consensus Score (CS)**: WFC's review aggregation metric. Formula: `CS = (0.5 × R̄) + (0.3 × R̄ × k/n) + (0.2 × R_max)` where R̄ = mean severity, k/n = reviewer agreement, R_max = max severity.

**MCP (Model Context Protocol)**: Anthropic protocol for Claude Code tool integration via JSON-RPC 2.0.

**Token Bucket**: Rate limiting algorithm. Bucket holds N tokens, refills at R tokens/min. Each API call consumes tokens. Empty bucket = request queued.

**RBAC**: Role-Based Access Control. Users assigned roles (admin, reviewer, viewer) per project. Roles determine permissions (read, write, delete).

**Orphan Worktree**: Worktree left on disk after process crash. Cleanup: background task deletes worktrees >24h old with no active process.

**FileLock**: Advisory file locking via `fcntl.flock()` (Unix) or equivalent. Ensures atomic writes to shared KNOWLEDGE.md.

**Fingerprint**: SHA-256 hash of finding (file, line range, category). Used for deduplication with ±3-line tolerance.

**Developer Attribution**: Tagging every review/finding with developer_id for audit trail. Enables "who reviewed what, when" queries.

**Hybrid Architecture**: Both MCP and REST interfaces available. Solo devs use MCP (local), teams use REST API (shared), MCP can delegate to REST for team knowledge.

---

## 10. Implementation Streams

### Stream 1: MCP-First (Solo Developer)

**Timeline**: 2 weeks
**Target**: 1 developer, 6 local projects

**Week 1**: Shared core fixes

- Add ProjectContext to orchestrators
- Add FileLock to KNOWLEDGE.md writes
- Namespace worktrees: `.worktrees/{project_id}/wfc-{task_id}`

**Week 2**: MCP interface

- Implement `wfc/mcp/server.py`
- Add MCP resources (review://, knowledge:// URIs)
- Add MCP tools (review_code, generate_plan)
- Test with Claude Code locally

**Deliverable**: Solo dev runs 6 concurrent reviews via MCP with 0 collisions

---

### Stream 2: REST-First (Team Deployment)

**Timeline**: 4 weeks
**Target**: 10 developers, 50 projects

**Week 1-2**: Shared core fixes (same as Stream 1)

**Week 3**: REST interface

- Implement `wfc/api/main.py` (FastAPI)
- Add authentication layer (API key validation)
- Add PostgreSQL/Redis integration
- Deploy to AWS ECS or equivalent

**Week 4**: Team features

- RBAC per project
- Audit logging (PostgreSQL reviews table)
- Rate limiting (token bucket)
- WebSocket progress streaming

**Deliverable**: Team of 10 devs runs 50 concurrent reviews via REST API with full audit trail

---

### Stream 3: Hybrid (Best of Both)

**Timeline**: 3-6 weeks
**Target**: Solo devs + teams

**Weeks 1-2**: Core + MCP (as in Stream 1)
**Weeks 3-4**: Add REST interface (as in Stream 2)
**Week 5**: MCP → REST delegation

**Deliverable**:

- Solo devs use MCP (local speed)
- Teams use REST API (shared knowledge)
- MCP can optionally delegate to REST for team data

---

## 11. Acceptance Criteria

### Test 1: Concurrent Project Reviews

```bash
# Start 6 reviews simultaneously
for i in {1..6}; do
  curl -X POST http://localhost:8000/v1/review \
    -d '{"project_id": "proj'$i'", "task_id": "test"}' &
done
wait

# ✅ All 6 complete successfully
# ✅ No worktree collisions
# ✅ 6 separate reports: REVIEW-proj{1-6}-test.md
# ✅ KNOWLEDGE.md not corrupted
```

### Test 2: Rate Limiting Under Load

```bash
# Spawn 50 concurrent requests
for i in {1..50}; do
  curl -X POST http://localhost:8000/v1/review \
    -d '{"project_id": "proj1", "task_id": "load-'$i'"}' &
done

# ✅ No 429 errors from Anthropic API
# ✅ Token bucket queues fairly
# ✅ All 50 complete within 15 minutes
```

### Test 3: Crash Recovery

```bash
# Start review
curl -X POST http://localhost:8000/v1/review/async \
  -d '{"project_id": "proj1", "task_id": "crash-test"}'

# Kill service mid-review
docker kill wfc-api

# Restart service
docker start wfc-api

# ✅ Job state recovered from PostgreSQL
# ✅ Review resumes from last checkpoint
# ✅ No orphaned worktrees after completion
```

### Test 4: Developer Isolation

```bash
# Alice creates worktree
curl -X POST -H "X-API-Key: alice-key" \
  http://localhost:8000/v1/review \
  -d '{"project_id": "proj1", "task_id": "feature"}'

# Bob creates worktree (same task_id, different project)
curl -X POST -H "X-API-Key": bob-key" \
  http://localhost:8000/v1/review \
  -d '{"project_id": "proj2", "task_id": "feature"}'

# ✅ No collision (different project namespaces)
# ✅ Git author = alice for first review
# ✅ Git author = bob for second review
# ✅ Audit log shows correct attribution
```

### Test 5: MCP Local Speed

```bash
# Benchmark: current WFC (session) vs MCP
time wfc-review (current)  # Baseline
time @wfc review this code (MCP)  # New

# ✅ MCP overhead < 500ms
```

### Test 6: Shared Knowledge Base

```bash
# Alice reviews code with SQL injection
# Bob reviews different code with SQL injection

# ✅ Bob's review shows "similar finding detected by alice on 2026-02-21"
# ✅ Shared KNOWLEDGE.md updated with both findings
```

---

## 12. Success Metrics

**Deployment success** (week 4):

- ✅ 0% worktree collision rate (across 100 test reviews)
- ✅ 0% knowledge base corruption (across 100 concurrent writes)
- ✅ 100% audit trail coverage (every review has developer_id)
- ✅ 0 Anthropic 429 errors (across 50 concurrent reviews)

**Adoption success** (week 8):

- ✅ 3+ developers using REST API daily
- ✅ 10+ projects registered in system
- ✅ 50+ reviews completed via API
- ✅ 95%+ review success rate (not crashed/corrupted)

**Performance success**:

- ✅ MCP latency < 500ms overhead vs current
- ✅ REST API latency < 2s overhead vs current
- ✅ Database query time < 100ms (p95)
- ✅ Orphan cleanup task completes < 5 min

---

## 13. Next Steps

1. **Validate this BA document** → Run `/wfc-validate` to check quality
2. **Plan generation** → Feed BA to `/wfc-plan` to generate TASKS.md
3. **Architecture review** → Review plan with team, choose stream (MCP/REST/Hybrid)
4. **Deployment target** → Decide: AWS ECS, GCP Cloud Run, or on-prem
5. **Database setup** → Provision PostgreSQL + Redis if REST stream chosen
6. **Implementation** → Run `/wfc-implement` with generated TASKS.md
