"""
Phase 1 - TASK-010 Tests
Test WorktreePool resource pooling with LRU eviction and orphan cleanup.
"""

import time
from wfc.shared.resource_pool import WorktreePool


class TestWorktreePool:
    """Test WorktreePool resource management."""

    def test_worktree_pool_initialization(self, tmp_path):
        """WorktreePool should initialize with pool directory."""
        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=10)

        assert pool.pool_dir == tmp_path
        assert pool.max_worktrees == 10
        assert pool.pool_dir.exists()

    def test_acquire_creates_new_worktree(self, tmp_path):
        """acquire() should create new worktree if it doesn't exist."""
        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=10)

        worktree_path = pool.acquire(task_id="task-001", project_id="proj1")

        assert worktree_path.exists()
        assert worktree_path.is_dir()
        assert "proj1-task-001" in str(worktree_path)

    def test_acquire_reuses_existing_worktree(self, tmp_path):
        """acquire() should reuse existing worktree for same task/project."""
        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=10)

        path1 = pool.acquire(task_id="task-001", project_id="proj1")

        pool.release(path1)

        path2 = pool.acquire(task_id="task-001", project_id="proj1")

        assert path1 == path2

    def test_pool_respects_max_worktrees(self, tmp_path):
        """Pool should not exceed max_worktrees capacity."""
        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=3)

        path1 = pool.acquire("task-001", "proj1")
        pool.release(path1)
        path2 = pool.acquire("task-002", "proj1")
        pool.release(path2)
        path3 = pool.acquire("task-003", "proj1")
        pool.release(path3)

        path4 = pool.acquire("task-004", "proj1")

        assert path4.exists()
        worktrees = [p for p in tmp_path.iterdir() if p.is_dir() and not p.name.startswith(".")]
        assert len(worktrees) <= 3

    def test_evict_lru_removes_oldest(self, tmp_path):
        """LRU eviction should remove least recently used worktree."""
        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=2)

        path1 = pool.acquire("task-001", "proj1")
        pool.release(path1)

        time.sleep(0.1)

        path2 = pool.acquire("task-002", "proj1")
        pool.release(path2)

        path3 = pool.acquire("task-003", "proj1")

        assert not path1.exists()
        assert path2.exists()
        assert path3.exists()

    def test_cleanup_orphans_removes_old_worktrees(self, tmp_path):
        """Orphan cleanup should remove worktrees older than timeout."""
        pool = WorktreePool(pool_dir=tmp_path, orphan_timeout_hours=0.0001)

        path = pool.acquire("task-001", "proj1")
        pool.release(path)

        time.sleep(0.5)

        removed = pool._cleanup_orphans()

        assert removed == 1
        assert not path.exists()

    def test_cleanup_orphans_preserves_in_use_worktrees(self, tmp_path):
        """Orphan cleanup should NOT remove worktrees currently in use."""
        pool = WorktreePool(pool_dir=tmp_path, orphan_timeout_hours=0.0001)

        path = pool.acquire("task-001", "proj1")

        time.sleep(0.5)

        removed = pool._cleanup_orphans()

        assert removed == 0
        assert path.exists()

    def test_release_marks_worktree_available(self, tmp_path):
        """release() should mark worktree as available for reuse."""
        pool = WorktreePool(pool_dir=tmp_path)

        path = pool.acquire("task-001", "proj1")

        assert pool._is_in_use(path)

        pool.release(path)

        assert not pool._is_in_use(path)

    def test_concurrent_acquire_uses_file_locking(self, tmp_path):
        """Concurrent acquire() should be safe via file locking."""
        import threading

        pool = WorktreePool(pool_dir=tmp_path, max_worktrees=10)
        results = []

        def acquire_worktree(task_id):
            path = pool.acquire(task_id, "proj1")
            results.append(path)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=acquire_worktree, args=(f"task-{i:03d}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 5
        assert len(set(results)) == 5

    def test_worktree_id_format(self, tmp_path):
        """Worktree ID should be formatted as {project_id}-{task_id}."""
        pool = WorktreePool(pool_dir=tmp_path)

        path = pool.acquire("task-001", "my-project")

        assert "my-project-task-001" in str(path)
