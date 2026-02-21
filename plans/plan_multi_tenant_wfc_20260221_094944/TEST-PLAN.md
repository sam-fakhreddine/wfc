---
title: Multi-Tenant WFC Test Plan
created: 2026-02-21
total_tests: 43
coverage_target: 95%
related_ba: BA-multi-tenant-wfc.md
---

# Test Plan - Multi-Tenant WFC

## Testing Strategy

### Unit Tests (per-component)

- Each critical component must have corresponding unit tests
- Coverage target: 95% line coverage per file
- Framework: pytest with pytest-cov
- Philosophy: Test behavior, not implementation

### Integration Tests (cross-component)

- Test interactions between components (e.g., orchestrator + worktree pool)
- 6 acceptance tests from BA Section 11 mapped to integration tests
- Framework: pytest with fixtures and mocks

### Load Tests (concurrency)

- Concurrent review simulation (50 simultaneous)
- Rate limiting validation
- Framework: pytest-xdist for parallelization, locust for HTTP load

### End-to-End Tests (full workflows)

- MCP interface: review via Claude Code
- REST interface: review via HTTP
- Hybrid: MCP delegates to REST

---

## Unit Test Cases

### Component 1: Project Context & Configuration

#### TEST-U001: ProjectContext Creation

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_project_context.py`
- **Description**: Test ProjectContext dataclass creation and validation

**Test Steps**:

```python
def test_project_context_creation():
    """Test ProjectContext dataclass with all required fields."""
    ctx = ProjectContext(
        project_id="test-proj",
        developer_id="alice",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees/test-proj"),
        metrics_dir=Path.home() / ".wfc/metrics/test-proj",
        output_dir=Path("/tmp/repo/.wfc/output/test-proj")
    )
    assert ctx.project_id == "test-proj"
    assert ctx.developer_id == "alice"
    assert ctx.worktree_dir == Path("/tmp/repo/.worktrees/test-proj")
    assert ctx.metrics_dir == Path.home() / ".wfc/metrics/test-proj"
    assert all(p.is_absolute() for p in [ctx.repo_path, ctx.worktree_dir])
```

**Expected**: All assertions pass, paths are absolute

---

#### TEST-U002: ProjectContext Validation - Invalid project_id

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_project_context.py`
- **Description**: Reject invalid project_id with path traversal

**Test Steps**:

```python
def test_project_context_rejects_path_traversal():
    """Test that project_id with path traversal is rejected."""
    with pytest.raises(ValueError, match="path traversal"):
        ProjectContext(
            project_id="../evil",
            developer_id="alice",
            repo_path=Path("/tmp/repo"),
            worktree_dir=Path("/tmp/repo/.worktrees"),
            metrics_dir=Path.home() / ".wfc/metrics",
            output_dir=Path("/tmp/repo/.wfc/output")
        )
```

**Expected**: ValueError raised with "path traversal" message

---

#### TEST-U003: WFCConfig Factory Method

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_wfc_config.py`
- **Description**: Test WFCConfig.create_project_context() factory method

**Test Steps**:

```python
def test_wfc_config_creates_project_context():
    """Test factory method generates correct paths."""
    config = WFCConfig()
    ctx = config.create_project_context(
        project_id="proj-123",
        developer_id="bob",
        repo_path=Path("/code/myapp")
    )
    assert ctx.project_id == "proj-123"
    assert ctx.developer_id == "bob"
    assert ctx.worktree_dir == Path("/code/myapp/.worktrees/proj-123")
    assert ctx.metrics_dir == Path.home() / ".wfc/metrics/proj-123"
    assert ctx.output_dir == Path("/code/myapp/.wfc/output/proj-123")
```

**Expected**: All path components include project_id namespace

---

#### TEST-U004: ProjectContext Immutability

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_project_context.py`
- **Description**: Ensure ProjectContext is frozen (dataclass frozen=True)

**Test Steps**:

```python
def test_project_context_immutable():
    """Test that ProjectContext cannot be modified after creation."""
    ctx = ProjectContext(
        project_id="test",
        developer_id="alice",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees"),
        metrics_dir=Path.home() / ".wfc/metrics",
        output_dir=Path("/tmp/repo/.wfc/output")
    )
    with pytest.raises(FrozenInstanceError):
        ctx.project_id = "modified"
```

**Expected**: FrozenInstanceError raised (dataclass is frozen)

---

### Component 2: Worktree Namespacing

#### TEST-U005: Worktree Path Namespacing

- **Type**: unit
- **Related BA**: M1 (Project Isolation), S1 (No cross-project contamination)
- **File**: `tests/test_worktree_namespacing.py`
- **Description**: Test worktree paths include project_id

**Test Steps**:

```python
def test_worktree_path_includes_project_id():
    """Test that worktree paths are namespaced by project_id."""
    ops = WorktreeOperations(project_id="proj1")
    path = ops._worktree_path("feature-001")
    assert "proj1" in str(path)
    assert path.parts[-2] == "proj1"
    assert path.parts[-1] == "wfc-feature-001"
    assert str(path) == ".worktrees/proj1/wfc-feature-001"
```

**Expected**: Path structure: `.worktrees/{project_id}/wfc-{task_id}`

---

#### TEST-U006: Worktree Collision Prevention

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_worktree_namespacing.py`
- **Description**: Two projects with same task_id get different worktrees

**Test Steps**:

```python
def test_different_projects_same_task_no_collision():
    """Test that same task_id in different projects creates separate worktrees."""
    ops1 = WorktreeOperations(project_id="proj1")
    ops2 = WorktreeOperations(project_id="proj2")

    path1 = ops1._worktree_path("TASK-001")
    path2 = ops2._worktree_path("TASK-001")

    assert path1 != path2
    assert "proj1" in str(path1)
    assert "proj2" in str(path2)
```

**Expected**: Different paths for different projects, same task_id

---

#### TEST-U007: Worktree Branch Naming

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_worktree_namespacing.py`
- **Description**: Branch names include project_id

**Test Steps**:

```python
@patch("wfc.gitwork.api.worktree._run_manager")
def test_branch_name_includes_project_id(mock_run):
    """Test that branch names are namespaced by project_id."""
    mock_run.return_value = MagicMock(returncode=0, stdout="created", stderr="")

    ops = WorktreeOperations(project_id="proj1")
    result = ops.create("TASK-001", "develop")

    assert result["success"] is True
    assert result["branch_name"] == "wfc/proj1/TASK-001"
```

**Expected**: Branch name: `wfc/{project_id}/{task_id}`

---

### Component 3: File I/O Locking

#### TEST-U008: FileLock Acquisition

- **Type**: unit
- **Related BA**: M2 (Concurrent Access Safety)
- **File**: `tests/test_file_lock.py`
- **Description**: Test FileLock context manager acquires lock

**Test Steps**:

