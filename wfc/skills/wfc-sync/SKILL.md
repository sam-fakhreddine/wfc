---
name: wfc-sync
description: >
  Synchronizes agent context files (.claude/rules/ and .claude/skills/) with the
  current codebase state. Use when the codebase has changed and agent instructions
  are stale or missing.

  Direction: Codebase is the source of truth. Rules are updated to match code.
  This skill NEVER modifies source code, tests, or configuration files—only
  markdown documentation in .claude/ directories.

  Trigger phrases: "sync agent rules with code", "update claude rules from
  codebase", "document current code patterns", "my agent rules are outdated",
  "discover code conventions", "run /wfc-sync", "bootstrap claude rules",
  "create project.md context"
license: MIT
---

# WFC-SYNC - Sync Project Rules & Skills

Synchronizes agent context files (`.claude/rules/`, `.claude/skills/`) with the current codebase. Code is truth. Rules are updated to match implementation.

## When to Use

- After major refactors or architecture changes
- When onboarding a new project
- When existing rules reference outdated paths or patterns
- Periodically to capture undocumented conventions
- After adding new frameworks, languages, or tools
- First-run setup (creates initial context files)

## Quick Reference

| Phase | What Happens |
|-------|-------------|
| 1. Setup & Read | Create directories if needed, load existing rules |
| 2. Explore | Scan structure, identify technologies |
| 3. Compare | Identify outdated/missing documentation |
| 4. Sync Project | Update project.md context |
| 5. Sync Skills | Update existing skills |
| 6. New Rules | Document discovered patterns |
| 7. Summary | Report all changes |

---

## EXECUTION SEQUENCE

## Phase 1: Setup & Read Existing Rules

**FIRST STEP: Establish baseline.**

### Step 1.1: Ensure Directory Structure Exists

```bash
mkdir -p .claude/rules .claude/skills
```

If directories were just created, skip to Phase 2.

### Step 1.2: Read Custom Rules

1. **List all custom rules:**

   ```bash
   ls -la .claude/rules/*.md 2>/dev/null || echo "No rules found"
   ```

2. **Read each existing rule file** to understand:
   - What patterns are already documented
   - What areas are covered
   - What conventions are established

### Step 1.3: Read Custom Skills

1. **List all custom skills:**

   ```bash
   ls -la .claude/skills/*/SKILL.md 2>/dev/null || echo "No skills found"
   ```

2. **Read each SKILL.md** and verify referenced files exist:

   ```bash
   # For each file path mentioned in SKILL.md, verify existence
   # Flag skills with missing references as "needs update"
   ```

3. **Build inventory:**

   ```
   Documented rules: [list]
   Documented skills: [list]
   Skills with broken references: [list]
   Potential gaps: [areas not covered by existing rules]
   ```

---

## Phase 2: Explore Codebase

**Scan current state. Skip .claude/ directory—do not analyze rules as code patterns.**

### Step 2.1: Scan Directory Structure

```bash
tree -L 3 -I 'node_modules|.git|__pycache__|*.pyc|dist|build|.venv|.next|coverage|.cache|.pytest_cache|.ruff_cache|.claude'
```

**Exclude from analysis:**

- Binary files (images, compiled code, encrypted files)
- Lockfiles (package-lock.json, poetry.lock)
- `.claude/` directory contents (prevent self-referential rules)

### Step 2.2: Identify Technologies

Check for config files and identify:

- Primary language(s)
- Framework(s)
- Build tools
- Test frameworks
- Package managers

### Step 2.3: Read Files in Gap Areas

Based on Phase 1 inventory:

1. **Identify areas NOT covered by existing rules**
2. **Select 5-10 files** using these criteria:
   - Files in directories with recent commits (if git available)
   - Files in areas identified as gaps
   - Files with higher complexity or non-standard patterns
   - NOT standard boilerplate or generated code

3. **Read selected files** to understand actual patterns

### Step 2.4: Search for Specific Patterns

Only search for patterns relevant to identified gaps:

- API response structures (if API layer exists and is undocumented)
- Error handling formats (if error patterns not documented)
- Naming conventions (if naming rules are missing)
- Import organization (if module structure not documented)

---

## Phase 3: Compare & Identify Gaps

**Compare discovered state against existing documentation.**

### Step 3.1: Evaluate Each Existing Rule

For each rule, check:

- [ ] Does the documented pattern still appear in codebase?
- [ ] Are referenced file paths still correct?
- [ ] Are commands/URLs still valid?
- [ ] Has the technology stack changed in ways that affect this rule?

### Step 3.2: Categorize Findings

- **Outdated**: Rule contradicts current codebase patterns
- **Broken references**: Rule mentions files/paths that no longer exist
- **Still current**: Rule accurately describes current state
- **New gap**: Pattern exists in code but no rule documents it

### Step 3.3: Present Findings to User

