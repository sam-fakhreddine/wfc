---
name: wfc-retro
description: >
  Performs retrospective analysis of WFC telemetry for a completed time window.
  Reads wfc-*.WNN.jsonl files under .development/wfc/ and produces a
  structured improvement report.

  REQUIRES ALL of: (a) user explicitly references WFC, agent workflows, or
  workflow telemetry; (b) analysis targets a completed past period; (c)
  wfc-*.WNN.jsonl files exist for that period.

  TRIGGERS: "/wfc-retro", "run a WFC retrospective", "summarize agent task
  performance for last sprint", "what bottlenecks in our WFC workflow this
  month", "analyze WFC telemetry from the past [N] days/weeks", "show me the
  Say:Do ratio for last sprint".

  Not for: specific failing tasks or live issues; requests not mentioning WFC
  or workflow telemetry; product features, PRs, or tickets; future planning;
  team ceremonies without WFC telemetry; raw log views or compliance reports;
  periods under one completed day or in-progress tasks. Halts with a warning
  if no JSONL files exist — does not fabricate reports.
license: MIT

---

# WFC:RETRO — Workflow Controller Retrospective Analysis

Reads WFC (Workflow Controller) JSONL telemetry, aggregates metrics for a
completed period, and produces a structured improvement
