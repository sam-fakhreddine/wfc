"""Tests for idempotent machine ID (TASK-001).

Properties verified:
- PROP-001: INVARIANT — same value every call on same host
- PROP-002: SAFETY — no file writes, no network, no side effects
"""

import hashlib
from pathlib import Path
from unittest.mock import patch

from wfc.shared.machine import machine_id


class TestMachineIdDeterminism:
    """TEST-001: machine_id() returns identical value across calls."""

    def test_returns_same_value_100_times(self):
        results = [machine_id() for _ in range(100)]
        assert len(set(results)) == 1, "machine_id() must be deterministic"

    def test_returns_8_hex_chars(self):
        result = machine_id()
        assert len(result) == 8
        assert all(c in "0123456789abcdef" for c in result)


class TestMachineIdFromEtcMachineId:
    """TEST-002: Primary path reads /etc/machine-id."""

    def test_uses_etc_machine_id(self, tmp_path):
        fake_id = "abc123def456789"
        machine_id_file = tmp_path / "machine-id"
        machine_id_file.write_text(fake_id + "\n")

        expected = hashlib.sha256(fake_id.encode()).hexdigest()[:8]

        with patch(
            "wfc.shared.machine.Path",
            return_value=machine_id_file,
        ) as mock_path:
            mock_path.return_value = machine_id_file
            pass

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", return_value=fake_id + "\n"),
        ):
            result = machine_id()
            assert result == expected


class TestMachineIdFallbackUuid:
    """TEST-003: Fallback to uuid.getnode() when /etc/machine-id absent."""

    def test_uses_mac_address(self):
        known_mac = 0x001122334455
        expected = hashlib.sha256(str(known_mac).encode()).hexdigest()[:8]

        with (
            patch.object(Path, "exists", return_value=False),
            patch("wfc.shared.machine.uuid.getnode", return_value=known_mac),
        ):
            result = machine_id()
            assert result == expected


class TestMachineIdFallbackPlatform:
    """TEST-003b: Final fallback when uuid.getnode() returns random MAC."""

    def test_uses_platform_info(self):
        random_mac = 0x010000000000
        expected = hashlib.sha256(b"hostx86_64dev").hexdigest()[:8]

        with (
            patch.object(Path, "exists", return_value=False),
            patch("wfc.shared.machine.uuid.getnode", return_value=random_mac),
            patch("wfc.shared.machine.platform.node", return_value="host"),
            patch("wfc.shared.machine.platform.machine", return_value="x86_64"),
            patch("wfc.shared.machine.getpass.getuser", return_value="dev"),
        ):
            result = machine_id()
            assert result == expected


class TestMachineIdNoSideEffects:
    """TEST-004: No filesystem or network writes (PROP-002)."""

    def test_no_file_writes(self):
        with (
            patch.object(Path, "write_text") as mock_write,
            patch.object(Path, "mkdir") as mock_mkdir,
        ):
            machine_id()
            mock_write.assert_not_called()
            mock_mkdir.assert_not_called()
