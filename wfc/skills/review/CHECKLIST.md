# WFC Code Review Checklist

**Source**: Adapted from antigravity-awesome-skills/code-review-checklist
**Integration**: wfc-review multi-agent consensus system
**Philosophy**: Systematic 6-step review methodology for individual reviewers

---

## Overview

This checklist provides a systematic framework for WFC reviewers to ensure comprehensive code review before consensus. Each reviewer (CR, SEC, PERF, COMP) focuses on their domain expertise while following this structured approach.

**Key Principle**: Catch issues systematically, not randomly. A structured checklist ensures no blind spots.

---

## The 6-Step Review Process

### 1. UNDERSTAND CONTEXT

**Purpose**: Grasp the big picture before diving into code

**Questions to Answer**:
- What problem is this code solving?
- What are the acceptance criteria?
- What files were changed and why?
- What is the testing strategy?

**For WFC Reviews**:
- Read TASK-XXX description and acceptance criteria
- Review PROPERTIES.md for formal properties to verify
- Check TEST-PLAN.md for testing approach
- Understand the "why" behind changes

**Red Flags**:
- ❌ Changes without clear purpose
- ❌ Missing acceptance criteria
- ❌ No link to task/issue
- ❌ Unclear requirements

---

### 2. REVIEW FUNCTIONALITY

**Purpose**: Verify the code solves the stated problem correctly

**Core Questions**:
- ✅ Does the code solve the problem stated in the task?
- ✅ Are all acceptance criteria met?
- ✅ Does it handle edge cases correctly?
- ✅ Is error handling appropriate?
- ✅ Are inputs validated?

**Edge Cases to Consider**:
- **Null/None values**: What if input is None/null?
- **Empty collections**: What if list/dict is empty?
- **Boundary values**: Min/max values, overflow, underflow
- **Concurrent access**: Race conditions, thread safety
- **External failures**: API calls fail, database unavailable

**For WFC Reviews**:
- Verify each acceptance criterion is satisfied
- Check that formal properties (SAFETY, LIVENESS) are upheld
- Look for unhandled edge cases
- Verify error messages are clear and actionable

**Red Flags**:
- ❌ Acceptance criteria not met
- ❌ No null/boundary checks where needed
- ❌ Generic error handling (catch all exceptions)
- ❌ Incomplete logic paths
- ❌ Missing validation for user inputs

---

### 3. REVIEW CODE QUALITY

**Purpose**: Ensure code is readable, maintainable, and follows best practices

**Readability**:
- ✅ Code is easy to understand at a glance
- ✅ Variable/function names are descriptive
- ✅ Functions are focused (single responsibility)
- ✅ Comments explain "why", not "what"
- ✅ Complex logic is broken down

**Structure**:
- ✅ Functions are small (<50 lines ideal)
- ✅ Classes have clear, focused responsibilities
- ✅ No deep nesting (max 3-4 levels)
- ✅ DRY principle followed (no duplication)
- ✅ SOLID principles applied

**Naming Conventions**:
- ✅ Variables: descriptive, not abbreviated (`user_count` not `uc`)
- ✅ Functions: verb phrases (`calculate_total`, `validate_input`)
- ✅ Classes: noun phrases (`UserManager`, `PaymentProcessor`)
- ✅ Constants: UPPERCASE_WITH_UNDERSCORES
- ✅ Boolean variables: `is_`, `has_`, `can_` prefixes

**For WFC Reviews**:
- Verify ELEGANT principles (Explicit, Layered, Encapsulated, Graceful, Testable)
- Check for MULTI-TIER separation (presentation/logic/data)
- Ensure functions are focused and single-purpose
- Look for unnecessary complexity

**Red Flags**:
- ❌ Functions longer than 50-100 lines
- ❌ Unclear variable names (`x`, `temp`, `data`)
- ❌ Deep nesting (>4 levels)
- ❌ Duplicated code blocks
- ❌ God classes (too many responsibilities)
- ❌ Comments explaining what code does (code should be self-documenting)

---

### 4. REVIEW SECURITY

**Purpose**: Prevent security vulnerabilities and data leaks

**Critical Security Checks**:

**Input Validation**:
- ✅ All user inputs are validated
- ✅ SQL injection prevented (parameterized queries, ORM)
- ✅ XSS prevented (output sanitization)
- ✅ Command injection prevented (no shell execution of user input)
- ✅ Path traversal prevented (validate file paths)

