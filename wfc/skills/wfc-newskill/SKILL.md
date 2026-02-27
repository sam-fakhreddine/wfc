---
name: wfc-newskill
description: >
  Factory skill for scaffolding a new WFC (Workflow Control Framework) skill
  definition file (.md). This skill conducts a requirements interview and
  outputs a structured prompt file suitable for the WFC pipeline.

  INVOKE STRICTLY when:
  1. User explicitly requests to CREATE, BUILD, or SCAFFOLD a new skill/tool.
  2. The requested capability DOES NOT currently exist (agent must check registry).
  3. The output target is a reusable WFC skill file, not application code.

  DO NOT INVOKE for executing tasks, modifying existing skills, or writing
  non-skill scripts.

license: MIT
---

# WFC:NEWSKILL - Meta-Skill Builder

Scaffolds new WFC skills. Produces a spec-compliant prompt file and,
optionally, chains into `wfc-plan` → `wfc-implement` for full build-out.

## Not for

- **Modifying existing skills**. If the skill name exists in the registry, halt.
  Indicator: Request uses verbs "update," "fix," "change," or "add to" regarding
  a specific named skill. Use `wfc-implement` instead.
- **Executing capabilities**. If the user wants a task performed (e.g., "review
  this code"), do not scaffold; invoke the appropriate existing skill.
- **Standalone scripts or application code**. Indicator: Request asks for .py,
  .sh, .js files or "scripts" without mentioning WFC or skill registration.
- **General project planning**. Indicator: Request asks for TASKS.md, roadmaps,
  or decomposition without defining a specific agent capability.
- **Processing unknown flags**. If the user provides flags not defined below,
  ignore them. Do not pass extra flags to downstream skills.

## Usage

```bash
# Interview mode — produce prompt file only
/wfc-newskill

# Auto-build mode — produce prompt file, then invoke wfc-plan → wfc-implement
/wfc-newskill --build
```

**Removed flags**: `--from-chat` is not implemented. Do not infer requirements
from conversation history.

## Pre-flight Checks

Before beginning, verify:

1. **Name Collision**: Check the WFC skill registry for the proposed name.
   - If the exact name exists: Halt and report conflict.
   - If registry is inaccessible: Warn user "Registry check failed. Proceed with
     caution to avoid overwriting existing skills."
2. **Dependencies**: If `--build` is specified, verify `wfc-plan` and
   `wfc-implement` are available. If missing, downgrade to interview-only mode
   and notify user: "Dependency [missing-skill] not found. Proceeding in
   interview-only mode."

## Interview Process

Ask the following questions in order. Questions marked **[required]** must
receive a substantive answer.

**Strict Flow Control**:

- Do not reorder or skip questions.
- If the user answers multiple questions at once, acknowledge and proceed.
- **Re-prompt Limit**: If a required question receives a non-answer, re-prompt
  once with an example. If still unresolved, HALT with error: "Cannot generate
  skill: Requirement [Question Name] unclear."

1. **[required] Purpose**: What specific capability will this skill provide?
   (Describe the action and outcome in 1-2 sentences.)
2. **[required] Trigger / Name**: What slash command name should invoke it?
   - **Validation**: Normalize to `wfc-{name}`. Force lowercase.
   - **Sanitization**: Allow ONLY `[a-z0-9-]`. Max 32 chars.
   - **Action**: If the user provides "My Skill", propose `wfc-my-skill`.
   - **Rejection**: If the name contains invalid chars or is empty, reject and
     ask for a new name immediately.
3. **[required] Input**: What inputs does the skill accept?
   (Files, flags, arguments, or stdin.)
4. **[required] Output**: What artifacts does the skill produce?
   (Files written, stdout output, or side effects.)
5. **[optional] Agent structure**: Single-agent or multi-agent? (If multi-agent,
   define roles.)

## Output Generation

Upon completion of the interview:

1. Create a file named `{normalized-name}-prompt.md`.
2. **Chaining**: If `--build` was specified, execute the chain:
   `/wfc-plan {normalized-name}-prompt.md` → `/wfc-implement`.
