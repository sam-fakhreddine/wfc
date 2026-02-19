"""Emergency bypass mechanism with immutable audit trail.

Allows developers to override a failing review with a mandatory reason,
24-hour expiry, and append-only audit logging.
"""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from wfc.scripts.orchestrators.review.consensus_score import ConsensusScoreResult

logger = logging.getLogger(__name__)


@dataclass
class BypassRecord:
    """Immutable record of an emergency bypass."""

    bypass_id: str
    task_id: str
    reason: str
    bypassed_by: str
    created_at: datetime
    expires_at: datetime
    cs_at_bypass: float
    tier_at_bypass: str

    @property
    def is_expired(self) -> bool:
        """Check whether this bypass has expired."""
        return datetime.now(UTC) >= self.expires_at


class EmergencyBypass:
    """Emergency bypass mechanism with audit trail."""

    BYPASS_EXPIRY_HOURS: int = 24
    AUDIT_FILE: str = "BYPASS-AUDIT.json"

    def __init__(self, audit_dir: Path) -> None:
        """Initialize with directory for audit trail storage."""
        self._audit_dir = audit_dir
        self._audit_path = audit_dir / self.AUDIT_FILE

    def create_bypass(
        self,
        task_id: str,
        reason: str,
        bypassed_by: str,
        cs_result: ConsensusScoreResult,
    ) -> BypassRecord:
        """Create a bypass record and append to audit trail.

        Raises:
            ValueError: If reason is empty/whitespace.
        """
        if not reason or not reason.strip():
            msg = "Bypass reason must be non-empty."
            raise ValueError(msg)

        now = datetime.now(UTC)
        record = BypassRecord(
            bypass_id=str(uuid.uuid4()),
            task_id=task_id,
            reason=reason,
            bypassed_by=bypassed_by,
            created_at=now,
            expires_at=now + timedelta(hours=self.BYPASS_EXPIRY_HOURS),
            cs_at_bypass=cs_result.cs,
            tier_at_bypass=cs_result.tier,
        )

        trail = self._load_raw()
        trail.append(self._record_to_dict(record))
        self._audit_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self._audit_dir, suffix=".tmp")
        try:
            with open(fd, "w") as f:
                json.dump(trail, f, indent=2)
            Path(tmp).replace(self._audit_path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

        return record

    def load_audit_trail(self) -> list[BypassRecord]:
        """Load all bypass records from the audit file."""
        return [r for r in (self._dict_to_record(d) for d in self._load_raw()) if r is not None]

    def is_bypassed(self, task_id: str) -> bool:
        """Check if a task has an active (non-expired) bypass."""
        for record in self.load_audit_trail():
            if record.task_id == task_id and not record.is_expired:
                return True
        return False

    def get_active_bypasses(self) -> list[BypassRecord]:
        """Return all non-expired bypasses."""
        return [r for r in self.load_audit_trail() if not r.is_expired]

    def _load_raw(self) -> list[dict]:
        """Load the raw JSON array from the audit file."""
        if not self._audit_path.exists():
            return []
        text = self._audit_path.read_text().strip()
        if not text:
            return []
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            corrupt_path = self._audit_path.with_suffix(".corrupt")
            logger.critical(
                "Audit file is corrupt; renaming to %s for recovery. Path: %s",
                corrupt_path,
                self._audit_path,
            )
            self._audit_path.rename(corrupt_path)
            return []

    @staticmethod
    def _record_to_dict(record: BypassRecord) -> dict:
        d = asdict(record)
        d["created_at"] = record.created_at.isoformat()
        d["expires_at"] = record.expires_at.isoformat()
        return d

    @staticmethod
    def _dict_to_record(d: dict) -> BypassRecord | None:
        try:
            return BypassRecord(
                bypass_id=d["bypass_id"],
                task_id=d["task_id"],
                reason=d["reason"],
                bypassed_by=d["bypassed_by"],
                created_at=datetime.fromisoformat(d["created_at"]),
                expires_at=datetime.fromisoformat(d["expires_at"]),
                cs_at_bypass=d["cs_at_bypass"],
                tier_at_bypass=d["tier_at_bypass"],
            )
        except (KeyError, ValueError, TypeError):
            logger.warning("Skipping malformed bypass record: %r", d)
            return None
