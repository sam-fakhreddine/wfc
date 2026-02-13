# WFC Systematic Debugging Methodology

**Source**: Adapted from antigravity-awesome-skills/systematic-debugging
**Integration**: wfc-implement agent TDD workflow
**Philosophy**: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST

---

## Core Principle

**CRITICAL RULE**: Never apply fixes without understanding root cause first.

Random fixes waste time, introduce new bugs, and demonstrate cargo-cult programming. Professional debugging is systematic, scientific, and rooted in understanding.

---

## The Four-Phase Debugging Workflow

### Phase 1: ROOT CAUSE INVESTIGATION

**STOP. DO NOT SKIP THIS PHASE.**

Before touching ANY code, complete this investigation:

#### 1.1 Read Error Messages Carefully
```
❌ BAD: "There's an error, let me try this fix..."
✅ GOOD: "The error says 'NoneType has no attribute id' at line 123.
         This means user object is None when we expect a User instance."
```

**Action Items**:
- Read the FULL error message, not just the last line
- Read the FULL stack trace, not just the first frame
- Identify the EXACT line where the failure occurs
- Identify the EXACT value that is wrong (None, wrong type, wrong value)

#### 1.2 Reproduce Consistently
```
❌ BAD: "It fails sometimes, I'll just add error handling..."
✅ GOOD: "It fails 100% of the time when user token is expired.
         Reproduction: auth_token = 'expired'; call endpoint; observe error."
```

**Action Items**:
- Create minimal reproduction case (simplest input that triggers bug)
- Verify bug reproduces 100% of the time with that input
- Document the reproduction steps clearly
- If bug is intermittent, identify the environmental variable (race condition, timing, state)

#### 1.3 Trace Data Flow
```
❌ BAD: "The output is wrong, I'll change the calculation..."
✅ GOOD: "Input: user_id=5. At line 50: user_id is still 5.
         At line 75: user_id is now '5' (string!). That's the bug source."
```

