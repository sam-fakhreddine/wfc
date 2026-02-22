# Business Analysis: MCP Gateway Integration for WFC

**Date**: 2026-02-22
**Feature**: Unified MCP Gateway Layer
**Analyst**: Claude Code with WFC-BA

---

## 1. Executive Summary

**Vision**: Transform WFC into a **centralized AI development platform** where all development artifacts (plans, reviews, implementations, BA documents, tests) flow through MCP/API as single source of truth. Teams interact with WFC exclusively through these interfaces, creating a **living, breathing documentation engine** that captures the entire development lifecycle.

**Current Gap**: WFC operates dual transport layers (MCP stdio + REST API) with duplicated auth/rate-limit logic and no artifact persistence layer. Agents cannot post back development artifacts (TASKS.md, REVIEW.md, BA docs) to a central system.

**Proposed Solution**:

1. Unified MCP gateway layer (auth, rate-limit, observability)
2. **Artifact Storage System** (plans, reviews, BAs, tests, implementations)
3. **Living Documentation API** (query/search all artifacts, generate insights)
4. Multi-agent collaboration hub (agents post updates, teams consume via dashboard)

**Expected Impact**:

- Single source of truth for all development work
- Automatic documentation generation from actual work artifacts
- Team-wide visibility into AI agent activities
- Foundation for enterprise SaaS offering

---

## 2. Current State

### 2.1 Architecture

WFC implements a **dual-server architecture**:

```
Claude Desktop (stdio) → WFCMCPServer → ReviewOrchestrator
HTTP Clients → Traefik → FastAPI → ReviewOrchestrator
```

**Key Components**:

- **MCP Server** (`wfc/servers/mcp_server.py`): stdio transport, directly handles authentication + rate limiting
- **REST API** (`wfc/servers/rest_api/`): FastAPI with Traefik reverse proxy
- **Shared Infrastructure**: APIKeyStore, TokenBucket, ProjectRateLimiter, WorktreePool, ReviewOrchestrator

### 2.2 Critical Gaps

| Gap | Current Impact | Risk |
|-----|----------------|------|
| **Duplicate Authentication** | APIKeyStore used in both MCP and REST with different validation contexts | Inconsistent security, hard to audit |
| **Inconsistent Rate Limiting** | MCP uses global TokenBucket; REST uses TokenBucket + ProjectRateLimiter + Traefik | One project can starve others in MCP |
| **No Unified Audit Trail** | REST has implicit audit logging; MCP has explicit AuthAuditor calls | Cannot correlate cross-transport events |
| **No Transport Abstraction** | ReviewOrchestrator mixed with transport concerns | Future transports (gRPC, AMQP) require code duplication |
| **No Credential Lifecycle** | API keys created via REST only, no rotation/expiration/scopes | Security risk for long-lived credentials |

### 2.3 Existing Integration Points

**Files**:

- `wfc/servers/mcp_server.py` — MCP entry point (277 lines)
- `wfc/servers/rest_api/main.py` — FastAPI application
- `wfc/servers/rest_api/auth.py` — APIKeyStore (shared)
- `wfc/servers/rest_api/audit.py` — AuthAuditor (REST only)
- `wfc/shared/rate_limiting.py` — ProjectRateLimiter (REST only)
- `wfc/shared/resource_pool.py` — TokenBucket (both transports)

---

## 3. Requirements

### MUST (Non-Negotiable)

#### M-000: Central Artifact Storage System 🆕

**Requirement**: All development artifacts (plans, reviews, BA docs, test results, implementations) stored in centralized system accessible via MCP/API.

**Acceptance**:

- Database schema for artifacts: `{artifact_id, project_id, artifact_type, content, metadata, created_at, created_by}`
- Artifact types: `plan`, `review`, `ba`, `test_result`, `implementation`, `validation`
- MCP resource: `artifact://project/{project_id}/type/{type}` returns list
- MCP resource: `artifact://project/{project_id}/artifact/{artifact_id}` returns single artifact
- REST endpoints: `GET /v1/projects/{id}/artifacts`, `POST /v1/projects/{id}/artifacts`
- Agents can POST artifacts back after completing work
- Teams can query/search all artifacts via API

