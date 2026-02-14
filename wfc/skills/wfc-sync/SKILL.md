---
name: wfc-sync
description: Sync project rules and skills with codebase state. Discovers undocumented patterns, updates stale rules, creates project context, and identifies new conventions. Triggers on "sync rules", "update project rules", "discover patterns", "sync project", or explicit /wfc-sync. Use after major refactors, onboarding, or when rules drift from reality.
license: MIT
---

# WFC-SYNC - Sync Project Rules & Skills

**Sync custom rules and skills with the current state of the codebase.** Reads existing rules, explores code patterns, identifies gaps, updates documentation, and creates new rules when conventions are discovered.

## When to Use

- After major refactors or architecture changes
- When onboarding a new project to WFC
- When rules feel stale or outdated
- Periodically to capture tribal knowledge
- After adding new frameworks, languages, or tools

## Quick Reference

| Phase | What Happens |
|-------|-------------|
| 1. Read Existing | Load rules & skills, build inventory |
| 2. Explore | Discover patterns in codebase |
| 3. Compare | Find outdated/missing documentation |
| 4. Sync Project | Update project.md context |
| 5. Sync Skills | Update existing skills |
| 6. New Rules | Document undocumented patterns |
| 7. Summary | Report all changes |

---

# EXECUTION SEQUENCE

## Phase 1: Read Existing Rules & Skills

**MANDATORY FIRST STEP: Understand what's already documented.**

### Step 1.1: Read Custom Rules

1. **List all custom rules:**

   ```bash
   ls -la .claude/rules/*.md 2>/dev/null
   ```

2. **Read each existing rule file** to understand:
   - What patterns are already documented
   - What areas are covered
   - What conventions are established

### Step 1.2: Read Custom Skills

1. **List all custom skills:**

   ```bash
   ls -la .claude/skills/*/SKILL.md 2>/dev/null
   ```

2. **Read each SKILL.md** to understand:
   - What workflows are documented
   - Whether each skill is still relevant

3. **Build mental inventory:**
   ```
   Documented rules: [list]
   Documented skills: [list]
   Potential gaps: [areas not covered]
   Possibly outdated: [rules with stale content]
   ```

## Phase 2: Explore Codebase

**Discover current patterns using search and file analysis.**

1. **Scan directory structure:**

   ```bash
   tree -L 3 -I 'node_modules|.git|__pycache__|*.pyc|dist|build|.venv|.next|coverage|.cache|.pytest_cache|.ruff_cache'
   ```

2. **Identify technologies:**
   - Check `package.json`, `pyproject.toml`, `tsconfig.json`, `go.mod`, `Cargo.toml`
   - Note frameworks, build tools, test frameworks, package managers

3. **Search for patterns:**
   - Use Grep for API response structures, error formats
   - Use Grep for naming conventions, prefixes/suffixes
   - Use Grep for import patterns, module organization
   - Search based on gaps identified in Phase 1

4. **Read representative files** (5-10) in key areas to understand actual patterns

## Phase 3: Compare & Identify Gaps

**Compare discovered patterns against existing documentation.**

1. **For each existing rule, check:**
   - Is the documented pattern still accurate?
   - Are there new patterns not yet documented?
   - Has the technology stack changed?
   - Are commands/paths still correct?

2. **Identify gaps:**
   - Undocumented tribal knowledge
   - New conventions that emerged
   - Changed patterns not reflected in rules
   - Missing areas entirely

3. **Use AskUserQuestion to confirm findings:**

   Ask: "I compared existing rules with the codebase. Here's what I found:"
   Options:
   - "Update all" - Apply all suggested changes
   - "Review each" - Walk through changes one by one
   - "Skip updates" - Keep existing rules as-is

## Phase 4: Sync Project Rule

**Update `.claude/rules/project.md` with current project state.**

### If project.md exists:
- Compare documented tech stack with actual
- Verify directory structure is current
- Check if commands still work
- Update timestamp
- Preserve custom sections