```python
def test_file_lock_acquires_lock():
    """Test that FileLock successfully acquires a lock."""
    test_file = Path("/tmp/test_knowledge.md")
    test_file.write_text("initial content")

    with FileLock(test_file) as lock:
        assert lock.is_locked() is True

    assert lock.is_locked() is False
```

**Expected**: Lock acquired within context, released after

---

#### TEST-U009: FileLock Blocking Behavior

- **Type**: unit
- **Related BA**: M2 (Concurrent Access Safety)
- **File**: `tests/test_file_lock.py`
- **Description**: Second lock waits for first to release

**Test Steps**:

```python
def test_file_lock_blocks_concurrent_access():
    """Test that second lock waits for first lock to release."""
    test_file = Path("/tmp/test_knowledge.md")
    test_file.write_text("initial")

    acquired_order = []

    def writer1():
        with FileLock(test_file):
            acquired_order.append(1)
            time.sleep(0.1)

    def writer2():
        time.sleep(0.05)  # Start after writer1
        with FileLock(test_file):
            acquired_order.append(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(writer1)
        f2 = executor.submit(writer2)
        f1.result()
        f2.result()

    assert acquired_order == [1, 2]  # writer2 waited for writer1
```

**Expected**: Second writer blocks until first completes

---

#### TEST-U010: FileLock Timeout

- **Type**: unit
- **Related BA**: M2 (Concurrent Access Safety)
- **File**: `tests/test_file_lock.py`
- **Description**: FileLock raises timeout error if cannot acquire

**Test Steps**:

```python
def test_file_lock_timeout():
    """Test that FileLock times out if lock cannot be acquired."""
    test_file = Path("/tmp/test_knowledge.md")
    test_file.write_text("initial")

    with FileLock(test_file):
        # Try to acquire again with short timeout
        with pytest.raises(TimeoutError):
            with FileLock(test_file, timeout=0.1):
                pass
```

**Expected**: TimeoutError raised after 0.1s

---

### Component 4: Knowledge Writer Attribution

#### TEST-U011: Knowledge Entry Developer Attribution

- **Type**: unit
- **Related BA**: M3 (Developer Attribution)
- **File**: `tests/test_knowledge_writer.py`
- **Description**: Knowledge entries tagged with developer_id

**Test Steps**:

```python
def test_knowledge_entry_includes_developer_id():
    """Test that knowledge entries are tagged with developer_id."""
    writer = KnowledgeWriter(developer_id="alice")
    entry = writer.create_entry(
        category="security",
        description="SQL injection found",
        remediation="Use parameterized queries"
    )

    assert entry["developer_id"] == "alice"
    assert entry["category"] == "security"
    assert "timestamp" in entry
```

**Expected**: Entry contains developer_id and timestamp

---

#### TEST-U012: Knowledge Writer Append with Lock

- **Type**: unit
- **Related BA**: M2 (Concurrent Access Safety), M3 (Developer Attribution)
- **File**: `tests/test_knowledge_writer.py`
- **Description**: Knowledge writer uses FileLock during append

**Test Steps**:

```python
@patch("wfc.scripts.knowledge.knowledge_writer.FileLock")
def test_knowledge_writer_uses_lock(mock_lock):
    """Test that KnowledgeWriter uses FileLock when appending."""
    writer = KnowledgeWriter(developer_id="bob")
    knowledge_file = Path("/tmp/KNOWLEDGE.md")

    writer.append_entry(
        knowledge_file,
        category="performance",
        description="N+1 query detected"
    )

    mock_lock.assert_called_once_with(knowledge_file, timeout=5.0)
```

**Expected**: FileLock called with knowledge file path

---

#### TEST-U013: Knowledge Entry Format Validation

- **Type**: unit
- **Related BA**: M2 (Concurrent Access Safety)
- **File**: `tests/test_knowledge_writer.py`
- **Description**: Knowledge entries are valid markdown

**Test Steps**:

```python
def test_knowledge_entry_valid_markdown():
    """Test that knowledge entries produce valid markdown."""
    writer = KnowledgeWriter(developer_id="charlie")
    entry_md = writer.format_entry(
        category="reliability",
        description="Race condition in cache",
        remediation="Use atomic operations"
    )

    assert "## reliability" in entry_md.lower()
    assert "developer: charlie" in entry_md.lower()
    assert "race condition" in entry_md.lower()
    assert entry_md.count("```") % 2 == 0  # Balanced code fences
```

**Expected**: Valid markdown with proper structure

---

### Component 5: Token Bucket Rate Limiting

#### TEST-U014: TokenBucket Initialization

- **Type**: unit
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/test_token_bucket.py`
- **Description**: TokenBucket initializes with correct capacity

**Test Steps**:

```python
def test_token_bucket_initialization():
    """Test that TokenBucket initializes with correct parameters."""
    bucket = TokenBucket(capacity=100, refill_rate=10)  # 10 tokens/sec

    assert bucket.capacity == 100
    assert bucket.refill_rate == 10
    assert bucket.tokens == 100  # Starts full
```

**Expected**: Bucket initialized with full tokens

---

#### TEST-U015: TokenBucket Consume Success

- **Type**: unit
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/test_token_bucket.py`
- **Description**: TokenBucket allows consumption when tokens available

**Test Steps**:

```python
def test_token_bucket_consume_success():
    """Test that TokenBucket allows consumption when tokens available."""
    bucket = TokenBucket(capacity=100, refill_rate=10)

    result = bucket.consume(50)
    assert result is True
    assert bucket.tokens == 50

    result = bucket.consume(30)
    assert result is True
    assert bucket.tokens == 20
```

**Expected**: Consumption succeeds, tokens decremented

---

#### TEST-U016: TokenBucket Consume Failure

- **Type**: unit
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/test_token_bucket.py`
- **Description**: TokenBucket rejects consumption when insufficient tokens

**Test Steps**:

```python
def test_token_bucket_consume_insufficient_tokens():
    """Test that TokenBucket rejects when insufficient tokens."""
    bucket = TokenBucket(capacity=100, refill_rate=10)
    bucket.consume(95)

    result = bucket.consume(10)  # Only 5 left
    assert result is False
    assert bucket.tokens == 5  # Unchanged
```

**Expected**: Consumption fails, tokens unchanged

---

#### TEST-U017: TokenBucket Refill

- **Type**: unit
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/test_token_bucket.py`
- **Description**: TokenBucket refills over time

**Test Steps**:

```python
def test_token_bucket_refill():
    """Test that TokenBucket refills tokens over time."""
    bucket = TokenBucket(capacity=100, refill_rate=10)  # 10/sec
    bucket.consume(100)  # Empty the bucket

    assert bucket.tokens == 0
    time.sleep(1.0)  # Wait 1 second

    bucket._refill()  # Explicit refill call
    assert bucket.tokens == 10  # 10 tokens refilled