**Storage**: SQLite for MVP (simple, embedded), PostgreSQL for production scale

**Performance**: Artifact retrieval < 50ms (P95), search < 200ms (P95)

**Schema Example**:

```sql
CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,  -- plan, review, ba, test_result, implementation
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- Markdown or JSON
    metadata JSONB,  -- {consensus_score, passed, agent_id, task_ids, etc.}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,  -- developer_id or agent_id
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_artifacts_project_type ON artifacts(project_id, artifact_type);
CREATE INDEX idx_artifacts_created_at ON artifacts(created_at DESC);
```

---

#### M-001: Unified Authentication Gateway

**Requirement**: Centralize API key validation for all transports (MCP, REST, future gRPC).

**Acceptance**:

- Single `AuthGateway` class used by both MCP and REST servers
- APIKeyStore accessed only through AuthGateway
- All auth attempts logged to unified audit trail
- Zero code duplication between transports

**Performance**: Auth latency < 5ms (P95)

**Security**:

- Constant-time comparison for API keys
- SHA256 hashing maintained
- Failed attempt tracking across transports

---

#### M-002: Consistent Per-Project Rate Limiting

**Requirement**: Enforce ProjectRateLimiter quotas for all transports, not just REST.

**Acceptance**:

- MCP requests subject to same per-project quotas as REST
- No project can starve others (eliminate global TokenBucket)
- Rate limit headers returned in all responses (Retry-After, remaining, reset)
- Traefik layer understands project isolation (not just IP-based)

**Performance**: Rate limit check < 3ms (P95)

---

#### M-003: Request Normalization Layer

**Requirement**: Abstract transport differences into unified `ReviewRequest` model.

**Acceptance**:

- MCP `{project_id, api_key, diff_content}` → `ReviewRequest`
- REST `{X-Project-ID, Authorization, body}` → `ReviewRequest`
- Future gRPC/AMQP transports → same `ReviewRequest`
- ReviewOrchestrator receives only `ReviewRequest` (no transport awareness)

**Testing**: Add gRPC transport without modifying ReviewOrchestrator

---

#### M-004: Unified Observability Pipeline

**Requirement**: Emit telemetry events with correlation IDs across all transports.

**Acceptance**:

- Every request gets unique `request_id` (UUID v4)
- Audit logs include: request_id, project_id, transport, auth_duration, rate_limit_duration, execution_duration, consensus_score, passed
- Prometheus metrics exposed: request_count, latency_histogram, error_rate (by transport, project_id, endpoint)
- Jaeger/Datadog traces with correlation IDs

**Performance**: Telemetry overhead < 1ms per request

---

#### M-005: Living Documentation API 🆕

**Requirement**: Query and generate insights from all stored artifacts.

**Acceptance**:

- **Search endpoint**: `GET /v1/projects/{id}/artifacts/search?q={query}` (full-text search)
- **Timeline endpoint**: `GET /v1/projects/{id}/timeline` (chronological activity feed)
- **Insights endpoint**: `GET /v1/projects/{id}/insights` (aggregate metrics: review pass rate, common findings, plan completion rate)
- **Dependency graph**: `GET /v1/projects/{id}/dependencies` (which artifacts reference each other)
- **MCP resource**: `insights://project/{project_id}/summary` (generated documentation)

**Insights Generated**:

- Review pass rate over time (trend analysis)
- Most common security findings (from all reviews)
- Plan vs actual completion (planned tasks vs implemented)
- Token usage per workflow (cost tracking)
- Agent performance metrics (which agents deliver best results)

**Performance**: Search < 200ms (P95), insights generation < 500ms (P95)

**Output Format**: Markdown summary + JSON data

---

#### M-006: OAuth 2.1 Support (Future-Proof)

**Requirement**: Prepare gateway architecture for OAuth 2.1 integration.

**Acceptance**:

- AuthGateway interface supports both API keys and OAuth tokens
- OAuth Protected Resource Metadata (RFC9728) endpoint implemented
- Dynamic Client Registration (DCR) endpoint implemented
- On-Behalf-Of (OBO) token delegation pattern supported

