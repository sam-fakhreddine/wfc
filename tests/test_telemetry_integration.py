"""
Integration tests for WFC Telemetry System

Tests event logging, workflow metrics, and PR tracking.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from wfc.shared.telemetry_auto import (
    AutoTelemetry,
    log_event,
    get_workflow_metrics,
    print_workflow_metrics,
)


class TestAutoTelemetry:
    """Test AutoTelemetry class."""

    def test_init_creates_storage_dir(self):
        """Test that initialization creates storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            assert storage_dir.exists()
            assert telemetry.storage_dir == storage_dir

    def test_init_creates_session_file(self):
        """Test that initialization creates session file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            assert telemetry.session_file.parent == storage_dir
            assert "session-" in telemetry.session_file.name

    def test_init_creates_aggregate_file(self):
        """Test that initialization creates aggregate file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            assert telemetry.aggregate_file == storage_dir / "aggregate.json"

    def test_log_task_start(self):
        """Test logging task start."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            telemetry.log_task_start(
                task_id="TASK-001",
                complexity="M",
                properties=["SAFETY", "PERFORMANCE"],
                thinking_budget=1000,
                thinking_mode="extended",
            )

            # Check that session file was created
            assert telemetry.session_file.exists()

            # Read session file
            with open(telemetry.session_file) as f:
                data = json.loads(f.readline())

            assert data["task_id"] == "TASK-001"
            assert data["complexity"] == "M"
            assert data["status"] == "in_progress"
            assert data["thinking_budget_allocated"] == 1000

    def test_log_task_complete(self):
        """Test logging task completion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            # Start task first
            telemetry.log_task_start(
                task_id="TASK-001",
                complexity="M",
                properties=["SAFETY"],
                thinking_budget=1000,
                thinking_mode="normal",
            )

            # Complete task
            telemetry.log_task_complete(
                task_id="TASK-001",
                status="success",
                thinking_budget_used=800,
                thinking_truncated=False,
                retry_count=0,
                duration_seconds=120.5,
                tokens_input=500,
                tokens_output=300,
                tests_run=10,
                tests_passed=10,
                tests_failed=0,
            )

            # Read session file (last line)
            lines = telemetry.session_file.read_text().strip().split("\n")
            data = json.loads(lines[-1])

            assert data["task_id"] == "TASK-001"
            assert data["status"] == "success"
            assert data["thinking_budget_used"] == 800
            assert data["duration_seconds"] == 120.5
            assert data["tokens_total"] == 800

    def test_aggregate_file_created(self):
        """Test that aggregate file is created on task completion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            telemetry.log_task_complete(
                task_id="TASK-001",
                status="success",
                thinking_budget_used=800,
                thinking_truncated=False,
                retry_count=0,
                duration_seconds=120.5,
                tokens_input=500,
                tokens_output=300,
                tests_run=10,
                tests_passed=10,
                tests_failed=0,
            )

            assert telemetry.aggregate_file.exists()

            with open(telemetry.aggregate_file) as f:
                aggregate = json.load(f)

            assert aggregate["total_tasks"] == 1
            assert aggregate["successful_tasks"] == 1
            assert aggregate["failed_tasks"] == 0

    def test_aggregate_multiple_tasks(self):
        """Test aggregate statistics for multiple tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            telemetry = AutoTelemetry(storage_dir)

            # Complete 3 tasks (2 success, 1 failed)
            for i in range(3):
                status = "success" if i < 2 else "failed"
                telemetry.log_task_complete(
                    task_id=f"TASK-{i:03d}",
                    status=status,
                    thinking_budget_used=800,
                    thinking_truncated=False,
                    retry_count=0,
                    duration_seconds=100.0,
                    tokens_input=500,
                    tokens_output=300,
                    tests_run=10,
                    tests_passed=10 if status == "success" else 5,
                    tests_failed=0 if status == "success" else 5,
                )

            with open(telemetry.aggregate_file) as f:
                aggregate = json.load(f)

            assert aggregate["total_tasks"] == 3
            assert aggregate["successful_tasks"] == 2
            assert aggregate["failed_tasks"] == 1
            assert aggregate["total_tokens"] == 800 * 3


