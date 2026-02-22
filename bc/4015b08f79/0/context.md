# Session Context

## User Prompts

### Prompt 1

New branch.
we have a skill fixer skill

lets run it against our skills

### Prompt 2

[Request interrupted by user for tool use]

### Prompt 3

youll need to be in a worktree please so we dont collide

### Prompt 4

exit plan mode, create worktree from MAIN and then do the skill fixer

### Prompt 5

[Request interrupted by user]

### Prompt 6

did we ever do this in a branch? # Agentic Skill Remediation System

A multi-agent pipeline for diagnosing and fixing Claude Skills at scale. Skills have structural, behavioral, and operational dimensions that raw prompts don't — this system accounts for all three.

---

## How Skills Differ from Prompts

Skills are not just prompts. A skill is a directory containing:

```
skill-name/
├── SKILL.md          (required — frontmatter + instructions)
├── scripts/          (executable ...

### Prompt 7

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-implement

# wfc-implement - Multi-Agent Parallel Implementation Engine

**Core skill #3** - Reads TASKS.md, orchestrates N agents in isolated worktrees, enforces TDD, routes through review, auto-merges, handles rollbacks.

## Status

✅ **PRODUCTION READY**

- ✅ Shared infrastructure (config, telemetry, schemas, utils)
- ✅ Orchestrator logic (task queue, dependency management) - 355 lines
- ✅ Agent implementation (TD...

### Prompt 8

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-plan

# WFC:PLAN - Adaptive Planning with Formal Properties

Converts requirements into structured implementation plans through adaptive interviewing.

## What It Does

1. **Adaptive Interview** - Asks intelligent questions that adapt based on answers
2. **Task Generation** - Breaks down requirements into structured TASKS.md with dependencies
3. **Property Extraction** - Identifies formal properties (SAFETY, LIVENESS, INVARI...

### Prompt 9

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-build

# WFC:BUILD - Intentional Vibe Coding

**"Vibe coding with guardrails"** - Quick iteration with WFC quality standards.

## What It Does

Simplified workflow that skips formal planning but maintains all WFC quality infrastructure:

1. **Adaptive Interview** - Quick clarifying questions (not full wfc-plan)
2. **Complexity Assessment** - Orchestrator decides: 1 agent or multi-agent?
3. **Subagent Delegation** - Spawn sub...

### Prompt 10

1) all 6
2) youll have to determine this
3) integration

### Prompt 11

lets do it

### Prompt 12

lets target 5 and see what happens

### Prompt 13

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-skill-fixer

# Skill Fixer

6-agent pipeline for diagnosing and fixing Claude Skills at scale.

## Quick Reference

```bash
# Fix single skill
/wfc-skill-fixer ~/.claude/skills/wfc-build

# With functional QA (slow)
/wfc-skill-fixer --functional-qa ~/.claude/skills/wfc-build
```

## Core Workflow

1. **Cataloger** - Local filesystem inventory (no LLM)
2. **Analyst** - Diagnose against skill rubric (LLM or fallback)
3. **Fixe...

### Prompt 14

run against all

### Prompt 15

can you do the grade B but those should exist, so they might be misplaced

### Prompt 16

no see its the issue of being in th REPO we are developing for WFC so it should always check ~ , it needs to be installed there

### Prompt 17

rerun

### Prompt 18

2

### Prompt 19

run our prompt fixer on our prompts

### Prompt 20

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-prompt-fixer

# wfc-prompt-fixer

Fix Claude prompts using evidence-based diagnostics and structured rewrites.

## What It Does

Analyzes Claude prompts against a rubric of known failure modes and produces fixed versions that:

- Preserve original intent
- Resolve antipatterns (decorative roles, vague specs, contradictory instructions, etc.)
- Optimize for Claude 4.x literal instruction following
- Maintain token efficiency
...

### Prompt 21

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

Analysis:
Let me chronologically analyze this conversation:

1. **Initial Request**: User asked to implement a skill fixer and said "lets do it"
2. **Planning Phase**: I exited plan mode and created a worktree from main branch for skill-fixer development
3. **Implementation Attempt**: Tried using wfc-implement but it expected TASKS.md format, so...

### Prompt 22

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-prompt-fixer

# wfc-prompt-fixer

Fix Claude prompts using evidence-based diagnostics and structured rewrites.

## What It Does

Analyzes Claude prompts against a rubric of known failure modes and produces fixed versions that:

- Preserve original intent
- Resolve antipatterns (decorative roles, vague specs, contradictory instructions, etc.)
- Optimize for Claude 4.x literal instruction following
- Maintain token efficiency
...

### Prompt 23

Do we have other prompts to fix

### Prompt 24

We should not inline prompts