**Timeline**: Phase 2 (not MVP)

---

### SHOULD (Valuable, Deferrable)

#### S-000: Team Dashboard 🆕

**Requirement**: Web UI for teams to visualize all AI development activity.

**Benefit**:

- Non-technical stakeholders see what agents are doing
- Product managers track feature progress without CLI
- Compliance teams audit AI agent decisions

**Features**:

- Real-time activity feed (agents posting artifacts)
- Project timeline visualization
- Review results dashboard (pass/fail trends)
- Plan progress tracking (tasks completed vs pending)
- Token usage analytics (cost per project)

**Tech Stack**: React + FastAPI backend (reuse existing REST API)

**Defer**: Build API first (M-000, M-005), dashboard consumes it later

---

#### S-001: Multi-Cloud Routing

**Requirement**: Route requests to regional MCP servers based on geo-location.

**Benefit**: Reduced latency for global users, compliance with data residency requirements.

**Defer**: Until WFC has multi-region deployments.

---

#### S-002: Circuit Breakers

**Requirement**: Implement circuit breakers for failing upstream services.

**Benefit**: Prevents cascading failures, improves resilience.

**Defer**: Can add incrementally after MVP.

---

#### S-003: Dynamic Configuration

**Requirement**: Update gateway routing rules without downtime (hot-reload).

**Benefit**: Operational flexibility, zero-downtime updates.

**Defer**: Static configuration acceptable for MVP.

---

### COULD (Future Iteration)

#### C-000: Agent Collaboration Channels 🆕

**Requirement**: Agents post status updates to shared channels (like Slack for AI agents).

**Benefit**:

- Agents coordinate work (wfc-implement agents share test results)
- Humans follow along in real-time
- Async agent workflows (agent A posts artifact, agent B consumes it later)

**Implementation**:

- WebSocket endpoint for real-time updates
- Channel types: `project:{id}:reviews`, `project:{id}:implementations`
- Message format: `{event: "artifact_created", artifact_id, project_id, summary}`

**Defer**: Requires WebSocket infrastructure, not critical for MVP

---

#### C-001: Unified Tool Catalog

**Requirement**: Gateway builds unified catalog of all 30 WFC skills.

**Benefit**: Agents discover tools dynamically without hardcoded references.

**Defer**: Current wfc-* skill system works well, low ROI.

---

#### C-002: Session State Management

**Requirement**: Gateway manages session state for multi-turn interactions.

**Benefit**: Enables stateful agent conversations.

**Defer**: Current knowledge system handles context, not critical.

---

### WON'T (Explicit Exclusion)

#### W-001: Replace Traefik

**Reason**: Traefik provides battle-tested HTTPS termination, Let's Encrypt, infrastructure-level rate limiting. Gateway should complement, not replace.

---

#### W-002: Implement Full MCP Proxy

**Reason**: WFC is an MCP server, not a proxy. Gateway focuses on auth/rate-limit/observability, not protocol translation.

---

#### W-003: Support Legacy Transports

**Reason**: No need for SSE (deprecated) or legacy JSON-RPC patterns. Modern Streamable HTTP + stdio only.

---

#### W-004: Build Custom Time-Series Database 🆕

**Reason**: Use existing solutions (Prometheus for metrics, SQLite/PostgreSQL for artifacts). Don't reinvent time-series storage.

---

## 4. Integration Seams

### Input From

| Source | Data | Transport |
|--------|------|-----------|
| Claude Desktop | MCP tool calls (`review_code`) | stdio |
| HTTP Clients | REST API requests (`POST /v1/reviews`) | HTTPS via Traefik |
| Future gRPC Clients | gRPC `ReviewService.SubmitReview` | gRPC/HTTP2 |

### Output To

| Consumer | Data | Transport |
|----------|------|-----------|
| ReviewOrchestrator | Normalized `ReviewRequest` | In-process function call |
| Audit System | Auth events, request telemetry | File (`~/.wfc/audit/`) + Prometheus |
| Traefik | Rate limit headers, error responses | HTTP headers |

### Files Touched

**Modified**:

