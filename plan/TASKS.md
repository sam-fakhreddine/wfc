# WFC-BUILD IMPLEMENTATION TASKS

**PROJECT:** wfc-build - Streamlined Feature Builder
**GENERATED:** 2026-02-12
**COMPLEXITY:** MEDIUM (estimated 12-14 hours)

---

## DEPENDENCY GRAPH

```
TASK-001 (Setup)
    ↓
TASK-002 (Interview) ← TASK-003 (Complexity)
    ↓
TASK-004 (Orchestrator)
    ↓
TASK-005 (CLI)
    ↓
TASK-006 (Integration)
    ↓
TASK-007 (Tests)
    ↓
TASK-008 (Documentation)
```

---

## TASK-001: Setup skill structure

**COMPLEXITY:** S
**DEPENDENCIES:** []
**ESTIMATED TIME:** 30 minutes
**PROPERTIES:** []

**DESCRIPTION:**
Create Agent Skills compliant directory structure for wfc-build.

**FILES AFFECTED:**
- `~/.claude/skills/wfc-build/SKILL.md` (NEW)
- `wfc/scripts/skills/build/__init__.py` (NEW)
- `wfc/scripts/skills/build/interview.py` (NEW)
- `wfc/scripts/skills/build/complexity_assessor.py` (NEW)
- `wfc/scripts/skills/build/orchestrator.py` (NEW)

**ACCEPTANCE CRITERIA:**
- [ ] Directory structure matches Agent Skills standard
- [ ] SKILL.md has valid frontmatter (name, description, license)
- [ ] Package structure follows WFC conventions
- [ ] Imports work from wfc.shared

---

## TASK-002: Implement quick interview

**COMPLEXITY:** M
**DEPENDENCIES:** [TASK-001]
**ESTIMATED TIME:** 2 hours
**PROPERTIES:** [PROP-008]

**DESCRIPTION:**
Create streamlined interview that gathers enough context for complexity assessment and implementation in 3-5 questions.

**FILES AFFECTED:**
- `wfc/scripts/skills/build/interview.py` (MODIFY)

**ACCEPTANCE CRITERIA:**
- [ ] Max 5 questions asked
- [ ] Questions adapt based on previous answers
- [ ] Captures: feature description, scope, constraints, tech stack
- [ ] Returns structured InterviewResult dataclass
- [ ] Completes in <30 seconds (PROP-008)

**INTERVIEW FLOW:**
```
Q1: What feature do you want to build?
    → Parse: feature_description, domain clues

Q2: What's the scope? (single file / few files / many files / new module)
    → Parse: scope_size

Q3: [ADAPTIVE] Based on scope:
    - If "new module": What dependencies?
    - If "few files": Which files?
    - If "many files": What architectural pattern?

Q4: Any constraints? (performance / security / compatibility)
    → Parse: constraints

Q5: [OPTIONAL] Existing tests to update?
    → Parse: test_context
```

---

## TASK-003: Implement complexity assessor

**COMPLEXITY:** M
**DEPENDENCIES:** [TASK-001]
**ESTIMATED TIME:** 1.5 hours
**PROPERTIES:** [PROP-006]

**DESCRIPTION:**
Algorithm that analyzes interview responses and assigns complexity rating (S/M/L/XL) which determines agent count.

**FILES AFFECTED:**
- `wfc/scripts/skills/build/complexity_assessor.py` (MODIFY)

**ACCEPTANCE CRITERIA:**
- [ ] Takes InterviewResult as input
- [ ] Returns ComplexityRating (S/M/L/XL) + rationale
- [ ] Determines agent_count (1-5)
- [ ] Assessment is deterministic (same input = same output)
- [ ] Follows PROP-006 invariant

**COMPLEXITY RULES:**
```
S (1 agent):  Single file, <50 LOC, no new deps, no arch impact
M (1-2 agents): 2-3 files, 50-200 LOC, minor deps, localized impact
L (2-3 agents): 4-10 files, 200-500 LOC, new module, moderate impact
XL (3-5 agents): >10 files, >500 LOC, major refactor, significant arch changes
```

**NOTE:** If XL, recommend using wfc-plan + wfc-implement instead.

---

## TASK-004: Implement build orchestrator

**COMPLEXITY:** L
**DEPENDENCIES:** [TASK-002, TASK-003]
**ESTIMATED TIME:** 3 hours
**PROPERTIES:** [PROP-001, PROP-002, PROP-004, PROP-007]

**DESCRIPTION:**
Core orchestration logic that routes interview → complexity assessment → implementation execution.

**FILES AFFECTED:**
- `wfc/scripts/skills/build/orchestrator.py` (MODIFY)

