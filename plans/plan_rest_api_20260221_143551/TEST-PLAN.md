# TEST PLAN - REST API FOR MULTI-TENANT WFC

## Overview

Comprehensive test strategy for REST API implementation targeting **95%+ code coverage** and **100% property coverage** from PROPERTIES.md.

**Test Pyramid**:

- Unit tests: 60% (fast, isolated, property-focused)
- Integration tests: 30% (async client, full request/response cycle)
- Load tests: 10% (performance properties, concurrent behavior)

---

## TEST INFRASTRUCTURE

### Test Dependencies

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.27.0",
    "hypothesis>=6.100.0",
    "faker>=24.0.0",
    "locust>=2.24.0",  # Load testing
]
```

### Test Directory Structure

```
tests/
├── rest_api/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_models.py           # Pydantic model validation (TASK-011)
│   ├── test_auth.py             # API key store (TASK-012)
│   ├── test_background.py       # Review status store (TASK-013)
│   ├── test_review_endpoints.py # Review endpoints (TASK-014)
│   ├── test_project_endpoints.py # Project endpoints (TASK-015)
│   ├── test_resource_endpoints.py # Resource endpoints (TASK-016)
│   ├── test_properties.py       # Property-based tests
│   ├── test_security.py         # Security hardening
│   └── load/
│       ├── locustfile.py        # Load test scenarios
│       └── test_performance.py  # Performance property verification
```

---

## UNIT TESTS (60% of test suite)

### 1. Pydantic Model Validation (TASK-011)

**File**: `tests/rest_api/test_models.py`

**Coverage**: 100% of `wfc/servers/rest_api/models.py`

**Test Classes**:

#### TestReviewSubmitRequest

```python
def test_valid_request()
def test_empty_diff_content_fails()
def test_empty_files_allowed()
def test_non_string_files_fail()
def test_whitespace_only_files_fail()
def test_max_diff_size_enforced()
```

#### TestReviewStatusResponse

```python
def test_status_enum_validation()
def test_consensus_score_range_0_to_10()
def test_datetime_serialization()
def test_findings_list_validation()
```

#### TestProjectCreateRequest

```python
def test_valid_project_id_alphanumeric_dash_underscore()
def test_invalid_project_id_special_chars()
def test_project_id_length_1_to_64()
def test_developer_id_validation()
def test_relative_repo_path_fails()
def test_absolute_repo_path_passes()
```

#### TestReviewFinding

```python
def test_confidence_range_0_to_100()
def test_confidence_out_of_range_fails()
def test_optional_fields_allowed()
```

**Property-Based Tests** (using Hypothesis):

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1_000_000))
def test_diff_content_accepts_any_non_empty_string(diff_content):
    """Property: Any non-empty string is valid diff_content."""
    request = ReviewSubmitRequest(diff_content=diff_content, files=[])
    assert request.diff_content == diff_content

@given(st.lists(st.text(min_size=1, max_size=255)))
def test_files_accepts_list_of_strings(files):
    """Property: Any list of non-empty strings is valid files."""
    request = ReviewSubmitRequest(diff_content="diff", files=files)
    assert request.files == files
```

**Coverage Target**: 100% of models.py (all validation paths)

---

### 2. API Key Authentication (TASK-012)

**File**: `tests/rest_api/test_auth.py`

**Coverage**: 100% of `wfc/servers/rest_api/auth.py`

**Test Classes**:

#### TestAPIKeyStore

```python
def test_create_api_key_generates_unique_key()
def test_api_key_length_greater_than_30()
def test_validate_api_key_accepts_valid_key()
def test_validate_api_key_rejects_invalid_key()
def test_validate_api_key_rejects_nonexistent_project()
def test_create_duplicate_project_fails()
def test_get_developer_id_returns_correct_id()
def test_get_developer_id_nonexistent_returns_none()
def test_revoke_api_key_invalidates_key()
def test_list_projects_returns_all_projects()
def test_list_projects_empty_when_no_projects()
```

**Security Properties**:

