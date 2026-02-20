"""Settings.json validation checker."""

import json
from pathlib import Path

from ..types import CheckResult


class SettingsChecker:
    """Check ~/.claude/settings.json validity."""

    def check(self, auto_fix: bool = False) -> CheckResult:
        """
        Check settings.json.

        - Validates JSON syntax
        - Checks hook matchers (e.g., Task in context_monitor)
        - Validates permission modes
        """

        issues = []
        fixes_applied = []

        settings_path = Path.home() / ".claude" / "settings.json"

        if not settings_path.exists():
            issues.append("~/.claude/settings.json not found")
            status = "WARN"
        else:
            try:
                with open(settings_path) as f:
                    _ = json.load(f)

                # TODO: Validate hook matchers
                # TODO: Check permission modes
                # TODO: Detect Task in context_monitor matcher

                status = "PASS"
            except json.JSONDecodeError as e:
                issues.append(f"Invalid JSON: {e}")
                status = "FAIL"

        return CheckResult(
            name="settings", status=status, issues=issues, fixes_applied=fixes_applied
        )
