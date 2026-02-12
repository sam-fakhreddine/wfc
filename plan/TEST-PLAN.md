# WFC-BUILD TEST PLAN

**PROJECT:** wfc-build - Streamlined Feature Builder
**GENERATED:** 2026-02-12
**TARGET COVERAGE:** >80%

---

## TEST STRATEGY

### Test Pyramid

```
       /\
      /E2\     Integration Tests (20%)
     /────\
    /      \   Unit Tests (80%)
   /________\
```

**Rationale:** Most testing at unit level for fast feedback, integration tests for critical workflows.

---

## UNIT TESTS

### Test Suite: test_build_interview.py

**Coverage Target:** Interview logic, adaptive questions

#### TEST-001: Interview completes in <30s (PROP-008)
- **Property:** PROP-008
- **Steps:**
  1. Mock LLM responses (realistic delays)
  2. Run interview.conduct()
  3. Measure duration
- **Expected:** P50 <10s, P95 <20s, P99 <30s

#### TEST-002: Max 5 questions asked
- **Steps:**
  1. Run interview with various feature descriptions
  2. Count questions asked
- **Expected:** ≤5 questions always

#### TEST-003: Adaptive question flow
- **Steps:**
  1. Answer Q2 with "new module"
  2. Assert Q3 asks about dependencies
  3. Answer Q2 with "few files"
  4. Assert Q3 asks which files
- **Expected:** Questions adapt to previous answers

#### TEST-004: Structured output parsing
- **Steps:**
  1. Provide interview answers
  2. Get InterviewResult
  3. Assert all fields populated
- **Expected:** Valid InterviewResult dataclass

---

### Test Suite: test_build_complexity.py

**Coverage Target:** Complexity assessment algorithm (PROP-006)

#### TEST-005: S complexity assessment
- **Property:** PROP-006
- **Steps:**
  1. Create InterviewResult: single file, <50 LOC, no deps
  2. Run assess()
  3. Assert ComplexityRating = S, agent_count = 1
- **Expected:** S rating, 1 agent

#### TEST-006: M complexity assessment
- **Steps:**
  1. InterviewResult: 2-3 files, 100 LOC, minor deps
  2. assess()
  3. Assert M rating, agent_count ∈ {1,2}
- **Expected:** M rating, 1-2 agents

#### TEST-007: L complexity assessment
- **Steps:**
  1. InterviewResult: 5 files, 300 LOC, new module
  2. assess()
  3. Assert L rating, agent_count ∈ {2,3}
- **Expected:** L rating, 2-3 agents

#### TEST-008: XL complexity triggers recommendation
- **Steps:**
  1. InterviewResult: 15 files, 600 LOC, major refactor
  2. assess()
  3. Assert XL rating, recommendation = "use wfc-plan"
- **Expected:** XL + recommendation

#### TEST-009: Deterministic assessment
- **Property:** PROP-006
- **Steps:**
  1. Same InterviewResult → assess() × 100
  2. Assert all results identical
- **Expected:** 100% determinism

---

### Test Suite: test_build_orchestrator.py

**Coverage Target:** Orchestration logic, integration with wfc-implement

#### TEST-010: Routes to wfc-implement orchestrator
- **Steps:**
  1. Mock wfc-implement orchestrator
  2. Run build_orchestrator.execute()
  3. Assert wfc-implement called with correct args
- **Expected:** Delegation to wfc-implement

#### TEST-011: Enforces quality gates (PROP-001)
- **Property:** PROP-001
- **Steps:**
  1. Mock quality_checker.check_all() → FAIL
  2. Run orchestrator
  3. Assert build fails, no merge
- **Expected:** Build blocked by quality gate

#### TEST-012: Routes to consensus review (PROP-002)
- **Property:** PROP-002
- **Steps:**
  1. Mock wfc-review consensus
  2. Run orchestrator
  3. Assert consensus called
- **Expected:** Review integration

#### TEST-013: Enforces TDD workflow (PROP-007)
- **Property:** PROP-007
- **Steps:**
  1. Mock agent workflow
  2. Assert TEST_FIRST phase before IMPLEMENT
- **Expected:** RED → GREEN → REFACTOR

#### TEST-014: Graceful failure handling (PROP-004)
- **Property:** PROP-004
- **Steps:**
  1. Inject failure at each stage (interview, impl, review)
  2. Assert actionable feedback provided
  3. Assert no hanging state
- **Expected:** Clean failure + feedback

#### TEST-015: No auto-push (PROP-003)
- **Property:** PROP-003
- **Steps:**
  1. Run full orchestrator workflow
  2. Check git commands executed
  3. Assert no "git push" calls
- **Expected:** Merge to local main only

---

## INTEGRATION TESTS

### Test Suite: test_build_integration.py

**Coverage Target:** End-to-end workflows