```python
def test_api_key_stored_as_hash_not_plaintext(tmp_store):
    """Property S3: API keys never stored in plaintext."""
    api_key = tmp_store.create_api_key("proj1", "alice")

    # Read raw file
    with open(tmp_store.store_path, "r") as f:
        content = f.read()

    assert api_key not in content  # Plaintext key should not appear
    assert len(content) > 64  # Hash (SHA-256) should be present

def test_validate_uses_constant_time_comparison():
    """Property S3: API key validation uses constant-time comparison."""
    import timeit

    store = APIKeyStore()
    api_key = store.create_api_key("proj1", "alice")

    # Time validation with correct key
    time_correct = timeit.timeit(
        lambda: store.validate_api_key("proj1", api_key),
        number=1000
    )

    # Time validation with incorrect key (same length)
    wrong_key = "X" * len(api_key)
    time_wrong = timeit.timeit(
        lambda: store.validate_api_key("proj1", wrong_key),
        number=1000
    )

    # Timing difference should be minimal (< 10% variance)
    ratio = max(time_correct, time_wrong) / min(time_correct, time_wrong)
    assert ratio < 1.1, "Timing attack vulnerability detected"
```

**Concurrency Tests**:

```python
def test_concurrent_create_api_key_uses_file_locking(tmp_store):
    """Test file locking prevents race conditions."""
    import threading

    results = []
    errors = []

    def create_key(project_id):
        try:
            api_key = tmp_store.create_api_key(project_id, "alice")
            results.append((project_id, api_key))
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=create_key, args=(f"proj{i}",))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # All 10 projects should be created (no corruption)
    assert len(results) == 10
    assert len(errors) == 0
```

**Coverage Target**: 100% of auth.py

---

### 3. Review Status Store (TASK-013)

**File**: `tests/rest_api/test_background.py`

**Coverage**: 100% of `wfc/servers/rest_api/background.py`

**Test Classes**:

#### TestReviewStatusStore

```python
def test_create_review_generates_uuid()
def test_get_review_returns_pending_status()
def test_get_nonexistent_review_returns_none()
def test_update_status_changes_status()
def test_complete_review_sets_results()
def test_complete_review_sets_completed_at_timestamp()
def test_fail_review_sets_error_message()
def test_fail_review_sets_failed_status()
```

**State Machine Tests** (Property I2):

```python
def test_status_transitions_follow_state_machine(tmp_store):
    """Property I2: Status transitions follow valid state machine."""
    review_id = tmp_store.create_review("proj1", "alice")

    # Valid transition: PENDING → IN_PROGRESS
    tmp_store.update_status(review_id, ReviewStatus.IN_PROGRESS)
    review = tmp_store.get_review(review_id)
    assert review.status == ReviewStatus.IN_PROGRESS

    # Valid transition: IN_PROGRESS → COMPLETED
    tmp_store.complete_review(review_id, 8.5, True, [])
    review = tmp_store.get_review(review_id)
    assert review.status == ReviewStatus.COMPLETED

    # Invalid transition: COMPLETED → IN_PROGRESS (should be no-op or error)
    tmp_store.update_status(review_id, ReviewStatus.IN_PROGRESS)
    review = tmp_store.get_review(review_id)
    assert review.status == ReviewStatus.COMPLETED  # Status unchanged
```

**Concurrency Tests**:

```python
def test_concurrent_status_updates_use_file_locking(tmp_store):
    """Test concurrent status updates don't corrupt state."""
    import threading

    review_id = tmp_store.create_review("proj1", "alice")

    def update_status(status):
        tmp_store.update_status(review_id, status)

    threads = [
        threading.Thread(target=update_status, args=(ReviewStatus.IN_PROGRESS,))
        for _ in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Status should be IN_PROGRESS (no corruption)
    review = tmp_store.get_review(review_id)
    assert review.status == ReviewStatus.IN_PROGRESS
```

**Coverage Target**: 100% of background.py (ReviewStatusStore class)

---

### 4. FastAPI Dependencies (TASK-004)

**File**: `tests/rest_api/test_dependencies.py`

**Coverage**: 100% of `wfc/servers/rest_api/dependencies.py`

**Test Functions**:

