"""
Authentication audit logging for WFC REST API (Issue #63).

Logs all authentication attempts with timestamp, project_id, IP, and outcome.
Implements failed auth rate limiting and suspicious pattern detection.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from filelock import FileLock

logger = logging.getLogger(__name__)


class AuthAuditor:
    """
    Authentication audit logger with rate limiting and alerting.

    Audit log format (JSONL):
    {
        "timestamp": "2026-02-21T10:30:00Z",
        "event_type": "auth.attempt",
        "outcome": "success" | "failure",
        "project_id": "project-123",
        "ip_address": "192.168.1.1",
        "user_agent": "WFC-Client/1.0",
        "failure_reason": "invalid_key" | "project_not_found" | null
    }
    """

    MAX_FAILURES_PER_HOUR = 10
    ALERT_THRESHOLD = 5

    def __init__(self, audit_log_path: Optional[Path] = None):
        """Initialize audit logger."""
        self.audit_log_path = audit_log_path or (Path.home() / ".wfc" / "audit" / "auth.jsonl")
        self.lock_path = self.audit_log_path.with_suffix(".lock")

        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        self._recent_failures: Dict[str, list[datetime]] = {}

    def log_auth_attempt(
        self,
        project_id: str,
        outcome: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        """
        Log authentication attempt.

        Args:
            project_id: Project identifier
            outcome: "success" or "failure"
            ip_address: Client IP address
            user_agent: Client user agent string
            failure_reason: Reason for failure (if applicable)
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "auth.attempt",
            "outcome": outcome,
            "project_id": project_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "failure_reason": failure_reason,
        }

        with FileLock(self.lock_path, timeout=5):
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(event) + "\n")

        if outcome == "failure":
            self._track_failure(project_id, ip_address)

        if outcome == "success":
            logger.info(f"Auth success: project={project_id} ip={ip_address} ua={user_agent}")
        else:
            logger.warning(
                f"Auth failure: project={project_id} ip={ip_address} "
                f"reason={failure_reason} ua={user_agent}"
            )

    def _track_failure(self, project_id: str, ip_address: str) -> None:
        """Track failed authentication for rate limiting."""
        key = hashlib.sha256(f"{project_id}:{ip_address}".encode()).hexdigest()
        now = datetime.now(timezone.utc)

        if key not in self._recent_failures:
            self._recent_failures[key] = []

        self._recent_failures[key].append(now)

        one_hour_ago = now - timedelta(hours=1)
        self._recent_failures[key] = [ts for ts in self._recent_failures[key] if ts > one_hour_ago]

        one_minute_ago = now - timedelta(minutes=1)
        recent_failures = [ts for ts in self._recent_failures[key] if ts > one_minute_ago]

        if len(recent_failures) >= self.ALERT_THRESHOLD:
            logger.error(
                f"SECURITY ALERT: {len(recent_failures)} failed auth attempts "
                f"in 1 minute for project={project_id} ip={ip_address}"
            )

    def is_rate_limited(self, project_id: str, ip_address: str) -> bool:
        """
        Check if project+IP is rate limited due to too many failures.

        Args:
            project_id: Project identifier
            ip_address: Client IP address

        Returns:
            True if rate limited (should block), False otherwise
        """
        key = hashlib.sha256(f"{project_id}:{ip_address}".encode()).hexdigest()

        if key not in self._recent_failures:
            return False

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_failures = [ts for ts in self._recent_failures[key] if ts > one_hour_ago]

        if len(recent_failures) >= self.MAX_FAILURES_PER_HOUR:
            logger.warning(
                f"Rate limit triggered: {len(recent_failures)} failures in 1 hour "
                f"for project={project_id} ip={ip_address}"
            )
            return True

        return False

    def get_failure_count(self, project_id: str, ip_address: str) -> int:
        """Get number of recent failures for project+IP."""
        key = hashlib.sha256(f"{project_id}:{ip_address}".encode()).hexdigest()

        if key not in self._recent_failures:
            return 0

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        return len([ts for ts in self._recent_failures[key] if ts > one_hour_ago])
