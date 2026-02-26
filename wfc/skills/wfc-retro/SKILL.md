---
name: wfc-retro
description: >-
  Reads WFC JSONL telemetry for a completed period and produces a structured
  retrospective report with metrics and improvement recommendations.

  TRIGGERS: "/wfc-retro", "run a WFC retrospective", "summarize agent task
  performance for last sprint", "analyze WFC telemetry from the past N days",
  "show me the Say:Do ratio for last sprint".

  REQUIRES: user references WFC/agent workflows AND targets a completed past
  period AND wfc-*.WNN.jsonl files exist for that period.

  NOT FOR: real-time monitoring, debugging a single failing task, requests
  without WFC telemetry context, product feature analysis, future planning,
  sprint planning, raw log views, or when no JSONL files exist for the period.
license: MIT
---

# WFC:RETRO — Workflow Controller Retrospective Analysis

Reads WFC (Workflow Controller) JSONL telemetry, aggregates metrics for a
completed period, and produces a structured improvement
