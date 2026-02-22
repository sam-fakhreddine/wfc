# WFC2 Platform Transformation Roadmap

**Branch**: `feat/wfc2-platform`
**Start Date**: 2026-02-22
**Status**: In Progress
**Vision**: Transform WFC from CLI tool → Centralized AI Development Platform

---

## Overview

WFC2 represents a major architectural evolution:

**Before (WFC 1.0)**: CLI tool, local artifacts, stdio/REST transports
**After (WFC 2.0)**: Platform with artifact storage, living documentation, team dashboard

---

## Phase 1: Platform Foundation (3-4 months)

### M-000: Central Artifact Storage System

- [ ] Database schema (SQLite for MVP)
- [ ] `wfc/storage/artifact_store.py`
- [ ] `wfc/storage/models.py`
- [ ] Alembic migrations
- [ ] MCP resources: `artifact://`, `insights://`
- [ ] REST endpoints: `/v1/projects/{id}/artifacts`

### M-001: Unified Authentication Gateway

- [ ] `wfc/servers/gateway/auth_gateway.py`
- [ ] Consolidate APIKeyStore access
- [ ] Unified audit logging

### M-002: Consistent Per-Project Rate Limiting

- [ ] `wfc/servers/gateway/rate_limit_gateway.py`
- [ ] ProjectRateLimiter for all transports
- [ ] Rate limit headers

### M-003: Request Normalization Layer

- [ ] `wfc/servers/gateway/request_gateway.py`
- [ ] `ReviewRequest` model
- [ ] MCP/REST → unified request

### M-004: Unified Observability Pipeline

- [ ] `wfc/servers/gateway/observability.py`
- [ ] Correlation IDs
- [ ] Prometheus metrics
- [ ] Jaeger/Datadog traces

### M-005: Living Documentation API

- [ ] `wfc/servers/rest_api/artifact_routes.py`
- [ ] `wfc/analysis/insights_generator.py`
- [ ] Search endpoint (full-text)
- [ ] Timeline endpoint
- [ ] Insights endpoint (metrics)
- [ ] Dependency graph

### Integration

- [ ] wfc-review posts REVIEW.md to artifact store
- [ ] wfc-plan posts TASKS.md to artifact store
- [ ] wfc-ba posts BA docs to artifact store
- [ ] MCP server uses gateways
- [ ] REST API uses gateways

### Testing

- [ ] Unit tests (85% coverage)
- [ ] Integration tests (gateway → storage)
- [ ] Performance benchmarks (auth < 5ms, artifacts < 50ms)

---

## Phase 2: Team Experience (2-3 months)

### S-000: Team Dashboard

- [ ] React frontend (`wfc/ui/`)
- [ ] Activity feed
- [ ] Timeline visualization
- [ ] Review trends dashboard
- [ ] Token analytics

### M-006: OAuth 2.1 Support

- [ ] OAuth Protected Resource Metadata (RFC9728)
- [ ] Dynamic Client Registration (DCR)
- [ ] On-Behalf-Of (OBO) token delegation

### S-002: Circuit Breakers

- [ ] ReviewOrchestrator resilience
- [ ] Retry logic
- [ ] Graceful degradation

### Real-Time Updates

- [ ] WebSocket infrastructure
- [ ] Artifact event stream
- [ ] Dashboard live updates

---

## Phase 3: Enterprise + SaaS (6-12 months)

### S-001: Multi-Cloud Routing

- [ ] Regional MCP servers (US, EU, APAC)
- [ ] Geo-aware routing
- [ ] Data residency compliance

### C-000: Agent Collaboration Channels

- [ ] WebSocket pub/sub
- [ ] Project channels
- [ ] Agent coordination

### Enterprise Features

- [ ] SSO integration
- [ ] RBAC (role-based access control)
- [ ] Compliance reporting
- [ ] Audit trail export

### SaaS Platform

- [ ] Multi-tenant SaaS offering
- [ ] Billing integration
- [ ] Customer dashboard
- [ ] Enterprise support

---

## Development Guidelines

### Branch Strategy