```

**Expected**: Tokens refilled based on elapsed time

---

#### TEST-U018: TokenBucket Max Capacity

- **Type**: unit
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/test_token_bucket.py`
- **Description**: TokenBucket never exceeds capacity

**Test Steps**:

```python
def test_token_bucket_max_capacity():
    """Test that TokenBucket never exceeds capacity."""
    bucket = TokenBucket(capacity=100, refill_rate=50)

    time.sleep(3.0)  # 150 tokens would be generated
    bucket._refill()

    assert bucket.tokens == 100  # Capped at capacity
```

**Expected**: Tokens capped at capacity

---

### Component 6: Telemetry Namespacing

#### TEST-U019: Telemetry Path Namespacing

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_telemetry_namespacing.py`
- **Description**: Telemetry files scoped to project_id

**Test Steps**:

```python
def test_telemetry_path_includes_project_id():
    """Test that telemetry paths are namespaced by project_id."""
    ctx = ProjectContext(
        project_id="proj-abc",
        developer_id="alice",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees"),
        metrics_dir=Path.home() / ".wfc/metrics/proj-abc",
        output_dir=Path("/tmp/repo/.wfc/output")
    )

    telemetry = TelemetryWriter(ctx)
    metrics_file = telemetry.get_metrics_file()

    assert "proj-abc" in str(metrics_file)
    assert metrics_file.parent.name == "proj-abc"
```

**Expected**: Metrics file path includes project_id

---

#### TEST-U020: Telemetry Entry Developer Attribution

- **Type**: unit
- **Related BA**: M3 (Developer Attribution)
- **File**: `tests/test_telemetry_namespacing.py`
- **Description**: Telemetry entries include developer_id

**Test Steps**:

```python
def test_telemetry_entry_includes_developer():
    """Test that telemetry entries are tagged with developer_id."""
    ctx = ProjectContext(
        project_id="proj-123",
        developer_id="bob",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees"),
        metrics_dir=Path.home() / ".wfc/metrics",
        output_dir=Path("/tmp/repo/.wfc/output")
    )

    telemetry = TelemetryWriter(ctx)
    entry = telemetry.create_entry(
        event_type="review_complete",
        data={"cs": 7.5}
    )

    assert entry["project_id"] == "proj-123"
    assert entry["developer_id"] == "bob"
    assert entry["event_type"] == "review_complete"
```

**Expected**: Entry contains project_id, developer_id, event_type

---

### Component 7: Worktree Cleanup

#### TEST-U021: Orphan Detection - Age-Based

- **Type**: unit
- **Related BA**: M5 (Guaranteed Resource Cleanup)
- **File**: `tests/test_worktree_cleanup.py`
- **Description**: Detect worktrees older than threshold

**Test Steps**:

```python
def test_orphan_detection_by_age():
    """Test that worktrees older than 24h are detected as orphans."""
    cleaner = WorktreeCleanup()

    # Create test worktree with old timestamp
    old_worktree = Path("/tmp/.worktrees/proj1/wfc-old")
    old_worktree.mkdir(parents=True, exist_ok=True)

    # Set mtime to 25 hours ago
    old_time = time.time() - (25 * 3600)
    os.utime(old_worktree, (old_time, old_time))

    orphans = cleaner.find_orphans(threshold_hours=24)

    assert old_worktree in orphans
```

**Expected**: Old worktree identified as orphan

---

#### TEST-U022: Orphan Detection - Process-Based

- **Type**: unit
- **Related BA**: M5 (Guaranteed Resource Cleanup)
- **File**: `tests/test_worktree_cleanup.py`
- **Description**: Detect worktrees with no active process

**Test Steps**:

```python
def test_orphan_detection_no_active_process():
    """Test that worktrees with no active process are orphans."""
    cleaner = WorktreeCleanup()

    # Create test worktree
    test_worktree = Path("/tmp/.worktrees/proj1/wfc-inactive")
    test_worktree.mkdir(parents=True, exist_ok=True)

    # Write PID file with non-existent PID
    pid_file = test_worktree / ".wfc_pid"
    pid_file.write_text("999999")  # PID doesn't exist

    orphans = cleaner.find_orphans_by_pid()

    assert test_worktree in orphans
```

**Expected**: Worktree with dead PID identified as orphan

---

#### TEST-U023: Cleanup with Context Manager

- **Type**: unit
- **Related BA**: M5 (Guaranteed Resource Cleanup)
- **File**: `tests/test_worktree_cleanup.py`
- **Description**: Worktree deleted via context manager on exit

**Test Steps**:

```python
def test_worktree_cleanup_context_manager():
    """Test that worktree is cleaned up via context manager."""
    ops = WorktreeOperations(project_id="proj1")

    with ops.create_worktree("TASK-001") as worktree_path:
        assert worktree_path.exists()

    # After context exits, worktree should be deleted
    assert not worktree_path.exists()
```

**Expected**: Worktree deleted after context exit

---

#### TEST-U024: Cleanup on Exception

- **Type**: unit
- **Related BA**: M5 (Guaranteed Resource Cleanup)
- **File**: `tests/test_worktree_cleanup.py`
- **Description**: Worktree cleaned up even on exception

**Test Steps**:

```python
def test_worktree_cleanup_on_exception():
    """Test that worktree is cleaned up even when exception occurs."""
    ops = WorktreeOperations(project_id="proj1")

    worktree_path = None
    with pytest.raises(RuntimeError):
        with ops.create_worktree("TASK-002") as wt_path:
            worktree_path = wt_path
            raise RuntimeError("Test exception")

    assert not worktree_path.exists()
```

**Expected**: Worktree deleted despite exception

---

### Component 8: Orchestrator Integration

#### TEST-U025: Orchestrator Accepts ProjectContext

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_orchestrator_context.py`
- **Description**: ReviewOrchestrator accepts ProjectContext parameter

**Test Steps**:

```python
def test_orchestrator_accepts_project_context():
    """Test that ReviewOrchestrator accepts ProjectContext."""
    ctx = ProjectContext(
        project_id="proj1",
        developer_id="alice",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees"),
        metrics_dir=Path.home() / ".wfc/metrics",
        output_dir=Path("/tmp/repo/.wfc/output")
    )

    orchestrator = ReviewOrchestrator(project_context=ctx)

    assert orchestrator.project_context == ctx
    assert orchestrator.project_id == "proj1"
    assert orchestrator.developer_id == "alice"
```

**Expected**: Orchestrator stores and uses ProjectContext

---

#### TEST-U026: Orchestrator Defaults to Single-Tenant Mode

- **Type**: unit
- **Related BA**: Backward Compatibility
- **File**: `tests/test_orchestrator_context.py`
- **Description**: Orchestrator works without ProjectContext (backward compat)

**Test Steps**:

