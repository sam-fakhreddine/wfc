# EARS Example: OAuth2 Authentication

This example shows how WFC uses EARS format throughout the planning process for an OAuth2 authentication feature.

## Initial Requirement

> "Add OAuth2 login with JWT tokens, refresh token rotation, and account lockout after failed attempts"

## Generated Planning Documents

### 1. TASKS.md (Excerpt)

```markdown
## TASK-002: Implement OAuth2 authentication flow

- **Complexity**: L
- **Dependencies**: [TASK-001]
- **Properties**: [PROP-001, PROP-002, PROP-003]
- **Files**: src/auth/oauth2.py, src/auth/jwt_handler.py, src/auth/token_rotation.py
- **Description**: Implement OAuth2 authentication with JWT tokens and refresh token rotation
- **Acceptance Criteria**:
  - [ ] WHEN user submits OAuth2 credentials, the system shall validate against OAuth provider
  - [ ] WHEN validation succeeds multiple times, behavior is consistent
  - [ ] WHEN validation does NOT occur, no action is taken
  - [ ] Implementation is testable and verifiable
  - [ ] Edge cases are handled correctly

## TASK-003: Implement JWT token issuance

- **Complexity**: M
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-001, PROP-004]
- **Files**: src/auth/jwt_handler.py
- **Description**: Issue JWT access and refresh tokens upon successful authentication
- **Acceptance Criteria**:
  - [ ] WHEN authentication succeeds, the system shall issue JWT access token
  - [ ] WHEN authentication succeeds multiple times, behavior is consistent
  - [ ] WHEN authentication does NOT occur, no action is taken
  - [ ] Implementation is testable and verifiable
  - [ ] Edge cases are handled correctly

## TASK-004: Implement token refresh mechanism

- **Complexity**: M
- **Dependencies**: [TASK-003]
- **Properties**: [PROP-005]
- **Files**: src/auth/token_rotation.py
- **Description**: Implement secure token refresh with rotation
- **Acceptance Criteria**:
  - [ ] WHILE access token is valid, the system shall authorize API requests
  - [ ] WHEN access token becomes false, the action stops
  - [ ] WHILE access token is valid, the action is continuous
  - [ ] Implementation is testable and verifiable
  - [ ] Edge cases are handled correctly

## TASK-005: Implement account lockout

- **Complexity**: M
- **Dependencies**: [TASK-002]
- **Properties**: [PROP-006]
- **Files**: src/auth/lockout_handler.py
- **Description**: Lock accounts after multiple failed login attempts
- **Acceptance Criteria**:
  - [ ] IF login fails 3 times, THEN the system shall lock account for 15 minutes
  - [ ] IF login fails 3 times is prevented, system logs the attempt
  - [ ] System recovers gracefully from login fails 3 times
  - [ ] Implementation is testable and verifiable
  - [ ] Edge cases are handled correctly
```

---

### 2. PROPERTIES.md (Complete)

```markdown
# Formal Properties

Properties that must hold across the implementation.

**Format**: Using [EARS](https://alistairmavin.com/ears/) (Easy Approach to Requirements Syntax)

---

## PROP-001: SAFETY

- **EARS Statement**: IF unauthorized token access attempted, THEN the OAuth2 authentication system shall prevent and log violation
- **Original**: Unauthenticated users must never access protected resources
- **Rationale**: Security requirement - prevent unauthorized access
- **Priority**: critical
- **Observables**: auth_failures, unauthorized_access_attempts, token_validation_errors

## PROP-002: SAFETY

- **EARS Statement**: IF invalid OAuth provider credentials submitted, THEN the OAuth2 authentication system shall prevent and log violation
- **Original**: Invalid OAuth provider credentials must be rejected
- **Rationale**: Security requirement - prevent credential stuffing attacks
- **Priority**: critical
- **Observables**: invalid_credential_attempts, oauth_provider_failures

## PROP-003: INVARIANT

- **EARS Statement**: WHILE system is running, the OAuth2 authentication system shall maintain JWT tokens are cryptographically signed
- **Original**: JWT tokens are cryptographically signed
- **Rationale**: Security requirement - prevent token tampering
- **Priority**: high
- **Observables**: token_signature_validation_count, unsigned_token_rejections

## PROP-004: LIVENESS

- **EARS Statement**: WHEN required condition occurs, the OAuth2 authentication system shall Token issuance completes within 500ms
- **Original**: Token issuance completes within 500ms
- **Rationale**: Performance requirement - maintain responsive authentication
- **Priority**: high
- **Observables**: token_issuance_latency_p99, token_generation_timeouts

## PROP-005: STATE_DRIVEN

- **EARS Statement**: WHILE refresh token is valid, the OAuth2 authentication system shall allow token refresh
- **Original**: Refresh tokens can be used to obtain new access tokens
- **Rationale**: User requirement - maintain session without re-authentication
- **Priority**: medium
- **Observables**: token_refresh_success_count, token_refresh_failures

## PROP-006: UNWANTED

- **EARS Statement**: IF account lockout triggered, THEN the OAuth2 authentication system shall prevent and log violation
- **Original**: Accounts locked after 3 failed login attempts
- **Rationale**: Security requirement - prevent brute force attacks
- **Priority**: critical
- **Observables**: account_lockouts, lockout_duration, failed_login_attempts
```

---

### 3. TEST-PLAN.md (Excerpt)