```python
@pytest.mark.asyncio
async def test_get_project_context_valid_credentials():
    """Test dependency with valid project_id and API key."""
    # Setup
    api_key_store = APIKeyStore()
    api_key = api_key_store.create_api_key("proj1", "alice")

    # Call dependency
    context = await get_project_context(
        x_project_id="proj1",
        authorization=f"Bearer {api_key}"
    )

    assert context.project_id == "proj1"
    assert context.developer_id == "alice"

@pytest.mark.asyncio
async def test_get_project_context_invalid_api_key():
    """Test dependency with invalid API key."""
    with pytest.raises(HTTPException) as exc_info:
        await get_project_context(
            x_project_id="proj1",
            authorization="Bearer invalid-key"
        )

    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_project_context_malformed_authorization_header():
    """Test dependency with malformed Authorization header."""
    with pytest.raises(HTTPException) as exc_info:
        await get_project_context(
            x_project_id="proj1",
            authorization="NotBearer key"
        )

    assert exc_info.value.status_code == 401
    assert "Invalid Authorization header format" in exc_info.value.detail
```

**Coverage Target**: 100% of dependencies.py

---

## INTEGRATION TESTS (30% of test suite)

Integration tests use `httpx.AsyncClient` to test full request/response cycles.

### 5. Review Endpoints (TASK-014)

**File**: `tests/rest_api/test_review_endpoints.py`

**Coverage**: Routes, authentication, authorization, background tasks

**Test Classes**:

#### TestReviewSubmission

```python
@pytest.mark.asyncio
async def test_submit_review_returns_202_with_review_id(client, setup_project):
    """Test POST /v1/reviews/ happy path."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    response = await client.post(
        "/v1/reviews/",
        json={"diff_content": "sample diff", "files": ["test.py"]},
        headers=headers
    )

    assert response.status_code == 202
    data = response.json()
    assert "review_id" in data
    assert data["status"] == "pending"
    assert data["project_id"] == setup_project["project_id"]

@pytest.mark.asyncio
async def test_submit_review_without_auth_returns_401(client):
    """Property S1: Unauthenticated requests return 401."""
    response = await client.post(
        "/v1/reviews/",
        json={"diff_content": "diff", "files": []}
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_submit_review_with_invalid_api_key_returns_401(client, setup_project):
    """Property S1: Invalid API key returns 401."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": "Bearer invalid-key"
    }

    response = await client.post(
        "/v1/reviews/",
        json={"diff_content": "diff", "files": []},
        headers=headers
    )

    assert response.status_code == 401
```

#### TestReviewStatusQuery

```python
@pytest.mark.asyncio
async def test_get_review_status_returns_pending(client, setup_project):
    """Test GET /v1/reviews/{id} returns status."""
    # Submit review first
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    submit_response = await client.post(
        "/v1/reviews/",
        json={"diff_content": "diff", "files": []},
        headers=headers
    )
    review_id = submit_response.json()["review_id"]

    # Query status
    status_response = await client.get(
        f"/v1/reviews/{review_id}",
        headers=headers
    )

    assert status_response.status_code == 200
    data = status_response.json()
    assert data["review_id"] == review_id
    assert data["status"] in ["pending", "in_progress", "completed"]

@pytest.mark.asyncio
async def test_get_review_status_other_project_returns_403(client, setup_two_projects):
    """Property S2: Project isolation enforced."""
    proj1_headers = {
        "X-Project-ID": setup_two_projects["proj1"]["project_id"],
        "Authorization": f"Bearer {setup_two_projects['proj1']['api_key']}"
    }

    # Submit review with proj1
    submit_response = await client.post(
        "/v1/reviews/",
        json={"diff_content": "diff", "files": []},
        headers=proj1_headers
    )
    review_id = submit_response.json()["review_id"]

    # Try to access with proj2
    proj2_headers = {
        "X-Project-ID": setup_two_projects["proj2"]["project_id"],
        "Authorization": f"Bearer {setup_two_projects['proj2']['api_key']}"
    }

    status_response = await client.get(
        f"/v1/reviews/{review_id}",
        headers=proj2_headers
    )

    assert status_response.status_code == 403
```

#### TestRateLimiting