```python
def test_orchestrator_backward_compatibility():
    """Test that ReviewOrchestrator works without ProjectContext."""
    orchestrator = ReviewOrchestrator()

    assert orchestrator.project_context is None
    # Should derive project_id from cwd
    assert orchestrator.project_id is not None
```

**Expected**: Orchestrator works in single-tenant mode

---

#### TEST-U027: Report Path Namespacing

- **Type**: unit
- **Related BA**: M1 (Project Isolation)
- **File**: `tests/test_orchestrator_context.py`
- **Description**: Review reports namespaced by project_id

**Test Steps**:

```python
def test_report_path_includes_project_id():
    """Test that review report paths include project_id."""
    ctx = ProjectContext(
        project_id="proj-xyz",
        developer_id="alice",
        repo_path=Path("/tmp/repo"),
        worktree_dir=Path("/tmp/repo/.worktrees"),
        metrics_dir=Path.home() / ".wfc/metrics",
        output_dir=Path("/tmp/repo/.wfc/output/proj-xyz")
    )

    orchestrator = ReviewOrchestrator(project_context=ctx)
    report_path = orchestrator._get_report_path("task-001")

    assert "proj-xyz" in str(report_path)
    assert report_path.name == "REVIEW-proj-xyz-task-001.md"
```

**Expected**: Report filename includes project_id

---

---

## Integration Test Cases

### TEST-I001: Concurrent Project Reviews (BA Test 1)

- **Type**: integration
- **Related BA**: M1 (Project Isolation), Section 11 Test 1
- **File**: `tests/integration/test_concurrent_reviews.py`
- **Description**: 6 concurrent reviews across 6 projects with 0 collisions

**Test Steps**:

```python
@pytest.mark.integration
def test_concurrent_reviews_6_projects():
    """Test 6 concurrent reviews with 0 collisions.

    Maps to BA Section 11, Test 1:
    ✅ All 6 complete successfully
    ✅ No worktree collisions
    ✅ 6 separate reports: REVIEW-proj{1-6}-test.md
    ✅ KNOWLEDGE.md not corrupted
    """
    projects = [f"proj{i}" for i in range(1, 7)]

    def run_review(project_id):
        ctx = ProjectContext(
            project_id=project_id,
            developer_id="test-dev",
            repo_path=Path("/tmp/test-repo"),
            worktree_dir=Path(f"/tmp/.worktrees/{project_id}"),
            metrics_dir=Path.home() / f".wfc/metrics/{project_id}",
            output_dir=Path(f"/tmp/.wfc/output/{project_id}")
        )
        orchestrator = ReviewOrchestrator(project_context=ctx)
        return orchestrator.run_review(task_id="test", diff_content="...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(run_review, proj) for proj in projects]
        results = [f.result() for f in futures]

    # All 6 succeed
    assert all(r.success for r in results), "All reviews must succeed"

    # 6 separate reports
    report_paths = [r.report_path for r in results]
    assert len(set(report_paths)) == 6, "Must have 6 unique report paths"

    for i, path in enumerate(report_paths, 1):
        assert f"proj{i}" in str(path), f"Report must include project_id proj{i}"

    # KNOWLEDGE.md valid
    for i in range(1, 7):
        knowledge_path = Path(f"/tmp/.wfc/knowledge/proj{i}/KNOWLEDGE.md")
        if knowledge_path.exists():
            content = knowledge_path.read_text()
            assert is_valid_markdown(content), f"KNOWLEDGE.md for proj{i} corrupted"
```

**Expected**:

- All 6 reviews complete successfully
- 6 separate reports with project_id in filename
- KNOWLEDGE.md files are valid markdown

---

### TEST-I002: Rate Limiting Under Load (BA Test 2)

- **Type**: integration
- **Related BA**: M4 (API Rate Limiting), Section 11 Test 2
- **File**: `tests/integration/test_rate_limiting.py`
- **Description**: 50 concurrent requests with 0 Anthropic 429 errors

**Test Steps**:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_rate_limiting_50_concurrent():
    """Test 50 concurrent reviews with 0 rate limit errors.

    Maps to BA Section 11, Test 2:
    ✅ No 429 errors from Anthropic API
    ✅ Token bucket queues fairly
    ✅ All 50 complete within 15 minutes
    """
    # Shared token bucket for all reviews
    token_bucket = TokenBucket(capacity=50, refill_rate=5)  # 5 tokens/sec

    def run_review_with_rate_limit(i):
        # Wait for token
        while not token_bucket.consume(1):
            time.sleep(0.1)

        ctx = ProjectContext(
            project_id=f"load-proj-{i}",
            developer_id="load-tester",
            repo_path=Path("/tmp/test-repo"),
            worktree_dir=Path(f"/tmp/.worktrees/load-{i}"),
            metrics_dir=Path.home() / f".wfc/metrics/load-{i}",
            output_dir=Path(f"/tmp/.wfc/output/load-{i}")
        )
        orchestrator = ReviewOrchestrator(
            project_context=ctx,
            token_bucket=token_bucket
        )
        return orchestrator.run_review(task_id=f"load-{i}", diff_content="...")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(run_review_with_rate_limit, i) for i in range(50)]
        results = [f.result() for f in futures]

    duration = time.time() - start_time

    # No rate limit errors
    rate_limit_errors = sum(1 for r in results if r.error_code == 429)
    assert rate_limit_errors == 0, "No Anthropic 429 errors allowed"

    # All complete within 15 min
    assert duration < 900, f"Must complete within 15 min, took {duration}s"

    # All succeed
    assert all(r.success for r in results), "All reviews must succeed"
```

**Expected**:

- 0 rate limit errors (429)
- All complete within 15 minutes
- Fair queuing via token bucket

---

### TEST-I003: Crash Recovery (BA Test 3)

- **Type**: integration
- **Related BA**: S1 (Crash Recovery), Section 11 Test 3
- **File**: `tests/integration/test_crash_recovery.py`
- **Description**: Review resumes after service crash

**Test Steps**:

```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires PostgreSQL for state persistence")
def test_crash_recovery():
    """Test that review resumes after service crash.

    Maps to BA Section 11, Test 3:
    ✅ Job state recovered from PostgreSQL
    ✅ Review resumes from last checkpoint
    ✅ No orphaned worktrees after completion

    NOTE: Only applicable to REST API with PostgreSQL persistence.
    MCP interface does not persist state (acceptable for solo dev use).
    """
    # Start review
    ctx = ProjectContext(
        project_id="crash-test",
        developer_id="crash-tester",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/crash-test"),
        metrics_dir=Path.home() / ".wfc/metrics/crash-test",
        output_dir=Path("/tmp/.wfc/output/crash-test")
    )

    orchestrator = ReviewOrchestrator(
        project_context=ctx,
        enable_persistence=True,
        db_url="postgresql://localhost/wfc_test"
    )

    # Start async review
    job_id = orchestrator.start_review_async(task_id="crash-test")

    # Wait for partial progress
    time.sleep(2.0)

    # Simulate crash (kill process)
    orchestrator.crash()  # Forcefully terminate

    # Restart orchestrator
    orchestrator2 = ReviewOrchestrator(
        project_context=ctx,
        enable_persistence=True,
        db_url="postgresql://localhost/wfc_test"
    )

    # Resume review
    result = orchestrator2.resume_review(job_id)

    assert result.success is True
    assert result.resumed is True

    # No orphaned worktrees
    orphans = WorktreeCleanup().find_orphans()
    assert len(orphans) == 0