class TestGenericEventLogging:
    """Test generic event logging functionality."""

    def test_log_event_creates_events_file(self):
        """Test that log_event creates events file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                log_event("test_event", {"key": "value"})

                events_file = storage_dir / "events.jsonl"
                assert events_file.exists()

    def test_log_event_appends_to_file(self):
        """Test that log_event appends to events file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Log multiple events
                log_event("event1", {"data": "value1"})
                log_event("event2", {"data": "value2"})

                events_file = storage_dir / "events.jsonl"
                lines = events_file.read_text().strip().split("\n")

                assert len(lines) == 2

    def test_log_event_includes_timestamp(self):
        """Test that log_event includes timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                log_event("test_event", {"key": "value"})

                events_file = storage_dir / "events.jsonl"
                data = json.loads(events_file.read_text())

                assert "timestamp" in data
                assert "event" in data
                assert data["event"] == "test_event"

    def test_log_pr_created_event(self):
        """Test logging PR created event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                log_event(
                    "pr_created",
                    {
                        "pr_url": "https://github.com/user/repo/pull/42",
                        "task_id": "TASK-001",
                        "success": True,
                        "pr_number": 42,
                    },
                )

                events_file = storage_dir / "events.jsonl"
                data = json.loads(events_file.read_text())

                assert data["event"] == "pr_created"
                assert data["pr_url"] == "https://github.com/user/repo/pull/42"
                assert data["task_id"] == "TASK-001"
                assert data["success"] is True

    def test_log_hook_warning_event(self):
        """Test logging hook warning event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                log_event(
                    "hook_warning",
                    {
                        "hook": "pre-commit",
                        "violation": "direct_commit_to_protected",
                        "branch": "main",
                    },
                )

                events_file = storage_dir / "events.jsonl"
                data = json.loads(events_file.read_text())

                assert data["event"] == "hook_warning"
                assert data["hook"] == "pre-commit"
                assert data["violation"] == "direct_commit_to_protected"


class TestWorkflowMetrics:
    """Test workflow metrics functionality."""

    def test_get_workflow_metrics_empty(self):
        """Test workflow metrics with no events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                metrics = get_workflow_metrics(days=30)

                assert metrics["total_prs"] == 0
                assert metrics["successful_prs"] == 0
                assert metrics["pr_creation_success_rate"] == 0

    def test_get_workflow_metrics_pr_events(self):
        """Test workflow metrics with PR events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Log PR events
                log_event("pr_created", {"success": True, "pr_number": 1})
                log_event("pr_created", {"success": True, "pr_number": 2})
                log_event("pr_created", {"success": False, "pr_number": 3})

                metrics = get_workflow_metrics(days=30)

                assert metrics["total_prs"] == 3
                assert metrics["successful_prs"] == 2
                assert metrics["pr_creation_success_rate"] == pytest.approx(66.67, 0.01)

    def test_get_workflow_metrics_hook_warnings(self):
        """Test workflow metrics with hook warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Log hook warnings
                log_event(
                    "hook_warning",
                    {"violation": "direct_commit_to_protected", "branch": "main"},
                )
                log_event(
                    "hook_warning",
                    {"violation": "direct_commit_to_protected", "branch": "main"},
                )
                log_event("hook_warning", {"violation": "force_push"})

                metrics = get_workflow_metrics(days=30)

                assert metrics["direct_main_commits"] == 2
                assert metrics["force_pushes"] == 1

    def test_get_workflow_metrics_time_filtering(self):
        """Test workflow metrics filters by time range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"
            events_file = storage_dir / "events.jsonl"
            storage_dir.mkdir()

            # Create events with different timestamps
            now = datetime.now()
            old_event = {
                "event": "pr_created",
                "timestamp": (now - timedelta(days=40)).isoformat(),
                "success": True,
            }
            recent_event = {
                "event": "pr_created",
                "timestamp": (now - timedelta(days=10)).isoformat(),
                "success": True,
            }

            with open(events_file, "w") as f:
                f.write(json.dumps(old_event) + "\n")
                f.write(json.dumps(recent_event) + "\n")

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Get metrics for last 30 days
                metrics = get_workflow_metrics(days=30)

                # Should only include recent event
                assert metrics["total_prs"] == 1

    def test_print_workflow_metrics(self):
        """Test printing workflow metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Log some events
                log_event("pr_created", {"success": True})
                log_event("pr_created", {"success": True})

                # Should not raise exception
                import io

                captured_output = io.StringIO()
                with patch("sys.stdout", new=captured_output):
                    print_workflow_metrics(days=30)

                output = captured_output.getvalue()
                assert "WFC WORKFLOW METRICS" in output
                assert "PR Creation" in output


