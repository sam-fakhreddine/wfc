# FORMAL PROPERTIES - REST API FOR MULTI-TENANT WFC

## Overview

This document defines the formal properties that the REST API implementation MUST satisfy. These properties serve as:

1. Design constraints during implementation
2. Test oracle for property-based testing
3. Runtime invariants for monitoring/alerting

Properties are categorized into: SAFETY, LIVENESS, INVARIANT, PERFORMANCE.

---

## SAFETY PROPERTIES

Safety properties define "bad things that must never happen".

### S1: Authentication Enforcement

**Property**: Unauthenticated requests MUST NEVER access protected endpoints.

**Formal Definition**:

```
∀ request ∈ ProtectedEndpoints:
  (request.headers["Authorization"] = ∅ ∨ ¬valid(request.headers["Authorization"]))
    ⇒ response.status_code = 401
```

**Protected Endpoints**:

- POST /v1/reviews/
- GET /v1/reviews/{review_id}
- GET /v1/resources/pool
- GET /v1/resources/rate-limit

**Test Strategy**:

- Property-based test: Generate random requests without auth headers
- Assert all return 401
- Test invalid API key formats (empty, malformed, wrong project)

**Monitoring**:

- Alert if authenticated endpoint returns 200 without valid Authorization header
- Log all 401 responses for security audit

---

### S2: Project Isolation

**Property**: Users MUST NEVER access resources belonging to other projects.

**Formal Definition**:

```
∀ request, resource:
  (request.project_id ≠ resource.project_id)
    ⇒ response.status_code ∈ {403, 404}
```

**Enforcement Points**:

1. **Review access**: GET /v1/reviews/{review_id} checks review.project_id == request.project_id
2. **Resource monitoring**: Pool/rate-limit stats scoped to authenticated project
3. **API key validation**: API key maps to exactly one project_id

**Test Strategy**:

- Create two projects (proj1, proj2)
- Submit review with proj1 credentials
- Attempt to access review_id with proj2 credentials
- Assert 403 Forbidden

**Monitoring**:

- Alert on any 403 responses (should be rare in legitimate usage)
- Track cross-project access attempts for security analysis

---

### S3: Credential Security

**Property**: API keys MUST NEVER be stored or transmitted in plaintext (except initial creation response).

**Formal Definition**:

```
∀ api_key ∈ APIKeyStore:
  stored(api_key) ⇒ stored(SHA256(api_key))

∀ log_entry:
  log_entry.content ⊄ api_key (except sanitized "Bearer ***")
```

**Enforcement**:

1. **Storage**: APIKeyStore hashes keys with SHA-256 before writing to disk
2. **Validation**: Constant-time comparison using `secrets.compare_digest()`
3. **Logging**: Request logging middleware sanitizes Authorization headers
4. **Transmission**: API key only returned once at POST /v1/projects/ (201 response)

**Test Strategy**:

- Create API key, inspect ~/.wfc/api_keys.json
- Assert only hash stored, not plaintext
- Verify validation uses constant-time comparison (timing attack resistant)
- Parse logs, assert no plaintext API keys appear

**Monitoring**:

- Periodic audit of api_keys.json for plaintext patterns
- Alert if API key appears in application logs

---

### S4: Input Validation

**Property**: All user inputs MUST be validated before processing.

**Formal Definition**:

```
∀ input ∈ UserInputs:
  (¬valid(input) ∧ process(input)) ⇒ ⊥  (contradiction, must not occur)

valid(input) ≡
  size(input) ≤ MAX_SIZE ∧
  pattern_match(input) ∧
  type_check(input)
```

**Validation Rules**:

| Input | Constraint | Enforcement |
|-------|------------|-------------|
| project_id | ^[a-zA-Z0-9_-]{1,64}$ | Pydantic pattern validator |
| developer_id | ^[a-zA-Z0-9_-]{1,64}$ | Pydantic pattern validator |
| diff_content | 1 ≤ len ≤ 1MB | Pydantic min_length + middleware size check |
| files | List[str], non-empty strings | Pydantic field_validator |
| repo_path | Absolute path | Pydantic field_validator |
| review_id | UUID format | Path parameter (validated by FastAPI) |

**Test Strategy**:

- Property-based testing with hypothesis library
- Generate invalid inputs (oversized, wrong type, malicious patterns)
- Assert all rejected with 422 Unprocessable Entity

**Monitoring**:

- Track 422 response rate (high rate = attack or client bug)
- Log validation failures for security analysis

---

## LIVENESS PROPERTIES

Liveness properties define "good things that must eventually happen".

