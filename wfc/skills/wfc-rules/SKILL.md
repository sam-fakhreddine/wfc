---
name: wfc-rules
description: Markdown-based rule engine for custom code enforcement without writing code. Drop .wfc/rules/*.md files with YAML frontmatter to define patterns that are enforced via PreToolUse hooks. Use when you want project-specific coding standards enforced automatically. Triggers on "create rule", "enforce standard", "add coding rule", or explicit /wfc-rules. Ideal for team conventions and project-specific requirements. Not for security patterns (use wfc-safeguard instead).
license: MIT
---

# WFC:RULES - Markdown-Based Code Enforcement

Define project-specific coding rules as simple Markdown files. No code required.

## What It Does

WFC Rules lets you create custom enforcement rules that run automatically via PreToolUse hooks. Each rule is a Markdown file with YAML frontmatter that defines when and how to enforce the rule.

## Quick Start

1. Create a rules directory:

```bash
mkdir -p .wfc/rules
```

2. Create a rule file:

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

3. The rule is enforced automatically via the PreToolUse hook.

## Rule Format

Rules are Markdown files (`.md`) in `.wfc/rules/` with YAML frontmatter:

```yaml
---
name: rule-identifier          # Required: unique rule name
enabled: true                  # Optional: disable without deleting (default: true)
event: file                    # Required: "file", "bash", or "all"
action: warn                   # Required: "block" or "warn"
conditions:                    # Required: list of conditions (AND logic)
  - field: new_text, operator: regex_match, pattern: "pattern_here"
---

Human-readable message shown when the rule triggers.
This is the body of the Markdown file.
```

### Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | string | Unique rule identifier |
| `enabled` | No | true/false | Default: true |
| `event` | Yes | file, bash, all | Which tool types to check |
| `action` | Yes | block, warn | block prevents the action; warn allows it |
| `conditions` | Yes | list | All conditions must match (AND logic) |

### Condition Fields

| Field | Description |
|-------|-------------|
| `field` | The data field to check |
| `operator` | How to compare |
| `pattern` / `value` | The expected value |

### Available Fields

| Field | Available For | Maps To |
|-------|---------------|---------|
| `new_text` | Write, Edit, NotebookEdit | content / new_string / new_source |
| `file_path` | Write, Edit, NotebookEdit | file_path / notebook_path |
| `command` | Bash | command |

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `regex_match` | Field matches regex | `"TODO\\b"` |
| `contains` | Field contains string | `"debugger"` |
| `not_contains` | Field does not contain string | `"use strict"` |
| `equals` | Field equals value exactly | `"package.json"` |
| `starts_with` | Field starts with value | `"/etc/"` |
| `ends_with` | Field ends with value | `".env"` |

## Examples

### Block writing to .env files

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

### Warn on TODO comments

```markdown
---
name: todo-needs-ticket
enabled: true
event: file
action: warn
conditions:
  - field: new_text, operator: regex_match, pattern: "TODO(?!\\s*\\(\\w+-\\d+\\))"
---

TODOs should reference a ticket: `TODO(PROJ-123)`.
Untracked TODOs get lost. Create a ticket first.
```

### Block dangerous bash commands

```markdown
---
name: no-force-push
enabled: true
event: bash
action: block
conditions:
  - field: command, operator: contains, value: "push --force"
---

Force push is blocked by project policy. Use `--force-with-lease` instead
for safer force pushes that check for upstream changes.
```

### Enforce import style

```markdown
---
name: no-wildcard-imports
enabled: true
event: file
action: warn
conditions:
  - field: new_text, operator: regex_match, pattern: "from\\s+\\S+\\s+import\\s+\\*"
  - field: file_path, operator: ends_with, value: ".py"
---

Wildcard imports (`from x import *`) pollute the namespace.
Use explicit imports instead: `from x import foo, bar`.
```

### Multiple conditions (AND logic)

All conditions must match for the rule to trigger:

```markdown
---
name: no-any-type
enabled: true
event: file
action: warn
conditions:
  - field: file_path, operator: ends_with, value: ".py"
  - field: new_text, operator: regex_match, pattern: ":\\s*Any\\b"
---

Avoid using `Any` type annotation. Use specific types or generics.
See: https://mypy.readthedocs.io/en/stable/kinds_of_types.html
```

## Architecture

```
PreToolUse Hook
      |
      v
pretooluse_hook.py
      |
      +---> security_hook.py (built-in patterns)
      |
      +---> rule_engine.py (custom rules)
                |
                v
          config_loader.py
                |
                v
         .wfc/rules/*.md
```

### Key Files

- `wfc/scripts/hooks/rule_engine.py` - Rule evaluation engine
- `wfc/scripts/hooks/config_loader.py` - YAML frontmatter parser
- `wfc/scripts/hooks/pretooluse_hook.py` - Main dispatcher

## Tips

- **Start with warnings**: Use `action: warn` while developing rules, switch to `block` when confident.
- **Be specific**: Combine multiple conditions to avoid false positives.
- **Document well**: The Markdown body is shown to the user - make it helpful.
- **Disable, don't delete**: Set `enabled: false` to temporarily disable a rule.
- **Use regex sparingly**: `contains` and `starts_with` are faster and clearer.

## Integration with WFC

- **wfc-safeguard**: Built-in security patterns. Rules is for project-specific conventions.
- **wfc-review**: Reviews code after writing. Rules prevents issues during writing.
- **wfc-test**: Tests verify behavior. Rules enforce coding standards.
