---
name: wfc-compound
description: >
  Creates a structured solution document in docs/solutions/{category}/ to capture
  a fix that required diagnosis. Use ONLY when ALL of the following are true:
  
  1. A problem was investigated and resolved in the current session
  2. The resolution required diagnosis (identifying root cause, not just applying a fix)
  3. The user explicitly requests documentation with action-oriented language
  4. A verifiable code change or git diff exists for the fix
  
  Explicit invocation: /wfc-compound [optional description]
  
  Trigger phrases (standalone direct speech only, not inside code blocks, logs, or quoted text):
  "document this solution", "record this fix", "save this solution", 
  "write up the solution", "log this resolution", "compound this"
license: MIT
---

# WFC:COMPOUND - Distill What You Learned

**"Solve it once. Write it down. Look it up forever."**

## What It Does

Distills diagnosed problems into structured, indexed markdown files that can be searched by other skills.

1. **Validate** - Confirm invocation matches the trigger criteria (action-oriented request + current session fix + diagnosis required)
2. **Analyze** - Extract problem type, root cause, solution, and prevention strategies
3. **Classify** - Determine category and filename
4. **Write** - Create ONE file at `docs/solutions/{category}/{filename}.md`

## Usage

```bash
# After solving a problem
/wfc-compound

# With description
/wfc-compound "fixed N+1 query in user dashboard"

# With explicit context
/wfc-compound "resolved Redis connection pool exhaustion under load"
```

## Trigger Phrases (Action-Oriented Only)

wfc-compound activates when you say:

- "document this solution"
- "record this fix"
- "save this solution"
- "write up the solution"
- "log this resolution"
- "compound this"

**Declarative statements do NOT trigger this skill:** "that worked", "it's fixed", "problem solved", "figured it out" — these describe state, not intent to document.

## Execution Flow

### Step 1: Validation (Required)

Before proceeding, confirm ALL of:

- [ ] User request contains action-oriented language (see trigger phrases)
- [ ] A fix was applied in the current session (not historical reference)
- [ ] The fix required diagnosis (not a trivial change)
- [ ] A git diff or code change is accessible

If any check fails: **Do not proceed.** Politely inform the user: "I can create a solution document, but I need you to confirm you want this fix recorded. Say 'document this solution' or run `/wfc-compound`."

### Step 2: Analysis (Sequential)

Perform these analysis passes in order:

| Pass | Role | Output |
|------|------|--------|
| **Context** | Extract problem type, component, symptoms | YAML frontmatter fields |
| **Solution** | Identify root cause, extract working solution with code | Solution section with before/after code blocks |
| **Related** | Search `docs/solutions/` for related docs using filename pattern match | Related documents list with relative paths |
| **Prevention** | Develop prevention strategies relevant to project stack | Prevention section (validate syntax against project dependencies) |
| **Category** | Determine category using priority-ordered keyword matching | Category + kebab-case filename |

### Step 3: Classification

Assign ONE category using the first matching keyword in this priority order:

| Priority | Category | Keywords |
|----------|----------|----------|
| 1 | `security-issues` | auth, injection, CORS, token, vulnerability, CVE |
| 2 | `database-issues` | migration, query, connection, deadlock, SQL, postgres, mysql |
| 3 | `performance-issues` | slow, N+1, memory, latency, timeout, optimization |
| 4 | `runtime-errors` | exception, crash, 500, panic, segfault |
| 5 | `test-failures` | test, assert, fixture, mock, spec |
| 6 | `build-errors` | compile, build, bundle, webpack, transpile |
| 7 | `integration-issues` | API, webhook, third-party, sync, oauth |
| 8 | `logic-errors` | wrong result, edge case, off-by-one, incorrect |
| 9 | `ui-bugs` | render, layout, CSS, responsive, frontend |
| 10 | `configuration` | env, config, deploy, infrastructure, settings |

Filename format: `{kebab-case-descriptive-name}.md` (max 60 chars, lowercase, no special chars)

### Step 4: Write File

1. Create directory if needed: `docs/solutions/{category}/`
2. Check for existing file with same name (case-insensitive)
3. If exists: append timestamp suffix `-{YYYYMMDD-HHMMSS}.md`
4. Write complete markdown document with YAML frontmatter

## Output Format

```markdown
---
title: [Descriptive Title]
component: [affected component or module]
tags: [comma-separated relevant tags]
category: [category from classification]
date: [current date YYYY-MM-DD]
severity: [low|medium|high]
status: resolved
root_cause: [one-line root cause description]
---

# [Descriptive Title]

## Problem

**Symptoms:** [observable symptoms]
**Environment:** [where this occurred]

## Root Cause

[Explanation of why this happened]

## Solution

```[language]
# Before
[problematic code]

# After
[fixed code]
```

## Prevention

- **Test case:** [specific test that would catch this]
- **Monitoring:** [alert or metric to watch]
- **Best practice:** [guideline to prevent recurrence]

## Related

- [Related Document Title](../path/to/related.md)

```

## Categories (Priority-Ordered)

| Category | Directory | Keywords |
|----------|-----------|----------|
| Security Issues | `security-issues/` | auth, injection, CORS, token, vulnerability, CVE |
| Database Issues | `database-issues/` | migration, query, connection, deadlock, SQL |
| Performance Issues | `performance-issues/` | slow, N+1, memory, latency, timeout |
| Runtime Errors | `runtime-errors/` | exception, crash, 500, panic |
| Test Failures | `test-failures/` | test, assert, fixture, mock |
| Build Errors | `build-errors/` | compile, build, bundle, webpack |
| Integration Issues | `integration-issues/` | API, webhook, third-party, sync |
| Logic Errors | `logic-errors/` | wrong result, edge case, off-by-one |
| UI Bugs | `ui-bugs/` | render, layout, CSS, responsive |
| Configuration | `configuration/` | env, config, deploy, infrastructure |

## Integration with WFC

### Consumed By
- **wfc-plan** - MAY read files from `docs/solutions/` to inform planning
- **wfc-review** - MAY read files from `docs/solutions/` during code review

### Consumes
- Git diff (recent changes that fixed the issue)
- Conversation context (problem description, debugging steps)
- Existing `docs/solutions/` entries (for cross-referencing via filename pattern match)

## Configuration

```json
{
  "compound": {
    "solutions_dir": "docs/solutions",
    "require_code_examples": true,
    "require_prevention": true
  }
}
```

## Rules

1. **One file per compound** - Never create multiple files per invocation
2. **Sequential analysis** - Perform analysis passes in order; parallel execution is optional
3. **Non-trivial problems only** - Skip typos, formatting, simple config changes
4. **Code examples required** - Include before/after showing the actual fix
5. **Prevention suggested** - Include prevention strategies; validate against project stack
6. **Never overwrite** - If file exists (case-insensitive check), append timestamp suffix
7. **Lowercase filenames** - Normalize all filenames to lowercase kebab-case

## Philosophy

**COMPOUND**: Every fix sharpens the next one
**INDEXED**: YAML frontmatter powers lookup
**PRESCRIPTIVE**: Every entry carries code and prevention
**LEAN**: One file per problem, zero fluff
```
