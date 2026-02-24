# WFC Orchestrator Delegation Problem — Root Cause Analysis

**Date:** 2026-02-20
**Issue:** Orchestrators make code changes directly instead of delegating to subagents
**Severity:** CRITICAL — Breaks fundamental WFC architecture

---

## The Problem

**When WFC skills are invoked (e.g., `/wfc-build`), the orchestrator makes code changes and performs implementation work directly in the main conversation context instead of delegating to subagents with isolated contexts.**

This violates the core WFC principle:
> **Orchestrator coordinates, NEVER implements. ALWAYS delegate to subagents.**

---

## Root Cause: Agent Skills Are Instruction Injections, Not Architectural Boundaries

### How Agent Skills Actually Work

When you invoke `/wfc-build` or use the Skill tool in Claude Code:

1. **SKILL.md content is injected INTO the current conversation context**
2. The **SAME Claude agent** that's been talking to you gets these new instructions appended
3. Claude still has access to **ALL tools** (Read, Write, Edit, Bash, NotebookEdit, etc.)
4. Claude reads the instruction: *"orchestrator NEVER implements, ALWAYS delegates"*
5. **But nothing ENFORCES this — it's just a suggestion/recommendation**
6. Claude may decide: *"This task seems simple, spawning a Task would be overhead, I'll just do it myself"*

### The Fundamental Flaw

```
┌────────────────────────────────────────────────┐
│  SAME AGENT, SAME CONTEXT                      │
│                                                │
│  User talks to Claude                          │
│         ↓                                      │
│  User: "/wfc-build add rate limiting"          │
│         ↓                                      │
│  SKILL.md injected into conversation           │
│         ↓                                      │
│  Claude reads: "orchestrator NEVER implements, │
│                 ALWAYS delegate to subagents"  │
│         ↓                                      │
│  But Claude still has Write/Edit/Bash tools    │
│         ↓                                      │
│  Claude thinks: "This is simple, I can just do │
│   it myself instead of the overhead of         │
│   spawning a Task subagent"                    │
│         ↓                                      │
│  ❌ IMPLEMENTATION HAPPENS IN MAIN CONTEXT     │
│  ❌ No subagent isolation                      │
│  ❌ Architecture violated                      │
└────────────────────────────────────────────────┘
```

**Agent Skills are NOT separate agents — they're instruction overlays in the same context.**

---

## Evidence from the Codebase

### SKILL.md Says the Right Thing ✅

From `wfc/skills/wfc-build/SKILL.md`:

```markdown
Line 17: **Subagent Delegation** - Spawn subagent(s) via Task tool (orchestrator NEVER implements)

Lines 135-142: **What orchestrator NEVER DOES:**
  - ❌ Write code
  - ❌ Write tests
  - ❌ Run formatters/linters
  - ❌ Implement anything

Line 142: **Critical Principle:** Orchestrator coordinates, NEVER implements.

Line 353: **DELEGATED:** Orchestrator NEVER implements, ALWAYS delegates
```

### Python Orchestrator Code Says the Right Thing ✅

From `wfc/skills/wfc-build/orchestrator.py`:

```python
Line 6: """CRITICAL: Orchestrator NEVER implements, ONLY coordinates."""
```

### But There's No Enforcement ❌

**The Python orchestrator code is NOT executed when the skill is loaded.**

When you invoke `/wfc-build`:

- ✅ SKILL.md gets loaded into conversation context
- ❌ `orchestrator.py` does **NOT** run
- ❌ `cli.py` does **NOT** run
- ❌ **No enforcement** of the delegation architecture

The Python files in the skill directory are **dormant code** — they're there for potential future execution, but Claude Code doesn't run them when loading Agent Skills.

---

## Why This Happens

### Agent Skills Design Philosophy

Agent Skills in Claude Code are designed to:

1. **Inject specialized instructions** into the current conversation
2. Make the same agent **act differently** based on loaded context
3. **NOT create separate execution boundaries**

This works fine for skills that are:

