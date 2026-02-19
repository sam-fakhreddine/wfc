# Roadmap: Dashboard & Observability Plugin System

**Status:** Draft
**Motivation:** Internal ops -- we need visibility into our own WFC deployment (review scores, knowledge health, agent activity) and want to dogfood the plugin system.
**Scope:** Dashboard + Observability ONLY. No OIDC/SSO, no RBAC (revisit after plugin system proves out).
**Architecture:** Plugin system -- core review pipeline stays untouched; enterprise features are first-party plugins.

---

## Current State

WFC already produces significant telemetry. The problem is consumption, not production.

### What Exists (Ready to Consume)

| Data Source | Format | Location | Content |
|-------------|--------|----------|---------|
| AutoTelemetry | JSONL | `~/.wfc/telemetry/session-*.jsonl` | Task metrics: duration, tokens, complexity, test results, review scores |
| Generic Events | JSONL | `~/.wfc/telemetry/events.jsonl` | pr_created, hook_warning, workflow_violation, merge_complete |
| Aggregate Stats | JSON | `~/.wfc/telemetry/aggregate.json` | Rolling 100-task aggregate |
| Workflow Metrics | JSONL | `~/.wfc/memory/workflow_metrics.jsonl` | Per-task token usage, success rate, coverage |
| Bypass Audit Trail | JSON | `BYPASS-AUDIT.json` | Emergency bypass records with CS at time of bypass |
| Review Reports | Markdown | `REVIEW-{task_id}.md` | Full findings, CS score, tier, MPR status |
| Knowledge Files | Markdown | `wfc/reviewers/{id}/KNOWLEDGE.md` | Accumulated learnings per reviewer |

### What's Missing

| Gap | Impact |
|-----|--------|
| No plugin registry/loader | Can't add features without modifying core |
| No event subscription API | Plugins can't react to WFC events |
| No structured review export | CS results are markdown-only; dashboard needs JSON |
| No web server | No HTTP endpoint for dashboard or Prometheus scraping |
| No metric aggregation API | Each consumer must parse raw JSONL themselves |

---

## Phase 0: Structured Review Export (Pre-Plugin Foundation)

**Goal:** Make review results machine-consumable before building the plugin system.

**Why first:** The dashboard plugin is useless without structured review data. This is a small change to the existing orchestrator that pays dividends immediately (CI integration, GitHub PR comments, any future consumer).

**Changes:**

1. **Add JSON export to `orchestrator.py:finalize_review()`**
   - Write `REVIEW-{task_id}.json` alongside the existing `REVIEW-{task_id}.md`
   - Contains: `ConsensusScoreResult` (cs, tier, passed, minority_protection_applied), all `DeduplicatedFinding` objects, reviewer summaries, timestamps
   - Schema versioned (`"schema_version": "1.0"`) for forward compatibility

2. **Add JSON format to `cli.py`**
   - `wfc review --format json` already exists but outputs to stdout
   - Also write to disk so plugins can read asynchronously

3. **Emit review events via AutoTelemetry**
   - `log_event("review_complete", {"task_id": ..., "cs": ..., "tier": ..., "findings_count": ..., "mpr_applied": ...})`
   - `log_event("knowledge_updated", {"reviewer_id": ..., "entries_added": ..., "section": ...})`
   - `log_event("drift_detected", {"reviewer_id": ..., "signals": [...], "recommendation": ...})`

**Effort:** Small (1-2 days). Touches `orchestrator.py`, `cli.py`, `knowledge_writer.py`, `drift_detector.py`.

**Files modified:**

- `wfc/scripts/skills/review/orchestrator.py` -- add `_write_json_report()`
- `wfc/scripts/skills/review/cli.py` -- add disk write for JSON format
- `wfc/scripts/knowledge/knowledge_writer.py` -- add `log_event()` call in `append_entries()`
- `wfc/scripts/knowledge/drift_detector.py` -- add `log_event()` call in `analyze()`

---

## Phase 1: Plugin Foundation

**Goal:** A minimal plugin system that lets plugins subscribe to WFC events and expose HTTP endpoints.

### Plugin Discovery & Loading

```
~/.wfc/plugins/
├── wfc-dashboard/
│   ├── plugin.toml          # Metadata + entry point
│   └── dashboard_plugin.py  # Plugin implementation
├── wfc-observability/
│   ├── plugin.toml
│   └── observability_plugin.py
└── ...
```

