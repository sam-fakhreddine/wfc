---
name: wfc-build
description: |
  Triggers when a user requests NEW feature implementation with INTENTIONAL AMBIGUITY
  or EXPLICIT DELEGATION of technical decisions.
  
  Use when the user wants the agent to "figure it out," "make the call," or 
  "just build it" without providing implementation specifics.
  
  Workflow: Clarifying Interview (define spec) → Codebase Context → TDD Implementation → PR Creation.
  
  Canonical triggers:
  - "Just build [X], you decide the approach"
  - "Create [Y], figure out the details"
  - "Make me a [Z], use your judgment on stack/pattern"
  - "Build a prototype for [feature]"
  - "I need [X], design and implement it"
  
  NOT FOR:
  - Requests with complete specifications (5+ constraints, schema, or API contracts provided)
  - Trivial single-file changes (adding a button, single function, typo fix)
  - Pure refactoring without new functionality
  - Bug fixes or debugging (use debugging skills)
  - Architecture planning with explicit no-implementation instruction
  - Projects requiring 4+ independent parallel workstreams (use wfc-plan)
license: MIT
---

# WFC:BUILD - Intentional Vibe Coding

⚠️ **EXECUTION CONTEXT: ORCHESTRATION MODE**

You are running in **orchestration mode** with restricted tool access.

**Available tools:**

- ✅ Read, Grep, Glob (file inspection only)
- ✅ Task (REQUIRED for all implementation work)
- ✅ AskUserQuestion (clarification)
- ✅ Bash (git status, git worktree, git push, gh pr create, git branch)

**NOT available in this context:**

- ❌ Write (use Task → spawn implementation subagent)
- ❌ Edit (use Task → spawn implementation subagent)
- ❌ NotebookEdit (use Task → spawn implementation subagent)

**Critical constraint:** Every line of code written MUST be written by a subagent spawned via Task tool. No exceptions.

---

## Workflow Overview

1. **Preflight Check** - Validate request matches skill scope
2. **Adaptive Interview** - 3-5 clarifying questions based on complexity
3. **Codebase Context** - Read project structure and identify affected files
4. **Complexity Assessment** - Determine: 1 agent or multi-agent
5. **Worktree Setup** - Create isolated worktree for implementation
6. **Subagent Delegation** - Spawn subagent(s) via Task tool
7. **Quality Gates** - Verify tests, linters, formatters pass
8. **PR Creation** - Push branch and create GitHub PR
9. **Review Handoff** - Output instructions for wfc-review

---

## Preflight Check

Before starting the interview, validate the request:

IF request contains 5+ specific constraints OR detailed API spec OR database schema:
  → STOP. Suggest: "This appears to be a complete specification.
     Use standard coding workflow or /wfc-implement if available."
  
IF request is single-file modification OR trivial addition:
  → STOP. Suggest: "This is a single-file change. Use direct coding
     for faster results."

IF request is bug fix OR debugging:
  → STOP. Suggest: "Use debugging skills for bug fixes."

IF request explicitly says "plan only" or "don't implement":
  → STOP. Suggest: "Use /wfc-plan for planning-only requests."

IF request would require 4+ independent parallel workstreams:
  → STOP. Suggest: "This requires wfc-plan for complex multi-stream orchestration."

OTHERWISE:
  → Proceed with Adaptive Interview

```

---

## Adaptive Interview

Ask questions based on request complexity:

### Minimum Questions (3) - Simple Requests
```

Q1: What are you building? (one sentence goal)
Q2: Which area of the codebase does this touch? (directory or module)
Q3: What does success look like? (acceptance criteria)

```

### Extended Questions (+2) - Complex Requests
```

Q4: Any existing patterns in this codebase I should follow?
Q5: What should happen on error/edge cases?

```

### Question Count Decision
- User provides clear goal + location: 3 questions
- User provides goal only, location unclear: 4 questions  
- User provides vague goal, complex domain: 5 questions

---

## Codebase Context Phase

**Required before spawning subagents:**

```bash
# Discover project structure
find . -type f -name "*.py" -o -name "*.ts" -o -name "*.js" | head -50

# Identify relevant files
grep -r "[keyword from request]" --include="*.py" --include="*.ts" -l

# Check for existing patterns
ls -la [related directories]
```

**Output:** List of specific files to modify/create before proceeding to complexity assessment.

---

## Complexity Assessment

**Simple Task (1 Subagent):**

- Touches single top-level directory
- OR single component type (API only, UI only, scripts only)
- OR follows existing pattern exactly

**Complex Task (2-3 Subagents):**

- Touches 2-3 top-level directories
- OR requires backend + frontend coordination
- OR involves auth/data layer changes
- OR introduces new dependency

**Out of Scope (>3 workstreams):**

- Touches 4+ independent components
- Requires database migration + API + UI + tests + documentation
- → Route to wfc-plan instead

### Complexity Heuristic

```
IF files_to_modify in single_directory AND no_new_dependencies:
  → SIMPLE: 1 subagent
  
IF files_to_modify in 2-3 directories OR new_dependency OR auth_related:
  → COMPLEX: 2-3 subagents (parallel)

IF files_to_modify in 4+ directories OR multi_day_effort:
  → OUT OF SCOPE: Route to wfc-plan
```

---

## Worktree Setup

Before spawning subagent, create isolated worktree:

```bash
# Create feature branch
git checkout -b claude/[feature-name-kebab-case]