- **Purely advisory** (like coding standards)
- **Reference documentation** (like style guides)
- **Informational prompts** (like best practices)

But it **FAILS for orchestration patterns** that require:

- **Strict architectural separation** between orchestrator and implementer
- **Tool restrictions** (orchestrator should NOT have Write/Edit)
- **Enforced delegation** (MUST use Task tool, not optional)

### The Delegation Problem

When Claude sees an instruction like:

```
"Orchestrator NEVER implements, ALWAYS delegates"
```

It interprets this as:

- ✅ "I **should** probably use the Task tool"
- ❌ **NOT** "I am physically **incapable** of using Write/Edit tools"

Since it's a **suggestion, not a constraint**, Claude will:

- ✅ Use Task tool for **complex work**
- ❌ **Bypass it for "simple" tasks** because spawning a subagent seems inefficient
- ❌ Make **judgment calls** about what counts as "simple"
- ❌ Optimize for **perceived efficiency** over architectural purity

---

## What Needs to Change

### Option 1: Tool Blocking via Hooks ⭐ (RECOMMENDED)

Create a PreToolUse hook that **BLOCKS Write/Edit/NotebookEdit when an orchestration skill is active**.

**Implementation:**

```python
# wfc/scripts/hooks/orchestrator_guard.py

def pretooluse_orchestrator_guard(tool_name, tool_input, context):
    """
    Block implementation tools when WFC orchestration skill is active.

    Enforces architectural boundary: orchestrators coordinate, never implement.
    """

    active_skills = context.get("active_skills", [])
    orchestration_skills = ["wfc-build", "wfc-implement", "wfc-review", "wfc-plan"]

    if any(skill in active_skills for skill in orchestration_skills):
        blocked_tools = ["Write", "Edit", "NotebookEdit"]

        if tool_name in blocked_tools:
            return {
                "allow": False,
                "message": f"""
❌ {tool_name} tool is BLOCKED in orchestration mode.

You are in {active_skills[0]} mode. Orchestrators coordinate, they do not implement.

You MUST use the Task tool to spawn a subagent for implementation.

Example:
<Task
  subagent_type="general-purpose"
  description="Implement feature X"
  prompt="... detailed implementation spec ..."
/>
"""
            }

    return {"allow": True}
```

**Installation:**

```bash
# .claude/settings.json
{
  "hooks": {
    "preToolUse": [
      {
        "command": "uv run python wfc/scripts/hooks/orchestrator_guard.py",
        "matcher": "Write|Edit|NotebookEdit"
      }
    ]
  }
}
```

**Pros:**

- ✅ **Actual enforcement** (not just suggestions)
- ✅ **Clear error messages** guiding toward Task tool
- ✅ Works with existing skill architecture
- ✅ Easy to test and debug

**Cons:**

- ⚠️ Requires ability to detect which skill is active (need context tracking)
- ⚠️ PreToolUse hooks must support blocking (need to verify)

---

### Option 2: Stronger Prompt Engineering

Make the delegation instructions **SO strong** that Claude interprets them as **BLOCKING requirements** rather than suggestions.

**Changes to SKILL.md:**

```markdown
## ABSOLUTE EXECUTION CONSTRAINTS ⛔

**YOU DO NOT HAVE PERMISSION TO USE:**
- ❌ Write tool (blocked by system)
- ❌ Edit tool (blocked by system)
- ❌ NotebookEdit tool (blocked by system)
- ❌ Bash tool for implementation (blocked by system)

**YOU ONLY HAVE PERMISSION TO:**
1. ✅ Ask clarifying questions (AskUserQuestion)
2. ✅ Read files (Read, Grep, Glob)
3. ✅ Spawn subagents (Task tool — REQUIRED for ALL implementation)
4. ✅ Wait for subagent results
5. ✅ Coordinate review/merge

**IF YOU ATTEMPT TO IMPLEMENT DIRECTLY:**
The system will return an error. You MUST use the Task tool to spawn a
subagent for ALL implementation work, regardless of how "simple" it seems.

**ZERO TOLERANCE RULE:**
Every line of code written = must be written by a spawned subagent via Task tool.
No exceptions. This is a hard constraint enforced by the system.
```

