---
name: wfc-retro
description: >-
  Analyzes completed WFC (Workflow Controller) JSONL telemetry files to
  calculate aggregated performance metrics (e.g., throughput, completion rates)
  for a specific past period. Generates a standardized retrospective report
  focusing on quantitative observation.

  TRIGGERS: "/wfc-retro", "generate WFC retrospective", "calculate WFC
  completion metrics for completed sprint", "aggregate WFC statistics for past
  month", "report on Say:Do ratio for last week".

  REQUIRES: user references WFC/agent workflows AND specifies a completed past
  period (end date < current date) AND wfc-*.W[0-9][0-9].jsonl files exist for
  that period.

  NOT FOR: real-time monitoring, debugging a single failing task, root cause
  analysis for specific errors, sprint planning (future), requests for the
  current active sprint, raw log views, analyzing data without existing JSONL
  files, analyzing time ranges exceeding 30 days, or calculating custom KPIs
  outside the standard schema.
license: MIT
---

# WFC:RETRO — Workflow Controller Retrospective Analysis

Reads WFC (Workflow Controller) JSONL telemetry, aggregates metrics for a
completed period, and produces a structured report.

## Execution Logic

1. **Scope Validation**:
    * Verify `current_date > requested_end_date`. If false, refuse execution
        (Skill is for completed periods only).
    * Verify file size/period length < 30 days to prevent context overflow.

2. **File Resolution**:
    * Scan for files matching pattern `wfc-*.W[0-9][0-9].jsonl`.
    * Deduplicate records by `transaction_id` if overlapping files are found.

3. **Data Ingestion & Cleaning**:
    * Read JSONL lines. Skip malformed lines (logging count of skipped lines).
    * Abort if valid record count is 0 (Report: "Insufficient Data").

4. **Metric Calculation**:
    * **Say:Do Ratio**: $\frac{\text{Tasks Completed}}{\text{Tasks Started}}$
        (Note: 'Say' is defined as Intent Logged; 'Do' defined as Success Exit
        Code).
    * **Success Rate**: $\frac{\text{Exit Code 0}}{\text{Total Tasks}}$.

5. **Output Generation**:
    * Do NOT generate improvement recommendations (hallucination risk).
    * Generate report with the following strict schema:
        * **Header**: Period Analyzed, Source Files Used.
        * **Data Integrity**: Total Lines, Valid Lines, Skipped Errors.
        * **Metrics**: Say:Do Ratio, Success Rate, Total Throughput.
        * **Observations**: Bullet points of factual trends (e.g., "High
            failure rate observed on Tuesdays").

### Skill Attribution Priority

When attributing session friction to specific skills, use this priority order:

1. `skill_invocations[].skill` field in session-meta (if present) — most accurate
2. `/wfc-[\w-]+` regex match on `first_prompt` — available for ~21% of sessions
3. `tool_counts.Skill > 0` with no match — record as "unattributed skill session"

Never discard unattributed sessions. Count them separately as they represent real friction
that cannot yet be tied to a specific skill.
