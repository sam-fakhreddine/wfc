#!/usr/bin/env python3
"""
WFC Quality Checker

Pre-review quality gate that runs linting, formatting, and tests before
sending code to wfc-review consensus.

PHILOSOPHY:
- Catch simple issues before expensive multi-agent review
- Enforce code standards automatically
- Provide actionable feedback for fixes
- Token-efficient: Fix linting locally, not in review comments
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json


@dataclass
class QualityCheckResult:
    """Result from a quality check."""
    check_name: str
    passed: bool
    message: str
    details: Optional[str] = None
    fixable: bool = False
    fix_command: Optional[str] = None


@dataclass
class QualityReport:
    """Complete quality check report."""
    passed: bool
    checks: List[QualityCheckResult]
    files_checked: List[str]

    def __str__(self) -> str:
        """Format report for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("WFC QUALITY CHECK REPORT")
        lines.append("=" * 60)

        for check in self.checks:
            status = "✅" if check.passed else "❌"
            lines.append(f"\n{status} {check.check_name}")
            lines.append(f"   {check.message}")

            if check.details:
                lines.append(f"   Details: {check.details}")

            if not check.passed and check.fixable and check.fix_command:
                lines.append(f"   Fix: {check.fix_command}")

        lines.append("\n" + "=" * 60)
        if self.passed:
            lines.append("✅ ALL CHECKS PASSED - Ready for review")
        else:
            lines.append("❌ CHECKS FAILED - Fix issues before review")
        lines.append("=" * 60)

        return "\n".join(lines)


