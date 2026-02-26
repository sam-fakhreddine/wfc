---
name: wfc-newskill
description: >
  Meta-skill for scaffolding a new, reusable WFC (Workflow Control Framework)
  skill conforming to the agentskills.io specification. Conducts a structured
  requirements interview across defined dimensions, produces a
  {skill-name}-prompt.md file using the WFC skill template, and optionally
  chains into wfc-plan → wfc-implement for full build-out.

  INVOKE when the user's unambiguous intent is to CREATE A NEW, NAMED,
  REUSABLE WFC SKILL that does not yet exist. Required signals: the user
  must explicitly describe a new capability to be packaged as a WFC skill
  file. Canonical phrases: "create a new WFC skill", "build a WFC skill for
  [capability]", "I want to add a WFC skill that [does X]", "extend WFC with
  a new skill", "/wfc-newskill".

  DO NOT INVOKE (see not_for below) for any request where the output is not
  a new agentskills.io-spec skill file, or where the named skill already
  exists in the registry.
license: MIT
---

# WFC:NEWSKILL - Meta-Skill Builder

## Not for

- Implementing features, modules, or integrations in an existing codebase
  — use wfc-implement. Indicator: output is application code, not a skill
  file.
- One-off scripts, cron jobs, or standalone automations whose output is not
  a SKILL.md artifact.
- Workflow design, process planning, or project decomposition — use
  wfc-plan. Indicator: user's desired output is a plan or TASKS.md.
- Modifying, refactoring, or debugging an existing WFC skill — use
  wfc-implement. Indicator: target skill already exists by name.
- Invoking or running an existing WFC skill. Indicator: user names a
  specific existing skill rather than describing a new capability.
- Re-scaffolding a skill whose name already exists in the WFC registry
  without explicit --force flag.
- Modifying WFC core infrastructure, routing logic, or registry mechanisms
  — these are not addressable as skill files.
- Any request where "skill" is used in everyday language to mean ability or
  feature, not a WFC skill file artifact.

Scaffolds new WFC skills. Produces a spec-compliant prompt file and,
optionally, builds and places the implementation.

## Usage

```bash
# Interview mode — produce prompt file only
/wfc-newskill

# Auto-build mode — produce prompt file, then invoke wfc-plan → wfc-implement
/wfc-newskill --build
```

**Removed flags**: `--from-chat` is not implemented. Do not attempt to
infer requirements from conversation history.

## Pre-flight Checks

Before beginning the interview, verify:

1. Proposed skill name does not match any existing entry in the WFC skill
   registry. If it does, halt and report the conflict. Do not proceed without
   `--force`.
2. If `--build` is specified, verify that `wfc-plan` and `wfc-implement` are
   available as registered commands. If either is missing, downgrade to
   interview-only mode and notify the user before proceeding.

## Interview Process

Ask the following questions in order. Questions marked **[required]** must
receive a substantive answer before generation proceeds. If the user provides
a non-answer ("I don't know", blank, or equivalent) to a required question,
re-prompt once with a clarifying example. If still unresolved, halt and
explain that generation cannot proceed without this information.

Do not reorder, skip, or add questions beyond those listed. Do not describe
this process as "adaptive."

1. **[required] Purpose**: What should this skill do? Describe the
   capability in one or two sentences.
2. **[required] Trigger / Name**: What slash command name should invoke it?
   (Format: `wfc-{name}`, alphanumeric and hyphens only, max 32 characters.)
   Normalize the name to lowercase with hyphens; show the normalized name to
   the user and confirm before continuing.
3. **[required] Input**: What does the skill receive? (Files, flags,
   arguments, stdin, none.)
4. **[required] Output**: What does the skill produce? (Files written,
   stdout, side effects, none.)
5. **[optional] Agent structure**: Single-agent or multi-agent? If
   multi-agent, how many agents and what are their roles?