- `wfc/servers/mcp_server.py` — Use AuthGateway, RateLimitGateway, RequestGateway
- `wfc/servers/rest_api/routes.py` — Use same gateways in dependencies
- `wfc/servers/rest_api/dependencies.py` — Move logic to gateway layer

**New Files Created**:

- `wfc/servers/gateway/auth_gateway.py` — Unified authentication
- `wfc/servers/gateway/rate_limit_gateway.py` — Per-project rate limiting
- `wfc/servers/gateway/request_gateway.py` — Request normalization
- `wfc/servers/gateway/observability.py` — Telemetry pipeline
- `wfc/servers/gateway/__init__.py` — Gateway public API

---

## 5. Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Auth Latency (P95)** | < 5ms | Prometheus histogram: `wfc_gateway_auth_duration_seconds` |
| **Rate Limit Check (P95)** | < 3ms | Prometheus histogram: `wfc_gateway_rate_limit_duration_seconds` |
| **Telemetry Overhead** | < 1ms per request | Measure with/without telemetry enabled |
| **Backward Compatibility** | 100% (no breaking changes) | Existing MCP and REST clients work unchanged |
| **Code Coverage** | ≥ 85% for gateway layer | pytest --cov=wfc/servers/gateway |
| **Gateway Uptime** | 99.9% (same as Traefik) | Monitor with health checks |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Breaking existing MCP clients** | Medium | High | Comprehensive integration tests, feature flags for gradual rollout |
| **Performance regression** | Low | Medium | Benchmark before/after, profile gateway code paths |
| **Audit log storage growth** | Medium | Low | Log rotation policy, archive to S3/GCS after 30 days |
| **Gateway becomes single point of failure** | Medium | High | Health checks, circuit breakers, graceful degradation |
| **OAuth integration complexity** | High | Medium | Phase 2, defer until API keys proven insufficient |

---

## 7. Prior Art

### Industry MCP Gateways (2026)

**Solo.io Agent Gateway**:

- **Strength**: Purpose-built for multi-agent orchestration (A2A operations)
- **Adopt**: Service mesh approach for distributed reviewers, unified data plane
- **Relevance**: WFC's 5 parallel reviewers match Solo.io's agent coordination model

**Apache APISix**:

- **Strength**: Plugin architecture (Lua + WASM), cloud-native K8s design
- **Adopt**: Dynamic routing, payload modification for token budget enforcement
- **Relevance**: Matches WFC's hooks system (PreToolUse/PostToolUse)

**Lunar MCPX**:

- **Strength**: Multi-server aggregation, cost optimization, governance
- **Adopt**: Aggregate WFC's 30 skills through single MCP client
- **Relevance**: Aligns with WFC's 99% token reduction strategy

**MCP Ecosystem MCP Gateway**:

- **Strength**: Zero-code Docker deployment, protocol-native session handling
- **Adopt**: Lightweight prototyping option before committing to heavier solutions
- **Relevance**: Good for testing gateway integration strategy

**Traefik Hub (Triple-Gate Pattern)**:

- **Strength**: Defense-in-depth (AI model, MCP protocol, API layers)
- **Adopt**: Layered security approach
- **Relevance**: WFC already uses Traefik, natural extension

### Security Best Practices

**Triple-Gate Pattern**:

- Gate 1: AI Client → LLM (prompt injection protection, PII filtering)
- Gate 2: LLM → MCP Server (tool authorization, parameter validation)
- Gate 3: MCP Server → External API (rate limiting, credential management)

**OAuth 2.1 Integration**:

- Short-lived, server-specific tokens
- Resource Indicators scoped aggressively
- Never leak credentials into LLM context
- Token validation on every request (issuer, audience, expiration, scopes)

**Distributed Rate Limiting**:

- Sub-3ms latency under load
- Handles authentication in-memory (not database queries)
- Prevents agent runaway scenarios

---

## 8. Out of Scope

