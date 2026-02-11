---
name: wfc:retro
description: AI-powered retrospective analysis that examines WFC telemetry data to identify patterns, trends, and bottlenecks. Analyzes agent performance, review quality, task completion times, and common failure modes. Generates actionable recommendations for workflow improvement. Use after completing sprints, major features, or periodically for process improvement. Triggers on "run retrospective", "analyze recent work", "what can we improve", or explicit /wfc:retro. Ideal for team retrospectives and continuous improvement. Not for debugging specific issues or real-time monitoring.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--period 7d or --all]
---

# WFC:RETRO - AI-Powered Retrospectives

Analyzes WFC telemetry to identify improvements and optimize workflows.

## What It Does

1. **Telemetry Aggregator** - Reads wfc-*.WNN.jsonl files
2. **Trend Analyzer** - Identifies patterns over time
3. **Bottleneck Detector** - Finds slow/failing tasks
4. **Recommendation Generator** - Actionable improvements

## Usage

```bash
# Analyze last 7 days
/wfc:retro

# Analyze last 30 days
/wfc:retro --period 30d

# Analyze all time
/wfc:retro --all

# Analyze specific skill
/wfc:retro --skill implement
```

## Analysis Dimensions

- **Performance** - Slow tasks, timeouts, retries
- **Quality** - Review failures, test failures, rollbacks
- **Efficiency** - Agent utilization, parallel vs sequential
- **Patterns** - Common failure modes, success patterns

## Outputs

- RETRO-REPORT.md
- Trend charts (Mermaid)
- Top bottlenecks
- Prioritized recommendations

## Philosophy

**ELEGANT**: Learn from data, continuously improve
**MULTI-TIER**: Analyze all tiers
**PARALLEL**: Aggregate multiple telemetry files concurrently
