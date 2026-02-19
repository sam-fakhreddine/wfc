# Business Analysis: Loki Mode — Dashboard & Observability Plugin System

**Document ID:** BA-LOKI-2026-001
**Version:** 1.0
**Date:** 2026-02-17
**Author:** BA Analysis (Claude Agent)
**Status:** Draft — Pending WFC Plan Review

---

## 1. Executive Summary

WFC is a production-grade multi-agent consensus review system with 20 skills, 5 specialist reviewers, a hook infrastructure, a knowledge/RAG pipeline, and a parallel implementation engine. What it **lacks** is any way to observe, measure, or visualize what those systems are doing at runtime.

**Loki Mode** is the codename for a Dashboard & Observability Plugin System that gives WFC real-time introspection — metrics collection, structured event logging, a pluggable provider architecture, and a terminal/HTML dashboard for operators and developers.

### Business Justification

| Problem | Impact | Loki Mode Solution |
|---------|--------|---------------------|
| No visibility into review cycle times | Can't identify bottlenecks or regressions | Metrics collector tracks review duration, CS scores, finding counts per reviewer |
| Hook failures are silently swallowed (exit 0) | Security/quality regressions go unnoticed | Event emitter captures every hook decision with structured payloads |
| No way to compare reviewer effectiveness | Can't tune temperatures or knowledge files | Per-reviewer analytics: precision, recall, agreement rate, false-positive rate |
| Token budgets are estimated (len//4) | Over/under-spend is invisible | Token accounting per review phase, agent, and skill invocation |
| Knowledge drift is manual | Stale/bloated KNOWLEDGE.md files degrade review quality | Drift metrics feed dashboard; auto-alert on degradation |
| No plugin extensibility | Every new integration requires core changes | Provider interface lets users plug in Prometheus, Datadog, OTLP, file, etc. |

---

## 2. Stakeholder Analysis

| Stakeholder | Role | Needs | Priority |
|-------------|------|-------|----------|
| **WFC Operators** | Run WFC in CI/CD or locally | Real-time visibility into review health, hook activity, agent status | High |
| **WFC Developers** | Extend/maintain the WFC codebase | Clean plugin interfaces, comprehensive tests, no regressions | High |
| **Reviewer Knowledge Authors** | Maintain KNOWLEDGE.md files | Drift alerts, staleness/bloat visibility, usage stats | Medium |
| **Security Teams** | Audit hook enforcement | Complete audit trail of block/warn/pass decisions with payloads | High |
| **CI/CD Integrators** | Consume WFC metrics in pipelines | Machine-readable output (JSON, Prometheus exposition format) | Medium |
| **End Users (developers using WFC)** | Get code reviewed | Faster cycle times through bottleneck visibility | Medium |

---

## 3. Scope Definition

### 3.1 In Scope

1. **Metrics Collection Layer** — Counters, gauges, histograms, timers
2. **Structured Event Emitter** — Hook decisions, review lifecycle, agent lifecycle
3. **Provider Plugin Interface** — Abstract base + concrete providers
4. **Built-in Providers** — File (JSON-lines), Console (pretty-print), In-Memory (testing)
5. **Terminal Dashboard** — Rich/Textual-based live TUI (optional dependency)
6. **HTML Dashboard** — Static HTML report generation (wfc-playground style)
7. **CLI Integration** — `wfc observe`, `wfc metrics`, `wfc dashboard` commands
8. **Review System Instrumentation** — Orchestrator, engine, fingerprinter, CS algorithm
9. **Hook System Instrumentation** — PreToolUse, PostToolUse, security, rules
10. **Knowledge System Instrumentation** — Drift detector, RAG retriever, knowledge writer
11. **Test Suite** — Unit + integration tests for all new code (TDD)

### 3.2 Out of Scope (Future Work)

- External provider implementations (Prometheus, Datadog, OTLP) — plugin interface ships, concrete external providers are community/future work
- Persistent time-series storage — v1 is session-scoped; persistence is a provider concern
- Distributed tracing / span propagation — future enhancement once provider interface is proven
- Alerting / notification system — dashboards surface data; alerting is a provider concern
- Web server / live HTTP dashboard — v1 is static HTML generation and terminal TUI

### 3.3 Constraints

| Constraint | Rationale |
|------------|-----------|
| Zero core dependencies added | WFC core has zero required deps (`pyproject.toml` dependencies list is empty). Loki Mode must follow this pattern. Rich/Textual are optional extras. |
| Python 3.12+ only | Matches existing `requires-python = ">=3.12"` |
| UV-only toolchain | All operations via `uv run`, `uv pip install` per CLAUDE.md |
| Token-aware | Instrumentation overhead must not inflate token budgets; metrics collection is out-of-band |
| Agent Skills compliant | Any new skill (e.g., `wfc-observe`) must pass `make validate` |
| No breaking changes | Existing review/hook/knowledge APIs must remain backward-compatible |
| Exit-0 safety | Like hooks, telemetry failures must NEVER block the user's workflow |

---

## 4. Functional Requirements

### FR-1: Metrics Collection Layer

**Description:** A lightweight metrics library that instruments WFC internals without external dependencies.

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-1.1 | Support **Counter** metric type (monotonically increasing) | `counter.increment(value=1, labels={})` works; value never decreases |
| FR-1.2 | Support **Gauge** metric type (arbitrary value) | `gauge.set(value)`, `gauge.increment()`, `gauge.decrement()` all work |
| FR-1.3 | Support **Histogram** metric type (distribution of values) | `histogram.observe(value)` records; `.percentile(p)` returns correct value |
| FR-1.4 | Support **Timer** metric type (duration measurement) | Context manager `with timer.time():` records elapsed seconds as histogram |
| FR-1.5 | All metrics support **labels** (key-value dimensions) | `counter.increment(labels={"reviewer": "security"})` isolates per-label series |
| FR-1.6 | Thread-safe metric operations | Concurrent increments from parallel review agents don't lose data |
| FR-1.7 | **MetricsRegistry** singleton collects all registered metrics | `registry.get_all()` returns every metric; `registry.snapshot()` returns serializable dict |
| FR-1.8 | Registry supports **reset** for testing | `registry.reset()` clears all metrics to initial state |
| FR-1.9 | Metrics are **lazy-initialized** — no overhead if not used | Importing the metrics module alone does not create timers or counters |

**Source Grounding:**

- `reviewer_engine.py:103` already computes `token_count = len(prompt) // 4` — this becomes a metric
- `orchestrator.py:140-142` — dedup + CS calculation are prime candidates for timing
- `pretooluse_hook.py:39` — `_bypass_count` is already an ad-hoc counter; replace with proper metric

### FR-2: Structured Event Emitter

**Description:** A publish-subscribe event bus that emits structured events for every significant WFC action.

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-2.1 | Define **event schema** with: timestamp, event_type, source, payload, session_id | Every emitted event validates against this schema |
| FR-2.2 | **Review lifecycle events**: `review.started`, `review.reviewer.started`, `review.reviewer.completed`, `review.dedup.completed`, `review.scored`, `review.completed` | Orchestrator emits all 6 event types at correct lifecycle points |
| FR-2.3 | **Hook lifecycle events**: `hook.invoked`, `hook.decision` (block/warn/pass), `hook.error`, `hook.bypass` | PreToolUse hook emits all 4 event types |
| FR-2.4 | **Knowledge lifecycle events**: `knowledge.drift.detected`, `knowledge.entry.appended`, `knowledge.retrieval.completed` | Drift detector, knowledge writer, and retriever emit events |
| FR-2.5 | **Agent lifecycle events**: `agent.started`, `agent.phase.changed`, `agent.completed`, `agent.failed` | Implementation agent emits lifecycle events |
| FR-2.6 | Event bus supports **multiple subscribers** | `bus.subscribe("review.*", handler)` — wildcard and exact match |
| FR-2.7 | Event bus supports **async and sync subscribers** | Both `def handler(event)` and `async def handler(event)` work |
| FR-2.8 | Event emission is **fire-and-forget** — subscriber errors don't propagate | A failing subscriber logs warning but doesn't crash the emitter |
| FR-2.9 | Event bus supports **filtering** by event type pattern | `bus.subscribe("hook.decision", handler, filter={"decision": "block"})` |

**Source Grounding:**

- `orchestrator.py:102-108` (prepare_review) — emit `review.started`
- `orchestrator.py:110-152` (finalize_review) — emit `review.scored`, `review.completed`
- `pretooluse_hook.py:72-94` — emit `hook.decision` with block/warn/pass
- `drift_detector.py:64-88` (analyze) — emit `knowledge.drift.detected` per signal

### FR-3: Provider Plugin Interface

**Description:** An abstract interface that decouples metric/event collection from output/storage.

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-3.1 | Define **`ObservabilityProvider`** abstract base class | ABC with `on_event(event)`, `on_metric_snapshot(snapshot)`, `flush()`, `close()` |
| FR-3.2 | Provider **registration** via `ProviderRegistry` | `registry.register(provider)`, `registry.unregister(provider)` |
| FR-3.3 | Multiple providers can be active simultaneously | File + Console providers both receive all events and metrics |
| FR-3.4 | Providers receive **batched snapshots** on configurable interval | `flush_interval_seconds` config (default: 30s) triggers periodic snapshot push |
| FR-3.5 | Provider errors are **isolated** — one failing provider doesn't affect others | Provider A throwing doesn't prevent Provider B from receiving data |
| FR-3.6 | Providers are **configurable** via `wfc.observability` section in `pyproject.toml` or env vars | `WFC_OBSERVABILITY_PROVIDERS=file,console` or `[tool.wfc.observability]` in pyproject.toml |
| FR-3.7 | Provider interface is **versioned** (v1) | Interface includes `PROVIDER_API_VERSION = 1`; future changes bump version |

### FR-4: Built-in Providers

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-4.1 | **FileProvider**: Writes JSON-lines to configurable path | Each event/snapshot is one JSON line; path defaults to `.development/observability/events.jsonl` |
| FR-4.2 | **ConsoleProvider**: Pretty-prints events to stderr | Uses ANSI colors; respects `NO_COLOR` env var; severity-based coloring |
| FR-4.3 | **InMemoryProvider**: Stores events in a list for testing | `provider.events` is a list; `provider.clear()` resets; `provider.find(type=...)` queries |
| FR-4.4 | **NullProvider**: No-op provider (default when nothing configured) | All methods are no-ops; zero overhead |
| FR-4.5 | FileProvider supports **log rotation** by session | New file per WFC session; filename includes ISO timestamp |
| FR-4.6 | ConsoleProvider supports **verbosity levels** | `verbosity=0` (errors only), `1` (decisions), `2` (all events) |

### FR-5: Dashboard — Terminal (TUI)

**Description:** A live terminal dashboard using Rich/Textual (optional dependency).

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-5.1 | **Review panel**: Current review status, per-reviewer scores, CS, pass/fail | Updates live as review progresses |
| FR-5.2 | **Hook panel**: Recent hook decisions with block/warn/pass counts | Last N decisions shown; running totals |
| FR-5.3 | **Metrics panel**: Key counters (reviews run, findings total, bypasses, errors) | All FR-1 metrics renderable |
| FR-5.4 | **Knowledge panel**: Drift status per reviewer (healthy/needs_pruning/needs_review) | Mirrors `DriftReport.recommendation` per reviewer |
| FR-5.5 | **Graceful degradation**: If Rich/Textual not installed, fall back to plain text summary | `ImportError` caught; plain-text fallback renders same data |
| FR-5.6 | Dashboard launched via `wfc dashboard` CLI command | `wfc dashboard` opens TUI; `--format=text` forces plain text |

### FR-6: Dashboard — HTML Report

**Description:** A static HTML report generated from collected metrics and events.

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-6.1 | Generate self-contained HTML file (no external CDN dependencies) | Single `.html` file opens in any browser; CSS/JS inlined |
| FR-6.2 | **Review summary section**: CS scores over time, per-reviewer radar chart | Chart.js or similar inlined; shows last N reviews |
| FR-6.3 | **Hook activity section**: Block/warn/pass pie chart, timeline of decisions | Filterable by time range |
| FR-6.4 | **Knowledge health section**: Per-reviewer drift status, entry counts, staleness | Color-coded health indicators |
| FR-6.5 | **Metrics table**: All registered metrics with current values | Sortable table with labels expanded |
| FR-6.6 | Generated via `wfc report` CLI command | `wfc report --output report.html` creates the file |
| FR-6.7 | Uses WFC playground template pattern | Follows `wfc/assets/templates/playground/` conventions |

### FR-7: CLI Integration

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-7.1 | `wfc metrics` — Dump current metrics snapshot as JSON to stdout | Machine-readable; pipe-friendly |
| FR-7.2 | `wfc metrics --format=table` — Pretty-print metrics as a table | Human-readable table output |
| FR-7.3 | `wfc dashboard` — Launch terminal TUI dashboard | Opens Rich/Textual dashboard (or plain text fallback) |
| FR-7.4 | `wfc report` — Generate HTML dashboard report | Writes HTML file to specified path |
| FR-7.5 | `wfc observe` — Tail live events to terminal | Streams events as they occur; `--filter=hook.*` supports filtering |
| FR-7.6 | All CLI commands respect `--quiet` and `--verbose` flags | `--quiet` suppresses non-essential output; `--verbose` shows debug info |

### FR-8: Instrumentation Points

**Description:** Specific integration points where existing WFC code is instrumented.

| ID | Component | File | Instrumentation |
|----|-----------|------|-----------------|
| FR-8.1 | ReviewOrchestrator.prepare_review | `orchestrator.py:102` | Emit `review.started`, start timer |
| FR-8.2 | ReviewOrchestrator.finalize_review | `orchestrator.py:110` | Emit `review.scored` with CS result, stop timer, record histogram |
| FR-8.3 | ReviewerEngine.prepare_review_tasks | `reviewer_engine.py:70` | Counter: tasks prepared; Gauge: total tokens |
| FR-8.4 | ReviewerEngine.parse_results | `reviewer_engine.py:126` | Counter: findings parsed; per-reviewer score gauge |
| FR-8.5 | Fingerprinter.deduplicate | `fingerprint.py` | Counter: pre-dedup vs post-dedup findings; dedup ratio gauge |
| FR-8.6 | ConsensusScore.calculate | `consensus_score.py` | Histogram: CS values; Counter: MPR activations |
| FR-8.7 | PreToolUse hook main | `pretooluse_hook.py:33` | Emit `hook.invoked`, `hook.decision`; replace `_bypass_count` with counter |
| FR-8.8 | SecurityHook.check | `security_hook.py` | Counter: pattern matches by pattern name; Emit `hook.decision` with pattern details |
| FR-8.9 | RuleEngine.evaluate | `rule_engine.py` | Counter: rule evaluations; Counter: blocks/warns by rule |
| FR-8.10 | DriftDetector.analyze | `drift_detector.py:64` | Emit `knowledge.drift.detected`; Gauge: total entries, stale count, bloated count |
| FR-8.11 | KnowledgeWriter (auto-append) | `knowledge_writer.py` | Emit `knowledge.entry.appended`; Counter: entries written |
| FR-8.12 | KnowledgeRetriever.retrieve | `retriever.py` | Timer: retrieval latency; Counter: cache hits vs misses |
| FR-8.13 | EmergencyBypass | `emergency_bypass.py` | Emit `review.bypass.activated`; Counter: active bypasses |

---

## 5. Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Metric increment latency | < 1 microsecond (in-process counter update) |
| NFR-1.2 | Event emission latency | < 100 microseconds (fire-and-forget to subscribers) |
| NFR-1.3 | Memory overhead per metric | < 1 KB per metric series (counter + labels) |
| NFR-1.4 | Provider flush latency | < 50ms for FileProvider with 1000 events |
| NFR-1.5 | Dashboard render latency | < 500ms for terminal TUI refresh |
| NFR-1.6 | HTML report generation | < 2 seconds for 10,000 events |

### NFR-2: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Observability system crash must NEVER block WFC operations | All public APIs wrapped in try/except with silent degradation |
| NFR-2.2 | Provider failure isolation | Provider A failure doesn't affect Provider B |
| NFR-2.3 | Graceful degradation without optional deps | Core metrics/events work with zero deps; TUI requires Rich |
| NFR-2.4 | Thread safety | All metric operations safe under concurrent access |

### NFR-3: Testability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | Unit test coverage for new code | >= 90% line coverage |
| NFR-3.2 | InMemoryProvider enables deterministic testing | All event assertions use InMemoryProvider |
| NFR-3.3 | Registry.reset() enables test isolation | Each test starts with clean state |
| NFR-3.4 | TDD workflow | All features developed RED-GREEN-REFACTOR |

### NFR-4: Extensibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | Adding a new provider requires implementing 4 methods | `on_event`, `on_metric_snapshot`, `flush`, `close` |
| NFR-4.2 | Adding a new metric type requires subclassing `Metric` | One base class; one method to override |
| NFR-4.3 | Adding a new event type requires adding a string constant | No schema changes needed for new event types |

### NFR-5: Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-5.1 | Python 3.12+ | Matches existing project target |
| NFR-5.2 | No new required dependencies | Optional extras only |
| NFR-5.3 | Backward-compatible with all existing WFC APIs | Zero breaking changes to review/hook/knowledge interfaces |
| NFR-5.4 | Agent Skills compliant for any new skills | Passes `make validate` |

---

## 6. Data Requirements

### 6.1 Event Schema

```python
@dataclass
class ObservabilityEvent:
    timestamp: str          # ISO 8601 (e.g., "2026-02-17T14:30:00.123Z")
    event_type: str         # Dotted namespace (e.g., "review.scored")
    source: str             # Component name (e.g., "orchestrator")
    session_id: str         # Unique per WFC invocation
    payload: dict           # Event-specific data (varies by event_type)
    level: str              # "debug", "info", "warning", "error"
```

### 6.2 Metric Snapshot Schema

```python
@dataclass
class MetricSnapshot:
    timestamp: str          # ISO 8601
    session_id: str
    metrics: list[dict]     # Each: {"name": str, "type": str, "value": ..., "labels": dict}
```

### 6.3 Review Event Payloads

| Event Type | Payload Fields |
|------------|----------------|
| `review.started` | `task_id`, `file_count`, `reviewer_count` |
| `review.reviewer.completed` | `task_id`, `reviewer_id`, `score`, `finding_count`, `token_count` |
| `review.scored` | `task_id`, `cs`, `tier`, `passed`, `finding_count`, `mpr_applied` |
| `review.completed` | `task_id`, `duration_seconds`, `report_path` |

### 6.4 Hook Event Payloads

| Event Type | Payload Fields |
|------------|----------------|
| `hook.invoked` | `hook_type`, `tool_name`, `tool_input_keys` |
| `hook.decision` | `hook_type`, `decision` (block/warn/pass), `reason`, `pattern_name` |
| `hook.error` | `hook_type`, `error_type`, `error_message` |
| `hook.bypass` | `hook_type`, `bypass_count`, `error_type` |

### 6.5 Knowledge Event Payloads

| Event Type | Payload Fields |
|------------|----------------|
| `knowledge.drift.detected` | `reviewer_id`, `signal_type`, `severity`, `description` |
| `knowledge.entry.appended` | `reviewer_id`, `section`, `entry_preview` |
| `knowledge.retrieval.completed` | `reviewer_id`, `query_length`, `results_count`, `latency_ms` |

---

## 7. Architecture & Integration Design

### 7.1 Package Structure

```
wfc/
├── observability/                    # NEW — Loki Mode core package
│   ├── __init__.py                   # Public API: get_registry(), get_bus(), get_provider_registry()
│   ├── metrics.py                    # Counter, Gauge, Histogram, Timer, MetricsRegistry
│   ├── events.py                     # ObservabilityEvent, EventBus, subscribe/emit
│   ├── providers/
│   │   ├── __init__.py               # ObservabilityProvider ABC, ProviderRegistry
│   │   ├── file_provider.py          # JSON-lines file output
│   │   ├── console_provider.py       # Pretty-print to stderr
│   │   ├── memory_provider.py        # In-memory for testing
│   │   └── null_provider.py          # No-op default
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── terminal.py               # Rich/Textual TUI dashboard
│   │   ├── html_report.py            # Static HTML report generator
│   │   └── templates/
│   │       └── report.html           # Jinja2-free HTML template with Chart.js
│   └── config.py                     # Configuration loading (pyproject.toml / env vars)
│
├── scripts/
│   ├── skills/
│   │   └── observe/                  # NEW — Observe skill scripts
│   │       └── cli.py                # CLI: wfc metrics, wfc dashboard, wfc report, wfc observe
│   └── hooks/
│       └── pretooluse_hook.py        # MODIFIED — add event emission + metrics
│
├── reviewers/                        # UNCHANGED — but instrumented at orchestrator level
└── ...
```

### 7.2 Integration Strategy (Non-Invasive)

The instrumentation follows a **decorator/wrapper pattern** — existing functions are NOT modified internally. Instead:

1. **Orchestrator instrumentation**: The `ReviewOrchestrator` methods emit events and record metrics at the boundary (before/after calls to engine/fingerprinter/scorer). No changes to engine internals.

2. **Hook instrumentation**: The `pretooluse_hook.py:_run()` function gets event emission added at the 3 decision points (block/warn/pass). The existing `_bypass_count` global is replaced with a proper Counter metric.

3. **Knowledge instrumentation**: `DriftDetector.analyze()` emits events after computing signals. Zero changes to detection logic.

This means: **all existing unit tests continue to pass unchanged**.

### 7.3 Initialization Flow

```
WFC CLI entry (wfc/cli.py)
  → Load observability config (env vars / pyproject.toml)
  → Initialize MetricsRegistry (singleton)
  → Initialize EventBus (singleton)
  → Register configured providers (FileProvider, ConsoleProvider, etc.)
  → Existing WFC flow proceeds (review, hooks, etc.)
  → Instrumented code emits events / records metrics automatically
  → On exit: flush all providers, close all providers
```

### 7.4 Dependency Graph

```
wfc.observability.metrics     → (no deps — pure Python dataclasses + threading.Lock)
wfc.observability.events      → (no deps — pure Python)
wfc.observability.providers   → (no deps for core; Rich optional for console)
wfc.observability.dashboard   → Rich/Textual (optional), Chart.js (inlined in HTML)
wfc.observability.config      → tomllib (stdlib in 3.12+)
```

---

## 8. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Instrumentation introduces bugs in review/hook paths | Low | High | Non-invasive wrapper pattern; all existing tests must still pass; instrumentation wrapped in try/except |
| Performance overhead from metrics collection | Low | Medium | Benchmarked at < 1μs per counter increment; lazy initialization; NullProvider default |
| Optional dependency (Rich) causes install failures | Low | Low | Graceful `ImportError` fallback; Rich is optional extra, not required |
| Scope creep into external providers (Prometheus, etc.) | Medium | Medium | Strict scope boundary: v1 ships interface + 4 built-in providers only |
| Thread safety issues with concurrent agents | Medium | High | Use `threading.Lock` for all metric operations; fuzz testing in CI |
| Event bus memory leak from unbounded subscriber lists | Low | Medium | Weak references for subscribers; explicit `unsubscribe()` API |
| HTML report grows too large with many events | Low | Low | Configurable max events in report; pagination in HTML |

---

## 9. Acceptance Criteria (Release Gate)

The following must ALL be true before Loki Mode is merged:

| # | Criteria | Verification |
|---|----------|-------------- |
| 1 | All existing WFC tests pass (`make test`) | CI green |
| 2 | New test coverage >= 90% for `wfc/observability/` | `make test-coverage` |
| 3 | `make validate` passes (Agent Skills compliance) | CI green |
| 4 | `make lint` and `make format` pass | CI green |
| 5 | Zero new required dependencies in `pyproject.toml` | Manual review |
| 6 | `wfc metrics` CLI command works end-to-end | Integration test |
| 7 | `wfc dashboard` launches TUI (or plain text fallback) | Integration test |
| 8 | `wfc report --output /tmp/test.html` generates valid HTML | Integration test |
| 9 | FileProvider writes valid JSON-lines | Unit test |
| 10 | InMemoryProvider captures all emitted events | Unit test |
| 11 | Orchestrator emits all 6 review lifecycle events | Integration test |
| 12 | PreToolUse hook emits decision events | Integration test |
| 13 | DriftDetector emits drift events | Unit test |
| 14 | Thread safety: concurrent counter increments don't lose data | Stress test |
| 15 | Performance: metric increment < 10μs (conservative) | Benchmark test |
| 16 | `wfc observe --filter=hook.*` streams filtered events | Integration test |
| 17 | HTML report renders correctly in Chrome/Firefox | Manual QA |
| 18 | No breaking changes to existing public APIs | Backward-compat test |

---

## 10. Phased Delivery Plan (Recommended)

### Phase 1: Foundation (Core Metrics + Events + Providers)

- `wfc/observability/metrics.py` — Counter, Gauge, Histogram, Timer, Registry
- `wfc/observability/events.py` — EventBus, ObservabilityEvent, subscribe/emit
- `wfc/observability/providers/` — ABC, NullProvider, InMemoryProvider, FileProvider, ConsoleProvider
- `wfc/observability/config.py` — Configuration loading
- Full test suite for all above
- **Deliverable:** Metrics and events work internally; FileProvider writes JSON-lines

### Phase 2: Instrumentation (Wire Into Existing Systems)

- Instrument `ReviewOrchestrator` (6 review lifecycle events + timing metrics)
- Instrument `pretooluse_hook.py` (4 hook events + replace `_bypass_count`)
- Instrument `DriftDetector` (3 knowledge events + drift gauges)
- Instrument `ReviewerEngine` (token counting metrics)
- Instrument `Fingerprinter` + `ConsensusScore` (dedup ratio, CS histogram, MPR counter)
- **Deliverable:** All 13 instrumentation points (FR-8) active

### Phase 3: CLI + Dashboard

- `wfc metrics` / `wfc metrics --format=table` CLI commands
- `wfc observe` live event tailing with filter support
- `wfc dashboard` terminal TUI (Rich/Textual) with graceful fallback
- `wfc report` HTML report generation
- CLI integration tests
- **Deliverable:** Full operator experience; `wfc dashboard` and `wfc report` functional

### Phase 4: Polish + Documentation

- Performance benchmarking and optimization
- Provider documentation (how to write a custom provider)
- Update CLAUDE.md with observability commands
- Update `make doctor` to check observability health
- Edge case hardening (empty reviews, concurrent sessions, etc.)
- **Deliverable:** Production-ready; documented; benchmarked

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **CS** | Consensus Score — mathematical aggregation of reviewer findings |
| **MPR** | Minority Protection Rule — elevates CS when a security/reliability reviewer finds critical issues |
| **Provider** | A plugin that receives metrics/events and outputs them (file, console, Prometheus, etc.) |
| **Event Bus** | Publish-subscribe system for structured observability events |
| **TUI** | Terminal User Interface — Rich/Textual based dashboard |
| **JSON-lines** | One JSON object per line file format (`.jsonl`) |
| **Drift** | Knowledge file degradation: staleness, bloat, contradictions, orphans |
| **Loki Mode** | Codename for this Dashboard & Observability Plugin System feature |

---

## 12. Open Questions (For WFC Plan Review)

1. **Session ID generation**: UUID4 per CLI invocation, or should it chain across `wfc plan` → `wfc implement` → `wfc review` as one logical session?
2. **Config location**: `pyproject.toml [tool.wfc.observability]` vs standalone `.wfc/observability.toml`?
3. **Event retention in FileProvider**: Rotate per session, per day, or by size?
4. **HTML report charting**: Inline Chart.js (~200KB) or use a lighter SVG-based approach?
5. **TUI framework**: Rich Tables (simpler, less deps) vs Textual App (richer, more deps)?

---

*This document is the input for `/wfc-plan`. All requirements are grounded in existing source code references and designed to integrate non-invasively with the current WFC architecture.*