- **Full MCP Proxy Implementation**: WFC is an MCP server, not a proxy. Gateway focuses on auth/rate-limit/observability.
- **Replacing Traefik**: Existing infrastructure works well. Gateway complements, not replaces.
- **Supporting Legacy SSE Transport**: Modern Streamable HTTP + stdio only.
- **Multi-Tenant SaaS Platform**: WFC is open-source tooling, not SaaS. Gateway enables self-hosted multi-tenancy, not managed service.
- **Tool Discovery/Catalog**: Current wfc-* skill system sufficient, low ROI for unified catalog.

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **MCP (Model Context Protocol)** | Standard protocol for AI agent-to-tool communication, uses JSON-RPC 2.0 |
| **Transport** | Communication mechanism (stdio, Streamable HTTP, gRPC) |
| **Tool Call** | MCP operation where AI agent invokes a tool (e.g., `review_code`) |
| **ProjectContext** | WFC's per-project isolation context (API keys, rate limits, directories) |
| **Triple-Gate Pattern** | Defense-in-depth security with 3 layers (AI client, MCP server, external API) |
| **On-Behalf-Of (OBO)** | OAuth pattern where MCP server acts with same identity/permissions as original client |
| **OAuth 2.1** | Latest OAuth specification with improved security (PKCE, refresh token rotation) |
| **Streamable HTTP** | Modern MCP transport (replaces legacy SSE), supports bidirectional streaming |
| **JSON-RPC 2.0** | MCP's wire format for request/response messages |
| **Session Affinity** | Routing pattern where requests with same `session_id` go to same server instance |

---

## 10. Implementation Roadmap

### Phase 1: Platform Foundation (MVP) 🔄 UPDATED

**Scope**: M-000 (Artifact Storage), M-001 (Auth), M-002 (Rate Limit), M-003 (Request Normalization), M-004 (Observability), M-005 (Living Documentation)

**Deliverables**:

**Gateway Layer**:

- `wfc/servers/gateway/auth_gateway.py` — Unified authentication
- `wfc/servers/gateway/rate_limit_gateway.py` — Per-project rate limiting
- `wfc/servers/gateway/request_gateway.py` — Request normalization
- `wfc/servers/gateway/observability.py` — Telemetry pipeline

**Artifact Storage** 🆕:

- `wfc/storage/artifact_store.py` — SQLite/PostgreSQL abstraction
- `wfc/storage/models.py` — Artifact, Project, Developer models
- `wfc/storage/migrations/` — Schema migrations (Alembic)
- Database: `~/.wfc/artifacts.db` (SQLite for MVP)

**Living Documentation API** 🆕:

- `wfc/servers/rest_api/artifact_routes.py` — CRUD + search + insights endpoints
- `wfc/servers/mcp_server.py` updates — New resources: `artifact://`, `insights://`
- `wfc/analysis/insights_generator.py` — Generate aggregate insights from artifacts

**Integration**:

- Modified `mcp_server.py` to use gateways + post artifacts
- Modified `rest_api/routes.py` to use gateways + artifact endpoints
- wfc-review posts REVIEW.md to artifact store after completion
- wfc-plan posts TASKS.md to artifact store after generation
- wfc-ba posts BA docs to artifact store

**Testing**:

- Integration tests (85% coverage)
- Performance benchmarks (auth < 5ms, rate limit < 3ms, artifact retrieval < 50ms)

**Success Criteria**:

- Existing MCP and REST clients work unchanged
- All requests flow through gateways (audit logs confirm)
- Per-project rate limiting works for both transports
- Prometheus metrics exposed and validated
- **Artifacts stored after every workflow** (review, plan, BA) 🆕
- **Living documentation generated** (insights API returns metrics) 🆕
- **Teams can query artifacts via API** (search works, timeline works) 🆕

---

### Phase 2: Team Dashboard + Advanced Features

**Scope**: S-000 (Team Dashboard), M-006 (OAuth 2.1), S-002 (circuit breakers)

**Deliverables**:

**Team Dashboard** 🆕:

- React frontend (`wfc/ui/`) — Activity feed, timeline, insights charts
- WebSocket integration — Real-time artifact updates
- Authentication — OAuth login for team members
- Deployment — Docker container, Traefik routing

**OAuth 2.1**:

- OAuth Protected Resource Metadata (RFC9728) endpoint
- Dynamic Client Registration (DCR) endpoint
- On-Behalf-Of (OBO) token delegation

**Security Hardening**:

