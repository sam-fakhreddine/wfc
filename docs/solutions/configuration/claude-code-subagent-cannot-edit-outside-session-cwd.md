---
title: Claude Code Subagents Cannot Edit Files Outside Their Session CWD
component: wfc-implement / agent orchestration
tags: claude-code, subagent, worktree, file-editing, orchestration, permissions
category: configuration
date: 2026-03-02
severity: high
status: resolved
root_cause: Claude Code spawned subagents run in an isolated session context and cannot use Edit/Write tools on paths outside their working directory, regardless of the `mode` parameter passed to the Agent tool.
---

## Problem

**Symptoms:**

- Subagent receives `Edit` tool call denied error
- Occurs consistently regardless of `mode`: `default`, `acceptEdits`, `bypassPermissions` all fail identically
- Orchestrator spawns agents with correct file paths (e.g. `.worktrees/TASK-001/src/foo.py`) but agents cannot write to them
- No error message distinguishes this from a permissions policy denial — both surface as "Edit tool denied"

**Environment:** Claude Code CLI, multi-agent orchestration via `Agent` tool with `subagent_type: "general-purpose"`, files located in git worktrees under `.worktrees/`

## Root Cause

Claude Code subagents spawned via the `Agent` tool run in a **separate session context**. Each subagent session has its own working directory scope. File editing tools (`Edit`, `Write`, `NotebookEdit`) are constrained to paths within or beneath that session's working directory.

The `mode` parameter (`acceptEdits`, `bypassPermissions`) controls **permission prompting** — whether the user is asked to approve tool calls. It does **not** expand the set of file paths the agent can access. A subagent spawned at session root `/Users/x/project` cannot edit `/Users/x/project/.worktrees/branch-a/src/foo.py` because `.worktrees/branch-a/` resolves to a different git worktree context, not because of a permission policy.

This means the standard `wfc-implement` pattern — orchestrator creates worktrees, spawns one agent per worktree, agent edits files in its worktree — **does not work** in Claude Code's current execution model.

## Solution

```
# Before (broken pattern)
Agent tool → spawn subagent with worktree path
  → subagent calls Edit on .worktrees/TASK-001/src/file.py
  → DENIED (3 rounds, 3 modes, same result)

# After (working pattern)
Orchestrator directly applies all edits in the main session
  → Read file at .worktrees/TASK-001/src/file.py
  → Edit file at .worktrees/TASK-001/src/file.py
  → Commit from within the worktree using Bash
```

**Concretely:** replace agent spawning with direct orchestrator execution. Worktrees still provide branch isolation — commits go to the right branch — but the editing happens in the main session, not delegated subagents.

```bash
# Still valid: create worktrees for branch isolation
git worktree add .worktrees/TASK-001 -b claude/TASK-001 develop

# Work directly from main session
# Read/Edit .worktrees/TASK-001/wfc/skills/wfc-implement/SKILL.md
# Then commit from within the worktree:
cd .worktrees/TASK-001 && git add <file> && git commit -m "..."
```

## Prevention

- **Design rule:** Never design an orchestration flow where subagents need to edit files in git worktrees. If you need worktree isolation, use it for branch/commit isolation only — do editing in the main session.
- **Canary test:** Before a large multi-worktree implementation run, spawn one test agent and have it attempt a trivial Edit on the worktree path. Fail fast before creating N worktrees.
- **Skill update:** `wfc-implement` SKILL.md should document this limitation explicitly in its `## Limitations` section so future orchestrators don't re-learn it. (Done: TASK-001/002 in this plan added the HARD STOP block; a follow-up task should add this to Limitations.)
- **Alternative pattern for true parallelism:** Use the `isolation: "worktree"` parameter on the Agent tool itself — this creates a worktree *as the agent's working directory* and **fully resolves the path scope issue (confirmed 2026-03-02)**. The agent's CWD is set to its own worktree copy of the repo; Write, Edit, and Read all work normally. The worktree path and branch are returned in the result for follow-up commits. This is the correct pattern for true parallel agent execution.

## Related

- [LLM Orchestrator Stage Ordering, Threading, and Retry](../logic-errors/llm-orchestrator-stage-ordering-threading-retry.md)
