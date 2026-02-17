# PLANNING.md

**Architecture, Design Principles, and Absolute Rules for WFC**

> This document is read by Claude Code at session start to ensure consistent, high-quality development aligned with project standards.

---

## 🎯 Project Vision

**WFC (World Fucking Class)** transforms multi-agent code review through:
- **99% token reduction** via ultra-minimal prompts + file references
- **Agent Skills compliance** for Claude Code integration
- **56 expert personas** with automatic selection
- **Weighted consensus** algorithm for quality decisions

**Core Mission**: Provide production-grade, token-efficient, multi-agent consensus code review that is:
- **Accurate** - Specialized personas with domain expertise
- **Efficient** - 99% token reduction (150k → 1.5k tokens)
- **Compliant** - Agent Skills specification enforced
- **Validated** - Automated checks prevent regressions

---

## 🏗️ Architecture Overview

### Current State (v0.1.0)

WFC is a **Python package** with:
- Ultra-minimal persona system (200 tokens per persona)
- File reference architecture (send paths, not content)
- Token budget manager (accurate tiktoken counting)
- Consensus algorithm (weighted voting)
- 17 Agent Skills compliant skills
- Professional CLI (`wfc` command)
- Automated validation (pre-commit + CI/CD)

```
WFC Architecture v0.1.0
│
├── Core Package (wfc/)
│   ├── scripts/                    # Executable code
│   │   ├── personas/               # Persona system
│   │   │   ├── token_manager.py            # 99% token reduction
│   │   │   ├── ultra_minimal_prompts.py    # 200-token prompts
│   │   │   ├── file_reference_prompts.py   # File refs not content
│   │   │   ├── persona_executor.py         # Prepare subagent tasks
│   │   │   └── persona_orchestrator.py     # Select personas
│   │   ├── hooks/                   # Hook infrastructure
│   │   │   ├── pretooluse_hook.py          # PreToolUse hook handler
│   │   │   ├── security_hook.py            # Security enforcement
│   │   │   ├── rule_engine.py              # Custom rule engine
│   │   │   ├── config_loader.py            # Hook configuration
│   │   │   ├── hook_state.py               # Hook state management
│   │   │   └── patterns/                   # Security patterns (JSON)
│   │   └── skills/                 # Skill implementations
│   │       └── review/
│   │           ├── orchestrator.py         # Review workflow
│   │           ├── consensus.py            # Consensus algorithm
│   │           └── agents.py               # Agent logic
│   ├── references/                 # Progressive disclosure
│   │   ├── personas/               # 56 expert personas (JSON)
│   │   ├── ARCHITECTURE.md
│   │   ├── TOKEN_MANAGEMENT.md
│   │   └── ULTRA_MINIMAL_RESULTS.md
│   └── assets/                     # Templates, configs
│       └── templates/
│           └── playground/         # HTML playground templates
│
├── Installed Skills (~/.claude/skills/wfc-*)
│   ├── wfc-review/                 # Multi-agent consensus review
│   ├── wfc-plan/                   # Adaptive planning
│   ├── wfc-implement/              # Parallel implementation
│   ├── wfc-security/               # STRIDE threat analysis
│   ├── wfc-architecture/           # Architecture docs + C4 diagrams
│   ├── wfc-test/                   # Property-based tests
│   ├── wfc-safeguard/              # Real-time security enforcement hooks
│   ├── wfc-rules/                  # Markdown-based custom enforcement rules
│   ├── wfc-playground/             # Interactive HTML playground generator
│   └── ... (17 total)
│
├── Tests (tests/)
│   ├── test_implement_e2e.py       # End-to-end tests
│   ├── personas/
│   │   └── test_persona_selection.py
│   └── skills/
│       └── plan/test_plan_generator.py
│
├── Documentation (docs/)
│   ├── architecture/               # System design, planning
│   ├── security/                   # OWASP, hooks, git safety
│   ├── workflow/                   # Install, PR, build, implementation
│   ├── quality/                    # Quality gates, personas
│   ├── reference/                  # Compliance, registries
│   └── examples/
│
└── Tooling
    ├── Makefile                    # Development tasks
    ├── .github/workflows/          # CI/CD
    ├── scripts/                    # Utilities
    │   ├── benchmark_tokens.py     # Token benchmarks
    │   └── pre-commit.sh           # Pre-commit validation
    └── wfc/cli.py                  # wfc command
```