```python
@pytest.mark.asyncio
async def test_rate_limiting_enforced(client, setup_project):
    """Test rate limiting returns 429 when capacity exceeded."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    # Submit 11 reviews rapidly (capacity is 10)
    responses = []
    for i in range(11):
        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": f"diff {i}", "files": []},
            headers=headers
        )
        responses.append(response)

    # At least one should be rate limited
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes

@pytest.mark.asyncio
async def test_rate_limit_refills_over_time(client, setup_project):
    """Test token bucket refills at configured rate."""
    import asyncio

    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    # Exhaust rate limit
    for _ in range(10):
        await client.post("/v1/reviews/", json={"diff_content": "diff", "files": []}, headers=headers)

    # Next request should be rate limited
    response = await client.post("/v1/reviews/", json={"diff_content": "diff", "files": []}, headers=headers)
    assert response.status_code == 429

    # Wait for refill (1 token at 10 tokens/sec = 0.1 seconds)
    await asyncio.sleep(0.2)

    # Should succeed now
    response = await client.post("/v1/reviews/", json={"diff_content": "diff", "files": []}, headers=headers)
    assert response.status_code == 202
```

**Coverage Target**: 100% of review routes

---

### 6. Project Endpoints (TASK-015)

**File**: `tests/rest_api/test_project_endpoints.py`

**Test Classes**:

#### TestProjectCreation

```python
@pytest.mark.asyncio
async def test_create_project_returns_201_with_api_key(client):
    """Test POST /v1/projects/ creates project."""
    response = await client.post(
        "/v1/projects/",
        json={
            "project_id": "new-proj",
            "developer_id": "alice",
            "repo_path": "/absolute/path"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == "new-proj"
    assert "api_key" in data
    assert len(data["api_key"]) > 30

@pytest.mark.asyncio
async def test_create_duplicate_project_returns_409(client):
    """Property I1: Duplicate project creation fails."""
    payload = {
        "project_id": "dup-proj",
        "developer_id": "alice",
        "repo_path": "/absolute/path"
    }

    # Create first time
    await client.post("/v1/projects/", json=payload)

    # Try to create again
    response = await client.post("/v1/projects/", json=payload)

    assert response.status_code == 409
```

#### TestProjectListing

```python
@pytest.mark.asyncio
async def test_list_projects_returns_all_projects(client):
    """Test GET /v1/projects/ lists all projects."""
    # Create two projects
    await client.post(
        "/v1/projects/",
        json={"project_id": "proj1", "developer_id": "alice", "repo_path": "/path1"}
    )
    await client.post(
        "/v1/projects/",
        json={"project_id": "proj2", "developer_id": "bob", "repo_path": "/path2"}
    )

    # List projects
    response = await client.get("/v1/projects/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) >= 2
    project_ids = [p["project_id"] for p in data["projects"]]
    assert "proj1" in project_ids
    assert "proj2" in project_ids

@pytest.mark.asyncio
async def test_list_projects_does_not_expose_api_keys(client):
    """Property S3: API keys not exposed in list response."""
    await client.post(
        "/v1/projects/",
        json={"project_id": "proj1", "developer_id": "alice", "repo_path": "/path"}
    )

    response = await client.get("/v1/projects/")

    data = response.json()
    for project in data["projects"]:
        assert "api_key" not in project
        assert "api_key_hash" not in project
```

**Coverage Target**: 100% of project routes

---

### 7. Resource Monitoring Endpoints (TASK-016)

**File**: `tests/rest_api/test_resource_endpoints.py`

**Test Classes**:

#### TestPoolStatus

```python
@pytest.mark.asyncio
async def test_get_pool_status_returns_metrics(client, setup_project):
    """Test GET /v1/resources/pool returns pool metrics."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    response = await client.get("/v1/resources/pool", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "max_worktrees" in data
    assert "active_worktrees" in data
    assert "available_capacity" in data
    assert data["max_worktrees"] == 10

@pytest.mark.asyncio
async def test_pool_status_requires_auth(client):
    """Property S1: Resource endpoints require authentication."""
    response = await client.get("/v1/resources/pool")

    assert response.status_code == 401
```

#### TestRateLimitStatus

```python
@pytest.mark.asyncio
async def test_get_rate_limit_status_returns_metrics(client, setup_project):
    """Test GET /v1/resources/rate-limit returns metrics."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    response = await client.get("/v1/resources/rate-limit", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "capacity" in data
    assert "refill_rate" in data
    assert "available_tokens" in data
    assert data["capacity"] == 10
```

