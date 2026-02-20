"""
Doctor Orchestrator

Coordinates 5 health checks: Agent Skills, Prompt Quality, Settings, Hooks, Pre-commit
CRITICAL: Orchestrator NEVER implements, ONLY coordinates.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .checks.hooks_check import HooksChecker
from .checks.precommit_check import PrecommitChecker
from .checks.prompts_check import PromptsChecker
from .checks.settings_check import SettingsChecker
from .checks.skills_check import SkillsChecker
from .types import CheckResult, HealthCheckResult


class DoctorOrchestrator:
    """
    Orchestrates WFC health checks and auto-fixes.

    Runs 5 checks:
    1. Agent Skills compliance
    2. Prompt quality (delegates to wfc-prompt-fixer)
    3. Settings.json validation
    4. Hook installation
    5. Pre-commit
    """

    def __init__(self, cwd: Optional[Path] = None):
        """Initialize orchestrator."""
        self.cwd = cwd or Path.cwd()
        self.report_dir = self.cwd / ".development"
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.skills_checker = SkillsChecker()
        self.prompts_checker = PromptsChecker(self.cwd)
        self.settings_checker = SettingsChecker()
        self.hooks_checker = HooksChecker(self.cwd)
        self.precommit_checker = PrecommitChecker(self.cwd)

    def run_health_check(self, auto_fix: bool = False) -> HealthCheckResult:
        """
        Run all health checks.

        Args:
            auto_fix: Auto-fix safe issues

        Returns:
            HealthCheckResult with status, checks, report path
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🩺 WFC Health Check - {timestamp}")
        print(f"   Auto-fix: {'enabled' if auto_fix else 'disabled'}\n")

        checks = {}

        print("1️⃣  Checking Agent Skills compliance...")
        checks["skills"] = self.skills_checker.check(auto_fix=auto_fix)
        self._print_check_result(checks["skills"])

        print("\n2️⃣  Checking prompt quality...")
        checks["prompts"] = self.prompts_checker.check(auto_fix=auto_fix)
        self._print_check_result(checks["prompts"])

        print("\n3️⃣  Checking settings.json...")
        checks["settings"] = self.settings_checker.check(auto_fix=auto_fix)
        self._print_check_result(checks["settings"])

        print("\n4️⃣  Checking hook installation...")
        checks["hooks"] = self.hooks_checker.check(auto_fix=auto_fix)
        self._print_check_result(checks["hooks"])

        print("\n5️⃣  Checking pre-commit...")
        checks["precommit"] = self.precommit_checker.check(auto_fix=auto_fix)
        self._print_check_result(checks["precommit"])

        overall_status = self._determine_overall_status(checks)

        report_path = self._generate_report(timestamp, overall_status, checks, auto_fix)

        return HealthCheckResult(
            status=overall_status, checks=checks, report_path=report_path, timestamp=timestamp
        )

    def _print_check_result(self, result: CheckResult) -> None:
        """Print check result to console."""
        status_emoji = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
        print(f"   {status_emoji.get(result.status, '?')} {result.status}")
        if result.issues:
            for issue in result.issues[:3]:
                print(f"      - {issue}")
            if len(result.issues) > 3:
                print(f"      ... and {len(result.issues) - 3} more")

    def _determine_overall_status(self, checks: Dict[str, CheckResult]) -> str:
        """Determine overall status from individual checks."""
        statuses = [check.status for check in checks.values()]

        if "FAIL" in statuses:
            return "FAIL"
        elif "WARN" in statuses:
            return "WARN"
        else:
            return "PASS"

    def _generate_report(
        self, timestamp: str, status: str, checks: Dict[str, CheckResult], auto_fix: bool
    ) -> Path:
        """Generate markdown health report."""
        report_path = self.report_dir / "wfc-doctor-report.md"

        status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}

        lines = [
            "# WFC Health Check Report",
            "",
            f"**Timestamp:** {timestamp}",
            f"**Status:** {status_emoji.get(status, '?')} {status}",
            f"**Auto-fix:** {'enabled' if auto_fix else 'disabled'}",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Check | Status | Issues |",
            "|-------|--------|--------|",
        ]

        for name, result in checks.items():
            emoji = status_emoji.get(result.status, "?")
            lines.append(f"| {name.title()} | {emoji} {result.status} | {len(result.issues)} |")

        lines.extend(["", "---", "", "## Details", ""])

        for name, result in checks.items():
            lines.append(f"### {name.title()}")
            lines.append(f"{status_emoji.get(result.status, '?')} {result.status}")
            lines.append("")

            if result.issues:
                lines.append("**Issues:**")
                for issue in result.issues:
                    lines.append(f"- {issue}")
                lines.append("")

            if result.fixes_applied:
                lines.append("**Fixes Applied:**")
                for fix in result.fixes_applied:
                    lines.append(f"- {fix}")
                lines.append("")

        lines.extend(["---", "", "## Recommendations", ""])

        if status == "PASS":
            lines.append("✅ WFC installation is healthy. No action needed.")
        elif status == "WARN":
            lines.append("⚠️  Minor issues detected. Review details above.")
        else:
            lines.append("❌ Critical issues detected. Fix failures before proceeding.")
            lines.append("")
            lines.append("**Suggested actions:**")
            for name, result in checks.items():
                if result.status == "FAIL":
                    lines.append(f"- Fix {name} issues listed above")

        report_path.write_text("\n".join(lines))
        return report_path