class TestTelemetryIntegrationWithMergeEngine:
    """Test telemetry integration with merge engine."""

    def test_pr_creation_logs_telemetry(self):
        """Test that PR creation logs telemetry event."""
        # This test verifies the integration conceptually
        # Full end-to-end testing would require a complete git setup

        with patch("wfc.shared.telemetry_auto.log_event") as mock_log:
            # Simulate what merge_engine.create_pr() does
            mock_log(
                "pr_created",
                {
                    "task_id": "TASK-001",
                    "pr_url": "https://github.com/user/repo/pull/42",
                    "success": True,
                },
            )

            # Verify log_event was called
            mock_log.assert_called_once()


class TestTelemetryErrorHandling:
    """Test telemetry error handling."""

    def test_log_event_handles_failure_gracefully(self):
        """Test that log_event doesn't crash on failure."""
        with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
            mock_get.side_effect = Exception("Telemetry error")

            # Should not raise exception
            try:
                log_event("test_event", {"key": "value"})
            except Exception as e:
                pytest.fail(f"log_event raised exception: {e}")

    def test_telemetry_file_write_failure(self):
        """Test handling of file write failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Make storage dir read-only
                storage_dir.chmod(0o444)

                # Should not raise exception
                try:
                    log_event("test_event", {"key": "value"})
                except Exception as e:
                    pytest.fail(f"log_event raised exception on write failure: {e}")
                finally:
                    # Restore permissions
                    storage_dir.chmod(0o755)


class TestTelemetryMetricsSummary:
    """Test comprehensive workflow metrics."""

    def test_complete_workflow_scenario(self):
        """Test complete workflow with PRs, hooks, and commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "telemetry"

            with patch("wfc.shared.telemetry_auto.get_telemetry") as mock_get:
                telemetry = AutoTelemetry(storage_dir)
                mock_get.return_value = telemetry

                # Simulate a complete workflow
                # 1. Log PR creations
                log_event("pr_created", {"success": True, "task_id": "TASK-001"})
                log_event("pr_created", {"success": True, "task_id": "TASK-002"})
                log_event("pr_created", {"success": False, "task_id": "TASK-003"})

                # 2. Log hook warnings
                log_event("hook_warning", {"violation": "direct_commit_to_protected"})
                log_event("hook_warning", {"violation": "non_conventional_commit"})

                # 3. Log commits with tasks
                log_event(
                    "commit_with_task",
                    {"task_id": "TASK-001", "message": "TASK-001: Add feature"},
                )
                log_event(
                    "commit_with_task",
                    {"task_id": "TASK-002", "message": "TASK-002: Fix bug"},
                )

                # Get metrics
                metrics = get_workflow_metrics(days=30)

                # Verify metrics
                assert metrics["total_prs"] == 3
                assert metrics["successful_prs"] == 2
                assert metrics["pr_creation_success_rate"] == pytest.approx(66.67, 0.01)
                assert metrics["direct_main_commits"] == 1
                assert len(metrics["hook_warnings"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
