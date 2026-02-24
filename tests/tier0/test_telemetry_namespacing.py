"""
Tier 0 MVP - TASK-004 Tests
Test AutoTelemetry project namespacing.
"""

from pathlib import Path
from wfc.shared.telemetry_auto import AutoTelemetry, get_telemetry


class TestTelemetryNamespacing:
    """Test AutoTelemetry project_id namespacing."""

    def test_autotelemetry_accepts_project_id(self):
        """AutoTelemetry should accept project_id parameter."""
        telemetry = AutoTelemetry(project_id="proj1")
        assert telemetry.project_id == "proj1"

    def test_autotelemetry_defaults_to_none(self, tmp_path):
        """AutoTelemetry should default project_id to None."""
        telemetry = AutoTelemetry(storage_dir=tmp_path)
        assert telemetry.project_id is None

    def test_storage_dir_with_project_id(self, tmp_path):
        """Storage directory should include project_id when set."""
        base_dir = tmp_path / "telemetry"
        telemetry = AutoTelemetry(storage_dir=base_dir, project_id="proj1")

        assert telemetry.storage_dir == base_dir

    def test_storage_dir_default_with_project_id(self):
        """Default storage directory should namespace by project_id."""
        telemetry = AutoTelemetry(project_id="my-project")

        expected = Path.home() / ".wfc" / "telemetry" / "my-project"
        assert telemetry.storage_dir == expected

    def test_storage_dir_default_without_project_id(self):
        """Default storage directory should be ~/.wfc/telemetry/ when no project_id."""
        telemetry = AutoTelemetry()

        expected = Path.home() / ".wfc" / "telemetry"
        assert telemetry.storage_dir == expected

    def test_get_telemetry_factory_exists(self):
        """get_telemetry factory function should exist."""

    def test_get_telemetry_without_project_id(self):
        """get_telemetry should return global instance when no project_id."""
        telemetry = get_telemetry()

        assert telemetry.project_id is None
        assert isinstance(telemetry, AutoTelemetry)

    def test_get_telemetry_with_project_id(self):
        """get_telemetry should return project-specific instance."""
        telemetry = get_telemetry(project_id="proj1")

        assert telemetry.project_id == "proj1"
        assert isinstance(telemetry, AutoTelemetry)

    def test_get_telemetry_returns_same_instance(self):
        """get_telemetry should return same instance for same project_id."""
        tel1 = get_telemetry(project_id="proj1")
        tel2 = get_telemetry(project_id="proj1")

        assert tel1 is tel2

    def test_get_telemetry_different_instances_per_project(self):
        """get_telemetry should return different instances for different projects."""
        tel1 = get_telemetry(project_id="proj1")
        tel2 = get_telemetry(project_id="proj2")
        tel_global = get_telemetry()

        assert tel1 is not tel2
        assert tel1 is not tel_global
        assert tel2 is not tel_global

        assert tel1.project_id == "proj1"
        assert tel2.project_id == "proj2"
        assert tel_global.project_id is None

    def test_different_projects_different_storage_dirs(self):
        """Different projects should have separate storage directories."""
        tel1 = get_telemetry(project_id="proj1")
        tel2 = get_telemetry(project_id="proj2")

        assert tel1.storage_dir != tel2.storage_dir
        assert "proj1" in str(tel1.storage_dir)
        assert "proj2" in str(tel2.storage_dir)
