# EARS Integration in WFC

**EARS** (Easy Approach to Requirements Syntax) is integrated into WFC's planning system to generate clear, testable requirements.

## What is EARS?

EARS provides five structured templates for writing requirements that are:
- **Unambiguous** - Clear trigger/action relationships
- **Testable** - Easy to derive test cases from
- **Complete** - Forces specification of conditions
- **Consistent** - Same format across all requirements

Developed by Rolls-Royce and Airbus for safety-critical systems.

## The 5 EARS Templates

### 1. Ubiquitous (Always Active)
```
The <system> shall <action>
```
**Example**: *The authentication system shall encrypt passwords using bcrypt*

**Use when**: Requirement applies universally, no conditions

---

### 2. Event-Driven (Triggered by Event)
```
WHEN <trigger>, the <system> shall <action>
```
**Example**: *WHEN user clicks login button, the system shall validate credentials*

**Use when**: Action occurs in response to specific event

---

### 3. State-Driven (Depends on State)
```
WHILE <state>, the <system> shall <action>
```
**Example**: *WHILE session is active, the system shall refresh tokens every 15 minutes*

**Use when**: Action continues while condition holds

---

### 4. Optional Feature (Conditional Capability)
```
WHERE <feature>, the <system> shall <action>
```
**Example**: *WHERE 2FA is enabled, the system shall require OTP verification*

**Use when**: Feature is optional/configurable

---

### 5. Unwanted Behavior (Constraints/Prevention)
```
IF <condition>, THEN the <system> shall <action>
```
**Example**: *IF login fails 3 times, THEN the system shall lock the account*

**Use when**: Preventing unwanted behavior or enforcing constraints

---

## EARS in WFC Planning

### wfc-plan Integration

When you run `/wfc-plan`, EARS format is automatically applied to:

1. **TASKS.md** - Acceptance criteria use EARS format
2. **PROPERTIES.md** - Formal properties mapped to EARS templates
3. **TEST-PLAN.md** - Test steps derived from EARS requirements

### Property Type → EARS Mapping

| Property Type | EARS Template | Example |
|---------------|---------------|---------|
| **SAFETY** | UNWANTED | IF unauthorized access attempted, THEN system shall deny and log |
| **LIVENESS** | EVENT_DRIVEN | WHEN health check requested, system shall respond within 100ms |
| **INVARIANT** | STATE_DRIVEN | WHILE system is running, data integrity shall be maintained |
| **PERFORMANCE** | UBIQUITOUS | The system shall respond to API calls within 200ms |

---

## Example: OAuth2 Feature

### Natural Language Requirement
```
"Add OAuth2 login with JWT tokens and refresh token rotation"
```

### Generated EARS Requirements

#### TASKS.md
```markdown
## TASK-002: Implement OAuth2 authentication

- **Acceptance Criteria**:
  - [ ] WHEN user submits OAuth2 credentials, the system shall validate against provider
  - [ ] WHEN validation succeeds, the system shall issue JWT access token
  - [ ] WHILE access token is valid, the system shall authorize API requests
  - [ ] WHERE refresh tokens are enabled, the system shall rotate tokens on refresh
  - [ ] IF refresh token is expired, THEN the system shall require re-authentication
  - [ ] Implementation is testable and verifiable
  - [ ] Edge cases are handled correctly
```

#### PROPERTIES.md
```markdown
## PROP-001: SAFETY

- **EARS Statement**: IF unauthorized token access attempted, THEN the system shall prevent and log violation
- **Original**: Unauthenticated users must never access protected resources
- **Rationale**: Security requirement - prevent unauthorized access
- **Priority**: critical
- **Observables**: auth_failures, unauthorized_access_attempts, token_validation_errors
```

#### TEST-PLAN.md
```markdown
### TEST-002: Verify OAuth2 token validation

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-001
- **Description**: Verify OAuth2 authentication flow with JWT tokens
- **Steps**:
  1. Setup test environment
  2. Trigger event: user submits valid OAuth2 credentials
  3. Verify action: JWT token issued
  4. Test with event occurring multiple times
  5. Test with event NOT occurring (no action expected)
- **Expected**: Feature works as specified in EARS requirement
```

---

## Benefits

### For Developers
- **Clear requirements** - No ambiguity about when/how features work
- **Easier testing** - Test cases derive naturally from EARS format
- **Better coverage** - EARS forces you to think about conditions

### For Reviewers
- **Consistent format** - All requirements follow same structure
- **Testability** - Can verify each requirement independently
- **Completeness** - Missing conditions become obvious

### For WFC Agents
- **Automated test generation** - EARS → test steps mapping is deterministic
- **Property verification** - Clear pass/fail criteria from EARS statements
- **Implementation guidance** - EARS requirements guide TDD workflow

---

## Usage in WFC

### Automatic (Default)

When you use `/wfc-plan`, EARS is applied automatically:

```bash
/wfc-plan

# Interview process...
# Requirements gathered...

# Generated files use EARS format:
# - plan/TASKS.md (acceptance criteria)
# - plan/PROPERTIES.md (formal properties)
# - plan/TEST-PLAN.md (test steps)
```

### Manual (Python API)

You can use EARS utilities directly:

```python
from wfc.skills.wfc_plan.ears import (
    EARSFormatter,
    EARSRequirement,
    EARSType,
    generate_acceptance_criteria_ears
)

# Parse natural language
req = EARSFormatter.parse_natural_language(
    "When user logs in, validate credentials",
    system="auth-service"
)

# Format as EARS
ears_text = EARSFormatter.format(req)
# Output: "WHEN user logs in, the auth-service shall validate credentials"

# Generate acceptance criteria
criteria = generate_acceptance_criteria_ears(
    "Refresh JWT tokens every 15 minutes while session active",
    system="auth-service"
)
# Output: List of EARS-formatted acceptance criteria
```

---

## Best Practices

### Writing EARS Requirements

1. **Be specific with triggers/states**
   - ❌ "WHEN request comes in"
   - ✅ "WHEN valid API request received"

2. **Use measurable actions**
   - ❌ "system shall handle it"
   - ✅ "system shall respond within 200ms"

3. **Include edge cases**
   - Always specify what happens when condition is false
   - Example: "WHEN login succeeds..." and "IF login fails..."

4. **Keep system name consistent**
   - Use same system name throughout related requirements
   - Example: "auth-service" not "authentication system"

### Mapping Requirements to EARS

| Keyword in Requirement | Suggested EARS Type |
|------------------------|---------------------|
| "when", "after", "on" | EVENT_DRIVEN |
| "while", "during", "as long as" | STATE_DRIVEN |
| "if", "prevent", "must not" | UNWANTED |
| "if available", "where supported" | OPTIONAL |
| (no condition) | UBIQUITOUS |

---

## References

- [EARS Official Guide](https://alistairmavin.com/ears/) - Alistair Mavin (creator)
- [NASA Systems Engineering Handbook](https://www.nasa.gov/seh/) - Requirements best practices
- [WFC Planning Documentation](../architecture/PLANNING.md) - How WFC uses EARS

---

**This is World Fucking Class.**

*Clear requirements. Testable specifications. Automated test generation.*
