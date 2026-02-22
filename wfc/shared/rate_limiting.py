"""
Per-project rate limiting and resource quotas (Issue #65).

Implements token bucket algorithm per project_id with configurable quotas.
Prevents one project from starving others of review capacity.
"""

import logging
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProjectRateLimiter:
    """
    Per-project rate limiter with resource quotas.

    Each project gets:
    - Reviews per hour quota (token bucket)
    - Concurrent reviews limit (semaphore-like)
    - Independent from other projects (multi-tenant isolation)

    Quotas are configurable per-project or use system defaults.
    """

    def __init__(
        self,
        default_reviews_per_hour: int = 60,
        default_concurrent_reviews: int = 3,
        refill_interval: float = 1.0,
    ):
        """
        Initialize project rate limiter.

        Args:
            default_reviews_per_hour: Default hourly review quota per project
            default_concurrent_reviews: Default concurrent review limit per project
            refill_interval: Token refill interval in seconds
        """
        self.default_reviews_per_hour = default_reviews_per_hour
        self.default_concurrent_reviews = default_concurrent_reviews
        self.refill_interval = refill_interval

        self.quotas: Dict[str, dict] = {}
        self.lock = threading.Lock()

        self._start_refill_thread()

    def create_project_quota(
        self,
        project_id: str,
        reviews_per_hour: Optional[int] = None,
        concurrent_reviews: Optional[int] = None,
    ) -> None:
        """
        Create quota for project.

        Args:
            project_id: Project identifier
            reviews_per_hour: Custom hourly quota (None = use default)
            concurrent_reviews: Custom concurrent limit (None = use default)
        """
        with self.lock:
            if project_id in self.quotas:
                logger.warning(f"Project {project_id} quota already exists, skipping")
                return

            self.quotas[project_id] = {
                "reviews_per_hour": reviews_per_hour or self.default_reviews_per_hour,
                "concurrent_reviews": concurrent_reviews or self.default_concurrent_reviews,
                "tokens": reviews_per_hour or self.default_reviews_per_hour,
                "active_reviews": 0,
                "last_refill": time.time(),
            }

            logger.info(
                f"Created quota for {project_id}: "
                f"{self.quotas[project_id]['reviews_per_hour']}/hour, "
                f"{self.quotas[project_id]['concurrent_reviews']} concurrent"
            )

    def acquire(self, project_id: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens for project (rate limiting).

        Args:
            project_id: Project identifier
            tokens: Number of tokens to acquire
            timeout: Max wait time (None = no wait, 0 = wait forever)

        Returns:
            True if tokens acquired, False if rate limited
        """
        start_time = time.time()

        while True:
            with self.lock:
                if project_id not in self.quotas:
                    self.quotas[project_id] = {
                        "reviews_per_hour": self.default_reviews_per_hour,
                        "concurrent_reviews": self.default_concurrent_reviews,
                        "tokens": self.default_reviews_per_hour,
                        "active_reviews": 0,
                        "last_refill": time.time(),
                    }
                    logger.info(
                        f"Auto-created quota for {project_id}: "
                        f"{self.default_reviews_per_hour}/hour, "
                        f"{self.default_concurrent_reviews} concurrent"
                    )

                quota = self.quotas[project_id]

                if quota["tokens"] >= tokens:
                    quota["tokens"] -= tokens
                    return True

            if timeout is None:
                return False
            elif timeout == 0:
                time.sleep(0.01)
            elif time.time() - start_time >= timeout:
                return False
            else:
                time.sleep(0.01)

    def start_review(self, project_id: str) -> bool:
        """
        Start a review (acquire concurrent slot).

        Args:
            project_id: Project identifier

        Returns:
            True if slot acquired, False if concurrent limit reached
        """
        with self.lock:
            if project_id not in self.quotas:
                self.create_project_quota(project_id)

            quota = self.quotas[project_id]

            if quota["active_reviews"] < quota["concurrent_reviews"]:
                quota["active_reviews"] += 1
                logger.debug(f"Started review for {project_id} ({quota['active_reviews']} active)")
                return True
            else:
                logger.warning(
                    f"Concurrent review limit reached for {project_id} "
                    f"({quota['active_reviews']}/{quota['concurrent_reviews']})"
                )
                return False

    def finish_review(self, project_id: str) -> None:
        """
        Finish a review (release concurrent slot).

        Args:
            project_id: Project identifier
        """
        with self.lock:
            if project_id not in self.quotas:
                logger.warning(f"Attempted to finish review for unknown project {project_id}")
                return

            quota = self.quotas[project_id]

            if quota["active_reviews"] > 0:
                quota["active_reviews"] -= 1
                logger.debug(f"Finished review for {project_id} ({quota['active_reviews']} active)")
            else:
                logger.warning(f"No active reviews to finish for {project_id}")

    def get_quota_status(self, project_id: str) -> dict:
        """
        Get current quota status for project.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary with quota limits and current usage
        """
        with self.lock:
            if project_id not in self.quotas:
                return {}

            quota = self.quotas[project_id]
            return {
                "reviews_per_hour": quota["reviews_per_hour"],
                "concurrent_reviews": quota["concurrent_reviews"],
                "tokens_available": quota["tokens"],
                "active_reviews": quota["active_reviews"],
            }

    def update_project_quota(
        self,
        project_id: str,
        reviews_per_hour: Optional[int] = None,
        concurrent_reviews: Optional[int] = None,
    ) -> None:
        """
        Update quota limits for existing project.

        Args:
            project_id: Project identifier
            reviews_per_hour: New hourly quota (None = no change)
            concurrent_reviews: New concurrent limit (None = no change)
        """
        with self.lock:
            if project_id not in self.quotas:
                logger.warning(f"Cannot update non-existent project {project_id}")
                return

            if reviews_per_hour is not None:
                self.quotas[project_id]["reviews_per_hour"] = reviews_per_hour
                self.quotas[project_id]["tokens"] = min(
                    self.quotas[project_id]["tokens"], reviews_per_hour
                )

            if concurrent_reviews is not None:
                self.quotas[project_id]["concurrent_reviews"] = concurrent_reviews

            logger.info(f"Updated quota for {project_id}")

    def delete_project_quota(self, project_id: str) -> None:
        """
        Delete project quota (cleanup).

        Args:
            project_id: Project identifier
        """
        with self.lock:
            if project_id in self.quotas:
                del self.quotas[project_id]
                logger.info(f"Deleted quota for {project_id}")

    def list_quotas(self) -> Dict[str, dict]:
        """
        List all project quotas.

        Returns:
            Dictionary of project_id -> quota status
        """
        with self.lock:
            return {
                project_id: {
                    "reviews_per_hour": quota["reviews_per_hour"],
                    "concurrent_reviews": quota["concurrent_reviews"],
                    "tokens_available": quota["tokens"],
                    "active_reviews": quota["active_reviews"],
                }
                for project_id, quota in self.quotas.items()
            }

    def _refill_tokens(self) -> None:
        """Refill tokens for all projects based on elapsed time."""
        with self.lock:
            now = time.time()

            for project_id, quota in self.quotas.items():
                elapsed = now - quota["last_refill"]
                tokens_to_add = (elapsed / 3600) * quota["reviews_per_hour"]

                quota["tokens"] = min(quota["tokens"] + tokens_to_add, quota["reviews_per_hour"])
                quota["last_refill"] = now

    def _start_refill_thread(self) -> None:
        """Start background thread to refill tokens."""

        def refill_loop():
            while True:
                time.sleep(self.refill_interval)
                self._refill_tokens()

        thread = threading.Thread(target=refill_loop, daemon=True)
        thread.start()
        logger.info("Started token refill thread")