- Circuit breakers for ReviewOrchestrator
- PII redaction in audit logs
- Prompt injection detection (Gate 1)

**Success Criteria**:

- OAuth flow tested with external identity provider (Auth0, Okta)
- Circuit breaker trips and recovers correctly under load
- PII never appears in audit logs
- **Team dashboard deployed and accessible** (teams can see agent activity) 🆕
- **Real-time updates working** (WebSocket pushes artifact events) 🆕

---

### Phase 3: Enterprise Scale + SaaS

**Scope**: S-001 (multi-cloud routing), S-003 (dynamic config), C-000 (agent collaboration channels)

**Deliverables** 🆕:

- Multi-region deployment (US, EU, APAC)
- Agent collaboration channels (WebSocket pub/sub)
- SaaS offering (managed WFC platform)
- Enterprise features (SSO, RBAC, compliance reporting)

**Defer**: Until WFC has proven product-market fit and enterprise demand.

---

## 11. Acceptance Criteria Summary

**Gateway Integration Complete When**:

✅ **Auth**: All transports use `AuthGateway`, zero code duplication
✅ **Rate Limit**: Per-project quotas enforced consistently (both MCP and REST)
✅ **Observability**: Correlation IDs in all logs, Prometheus metrics exposed
✅ **Performance**: Auth < 5ms (P95), rate limit < 3ms (P95), telemetry < 1ms
✅ **Compatibility**: Existing clients work unchanged
✅ **Testing**: ≥ 85% coverage, integration tests pass
✅ **Documentation**: Gateway architecture documented in `docs/GATEWAY.md`

---

## 12. Strategic Vision: WFC as AI Development Platform

### The Big Picture

**Today**: WFC is a CLI tool that agents use locally, artifacts scattered in git repos.

**Tomorrow**: WFC is a **centralized platform** where:

- All AI development work flows through MCP/API
- Every artifact (plan, review, BA, test, implementation) stored centrally
- Teams query and search all work via living documentation API
- Dashboard visualizes AI agent activity in real-time
- Agents collaborate asynchronously through shared artifact store

### Why This Matters

**Single Source of Truth**:

- No more scattered REVIEW.md files in git branches
- No more lost planning documents in old PRs
- No more "what did the agent actually do?" questions

**Living Documentation**:

- Auto-generated from actual work artifacts
- Always up-to-date (agents post updates continuously)
- Searchable, queryable, analyzable

**Team Visibility**:

- Product managers see feature progress without CLI
- Compliance teams audit AI decisions via artifact trail
- Developers discover patterns (common findings, best practices)

**Foundation for SaaS**:

- Multi-tenant architecture already in place
- API-first design enables external integrations
- Dashboard provides non-technical user experience

### Path to Production

**Phase 1** (3-4 months): Platform MVP

- Artifact storage + living documentation API
- Gateway consolidation (auth, rate-limit, observability)
- Agent integration (wfc-review, wfc-plan, wfc-ba post artifacts)

**Phase 2** (2-3 months): Team Experience

- Team dashboard (React UI)
- OAuth 2.1 for team login
- Real-time updates (WebSocket)

**Phase 3** (6-12 months): Enterprise + SaaS

- Multi-region deployment
- Enterprise features (SSO, RBAC, compliance)
- SaaS offering (managed WFC platform)

---

## 13. Next Steps

1. **Validate BA with `/wfc-validate`** — Ensure completeness before planning
2. **Generate Plan with `/wfc-plan`** — Create TASKS.md with TDD test plans (focus on Phase 1)
3. **Prototype Artifact Storage** — SQLite schema, basic CRUD operations
4. **Implement Gateway Layer** — Auth, rate-limit, request normalization
5. **Integrate with wfc-review** — Post REVIEW.md to artifact store after completion
6. **Build Living Documentation API** — Search, timeline, insights endpoints
7. **Deploy to Staging** — Test with real MCP clients + artifact posting
8. **Team Alpha Testing** — Get feedback on artifact storage + search
9. **Phase 2 Planning** — Design team dashboard based on Phase 1 learnings

---

**Business Analysis Complete**: 2026-02-22
**Next Action**: `/wfc-validate` on this BA document