class QualityChecker:
    """
    Run pre-review quality checks on code.

    Checks (in order):
    1. Python formatting (black --check)
    2. Python linting (ruff check)
    3. Type checking (mypy) - optional
    4. Tests (pytest) - optional
    5. Markdown linting (markdownlint) - optional
    """

    def __init__(
        self,
        files: List[str],
        run_tests: bool = True,
        run_type_check: bool = False,
        run_markdown_lint: bool = False,
        project_root: Optional[Path] = None
    ):
        """
        Initialize quality checker.

        Args:
            files: List of file paths to check
            run_tests: Run pytest on relevant test files
            run_type_check: Run mypy type checking
            run_markdown_lint: Run markdown linting
            project_root: Project root directory (default: current)
        """
        self.files = [Path(f) for f in files]
        self.run_tests = run_tests
        self.run_type_check = run_type_check
        self.run_markdown_lint = run_markdown_lint
        self.project_root = project_root or Path.cwd()

        # Separate files by type
        self.python_files = [f for f in self.files if f.suffix == '.py']
        self.markdown_files = [f for f in self.files if f.suffix == '.md']

    def check_all(self) -> QualityReport:
        """
        Run all quality checks.

        Returns:
            QualityReport with results
        """
        checks = []

        # 1. Python formatting
        if self.python_files:
            checks.append(self._check_black())

        # 2. Python linting
        if self.python_files:
            checks.append(self._check_ruff())

        # 3. Type checking (optional)
        if self.run_type_check and self.python_files:
            checks.append(self._check_mypy())

        # 4. Tests (optional)
        if self.run_tests and self.python_files:
            checks.append(self._check_tests())

        # 5. Markdown linting (optional)
        if self.run_markdown_lint and self.markdown_files:
            checks.append(self._check_markdown())

        # Overall pass/fail
        passed = all(check.passed for check in checks)

        return QualityReport(
            passed=passed,
            checks=checks,
            files_checked=[str(f) for f in self.files]
        )

    def _check_black(self) -> QualityCheckResult:
        """Check Python formatting with black."""
        try:
            result = subprocess.run(
                ["black", "--check", "--line-length=100"] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return QualityCheckResult(
                    check_name="Python Formatting (black)",
                    passed=True,
                    message=f"All {len(self.python_files)} Python files formatted correctly"
                )
            else:
                return QualityCheckResult(
                    check_name="Python Formatting (black)",
                    passed=False,
                    message=f"{len(self.python_files)} files need formatting",
                    details=result.stdout[:200] if result.stdout else None,
                    fixable=True,
                    fix_command="black --line-length=100 <files> (or: make format)"
                )

        except FileNotFoundError:
            return QualityCheckResult(
                check_name="Python Formatting (black)",
                passed=False,
                message="black not installed",
                fixable=True,
                fix_command="uv pip install black"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="Python Formatting (black)",
                passed=False,
                message=f"Check failed: {e}"
            )

    def _check_ruff(self) -> QualityCheckResult:
        """Check Python linting with ruff."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--line-length=100"] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return QualityCheckResult(
                    check_name="Python Linting (ruff)",
                    passed=True,
                    message=f"All {len(self.python_files)} Python files pass linting"
                )
            else:
                # Count errors
                error_count = result.stdout.count('\n') if result.stdout else 0

                return QualityCheckResult(
                    check_name="Python Linting (ruff)",
                    passed=False,
                    message=f"{error_count} linting errors found",
                    details=result.stdout[:500] if result.stdout else None,
                    fixable=True,
                    fix_command="ruff check --fix <files> (or: make lint --fix)"
                )

        except FileNotFoundError:
            return QualityCheckResult(
                check_name="Python Linting (ruff)",
                passed=False,
                message="ruff not installed",
                fixable=True,
                fix_command="uv pip install ruff"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="Python Linting (ruff)",
                passed=False,
                message=f"Check failed: {e}"
            )

    def _check_mypy(self) -> QualityCheckResult:
        """Check type hints with mypy."""
        try:
            result = subprocess.run(
                ["mypy"] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return QualityCheckResult(
                    check_name="Type Checking (mypy)",
                    passed=True,
                    message="All type checks passed"
                )
            else:
                error_count = result.stdout.count('error:') if result.stdout else 0

                return QualityCheckResult(
                    check_name="Type Checking (mypy)",
                    passed=False,
                    message=f"{error_count} type errors found",
                    details=result.stdout[:500] if result.stdout else None,
                    fixable=False
                )

        except FileNotFoundError:
            # mypy optional - don't fail if not installed
            return QualityCheckResult(
                check_name="Type Checking (mypy)",
                passed=True,
                message="mypy not installed (optional check skipped)"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="Type Checking (mypy)",
                passed=False,
                message=f"Check failed: {e}"
            )

    def _check_tests(self) -> QualityCheckResult:
        """Run pytest on relevant test files."""
        # Find corresponding test files
        test_files = []
        for py_file in self.python_files:
            # Check if there's a corresponding test file
            potential_test = py_file.parent / f"test_{py_file.name}"
            if potential_test.exists():
                test_files.append(potential_test)

            # Check in tests/ directory
            test_dir = self.project_root / "tests"
            if test_dir.exists():
                potential_test = test_dir / f"test_{py_file.name}"
                if potential_test.exists():
                    test_files.append(potential_test)

        if not test_files:
            return QualityCheckResult(
                check_name="Tests (pytest)",
                passed=True,
                message="No test files found (check skipped)"
            )

        try:
            result = subprocess.run(
                ["pytest", "-v"] + [str(f) for f in test_files],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return QualityCheckResult(
                    check_name="Tests (pytest)",
                    passed=True,
                    message=f"All tests passed ({len(test_files)} test files)"
                )
            else:
                # Extract failure info
                failed = result.stdout.count('FAILED') if result.stdout else 0

                return QualityCheckResult(
                    check_name="Tests (pytest)",
                    passed=False,
                    message=f"{failed} tests failed",
                    details=result.stdout[-500:] if result.stdout else None,
                    fixable=False
                )

        except FileNotFoundError:
            return QualityCheckResult(
                check_name="Tests (pytest)",
                passed=False,
                message="pytest not installed",
                fixable=True,
                fix_command="uv pip install pytest"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="Tests (pytest)",
                passed=False,
                message=f"Tests failed: {e}"
            )

    def _check_markdown(self) -> QualityCheckResult:
        """Check markdown files with markdownlint."""
        try:
            result = subprocess.run(
                ["markdownlint"] + [str(f) for f in self.markdown_files],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return QualityCheckResult(
                    check_name="Markdown Linting",
                    passed=True,
                    message=f"All {len(self.markdown_files)} markdown files pass linting"
                )
            else:
                return QualityCheckResult(
                    check_name="Markdown Linting",
                    passed=False,
                    message="Markdown linting errors found",
                    details=result.stdout[:500] if result.stdout else None,
                    fixable=True,
                    fix_command="markdownlint --fix <files>"
                )

        except FileNotFoundError:
            # markdownlint optional
            return QualityCheckResult(
                check_name="Markdown Linting",
                passed=True,
                message="markdownlint not installed (optional check skipped)"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="Markdown Linting",
                passed=False,
                message=f"Check failed: {e}"
            )


def main():
    """CLI interface for quality checker."""
    import argparse

    parser = argparse.ArgumentParser(description="WFC Quality Checker")
    parser.add_argument("files", nargs="+", help="Files to check")
    parser.add_argument("--no-tests", action="store_true", help="Skip test execution")
    parser.add_argument("--type-check", action="store_true", help="Run mypy type checking")
    parser.add_argument("--markdown", action="store_true", help="Check markdown files")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    checker = QualityChecker(
        files=args.files,
        run_tests=not args.no_tests,
        run_type_check=args.type_check,
        run_markdown_lint=args.markdown
    )

    report = checker.check_all()

    if args.json:
        # JSON output
        output = {
            "passed": report.passed,
            "files_checked": report.files_checked,
            "checks": [
                {
                    "name": c.check_name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details,
                    "fixable": c.fixable,
                    "fix_command": c.fix_command
                }
                for c in report.checks
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(str(report))

    # Exit code
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