### Completed Enhancements (v0.1.0)

✅ **wfc-implement Complete** (Phases 1-3):
- Memory system (cross-session learning via ReflexionMemory)
- Confidence-first implementation (prevent wrong-direction work)
- Workflow metrics tracking (tokens, time, success rates)
- Token budget optimization (historical learning)
- Universal quality gate (Trunk.io integration)
- TDD workflow enforcement (RED-GREEN-REFACTOR)
- Merge engine with rollback (main always passing)
- Integration tests (>80% coverage)

### Future State (v0.2.0+)

Planned enhancements:
- Dashboard (WebSocket, Mermaid visualization) - Phase 4 Optional
- Enhanced MCP integration
- Advanced pattern learning
- Distributed execution (cloud agents)

### TEAMCHARTER Governance (v0.1.1+)

**Values-Driven Workflow**: All plans are validated against 6 core values

**6 Core Values**:
1. **Innovation & Experimentation** - Embrace failure as learning, validate through critique
2. **Accountability & Simplicity** - Complexity budgets, Say:Do ratio tracking
3. **Teamwork & Collaboration** - Multi-agent consensus, customer advocate persona
4. **Continuous Learning & Curiosity** - ReflexionMemory, retrospective analysis
5. **Customer Focus & Service Excellence** - Customer-centric interview questions
6. **Trust & Autonomy** - Confidence thresholds, informed decision-making

**Enforcement Mechanisms**:
- **Complexity Budgets**: Pre-gate flags when tasks exceed S/M/L/XL limits
- **Interview Questions**: "Who is the customer?", "What does success look like?"
- **Review Personas**: Customer Advocate ensures stakeholder voice in reviews
- **Memory Tracking**: Values alignment field in reflexion entries
- **Audit Trails**: Immutable proof that validation was performed

**Validated Plan Flow**:

```
Plan Generation → Validate (7D critique) → Revise → Code Review (loop to 8.5+) → Final
```

**Governance Documents**:
- `wfc/references/TEAMCHARTER.md` - Human-readable values and enforcement
- `wfc/references/teamcharter_values.json` - Machine-readable schema for agents

**Why This Matters**:
- Prevents over-engineering through evidence-based complexity assessment
- Ensures customer value is central to every task
- Builds institutional memory through values-aligned retrospectives
- Provides accountability through Say:Do ratio tracking

---

## ⚙️ Design Principles

### 1. Token Efficiency is Paramount

**Goal**: Minimize token usage while maximizing review quality

**How**:
- **Ultra-minimal prompts**: 200 tokens (was 3000) - 93% reduction
- **File references**: Send paths, not content - 95% reduction
- **Domain guidance**: What to look for, not how to grep
- **Progressive disclosure**: Load only what's needed

**Never**:
- ❌ Send full file content to personas
- ❌ Use verbose backstories or examples
- ❌ Include redundant information
- ❌ Exceed token budgets without justification

**Always**:
- ✅ Measure token usage with benchmarks
- ✅ Use file reference architecture
- ✅ Build ultra-minimal prompts
- ✅ Report token savings

### 2. Agent Skills Compliance

**Goal**: All WFC skills comply with Agent Skills specification

**How**:
- Valid frontmatter (only: name, description, license)
- Hyphenated names (wfc-review, not wfc-review)
- Comprehensive descriptions (triggers, use cases, anti-use cases)
- XML prompt generation
- Progressive disclosure pattern
- Validated with skills-ref

**Never**:
- ❌ Use colons in skill names
- ❌ Include invalid frontmatter fields
- ❌ Skip validation before commit
- ❌ Break XML prompt generation

**Always**:
- ✅ Validate with `make validate`
- ✅ Test XML generation
- ✅ Follow progressive disclosure
- ✅ Keep SKILL.md < 500 lines

### 3. Evidence-Based Development

**Goal**: Never guess - always verify

**How**:
- Read files before editing
- Check existing code with Glob/Grep
- Verify assumptions with tests
- Measure token usage with benchmarks
- Validate skills with skills-ref

**Never**:
- ❌ Implement based on assumptions
- ❌ Skip reading existing code
- ❌ Guess at file locations
- ❌ Trust outdated knowledge

