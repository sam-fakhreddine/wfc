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
