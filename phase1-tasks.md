---
title: Multi-Tenant WFC - Phase 1 Continuation
status: active
created: 2026-02-21T12:00:00Z
updated: 2026-02-21T12:00:00Z
tier0_complete: 2026-02-21 (58/58 tests passing)
tasks_total: 15
tasks_completed: 0
complexity: L
---

# Phase 1: Integration & Resource Pooling

**Context**: Tier 0 MVP complete (100% tests passing). Core primitives implemented:

- ✅ ProjectContext with namespaced paths
- ✅ WorktreeOperations with project_id
- ✅ FileLock for concurrent writes
- ✅ AutoTelemetry with project_id
- ✅ KnowledgeWriter with developer_id
- ✅ worktree-manager.sh with attribution

**Goal**: Integrate multi-tenant primitives into review orchestrator and add resource pooling (WorktreePool, TokenBucket) for production use.

**Timeline**: 2-3 days (15 tasks × 30min avg = 7.5 hours)

---

## TASK-008: Integrate ProjectContext into ReviewOrchestrator

**File**: `wfc/scripts/orchestrators/review/orchestrator.py`
**Complexity**: M (50-200 lines)
**Dependencies**: [Tier 0 complete]
**Properties**: [M1-Project-Isolation, M3-Developer-Attribution]
**Estimated Time**: 45min
**Agent Level**: Sonnet

### Description

Update ReviewOrchestrator to accept ProjectContext and use namespaced paths for all outputs (reports, metrics, worktrees).

### Code Pattern Example

```python
from wfc.shared.config.wfc_config import ProjectContext

class ReviewOrchestrator:
    def __init__(
        self,
        config: WFCConfig,
        project_context: Optional[ProjectContext] = None,  # NEW
    ):
        self.config = config
        self.project_context = project_context  # NEW

        # Use namespaced output directory if project_context provided
        if project_context:
            self.output_dir = project_context.output_dir
        else:
            self.output_dir = Path(".wfc/output")  # Legacy default

    def _create_worktree_operations(self) -> WorktreeOperations:
        """Create WorktreeOperations with project namespacing."""
        if self.project_context:
            return WorktreeOperations(project_id=self.project_context.project_id)
        else:
            return WorktreeOperations()  # Legacy behavior

    def _generate_report(self, findings: List[Finding]) -> Path:
        """Generate report in project-namespaced directory."""
        report_name = f"REVIEW-{self.project_context.project_id if self.project_context else 'global'}.md"
        report_path = self.output_dir / report_name
        # ... generate report
        return report_path
```

### Acceptance Criteria

- [ ] project_context parameter added to `__init__`
- [ ] Output directory uses project_context.output_dir when provided
- [ ] WorktreeOperations created with project_id
- [ ] Report filename includes project_id
- [ ] Backward compatible (None → legacy paths)
- [ ] Unit test: `test_orchestrator_with_project_context`

---

## TASK-009: Thread developer_id to KnowledgeWriter

**File**: `wfc/scripts/orchestrators/review/orchestrator.py`
**Complexity**: S (10-50 lines)
**Dependencies**: [TASK-008]
**Properties**: [M3-Developer-Attribution]
**Estimated Time**: 20min
**Agent Level**: Haiku

### Description

Pass developer_id from ProjectContext to KnowledgeWriter so all learning entries are attributed.

### Code Pattern Example

```python
def _extract_learnings(self, findings: List[Finding]) -> None:
    """Extract learnings and write to knowledge base with developer attribution."""
    writer = KnowledgeWriter(reviewers_dir=self.config.reviewers_dir)

    learnings = []
    for finding in findings:
        if finding.should_learn:
            entry = LearningEntry(
                text=finding.description,
                section=finding.category,
                reviewer_id=finding.reviewer_id,
                source=finding.file_path,
                developer_id=self.project_context.developer_id if self.project_context else "",
            )
            learnings.append(entry)

    if learnings:
        writer.append_entries(learnings)
```

### Acceptance Criteria

- [ ] developer_id passed to LearningEntry from project_context
- [ ] Falls back to empty string if project_context is None
- [ ] Unit test: `test_learnings_include_developer_id`

---

## TASK-010: Create WorktreePool with resource pooling

**File**: `wfc/shared/resource_pool.py` (new file)
**Complexity**: L (200-500 lines)
**Dependencies**: [Tier 0 TASK-003 FileLock]
**Properties**: [M2-Concurrent-Access-Safety, PROP-P001, PROP-L001]
**Estimated Time**: 60min
**Agent Level**: Sonnet

### Description

