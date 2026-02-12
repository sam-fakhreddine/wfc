# WFC Changelog

All notable changes to WFC (World Fucking Class) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2026-02-10

### Added - Week 1-3 Enhancements

#### Extended Thinking Intelligence
- **Increased token budgets** (4-5x) for all complexity levels
  - S: 500 → 2,000 tokens (1% of 200k context)
  - M: 1,000 → 5,000 tokens (2.5% of context)
  - L: 2,500 → 10,000 tokens (5% of context)
  - XL: 5,000 → 20,000 tokens (10% of context)
- **Updated retry threshold** from 1 to 3 attempts before UNLIMITED mode
- **Hard limit** of 4 total retries maximum (5 attempts)
- **Rationale comments** explaining 200k context window allocation

**Expected Impact**: 30-50% reduction in truncated thinking

#### Systematic Debugging
- **Created** `wfc/skills/implement/DEBUGGING.md` with comprehensive 4-phase methodology
- **Integrated** debugging workflow into agent TDD prompts
- **Added** `AgentReport.root_cause` field for bug fix documentation
- **Enforces** "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST" principle
- **Phases**: Root Cause Investigation → Pattern Analysis → Hypothesis Testing → Fix Implementation

**Expected Impact**: 50-70% reduction in debugging time

#### Code Review Checklist
- **Created** `wfc/skills/review/CHECKLIST.md` with systematic 6-step methodology
- **Integrated** into wfc-review skill documentation
- **Maps** checklist sections to reviewer personas (CR, SEC, PERF, COMP)
- **Steps**: Understand Context → Functionality → Quality → Security → Performance → Tests

**Expected Impact**: 30-40% more issues caught vs ad-hoc review

#### Automatic Metrics Collection
- **Created** `wfc/shared/telemetry_auto.py` for local metrics storage
- **Created** `wfc/cli/metrics.py` CLI for viewing metrics
- **Tracks**: Success rate, thinking usage, retries, debugging time, tokens, coverage
- **Storage**: Local only (no external services) at `~/.wfc/telemetry/`
- **Usage**: `python3 wfc/cli/metrics.py [TASK-ID]`

#### Validation Framework
- **Created** `validation/VALIDATION-REPORT.md` template
- **Created** `validation/metrics.json` for structured data
- **Created** `validation/collect_metrics.py` automation script
- **Decision**: EARLY GO based on 100% success rate, 0% truncation, 0 retries (3/10 tasks)
- **Strategy**: Continued monitoring through tasks 4-10

### Changed

#### Extended Thinking Logic
- **Modified** `wfc/shared/extended_thinking.py` retry threshold logic
- **Old**: `if retry_count > 0` (triggered after 1 retry)
- **New**: `if retry_count >= 3` (triggers after 3 retries)
- **Added**: Warning for retry_count > 4 (exceeded maximum)

#### Agent Workflow
- **Updated** `wfc/skills/implement/executor.py` agent prompts
- **Added**: Systematic debugging steps 3a-3d in TDD workflow
- **Added**: Root cause documentation requirement

#### Agent Report Schema
- **Updated** `wfc/skills/implement/agent.py` AgentReport dataclass
- **Added**: `root_cause: Optional[Dict[str, str]]` field
- **Format**: {what, why, where, fix, tests}

#### Documentation
- **Updated** `QUICKSTART.md` with recent enhancements section
- **Updated** `wfc/skills/review/SKILL.md` with checklist methodology
- **Added**: Extended thinking budget rationale
- **Added**: Retry threshold explanation

### Fixed

None in this release (enhancements only)

### Analysis - ISTHISSMART Review

**Score**: 9.2/10 - PROCEED
**Verdict**: 18 clear strengths, 3 minor considerations
**Risk**: Low - additive changes, proven patterns from antigravity-awesome-skills
**Testing**: Preliminary validation shows 100% success, 0% truncation, 0 retries

---

## [1.0.0] - Initial Release

### Added
- Multi-agent consensus code review system
- 54 specialized reviewer personas
- ELEGANT principles enforcement
- WFC-plan adaptive planning
- WFC-implement TDD-first execution
- WFC-security threat modeling
- WFC-observe observability generation
- Quality gate pre-review checks
- Merge engine with rollback
- Git worktree isolation
- Mock review system

### Philosophy
- **ELEGANT**: Explicit, Layered, Encapsulated, Graceful, Testable
- **MULTI-TIER**: Presentation/Logic/Data/Config separation
- **PARALLEL**: Maximum safe concurrency

---

## Versioning

WFC follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

---

## References

- **ISTHISSMART.md**: Decision analysis for v1.1.0 enhancements
- **plan/**: Implementation planning artifacts (TASKS.md, PROPERTIES.md, TEST-PLAN.md)
- **validation/**: Validation framework and metrics
- **Antigravity Skills**: code-review-checklist, systematic-debugging, test-fixing