**Always**:
- ✅ Read before writing
- ✅ Search before creating
- ✅ Test before claiming success
- ✅ Benchmark before optimizing

### 4. WFC Philosophy (ELEGANT)

**E**LEGANT: Simplest solution wins
- No over-engineering
- Clear, readable code
- Minimal abstractions

**M**ULTI-TIER: Clear separation of concerns
- Logic separated from presentation
- Personas (logic) vs CLI (presentation)
- Progressive disclosure (load on demand)

**P**ARALLEL: True concurrent execution
- Independent subagents
- No context bleeding
- Claude Code Task tool integration

**P**ROGRESSIVE: Load only what's needed
- SKILL.md first (< 500 lines)
- References on demand
- Scripts when executed

**T**OKEN-AWARE: Every token counts
- Measure with benchmarks
- 99% reduction target
- Budget enforcement

**C**OMPLIANT: Agent Skills spec enforced
- Validated with skills-ref
- XML prompts work
- No regressions

### 5. Quality Over Speed

**Goal**: Correctness and maintainability trump quick implementations

**How**:
- Run `make check-all` before commit
- Fix failing tests immediately
- Document non-obvious decisions
- Follow pre-commit hooks

**Never**:
- ❌ Skip tests to save time
- ❌ Bypass pre-commit hooks
- ❌ Leave TODOs in production code
- ❌ Commit broken code

**Always**:
- ✅ Run tests before commit
- ✅ Format code with `make format`
- ✅ Validate skills with `make validate`
- ✅ Check all with `make check-all`

---

## 🛠️ Implementation Patterns

### TDD Workflow (RED-GREEN-REFACTOR)

**Pattern**: All implementations follow strict TDD workflow

**Phases**:
1. **UNDERSTAND** - Read task, assess confidence (≥90%), search past errors
2. **TEST_FIRST** - Write tests BEFORE implementation (RED phase - tests fail)
3. **IMPLEMENT** - Write minimum code to pass tests (GREEN phase - tests pass)
4. **REFACTOR** - Clean up while maintaining passing tests
5. **QUALITY_CHECK** - Run universal quality gate (Trunk.io)
6. **SUBMIT** - Verify all criteria met, route to review

**Why**: Prevents over-engineering, ensures testability, documents behavior

**Example**:
```python
# 1. UNDERSTAND
task = read_task("TASK-001")
confidence = assess_confidence(task)  # Must be ≥90%
past_errors = search_similar_errors(task.description)

# 2. TEST_FIRST (RED)
def test_add_logging():
    result = my_function()
    assert "Entered my_function" in captured_logs
    assert "Exited my_function" in captured_logs
# Run tests → FAIL (good!)

# 3. IMPLEMENT (GREEN)
def my_function():
    logging.info("Entered my_function")
    # ... implementation ...
    logging.info("Exited my_function")
    return result
# Run tests → PASS

# 4. REFACTOR
def my_function():
    log_function_entry("my_function")
    result = _do_work()
    log_function_exit("my_function")
    return result
# Run tests → Still PASS

# 5. QUALITY_CHECK
trunk check my_function.py  # Must pass

# 6. SUBMIT
verify_acceptance_criteria(task)
route_to_review(agent_report)
```

### Confidence-First Implementation

**Pattern**: Assess confidence BEFORE starting work (SuperClaude pattern)

**Decision Tree**:
- **≥90%**: Proceed with implementation
- **70-89%**: Present alternatives + ask clarifying questions
- **<70%**: STOP - Investigate more, ask user for guidance

**Why**: Prevents 25-250x token waste from wrong-direction work

**Example**:
```python
assessment = confidence_checker.assess(task)

if assessment.confidence_score >= 90:
    proceed_with_implementation()
elif assessment.confidence_score >= 70:
    ask_clarifying_questions(assessment.questions)
    present_alternatives(assessment.alternatives)
else:
    stop_and_investigate(assessment.risks)
```

### Cross-Session Learning (ReflexionMemory)

**Pattern**: Log errors and fixes for future reference

**Files**:
- `wfc/memory/reflexion.jsonl` - Errors and fixes
- `wfc/memory/workflow_metrics.jsonl` - Performance metrics

**Why**: Don't repeat the same mistakes across sessions