# Create worktree for subagent
git worktree add .worktrees/[feature-name] -b worktree/[feature-name]
```

**Branch Naming Convention:**

- `claude/*` branches: Auto-merge to develop when CI passes
- `feat/*` branches: Require manual human review

---

## Spawn Implementation Subagent

Use this template AFTER codebase context phase:

```xml
<Task
  subagent_type="general-purpose"
  description="Implement [feature name]"
  prompt="
You are implementing: [detailed feature description from interview]

Working directory: .worktrees/[feature-name]

Files to create/modify (discovered from codebase):
- [specific file 1]
- [specific file 2]

User context from interview:
- Goal: [Q1 answer]
- Location: [Q2 answer]
- Success criteria: [Q3 answer]
- [Additional context if provided]

Requirements:
- [requirement 1 from interview]
- [requirement 2 from interview]

Follow TDD workflow:
1. Write tests FIRST (RED phase)
2. Implement minimum code to pass tests (GREEN phase)
3. Refactor while keeping tests passing (REFACTOR phase)
4. Run quality checks (formatters, linters, tests)

Available quality tools:
- Python: black, ruff, pytest
- JavaScript/TypeScript: prettier, eslint, jest/npm test
- Check pyproject.toml or package.json for project-specific config

Deliverables (output as structured report):
## Implementation Report
### Files Created: [list]
### Files Modified: [list]
### Tests Written: [list]
### Tests Status: [pass/fail count]
### Quality Checks: [formatter/linter status]
### Summary: [2-3 sentence implementation summary]
"
/>
```

---

## Post-Subagent Workflow

### 1. Collect Reports

Wait for all spawned subagents to complete. Timeout: 10 minutes per subagent.

### 2. Verify Quality

```bash
# In worktree
cd .worktrees/[feature-name]
pytest  # or appropriate test command
black --check .  # or prettier --check
ruff check .  # or eslint
```

### 3. Create PR

```bash
# Push branch
git push -u origin claude/[feature-name]

# Create PR
gh pr create --base develop --title "[Feature Name]" --body "[PR body]"
```

### 4. PR Body Template

```markdown
## Summary
[From subagent report summary]

## Changes
### Files Created
[From subagent report]

### Files Modified
[From subagent report]

## Testing
- Tests written: [count]
- All tests passing: [yes/no]

## Post-Deploy Validation

### Health Checks
- [ ] [Specific functionality to verify]
- [ ] [Edge case to test]

### Failure Indicators
- [Specific error to watch for]
- [Metric threshold if known]

### Rollback Trigger
If [specific condition], rollback this PR.

---
Generated by wfc-build
```

### 5. Review Handoff

Output to user:

```
✅ Implementation complete. PR created: [PR URL]

Next step: Run code review
/wfc-review --pr [PR number]
```

---

## Quality Tool Discovery

Before running quality checks, discover project configuration:

```bash
# Python projects
ls pyproject.toml setup.cfg .flake8

# JavaScript/TypeScript projects  
ls package.json .eslintrc .prettierrc

# Run discovered tools
if [ -f pyproject.toml ]; then
  black . && ruff check . && pytest
fi

if [ -f package.json ]; then
  npm run lint && npm test
fi
```

---

## Configuration

```json
{
  "build": {
    "interview_questions_min": 3,
    "interview_questions_max": 5,
    "subagent_timeout_minutes": 10,
    "max_agents": 3,
    "enforce_tdd": true,
    "require_quality_check": true,
    "branch_prefix": "claude/",
    "target_branch": "develop"
  }
}
```

---

## Git Workflow Policy

**What WFC-Build does:**

- Creates `claude/[feature-name]` branch
- Creates isolated worktree at `.worktrees/[feature-name]`
- Pushes branch to remote
- Creates GitHub PR targeting `develop`
- Outputs review handoff instructions

**What WFC-Build never does:**

- Push directly to `main`/`master`
- Force push
- Merge PRs (requires human or separate automation)
- Create branches in `feat/*` namespace (reserved for human developers)

**Branch existence check:**

```bash
# Verify develop branch exists
git branch -r | grep develop || echo "WARNING: develop branch not found, will target main"
```

---

## When to Use

### Use wfc-build when

- ✅ New feature with unclear implementation details
- ✅ User explicitly delegates technical decisions
- ✅ "Just build it" / "figure it out" intent clear
- ✅ Scope is discoverable (1-3 workstreams)

### Use wfc-plan + wfc-implement when

- ✅ Large feature with 4+ parallel tasks
- ✅ Complex dependencies between components
- ✅ Multi-day effort
- ✅ Need formal architecture documentation

### Use direct coding when

- ✅ Complete specification provided
- ✅ Single-file modification
- ✅ Trivial change (typo, rename, config tweak)

---

## Example Session

```
User: /wfc-build "add rate limiting to API"

[PREFLIGHT CHECK: Rate limiting is new feature, no complete spec → PROCEED]

Orchestrator:
  Q1: What's the main goal?
  A: Prevent API abuse, 100 requests/minute per user

  Q2: Which endpoints need protection?
  A: All /api/* endpoints

  Q3: What should happen when limit is exceeded?
  A: Return 429 Too Many Requests with retry header

  Q4: Any existing rate limiting patterns in codebase?
  A: No, this is new

[CODEBASE CONTEXT PHASE]
  → Found: src/api/middleware/
  → Found: src/config/settings.py
  → Need to create: src/api/middleware/rate_limit.py

[COMPLEXITY ASSESSMENT]
  → Single directory (src/api/)
  → New dependency (Redis for distributed rate limiting)
  → COMPLEX: 2 subagents

[WORKTREE SETUP]
  → Branch: claude/rate-limiting
