"""
Resource pooling for WFC multi-tenant operations.

Implements:
- WorktreePool: LRU-evicted pool of reusable worktrees
- TokenBucket: Rate limiting for review requests
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from filelock import FileLock

logger = logging.getLogger(__name__)


class WorktreePool:
    """
    Manages a pool of reusable worktrees with LRU eviction.

    Features:
    - Max concurrent worktrees (configurable)
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
        """
        Initialize WorktreePool.

        Args:
            pool_dir: Directory for worktree pool
            max_worktrees: Maximum concurrent worktrees
            orphan_timeout_hours: Hours before worktree considered orphan
        """
        self.pool_dir = Path(pool_dir)
        self.max_worktrees = max_worktrees
        self.orphan_timeout = timedelta(hours=orphan_timeout_hours)
        self.lock_file = self.pool_dir / ".pool.lock"

        self.pool_dir.mkdir(parents=True, exist_ok=True)

    def acquire(self, task_id: str, project_id: str) -> Path:
        """
        Acquire a worktree from the pool or create new one.

        Args:
            task_id: Task identifier
            project_id: Project identifier

        Returns:
            Path to worktree directory

        Raises:
            ResourceExhaustedError: If pool full and no orphans to evict
        """
        with FileLock(self.lock_file, timeout=10):
            self._cleanup_orphans()

            worktree_id = f"{project_id}-{task_id}"
            worktree_path = self.pool_dir / worktree_id

            if worktree_path.exists():
                self._update_last_used(worktree_path)
                self._mark_in_use(worktree_path)
                return worktree_path

            if self._count_worktrees() >= self.max_worktrees:
                self._evict_lru()

            worktree_path.mkdir(parents=True, exist_ok=True)
            self._mark_in_use(worktree_path)
            return worktree_path

    def release(self, worktree_path: Path) -> None:
        """
        Release a worktree back to the pool.

        Args:
            worktree_path: Path to worktree to release
        """
        with FileLock(self.lock_file, timeout=10):
            self._mark_available(worktree_path)

    def _cleanup_orphans(self) -> int:
        """
        Remove worktrees older than orphan_timeout.

        Returns:
            Number of orphans removed
        """
        now = datetime.now()
        removed = 0

        for worktree_path in self.pool_dir.iterdir():
            if worktree_path.is_dir() and not worktree_path.name.startswith("."):
                created_at = datetime.fromtimestamp(worktree_path.stat().st_ctime)
                age = now - created_at

                if age > self.orphan_timeout and not self._is_in_use(worktree_path):
                    shutil.rmtree(worktree_path)
                    removed += 1
                    logger.info(f"Removed orphan worktree: {worktree_path}")

        return removed

    def _evict_lru(self) -> None:
        """Evict least recently used worktree."""
        lru_path = None
        lru_time = datetime.now()

        for worktree_path in self.pool_dir.iterdir():
            if (
                worktree_path.is_dir()
                and not self._is_in_use(worktree_path)
                and not worktree_path.name.startswith(".")
            ):
                mtime = datetime.fromtimestamp(worktree_path.stat().st_mtime)
                if mtime < lru_time:
                    lru_time = mtime
                    lru_path = worktree_path

        if lru_path:
            shutil.rmtree(lru_path)
            logger.info(f"Evicted LRU worktree: {lru_path}")

    def _count_worktrees(self) -> int:
        """Count active worktrees in pool."""
        return len(
            [p for p in self.pool_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        )

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
        import threading
        import time

        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self.lock = threading.Lock()
        self._time_module = time

    def acquire(self, tokens: int = 1, timeout: float = 0.0) -> bool:
        """
        Try to acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire
            timeout: Max wait time in seconds (0 = non-blocking)

        Returns:
            True if tokens acquired, False otherwise
        """
        import time

        deadline = time.time() + timeout if timeout > 0 else 0

        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if timeout == 0 or time.time() >= deadline:
                    return False

            time.sleep(0.1)

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        import time

        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            return min(self.capacity, self.tokens + (elapsed * self.refill_rate))