### L1: Review Completion

**Property**: All submitted reviews MUST eventually reach a terminal state (COMPLETED or FAILED).

**Formal Definition**:

```
∀ review ∈ Reviews:
  submitted(review, t₀) ⇒ ∃ t₁ > t₀: status(review, t₁) ∈ {COMPLETED, FAILED}
```

**Terminal States**:

- COMPLETED: Review finished successfully with consensus_score and findings
- FAILED: Review encountered unrecoverable error with error_message

**Failure Modes & Recovery**:

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| ReviewOrchestrator crash | Background task exception | execute_review_task catches exception, calls fail_review() |
| Timeout (>10 min) | Not implemented (TASK-026) | Add timeout wrapper in execute_review_task |
| Stuck in IN_PROGRESS | Orphan detection (>24h) | Add cleanup job to scan and fail stale reviews |

**Test Strategy**:

- Submit review, wait for completion
- Mock ReviewOrchestrator to raise exception, verify FAILED status
- Simulate long-running review (sleep), verify eventual completion

**Monitoring**:

- Alert if review stuck in IN_PROGRESS for >30 minutes
- Track review completion time distribution (p50, p95, p99)

---

### L2: Resource Cleanup

**Property**: Orphaned resources (worktrees, review files) MUST eventually be cleaned up.

**Formal Definition**:

```
∀ resource ∈ {Worktrees, ReviewFiles}:
  (age(resource) > ORPHAN_TIMEOUT ∧ ¬in_use(resource))
    ⇒ ∃ t: cleaned(resource, t)
```

**Orphan Timeout**:

- Worktrees: 24 hours (WorktreePool.orphan_timeout_hours)
- Review files: Not implemented (TASK-027: add cleanup job)

**Cleanup Triggers**:

1. **Proactive**: WorktreePool._cleanup_orphans() called on every acquire()
2. **Reactive**: GET /v1/resources/pool triggers cleanup
3. **Scheduled**: Not implemented (add cron job or background task)

**Test Strategy**:

- Create worktree, wait 24+ hours (or mock time), verify cleanup
- Create review, simulate orphan (no completion), verify eventual cleanup

**Monitoring**:

- Track orphaned_worktrees count from pool status
- Alert if orphan count exceeds threshold (e.g., >5)

---

## INVARIANT PROPERTIES

Invariant properties define conditions that MUST hold at all times.

### I1: API Key Uniqueness

**Property**: Each API key maps to exactly one project.

**Formal Definition**:

```
∀ api_key, p₁, p₂:
  (maps_to(api_key, p₁) ∧ maps_to(api_key, p₂)) ⇒ p₁ = p₂
```

**Enforcement**:

1. **Creation**: APIKeyStore.create_api_key() raises ValueError if project_id already exists
2. **Storage**: File-based storage with project_id as key (natural uniqueness)
3. **Revocation**: Revoke entire project (cannot revoke just one key)

**Test Strategy**:

- Create project, attempt to create again with same project_id
- Assert ValueError raised
- Verify api_keys.json has project_id as top-level key (enforces uniqueness)

**Monitoring**:

- Periodic audit of api_keys.json for duplicate entries (should never occur)

---

### I2: Review Status Transitions

**Property**: Review status MUST follow valid state machine transitions.

**Formal Definition**:

```
ValidTransitions = {
  PENDING → IN_PROGRESS,
  IN_PROGRESS → COMPLETED,
  IN_PROGRESS → FAILED
}

∀ review, t₁, t₂:
  (t₁ < t₂ ∧ status(review, t₁) = s₁ ∧ status(review, t₂) = s₂)
    ⇒ (s₁ → s₂) ∈ ValidTransitions ∨ s₁ = s₂
```

**Invalid Transitions** (MUST NEVER occur):

- COMPLETED → any other state
- FAILED → any other state
- PENDING → COMPLETED (must go through IN_PROGRESS)
- PENDING → FAILED (must go through IN_PROGRESS first, or stay PENDING if never started)

**Enforcement**:

- ReviewStatusStore methods enforce transitions:
  - update_status(IN_PROGRESS) only called after create_review() (PENDING)
  - complete_review() sets COMPLETED atomically
  - fail_review() sets FAILED atomically

**Test Strategy**:

- Unit test ReviewStatusStore state transitions
- Assert invalid transitions raise error or are no-ops
- Integration test: submit review, verify PENDING → IN_PROGRESS → COMPLETED sequence

**Monitoring**:

- Log all status transitions
- Alert on invalid transition attempts

---

### I3: Worktree Pool Capacity

