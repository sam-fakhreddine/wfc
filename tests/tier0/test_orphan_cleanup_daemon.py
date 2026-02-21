"""
Phase 1 - TASK-012 Tests
Test OrphanCleanupDaemon for background orphan cleanup.
"""

import pytest
import asyncio
from wfc.scripts.daemons.orphan_cleanup import OrphanCleanupDaemon
from wfc.shared.resource_pool import WorktreePool


class TestOrphanCleanupDaemon:
    """Test OrphanCleanupDaemon background cleanup."""

    def test_daemon_initialization(self, tmp_path):
        """Daemon should initialize with pool directory and intervals."""
        daemon = OrphanCleanupDaemon(
            pool_dir=tmp_path, cleanup_interval_hours=6, orphan_timeout_hours=24
        )

        assert daemon.pool_dir == tmp_path
        assert daemon.cleanup_interval == 6 * 3600
        assert daemon.orphan_timeout == 24
        assert daemon.running is False

    @pytest.mark.asyncio
    async def test_daemon_runs_periodic_cleanup(self, tmp_path):
        """Daemon should run cleanup periodically."""
        pool = WorktreePool(pool_dir=tmp_path, orphan_timeout_hours=0.0001)
        path = pool.acquire("task-001", "proj1")
        pool.release(path)

        daemon = OrphanCleanupDaemon(
            pool_dir=tmp_path,
            cleanup_interval_hours=0.0001,
            orphan_timeout_hours=0.0001,
        )

        task = asyncio.create_task(daemon.start())

        await asyncio.sleep(0.5)

        daemon.stop()
        await asyncio.sleep(0.1)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert not path.exists()

    @pytest.mark.asyncio
    async def test_daemon_stop_gracefully(self, tmp_path):
        """Daemon should stop gracefully when stop() called."""
        daemon = OrphanCleanupDaemon(pool_dir=tmp_path, cleanup_interval_hours=1)

        task = asyncio.create_task(daemon.start())

        await asyncio.sleep(0.1)

        daemon.stop()

        assert daemon.running is False

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_daemon_handles_cleanup_errors_gracefully(self, tmp_path):
        """Daemon should continue running even if cleanup fails."""
        daemon = OrphanCleanupDaemon(
            pool_dir=tmp_path / "nonexistent",
            cleanup_interval_hours=0.0001,
            orphan_timeout_hours=24,
        )

        task = asyncio.create_task(daemon.start())

        await asyncio.sleep(0.5)

        assert daemon.running is True

        daemon.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def test_daemon_default_intervals(self, tmp_path):
        """Daemon should have sensible default intervals."""
        daemon = OrphanCleanupDaemon(pool_dir=tmp_path)

        assert daemon.cleanup_interval == 6 * 3600

        assert daemon.orphan_timeout == 24
