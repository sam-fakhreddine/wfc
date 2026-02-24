# Implementation Plan Summary

## WFC Validate Skill Remediation Fixes

**Created**: 2026-02-20
**Status**: Ready for implementation
**Estimated Effort**: 17-23 hours (12-14 hours with parallelization)

---

## What This Plan Fixes

Based on VALIDATE.md analysis, implements 3 critical fixes to improve wfc-validate from **6.8/10 to 8.4/10**:

### Fix 1: Dimension 7 - Claude Code Orchestration (2/10 → 9/10)

**Problem**: Design assumed SDK `call_agent()` that doesn't exist in Claude Code
**Solution**: Two-phase orchestrator with file-based workspace
**Tasks**: TASK-001 through TASK-006 (6 tasks, 6-8 hours)

### Fix 2: Dimension 5 - Analyzer Content Analysis (4/10 → 9/10)

**Problem**: Analyzer returns hardcoded 8/10 scores regardless of content
**Solution**: Pattern detection for 24 patterns across 13 categories
**Tasks**: TASK-007 through TASK-010 (4 tasks, 2-3 hours)

### Fix 3: Dimension 6 - Blast Radius Mitigations (6/10 → 9/10)

**Problem**: Batch mode can partially succeed (27/30 PRs merged, 3 stuck)
**Solution**: Atomic batch semantics, dry-run mode, rollback plan
**Tasks**: TASK-011 through TASK-015 (5 tasks, 6-8 hours)

---

## Plan Structure

**TASKS.md**: 18 implementation tasks with dependencies
**PROPERTIES.md**: 19 formal properties (9 critical, 10 important)
**TEST-PLAN.md**: 44 tests (28 unit, 12 integration, 4 E2E)

---

## Implementation Phases

**Phase 1** (6-8 hours): Component 1 - Orchestration

- Create RemediationOrchestrator class
- Implement workspace management
- Create agent prompt templates
- Build task spec generation
- Implement result finalization

**Phase 2** (2-3 hours): Component 2 - Analyzer

- Pattern detection (13 categories)
- Failure mode checking (11 modes)
- Dynamic scoring (2-10 range)
- Context-aware recommendations

**Phase 3** (6-8 hours): Component 3 - Batch Safety

- Dry-run mode (two-phase validation)
- Safety gates (intent, scope creep)
- Rollback checklist generator
- Batch summary report
- CLI flags

**Phase 4** (3-4 hours): Testing

- Orchestrator tests (TASK-016)
- Analyzer tests (TASK-017)
- Batch safety tests (TASK-018)
- E2E workflows

---

## Critical Path

```
TASK-001 (2h) → TASK-002 (2h) → TASK-003 (3h) → TASK-004 (2h) → TASK-005 (2h) → TASK-016 (3h)
Total: 14 hours sequential
```

With parallelization:

- Phase 2 can run concurrently with Phase 1
- Phase 3 can start after Phase 1 completes
- Phase 4 tests can run in parallel

**Wall clock: 12-14 hours** with 2 parallel work streams

---

## Key Files to Create/Modify

**New Files** (orchestrator):

- `wfc/scripts/orchestrators/validate/orchestrator.py`
- `wfc/scripts/orchestrators/validate/schemas.py`
- `wfc/skills/wfc-validate/agents/cataloger.md`
- `wfc/skills/wfc-validate/agents/validator.md`
- `wfc/skills/wfc-validate/references/rubric.json`
- `wfc/skills/wfc-validate/references/antipatterns.json`

**Modified Files** (analyzer):

- `wfc/skills/wfc-validate/analyzer.py` (4 new methods)

**Modified Files** (batch safety):

- `wfc/skills/wfc-prompt-fixer/orchestrator.py` (5 new methods, 5 dataclasses)
- `wfc/skills/wfc-prompt-fixer/cli.py` (3 new flags)

**Test Files**:

- `tests/test_validate_orchestrator.py` (9 tests)
- `tests/test_validate_analyzer.py` (9 tests)
- `tests/test_batch_safety.py` (12 tests)
- `tests/test_e2e_validate.py` (4 tests)

---

## Success Criteria

✅ All 18 tasks completed
✅ All 19 properties validated
✅ All 44 tests passing (>85% coverage)
✅ Dimension 7 score: 9/10 (two-phase orchestrator working)
✅ Dimension 5 score: 9/10 (analyzer detects patterns, no hardcoded scores)
✅ Dimension 6 score: 9/10 (atomic batches, rollback in 10 seconds)
✅ Overall VALIDATE.md score: 8.4/10 (up from 6.8/10)

---

## Next Steps

1. Review this plan
2. Run `/wfc-implement plans/plan_validate_fixes_20260220/TASKS.md`
3. TDD approach: Write tests first (Phase 4), then implementation (Phases 1-3)
4. Validate with `/wfc-review` after each component
5. Integration test after all 3 components complete
6. Update VALIDATE.md with "IMPLEMENTED" status

---

## Reference Documents

All design documents from VALIDATE.md analysis are in `.development/`:

**Dimension 7 Fix**:

- `.development/fix-dimension-7-orchestration.md` (879 lines)

**Dimension 5 Fix**:

- `.development/fix-dimension-5-analyzer.md`

**Dimension 6 Fix**:

- `.development/dimension-6-index.md` (master navigation)
- `.development/dimension-6-quick-reference.md` (TL;DR)
- `.development/fix-dimension-6-mitigations.md` (full design)
- 4 more supporting documents (7 total, 3,279 lines)

**Total Design Documentation**: 4,158 lines across 8 files
