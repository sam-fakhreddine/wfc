# Session Context

## User Prompts

### Prompt 1

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-housekeeping

# WFC:HOUSEKEEPING - Project Hygiene & Cleanup

**Keep the codebase World Fucking Class.** Systematic cleanup with safety guardrails.

## What It Does

1. **Scan** - Analyze the codebase for cleanup opportunities across 5 domains
2. **Report** - Present categorized findings with severity and safety ratings
3. **Approve** - User reviews and selects which cleanups to apply
4. **Execute** - Apply cleanups in paral...

### Prompt 2

create a feature branch and push it up

### Prompt 3

[Request interrupted by user]

### Prompt 4

creat a chore branch and push it up

### Prompt 5

why do test files have imports in the functions

### Prompt 6

ok cool! good answer

### Prompt 7

is this PR still needing to be merged? https://github.com/sam-fakhreddine/wfc/pull/15

### Prompt 8

yep

### Prompt 9

rework the readme it is no longer uptodate.

### Prompt 10

commit and push up

### Prompt 11

Base directory for this skill: /Users/samfakhreddine/.claude/skills/wfc-pr-comments

# WFC:PR-COMMENTS - Intelligent PR Comment Triage & Fix

**Fetch, triage, fix.** Automates addressing PR review comments from humans, Copilot, CodeRabbit, and other reviewers.

## What It Does

1. **Fetch** all PR comments via `gh` CLI
2. **Triage** each comment against 5 validity criteria
3. **Present** triage summary to user for approval
4. **Fix** valid comments in parallel (subagents by category)
5. **Commit...

### Prompt 12

please resolve all comments that are dealt with

### Prompt 13

write a helper script so we dont have to through this all the time and make it part of the PR comment workflow, once done, comment on the PR comment with what you did and then resolve. https://docs.github.com/en/graphql/reference/mutations#resolvereviewthread

### Prompt 14

failing checks

    CI / Lint & Format Check (pull_request)
    CI / Lint & Format Check (pull_request)Failing after 10s
    Quick Check / Fast Validation (pull_request)
    Quick Check / Fast Validation (pull_request)Failing after 10s
    Required
    Validate WFC Skills / Run Tests (pull_request)
    Validate WFC Skills / Run Tests (pull_request)Failing after 20s
    Required

### Prompt 15

2. and a skill to help troublershoot failing gh actions

