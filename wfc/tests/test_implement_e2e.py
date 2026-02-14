"""
End-to-end test for wfc-implement

Tests the full pipeline: TASKS.md → agents → review → merge
"""

import tempfile
from pathlib import Path
import subprocess
import sys

import pytest

# Add wfc to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wfc.skills.plan.mock import generate_mock_plan
from wfc.skills.implement import run_implementation


def test_full_pipeline():
    """Test complete implementation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Generate mock plan
        plan_dir = project_root / "plan"
        generate_mock_plan(plan_dir)

        # Initialize git repo (required for worktrees)
        subprocess.run(["git", "init"], cwd=project_root, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@wfc.com"], cwd=project_root, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "WFC Test"], cwd=project_root, capture_output=True
        )

        # Create initial commit (required for worktrees)
        (project_root / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=project_root, capture_output=True
        )

        # Run implementation
        result = run_implementation(tasks_file=plan_dir / "TASKS.md", project_root=project_root)

        assert result.tasks_completed > 0, (
            f"Expected at least one completed task, got {result.tasks_completed} completed "
            f"and {result.tasks_failed} failed"
        )
