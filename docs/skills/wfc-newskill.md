# wfc-newskill

## What It Does

`wfc-newskill` is the meta-skill that builds WFC skills. It conducts a structured 8-dimension interview to understand what the new skill should do, then generates a complete Claude Code agentic prompt and SKILL.md following WFC conventions. Optionally, with `--build`, it feeds the generated prompt directly into `wfc-plan` and `wfc-implement` to auto-build and register the skill as a working slash command.

## When to Use It

- You want to extend WFC with a new capability or custom workflow automation
- You need to create a repeatable, installable slash command for a task you do regularly
- You want WFC to generate the skill scaffolding rather than writing it by hand
- You have a clear idea of what a new skill should do and want a structured interview to flesh out the details
- You want to auto-build a skill without leaving the WFC pipeline

## Usage

```bash
/wfc-newskill
/wfc-newskill --build
/wfc-newskill --from-chat
```

## Example

```
User: /wfc-newskill --build

> What should this skill do?
> "Analyze database schema and generate data models"

> What slash command name?
> "wfc-db-schema"

> What does it receive as input?
> "Path to a .sql schema file or a live database connection string"

> What does it produce?
> "Pydantic models, SQLAlchemy ORM classes, and a migration checklist"

> Single agent or multi-agent?
> "Single agent, sequential"

> Which WFC skills does it integrate with?
> "wfc-review for code quality, wfc-test for generated model tests"

> Configuration options?
> "Target ORM: sqlalchemy | django | none"

> What to track in telemetry?
> "Schema file size, number of models generated, review score"

[Interview complete]

Generating wfc-db-schema-prompt.md...
Feeding into wfc-plan → wfc-implement...

✅ Skill built and registered
✅ /wfc-db-schema is now available
```

## Options

```bash
/wfc-newskill               # Interview mode — generates prompt and SKILL.md only
/wfc-newskill --build       # Interview + auto-build using wfc-plan → wfc-implement
/wfc-newskill --from-chat   # Bootstrap requirements from current conversation context
```

## Integration

**Produces:**

- `{skill-name}-prompt.md` — complete Claude Code agentic prompt with YAML front matter, inputs/outputs, integration points, configuration schema, and telemetry spec
- `SKILL.md` structure following WFC conventions
- (with `--build`) working slash command registered and ready for use

**Consumes:**

- Your answers across 8 interview dimensions: purpose, input, output, agents, integration, configuration, telemetry, properties
- (with `--from-chat`) conversation context captured automatically via `--from-chat`

**Next step:** After generating the prompt, review `{skill-name}-prompt.md`, then run `wfc validate` to confirm Agent Skills compliance before distributing.