**Coverage Target**: 100% of resource routes

---

## LOAD TESTS (10% of test suite)

Load tests verify performance properties (P1-P4) under realistic workloads.

### 8. Locust Load Testing

**File**: `tests/rest_api/load/locustfile.py`

**Scenarios**:

```python
from locust import HttpUser, task, between

class WFCAPIUser(HttpUser):
    """Simulated API user."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Setup: Create project and get API key."""
        response = self.client.post(
            "/v1/projects/",
            json={
                "project_id": f"load-test-{self.environment.runner.user_count}",
                "developer_id": "loadtest",
                "repo_path": "/tmp/test"
            }
        )
        data = response.json()
        self.project_id = data["project_id"]
        self.api_key = data["api_key"]

    @task(10)
    def submit_review(self):
        """Submit review (most common operation)."""
        headers = {
            "X-Project-ID": self.project_id,
            "Authorization": f"Bearer {self.api_key}"
        }

        with self.client.post(
            "/v1/reviews/",
            json={"diff_content": "sample diff", "files": ["test.py"]},
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 202:
                response.success()
                self.review_id = response.json()["review_id"]
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def check_review_status(self):
        """Check review status (common operation)."""
        if not hasattr(self, "review_id"):
            return

        headers = {
            "X-Project-ID": self.project_id,
            "Authorization": f"Bearer {self.api_key}"
        }

        with self.client.get(
            f"/v1/reviews/{self.review_id}",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def check_pool_status(self):
        """Check pool status (infrequent operation)."""
        headers = {
            "X-Project-ID": self.project_id,
            "Authorization": f"Bearer {self.api_key}"
        }

        self.client.get("/v1/resources/pool", headers=headers)
```

**Run Load Test**:

```bash
# Start server
uv run python -m wfc.servers.rest_api.main &

# Run load test
locust -f tests/rest_api/load/locustfile.py --headless \
  --users 100 --spawn-rate 10 --run-time 5m \
  --host http://localhost:8000
```

**Success Criteria**:

| Metric | Target | Property |
|--------|--------|----------|
| RPS (requests/sec) | >50 | P3 |
| POST /v1/reviews/ p95 | <100ms | P1 |
| GET /v1/reviews/{id} p95 | <200ms | P2 |
| Error rate | <1% | - |
| Memory usage | <500MB | P4 |

---

### 9. Performance Property Verification

**File**: `tests/rest_api/load/test_performance.py`

**Test Functions**:

```python
import pytest
import asyncio
import psutil
from httpx import AsyncClient
from wfc.servers.rest_api.main import app


@pytest.mark.asyncio
async def test_property_p1_review_submission_latency(setup_project):
    """Property P1: Review submission p95 < 100ms."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        latencies = []

        for i in range(100):
            start = asyncio.get_event_loop().time()

            await client.post(
                "/v1/reviews/",
                json={"diff_content": f"diff {i}", "files": []},
                headers=headers
            )

            latency = (asyncio.get_event_loop().time() - start) * 1000  # Convert to ms
            latencies.append(latency)

        latencies.sort()
        p95 = latencies[94]  # 95th percentile

        assert p95 < 100, f"P1 violated: p95={p95:.2f}ms (expected <100ms)"


@pytest.mark.asyncio
async def test_property_p3_concurrent_request_capacity(setup_project):
    """Property P3: Handle 100 concurrent requests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        async def submit_review(i):
            return await client.post(
                "/v1/reviews/",
                json={"diff_content": f"diff {i}", "files": []},
                headers=headers
            )

        # Submit 100 reviews concurrently
        tasks = [submit_review(i) for i in range(100)]
        responses = await asyncio.gather(*tasks)

        # Count successful responses (202 or 429)
        success_count = sum(1 for r in responses if r.status_code in [202, 429])

        assert success_count == 100, f"P3 violated: {100 - success_count} requests failed"


@pytest.mark.asyncio
async def test_property_p4_memory_usage(setup_project):
    """Property P4: Memory usage <500MB under load."""
    import psutil
    import os

    process = psutil.Process(os.getpid())

    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}"
        }

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Submit 1000 reviews
        for i in range(1000):
            await client.post(
                "/v1/reviews/",
                json={"diff_content": f"diff {i}", "files": []},
                headers=headers
            )

        # Peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        assert peak_memory < 500, f"P4 violated: memory={peak_memory:.2f}MB (expected <500MB)"
```

