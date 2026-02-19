# Session Context

## User Prompts

### Prompt 1

ok I run wfc local and this is the development code.
I want to remove the "installed" version of wfc without losing my development data because I want to get to the version we have in `main` right now. Understood?

### Prompt 2

what do you mean unstaged?

### Prompt 3

.development should move to ~/.wfc/development (thats the new pattern)
same with test-results and validation
and then we deep dive on docs and skills

### Prompt 4

yes nothing lost just moved

### Prompt 5

tell me what is unstaged and why

### Prompt 6

ok lets drop anything that is duplicated.
and lets compare to what is in main right now because I merged a large PR an hour ago

### Prompt 7

gonna need to rbanch because you cant push to main but #1

### Prompt 8

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-pr-comments

# WFC:PR-COMMENTS - Intelligent PR Comment Triage & Fix

**Fetch, triage, fix.** Automates addressing PR review comments from humans, Copilot, CodeRabbit, and other reviewers.

## What It Does

1. **Fetch** all PR comments via `gh` CLI
2. **Triage** each comment against 5 validity criteria
3. **Present** triage summary to user for approval
4. **Fix** valid comments in parallel (subagents by category)
5. **Commit...

### Prompt 9

you didnt clear the conflicts

### Prompt 10

actions failing

