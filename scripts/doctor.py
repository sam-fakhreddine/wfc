#!/usr/bin/env python3
"""
WFC Doctor - Comprehensive Health Check

Runs diagnostics to ensure WFC is properly installed and configured.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


class HealthCheck:
    """Individual health check."""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.message = ""
        self.severity = "error"

    def pass_check(self, message: str = ""):
        """Mark check as passed."""
        self.passed = True
        self.message = message
        self.severity = "info"

    def fail_check(self, message: str, severity: str = "error"):
        """Mark check as failed."""
        self.passed = False
        self.message = message
        self.severity = severity


class WFCDoctor:
    """WFC health check runner."""

    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.project_root = Path(__file__).parent.parent

    def add_check(self, name: str, category: str) -> HealthCheck:
        """Add a new health check."""
        check = HealthCheck(name, category)
        self.checks.append(check)
        return check

    def run_all_checks(self) -> bool:
        """Run all health checks and return True if all critical checks pass."""
        print("🩺 WFC Doctor - Comprehensive Health Check")
        print("=" * 60)
        print()

        self._check_python_version()
        self._check_wfc_installation()
        self._check_project_structure()

        self._check_optional_dependencies()
        self._check_dev_dependencies()
        self._check_external_tools()

        self._check_skills_installation()

        self._check_configuration_files()

        self._check_token_manager()

        self._print_results()

        critical_failures = [c for c in self.checks if not c.passed and c.severity == "error"]

        return len(critical_failures) == 0

    def _check_python_version(self):
        """Check Python version meets requirements."""
        check = self.add_check("Python version", "Core")

        version = sys.version_info

        if version >= (3, 12):
            check.pass_check(f"Python {version.major}.{version.minor}.{version.micro}")
        else:
            check.fail_check(
                f"Python {version.major}.{version.minor}.{version.micro} < 3.12 (required)"
            )

    def _check_wfc_installation(self):
        """Check if WFC is installed."""
        check = self.add_check("WFC installation", "Core")

        wfc_cmd = shutil.which("wfc")

        if wfc_cmd:
            try:
                result = subprocess.run(
                    ["wfc", "--version"], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    version = result.stdout.strip()
                    check.pass_check(f"wfc command available ({version})")
                else:
                    check.pass_check(f"wfc command at {wfc_cmd}")
            except Exception:
                check.pass_check(f"wfc command at {wfc_cmd}")
        else:
            check.fail_check("wfc command not found - run: pip install -e .")

    def _check_project_structure(self):
        """Check project structure is intact."""
        check = self.add_check("Project structure", "Core")

        required_dirs = [
            "wfc",
            "wfc/skills",
            "wfc/scripts",
            "wfc/shared",
        ]

        missing = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing.append(dir_path)

        if not missing:
            check.pass_check(f"All {len(required_dirs)} core directories present")
        else:
            check.fail_check(f"Missing directories: {', '.join(missing)}")

    def _check_optional_dependencies(self):
        """Check optional dependencies."""
        check_tiktoken = self.add_check("tiktoken (tokens)", "Optional")

        try:
            import tiktoken

            check_tiktoken.pass_check(f"tiktoken {tiktoken.__version__}")
        except ImportError:
            check_tiktoken.fail_check(
                "Install with: pip install -e '.[tokens]'", severity="warning"
            )

    def _check_dev_dependencies(self):
        """Check development dependencies."""
        dev_deps = [
            ("pytest", "pytest"),
            ("black", "black"),
            ("ruff", "ruff"),
        ]

        for import_name, package_name in dev_deps:
            check = self.add_check(f"{package_name}", "Development")

            try:
                module = __import__(import_name)
                version = getattr(module, "__version__", "installed")
                check.pass_check(f"{version}")
            except ImportError:
                check.fail_check("Install with: pip install -e '.[dev]'", severity="warning")

    def _check_external_tools(self):
        """Check external tools."""
        check_trunk = self.add_check("trunk.io (quality)", "External")

        if shutil.which("trunk"):
            try:
                result = subprocess.run(
                    ["trunk", "version"], capture_output=True, text=True, timeout=5
                )
                version = result.stdout.strip() if result.returncode == 0 else "installed"
                check_trunk.pass_check(version)
            except Exception:
                check_trunk.pass_check("installed")
        else:
            check_trunk.fail_check(
                "Install: curl https://get.trunk.io -fsSL | bash", severity="warning"
            )

        check_skills_ref = self.add_check("skills-ref (validation)", "External")

        skills_ref_path = Path.home() / "repos/agentskills/skills-ref"

        if skills_ref_path.exists():
            venv_path = skills_ref_path / ".venv"
            if venv_path.exists():
                check_skills_ref.pass_check(f"Available at {skills_ref_path}")
            else:
                check_skills_ref.fail_check(
                    f"Found but venv missing - run: cd {skills_ref_path} && uv venv && uv pip install -e .",
                    severity="warning",
                )
        else:
            check_skills_ref.fail_check(
                "Clone to: ~/repos/agentskills/skills-ref", severity="warning"
            )

    def _check_skills_installation(self):
        """Check WFC skills are installed."""
        check = self.add_check("WFC skills", "Skills")

        claude_skills_dir = Path.home() / ".claude/skills"

        if not claude_skills_dir.exists():
            check.fail_check("~/.claude/skills directory not found", severity="error")
            return

        expected_skills = [
            "wfc-implement",
            "wfc-review",
            "wfc-plan",
            "wfc-test",
            "wfc-security",
            "wfc-architecture",
            "wfc-observe",
            "wfc-retro",
            "wfc-safeclaude",
            "wfc-validate",
            "wfc-newskill",
        ]

        installed = []
        missing = []

        for skill_name in expected_skills:
            skill_path = claude_skills_dir / skill_name
            if skill_path.exists():
                installed.append(skill_name)
            else:
                missing.append(skill_name)

        if not missing:
            check.pass_check(f"All {len(expected_skills)} WFC skills installed")
        else:
            check.fail_check(
                f"{len(installed)}/{len(expected_skills)} installed - Missing: {', '.join(missing)}",
                severity="warning",
            )

    def _check_configuration_files(self):
        """Check configuration files exist."""
        check_config = self.add_check("wfc.config.json", "Configuration")

        config_locations = [
            self.project_root / "wfc.config.json",
            Path.home() / ".wfc/wfc.config.json",
        ]

        found = False
        for config_path in config_locations:
            if config_path.exists():
                found = True
                check_config.pass_check(f"Found at {config_path}")
                break

        if not found:
            check_config.fail_check("No config found - will use defaults", severity="info")

        check_index = self.add_check("PROJECT_INDEX.json", "Configuration")

        index_path = self.project_root / "PROJECT_INDEX.json"

        if index_path.exists():
            check_index.pass_check("Project index available")
        else:
            check_index.fail_check("Not found - run: wfc implement (TASK-010)", severity="warning")

    def _check_token_manager(self):
        """Check token manager is functional."""
        check = self.add_check("Token management", "Performance")

        try:
            sys.path.insert(0, str(self.project_root))
            from wfc.scripts.token_manager import TaskComplexity, TokenManager

            manager = TokenManager()
            budget = manager.create_budget("TEST", TaskComplexity.M, use_history=False)

            if budget.budget_total == 1000:
                check.pass_check("Functional (default budgets working)")
            else:
                check.fail_check("Budget calculation incorrect", severity="warning")
        except Exception as e:
            check.fail_check(f"Error: {str(e)}", severity="warning")

    def _print_results(self):
        """Print health check results."""
        print()
        print("=" * 60)
        print("HEALTH CHECK RESULTS")
        print("=" * 60)
        print()

        categories = {}
        for check in self.checks:
            if check.category not in categories:
                categories[check.category] = []
            categories[check.category].append(check)

        for category, checks in categories.items():
            print(f"{category}:")
            for check in checks:
                status_icon = "✅" if check.passed else "❌"
                if check.severity == "warning":
                    status_icon = "⚠️ "
                elif check.severity == "info":
                    status_icon = "ℹ️ "

                print(f"  {status_icon} {check.name}: {check.message}")
            print()

        total = len(self.checks)
        passed = len([c for c in self.checks if c.passed])
        errors = len([c for c in self.checks if not c.passed and c.severity == "error"])
        warnings = len([c for c in self.checks if not c.passed and c.severity == "warning"])

        print("=" * 60)
        print(f"Summary: {passed}/{total} checks passed")

        if errors > 0:
            print(f"  ❌ {errors} critical errors")
        if warnings > 0:
            print(f"  ⚠️  {warnings} warnings")

        print("=" * 60)
        print()

        if errors == 0 and warnings == 0:
            print("🎉 WFC is healthy! ✅")
            print()
            print("This is World Fucking Class. 🚀")
        elif errors == 0:
            print("⚠️  WFC is functional but has warnings")
            print("   Consider addressing warnings for optimal performance")
        else:
            print("❌ WFC has critical issues")
            print("   Fix errors above before using WFC")

        print()


def main():
    """Run WFC doctor."""
    doctor = WFCDoctor()
    is_healthy = doctor.run_all_checks()

    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()
