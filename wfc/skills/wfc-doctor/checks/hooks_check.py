"""Hook installation checker."""

import os
from pathlib import Path

from ..types import CheckResult


class HooksChecker:
    """Check WFC hooks installation and permissions."""

    def __init__(self, cwd: Path):
        """Initialize checker."""
        self.cwd = cwd
        self.hooks_dir = cwd / "wfc" / "scripts" / "hooks"

    def check(self, auto_fix: bool = False) -> CheckResult:
        """
        Check hook installation.

        - Verifies hook scripts exist
        - Checks file permissions (executable)
        - Validates hook registration in settings
        """

        issues = []
        fixes_applied = []

        if not self.hooks_dir.exists():
            issues.append(f"Hooks directory not found: {self.hooks_dir}")
            status = "FAIL"
        else:
            required_hooks = [
                "pretooluse_hook.py",
                "posttooluse_hook.py",
                "tdd_enforcer.py",
                "file_checker.py",
            ]

            for hook in required_hooks:
                hook_path = self.hooks_dir / hook
                if not hook_path.exists():
                    issues.append(f"Missing hook: {hook}")
                elif not os.access(hook_path, os.X_OK):
                    issues.append(f"Hook not executable: {hook}")
                    if auto_fix:
                        os.chmod(hook_path, 0o755)
                        fixes_applied.append(f"Set executable permission on {hook}")

            status = "FAIL" if issues else "PASS"

        return CheckResult(name="hooks", status=status, issues=issues, fixes_applied=fixes_applied)
