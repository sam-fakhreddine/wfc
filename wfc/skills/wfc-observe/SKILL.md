---
name: wfc-observe
description: >-
  Generates observability artifacts — metric definitions, alert rule skeletons,
  dashboard panel specs — by mapping formal property specs to signals. REQUIRES:
  a PROPERTIES.md with at least one SAFETY, LIVENESS, INVARIANT, or PERFORMANCE
  property with numeric bounds; target platform (Prometheus/Alertmanager,
  OpenTelemetry, Datadog, or CloudWatch); target language/metrics library.
  Trigger: /wfc-observe; explicit reference to a PROPERTIES.md with request to
  derive monitoring artifacts; production readiness requiring property-to-signal
  mapping. Not for: instrumentation without PROPERTIES.md, freeform dashboard
  setup, incident triage, IaC for monitoring infra, or auditing existing configs.
license: MIT
---

# WFC:OBSERVE - Observability from Properties

Generates observability infrastructure from formal properties.

## What It Does

1. **Property → Observable Mapper** - Maps SAFETY/LIVENESS/PERFORMANCE properties to metrics
2. **Metrics Collector Generator** - Creates code to collect metrics
3. **Alert Rule Generator** - Alert rules for property violations
4. **Dashboard Panel Generator** - Visualization for properties

## Usage

```bash
# Generate observability from PROPERTIES.md
/wfc-observe

# Generate for specific properties
/wfc-observe --properties PROP-001,PROP-002
```

## Mapping Rules

- **SAFETY** → Error counts, assertion failures, security violations
- **LIVENESS** → Health checks, response times, timeout counts
- **INVARIANT** → Data integrity checks, state validation
- **PERFORMANCE** → Latency percentiles, throughput, resource utilization

## Outputs

- OBSERVABILITY.md
- metrics/ (collector code)
- alerts/ (alert rule definitions)
- dashboards/ (dashboard JSON)

## Philosophy

**ELEGANT**: Observability follows naturally from properties
**MULTI-TIER**: Observe each tier
**PARALLEL**: Deploy all observability concurrently