**Example**:
```python
# Log reflexion entry
reflexion = ReflexionEntry(
    task_id="TASK-001",
    mistake="Forgot to run tests after refactoring",
    evidence="pytest returned 3 failures",
    fix="Rolled back refactoring commit",
    rule="ALWAYS run tests after refactoring before committing",
    severity="high"
)
memory_manager.log_reflexion(reflexion)

# Before starting new task, search for similar errors
similar = memory_manager.search_similar_errors("refactoring authentication")
if similar:
    warn_about_past_mistakes(similar)
```

### Token Budget Optimization

**Pattern**: Complexity-based budgets with historical learning

**Budgets**:
- S (Simple): 200 tokens
- M (Medium): 1,000 tokens
- L (Large): 2,500 tokens
- XL (Extra Large): 5,000 tokens

**Why**: Prevent over-engineering, optimize based on history

**Example**:
```python
budget = token_manager.create_budget("TASK-M", TaskComplexity.M, use_history=True)
# If history shows M tasks average 1,500 tokens:
# budget.budget_total = 1,500 * 1.2 = 1,800 tokens (20% buffer)

budget = token_manager.update_usage(budget, input_tokens=800, output_tokens=400)
if budget.is_approaching_limit():
    warn("⚠️ APPROACHING BUDGET: 88% used")
```

### Failure Severity Classification

