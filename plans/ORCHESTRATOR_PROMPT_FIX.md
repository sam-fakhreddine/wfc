# Orchestrator Delegation Fix — Simple Prompt Strengthening

**Status:** READY TO IMPLEMENT
**Effort:** 20-30 minutes
**Risk:** MINIMAL (trivial rollback via git revert)
**Test:** `/wfc-build "add fibonacci function"` → verify Task spawned

---

## Problem

Orchestrators MAY implement directly instead of delegating to subagents because:

1. Delegation instruction buried at line 135+ of SKILL.md (gets skipped)
2. Framed as "you should delegate" (suggestion, not constraint)
3. No immediate Task template (delegation feels harder than direct implementation)

## Solution

**Front-load execution constraints** to make delegation feel like a technical limitation, not a behavioral suggestion.

### Changes (4 files)

1. `wfc/skills/wfc-build/SKILL.md`
2. `wfc/skills/wfc-implement/SKILL.md`
3. `wfc/skills/wfc-review/SKILL.md`
4. `wfc/skills/wfc-plan/SKILL.md`

### Template

Replace current top section with:

```markdown
---
name: wfc-{skill}
description: [keep existing]
license: MIT
---

# WFC:{SKILL} - {Title}

⚠️ **EXECUTION CONTEXT: ORCHESTRATION MODE**

You are running in **orchestration mode** with restricted tool access.

**Available tools:**
- ✅ Read, Grep, Glob (inspection only)
- ✅ Task (REQUIRED for all implementation/analysis)
- ✅ AskUserQuestion (clarification)
- ✅ Bash (coordination commands only: git status, worktree list)

**NOT available in this context:**
- ❌ Write (use Task → implementation subagent)
- ❌ Edit (use Task → implementation subagent)
- ❌ NotebookEdit (use Task → implementation subagent)

**Critical constraint:** Every line of code written must be written by a subagent spawned via Task tool. No exceptions.

---

## Quick Start Template

Use this template to spawn implementation subagents:

\`\`\`xml
<Task
  subagent_type="general-purpose"
  description="[5-word summary]"
  prompt="
You are implementing: [feature description]

Files to modify:
- [list files]

Requirements:
- [requirement 1]
- [requirement 2]

Follow TDD:
1. Write tests first (RED)
2. Implement minimum code to pass (GREEN)
3. Refactor (REFACTOR)
4. Run formatters/linters

Deliverables:
- Implementation code
- Tests (passing)
- Quality checks (passing)
"
/>
\`\`\`

---

[REST OF EXISTING SKILL.MD CONTENT]
```

---

## Implementation Steps

### Step 1: Update wfc-build (5 min)

```bash
# Open file
code wfc/skills/wfc-build/SKILL.md

# Replace lines 1-35 with template above
# Keep rest of file unchanged (line 36+)
```

**Key changes:**

- Line 1-10: Execution context warning (NEW)
- Line 12-20: Tool availability list (NEW)
- Line 22-45: Quick start Task template (NEW)
- Line 47+: Existing content (UNCHANGED)

### Step 2: Update wfc-implement (5 min)

```bash
code wfc/skills/wfc-implement/SKILL.md

# Same template, adjust for wfc-implement specifics
# - Title: "Multi-Agent Parallel Implementation"
# - Context: Orchestrates N agents in worktrees
```

### Step 3: Update wfc-review (5 min)

```bash
code wfc/skills/wfc-review/SKILL.md

# Same template, adjust for wfc-review specifics
# - Title: "Five-Agent Consensus Review"
# - Context: Routes to 5 specialist reviewers
# - Task template: spawn reviewer subagents
```

### Step 4: Update wfc-plan (5 min)

```bash
code wfc/skills/wfc-plan/SKILL.md

# Same template, adjust for wfc-plan specifics
# - Title: "Adaptive Planning System"
# - Context: Conducts interview, generates TASKS.md
# - Note: wfc-plan does less delegation (mostly coordination)
```

### Step 5: Test (10 min)

**Test each skill:**

```bash
# Test 1: wfc-build
# Expected: Asks questions, then spawns Task (not Write/Edit)
/wfc-build "add a utility function to calculate fibonacci sequence"

# Verify:
# ✅ Orchestrator asks clarifying questions
# ✅ Orchestrator uses Task tool to spawn subagent
# ❌ Orchestrator does NOT use Write/Edit directly

# Test 2: wfc-implement
/wfc-implement --tasks plan/TASKS.md

# Verify:
# ✅ Reads TASKS.md
# ✅ Spawns Task for each task
# ❌ Does NOT implement in main context

# Test 3: wfc-review (if we have code to review)
/wfc-review

# Verify:
# ✅ Spawns Task for each reviewer
# ❌ Does NOT analyze code in main context
```

**Success criteria:**

- 100% of orchestrations spawn Task subagent
- 0% use Write/Edit in main context
- Clear error if constraint violated (though no enforcement yet)

---

## Why This Works

### 1. Front-Loading (Lines 1-10)

**Before:** Constraint buried at line 135
**After:** Constraint at line 1

**Psychological impact:** Impossible to miss, sets expectation immediately

### 2. Technical Framing (Lines 12-20)

**Before:** "You should not use Write/Edit"
**After:** "NOT available in this context"

**Psychological impact:** Feels like a system limitation, not a suggestion

### 3. Template Provision (Lines 22-45)

