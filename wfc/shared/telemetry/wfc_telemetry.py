"""
WFC Telemetry System - ELEGANT & SIMPLE

DEPRECATED: Use wfc.shared.telemetry_auto.AutoTelemetry instead.

This module will be removed in a future version. AutoTelemetry is the
canonical telemetry system with richer metrics (extended thinking, quality,
review scores).

Migration: Replace WFCTelemetry.record() with AutoTelemetry.log_task_*() methods.

---

Writes telemetry records to JSONL files in ~/.claude/metrics/YYYY/wfc-*.WNN.jsonl
Week-numbered files for easy aggregation and analysis.

Design principles:
- Single Responsibility: Append-only telemetry writing
- DRY: One writer for all WFC skills
- Simple: JSONL format, atomic writes, no database
"""

import warnings

warnings.warn(
    "wfc.shared.telemetry.wfc_telemetry is deprecated. "
    "Use wfc.shared.telemetry_auto.AutoTelemetry instead.",
    DeprecationWarning,
    stacklevel=2,
)

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import fcntl  # For file locking on Unix


class WFCTelemetry:
    """
    WFC Telemetry writer - appends records to week-numbered JSONL files.

    File format: ~/.claude/metrics/YYYY/wfc-{skill}.WNN.jsonl
    Example: ~/.claude/metrics/2026/wfc-implement.W06.jsonl

    Each line is a JSON record. Append-only for reliability.
    """

    def __init__(self, metrics_dir: Optional[Path] = None):
        """
        Initialize telemetry writer.

        Args:
            metrics_dir: Base metrics directory (default: ~/.claude/metrics)
        """
        if metrics_dir is None:
            metrics_dir = Path.home() / ".claude" / "metrics"
        self.metrics_dir = Path(metrics_dir)

    def record(self, skill: str, data: Dict[str, Any]) -> None:
        """
        Append a telemetry record to the appropriate JSONL file.

        Args:
            skill: Skill name (e.g., "implement", "plan", "review")
            data: Telemetry data dictionary

        The record will automatically include timestamp if not present.
        """
        now = datetime.now()
        year = now.strftime("%Y")
        week_num = self._get_week_number(now)

        # Ensure timestamp is present
        if "timestamp" not in data:
            data["timestamp"] = now.isoformat()

        # Ensure skill is recorded
        if "skill" not in data:
            data["skill"] = f"wfc-{skill}"

        # Build file path: YYYY/wfc-{skill}.WNN.jsonl
        year_dir = self.metrics_dir / year
        year_dir.mkdir(parents=True, exist_ok=True)

        filename = f"wfc-{skill}.W{week_num:02d}.jsonl"
        file_path = year_dir / filename

        # Append record atomically
        self._append_jsonl(file_path, data)

    def _append_jsonl(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Atomically append a JSON record to a JSONL file.

        Uses file locking to prevent corruption from concurrent writes.
        """
        try:
            # Open in append mode, create if doesn't exist
            with open(file_path, "a") as f:
                # Lock file for atomic write (Unix only, gracefully degrades on Windows)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                except (AttributeError, IOError):
                    # Windows or locking not available - proceed without lock
                    pass

                # Write JSON line
                json_line = json.dumps(data, ensure_ascii=False)
                f.write(json_line + "\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure data hits disk

                # Unlock (automatic on close, but explicit is clear)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (AttributeError, IOError):
                    pass

        except IOError as e:
            print(f"Warning: Failed to write telemetry to {file_path}: {e}")

    @staticmethod
    def _get_week_number(dt: datetime) -> int:
        """
        Get ISO week number (1-53).

        Args:
            dt: Datetime object

        Returns:
            Week number (1-53)
        """
        return dt.isocalendar()[1]


class TelemetryRecord:
    """
    Helper class to build telemetry records with common fields.

    Usage:
        >>> record = TelemetryRecord("implement", run_id="abc123")
        >>> record.add("tasks_completed", 5)
        >>> record.add("duration_ms", 120000)
        >>> record.save()
    """

    def __init__(
        self, skill: str, run_id: Optional[str] = None, metrics_dir: Optional[Path] = None
    ):
        """
        Initialize telemetry record builder.

        Args:
            skill: Skill name
            run_id: Optional run identifier
            metrics_dir: Optional metrics directory
        """
        self.skill = skill
        self.telemetry = WFCTelemetry(metrics_dir)
        self.data: Dict[str, Any] = {}

        if run_id:
            self.data["run_id"] = run_id

    def add(self, key: str, value: Any) -> "TelemetryRecord":
        """
        Add a field to the telemetry record.

        Args:
            key: Field name
            value: Field value

        Returns:
            Self for chaining
        """
        self.data[key] = value
        return self

    def save(self) -> None:
        """Save the telemetry record."""
        self.telemetry.record(self.skill, self.data)


# Convenience function
def get_telemetry(metrics_dir: Optional[Path] = None) -> WFCTelemetry:
    """
    Get telemetry writer instance.

    Args:
        metrics_dir: Optional metrics directory

    Returns:
        WFCTelemetry instance
    """
    return WFCTelemetry(metrics_dir)


if __name__ == "__main__":
    # Simple test
    telemetry = get_telemetry()

    # Test record
    test_record = {"run_id": "test-001", "status": "success", "duration_ms": 1500, "test": True}

    telemetry.record("test", test_record)
    print("Test record written to metrics directory")

    # Test builder pattern
    record = TelemetryRecord("test", run_id="test-002")
    record.add("tasks", 5).add("duration_ms", 2000).save()
    print("Test record (builder pattern) written")