### If project.md doesn't exist, create it:

```markdown
# Project: [Name]

**Last Updated:** [date]

## Technology Stack

- **Language:** [primary]
- **Framework:** [main framework]
- **Build Tool:** [tool]
- **Testing:** [framework]
- **Package Manager:** [manager]

## Directory Structure

[Simplified tree - key directories only]

## Key Files

- **Config:** [main config files]
- **Entry Points:** [src/index.ts, main.py, etc.]
- **Tests:** [test directory]

## Development Commands

- **Install:** `[command]`
- **Dev:** `[command]`
- **Build:** `[command]`
- **Test:** `[command]`
- **Lint:** `[command]`

## Architecture Notes

[Brief patterns description]
```

## Phase 5: Sync Existing Skills

**Update custom skills to reflect current codebase.**

### Step 5.1: Review Each Skill

For each skill found in Phase 1.2:

1. Does the workflow/tool still exist in codebase?
2. Has the process changed?
3. Are referenced files/scripts still valid?
4. Are the steps still accurate?

### Step 5.2: Update Outdated Skills

Use AskUserQuestion with multiSelect:

- "[skill-name]" - [What changed and why]
- "None" - Skip skill updates

For each selected skill:
- Update content to reflect current state
- Update any referenced scripts/assets

### Step 5.3: Remove Obsolete Skills

If a skill is no longer relevant, ask user:
- "Yes, remove it"
- "Keep it"
- "Update instead"

## Phase 6: Discover New Rules

**Find and document undocumented tribal knowledge.**

### Step 6.1: Identify Undocumented Areas

Based on Phase 1 (existing rules) and Phase 2 (codebase exploration):

1. List areas NOT yet covered by existing rules
2. Prioritize by:
   - Frequency of pattern usage
   - Uniqueness (not standard framework behavior)
   - Likelihood of mistakes without documentation

3. Use AskUserQuestion with multiSelect:
   - "[Area 1]" - [Pattern found, why it matters]
   - "[Area 2]" - [Pattern found, why it matters]
   - "None" - Skip adding new rules

### Step 6.2: Document Selected Patterns

For each selected pattern:

1. Ask clarifying questions about edge cases and exceptions
2. Draft the rule based on codebase examples + user input
3. Confirm before creating

### Step 6.3: Rule Format

```markdown
## [Standard Name]

[One-line summary]

### When to Apply
- [Trigger 1]
- [Trigger 2]

### The Pattern
```[language]
[Code example]
```

### Why
[1-2 sentences if not obvious]

### Common Mistakes
- [Mistake to avoid]
```

Write to `.claude/rules/[pattern-name].md`

## Phase 7: Summary

**Report what was synced:**

```
## Sync Complete

**Rules Updated:**
- project.md - Updated tech stack, commands

**New Rules Created:**
- api-responses.md - Response envelope pattern

**Skills Updated:**
- my-workflow - Updated steps for new API

**No Changes Needed:**
- existing-rule.md - Still current
```

Offer to continue:
- "Discover more patterns" - Look deeper
- "Create new skills" - Invoke /wfc-newskill for workflow patterns
- "Done" - Finish sync

---

## Guidelines

- **Always use AskUserQuestion** when asking the user anything
- **Read before writing** — Check existing rules before creating new ones
- **Write concise rules** — Every word costs tokens in context
- **Idempotent** — Running multiple times produces consistent results
- **Lead with the rule** — What to do first, why second
- **Use code examples** — Show, don't tell
- **Skip the obvious** — Don't document standard framework behavior
- **One concept per rule** — Don't combine unrelated patterns
- **Max ~100 lines per file** — Split large topics

## Output Locations

| Type | Location | Purpose |
|------|----------|---------|
| Project context | `.claude/rules/project.md` | Tech stack, structure, commands |
| Discovered rules | `.claude/rules/[name].md` | Tribal knowledge, conventions |
| Skills | `.claude/skills/[name]/` | Multi-step workflows |