Implement WorktreePool class that manages a pool of reusable worktrees with:

- Max concurrent worktrees (configurable)
- LRU eviction when pool full
- Orphan cleanup (worktrees older than 24h)
- File-based locking for concurrent access

### Code Pattern Example

```python
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from filelock import FileLock
import shutil

@dataclass
class WorktreeEntry:
    """Metadata for a pooled worktree."""
    worktree_id: str
    path: Path
    created_at: datetime
    last_used: datetime
    in_use: bool

class WorktreePool:
    """
    Manages a pool of reusable worktrees with LRU eviction.

    Features:
    - Max concurrent worktrees (default: 10)
    - Automatic cleanup of orphans (>24h old)
    - File-based locking for concurrent safety
    - LRU eviction when pool full
    """

    def __init__(
        self,
        pool_dir: Path,
        max_worktrees: int = 10,
        orphan_timeout_hours: int = 24,
    ):
        self.pool_dir = Path(pool_dir)
        self.max_worktrees = max_worktrees
        self.orphan_timeout = timedelta(hours=orphan_timeout_hours)
        self.lock_file = self.pool_dir / ".pool.lock"

        # Create pool directory
        self.pool_dir.mkdir(parents=True, exist_ok=True)

    def acquire(self, task_id: str, project_id: str) -> Path:
        """
        Acquire a worktree from the pool or create new one.

        Returns:
            Path to worktree directory

        Raises:
            ResourceExhaustedError: If pool full and no orphans to evict
        """
        with FileLock(self.lock_file, timeout=10):
            # Cleanup orphans first
            self._cleanup_orphans()

            # Check if worktree already exists for this task
            worktree_id = f"{project_id}-{task_id}"
            worktree_path = self.pool_dir / worktree_id

            if worktree_path.exists():
                # Reuse existing worktree
                self._update_last_used(worktree_path)
                return worktree_path

            # Check pool capacity
            if self._count_worktrees() >= self.max_worktrees:
                # Evict LRU worktree
                self._evict_lru()

            # Create new worktree
            worktree_path.mkdir(parents=True, exist_ok=True)
            self._mark_in_use(worktree_path)
            return worktree_path

    def release(self, worktree_path: Path) -> None:
        """Release a worktree back to the pool."""
        with FileLock(self.lock_file, timeout=10):
            self._mark_available(worktree_path)

    def _cleanup_orphans(self) -> int:
        """Remove worktrees older than orphan_timeout."""
        now = datetime.now()
        removed = 0

        for worktree_path in self.pool_dir.iterdir():
            if worktree_path.is_dir() and not worktree_path.name.startswith("."):
                created_at = datetime.fromtimestamp(worktree_path.stat().st_ctime)
                age = now - created_at

                if age > self.orphan_timeout and not self._is_in_use(worktree_path):
                    shutil.rmtree(worktree_path)
                    removed += 1

        return removed

    def _evict_lru(self) -> None:
        """Evict least recently used worktree."""
        # Find LRU worktree (oldest mtime)
        lru_path = None
        lru_time = datetime.now()

        for worktree_path in self.pool_dir.iterdir():
            if worktree_path.is_dir() and not self._is_in_use(worktree_path):
                mtime = datetime.fromtimestamp(worktree_path.stat().st_mtime)
                if mtime < lru_time:
                    lru_time = mtime
                    lru_path = worktree_path

        if lru_path:
            shutil.rmtree(lru_path)

    def _count_worktrees(self) -> int:
        """Count active worktrees in pool."""
        return len([p for p in self.pool_dir.iterdir() if p.is_dir() and not p.name.startswith(".")])

    def _is_in_use(self, worktree_path: Path) -> bool:
        """Check if worktree is currently in use."""
        lock_file = worktree_path / ".in_use"
        return lock_file.exists()

    def _mark_in_use(self, worktree_path: Path) -> None:
        """Mark worktree as in use."""
        lock_file = worktree_path / ".in_use"
        lock_file.touch()

    def _mark_available(self, worktree_path: Path) -> None:
        """Mark worktree as available."""
        lock_file = worktree_path / ".in_use"
        if lock_file.exists():
            lock_file.unlink()

    def _update_last_used(self, worktree_path: Path) -> None:
        """Update last used timestamp."""
        worktree_path.touch()
```

### Acceptance Criteria