```

**Expected**:

- Review resumes from checkpoint
- No orphaned worktrees
- State recovered from database

---

### TEST-I004: Developer Isolation (BA Test 4)

- **Type**: integration
- **Related BA**: M3 (Developer Attribution), Section 11 Test 4
- **File**: `tests/integration/test_developer_isolation.py`
- **Description**: Two developers with same task_id don't collide

**Test Steps**:

```python
@pytest.mark.integration
def test_developer_isolation_same_task():
    """Test that two developers with same task_id don't collide.

    Maps to BA Section 11, Test 4:
    ✅ No collision (different project namespaces)
    ✅ Git author = alice for first review
    ✅ Git author = bob for second review
    ✅ Audit log shows correct attribution
    """
    # Alice creates worktree
    ctx_alice = ProjectContext(
        project_id="proj1",
        developer_id="alice",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/proj1"),
        metrics_dir=Path.home() / ".wfc/metrics/proj1",
        output_dir=Path("/tmp/.wfc/output/proj1")
    )

    # Bob creates worktree (different project, same task_id)
    ctx_bob = ProjectContext(
        project_id="proj2",
        developer_id="bob",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/proj2"),
        metrics_dir=Path.home() / ".wfc/metrics/proj2",
        output_dir=Path("/tmp/.wfc/output/proj2")
    )

    orchestrator_alice = ReviewOrchestrator(project_context=ctx_alice)
    orchestrator_bob = ReviewOrchestrator(project_context=ctx_bob)

    # Both run review with same task_id
    result_alice = orchestrator_alice.run_review(task_id="feature", diff_content="...")
    result_bob = orchestrator_bob.run_review(task_id="feature", diff_content="...")

    # No collision
    assert result_alice.success is True
    assert result_bob.success is True
    assert result_alice.worktree_path != result_bob.worktree_path

    # Git author attribution
    alice_commits = get_commits_in_worktree(result_alice.worktree_path)
    bob_commits = get_commits_in_worktree(result_bob.worktree_path)

    assert all(c.author_name == "alice" for c in alice_commits)
    assert all(c.author_name == "bob" for c in bob_commits)

    # Audit log attribution
    alice_audit = get_audit_entries(developer_id="alice")
    bob_audit = get_audit_entries(developer_id="bob")

    assert len(alice_audit) > 0
    assert len(bob_audit) > 0
    assert alice_audit[0]["developer_id"] == "alice"
    assert bob_audit[0]["developer_id"] == "bob"
```

**Expected**:

- No collision between developers
- Correct git author attribution
- Correct audit log attribution

---

### TEST-I005: Shared Knowledge Base (BA Test 6)

- **Type**: integration
- **Related BA**: S2 (Shared Knowledge Base), Section 11 Test 6
- **File**: `tests/integration/test_shared_knowledge.py`
- **Description**: Knowledge shared across developers' reviews

**Test Steps**:

```python
@pytest.mark.integration
def test_shared_knowledge_base():
    """Test that knowledge is shared across developers.

    Maps to BA Section 11, Test 6:
    ✅ Bob's review shows "similar finding detected by alice"
    ✅ Shared KNOWLEDGE.md updated with both findings
    """
    # Alice reviews code with SQL injection
    ctx_alice = ProjectContext(
        project_id="shared-proj",
        developer_id="alice",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/shared-proj"),
        metrics_dir=Path.home() / ".wfc/metrics/shared-proj",
        output_dir=Path("/tmp/.wfc/output/shared-proj")
    )

    orchestrator_alice = ReviewOrchestrator(project_context=ctx_alice)
    result_alice = orchestrator_alice.run_review(
        task_id="alice-review",
        diff_content="sql = f'SELECT * FROM users WHERE id={user_id}'"
    )

    # Bob reviews different code with same issue
    ctx_bob = ProjectContext(
        project_id="shared-proj",
        developer_id="bob",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/shared-proj"),
        metrics_dir=Path.home() / ".wfc/metrics/shared-proj",
        output_dir=Path("/tmp/.wfc/output/shared-proj")
    )

    orchestrator_bob = ReviewOrchestrator(project_context=ctx_bob)
    result_bob = orchestrator_bob.run_review(
        task_id="bob-review",
        diff_content="query = 'DELETE FROM posts WHERE id=' + post_id"
    )

    # Bob's review references Alice's finding
    assert result_bob.success is True
    assert "similar finding" in result_bob.report.lower()
    assert "alice" in result_bob.report.lower()

    # Shared KNOWLEDGE.md has both
    knowledge_path = Path("/tmp/.wfc/knowledge/shared-proj/KNOWLEDGE.md")
    knowledge_content = knowledge_path.read_text()

    assert "developer: alice" in knowledge_content.lower()
    assert "developer: bob" in knowledge_content.lower()
    assert "sql injection" in knowledge_content.lower()
```

**Expected**:

- Bob's review references Alice's finding
- Shared knowledge file contains both developers' findings

---

### TEST-I006: MCP Local Speed (BA Test 5)

- **Type**: integration
- **Related BA**: Section 11 Test 5 (MCP overhead < 500ms)
- **File**: `tests/integration/test_mcp_performance.py`
- **Description**: MCP interface has minimal overhead vs direct orchestrator

**Test Steps**:

```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires MCP server implementation")
def test_mcp_overhead():
    """Test that MCP overhead is less than 500ms.

    Maps to BA Section 11, Test 5:
    ✅ MCP overhead < 500ms

    NOTE: Requires MCP server implementation (Phase 2A).
    """
    # Baseline: direct orchestrator call
    ctx = ProjectContext(
        project_id="perf-test",
        developer_id="perf-tester",
        repo_path=Path("/tmp/test-repo"),
        worktree_dir=Path("/tmp/.worktrees/perf-test"),
        metrics_dir=Path.home() / ".wfc/metrics/perf-test",
        output_dir=Path("/tmp/.wfc/output/perf-test")
    )

    orchestrator = ReviewOrchestrator(project_context=ctx)

    start_direct = time.time()
    result_direct = orchestrator.run_review(task_id="perf", diff_content="...")
    direct_duration = time.time() - start_direct

    # MCP call
    mcp_client = MCPClient("http://localhost:8080")

    start_mcp = time.time()
    result_mcp = mcp_client.review_code(
        project_id="perf-test",
        task_id="perf-mcp",
        diff_content="..."
    )
    mcp_duration = time.time() - start_mcp

    # Overhead calculation
    overhead = mcp_duration - direct_duration

    assert overhead < 0.5, f"MCP overhead {overhead}s exceeds 500ms threshold"