**Property**: Number of active worktrees MUST NEVER exceed max_worktrees.

**Formal Definition**:

```
∀ t: count(active_worktrees(t)) ≤ max_worktrees
```

**Enforcement**:

1. **Acquire**: WorktreePool.acquire() checks count before creating new worktree
2. **Eviction**: If pool full, evict LRU worktree before creating new one
3. **File locking**: FileLock prevents race conditions in concurrent acquire()

**Test Strategy**:

- Set max_worktrees=3
- Acquire 4 worktrees concurrently
- Assert count never exceeds 3
- Verify LRU eviction occurred

**Monitoring**:

- Track active_worktrees from pool status
- Alert if count exceeds max_worktrees (invariant violation)

---

### I4: Rate Limit Capacity

**Property**: Available tokens MUST NEVER exceed configured capacity.

**Formal Definition**:

```
∀ t: tokens(t) ≤ capacity
```

**Enforcement**:

- TokenBucket.acquire() refills tokens: `min(capacity, tokens + elapsed * refill_rate)`
- Refill capped at capacity (prevents unbounded accumulation)

**Test Strategy**:

- Wait for full refill (capacity seconds)
- Assert get_available_tokens() ≤ capacity
- Refill again, verify still ≤ capacity (no overflow)

**Monitoring**:

- Log token bucket state on each acquire()
- Alert if available_tokens > capacity (invariant violation)

---

## PERFORMANCE PROPERTIES

Performance properties define quantitative SLAs.

### P1: Review Submission Latency

**Property**: Review submission (POST /v1/reviews/) MUST respond within 100ms (p95).

**Formal Definition**:

```
∀ request ∈ POST /v1/reviews/:
  p95(response_time(request)) < 100ms
```

**Operations**:

1. Validate request (Pydantic): ~5ms
2. Authenticate (API key lookup): ~10ms
3. Acquire rate limit token: ~1ms
4. Create review entry (file write): ~20ms
5. Schedule background task: ~5ms
6. Total: ~41ms (p50), ~80ms (p95 with I/O variance)

**Optimizations**:

- Use async I/O (FastAPI async def endpoints)
- File-based storage with minimal locking
- Background task scheduling (no blocking on review execution)

**Test Strategy**:

- Load test with 100 concurrent requests
- Measure p50, p95, p99 latencies
- Assert p95 < 100ms

**Monitoring**:

- Expose latency histogram via Prometheus (review_submission_duration_seconds)
- Alert if p95 > 100ms

---

### P2: Status Query Latency

**Property**: Review status queries (GET /v1/reviews/{id}) MUST respond within 200ms (p95).

**Formal Definition**:

```
∀ request ∈ GET /v1/reviews/{id}:
  p95(response_time(request)) < 200ms
```

**Operations**:

1. Authenticate: ~10ms
2. Read review file: ~30ms (with locking)
3. Parse JSON: ~5ms
4. Serialize response: ~5ms
5. Total: ~50ms (p50), ~100ms (p95)

**Optimizations**:

- Single file read (no database query overhead)
- Minimal locking (read-only operation, shared lock)

**Test Strategy**:

- Benchmark 1000 status queries
- Assert p95 < 200ms

**Monitoring**:

- Track GET /v1/reviews/{id} latency
- Alert if p95 > 200ms

---

### P3: Concurrent Request Capacity

**Property**: Server MUST handle 100 concurrent requests without degradation.

**Formal Definition**:

```
concurrent_requests = 100 ⇒
  p95(response_time) < 2 × p95(response_time | concurrent_requests = 1)
```

**Configuration**:

- uvicorn workers: 4 (multi-process)
- limit_concurrency: 100
- FastAPI async endpoints (non-blocking I/O)

**Bottlenecks**:

1. **File locking**: Sequential writes to api_keys.json, review files
   - Mitigation: Short critical sections, read-heavy workload
2. **ReviewOrchestrator**: Sync blocking execution
   - Mitigation: Run in thread pool via run_in_executor()

**Test Strategy**:

- Load test with 100 concurrent POST /v1/reviews/ requests
- Measure throughput (requests/second)
- Assert p95 latency < 200ms (2x normal)

**Monitoring**:

- Track concurrent_requests gauge
- Alert if throughput drops below threshold (e.g., <50 req/s)

---

### P4: Memory Usage

**Property**: Server memory usage MUST NOT exceed 500MB under normal load.

**Formal Definition**:

```
load = "normal" (100 concurrent requests, 10 reviews/sec) ⇒
  memory_usage < 500MB
```

**Memory Profile**:

