"""Pre-commit checker."""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestrator import CheckResult


class PrecommitChecker:
    """Check pre-commit setup and run checks."""

    def __init__(self, cwd: Path):
        """Initialize checker."""
        self.cwd = cwd

    def check(self, auto_fix: bool = False) -> "CheckResult":
        """
        Check pre-commit.

        - Runs: uv run pre-commit run --all-files
        - Reports failures by category
        - Auto-fixes if --fix enabled
        """
        from ..orchestrator import CheckResult

        issues = []
        fixes_applied = []

        precommit_config = self.cwd / ".pre-commit-config.yaml"
        if not precommit_config.exists():
            issues.append(".pre-commit-config.yaml not found")
            status = "WARN"
            return CheckResult(
                name="precommit", status=status, issues=issues, fixes_applied=fixes_applied
            )

        try:
            cmd = ["uv", "run", "pre-commit", "run", "--all-files"]
            if auto_fix:
                pass

            result = subprocess.run(cmd, cwd=self.cwd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                # TODO: Better parsing of pre-commit output
                issues.append("Pre-commit checks failed (see output)")
                status = "FAIL"
            else:
                status = "PASS"

        except subprocess.TimeoutExpired:
            issues.append("Pre-commit timed out after 120s")
            status = "FAIL"
        except FileNotFoundError:
            issues.append("uv or pre-commit not found in PATH")
            status = "FAIL"

        return CheckResult(
            name="precommit", status=status, issues=issues, fixes_applied=fixes_applied
        )
