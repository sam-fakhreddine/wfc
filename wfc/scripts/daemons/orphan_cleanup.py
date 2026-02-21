"""
Background daemon for orphan worktree cleanup.

Ensures PROP-L001: "All worktrees older than 24h with no active process
MUST EVENTUALLY be deleted."
"""

import asyncio
import logging
from pathlib import Path

from wfc.shared.resource_pool import WorktreePool

logger = logging.getLogger(__name__)


class OrphanCleanupDaemon:
    """
    Background daemon that periodically cleans up orphaned worktrees.

    Runs every cleanup_interval_hours to ensure PROP-L001 is satisfied.
    """

    def __init__(
        self,
        pool_dir: Path,
        cleanup_interval_hours: int = 6,
        orphan_timeout_hours: int = 24,
    ):
        """
        Initialize orphan cleanup daemon.

        Args:
            pool_dir: Worktree pool directory
            cleanup_interval_hours: Hours between cleanup runs
            orphan_timeout_hours: Hours before worktree considered orphan
        """
        self.pool_dir = Path(pool_dir)
        self.cleanup_interval = cleanup_interval_hours * 3600
        self.orphan_timeout = orphan_timeout_hours
        self.running = False

    async def start(self) -> None:
        """Start the cleanup daemon."""
        self.running = True
        logger.info(
            f"Starting orphan cleanup daemon "
            f"(interval: {self.cleanup_interval / 3600}h, "
            f"timeout: {self.orphan_timeout}h)"
        )

        while self.running:
            try:
                pool = WorktreePool(
                    pool_dir=self.pool_dir,
                    orphan_timeout_hours=self.orphan_timeout,
                )
                removed = pool._cleanup_orphans()

                if removed > 0:
                    logger.info(f"Cleaned up {removed} orphaned worktrees")

            except Exception as e:
                logger.error(f"Orphan cleanup failed: {e}", exc_info=True)

            await asyncio.sleep(self.cleanup_interval)

    def stop(self) -> None:
        """Stop the cleanup daemon."""
        self.running = False
        logger.info("Stopping orphan cleanup daemon")


async def main():
    """CLI entry point for running orphan cleanup daemon."""
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

    try:
        await daemon.start()
    except KeyboardInterrupt:
        daemon.stop()
        logger.info("Daemon stopped by user")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
