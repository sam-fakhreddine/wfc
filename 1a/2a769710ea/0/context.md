# Session Context

## User Prompts

### Prompt 1

ok does WFC have a deep document skiull that can update our README?

### Prompt 2

yes please but not ebook style for the readme, keep it reasonable

### Prompt 3

Base directory for this skill: /Users/samfakhreddine/.claude/skills/docs-architect

## Use this skill when

- Working on docs architect tasks or workflows
- Needing guidance, best practices, or checklists for docs architect

## Do not use this skill when

- The task is unrelated to docs architect
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable ...

### Prompt 4

is our folder structure good? i feel like its too much nesting, are we following best practises?

### Prompt 5

do a plan session with a deep dive

### Prompt 6

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-plan

# WFC:PLAN - Adaptive Planning with Formal Properties

Converts requirements into structured implementation plans through adaptive interviewing.

## What It Does

1. **Adaptive Interview** - Asks intelligent questions that adapt based on answers
2. **Task Generation** - Breaks down requirements into structured TASKS.md with dependencies
3. **Property Extraction** - Identifies formal properties (SAFETY, LIVENESS, INVARI...

### Prompt 7

<task-notification>
<task-id>a7831ac</task-id>
<status>completed</status>
<summary>Agent "Deep dive WFC import analysis" completed</summary>
<result>Perfect! Now I have all the information I need. Let me create a comprehensive final report:

## WFC Comprehensive Import/Dependency Analysis

Based on a thorough analysis of the codebase, here are my findings:

### 1. **Which gitwork is actually used: `wfc_tools` (underscore) is the canonical version**

**Evidence:**
- **Only `wfc_tools` is imported...

### Prompt 8

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-validate

# WFC:VALIDATE - Thoughtful Advisor

The experienced staff engineer who asks "is this the right approach?" before we commit.

## What It Does

Analyzes any WFC artifact (plan, architecture, idea) across 7 dimensions:

1. **Do We Even Need This?** - Real problem vs hypothetical
2. **Is This the Simplest Approach?** - Avoid over-engineering
3. **Is the Scope Right?** - Not too much, not too little
4. **What Are We Tr...

### Prompt 9

# /sc:save - Session Context Persistence

## Triggers
- Session completion and project context persistence needs
- Cross-session memory management and checkpoint creation requests
- Project understanding preservation and discovery archival scenarios
- Session lifecycle management and progress tracking requirements

## Usage
```
/sc:save [--type session|learnings|context|all] [--summarize] [--checkpoint]
```

## Behavioral Flow
1. **Analyze**: Examine session progress and identify discoveries wor...

