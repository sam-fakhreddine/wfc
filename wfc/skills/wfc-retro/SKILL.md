---
name: wfc-retro
description: AI-powered retrospective analysis that examines WFC telemetry data to identify patterns, trends, and bottlenecks. Analyzes agent performance, review quality, task completion times, and common failure modes. Generates actionable recommendations for workflow improvement. Use after completing sprints, major features, or periodically for process improvement. Triggers on "run retrospective", "analyze recent work", "what can we improve", or explicit /wfc-retro. Ideal for team retrospectives and continuous improvement. Not for debugging specific issues or real-time monitoring.
license: MIT
---

# WFC:RETRO - AI-Powered Retrospectives

Analyzes WFC telemetry to identify improvements and optimize workflows.

## What It Does

1. **Telemetry Aggregator** - Reads wfc-*.WNN.jsonl files
2. **Trend Analyzer** - Identifies patterns over time
3. **Bottleneck Detector** - Finds slow/failing tasks
4. **Recommendation Generator** - Actionable improvements
5. **Values Alignment Tracker** - TEAMCHARTER values adherence via Say:Do ratio

## Usage

```bash
# Analyze last 7 days
/wfc-retro

# Analyze last 30 days
/wfc-retro --period 30d

# Analyze all time
/wfc-retro --all

# Analyze specific skill
/wfc-retro --skill implement
```

## Analysis Dimensions

- **Performance** - Slow tasks, timeouts, retries
- **Quality** - Review failures, test failures, rollbacks
- **Efficiency** - Agent utilization, parallel vs sequential
- **Patterns** - Common failure modes, success patterns
- **Values Alignment** - TEAMCHARTER values adherence across sprint

## TEAMCHARTER Values Alignment

Every retro report MUST include a **"## TEAMCHARTER Values Alignment"** section with the following subsections:

### Say:Do Ratio

Compute and display the Say:Do ratio using `wfc.scripts.memory.saydo.compute_say_do_ratio`.
The ratio measures how accurately the team estimates and delivers:

```
Say:Do Ratio = tasks_completed_at_estimated_complexity / tasks_with_valid_complexity
```

A task is "on-estimate" when:
- Estimated complexity matches actual complexity (S stayed S, M stayed M)
- No re-estimation was needed
- No quality gate failures

Display format:
```
**Say:Do Ratio: 0.75** (6 of 8 tasks on-estimate)
```

### Values Adherence Chart

Generate a Mermaid bar chart showing upheld vs violated counts per value using
`wfc.scripts.memory.saydo.generate_values_mermaid_chart`. Data is aggregated from
`ReflexionEntry.team_values_impact` fields via `aggregate_values_alignment`.

### Recommendations

Generate actionable recommendations tied to specific values using
`wfc.scripts.memory.saydo.generate_values_recommendations`. Each recommendation
MUST reference the specific TEAMCHARTER value and SHOULD include concrete examples when supporting telemetry is available (e.g., "Simplicity score
dropped -- 3 tasks exceeded complexity budget").

### Implementation Reference

```python
from wfc.scripts.memory.saydo import (
    compute_say_do_ratio,
    aggregate_values_alignment,
    generate_values_mermaid_chart,
    generate_values_recommendations,
)
```

## Outputs

- .development/summaries/RETRO-REPORT.md
- Trend charts (Mermaid)
- Values adherence chart (Mermaid xychart-beta)
- Say:Do ratio
- Top bottlenecks
- Prioritized recommendations (including values-specific)

## Philosophy

**ELEGANT**: Learn from data, continuously improve
**MULTI-TIER**: Analyze all tiers
**PARALLEL**: Aggregate multiple telemetry files concurrently
