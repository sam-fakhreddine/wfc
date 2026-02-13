---
name: wfc-observe
description: Observability instrumentation generator that derives monitoring from formal properties. Maps PROPERTIES.md (SAFETY, LIVENESS, PERFORMANCE) to concrete observables, generates metrics collectors, alert rules, and dashboard panel configurations. Use when implementing observability for new features or improving monitoring coverage. Triggers on "add observability", "generate monitoring", "create alerts from properties", or explicit /wfc-observe. Ideal for SRE work, production readiness, and proactive monitoring. Not for log analysis or incident investigation.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--properties path]
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