**plugin.toml:**

```toml
[plugin]
name = "wfc-dashboard"
version = "0.1.0"
description = "Visual dashboard for WFC review metrics"
entry_point = "dashboard_plugin:DashboardPlugin"
requires = ["wfc>=2.0"]

[plugin.events]
subscribes = ["review_complete", "knowledge_updated", "drift_detected", "task_complete"]

[plugin.http]
enabled = true
port_range = [9400, 9410]  # Plugin picks first available
```

### Plugin Lifecycle Protocol

```python
class WFCPlugin(Protocol):
    """Interface that all WFC plugins must implement."""

    name: str
    version: str

    def on_activate(self, context: PluginContext) -> None:
        """Called when plugin is loaded. Receive event bus + data access."""
        ...

    def on_event(self, event: WFCEvent) -> None:
        """Called when a subscribed event fires."""
        ...

    def on_deactivate(self) -> None:
        """Called on shutdown. Clean up resources."""
        ...
```

### Plugin Context (What Plugins Receive)

```python
@dataclass
class PluginContext:
    """Read-only access to WFC data for plugins."""

    telemetry_dir: Path          # ~/.wfc/telemetry/
    memory_dir: Path             # ~/.wfc/memory/
    reviewers_dir: Path          # wfc/reviewers/
    reviews_dir: Path            # Where REVIEW-*.json files live
    bypass_audit_path: Path      # BYPASS-AUDIT.json

    def query_telemetry(self, days: int = 30) -> list[TaskMetrics]: ...
    def query_reviews(self, days: int = 30) -> list[dict]: ...
    def query_drift(self, reviewer_id: str) -> DriftReport: ...
    def query_bypasses(self, active_only: bool = True) -> list[BypassRecord]: ...
```

Plugins get **read-only** access to WFC data. They cannot modify reviews, knowledge, or core state.

### Plugin Registry

```python
# wfc/scripts/plugins/registry.py

class PluginRegistry:
    """Discovers, loads, and manages WFC plugins."""

    def discover(self) -> list[PluginManifest]: ...
    def load(self, plugin_name: str) -> WFCPlugin: ...
    def load_all(self) -> list[WFCPlugin]: ...
    def dispatch_event(self, event: WFCEvent) -> None: ...
    def shutdown(self) -> None: ...
```

### Event Dispatch Integration

Wire into existing code with minimal changes:

```python
# In orchestrator.py:finalize_review(), after generating report:
if self.plugin_registry:
    self.plugin_registry.dispatch_event(WFCEvent(
        type="review_complete",
        data={"task_id": task_id, "cs": result.cs, "tier": result.tier, ...}
    ))
```

The `plugin_registry` is optional -- if no plugins are installed, there is zero overhead. Core never depends on plugins.

**Effort:** Medium (3-5 days). New module `wfc/scripts/plugins/` with registry, loader, protocol, context.

**New files:**

- `wfc/scripts/plugins/__init__.py`
- `wfc/scripts/plugins/registry.py` -- discovery + loading
- `wfc/scripts/plugins/protocol.py` -- `WFCPlugin` protocol + `PluginContext`
- `wfc/scripts/plugins/events.py` -- `WFCEvent` dataclass + dispatch
- `wfc/scripts/plugins/loader.py` -- TOML parsing + importlib loading

**Files modified:**

- `wfc/scripts/skills/review/orchestrator.py` -- optional `plugin_registry` param, event dispatch
- `pyproject.toml` -- add `plugins` optional extra with `tomli` dependency

---

## Phase 2: Dashboard Plugin

**Goal:** A local web UI showing review history, CS trends, knowledge health, and active bypasses.

### Architecture

```
wfc-dashboard (plugin)
├── FastAPI app (lightweight, local-only)
├── Reads from PluginContext (telemetry JSONL, review JSONs, drift reports)
├── WebSocket for live updates (subscribes to review_complete, drift_detected)
├── Static HTML + Alpine.js (no build step, no node_modules)
└── Serves on localhost:9400
```

### Dashboard Views

