---
name: wfc-consensus-review
description: Multi-agent consensus code review using specialized expert personas. Automatically selects 5 relevant experts from 54 reviewers (security, architecture, performance, quality, domain specialists) to analyze code and reach consensus. Use when user requests code review, PR analysis, security assessment, or quality checks. Triggers on "review this code", "check for security issues", "analyze this PR", "is this code good", or explicit /wfc-consensus-review. Ideal for feature implementations, refactoring, API changes, and security-sensitive code. Not for simple typo fixes, documentation-only changes, or trivial updates.
license: MIT
user-invocable: true
disable-model-invocation: false
argument-hint: [task_id or path]
---

# WFC:CONSENSUS-REVIEW - Multi-Agent Consensus Code Review

Four specialized agents review code and reach consensus decision.

## What It Does

1. **Code Review Agent (CR)** - Correctness, readability, maintainability
2. **Security Agent (SEC)** - Security vulnerabilities, auth/authz
3. **Performance Agent (PERF)** - Performance issues, scalability
4. **Complexity Agent (COMP)** - Complexity, architecture, ELEGANT principles
5. **Consensus Algorithm** - Weighted voting with veto power

**Enhanced with Systematic Checklist**: Each reviewer follows the 6-step review methodology from CHECKLIST.md (Understand Context → Functionality → Quality → Security → Performance → Tests) to ensure comprehensive, consistent reviews.

## Usage

```bash
# Review specific task
/wfc-consensus-review TASK-001

# Review files directly
/wfc-consensus-review path/to/code

# With options
/wfc-consensus-review TASK-001 --properties PROP-001,PROP-002
```

## Agent Weighting

- **Security (SEC)**: 35% - Highest priority
- **Code Review (CR)**: 30% - Correctness
- **Performance (PERF)**: 20% - Scalability
- **Complexity (COMP)**: 15% - Maintainability

## Consensus Rules

1. **All agents must pass** (score >= 7/10)
2. **Overall score** = weighted average
3. **Any critical severity** = automatic fail
4. **Overall score >= 7.0** required to pass

## Review Methodology

Each reviewer follows the systematic 6-step checklist (see `CHECKLIST.md`):

### 1. UNDERSTAND CONTEXT
- Read task description, acceptance criteria, properties
- Understand the "why" behind changes
- Review test strategy

### 2. REVIEW FUNCTIONALITY
- Verify acceptance criteria met
- Check edge case handling
- Validate error handling and input validation

### 3. REVIEW CODE QUALITY
- Readability and naming conventions
- ELEGANT principles compliance
- SOLID/DRY principles
- Function size and complexity

### 4. REVIEW SECURITY
- Input validation, SQL injection, XSS prevention
- Authentication/authorization checks
- No hardcoded secrets
- Sensitive data protection

### 5. REVIEW PERFORMANCE
- N+1 query prevention
- Algorithm efficiency
- Memory management
- Appropriate caching

### 6. REVIEW TESTS
- Coverage of happy path and edge cases
- Property verification (SAFETY, LIVENESS, etc.)
- Test quality and independence

**Reviewer-Specific Focus**:
- **CR**: Steps 2 (Functionality), 3 (Quality), 6 (Tests)
- **SEC**: Steps 2 (Input validation), 4 (Security)
- **PERF**: Steps 5 (Performance), 6 (Performance tests)
- **COMP**: Step 3 (Complexity, ELEGANT principles)

## Output

### Review Report (REVIEW-TASK-XXX.md)

```markdown
# Code Review Report: TASK-001

**Status**: ✅ APPROVED
**Overall Score**: 8.5/10

---

## Agent Reviews

### ✅ CR: Code Review
**Score**: 8.5/10
**Summary**: Code is well-structured
**Comments**: 2

### ✅ SEC: Security
**Score**: 9.0/10
**Summary**: No critical security issues
**Comments**: 1

### ✅ PERF: Performance
**Score**: 8.0/10
**Summary**: Performance looks acceptable
**Comments**: 1

### ✅ COMP: Complexity
**Score**: 9.5/10
**Summary**: Code is ELEGANT
**Comments**: 1

---

## Detailed Comments

### MEDIUM: src/auth.py:45
**Message**: Consider extracting to separate function
**Suggestion**: Split large function

---

## Consensus

✅ APPROVED: Good quality with minor suggestions
```

## Integration with WFC

### Called By
- `wfc-implement` - After agent completes TDD workflow

### Consumes
- Task files (from git worktree)
- PROPERTIES.md (formal properties to verify)
- Test results (from TDD workflow)

### Produces
- Review report (REVIEW-{task_id}.md)
- Consensus decision (pass/fail)
- Detailed comments per file/line

## Configuration

```json
{
  "review": {
    "min_overall_score": 7.0,
    "require_all_agents_pass": true,
    "fail_on_critical": true,
    "agent_weights": {
      "CR": 0.3,
      "SEC": 0.35,
      "PERF": 0.2,
      "COMP": 0.15
    }
  }
}
```

## Philosophy

**ELEGANT**: Simple agent logic, clear consensus rules
**MULTI-TIER**: Agents (logic) separated from CLI (presentation)
**PARALLEL**: Agents can run concurrently (future optimization)