#### TEST-016: Simple feature (S) - Happy path
- **Properties:** ALL
- **Steps:**
  1. Run /wfc-build "Add logging to single file"
  2. Interview: single file, 20 LOC, no deps
  3. Assert complexity = S, 1 agent spawned
  4. Assert quality checks pass
  5. Assert review APPROVED
  6. Assert merge to main
  7. Assert <8 min total duration (PROP-009)
- **Expected:** Successful build, merged code

#### TEST-017: Medium feature (M) - Quality failure
- **Steps:**
  1. Run /wfc-build "Add auth to 2 files"
  2. Interview: 2 files, 100 LOC
  3. Inject formatting errors
  4. Assert quality gate blocks merge
  5. Assert actionable feedback (PROP-005)
- **Expected:** Build fails with fix instructions

#### TEST-018: Large feature (L) - Review failure
- **Steps:**
  1. Run /wfc-build "Refactor module structure"
  2. Interview: 5 files, 300 LOC
  3. Mock review → CONDITIONAL APPROVE
  4. Assert feedback provided
  5. Assert retry option offered
- **Expected:** Review feedback + retry

#### TEST-019: XL feature triggers recommendation
- **Steps:**
  1. Run /wfc-build "Complete system rewrite"
  2. Interview: 20 files, 1000 LOC
  3. Assert complexity = XL
  4. Assert recommends wfc-plan + wfc-implement
  5. Assert build does not proceed
- **Expected:** Recommendation displayed, no build

#### TEST-020: Dry-run mode
- **Steps:**
  1. Run /wfc-build --dry-run "Add feature"
  2. Assert interview conducted
  3. Assert complexity assessed
  4. Assert plan displayed
  5. Assert no actual implementation
- **Expected:** Preview only

#### TEST-021: Performance benchmark (PROP-008, PROP-009)
- **Properties:** PROP-008, PROP-009
- **Steps:**
  1. Run 50× S tasks, measure duration
  2. Run 50× M tasks, measure duration
  3. Compare to wfc-plan + wfc-implement baseline
- **Expected:**
  - Interview P95 < 20s
  - S tasks: wfc-build ≤ 50% of baseline
  - M tasks: wfc-build ≤ 50% of baseline

---

## PROPERTY VERIFICATION MATRIX

| Test ID | PROP-001 | PROP-002 | PROP-003 | PROP-004 | PROP-005 | PROP-006 | PROP-007 | PROP-008 | PROP-009 |
|:--------|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|
| TEST-001|          |          |          |          |          |          |          |    ✓     |          |
| TEST-005|          |          |          |          |          |    ✓     |          |          |          |
| TEST-009|          |          |          |          |          |    ✓     |          |          |          |
| TEST-011|    ✓     |          |          |          |          |          |          |          |          |
| TEST-012|          |    ✓     |          |          |          |          |          |          |          |
| TEST-013|          |          |          |          |          |          |    ✓     |          |          |
| TEST-014|          |          |          |    ✓     |          |          |          |          |          |
| TEST-015|          |          |    ✓     |          |          |          |          |          |          |
| TEST-016|    ✓     |    ✓     |    ✓     |    ✓     |          |          |    ✓     |          |    ✓     |
| TEST-017|    ✓     |          |          |          |    ✓     |          |          |          |          |
| TEST-021|          |          |          |          |          |          |          |    ✓     |    ✓     |

---

## TEST DATA

### Sample Interview Responses

**Simple (S):**
```json
{
  "feature_description": "Add request logging to middleware",
  "scope": "single_file",
  "files_affected": ["middleware.py"],
  "loc_estimate": 25,
  "new_dependencies": [],
  "constraints": []
}
```

**Medium (M):**
```json
{
  "feature_description": "Add JWT authentication",
  "scope": "few_files",
  "files_affected": ["auth.py", "middleware.py"],
  "loc_estimate": 150,
  "new_dependencies": ["pyjwt"],
  "constraints": ["security"]
}
```

**Large (L):**
```json
{
  "feature_description": "Refactor user module",
  "scope": "new_module",
  "files_affected": ["users/__init__.py", "users/models.py", "users/service.py", "users/repository.py", "users/api.py"],
  "loc_estimate": 400,
  "new_dependencies": [],
  "constraints": ["maintain_api_compatibility"]
}
```

---

## COVERAGE REQUIREMENTS

**Overall:** >80%
**Critical paths:** 100%
  - Orchestrator workflow
  - Quality gate enforcement
  - Review routing
  - Git safety (no push)

**Test Execution:**
```bash
uv run pytest tests/test_build_* -v --cov=wfc/scripts/skills/build --cov-report=html
```

---

## CI/CD INTEGRATION

**Pre-commit:**
- Run unit tests (<10s)
- Fail if coverage <80%

**Pre-push:**
- Run all tests (unit + integration)
- Fail if any test fails

**PR Checks:**
- Full test suite
- Property verification
- Performance benchmarks
- Coverage report