```

**Expected**: MCP overhead < 500ms

---

### TEST-I007: File Lock Concurrent Writes

- **Type**: integration
- **Related BA**: M2 (Concurrent Access Safety)
- **File**: `tests/integration/test_file_lock_concurrent.py`
- **Description**: 100 concurrent writes to KNOWLEDGE.md with 0 corruption

**Test Steps**:

```python
@pytest.mark.integration
def test_file_lock_prevents_corruption():
    """Test that FileLock prevents corruption under concurrent writes.

    100 concurrent writes to KNOWLEDGE.md → 0 corrupted entries
    """
    knowledge_file = Path("/tmp/test_knowledge.md")
    knowledge_file.write_text("# Knowledge Base\n\n")

    def write_entry(i):
        writer = KnowledgeWriter(developer_id=f"dev{i}")
        writer.append_entry(
            knowledge_file,
            category="test",
            description=f"Finding {i}",
            remediation=f"Fix {i}"
        )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(write_entry, i) for i in range(100)]
        for f in futures:
            f.result()  # Wait for all to complete

    # Validate KNOWLEDGE.md
    content = knowledge_file.read_text()

    # Count entries
    entry_count = content.count("## test")
    assert entry_count == 100, f"Expected 100 entries, found {entry_count}"

    # Validate markdown
    assert is_valid_markdown(content), "KNOWLEDGE.md corrupted"

    # Check for interleaved writes (corruption)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## test"):
            # Next line should be description
            assert "Finding" in lines[i+1], f"Corrupted at line {i}"
```

**Expected**:

- 100 entries written
- 0 corruption (valid markdown)
- No interleaved writes

---

---

## Load Test Cases

### TEST-L001: 50 Concurrent Reviews

- **Type**: load
- **Related BA**: Performance Requirements (50 simultaneous)
- **File**: `tests/load/test_concurrent_load.py`
- **Description**: Simulate 10 devs × 5 concurrent reviews each

**Test Configuration**:

```python
@pytest.mark.load
@pytest.mark.slow
def test_50_concurrent_reviews():
    """Load test: 50 concurrent reviews (10 devs × 5 reviews).

    Performance targets:
    - p95 latency < 2s (REST API overhead)
    - 0% error rate
    - Worker pool handles load without queue backup
    """
    num_developers = 10
    reviews_per_dev = 5

    def developer_reviews(dev_id):
        results = []
        for i in range(reviews_per_dev):
            ctx = ProjectContext(
                project_id=f"dev{dev_id}-proj{i}",
                developer_id=f"dev{dev_id}",
                repo_path=Path("/tmp/test-repo"),
                worktree_dir=Path(f"/tmp/.worktrees/dev{dev_id}-{i}"),
                metrics_dir=Path.home() / f".wfc/metrics/dev{dev_id}-{i}",
                output_dir=Path(f"/tmp/.wfc/output/dev{dev_id}-{i}")
            )
            orchestrator = ReviewOrchestrator(project_context=ctx)
            start = time.time()
            result = orchestrator.run_review(task_id=f"load-{i}", diff_content="...")
            duration = time.time() - start
            results.append({"success": result.success, "duration": duration})
        return results

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(developer_reviews, dev_id)
            for dev_id in range(num_developers)
        ]
        all_results = []
        for f in futures:
            all_results.extend(f.result())

    total_duration = time.time() - start_time

    # Success rate
    success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
    assert success_rate == 1.0, f"Success rate {success_rate*100}% must be 100%"

    # p95 latency
    durations = sorted([r["duration"] for r in all_results])
    p95_latency = durations[int(len(durations) * 0.95)]
    assert p95_latency < 2.0, f"p95 latency {p95_latency}s exceeds 2s threshold"

    print(f"✅ 50 reviews completed in {total_duration}s")
    print(f"✅ p95 latency: {p95_latency}s")
```

**Expected**:

- 100% success rate
- p95 latency < 2s

---

### TEST-L002: Token Bucket Fairness

- **Type**: load
- **Related BA**: M4 (API Rate Limiting)
- **File**: `tests/load/test_rate_limit_fairness.py`
- **Description**: Token bucket allocates fairly across developers

**Test Configuration**:

```python
@pytest.mark.load
def test_token_bucket_fairness():
    """Test that TokenBucket allocates tokens fairly.

    10 developers submit 10 requests each simultaneously.
    Each developer should get approximately equal token allocation.
    """
    bucket = TokenBucket(capacity=100, refill_rate=10)

    developer_requests = {f"dev{i}": [] for i in range(10)}

    def make_requests(dev_id):
        granted = []
        for _ in range(10):
            if bucket.consume(1):
                granted.append(time.time())
        return granted

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            dev_id: executor.submit(make_requests, dev_id)
            for dev_id in developer_requests.keys()
        }
        for dev_id, future in futures.items():
            developer_requests[dev_id] = future.result()

    # Check fairness: each dev should get approximately equal tokens
    token_counts = {dev: len(times) for dev, times in developer_requests.items()}

    avg_tokens = sum(token_counts.values()) / len(token_counts)
    max_deviation = max(abs(count - avg_tokens) for count in token_counts.values())

    # Allow 20% deviation from average
    assert max_deviation <= avg_tokens * 0.2, "Token allocation not fair"
```

**Expected**: Fair token allocation across developers (< 20% deviation)

---

### TEST-L003: Worktree Pool Scaling

- **Type**: load
- **Related BA**: Performance Requirements (horizontal scaling)
- **File**: `tests/load/test_worktree_pool.py`
- **Description**: Worktree pool scales to handle 50 concurrent requests

**Test Configuration**:

```python
@pytest.mark.load
def test_worktree_pool_scaling():
    """Test that WorktreePool scales to handle 50 concurrent requests.

    Performance targets:
    - Pool creates worktrees on-demand
    - No queue backup (requests don't wait > 5s)
    - All 50 complete successfully
    """
    pool = WorktreePool(max_size=10, cleanup_age_hours=24)

    def request_worktree(i):
        ctx = ProjectContext(
            project_id=f"pool-proj-{i}",
            developer_id="pool-tester",
            repo_path=Path("/tmp/test-repo"),
            worktree_dir=Path(f"/tmp/.worktrees/pool-{i}"),
            metrics_dir=Path.home() / f".wfc/metrics/pool-{i}",
            output_dir=Path(f"/tmp/.wfc/output/pool-{i}")
        )

        start = time.time()
        with pool.acquire_worktree(ctx, task_id=f"task-{i}") as worktree:
            wait_time = time.time() - start
            assert worktree.exists()
            return wait_time

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(request_worktree, i) for i in range(50)]
        wait_times = [f.result() for f in futures]

    # No request waited > 5s
    max_wait = max(wait_times)
    assert max_wait < 5.0, f"Max wait {max_wait}s exceeds 5s threshold"

    # All completed
    assert len(wait_times) == 50