**ACCEPTANCE CRITERIA:**
- [ ] Integrates with existing wfc-implement orchestrator
- [ ] Creates lightweight task specification (not full TASKS.md)
- [ ] Spawns appropriate number of agents based on complexity
- [ ] Enforces TDD workflow (PROP-007)
- [ ] Routes through quality gates (PROP-001)
- [ ] Routes through consensus review (PROP-002)
- [ ] Handles success/failure gracefully (PROP-004)

**ORCHESTRATION FLOW:**
```
1. Run interview.conduct()
2. Run complexity_assessor.assess()
3. IF complexity == XL:
     RECOMMEND wfc-plan + wfc-implement, EXIT
4. Generate lightweight task spec
5. Route to wfc-implement orchestrator
6. Route to wfc-review consensus
7. IF approved: Merge to main
   ELSE: Provide feedback, option to retry
```

---

## TASK-005: Implement CLI interface

**COMPLEXITY:** S
**DEPENDENCIES:** [TASK-004]
**ESTIMATED TIME:** 1 hour
**PROPERTIES:** []

**DESCRIPTION:**
SKILL.md that defines skill invocation and user experience.

**FILES AFFECTED:**
- `~/.claude/skills/wfc-build/SKILL.md` (MODIFY)

**ACCEPTANCE CRITERIA:**
- [ ] Skill is invocable via /wfc-build
- [ ] Accepts optional feature description as argument
- [ ] Supports --dry-run flag
- [ ] Displays clear progress indicators
- [ ] Shows final outcome

**USAGE:**
```bash
/wfc-build
/wfc-build "Add rate limiting to API endpoints"
/wfc-build --dry-run "Add user authentication"
```

---

## TASK-006: Integration with existing WFC

**COMPLEXITY:** M
**DEPENDENCIES:** [TASK-005]
**ESTIMATED TIME:** 2 hours
**PROPERTIES:** [PROP-001, PROP-002, PROP-003]

**DESCRIPTION:**
Ensure wfc-build integrates seamlessly with existing WFC skills and respects all safety properties.

**FILES AFFECTED:**
- `CLAUDE.md` (MODIFY - update workflow section)
- `README.md` (MODIFY - add wfc-build to skill suite)
- `wfc/shared/config/wfc_config.py` (MODIFY - add build config)

**ACCEPTANCE CRITERIA:**
- [ ] Respects all WFC safety properties
- [ ] NEVER bypasses quality gates (PROP-001)
- [ ] NEVER skips consensus review (PROP-002)
- [ ] NEVER auto-pushes to remote (PROP-003)
- [ ] Telemetry recorded
- [ ] Config options documented

---

## TASK-007: Tests

**COMPLEXITY:** M
**DEPENDENCIES:** [TASK-006]
**ESTIMATED TIME:** 2 hours
**PROPERTIES:** [PROP-004, PROP-005]

**DESCRIPTION:**
Comprehensive test suite covering unit and integration scenarios.

**FILES AFFECTED:**
- `tests/test_build_interview.py` (NEW)
- `tests/test_build_complexity.py` (NEW)
- `tests/test_build_orchestrator.py` (NEW)
- `tests/test_build_integration.py` (NEW)

**ACCEPTANCE CRITERIA:**
- [ ] Unit tests for interview logic
- [ ] Unit tests for complexity assessment
- [ ] Unit tests for orchestrator flow
- [ ] Integration tests for end-to-end workflow
- [ ] Test coverage >80%
- [ ] All tests pass with uv run pytest -v

---

## TASK-008: Documentation

**COMPLEXITY:** S
**DEPENDENCIES:** [TASK-007]
**ESTIMATED TIME:** 1 hour
**PROPERTIES:** []

**DESCRIPTION:**
Complete documentation for wfc-build skill.

**FILES AFFECTED:**
- `~/.claude/skills/wfc-build/SKILL.md` (MODIFY)
- `docs/WFC_BUILD.md` (NEW)
- `CLAUDE.md` (MODIFY)
- `README.md` (MODIFY)

**ACCEPTANCE CRITERIA:**
- [ ] SKILL.md has clear usage instructions
- [ ] WFC_BUILD.md explains philosophy and design
- [ ] CLAUDE.md workflow examples updated
- [ ] README skill suite table includes wfc-build

---

## SUMMARY

**TOTAL TASKS:** 8
**ESTIMATED TIME:** 12-14 hours
**COMPLEXITY DISTRIBUTION:** S: 3, M: 4, L: 1, XL: 0

**CRITICAL PATH:**
```
TASK-001 → TASK-002/003 → TASK-004 → TASK-005 → TASK-006 → TASK-007/008
```

**PARALLELIZATION:** TASK-002 and TASK-003 after TASK-001

**RISK FACTORS:**
- Integration with existing wfc-implement orchestrator
- Complexity assessment algorithm accuracy
- Performance: <30s interview, 50% speedup target
