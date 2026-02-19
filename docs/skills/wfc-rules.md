# wfc-rules

## What It Does

`wfc-rules` is a markdown-based rule engine that lets you enforce project-specific coding standards without writing any Python or shell code. You drop `.wfc/rules/*.md` files with YAML frontmatter into your project, and those rules are automatically enforced via PreToolUse hooks on every Write, Edit, and Bash tool call. Rules can block actions or emit warnings, and the human-readable Markdown body becomes the message shown to developers when a rule triggers.

## When to Use It

- When your team has conventions that aren't covered by general linters (naming patterns, import styles, API response shapes)
- When you want to enforce project-specific policies without modifying shared tooling
- When onboarding new contributors who might not know local conventions
- As a complement to `wfc-safeguard` (which handles built-in security patterns) for project-specific standards

## Usage

```bash
/wfc-rules
```

Then create rule files manually in `.wfc/rules/`:

```bash
mkdir -p .wfc/rules
# Create a rule file (see format below)
```

## Example

Rule file at `.wfc/rules/no-console-log.md`:

```markdown
---
name: no-console-log
enabled: true
event: file
action: warn
conditions:
  - field: new_text, operator: regex_match, pattern: "console\\.log\\("
---

Avoid console.log() in production code. Use the project logger instead:

    import { logger } from '@/lib/logger';
    logger.info('message');
```

When Claude writes a file containing `console.log(`, the hook fires:

```
[WARN] Rule triggered: no-console-log
Avoid console.log() in production code. Use the project logger instead:

    import { logger } from '@/lib/logger';
    logger.info('message');
```

Another example — block direct writes to `.env` files:

```markdown
---
name: protect-env-files
enabled: true
event: file
action: block
conditions:
  - field: file_path, operator: ends_with, value: ".env"
---

Do not write directly to .env files. Use .env.example for templates
and set actual values through your secrets manager.
```

## Options

Rules are configured entirely through YAML frontmatter in each `.wfc/rules/*.md` file.

**Frontmatter fields:**

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | string | Unique rule identifier |
| `enabled` | No | true/false | Default: true. Set false to disable without deleting. |
| `event` | Yes | `file`, `bash`, `all` | Which tool types to check |
| `action` | Yes | `block`, `warn` | `block` prevents the action; `warn` allows it with a message |
| `conditions` | Yes | list | All conditions must match (AND logic) |

**Condition operators:** `regex_match`, `contains`, `not_contains`, `equals`, `starts_with`, `ends_with`

**Condition fields:** `new_text` (file content), `file_path` (path being written), `command` (Bash command)

## Integration

**Produces:** Active custom enforcement rules loaded by the PreToolUse hook at runtime from `.wfc/rules/*.md`

**Consumes:** Every Write, Edit, NotebookEdit, and Bash tool call

**Next step:** Run `/wfc-sync` periodically to discover new conventions in the codebase and automatically generate corresponding rule files, keeping your rules aligned with how the project actually evolves.
