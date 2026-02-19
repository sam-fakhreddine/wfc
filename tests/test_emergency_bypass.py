"""Tests for the emergency bypass mechanism (TASK-010)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from wfc.scripts.orchestrators.review.consensus_score import ConsensusScoreResult
from wfc.scripts.orchestrators.review.emergency_bypass import BypassRecord, EmergencyBypass


def _make_cs_result(cs: float = 5.0, tier: str = "Moderate") -> ConsensusScoreResult:
    """Helper to build a minimal ConsensusScoreResult."""
    return ConsensusScoreResult(
        cs=cs,
        tier=tier,
        findings=[],
        R_bar=cs,
        R_max=cs,
        k_total=3,
        n=5,
        passed=False,
        minority_protection_applied=False,
        summary="test",
    )


class TestCreateBypass:
    def test_create_bypass_basic(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        cs_result = _make_cs_result(cs=5.5, tier="Moderate")
        record = eb.create_bypass(
            task_id="TASK-001",
            reason="Hotfix needed for production outage",
            bypassed_by="alice",
            cs_result=cs_result,
        )
        assert record.task_id == "TASK-001"
        assert record.reason == "Hotfix needed for production outage"
        assert record.bypassed_by == "alice"
        assert record.cs_at_bypass == 5.5
        assert record.tier_at_bypass == "Moderate"
        assert isinstance(record.created_at, datetime)
        assert isinstance(record.expires_at, datetime)
        assert record.bypass_id

    def test_create_bypass_empty_reason_raises(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        cs_result = _make_cs_result()
        with pytest.raises(ValueError):
            eb.create_bypass(
                task_id="TASK-001",
                reason="",
                bypassed_by="alice",
                cs_result=cs_result,
            )
        with pytest.raises(ValueError):
            eb.create_bypass(
                task_id="TASK-001",
                reason="   ",
                bypassed_by="alice",
                cs_result=cs_result,
            )

    def test_bypass_id_is_uuid(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        record = eb.create_bypass(
            task_id="TASK-002",
            reason="urgent fix",
            bypassed_by="bob",
            cs_result=_make_cs_result(),
        )
        parsed = uuid.UUID(record.bypass_id)
        assert parsed.version == 4

    def test_bypass_expiry_24h(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        record = eb.create_bypass(
            task_id="TASK-003",
            reason="deploy blocker",
            bypassed_by="carol",
            cs_result=_make_cs_result(),
        )
        expected_expiry = record.created_at + timedelta(hours=24)
        assert record.expires_at == expected_expiry


class TestIsExpired:
    def test_is_expired_fresh(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        record = eb.create_bypass(
            task_id="TASK-004",
            reason="fresh bypass",
            bypassed_by="dave",
            cs_result=_make_cs_result(),
        )
        assert record.is_expired is False

    def test_is_expired_after_24h(self, tmp_path: Path) -> None:
        record = BypassRecord(
            bypass_id=str(uuid.uuid4()),
            task_id="TASK-005",
            reason="old bypass",
            bypassed_by="eve",
            created_at=datetime.now(UTC) - timedelta(hours=25),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            cs_at_bypass=6.0,
            tier_at_bypass="Moderate",
        )
        assert record.is_expired is True


class TestAuditTrail:
    def test_audit_trail_persists(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        eb.create_bypass(
            task_id="TASK-006",
            reason="persistence test",
            bypassed_by="frank",
            cs_result=_make_cs_result(),
        )
        eb2 = EmergencyBypass(audit_dir=tmp_path)
        trail = eb2.load_audit_trail()
        assert len(trail) == 1
        assert trail[0].task_id == "TASK-006"
        assert trail[0].reason == "persistence test"

    def test_audit_trail_append_only(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        eb.create_bypass(
            task_id="TASK-007a",
            reason="first bypass",
            bypassed_by="grace",
            cs_result=_make_cs_result(),
        )
        eb.create_bypass(
            task_id="TASK-007b",
            reason="second bypass",
            bypassed_by="heidi",
            cs_result=_make_cs_result(),
        )
        trail = eb.load_audit_trail()
        assert len(trail) == 2
        assert trail[0].task_id == "TASK-007a"
        assert trail[1].task_id == "TASK-007b"

    def test_load_empty_audit(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        trail = eb.load_audit_trail()
        assert trail == []


class TestIsBypassed:
    def test_is_bypassed_active(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        eb.create_bypass(
            task_id="TASK-008",
            reason="active bypass",
            bypassed_by="ivan",
            cs_result=_make_cs_result(),
        )
        assert eb.is_bypassed("TASK-008") is True

    def test_is_bypassed_expired(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        expired = {
            "bypass_id": str(uuid.uuid4()),
            "task_id": "TASK-009",
            "reason": "expired bypass",
            "bypassed_by": "judy",
            "created_at": (datetime.now(UTC) - timedelta(hours=25)).isoformat(),
            "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "cs_at_bypass": 5.0,
            "tier_at_bypass": "Moderate",
        }
        audit_file = tmp_path / EmergencyBypass.AUDIT_FILE
        audit_file.write_text(json.dumps([expired]))
        assert eb.is_bypassed("TASK-009") is False

    def test_is_bypassed_no_bypass(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        assert eb.is_bypassed("TASK-NONEXISTENT") is False


class TestGetActiveBypasses:
    def test_get_active_bypasses(self, tmp_path: Path) -> None:
        eb = EmergencyBypass(audit_dir=tmp_path)
        eb.create_bypass(
            task_id="TASK-ACTIVE",
            reason="still active",
            bypassed_by="kim",
            cs_result=_make_cs_result(),
        )
        trail = eb.load_audit_trail()
        expired = {
            "bypass_id": str(uuid.uuid4()),
            "task_id": "TASK-EXPIRED",
            "reason": "expired",
            "bypassed_by": "leo",
            "created_at": (datetime.now(UTC) - timedelta(hours=25)).isoformat(),
            "expires_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "cs_at_bypass": 4.0,
            "tier_at_bypass": "Informational",
        }
        audit_file = tmp_path / EmergencyBypass.AUDIT_FILE
        raw = json.loads(audit_file.read_text())
        raw.append(expired)
        audit_file.write_text(json.dumps(raw))

        active = eb.get_active_bypasses()
        assert len(active) == 1
        assert active[0].task_id == "TASK-ACTIVE"
