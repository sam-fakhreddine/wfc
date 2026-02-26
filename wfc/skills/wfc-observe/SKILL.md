---
name: wfc-observe
description: >
  Generates observability artifacts — metric stubs, alert rule skeletons, and
  dashboard panel specs — by mapping formal property specifications to signals.

  REQUIRED: A PROPERTIES.md with at least one SAFETY, LIVENESS, INVARIANT, or
  PERFORMANCE property with explicit numeric bounds where thresholds are needed.
  If absent, skill declines and offers to scaffold a PROPERTIES.md template.
  Also requires target platform (Prometheus/Alertmanager, OpenTelemetry,
  Datadog, or CloudWatch) and target language/metrics library.

  INVOKE when user explicitly provides a PROPERTIES.md AND asks to derive
  monitoring artifacts from it; a production readiness review requires
  property-to-observable mapping; or user runs /wfc-observe with a properties
  file present and platform context specified.

  Not for: generic instrumentation without a formal property source; incident
  investigation; post-incident gap analysis; log analysis; IaC for monitoring
  infrastructure; reviewing existing artifacts.
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
