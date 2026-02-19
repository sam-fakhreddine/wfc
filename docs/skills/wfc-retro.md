# wfc-retro

## What It Does

`wfc-retro` performs an AI-powered retrospective by reading WFC telemetry files (`wfc-*.WNN.jsonl`) and aggregating data across configurable time windows. It identifies performance bottlenecks, quality trends, common failure modes, and TEAMCHARTER values alignment — then produces a prioritized recommendations report with a Say:Do ratio and Mermaid trend charts.

## When to Use It

- After completing a sprint or major feature to understand what went well and what slowed you down
- Periodically (weekly or monthly) for continuous process improvement
- When review scores are trending down or test failure rates are increasing
- When you want to measure TEAMCHARTER values adherence across a period of work
- After a run of wfc-implement or wfc-lfg sessions to audit agent performance and parallelism efficiency

## Usage

```bash
/wfc-retro
/wfc-retro --period 30d
/wfc-retro --all
/wfc-retro --skill implement
```

## Example

```
User: /wfc-retro --period 7d

Aggregating telemetry from the last 7 days...
  → 12 wfc-implement sessions
  → 47 tasks completed, 3 rolled back
  → 5 wfc-review runs (avg CS: 3.4)

## Performance
  Slowest tasks:
    - TASK-019: 42 min (timeout on external API in tests)
    - TASK-022: 38 min (3 quality gate retries)

## Quality
  Test failures: 4 (all in integration tier)
  Review blocks: 1 (CS 7.8 — maintainability finding)

## Efficiency
  Agent utilization: 74% (parallel) / 26% (sequential fallback)

## TEAMCHARTER Values Alignment
  Say:Do Ratio: 0.75 (6 of 8 tasks on-estimate)

  Values Adherence (Mermaid xychart-beta):
    Innovation: 8 upheld, 1 violated
    Simplicity:  5 upheld, 3 violated  ← recommendation flagged

## Recommendations
  1. [Simplicity] 3 tasks exceeded complexity budget — consider wfc-validate
     before implementing to catch scope creep early.
  2. [Accountability] 2 tasks re-estimated mid-flight — add upfront spike tasks
     for external API dependencies.

Report written to: .development/summaries/RETRO-REPORT.md
```

## Options

```bash
/wfc-retro                  # Analyze last 7 days (default)
/wfc-retro --period 30d     # Analyze last 30 days
/wfc-retro --all            # Analyze all available telemetry
/wfc-retro --skill implement # Scope to a specific WFC skill's telemetry
```

## Integration

**Produces:**

- `.development/summaries/RETRO-REPORT.md` — full retrospective report
- Mermaid trend charts (performance, quality over time)
- Mermaid `xychart-beta` values adherence chart
- Say:Do ratio with per-task breakdown
- Prioritized recommendations tied to specific TEAMCHARTER values

**Consumes:**

- `wfc-*.WNN.jsonl` telemetry files produced by wfc-implement, wfc-review, and other skills
- `ReflexionEntry.team_values_impact` fields via the memory system for values alignment data

**Next step:** Review `.development/summaries/RETRO-REPORT.md`, share recommendations with your team, and feed high-priority findings into `/wfc-compound` to codify the solutions for future agents.