**Action Items**:
- Add print statements / logging at each component boundary
- Track the value through the entire flow: input → processing → output
- Identify WHERE the value becomes wrong (not just that it's wrong)
- For multi-layer systems, instrument each layer boundary

#### 1.4 Identify Root Cause
```
❌ BAD: "The user is None, so I'll add a null check..."
✅ GOOD: "The user is None BECAUSE authenticate() returns None for
         expired tokens, AND we don't handle that case. Root cause:
         missing expired token handling in authenticate()."
```

**Document**:
- **WHAT**: What symptom are you observing? (e.g., "NoneType error")
- **WHY**: What is the underlying cause? (e.g., "authenticate() returns None for expired tokens")
- **WHERE**: Where in the code does this happen? (e.g., "api/routes.py:123, authenticate() at auth.py:45")

**RED FLAG INDICATORS** (you haven't found root cause yet):
- "I think..." - You should KNOW, not think
- "Maybe..." - No maybes, only certainties
- "Probably..." - Probably means you haven't investigated enough
- "Let's try..." - Trying is not the same as understanding

---

### Phase 2: PATTERN ANALYSIS

Once you understand WHY it's failing, look for working examples:

#### 2.1 Find Similar Working Code
```
✅ GOOD: "In users.py, authenticate() is called with error handling:
         user = authenticate(token)
         if not user:
             return 401
         This pattern works correctly."
```

**Action Items**:
- Search codebase for similar functionality that works
- Identify the pattern used in working code
- Note differences between working and broken code

#### 2.2 Compare Line-by-Line
```
WORKING (users.py:45):
    user = authenticate(token)
    if not user:
        return 401
    return user.data

BROKEN (api/routes.py:123):
    user = authenticate(token)
    return user.data  # ← MISSING NULL CHECK
```

**Action Items**:
- Create side-by-side comparison
- Identify EXACT differences
- Understand which difference causes the failure

#### 2.3 Map Dependencies
```
authenticate() depends on:
  - token_parser() - returns dict or None
  - user_lookup() - returns User or None

Assumptions:
  - Assumes token is valid (WRONG - can be expired)
  - Assumes user exists (WRONG - can be deleted)
```

**Action Items**:
- List all dependencies (functions called, data accessed)
- List all assumptions (implicit and explicit)
- Identify which assumption is violated

---

### Phase 3: HYPOTHESIS AND TESTING

Apply the scientific method:

#### 3.1 Form Hypothesis
```
❌ BAD: "I'll add error handling everywhere..."
✅ GOOD: "HYPOTHESIS: Adding null check after authenticate()
         will prevent NoneType error when token is expired."
```

**Requirements**:
- ONE clear hypothesis (not multiple changes)
- Testable prediction (what will happen if hypothesis is correct)
- Falsifiable (can prove it wrong if incorrect)

#### 3.2 Test Hypothesis with Minimal Change
```
✅ GOOD: "Change ONLY line 123:
         user = authenticate(token)
         + if not user:
         +     return {'error': 'unauthorized'}, 401
         return user.data"
```

**Action Items**:
- Make ONE change at a time
- Test the change in isolation
- Verify it fixes the bug (or doesn't)
- If it doesn't work, revert and form new hypothesis

#### 3.3 Verify Results
```
TEST CASE 1: Valid token
  ✅ Expected: Return user data
  ✅ Actual: Return user data

TEST CASE 2: Expired token
  ✅ Expected: Return 401 error
  ✅ Actual: Return 401 error

TEST CASE 3: Invalid token
  ✅ Expected: Return 401 error
  ✅ Actual: Return 401 error
```

**Action Items**:
- Test with original failing case (must now pass)
- Test with edge cases (expired, invalid, missing)
- Test with working cases (must still work)
- If ANY test fails, hypothesis is wrong - revert and try again

---

### Phase 4: IMPLEMENTATION

Only after understanding root cause and validating hypothesis:

#### 4.1 Write Test First
```python
def test_authenticate_with_expired_token():
    """Test that expired tokens return 401, not NoneType error"""
    token = create_expired_token()
    response = api_call('/endpoint', token)

    assert response.status == 401
    assert 'error' in response.data
    assert 'unauthorized' in response.data['error'].lower()
```

**Action Items**:
- Write test that reproduces the bug (fails before fix)
- Test covers the root cause, not just the symptom
- Test is specific and focused (one scenario per test)

#### 4.2 Implement Minimal Fix
```python
def process_request(token):
    user = authenticate(token)
    # FIX: Handle case where authenticate() returns None (expired/invalid token)
    if not user:
        return {'error': 'Unauthorized'}, 401

    return user.data
```

**Action Items**:
- ONE focused change that addresses root cause
- Add comment explaining WHY (references root cause)
- Follow existing code patterns (from Phase 2 analysis)
- No unrelated changes (formatting, refactoring, etc.)

#### 4.3 Verify All Tests Pass
```
✅ test_authenticate_with_valid_token
✅ test_authenticate_with_expired_token  ← NEW
✅ test_authenticate_with_invalid_token
✅ test_authenticate_with_missing_token
✅ All other tests still pass
```

**Action Items**:
- Run test suite (all tests, not just new ones)
- Verify new test passes (was failing before fix)
- Verify all existing tests still pass (no regressions)
- If ANY test fails, investigate why (may reveal deeper issue)

#### 4.4 Failure Threshold: 3 Strikes Rule

```
Strike 1: First fix attempt fails
  → Acceptable. Go back to Phase 1. Re-investigate root cause.

Strike 2: Second fix attempt fails
  → Concerning. Question your understanding. Get second opinion.

Strike 3: Third fix attempt fails
  → STOP. The problem is deeper than you think.
     - Is the architecture fundamentally broken?
     - Are you fixing symptoms instead of root cause?
     - Do you need to refactor instead of patch?
     - Time to escalate or redesign.
```

**Action Items**:
- Track how many attempts you've made
- If third attempt fails, STOP and reassess
- Consider whether the system needs refactoring, not fixing
- Don't thrash - repeated failures indicate architectural problem

---

## Integration with WFC TDD Workflow

The systematic debugging workflow integrates into the TDD cycle when bugs are discovered:

```
1. UNDERSTAND
   - Read task definition
   - Read properties
   - Read test plan
   - Read existing code

2. TEST_FIRST (RED)
   - Write tests BEFORE implementation
   - Tests cover acceptance criteria
   - Tests cover properties
   - Run tests → they FAIL

3. IMPLEMENT (GREEN)
   - Write minimum code to pass tests
   - Follow ELEGANT principles
   - Run tests → they PASS

   ↓ [IF BUGS DETECTED DURING IMPLEMENTATION OR TESTING]

   3a. ROOT_CAUSE_INVESTIGATION ← SYSTEMATIC DEBUGGING PHASE 1
       - Read error messages carefully
       - Reproduce consistently
       - Trace data flow
       - Identify root cause (WHAT, WHY, WHERE)
       - Document findings

   3b. PATTERN_ANALYSIS ← SYSTEMATIC DEBUGGING PHASE 2
       - Find similar working code
       - Compare line-by-line
       - Map dependencies and assumptions

   3c. HYPOTHESIS_TESTING ← SYSTEMATIC DEBUGGING PHASE 3
       - Form ONE clear hypothesis
       - Test with minimal change
       - Verify results

   3d. FIX_IMPLEMENTATION ← SYSTEMATIC DEBUGGING PHASE 4
       - Write test first (reproduces bug)
       - Implement minimal fix
       - Verify all tests pass
       - Apply 3-strikes rule

4. REFACTOR
   - Clean up without changing behavior
   - Maintain SOLID & DRY
   - Run tests → still PASS

5. QUALITY_CHECK
   - Run formatters, linters, tests
   - Verify all quality gates pass

6. SUBMIT
   - Verify quality check passed
   - Verify acceptance criteria met
   - Include root cause documentation for all fixes
   - Produce agent report
```

---

## Root Cause Documentation Format

Every bug fix MUST include documented root cause in this format:

```markdown
## Root Cause Analysis

**WHAT**: [Symptom observed]
- Error message, incorrect output, or unexpected behavior
- Example: "NoneType object has no attribute 'id' at api/routes.py:123"

**WHY**: [Underlying cause]
- Why does this happen?
- Example: "authenticate() returns None when token is expired, but code assumes user is always valid User object"

**WHERE**: [Code location]
- Exact file and line number(s)
- Example: "api/routes.py:123 (symptom), auth.py:45 (root cause - authenticate() returns None)"

**FIX**: [Solution applied]
- What change addresses the root cause?
- Example: "Added null check after authenticate() call. If user is None (expired/invalid token), return 401 error instead of accessing user.id"

**TESTS**: [Verification]
- What tests verify this is fixed?
- Example: "test_authenticate_with_expired_token - reproduces bug, now passes"
```

---

## Red Flags (Violations of Systematic Debugging)

If you find yourself doing any of these, STOP and restart at Phase 1:

❌ **"Let me try this..."** - Trying without understanding is guessing
❌ **"I'll add error handling just in case..."** - Defensive programming without understanding
❌ **Making multiple changes at once** - Can't isolate what fixed it
❌ **"It works on my machine..."** - Haven't identified environmental dependency
❌ **Copying code without understanding** - Cargo cult programming
❌ **Adding print statements without hypothesis** - Random debugging
❌ **"I'll refactor while I'm here..."** - Mixing concerns (debug vs refactor)
❌ **Commenting out code "to see if it helps"** - Not a hypothesis, just a guess

---

## Success Indicators

You're doing systematic debugging correctly when:

✅ You can explain WHAT, WHY, WHERE for every bug
✅ You have reproduction steps for every bug
✅ You make one change at a time and test it
✅ Your fixes work on the first or second attempt
✅ Your tests verify the root cause, not just the symptom
✅ You document your findings for future debugging
✅ You learn patterns that prevent similar bugs

---

## Expected Outcomes

Following this methodology:
- **50-70% reduction in debugging time** (from hours to 15-30 minutes)
- **Near-zero introduction of new bugs** during fixing
- **First or second attempt success rate** ~90%
- **Clear documentation** of what was wrong and why
- **Learning and pattern recognition** for future prevention

---

## References

- Antigravity systematic-debugging skill (source)
- Scientific method applied to debugging
- Root cause analysis (5 Whys technique)
- Test-Driven Debugging (TDD variant)