| View | Data Source | Shows |
|------|-----------|-------|
| **Review History** | `REVIEW-*.json` | CS scores over time, pass/fail trend, MPR triggers |
| **Findings Heatmap** | Deduplicated findings | Which files get flagged most, by which reviewer |
| **Knowledge Health** | DriftDetector via PluginContext | Staleness, bloat, contradictions per reviewer |
| **Bypass Monitor** | `BYPASS-AUDIT.json` | Active bypasses, expiry countdown, CS at bypass time |
| **Token Efficiency** | AutoTelemetry JSONL | Tokens per review, per complexity tier, trend |
| **Agent Activity** | `events.jsonl` | Recent task completions, PR creations, merge events |

### Tech Stack Rationale

- **FastAPI** over Flask: async-native, auto-OpenAPI docs, Pydantic validation
- **Alpine.js** over React/Vue: No build step, <15KB, works in a single HTML file
- **WebSocket** over polling: Plugin subscribes to events via `on_event()`, pushes to connected browsers
- **No external DB**: Reads directly from WFC's existing JSONL/JSON files

### Activation

```bash
# Install dashboard plugin
wfc plugin install wfc-dashboard

# Start dashboard (background process)
wfc dashboard
# → Dashboard running at http://localhost:9400

# Or auto-start via WFC config
# ~/.wfc/config.toml:
# [plugins.wfc-dashboard]
# auto_start = true
```

**Effort:** Medium-large (5-8 days). Plugin implementation + 6 dashboard views + WebSocket.

**New files:**

- `~/.wfc/plugins/wfc-dashboard/plugin.toml`
- `~/.wfc/plugins/wfc-dashboard/dashboard_plugin.py` -- FastAPI app + WebSocket
- `~/.wfc/plugins/wfc-dashboard/templates/` -- HTML views with Alpine.js
- `~/.wfc/plugins/wfc-dashboard/static/` -- Minimal CSS

**Dependencies:** `fastapi`, `uvicorn[standard]`, `websockets`

---

## Phase 3: Observability Plugin

**Goal:** Prometheus metrics endpoint + structured log export for SIEM/log aggregation.

### Prometheus Metrics

Exposed at `localhost:9401/metrics` in OpenMetrics format:

```
# HELP wfc_review_consensus_score Consensus Score from the latest review
# TYPE wfc_review_consensus_score gauge
wfc_review_consensus_score{task_id="TASK-001",tier="moderate"} 5.42

# HELP wfc_review_total Total reviews performed
# TYPE wfc_review_total counter
wfc_review_total{tier="informational"} 45
wfc_review_total{tier="moderate"} 23
wfc_review_total{tier="important"} 7
wfc_review_total{tier="critical"} 1

# HELP wfc_review_mpr_applied_total Reviews where Minority Protection Rule fired
# TYPE wfc_review_mpr_applied_total counter
wfc_review_mpr_applied_total 3

# HELP wfc_findings_total Total findings by reviewer and severity tier
# TYPE wfc_findings_total counter
wfc_findings_total{reviewer="security",severity_tier="critical"} 2
wfc_findings_total{reviewer="correctness",severity_tier="moderate"} 15

# HELP wfc_knowledge_entries_total Knowledge entries per reviewer
# TYPE wfc_knowledge_entries_total gauge
wfc_knowledge_entries_total{reviewer="security",section="patterns_found"} 12

# HELP wfc_knowledge_drift_score Drift health score per reviewer (0=healthy, 1=needs_review)
# TYPE wfc_knowledge_drift_score gauge
wfc_knowledge_drift_score{reviewer="security"} 0.0

# HELP wfc_bypass_active Active emergency bypasses
# TYPE wfc_bypass_active gauge
wfc_bypass_active 0

# HELP wfc_tokens_used_total Tokens consumed by WFC operations
# TYPE wfc_tokens_used_total counter
wfc_tokens_used_total{operation="review",complexity="M"} 4500
```

### Structured Log Export

Transform `events.jsonl` into structured format suitable for SIEM ingestion:

```json
{
  "timestamp": "2026-02-17T14:30:00Z",
  "level": "INFO",
  "source": "wfc.review",
  "event_type": "review_complete",
  "task_id": "TASK-001",
  "consensus_score": 5.42,
  "tier": "moderate",
  "passed": true,
  "findings_count": 3,
  "mpr_applied": false,
  "reviewers": ["security", "correctness", "performance", "maintainability", "reliability"]
}
```

Output targets (configurable):

- **File**: `~/.wfc/logs/wfc-structured.jsonl` (default)
- **Syslog**: RFC 5424 via UDP/TCP
- **Stdout**: For containerized environments (pipe to fluentd/vector)