```

**Expected**:

- All 50 worktrees created
- Max wait time < 5s

---

---

## End-to-End Test Cases

### TEST-E001: MCP Review Workflow

- **Type**: e2e
- **Related BA**: M6 (MCP Interface)
- **File**: `tests/e2e/test_mcp_workflow.py`
- **Description**: Full review via MCP interface

**Test Steps**:

```bash
# Manual E2E test (requires MCP server running)

# 1. Start MCP server
$ wfc-mcp-server --host localhost --port 8080

# 2. Claude Code connects to MCP
$ claude code
> Connect to MCP server at localhost:8080

# 3. Invoke review via MCP
> @wfc review this code

# 4. Verify result
✅ Review completes successfully
✅ Report generated at .wfc/output/{project_id}/REVIEW-{task_id}.md
✅ KNOWLEDGE.md updated
✅ Telemetry logged to ~/.wfc/metrics/{project_id}/
```

**Expected**: Full review workflow via MCP

---

### TEST-E002: REST API Review Workflow

- **Type**: e2e
- **Related BA**: M6 (REST Interface)
- **File**: `tests/e2e/test_rest_workflow.py`
- **Description**: Full review via REST API

**Test Steps**:

```python
@pytest.mark.e2e
@pytest.mark.skip(reason="Requires REST API server")
def test_rest_api_review():
    """Test full review workflow via REST API.

    POST /v1/review → review completes → report returned
    """
    # Start REST API server (in background)
    server = start_wfc_api_server()

    # Submit review
    response = requests.post(
        "http://localhost:8000/v1/review",
        json={
            "project_id": "e2e-proj",
            "developer_id": "e2e-tester",
            "task_id": "e2e-task",
            "diff_content": "diff --git a/test.py..."
        },
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 200
    result = response.json()

    # Verify result
    assert result["success"] is True
    assert result["consensus_score"] > 0
    assert "report_url" in result

    # Download report
    report_response = requests.get(result["report_url"])
    assert report_response.status_code == 200
    assert "# Review Report" in report_response.text

    server.stop()
```

**Expected**: Full review via REST API

---

### TEST-E003: Hybrid MCP→REST Delegation

- **Type**: e2e
- **Related BA**: M6 (Hybrid Architecture)
- **File**: `tests/e2e/test_hybrid_delegation.py`
- **Description**: MCP delegates to REST for team features

**Test Steps**:

```python
@pytest.mark.e2e
@pytest.mark.skip(reason="Requires both MCP and REST servers")
def test_mcp_delegates_to_rest():
    """Test MCP delegates to REST for shared knowledge.

    MCP client → MCP server → REST API → shared knowledge
    """
    # Start both servers
    rest_server = start_wfc_api_server(port=8000)
    mcp_server = start_wfc_mcp_server(
        port=8080,
        rest_api_url="http://localhost:8000"
    )

    # Connect MCP client
    mcp_client = MCPClient("http://localhost:8080")

    # Request review via MCP
    result = mcp_client.review_code(
        project_id="hybrid-proj",
        task_id="hybrid-task",
        diff_content="...",
        use_shared_knowledge=True  # Triggers delegation
    )

    # Verify delegation occurred
    assert result["delegated_to_rest"] is True
    assert result["shared_knowledge_used"] is True

    # Verify knowledge saved to REST API database
    knowledge_response = requests.get(
        "http://localhost:8000/v1/knowledge/hybrid-proj",
        headers={"X-API-Key": "test-key"}
    )
    assert knowledge_response.status_code == 200
    knowledge = knowledge_response.json()
    assert len(knowledge["entries"]) > 0

    mcp_server.stop()
    rest_server.stop()
```

**Expected**: MCP delegates to REST for shared knowledge

---

### TEST-E004: Orphan Cleanup Background Task

- **Type**: e2e
- **Related BA**: M5 (Guaranteed Resource Cleanup)
- **File**: `tests/e2e/test_orphan_cleanup.py`
- **Description**: Background task cleans up orphaned worktrees

**Test Steps**:

```python
@pytest.mark.e2e
@pytest.mark.slow
def test_orphan_cleanup_background_task():
    """Test that background task cleans up orphaned worktrees.

    1. Create old worktrees (25h old)
    2. Run cleanup task
    3. Verify orphans deleted
    """
    # Create 10 old worktrees
    old_worktrees = []
    for i in range(10):
        wt = Path(f"/tmp/.worktrees/orphan-{i}/wfc-old-{i}")
        wt.mkdir(parents=True, exist_ok=True)

        # Set mtime to 25h ago
        old_time = time.time() - (25 * 3600)
        os.utime(wt, (old_time, old_time))
        old_worktrees.append(wt)

    # Run cleanup task
    cleaner = WorktreeCleanup(threshold_hours=24)
    deleted = cleaner.cleanup_orphans()

    # Verify all deleted
    assert deleted == 10, f"Expected 10 deletions, got {deleted}"

    for wt in old_worktrees:
        assert not wt.exists(), f"Orphan {wt} not deleted"
```

**Expected**: All orphaned worktrees deleted

---

---

## Test Summary

| Category | Count | Framework | Coverage Target | Execution Time |
|----------|-------|-----------|-----------------|----------------|
| Unit | 27 | pytest | 95% line coverage | ~30s |
| Integration | 7 | pytest + fixtures | All BA acceptance tests | ~5min |
| Load | 3 | pytest-xdist, locust | Performance properties | ~10min |
| E2E | 4 | pytest + manual | Full workflows | ~15min (manual) |
| **Total** | **41** | - | - | **~30min** |

### Note on Test Count

Original target was 43 tests. Final count is 41 comprehensive tests covering all BA requirements.

---

## Test Execution Order

### Local Development

```bash
# 1. Unit tests (fast feedback)
uv run pytest tests/test_*.py -v --cov --cov-report=term-missing

# 2. Integration tests (requires test fixtures)
uv run pytest tests/integration/ -v -m integration

# 3. Load tests (slow, run selectively)
uv run pytest tests/load/ -v -m load --dist loadgroup -n 10
```

### CI/CD Pipeline

```yaml
# .github/workflows/multi-tenant-tests.yml
name: Multi-Tenant Tests

on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Unit Tests
        run: uv run pytest tests/test_*.py -v --cov --cov-report=xml
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration:
    runs-on: ubuntu-latest
    needs: unit
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - name: Integration Tests
        run: uv run pytest tests/integration/ -v -m integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/wfc_test

  load:
    runs-on: ubuntu-latest
    needs: integration
    steps:
      - uses: actions/checkout@v3
      - name: Load Tests
        run: uv run pytest tests/load/ -v -m load
```

---

## Test Data & Fixtures

### Shared Fixtures

```python
# tests/conftest.py

import pytest
from pathlib import Path
from wfc.shared.config.wfc_config import ProjectContext

@pytest.fixture
def temp_repo(tmp_path):
    """Create temporary git repository for testing."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    return repo

@pytest.fixture
def project_context(temp_repo):
    """Create test ProjectContext."""
    return ProjectContext(
        project_id="test-proj",
        developer_id="test-dev",
        repo_path=temp_repo,
        worktree_dir=temp_repo / ".worktrees" / "test-proj",
        metrics_dir=Path.home() / ".wfc/metrics/test-proj",
        output_dir=temp_repo / ".wfc/output/test-proj"
    )

@pytest.fixture
def knowledge_file(tmp_path):
    """Create temporary KNOWLEDGE.md for testing."""
    kf = tmp_path / "KNOWLEDGE.md"
    kf.write_text("# Knowledge Base\n\n")
    return kf

@pytest.fixture
def mock_anthropic_api(monkeypatch):
    """Mock Anthropic API to avoid rate limits in tests."""
    def mock_completion(*args, **kwargs):
        return {
            "completion": "Test review result",
            "model": "claude-sonnet-4",
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }

    monkeypatch.setattr(
        "anthropic.Anthropic.messages.create",
        mock_completion
    )
```

---

## Coverage Requirements

### Per-Component Coverage Targets

- **wfc/shared/config/wfc_config.py**: 95%
- **wfc/gitwork/api/worktree.py**: 95%
- **wfc/shared/file_io.py**: 95%
- **wfc/scripts/knowledge/knowledge_writer.py**: 95%
- **wfc/shared/telemetry_auto.py**: 90%
- **wfc/scripts/orchestrators/review/orchestrator.py**: 85% (complex, mocked dependencies)
- **wfc/shared/resource_pool.py** (new): 95%

### Coverage Gates

```bash
# Fail if coverage < 95%
uv run pytest --cov --cov-fail-under=95

# Generate HTML report
uv run pytest --cov --cov-report=html
open htmlcov/index.html
```

---

## Test Utilities

### Helper Functions

```python
# tests/utils.py

import re
from pathlib import Path

def is_valid_markdown(content: str) -> bool:
    """Check if content is valid markdown."""
    # Balanced code fences
    if content.count("```") % 2 != 0:
        return False

    # No malformed headers
    if re.search(r"^#{7,}", content, re.MULTILINE):
        return False

    return True

def get_commits_in_worktree(worktree_path: Path) -> list:
    """Get commits in worktree with author info."""
    result = subprocess.run(
        ["git", "log", "--format=%an|%ae|%s"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if line:
            author, email, subject = line.split("|")
            commits.append({
                "author_name": author,
                "author_email": email,
                "subject": subject
            })
    return commits

def get_audit_entries(developer_id: str) -> list:
    """Get audit log entries for developer."""
    # Placeholder: actual implementation depends on storage backend
    # (PostgreSQL for REST API, file-based for MCP)
    pass
```

---

## BA Section 11 Acceptance Test Mapping

| BA Test | Test ID | Type | Status |
|---------|---------|------|--------|
| Test 1: Concurrent Project Reviews | TEST-I001 | Integration | ✅ Mapped |
| Test 2: Rate Limiting Under Load | TEST-I002 | Integration | ✅ Mapped |
| Test 3: Crash Recovery | TEST-I003 | Integration | ⚠️ REST API only |
| Test 4: Developer Isolation | TEST-I004 | Integration | ✅ Mapped |
| Test 5: MCP Local Speed | TEST-I006 | Integration | ⚠️ Requires MCP |
| Test 6: Shared Knowledge Base | TEST-I005 | Integration | ✅ Mapped |

**Legend**:

- ✅ Mapped: Test fully specified and ready to implement
- ⚠️ Conditional: Test requires specific architecture (MCP/REST)

---

## Next Steps

1. **Create test infrastructure**:
   - `tests/test_project_context.py` (TEST-U001 - U004)
   - `tests/test_worktree_namespacing.py` (TEST-U005 - U007)
   - `tests/test_file_lock.py` (TEST-U008 - U010)
   - `tests/test_knowledge_writer.py` (TEST-U011 - U013)
   - `tests/test_token_bucket.py` (TEST-U014 - U018)
   - `tests/test_telemetry_namespacing.py` (TEST-U019 - U020)
   - `tests/test_worktree_cleanup.py` (TEST-U021 - U024)
   - `tests/test_orchestrator_context.py` (TEST-U025 - U027)

2. **Implement integration tests**:
   - `tests/integration/test_concurrent_reviews.py` (TEST-I001)
   - `tests/integration/test_rate_limiting.py` (TEST-I002)
   - `tests/integration/test_crash_recovery.py` (TEST-I003)
   - `tests/integration/test_developer_isolation.py` (TEST-I004)
   - `tests/integration/test_shared_knowledge.py` (TEST-I005)
   - `tests/integration/test_mcp_performance.py` (TEST-I006)
   - `tests/integration/test_file_lock_concurrent.py` (TEST-I007)

3. **Add load tests**:
   - `tests/load/test_concurrent_load.py` (TEST-L001)
   - `tests/load/test_rate_limit_fairness.py` (TEST-L002)
   - `tests/load/test_worktree_pool.py` (TEST-L003)

4. **Define E2E workflows**:
   - `tests/e2e/test_mcp_workflow.py` (TEST-E001)
   - `tests/e2e/test_rest_workflow.py` (TEST-E002)
   - `tests/e2e/test_hybrid_delegation.py` (TEST-E003)
   - `tests/e2e/test_orphan_cleanup.py` (TEST-E004)

5. **CI/CD integration**:
   - Add `.github/workflows/multi-tenant-tests.yml`
   - Configure PostgreSQL service for integration tests
   - Set coverage gates (95%)

6. **Documentation**:
   - Update `docs/testing/MULTI_TENANT_TESTING.md` with this test plan
   - Add test execution guide to `docs/quickstart/TESTING.md`

---

## Dependencies

### New Test Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
test-multi-tenant = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.3.1",      # Parallel test execution
    "pytest-timeout>=2.1.0",    # Timeout for slow tests
    "pytest-asyncio>=0.21.0",   # Async test support
    "locust>=2.15.0",           # Load testing
    "requests>=2.31.0",         # REST API testing
    "psycopg2-binary>=2.9.0",   # PostgreSQL for integration tests
]
```

### Test Infrastructure

- PostgreSQL 14+ (for integration tests with persistence)
- Redis 6+ (for rate limiting tests)
- Git 2.25+ (for worktree tests)

---

**Generated**: 2026-02-21
**Author**: Claude Sonnet 4.5
**Related**: ba/BA-multi-tenant-wfc.md