```markdown
# Test Plan

## Testing Strategy

**Testing Approach**: TDD with property-based tests
**Coverage Target**: 90%

### Test Pyramid
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user flows

---

## Test Cases

### TEST-001: Verify SAFETY: Unauthorized token access prevention

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-001
- **Description**: Test that unauthorized token access attempted is prevented
- **Steps**:
  1. Setup test environment
  2. Attempt to trigger: unauthorized token access attempted
  3. Verify system prevents the condition
  4. Verify appropriate error/log is generated
  5. Verify system state remains consistent
- **Expected**: SAFETY property holds under all conditions

### TEST-002: Verify INVARIANT: JWT signature validation

- **Type**: integration
- **Related Task**: TASK-003
- **Related Property**: PROP-003
- **Description**: Test that JWT tokens are cryptographically signed
- **Steps**:
  1. Setup test environment
  2. Execute multiple operations
  3. After each operation, verify: JWT tokens are cryptographically signed
  4. Test under concurrent access
  5. Verify invariant maintained throughout
- **Expected**: INVARIANT property holds under all conditions

### TEST-003: Verify LIVENESS: Token issuance performance

- **Type**: integration
- **Related Task**: TASK-004
- **Related Property**: PROP-004
- **Description**: Test that Token issuance completes within 500ms
- **Steps**:
  1. Setup test environment
  2. Trigger required condition
  3. Wait for: Token issuance completes within 500ms
  4. Verify action completes within timeout
  5. Verify no deadlock or starvation
- **Expected**: LIVENESS property holds under all conditions

### TEST-004: Verify OAuth2 authentication flow

- **Type**: integration
- **Related Task**: TASK-002
- **Related Property**: PROP-002
- **Description**: Verify implementation of: OAuth2 authentication with JWT tokens
- **Steps**:
  1. Setup test environment
  2. Trigger event: user submits OAuth2 credentials
  3. Verify action: validate against OAuth provider
  4. Test with event occurring multiple times
  5. Test with event NOT occurring (no action expected)
- **Expected**: Feature works as specified in EARS requirement

### TEST-005: Verify token refresh mechanism

- **Type**: unit
- **Related Task**: TASK-004
- **Related Property**: PROP-005
- **Description**: Verify implementation of: Refresh token rotation
- **Steps**:
  1. Setup test environment
  2. Establish state: access token is valid
  3. Verify action occurs: authorize API requests
  4. Exit state: access token is valid
  5. Verify action stops when state changes
- **Expected**: Feature works as specified in EARS requirement

### TEST-006: Verify account lockout

- **Type**: integration
- **Related Task**: TASK-005
- **Related Property**: PROP-006
- **Description**: Verify implementation of: Account lockout after failed attempts
- **Steps**:
  1. Setup test environment
  2. Attempt condition: login fails 3 times
  3. Verify prevention: lock account for 15 minutes
  4. Verify system logs the attempt
  5. Verify system recovers gracefully
- **Expected**: Feature works as specified in EARS requirement

### TEST-007: End-to-end OAuth2 flow

- **Type**: e2e
- **Related Task**: TASK-002, TASK-003, TASK-004, TASK-005
- **Related Property**: All properties
- **Description**: Complete user authentication flow from login to token refresh
- **Steps**:
  1. User navigates to login page
  2. User clicks "Login with OAuth2"
  3. User redirected to OAuth provider
  4. User authorizes application
  5. System receives OAuth2 callback
  6. System validates credentials
  7. System issues JWT tokens
  8. User makes authenticated API requests
  9. Access token expires
  10. System refreshes token using refresh token
  11. User continues using application
- **Expected**: Complete flow works end-to-end with all properties satisfied
```

---

## Key Observations

### 1. Clarity and Testability

Each requirement is **unambiguous**:

- **WHEN** user submits credentials → clear trigger
- **WHILE** token is valid → clear condition
- **IF** login fails 3 times → clear threshold

This makes test generation **deterministic**.

---

### 2. Complete Specification

EARS forces you to specify:

- What happens when trigger occurs
- What happens when trigger does NOT occur
- What happens when state changes
- Edge cases and error conditions

Example:

```
WHEN validation succeeds multiple times, behavior is consistent
WHEN validation does NOT occur, no action is taken
```

---

### 3. Property-to-Test Mapping

Each property type maps to specific test patterns:

| Property Type | Test Pattern |
|---------------|--------------|
| SAFETY | Verify prevention + logging + recovery |
| LIVENESS | Verify action completes + timeout + no deadlock |
| INVARIANT | Verify maintained across operations + concurrent access |
| PERFORMANCE | Verify within bounds + under load |

This enables **automated test generation** from EARS requirements.

---

### 4. Traceability

Clear relationships:

- TASK-002 → PROP-001, PROP-002, PROP-003
- PROP-001 → TEST-001
- TEST-001 → Specific test steps derived from EARS

You can trace from requirement → property → task → test → code.

---

## Benefits Demonstrated

1. **No ambiguity** - "WHEN user submits credentials" is clearer than "user authentication"
2. **Easier testing** - Test steps derive mechanically from EARS format
3. **Better coverage** - EARS forces consideration of all conditions
4. **Automated generation** - WFC generates EARS format automatically

---

**This is World Fucking Class.**

*Clear requirements. Automated test derivation. Complete traceability.*