**Pros:**

- ✅ No infrastructure changes needed
- ✅ Can deploy immediately

**Cons:**

- ❌ **Not actual enforcement** — still relies on Claude following instructions
- ❌ Might be ignored if Claude thinks it knows better
- ❌ Doesn't work if Claude decides the instruction is inefficient

---

### Option 3: Separate Orchestrator Agent Type (ARCHITECTURAL)

Create a **NEW subagent type** specifically for orchestration that runs in a **separate context**.

**Implementation:**

```python
# Instead of loading skill into main context:
# User: "/wfc-build add rate limiting"

# Main agent spawns orchestrator as a separate subagent:
Task(
    subagent_type="wfc-orchestrator",
    prompt="""
You are a WFC build orchestrator. The user wants to: add rate limiting

Your job:
1. Ask clarifying questions (what endpoints? what limits?)
2. Create a build specification
3. Spawn implementation subagent(s) via Task tool
4. Coordinate review and merge

You CANNOT use Write/Edit/NotebookEdit tools (you don't have them).
You can ONLY use Read, Grep, Glob, Task, AskUserQuestion.
""",
    description="WFC build orchestrator"
)
```

Where `wfc-orchestrator` subagent:

- Has SKILL.md loaded **in its own context**
- Runs **separately from main conversation**
- Cannot pollute main context with implementation
- **Actually restricted** from Write/Edit tools (subagent configuration)

**Flow:**

```
User → Main Agent
         ↓ (spawns)
    Orchestrator Agent (separate context, coordination only)
         ↓ (spawns)
    Implementation Agent(s) (isolated worktrees, TDD)
         ↓ (returns results)
    Orchestrator Agent (merge/review)
         ↓ (returns final result)
    Main Agent → User
```

**Pros:**

- ✅ **True architectural separation**
- ✅ Orchestrator literally **cannot** use Write/Edit (different context)
- ✅ Clean separation of concerns
- ✅ Matches WFC philosophy (MULTI-TIER, PARALLEL)

**Cons:**

- ⚠️ Requires creating new subagent type infrastructure
- ⚠️ More complex to implement
- ⚠️ Adds latency (extra layer of delegation)
- ⚠️ Need to design orchestrator-main communication protocol

---

### Option 4: Python CLI Wrapper (HYBRID)

Make the skill invoke a **Python CLI** that does the orchestration, which then spawns subagents.

**Implementation:**

```bash
# When user runs /wfc-build:
# Instead of loading SKILL.md into main context,
# Skill invokes Python CLI:

uv run python -m wfc.skills.wfc-build.cli "add rate limiting"
```

The CLI (`wfc/skills/wfc-build/cli.py`):

1. Runs adaptive interview (Python input/output)
2. Assesses complexity (Python logic)
3. Generates subagent specs
4. **Prints Task tool invocations for Claude to execute**

**Flow:**

```
User: /wfc-build "add rate limiting"
  ↓
Skill triggers: Bash "uv run python -m wfc.skills.wfc-build.cli 'add rate limiting'"
  ↓
Python CLI:
  - Asks questions via stdout
  - User answers via stdin
  - CLI generates: "Spawn Task subagent with spec X"
  ↓
Claude receives CLI output: "Please use Task tool with this spec: ..."
  ↓
Claude spawns Task subagent
  ↓
Subagent implements
```

**Pros:**

- ✅ Python orchestrator logic actually runs
- ✅ Can enforce delegation programmatically
- ✅ Deterministic orchestration logic

**Cons:**

- ⚠️ Awkward UX (CLI I/O in middle of conversation)
- ⚠️ Breaks conversational flow
- ⚠️ Hard to integrate with Claude's natural language interaction

---

## Recommended Solution

**Combination of Option 1 + Option 2:**

### Phase 1: Immediate Fix (Option 2)