**Coverage Target**: All performance properties (P1-P4) verified

---

## PROPERTY-BASED TESTS

**File**: `tests/rest_api/test_properties.py`

Use Hypothesis for generative testing:

```python
from hypothesis import given, strategies as st, settings
from wfc.servers.rest_api.auth import APIKeyStore


@given(
    project_id=st.text(
        min_size=1,
        max_size=64,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))
    )
)
def test_property_i1_api_key_uniqueness(project_id):
    """Property I1: Each API key maps to exactly one project."""
    store = APIKeyStore()

    # Create key
    api_key = store.create_api_key(project_id, "alice")

    # Property: key validates only for this project
    assert store.validate_api_key(project_id, api_key) is True

    # Property: same key cannot be created twice
    with pytest.raises(ValueError):
        store.create_api_key(project_id, "bob")


@given(
    diff_content=st.text(min_size=1, max_size=10000),
    files=st.lists(st.text(min_size=1, max_size=255), max_size=100)
)
def test_property_s4_input_validation(diff_content, files):
    """Property S4: All inputs validated before processing."""
    from wfc.servers.rest_api.models import ReviewSubmitRequest

    # Property: valid inputs always accepted
    try:
        request = ReviewSubmitRequest(diff_content=diff_content, files=files)
        assert request.diff_content == diff_content
        assert request.files == files
    except ValidationError:
        # Invalid input rejected (expected)
        pass


@given(
    initial_status=st.sampled_from(["pending", "in_progress"]),
    final_status=st.sampled_from(["completed", "failed"])
)
def test_property_i2_status_transitions(initial_status, final_status):
    """Property I2: Status transitions follow state machine."""
    from wfc.servers.rest_api.background import ReviewStatusStore
    from wfc.servers.rest_api.models import ReviewStatus

    store = ReviewStatusStore()
    review_id = store.create_review("proj1", "alice")

    # Transition to initial state
    store.update_status(review_id, ReviewStatus(initial_status))

    # Transition to final state
    if final_status == "completed":
        store.complete_review(review_id, 8.5, True, [])
    else:
        store.fail_review(review_id, "Error")

    # Verify final state
    review = store.get_review(review_id)
    assert review.status == ReviewStatus(final_status)

    # Property: terminal states cannot transition further
    store.update_status(review_id, ReviewStatus.IN_PROGRESS)
    review = store.get_review(review_id)
    assert review.status == ReviewStatus(final_status)  # Unchanged
```

**Coverage Target**: All SAFETY, LIVENESS, INVARIANT properties

---

## SECURITY TESTS

**File**: `tests/rest_api/test_security.py`

**Attack Scenarios**:

```python
@pytest.mark.asyncio
async def test_sql_injection_attempt(client, setup_project):
    """Test SQL injection patterns are safely handled."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    # SQL injection in diff_content
    response = await client.post(
        "/v1/reviews/",
        json={
            "diff_content": "'; DROP TABLE reviews; --",
            "files": []
        },
        headers=headers
    )

    # Should succeed (we use file-based storage, no SQL)
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_path_traversal_attempt(client):
    """Test path traversal in project_id is rejected."""
    response = await client.post(
        "/v1/projects/",
        json={
            "project_id": "../../../etc/passwd",
            "developer_id": "alice",
            "repo_path": "/tmp/test"
        }
    )

    # Should be rejected by pattern validation
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_oversized_request(client, setup_project):
    """Test oversized diff_content is rejected."""
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}"
    }

    # 2MB diff (exceeds 1MB limit)
    large_diff = "A" * (2 * 1024 * 1024)

    response = await client.post(
        "/v1/reviews/",
        json={"diff_content": large_diff, "files": []},
        headers=headers
    )

    # Should be rejected
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_timing_attack_on_api_key_validation(setup_project):
    """Test API key validation resists timing attacks."""
    import timeit
    from wfc.servers.rest_api.auth import APIKeyStore

    store = APIKeyStore()
    api_key = setup_project["api_key"]

    # Measure validation time for correct key
    time_correct = timeit.timeit(
        lambda: store.validate_api_key(setup_project["project_id"], api_key),
        number=1000
    )

    # Measure validation time for incorrect key (same length)
    wrong_key = "X" * len(api_key)
    time_wrong = timeit.timeit(
        lambda: store.validate_api_key(setup_project["project_id"], wrong_key),
        number=1000
    )

    # Timing ratio should be close to 1 (constant time)
    ratio = max(time_correct, time_wrong) / min(time_correct, time_wrong)
    assert ratio < 1.1, f"Timing attack vulnerability: ratio={ratio}"
```