```
main (production releases)
  ↑
develop (integration)
  ↑
feat/wfc2-platform (WFC2 work)
  ↑
feat/wfc2-* (sub-features)
```

**Sub-feature branches**:

- `feat/wfc2-artifact-storage` (M-000)
- `feat/wfc2-gateway-auth` (M-001)
- `feat/wfc2-gateway-rate-limit` (M-002)
- `feat/wfc2-gateway-request` (M-003)
- `feat/wfc2-observability` (M-004)
- `feat/wfc2-living-docs` (M-005)

### Merge Strategy

1. Sub-features → `feat/wfc2-platform` (PR review required)
2. `feat/wfc2-platform` → `develop` (periodic integration, every 2 weeks)
3. `develop` → `main` (after Phase 1 complete)

### Compatibility

**Critical**: WFC2 must maintain backward compatibility with WFC 1.0 clients.

- Existing MCP clients (Claude Desktop) work unchanged
- Existing REST clients work unchanged
- Artifact storage is additive (doesn't break existing workflows)

### Testing Requirements

- **Unit tests**: 85% coverage minimum
- **Integration tests**: All gateway + storage paths
- **Performance tests**: Auth < 5ms, artifacts < 50ms, search < 200ms
- **Load tests**: 100 concurrent requests, 1000 artifacts
- **Backward compat tests**: Ensure WFC 1.0 clients still work

### Documentation

- `docs/GATEWAY.md` — Gateway architecture
- `docs/ARTIFACT_STORAGE.md` — Storage design
- `docs/LIVING_DOCS.md` — Documentation API
- `docs/MIGRATION.md` — WFC 1.0 → 2.0 migration guide

---

## Success Metrics

### Phase 1 (Platform Foundation)

- ✅ All artifacts stored in central DB
- ✅ Living documentation API returns insights
- ✅ Teams can search/query artifacts
- ✅ Zero breaking changes for existing clients
- ✅ Performance targets met (auth < 5ms, artifacts < 50ms)

### Phase 2 (Team Experience)

- ✅ Dashboard deployed and accessible
- ✅ Real-time updates working (WebSocket)
- ✅ OAuth 2.1 integration tested
- ✅ 10+ teams using dashboard

### Phase 3 (Enterprise + SaaS)

- ✅ Multi-region deployment (3+ regions)
- ✅ SSO + RBAC working
- ✅ 50+ enterprise customers
- ✅ 99.9% uptime SLA

---

## Risk Management

### Technical Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing clients | Comprehensive backward compat tests, feature flags |
| Database performance | Profile early, optimize indexes, use PostgreSQL for scale |
| Gateway becomes bottleneck | Load tests, circuit breakers, horizontal scaling |
| Storage growth unbounded | Retention policies, archival to S3/GCS |

### Product Risks

| Risk | Mitigation |
|------|------------|
| Teams don't adopt dashboard | User research, alpha testing, feedback loops |
| Artifact storage not valuable | Validate with beta users in Phase 1 |
| Too complex for open-source | Keep SQLite option, simple deployment |

---

## Communication

### Status Updates

- **Weekly**: Progress report in #wfc2-dev channel
- **Bi-weekly**: Demo to stakeholders
- **Monthly**: Roadmap review and adjustments

### Stakeholder Communication

- **Developers**: GitHub issues, PR comments
- **Users**: Release notes, migration guides
- **Enterprise**: Customer success calls

---

## Current Status (2026-02-22)

**Completed**:

- ✅ BA document (WFC2 vision, requirements)
- ✅ Competitive analysis (MCP gateways)
- ✅ Branch created (`feat/wfc2-platform`)

**In Progress**:

- 🔄 Planning Phase 1 implementation

**Next Steps**:

1. Run `/wfc-validate` on BA document
2. Generate Phase 1 implementation plan (`/wfc-plan`)
3. Start with M-000 (artifact storage) as foundation
4. Build gateway layer on top of storage

---

**Last Updated**: 2026-02-22
**Branch**: feat/wfc2-platform
**Lead**: Claude Code + Team