- [ ] WorktreePool class implemented
- [ ] acquire() creates or reuses worktrees
- [ ] release() marks worktree available
- [ ] Orphan cleanup removes worktrees >24h old
- [ ] LRU eviction when pool full
- [ ] File-based locking for concurrent safety
- [ ] Unit tests:
  - [ ] `test_acquire_creates_new_worktree`
  - [ ] `test_acquire_reuses_existing`
  - [ ] `test_eviction_when_full`
  - [ ] `test_cleanup_orphans`
  - [ ] `test_concurrent_acquire_release`

---

## TASK-011: Create TokenBucket for rate limiting

**File**: `wfc/shared/resource_pool.py` (append to file)
**Complexity**: M (50-200 lines)
**Dependencies**: [TASK-010]
**Properties**: [PROP-P002, M2-Concurrent-Access-Safety]
**Estimated Time**: 30min
**Agent Level**: Haiku

### Description

Implement TokenBucket class for rate limiting review requests (default: 10 reviews/minute).

### Code Pattern Example

```python
from threading import Lock
from time import time

class TokenBucket:
    """
    Token bucket rate limiter for review requests.

    Allows burst of requests up to capacity, then enforces rate limit.
    Thread-safe for concurrent access.
    """

    def __init__(self, capacity: int = 10, refill_rate: float = 10.0):
        """
        Initialize token bucket.

        Args:
            capacity: Max tokens (max burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time()
        self.lock = Lock()

    def acquire(self, tokens: int = 1, timeout: float = 0.0) -> bool:
        """
        Try to acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire
            timeout: Max wait time in seconds (0 = non-blocking)

        Returns:
            True if tokens acquired, False otherwise
        """
        deadline = time() + timeout if timeout > 0 else 0

        while True:
            with self.lock:
                # Refill bucket based on elapsed time
                now = time()
                elapsed = now - self.last_refill
                self.tokens = min(
                    self.capacity,
                    self.tokens + (elapsed * self.refill_rate)
                )
                self.last_refill = now

                # Try to acquire tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Check timeout
                if timeout == 0 or time() >= deadline:
                    return False

            # Wait a bit before retry
            time.sleep(0.1)

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            now = time()
            elapsed = now - self.last_refill
            return min(
                self.capacity,
                self.tokens + (elapsed * self.refill_rate)
            )
```

### Acceptance Criteria

- [ ] TokenBucket class implemented
- [ ] acquire() enforces rate limit
- [ ] Refills tokens based on elapsed time
- [ ] Thread-safe with Lock
- [ ] Unit tests:
  - [ ] `test_acquire_within_capacity`
  - [ ] `test_acquire_blocks_when_empty`
  - [ ] `test_refill_over_time`
  - [ ] `test_concurrent_acquire`

---

## TASK-012: Add background orphan cleanup daemon

**File**: `wfc/scripts/daemons/orphan_cleanup.py` (new file)
**Complexity**: M (50-200 lines)
**Dependencies**: [TASK-010]
**Properties**: [PROP-L001]
**Estimated Time**: 30min
**Agent Level**: Haiku

### Description

Create background daemon that runs orphan cleanup every 6 hours, ensuring PROP-L001 (eventual cleanup) is satisfied.

### Code Pattern Example