**Pattern**: WARNING (don't block), ERROR (block but retryable), CRITICAL (immediate failure)

**Why**: "Warnings aren't failures but broken code is" (user feedback)

**Decision**:
- **WARNING**: Linting warnings, style issues → Don't block
- **ERROR**: Test failures, compilation errors → Block but retry (max 2)
- **CRITICAL**: Security vulnerabilities, data loss → Immediate failure

**Example**:
```python
severity = classify_test_failure(test_result)

if severity == FailureSeverity.WARNING:
    report_warning_but_continue()
elif severity == FailureSeverity.ERROR:
    if retry_count < max_retries:
        retry_task()
    else:
        fail_with_recovery_plan()
else:  # CRITICAL
    immediate_failure_no_retry()
```

### Merge with Rollback

**Pattern**: Main branch always passing, worktrees preserved on failure

**Workflow**:
1. Rebase on main
2. Re-run tests after rebase
3. Merge to main
4. Run integration tests
5. Rollback if integration tests fail

**Why**: Safety - never break main, preserve evidence for investigation

**Example**:
```python
# Merge workflow
result = merge_engine.merge(task, branch, worktree_path)

if result.status == MergeStatus.SUCCESS:
    cleanup_worktree()
elif result.status == MergeStatus.FAILED_TESTS:
    # Automatic rollback
    git_reset_hard(merge_sha)
    # Preserve worktree for investigation
    result.worktree_preserved = True
    # Re-queue with recovery plan
    if result.should_retry:
        create_recovery_plan(task)
        re_queue_task(task)
```

### Parallel Execution with Dependencies

**Pattern**: Topological sort, respect dependencies, max agents limit

**Why**: Maximum safe concurrency, respect task dependencies

**Example**:
```python
# Task graph with dependencies
tasks = [
    Task("TASK-001", dependencies=[]),
    Task("TASK-002", dependencies=["TASK-001"]),
    Task("TASK-003", dependencies=[]),
]

# Group by dependency level
levels = topological_sort(tasks)
# Level 1: TASK-001, TASK-003 (parallel)
# Level 2: TASK-002 (waits for TASK-001)

# Execute with max_agents limit
for level in levels:
    agents = min(len(level), max_agents)
    execute_parallel(level, agents)
```

---

## 🚫 Absolute Rules

### Token Management

**NEVER**:
- Send full file content to personas
- Use verbose persona backstories
- Exceed token budgets without justification
- Skip token benchmarking

**ALWAYS**:
- Use file reference architecture
- Build ultra-minimal prompts (200 tokens)
- Measure token usage with `make benchmark`
- Report token savings to user

### Agent Skills Compliance

**NEVER**:
- Use colons in skill names (use hyphens: `wfc-review`)
- Include invalid frontmatter fields (`user-invocable`, `disable-model-invocation`, `argument-hint`)
- Skip validation (`make validate`)
- Break XML prompt generation

**ALWAYS**:
- Validate with skills-ref before commit
- Use only allowed frontmatter fields (name, description, license)
- Test XML generation
- Keep SKILL.md < 500 lines

### Code Quality

**NEVER**:
- Commit failing tests
- Skip pre-commit hooks
- Bypass linting
- Leave debugging code

**ALWAYS**:
- Run `make check-all` before commit
- Format code with `make format`
- Fix linting errors
- Update tests when changing code

### Development Workflow

**NEVER**:
- Use `python -m` or `pip install` directly
- Bypass Make for common tasks
- Commit without running tests
- Skip documentation updates

**ALWAYS**:
- Use UV for Python operations (`uv run pytest`)
- Use Make for common tasks (`make test`, `make validate`)
- Run `make check-all` before commit
- Update docs when changing functionality

### Git Workflow

**NEVER**:
- Force push to main/master
- Commit secrets or credentials
- Skip commit message quality
- Bypass CI/CD checks

**ALWAYS**:
- Write clear commit messages
- Include Co-Authored-By for AI assistance
- Let CI/CD run before merge
- Follow conventional commits (optional)

---

## 🎯 Quality Gates

### Pre-commit

**Must pass before commit**:
1. ✅ All skills validate (skills-ref)
2. ✅ All tests pass (pytest)
3. ✅ Code is formatted (black + ruff)
4. ✅ No linting errors (ruff)

**Command**: `make check-all`

### CI/CD

**Must pass before merge**:
1. ✅ All tests pass
2. ✅ All skills validate
3. ✅ Code formatting correct
4. ✅ No linting errors
5. ✅ XML prompts generate correctly
6. ✅ Token benchmarks run

**Workflow**: `.github/workflows/validate.yml`

### Release

**Must pass before release**:
1. ✅ All quality gates pass
2. ✅ Documentation updated
3. ✅ CHANGELOG.md updated
4. ✅ Version bumped in pyproject.toml
5. ✅ Token benchmarks show 99% reduction

---

## 📊 Key Metrics

### Token Reduction

**Target**: 99% reduction
**Current**: 99% (150k → 1.5k tokens)

**Measurement**: `make benchmark`

### Agent Skills Compliance

**Target**: 100% skills validated
**Current**: 17/17 (100%)

**Measurement**: `make validate`

### Test Coverage

**Target**: >80%
**Current**: TBD (run `make test-coverage`)

**Measurement**: `pytest --cov=wfc`

### Code Quality

**Target**: No linting errors
**Current**: 0 errors

**Measurement**: `make lint`

---

## 🔄 Development Workflow

### Feature Development

1. **Create branch**: `git checkout -b feature/name`
2. **Develop**: Make changes, write tests
3. **Check**: `make check-all`
4. **Commit**: Clear message with Co-Authored-By
5. **Push**: Let CI/CD run
6. **Merge**: After CI/CD passes

### Bug Fixes

1. **Write test**: Reproduce bug
2. **Fix**: Minimum necessary change
3. **Verify**: Test passes, `make check-all`
4. **Commit**: Reference issue number
5. **Merge**: After CI/CD passes

### Documentation

1. **Update**: Keep docs in sync with code
2. **Examples**: Add usage examples
3. **Validation**: Run `make validate` if changing skills
4. **Commit**: Document changes in commit message

---

## 🚀 Release Process

### Version Bumping

**Semantic Versioning**: MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. ✅ All quality gates pass
2. ✅ CHANGELOG.md updated
3. ✅ Version bumped in pyproject.toml
4. ✅ Documentation updated
5. ✅ Token benchmarks run
6. ✅ All skills validated
7. ✅ Git tag created
8. ✅ PyPI package published (future)

---

## 📚 References

### Documentation

- **CLAUDE.md** - Session guidance for Claude Code
- **QUICKSTART.md** - Get started in 5 minutes
- **CONTRIBUTING.md** - How to contribute
- **docs/reference/AGENT_SKILLS_COMPLIANCE.md** - Compliance details

### Code

- **wfc/scripts/personas/** - Persona system
- **wfc/scripts/skills/** - Skill implementations
- **wfc/references/** - Progressive disclosure docs
- **~/.claude/skills/wfc-*/** - Installed skills

### Validation

- **skills-ref**: ~/repos/agentskills/skills-ref
- **Command**: `make validate`

---

**This is World Fucking Class.** 🚀