**MANDATORY: Use AskUserQuestion**

```
"I compared existing rules with the codebase. Here's what I found:

Outdated rules: [list with what changed]
Broken references: [list with missing files]
Undocumented patterns: [list with examples]

What would you like to do?"
```

Options:

- "Update all outdated and broken rules" - Apply all fixes
- "Review each change" - Walk through one by one
- "Skip rule updates" - Keep existing rules as-is

---

## Phase 4: Sync Project Rule

**Update `.claude/rules/project.md` with current project state.**

### Step 4.1: If project.md exists

1. Compare documented tech stack with actual (from Phase 2.2)
2. Verify directory structure is current
3. Test that commands still work
4. **Preservation rule**: Keep any sections NOT in the standard template below. If uncertain whether a section is custom, flag for user review.
5. Update the "Last Updated" line with ISO 8601 date

### Step 4.2: If project.md doesn't exist, create it

```markdown
# Project: [Name]

**Last Updated:** YYYY-MM-DD

## Technology Stack

- **Language:** [primary language]
- **Framework:** [main framework, if any]
- **Build Tool:** [tool]
- **Testing:** [framework]
- **Package Manager:** [manager]

## Directory Structure

[Simplified tree - key source directories only, 10-15 lines max]

## Key Files

- **Config:** [main config files]
- **Entry Points:** [src/index.ts, main.py, etc.]
- **Tests:** [test directory path]

## Development Commands

- **Install:** `[command]`
- **Dev:** `[command]`
- **Build:** `[command]`
- **Test:** `[command]`
- **Lint:** `[command]` (if applicable)

## Architecture Notes

[1-3 sentences describing primary patterns. Omit if standard framework structure.]
```

---

## Phase 5: Sync Existing Skills

**Update custom skills to reflect current codebase.**

### Step 5.1: Verify Each Skill

For each skill found in Phase 1.3:

1. **Check referenced files**: For every file path mentioned in the skill, verify existence using `ls` or `glob`
2. **Check workflow validity**: Does the process described still match current codebase structure?
3. **Categorize**:
   - **Current**: All references valid, workflow accurate
   - **Needs update**: Some references broken or workflow changed
   - **Obsolete**: Tool/workflow no longer exists in codebase

### Step 5.2: Update Skills Needing Changes

**Use AskUserQuestion with multiSelect:**

```
"These skills need updates:"
[skill-name] - [What changed and why]
[skill-name] - [What changed and why]
"None" - Skip all skill updates
```

**Logic for multi-select**: If user selects "None" AND other options, "None" takes precedence (skip all updates).

For each selected skill (when "None" not selected):

- Update content to reflect current state
- Fix or remove broken file references
- Preserve custom sections not in standard skill template

### Step 5.3: Handle Obsolete Skills

If a skill is obsolete, ask user:

```
"[skill-name] appears obsolete because [reason]. Remove it?"
```

Options:

- "Yes, remove it"
- "Keep it anyway"
- "Update it instead" (return to Step 5.2)

---

## Phase 6: Discover New Rules

**Find and document patterns not covered by existing rules.**

### Step 6.1: Identify Undocumented Areas

Based on Phase 1 (existing rules) and Phase 2 (codebase exploration):

1. List codebase patterns NOT covered by existing rules
2. **Filter out**:
   - Standard framework behavior (e.g., React component structure)
   - Standard library conventions (e.g., Python PEP 8 naming)
   - Patterns in `.claude/` directory (no self-referential rules)
3. **Present candidates without ranking**:

   ```
   "I found these undocumented patterns. Select which to document as rules:"
   [Pattern name] - [Brief description + 1-2 file examples]
   [Pattern name] - [Brief description + 1-2 file examples]
   "None" - Don't create new rules
   ```

   **Note**: Do not claim to measure "frequency" or "likelihood" without tooling to calculate these. Present all candidates neutrally.

### Step 6.2: Document Selected Patterns

For each selected pattern (if "None" not selected):

1. **Ask clarifying questions** (1-3 questions max):
   - Edge cases or exceptions
   - Naming or location preferences

2. **Draft the rule** using this format:

   ```markdown
   # [Pattern Name]

   ## What This Is
   [1-2 sentence description of the pattern]

   ## When to Apply
   [Conditions where this pattern should be used]

   ## Example
   [Code or structure example]

   ## Exceptions
   [Known exceptions or edge cases]
   ```

3. Write to `.claude/rules/[pattern-name].md` using kebab-case filename

---

## Phase 7: Summary Report

**Report all changes made.**

```
## WFC-SYNC Summary

### Rules Updated
- [rule-name]: [what changed]

### Skills Updated
- [skill-name]: [what changed]

### New Rules Created
- [rule-name]: [pattern documented]

### Skipped
- [item]: [reason]

### Recommended Next Steps
- [action if any]
```