```python
import asyncio
from pathlib import Path
from wfc.shared.resource_pool import WorktreePool
import logging

logger = logging.getLogger(__name__)

class OrphanCleanupDaemon:
    """
    Background daemon that periodically cleans up orphaned worktrees.

    Runs every cleanup_interval_hours to ensure PROP-L001 is satisfied:
    "All worktrees older than 24h with no active process MUST EVENTUALLY be deleted."
    """

    def __init__(
        self,
        pool_dir: Path,
        cleanup_interval_hours: int = 6,
        orphan_timeout_hours: int = 24,
    ):
        self.pool_dir = Path(pool_dir)
        self.cleanup_interval = cleanup_interval_hours * 3600  # Convert to seconds
        self.orphan_timeout = orphan_timeout_hours
        self.running = False

    async def start(self) -> None:
        """Start the cleanup daemon."""
        self.running = True
        logger.info(f"Starting orphan cleanup daemon (interval: {self.cleanup_interval/3600}h)")

        while self.running:
            try:
                # Run cleanup
                pool = WorktreePool(
                    pool_dir=self.pool_dir,
                    orphan_timeout_hours=self.orphan_timeout,
                )
                removed = pool._cleanup_orphans()

                if removed > 0:
                    logger.info(f"Cleaned up {removed} orphaned worktrees")

            except Exception as e:
                logger.error(f"Orphan cleanup failed: {e}")

            # Sleep until next cleanup
            await asyncio.sleep(self.cleanup_interval)

    def stop(self) -> None:
        """Stop the cleanup daemon."""
        self.running = False
        logger.info("Stopping orphan cleanup daemon")

# CLI entry point
async def main():
    import argparse

    parser = argparse.ArgumentParser(description="WFC Orphan Cleanup Daemon")
    parser.add_argument("--pool-dir", default=".worktrees", help="Worktree pool directory")
    parser.add_argument("--interval", type=int, default=6, help="Cleanup interval (hours)")
    parser.add_argument("--timeout", type=int, default=24, help="Orphan timeout (hours)")
    args = parser.parse_args()

    daemon = OrphanCleanupDaemon(
        pool_dir=Path(args.pool_dir),
        cleanup_interval_hours=args.interval,
        orphan_timeout_hours=args.timeout,
    )

    await daemon.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Acceptance Criteria

- [ ] OrphanCleanupDaemon class implemented
- [ ] Runs cleanup every cleanup_interval_hours
- [ ] Uses WorktreePool._cleanup_orphans()
- [ ] Graceful start/stop
- [ ] Logging for cleanup events
- [ ] CLI entry point for running as daemon
- [ ] Unit test: `test_daemon_runs_periodic_cleanup`

---

## TASK-013: Update wfc-review skill to use ProjectContext

**File**: `~/.claude/skills/wfc-review/PROMPT.md`
**Complexity**: S (10-50 lines)
**Dependencies**: [TASK-008, TASK-009]
**Properties**: [M1-Project-Isolation, M3-Developer-Attribution]
**Estimated Time**: 15min
**Agent Level**: Haiku

### Description

Update wfc-review skill prompt to accept --project-id and --developer-id flags and create ProjectContext.

### Code Pattern Example

```markdown
## Usage

```bash
/wfc-review [--project-id PROJECT_ID] [--developer-id DEVELOPER_ID] [FILE_PATTERN]
```

## Implementation

1. Parse --project-id and --developer-id flags (optional)
2. If flags provided, create ProjectContext:

   ```python
   from wfc.shared.config.wfc_config import WFCConfig

   config = WFCConfig()
   project_context = config.create_project_context(
       project_id=args.project_id,
       developer_id=args.developer_id,
   )
   ```

3. Pass project_context to ReviewOrchestrator:

   ```python
   orchestrator = ReviewOrchestrator(
       config=config,
       project_context=project_context,
   )
   ```

4. Run review as normal

```

### Acceptance Criteria

- [ ] --project-id flag documented
- [ ] --developer-id flag documented
- [ ] Prompts user to provide both or neither
- [ ] Creates ProjectContext when flags present
- [ ] Falls back to legacy mode when flags absent

---

## Next 10 Tasks (TASK-014 through TASK-023)

The remaining tasks will focus on:

1. **MCP Interface** (TASK-014 to TASK-018):
   - Create MCP server with review tool
   - Integrate ProjectContext into MCP
   - Add resource limits (WorktreePool, TokenBucket)

2. **REST API Interface** (TASK-019 to TASK-023):
   - Create FastAPI server
   - Add authentication (API keys)
   - Add async review endpoints
   - Add PostgreSQL for persistence
   - Add health/metrics endpoints

3. **Testing & Documentation** (TASK-024 to TASK-028):
   - Integration tests for MCP
   - Integration tests for REST API
   - Load testing (100 concurrent reviews)
   - Documentation updates
   - Migration guide

**Note**: These tasks will be defined in detail once Phase 1 core tasks (TASK-008 to TASK-013) are complete and validated.

---

## Success Criteria (Phase 1)

1. ✅ ReviewOrchestrator accepts ProjectContext
2. ✅ Developer attribution flows to knowledge base
3. ✅ WorktreePool manages concurrent reviews
4. ✅ TokenBucket enforces rate limits
5. ✅ Orphan cleanup runs in background
6. ✅ wfc-review skill supports --project-id/--developer-id
7. ✅ All existing tests still pass (backward compat)
8. ✅ New unit tests pass (15+ new tests)

---

## Stop/Go Decision Gate

After completing Phase 1 tasks (TASK-008 to TASK-013):

**Question**: Does the integrated system work correctly with resource pooling?

**Tests to validate**:
- Run 10 concurrent reviews with different project_ids → 0 collisions
- Verify WorktreePool evicts LRU when capacity reached
- Verify TokenBucket blocks requests when rate exceeded
- Verify orphan cleanup removes worktrees >24h old
- Verify all knowledge entries have developer attribution

**Decision**:
- **STOP** if integration issues found → debug before continuing to MCP/REST
- **GO to MCP/REST** if all tests pass → proceed with interfaces