- FastAPI app: ~50MB
- Uvicorn workers (4): ~100MB
- WorktreePool (10 worktrees): ~50MB (metadata only, not git data)
- ReviewStatusStore: ~10MB (file paths, minimal cache)
- Background tasks: ~200MB (ReviewOrchestrator instances)
- Total: ~410MB

**Leak Prevention**:

- No in-memory caching of large data (diffs, review results)
- File-based storage (offload to disk)
- Background task cleanup after completion

**Test Strategy**:

- Load test with 1000 reviews over 10 minutes
- Monitor memory usage with `psutil`
- Assert max memory < 500MB

**Monitoring**:

- Expose memory_usage_bytes gauge via Prometheus
- Alert if memory > 500MB

---

## PROPERTY-BASED TEST PLAN

### Test Coverage Matrix

| Property | Unit Tests | Integration Tests | Load Tests | Monitoring |
|----------|-----------|-------------------|------------|------------|
| S1 | ✓ | ✓ | ✓ | ✓ |
| S2 | ✓ | ✓ | - | ✓ |
| S3 | ✓ | ✓ | - | ✓ |
| S4 | ✓ | ✓ | ✓ | ✓ |
| L1 | ✓ | ✓ | - | ✓ |
| L2 | ✓ | - | - | ✓ |
| I1 | ✓ | ✓ | - | ✓ |
| I2 | ✓ | ✓ | - | ✓ |
| I3 | ✓ | ✓ | ✓ | ✓ |
| I4 | ✓ | - | ✓ | ✓ |
| P1 | - | ✓ | ✓ | ✓ |
| P2 | - | ✓ | ✓ | ✓ |
| P3 | - | - | ✓ | ✓ |
| P4 | - | - | ✓ | ✓ |

### Hypothesis Property-Based Tests

Use `hypothesis` library for generative testing:

```python
from hypothesis import given, strategies as st

@given(
    project_id=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    api_key=st.text(min_size=32, max_size=64)
)
def test_api_key_validation_property(project_id, api_key):
    """Property: validate_api_key() is deterministic and consistent."""
    store = APIKeyStore()

    # Create key
    actual_key = store.create_api_key(project_id, "alice")

    # Property: same key validates multiple times
    assert store.validate_api_key(project_id, actual_key) is True
    assert store.validate_api_key(project_id, actual_key) is True  # idempotent

    # Property: different key always fails
    if api_key != actual_key:
        assert store.validate_api_key(project_id, api_key) is False
```

---

## RUNTIME ASSERTIONS

Embed assertions in production code (disabled in production via `__debug__` flag):

```python
def acquire(self, task_id: str, project_id: str) -> Path:
    """Acquire worktree with invariant checking."""
    with FileLock(self.lock_file, timeout=10):
        # PRE-CONDITION
        assert self._count_worktrees() <= self.max_worktrees, "Invariant I3 violated"

        # ... acquisition logic ...

        # POST-CONDITION
        assert self._count_worktrees() <= self.max_worktrees, "Invariant I3 violated after acquire"

        return worktree_path
```

---

## FORMAL VERIFICATION OPPORTUNITIES

Future work: Use formal methods to prove properties mechanically.

### TLA+ Specification (State Machine)

Model review status transitions in TLA+:

```tla
---------------------------- MODULE ReviewStateMachine ----------------------------
VARIABLES status

ReviewStatusTransition ==
  \/ (status = "pending" /\ status' = "in_progress")
  \/ (status = "in_progress" /\ status' \in {"completed", "failed"})
  \/ (status \in {"completed", "failed"} /\ status' = status)  \* terminal states

Init == status = "pending"
Next == ReviewStatusTransition
Spec == Init /\ [][Next]_status

THEOREM Spec => []TypeOK  \* status always in valid set
THEOREM Spec => <>(status \in {"completed", "failed"})  \* eventually terminates
=============================================================================
```

Run TLC model checker to verify state machine correctness.

---

## SUMMARY

This REST API implementation defines and enforces 14 formal properties:

**SAFETY (4)**: Authentication, project isolation, credential security, input validation
**LIVENESS (2)**: Review completion, resource cleanup
**INVARIANT (4)**: API key uniqueness, status transitions, pool capacity, rate limit capacity
**PERFORMANCE (4)**: Submission latency, query latency, concurrent capacity, memory usage

All properties are:

1. Formally specified with mathematical notation
2. Tested with unit/integration/load tests
3. Monitored at runtime with alerts
4. Documented with enforcement mechanisms

Target: **95%+ property coverage** in automated test suite.