**Before:** No guidance on how to delegate
**After:** Copy-paste Task template ready to fill in

**Psychological impact:** Task tool becomes path of least resistance (easier than thinking about it)

### 4. Explicit Permission List

**Before:** Vague "delegate to subagents"
**After:** Specific tool availability list

**Psychological impact:** Clear boundaries, no ambiguity

---

## Rollback Plan

**If this doesn't work:**

```bash
# Instant rollback
git checkout HEAD -- wfc/skills/wfc-*/SKILL.md

# Or revert the commit
git revert <commit-hash>
```

**Time to rollback:** < 2 minutes

---

## What This Doesn't Do

**This is NOT enforcement.** It's stronger guidance.

**Limitations:**

- Claude can still ignore if it decides efficiency > instructions
- No technical prevention (tools still available)
- Relies on prompt following behavior

**If this fails:**

- Proceed to Phase 0: Verify hook context API (4-6h)
- Then potentially Phase 1: Implement hook (16-24h)
- OR accept constraint and use observability

---

## Validation Plan

**After implementation, monitor for 2 weeks:**

1. **Manual testing:** Run each skill 3-5 times, verify delegation
2. **Log analysis:** Check if Write/Edit ever used during skill sessions
3. **User feedback:** Do users report unexpected behavior?

**Decision point (2 weeks):**

- If 100% compliance → SUCCESS, done
- If 80-99% compliance → PARTIAL success, iterate prompt
- If <80% compliance → FAILED, proceed to hook enforcement

---

## Timeline

| Step | Time | Description |
|------|------|-------------|
| Update wfc-build | 5 min | Front-load constraint + template |
| Update wfc-implement | 5 min | Same pattern |
| Update wfc-review | 5 min | Same pattern |
| Update wfc-plan | 5 min | Same pattern |
| Test all 4 skills | 10 min | Verify delegation happens |
| **TOTAL** | **30 min** | Ready to commit |

**Monitoring period:** 2 weeks (passive observation)

---

## Success Metrics

**Immediate (during testing):**

- ✅ All 4 skills load without errors
- ✅ Task template appears in skill prompt
- ✅ Orchestrator uses Task tool (not Write/Edit)

**Medium-term (2 weeks):**

- ✅ Zero reports of orchestrators implementing directly
- ✅ User feedback: "delegation behavior is clear"
- ✅ Log analysis: No Write/Edit during orchestration sessions

**Long-term:**

- ✅ Pattern established for future orchestration skills
- ✅ Template reusable across WFC ecosystem

---

## Next Steps

1. **Implement** (30 min) — Update 4 SKILL.md files
2. **Test** (10 min) — Verify delegation in practice
3. **Commit** (5 min) — `feat(skills): front-load orchestration constraints`
4. **Monitor** (2 weeks) — Observe actual behavior
5. **Decide** (after 2 weeks) — Success, iterate, or escalate to hooks

**DO NOT proceed to hook implementation unless this fails.**

---

## Commit Message

```
feat(skills): front-load orchestration mode constraints

Problem:
- Delegation instructions buried at line 135+ (easily missed)
- Framed as suggestions ("you should") not constraints
- No immediate Task template (delegation felt hard)

Solution:
- Move execution context to lines 1-10 (impossible to miss)
- Frame as technical limitation ("NOT available")
- Provide copy-paste Task template (path of least resistance)

Changes:
- wfc-build/SKILL.md: Front-load constraint + template
- wfc-implement/SKILL.md: Front-load constraint + template
- wfc-review/SKILL.md: Front-load constraint + template
- wfc-plan/SKILL.md: Front-load constraint + template

Testing:
- Manual: All 4 skills verified to spawn Task (not Write/Edit)
- Next: Monitor for 2 weeks to validate effectiveness

Risk: MINIMAL (trivial rollback via git revert)
Effort: 30 minutes
Validation: 2 weeks observation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Appendix: Example Before/After

### Before (wfc-build/SKILL.md, lines 135-142)

```markdown
**What orchestrator NEVER DOES:**

- ❌ Write code
- ❌ Write tests
- ❌ Run formatters/linters
- ❌ Implement anything

**Critical Principle:** Orchestrator coordinates, NEVER implements.
```

**Problems:**

- Buried deep in file
- Passive voice ("never does")
- No template for alternative
- Easy to skip/miss

### After (wfc-build/SKILL.md, lines 1-45)

```markdown
---
name: wfc-build
description: [existing]
license: MIT
---

# WFC:BUILD - Intentional Vibe Coding

⚠️ **EXECUTION CONTEXT: ORCHESTRATION MODE**

You are running in orchestration mode with restricted tool access.

**Available tools:**
- ✅ Read, Grep, Glob (inspection only)
- ✅ Task (REQUIRED for all implementation)
- ✅ AskUserQuestion (clarification)

**NOT available in this context:**
- ❌ Write
- ❌ Edit
- ❌ NotebookEdit

Every line of code must be written by a Task subagent.

## Quick Start Template

\`\`\`xml
<Task subagent_type="general-purpose" description="..." prompt="..."/>
\`\`\`

---

[REST OF SKILL CONTENT]
```

**Improvements:**

- Lines 1-10: Immediate visibility
- Active constraint framing
- Explicit tool list
- Ready-to-use template

---

**READY TO IMPLEMENT. PROCEED?**
