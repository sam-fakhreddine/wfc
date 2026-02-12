---
name: wfc-newskill
description: Meta-skill for creating new WFC skills. Conducts structured interview to understand skill requirements, generates skill prompt and SKILL.md structure, and optionally auto-builds implementation using wfc-plan → wfc-implement workflow. Use when extending WFC with new capabilities or creating custom workflow automations. Triggers on "create a new skill", "build a WFC skill for", "I want to add a skill that", or explicit /wfc-newskill. Ideal for WFC extension and custom automation. Not for general feature implementation or one-off scripts.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [--build or --from-chat]
---

# WFC:NEWSKILL - Meta-Skill Builder

The skill that builds skills. WFC builds itself.

## What It Does

1. **Interviews** user about the new skill (adaptive questioning)
2. **Generates** Claude Code agentic prompt following WFC conventions
3. **Optionally** auto-builds using `wfc-plan` → `wfc-implement`

## Usage

```bash
# Interview mode - generate prompt only
/wfc-newskill

# Auto-build mode - generate and build
/wfc-newskill --build

# Bootstrap from conversation
/wfc-newskill --from-chat
```

## Interview Domains

Gathers requirements across 8 skill dimensions:

1. **Purpose & Trigger** - What does it do? Slash command name?
2. **Input** - What does it receive?
3. **Output** - What does it produce?
4. **Agents** - Multi-agent or single-agent?
5. **Integration** - Which WFC skills does it integrate with?
6. **Configuration** - What's configurable?
7. **Telemetry** - What should be tracked?
8. **Properties** - Any formal properties?

## Output

### Generated Prompt ({skill-name}-prompt.md)

Complete Claude Code agentic prompt following WFC patterns:
- YAML front matter (name, description, user-invocable)
- Purpose and usage
- Inputs/outputs
- Integration points
- Configuration schema
- Telemetry specification
- ELEGANT/MULTI-TIER/PARALLEL philosophy

### Optional: Auto-Build

When `--build` flag is used:
1. Feeds prompt into `wfc-plan` → generates TASKS.md
2. Feeds TASKS.md into `wfc-implement` → builds the skill
3. Registers new skill as working slash command

## Meta-Recursive Magic

WFC can build itself:

```bash
# Build a new skill to analyze database schemas
/wfc-newskill --build
> What should this skill do?
> "Analyze database schema and generate data models"

[Interview...]

[Auto-build using wfc-plan → wfc-implement...]

# New skill is ready
/wfc-db-schema path/to/schema.sql
```

## Philosophy

**ELEGANT**: Simple interview, template-based generation
**MULTI-TIER**: Interview → Generation → Build (clean layers)
**PARALLEL**: Meta-recursive (builds itself)