---

## TEST FIXTURES

**File**: `tests/rest_api/conftest.py`

**Shared Fixtures**:

```python
import pytest
import tempfile
from pathlib import Path
from httpx import AsyncClient

from wfc.servers.rest_api.main import app
from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.background import ReviewStatusStore


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def tmp_api_key_store(tmp_path):
    """Temporary API key store."""
    store_path = tmp_path / "api_keys.json"
    return APIKeyStore(store_path=store_path)


@pytest.fixture
def tmp_review_store(tmp_path):
    """Temporary review status store."""
    reviews_dir = tmp_path / "reviews"
    return ReviewStatusStore(reviews_dir=reviews_dir)


@pytest.fixture
def setup_project(tmp_api_key_store):
    """Create test project with API key."""
    api_key = tmp_api_key_store.create_api_key("test-proj", "alice")

    return {
        "project_id": "test-proj",
        "developer_id": "alice",
        "api_key": api_key
    }


@pytest.fixture
def setup_two_projects(tmp_api_key_store):
    """Create two projects for isolation testing."""
    api_key1 = tmp_api_key_store.create_api_key("proj1", "alice")
    api_key2 = tmp_api_key_store.create_api_key("proj2", "bob")

    return {
        "proj1": {"project_id": "proj1", "developer_id": "alice", "api_key": api_key1},
        "proj2": {"project_id": "proj2", "developer_id": "bob", "api_key": api_key2}
    }
```

---

## COVERAGE REPORTING

### Generate Coverage Report

```bash
# Run tests with coverage
uv run pytest tests/rest_api/ \
  --cov=wfc/servers/rest_api \
  --cov-report=html \
  --cov-report=term \
  --cov-fail-under=95

# View HTML report
open htmlcov/index.html
```

### Coverage Targets

| Module | Target | Critical Paths |
|--------|--------|---------------|
| models.py | 100% | All validation logic |
| auth.py | 100% | API key creation, validation, storage |
| background.py | 95% | Status transitions, background execution |
| routes.py | 100% | All endpoints, error handling |
| dependencies.py | 100% | Authentication, authorization |
| main.py | 90% | App initialization, middleware |

**Overall Target**: 95%+ code coverage

---

## CONTINUOUS INTEGRATION

### GitHub Actions Workflow

```yaml
name: REST API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[test,api]"

      - name: Run unit tests
        run: |
          uv run pytest tests/rest_api/ \
            --cov=wfc/servers/rest_api \
            --cov-report=xml \
            --cov-fail-under=95

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

      - name: Run load tests
        run: |
          uv run python -m wfc.servers.rest_api.main &
          sleep 5
          locust -f tests/rest_api/load/locustfile.py \
            --headless --users 50 --spawn-rate 5 --run-time 2m \
            --host http://localhost:8000
```

---

## SUMMARY

**Total Test Files**: 9 unit + 3 integration + 2 load = 14 files

**Test Count Estimate**: ~150 tests total

- Unit tests: ~90 tests
- Integration tests: ~45 tests
- Load tests: ~15 tests

**Coverage Targets**:

- Code coverage: 95%+
- Property coverage: 100% (all 14 properties)
- Endpoint coverage: 100% (all routes tested)

**Test Execution Time**:

- Unit tests: <10 seconds
- Integration tests: <30 seconds
- Load tests: ~5 minutes
- Total: ~6 minutes

**Key Quality Gates**:

1. All properties verified (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
2. 95%+ code coverage
3. 0 security vulnerabilities
4. <1% error rate under load
5. p95 latency within SLAs