**Authentication & Authorization**:
- ✅ Authentication required for protected endpoints
- ✅ Authorization checks before sensitive operations
- ✅ Session management is secure
- ✅ Password handling is secure (hashing, not plain text)
- ✅ API keys/tokens stored securely

**Data Protection**:
- ✅ Sensitive data encrypted at rest and in transit
- ✅ No hardcoded secrets (API keys, passwords)
- ✅ No sensitive data in logs
- ✅ PII (Personally Identifiable Information) handled properly
- ✅ Database credentials not in code

**For WFC Reviews**:
- Check SECURITY property verification (if present)
- Verify no secrets in code (use environment variables)
- Ensure authentication/authorization for protected operations
- Validate all external inputs

**Red Flags**:
- ❌ Hardcoded API keys, passwords, tokens
- ❌ String concatenation in SQL queries
- ❌ User input directly rendered in HTML
- ❌ No authentication on protected endpoints
- ❌ Sensitive data in logs or error messages
- ❌ Plain text password storage

---

### 5. REVIEW PERFORMANCE

**Purpose**: Ensure code scales and performs efficiently

**Database & Queries**:
- ✅ No N+1 query problems (use joins, batch loading)
- ✅ Indexes on frequently queried columns
- ✅ Pagination for large result sets
- ✅ Database connections properly managed (pooling, closing)

**Algorithms & Data Structures**:
- ✅ Appropriate algorithm complexity (avoid O(n²) if O(n log n) possible)
- ✅ Efficient data structures (dict for lookups, not list)
- ✅ No unnecessary iterations or nested loops
- ✅ Large computations cached when possible

**Memory Management**:
- ✅ No memory leaks (resources cleaned up)
- ✅ Large files processed in chunks/streams, not loaded entirely
- ✅ Objects dereferenced when no longer needed
- ✅ Avoid keeping large objects in memory unnecessarily

**Caching**:
- ✅ Frequently accessed data cached appropriately
- ✅ Cache invalidation strategy in place
- ✅ Cache keys are unique and predictable

**For WFC Reviews**:
- Check PERFORMANCE property verification (if present)
- Look for obvious inefficiencies (nested loops, repeated calculations)
- Verify appropriate data structures
- Check for resource cleanup (file handles, connections)

**Red Flags**:
- ❌ N+1 queries (loop calling database each iteration)
- ❌ Loading entire large file into memory
- ❌ Nested loops on large datasets
- ❌ No pagination on large result sets
- ❌ Repeated expensive computations
- ❌ Memory leaks (unclosed files, connections)

---

### 6. REVIEW TESTS

**Purpose**: Ensure tests adequately cover functionality and properties

**Test Coverage**:
- ✅ New code has corresponding tests
- ✅ Tests cover happy path (normal operation)
- ✅ Tests cover edge cases (null, empty, boundary values)
- ✅ Tests cover error cases (invalid input, failures)
- ✅ Coverage metrics meet project standards

**Test Quality**:
- ✅ Tests are independent (no shared state)
- ✅ Tests are deterministic (always same result)
- ✅ Tests have meaningful assertions (not just "doesn't crash")
- ✅ Test names clearly describe what they test
- ✅ Tests are fast (no unnecessary waits)

**For WFC Reviews**:
- Verify TEST-PLAN.md test cases are implemented
- Check that formal properties (SAFETY, LIVENESS) are tested
- Ensure acceptance criteria have corresponding tests
- Look for property-based tests where appropriate

**Red Flags**:
- ❌ No tests for new functionality
- ❌ Tests that only test happy path
- ❌ Tests with no assertions (smoke tests only)
- ❌ Flaky tests (pass/fail randomly)
- ❌ Tests that depend on external state
- ❌ Low coverage on critical code paths

---

## WFC-Specific Considerations

### Property Verification

For each formal property in PROPERTIES.md:

**SAFETY** (what must never happen):
- ✅ Tests demonstrate unsafe state cannot occur
- ✅ Error handling prevents unsafe conditions
- ✅ Invariants maintained throughout execution

**LIVENESS** (what must eventually happen):
- ✅ Progress guaranteed (no infinite loops, deadlocks)
- ✅ Timeouts prevent indefinite waits
- ✅ Retry logic with backoff/limits

**INVARIANT** (what must always be true):
- ✅ Assertions verify invariants at key points
- ✅ State transitions maintain invariants
- ✅ Tests check invariants hold