### Alerting Rules (Prometheus-Compatible)

Ship a `wfc.rules.yml` for Prometheus Alertmanager:

```yaml
groups:
  - name: wfc
    rules:
      - alert: WFCReviewBlocked
        expr: wfc_review_consensus_score > 7.0
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Review blocked (CS={{ $value }})"

      - alert: WFCKnowledgeDrift
        expr: wfc_knowledge_drift_score > 0.5
        for: 24h
        labels:
          severity: info
        annotations:
          summary: "Knowledge drift detected for {{ $labels.reviewer }}"

      - alert: WFCBypassActive
        expr: wfc_bypass_active > 0
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} active emergency bypass(es)"
```

**Effort:** Medium (3-5 days). Prometheus client is well-documented; structured logging is straightforward.

**New files:**

- `~/.wfc/plugins/wfc-observability/plugin.toml`
- `~/.wfc/plugins/wfc-observability/observability_plugin.py` -- Prometheus + log export
- `~/.wfc/plugins/wfc-observability/alerting/wfc.rules.yml` -- Alertmanager rules

**Dependencies:** `prometheus_client`

---

## Phase Summary

| Phase | Deliverable | Effort | Prerequisite | Core Changes |
|-------|------------|--------|--------------|-------------|
| **Phase 0** | Structured review JSON export + event emission | 1-2 days | None | Small (3-4 files) |
| **Phase 1** | Plugin foundation (registry, loader, protocol, events) | 3-5 days | Phase 0 | Small (orchestrator gets optional plugin_registry) |
| **Phase 2** | Dashboard plugin | 5-8 days | Phase 1 | None (pure plugin) |
| **Phase 3** | Observability plugin | 3-5 days | Phase 1 | None (pure plugin) |

**Total: 12-20 days across 4 phases.**

Phases 2 and 3 are independent and can run in parallel after Phase 1 completes.

---

## Design Principles

1. **Core never depends on plugins.** The `plugin_registry` parameter is always optional. If no plugins are installed, WFC works exactly as it does today with zero overhead.

2. **Plugins are read-only consumers.** `PluginContext` provides query methods for WFC data. Plugins cannot modify reviews, knowledge, or CS scores. This prevents a dashboard bug from corrupting review results.

3. **No new external services for core.** Plugins may require FastAPI/Prometheus, but core WFC remains dependency-free (`dependencies = []` in pyproject.toml stays empty).

4. **Structured data first, UI second.** Phase 0 (JSON export) benefits CI integration, GitHub PR comments, and any future consumer -- not just the dashboard. If we never build the dashboard, Phase 0 still pays for itself.

5. **Plugin isolation.** Each plugin runs in its own process/thread. A crashing dashboard doesn't affect reviews. A slow Prometheus scrape doesn't block the orchestrator.

---

## What This Roadmap Explicitly Excludes

| Feature | Why Excluded | Revisit When |
|---------|-------------|-------------|
| OIDC/SSO | No multi-user access to WFC today; adds auth complexity without a consumer | WFC runs as a shared service (not CLI) |
| RBAC | Same as OIDC; no access control needed for single-user CLI tool | Multi-user deployment exists |
| Integrity chains | SHA-256 chaining of audit trail; overkill for local JSON files | Compliance requirement (SOC2, etc.) |
| OpenClaw protocol | Multi-agent coordination protocol from Loki; WFC's orchestrator handles this | WFC agents span multiple machines |

These are valid features for a multi-user platform deployment. They are not needed for a single-user CLI tool with internal ops observability. The plugin system makes it easy to add them later without touching core.

---

## Relationship to Loki Analysis

This roadmap **revises Reject #4** from the Loki Mode Analysis. The original rejection was:

> "Enterprise observability and access control should be addressed through integration with existing tools rather than building them into the code quality framework itself."

This roadmap follows that principle exactly:

- Prometheus metrics are **exposed** by WFC but **consumed** by existing Prometheus/Grafana infrastructure
- Structured logs are **emitted** by WFC but **ingested** by existing SIEM/log aggregation
- The dashboard is a **plugin** that reads WFC data, not a feature built into the review pipeline
- Core WFC remains a focused code quality tool; enterprise features are optional add-ons

The rejection of *scope creep* stands. What changes is the mechanism: a plugin system makes enterprise features safe to add because they can't pollute core.
