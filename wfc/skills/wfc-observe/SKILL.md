---
name: wfc-observe
description: >-
  Translates formal system properties (SAFETY, LIVENESS, INVARIANTS, PERFORMANCE)
  from a PROPERTIES.md file into observability definition snippets (metric
  definitions, alert rule conditions, dashboard panel fragments).

  REQUIRES: A specification file (default: PROPERTIES.md) containing properties
  with quantifiable numeric bounds.

  USE FOR: Generating metric definition snippets, alert condition logic (PromQL),
  and dashboard panel JSON fragments based on formal specs.

  NOT FOR: Writing application instrumentation logic (inserting metrics into .py/.go files);
  generating high-cardinality metrics (user IDs, emails);
  properties enforced at compile-time (static analysis);
  setting up monitoring infrastructure (Terraform/Helm);
  incident triage.

license: MIT
---

# WFC:OBSERVE - Observability from Properties

Generates observability definitions from formal properties.

## Prerequisites

1. **Properties File**: A `PROPERTIES.md` file must exist.
2. **Quantifiable Bounds**: Properties must include numeric thresholds (e.g., `latency < 500ms`). Qualitative properties will be skipped or logged as unmappable.
3. **Runtime Observable**: Properties must be verify-able at runtime. Compile-time or formally verified properties (e.g., "No data races in Rust") are excluded.
4. **Cardinality Check**: Properties must not require high-cardinality labels (User IDs, Request IDs) for metrics. Use tracing for these dimensions.

## What It Does

1. **Property → Signal Mapper**: Reads properties and maps them to standard signal types (Counter, Gauge, Histogram).
2. **Metric Definition Generator**: Outputs initialization/registration code snippets for the target library.
3. **Alert Condition Generator**: Outputs alert rule *conditions* (e.g., PromQL expressions) without routing/receiver configuration.
4. **Dashboard Fragment Generator**: Outputs individual panel JSON objects compatible with the target platform.

## Usage

```bash
# Generate observability definitions for all valid properties
/wfc-observe --platform [prometheus|datadog|cloudwatch] --library [library_name]

# Generate for specific properties
/wfc-observe --properties PROP-001,PROP-002
```

## Mapping Rules

- **SAFETY** → Error counters, assertion failure gauges.
- **LIVENESS** → Health check gauges, timeout counters.
- **INVARIANT** → Logic validation counters (e.g., `state_mismatch_total`).
- **PERFORMANCE** → Latency histograms, throughput gauges.

## Outputs

All outputs are generated in a `./observability/` directory relative to the input file to prevent root clutter.

- `observability/metrics/`: Code snippets for metric registration (not fully wired application code).
- `observability/alerts/`: Rule files containing *conditions only*.
- `observability/dashboards/`: Panel JSON fragments (not fully importable dashboard definitions).

## Philosophy

**DEFINITIONAL**: Generates schemas and definitions, not infrastructure or instrumentation logic.
**PARALLEL**: Processes all valid properties in a single pass.
**EXPLICIT**: Fails explicitly on qualitative-only or high-cardinality properties.