**PERFORMANCE** (time/resource bounds):
- ✅ Performance metrics measured
- ✅ Resource limits enforced
- ✅ No unbounded growth (memory, time, connections)

### TDD Workflow Verification

Since WFC enforces TDD:
- ✅ Tests were written before implementation (check git history if needed)
- ✅ Tests initially failed (RED phase)
- ✅ Implementation made tests pass (GREEN phase)
- ✅ Code was refactored (REFACTOR phase)
- ✅ All quality checks passed

### Systematic Debugging Verification

If bugs were fixed during implementation:
- ✅ Root cause analysis documented (WHAT, WHY, WHERE)
- ✅ Tests reproduce the bug (fail before fix)
- ✅ Fix addresses root cause, not symptom
- ✅ No trial-and-error fixes (hypothesis-driven)

---

## Best Practices for Reviewers

### DO:
✅ **Review in small batches** - Review <400 lines at a time
✅ **Read tests first** - Tests explain intent better than implementation
✅ **Run code locally** - See it work, don't just read
✅ **Ask clarifying questions** - "Why did you choose this approach?"
✅ **Be constructive** - Suggest improvements, don't just criticize
✅ **Use automated tools** - Linters, formatters, type checkers
✅ **Verify documentation** - README, API docs updated
✅ **Consider scalability** - Will this work at 10x, 100x scale?
✅ **Check for regressions** - Run full test suite
✅ **Learn from the code** - Good code reviews teach both ways

### DON'T:
❌ **Approve without reading** - Rubber-stamping helps no one
❌ **Nitpick style** - Use automated formatters for style
❌ **Be vague** - "This looks wrong" → "This could cause X because Y"
❌ **Skip context** - Understand the problem before judging the solution
❌ **Overlook security** - Security issues can't be fixed post-deployment
❌ **Ignore tests** - Untested code will break
❌ **Review when tired** - Take breaks, stay fresh
❌ **Be disrespectful** - Critique code, not people
❌ **Rush** - Quality reviews take time

---

## Reviewer-Specific Mapping

### CR (Code Review) - Focuses on:
- **Step 2**: Functionality (acceptance criteria, edge cases)
- **Step 3**: Code Quality (readability, structure, ELEGANT principles)
- **Step 6**: Tests (coverage, quality, assertions)

### SEC (Security) - Focuses on:
- **Step 2**: Input validation from Functionality
- **Step 4**: Security (authentication, authorization, data protection)
- Hardcoded secrets, SQL injection, XSS, CSRF

### PERF (Performance) - Focuses on:
- **Step 5**: Performance (queries, algorithms, memory, caching)
- **Step 6**: Performance tests and benchmarks
- Scalability considerations

### COMP (Complexity) - Focuses on:
- **Step 3**: Code Quality (complexity, structure, maintainability)
- ELEGANT principles compliance
- SOLID principles
- Architectural cleanliness

---

## Common Anti-Patterns to Catch

### Functionality Anti-Patterns:
- ❌ **Catching all exceptions** without specific handling
- ❌ **Silent failures** (errors swallowed, not logged)
- ❌ **Magic numbers** (hardcoded values without explanation)
- ❌ **Incomplete error messages** (no context for debugging)

### Security Anti-Patterns:
- ❌ **SQL injection** via string concatenation
- ❌ **Hardcoded credentials** in code
- ❌ **Missing authentication** on protected endpoints
- ❌ **Sensitive data in logs** (passwords, tokens, PII)

### Performance Anti-Patterns:
- ❌ **N+1 queries** in loops
- ❌ **Unbounded collections** (loading all records)
- ❌ **Blocking I/O** on main thread
- ❌ **No caching** for frequently accessed data

### Code Quality Anti-Patterns:
- ❌ **God classes** (too many responsibilities)
- ❌ **Premature optimization** (complex code for marginal gains)
- ❌ **Copy-paste code** (DRY violation)
- ❌ **Deep nesting** (>4 levels)
- ❌ **Unclear naming** (abbreviations, single letters)

---

## Expected Outcomes

Following this checklist:
- **30-40% more issues caught** compared to ad-hoc review
- **Consistent review quality** across all reviewers
- **Faster reviews** (structured approach reduces wasted time)
- **Better feedback** (specific, actionable, constructive)
- **Shared understanding** (all reviewers use same framework)

---

## References

- Antigravity code-review-checklist skill (source)
- WFC ELEGANT principles
- WFC formal properties methodology
- SOLID principles
- Code review best practices (Google, Microsoft)
