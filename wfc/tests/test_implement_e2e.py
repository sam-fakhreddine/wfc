"""
End-to-end test for wfc-implement

Tests the full pipeline: TASKS.md → agents → review → merge
"""

import tempfile
from pathlib import Path
import sys

# Add wfc to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wfc.skills.plan.mock import generate_mock_plan
from wfc.skills.implement import run_implementation


def test_full_pipeline():
    """Test complete implementation pipeline."""
    print("🧪 Testing wfc-implement end-to-end...")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Generate mock plan
        plan_dir = project_root / "plan"
        generate_mock_plan(plan_dir)
        print(f"✅ Mock plan generated")

        # Initialize git repo (required for worktrees)
        import subprocess
        subprocess.run(["git", "init"], cwd=project_root, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@wfc.com"], cwd=project_root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "WFC Test"], cwd=project_root, capture_output=True)

        # Create initial commit (required for worktrees)
        (project_root / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_root, capture_output=True)
        print(f"✅ Git repo initialized")

        # Run implementation
        try:
            result = run_implementation(
                tasks_file=plan_dir / "TASKS.md",
                project_root=project_root
            )

            print()
            print("📊 Results:")
            print(f"   Tasks completed: {result.tasks_completed}")
            print(f"   Tasks failed: {result.tasks_failed}")
            print(f"   Duration: {result.duration_ms}ms")
            print()

            if result.tasks_completed > 0:
                print("✅ END-TO-END TEST PASSED!")
                return True
            else:
                print("⚠️  No tasks completed")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