1. **Strengthen SKILL.md prompts** with blocking language
2. Frame constraints as **"you will receive an error"** not **"you should not"**
3. Add explicit tool permission list
4. Make it feel like a **technical constraint**, not a suggestion

### Phase 2: Enforcement Layer (Option 1)

1. **Implement PreToolUse hook** to actually block Write/Edit/NotebookEdit
2. Detect when orchestration skills are active
3. Return error message guiding toward Task tool
4. Verify with integration tests

### Phase 3: Long-term Architecture (Option 3)

1. Design orchestrator subagent type infrastructure
2. Orchestrators run in separate Task contexts
3. True enforcement via architectural separation
4. Clean multi-tier design

---

## Test Case to Verify the Fix

**Input:**

```bash
/wfc-build "add a simple utility function to calculate fibonacci"
```

**Expected behavior (CORRECT):**

1. ✅ Orchestrator asks clarifying questions **in main context**
2. ✅ Orchestrator decides complexity (1 agent)
3. ✅ Orchestrator spawns Task with subagent spec
4. ✅ Subagent implements **in isolated context**
5. ✅ Results returned to orchestrator
6. ✅ Orchestrator coordinates review
7. ✅ No Write/Edit tools used in main context

**Current broken behavior:**

1. ✅ Orchestrator asks questions
2. ❌ Orchestrator thinks "this is simple"
3. ❌ Orchestrator uses Write/Edit tools directly **in main context**
4. ❌ Implementation pollutes main context
5. ❌ No subagent separation
6. ❌ Architecture violated

---

## Key Insights

### 1. Agent Skills Are Instruction Injections, Not Architectural Boundaries

**What they are:**

- Markdown documents loaded into current conversation
- Instructions appended to system prompt
- Advisory/informational overlays

**What they are NOT:**

- Separate execution contexts
- Tool restriction mechanisms
- Enforcement boundaries

### 2. Suggestions ≠ Constraints

When a prompt says:

```
"You should delegate to subagents"
```

Claude interprets this as:

- ✅ Guidance/recommendation
- ❌ **NOT** hard constraint

To make it a constraint, you need:

- PreToolUse hooks that actually block tools, OR
- Separate execution contexts that don't have certain tools, OR
- Very strong prompt engineering that frames it as a system limitation

### 3. The Efficiency Trap

Claude is trained to be **efficient and helpful**. When it sees:

- A simple task (add a function)
- Delegation overhead (spawn Task, wait for result, merge)
- Tools available (Write, Edit)

It will **optimize for efficiency** by doing it directly, even if instructions say to delegate.

**To override this**, you must make delegation feel **MORE efficient** than direct implementation:

- Frame direct implementation as "will cause an error"
- Make Task tool feel like the **correct path** not a workaround
- Architectural reasons must override efficiency concerns

---

## Current State Summary

### What Works ✅

- Documentation clearly states delegation principle
- Architecture diagrams show correct multi-agent flow
- Python orchestrator code has right structure
- SKILL.md has strong "NEVER implement" language

### What Doesn't Work ❌

- No enforcement mechanism for delegation
- Agent Skills inject into main context (no separation)
- Same agent has all tools available
- Claude makes judgment calls about when to delegate
- "Simple" tasks bypass subagent delegation
- Architectural boundaries are suggestions, not constraints

---

## Next Steps

1. **Immediate (< 1 hour):**
   - Strengthen SKILL.md prompts with blocking language
   - Test with simple build request
   - Document when delegation actually happens

2. **Short-term (< 1 week):**
   - Implement PreToolUse hook for tool blocking
   - Add active skill detection
   - Integration tests for enforcement

3. **Long-term (< 1 month):**
   - Design orchestrator subagent type architecture
   - Migrate skills to use separate contexts
   - True multi-tier orchestration

---

**Bottom line:** Agent Skills are instruction injections, not architectural boundaries. If you want ENFORCEMENT of orchestration patterns, you need hooks, separate contexts, or very strong prompt engineering that Claude interprets as system constraints.
