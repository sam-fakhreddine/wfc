#!/usr/bin/env python3
"""
WFC Universal Quality Checker

Uses Trunk.io as the universal linter/formatter for ALL languages.

TRUNK.IO:
- Universal meta-linter (100+ tools integrated)
- Works with Python, JS, TS, Go, Rust, Java, Ruby, C#, YAML, JSON, Markdown
- Auto-detects languages and runs appropriate tools
- Caches results (fast)
- One command for everything

PHILOSOPHY:
- WFC: Use best-in-class tools
- UNIVERSAL: One tool for all languages
- ELEGANT: Simple, fast, comprehensive
"""

import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TrunkCheckResult:
    """Result from Trunk check."""

    passed: bool
    issues_found: int
    files_checked: int
    output: str
    fixable_issues: int


class UniversalQualityChecker:
    """
    Universal quality checker using Trunk.io.

    Trunk automatically:
    - Detects file types
    - Runs appropriate linters (ruff, eslint, clippy, etc.)
    - Runs formatters (black, prettier, gofmt, etc.)
    - Checks security (semgrep, bandit, etc.)
    - Checks for secrets
    """

    def __init__(self, files: Optional[List[str]] = None):
        """
        Initialize checker.

        Args:
            files: Optional list of files to check (default: all tracked files)
        """
        self.files = files

    def check(self, auto_fix: bool = False) -> TrunkCheckResult:
        """
        Run Trunk check.

        Args:
            auto_fix: Automatically fix issues

        Returns:
            TrunkCheckResult
        """
        # Check if Trunk is installed
        if not self._is_trunk_installed():
            return self._install_trunk_prompt()

        # Build command
        cmd = ["trunk", "check"]

        if auto_fix:
            cmd.append("--fix")

        if self.files:
            cmd.extend(self.files)

        # Run Trunk
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes max
            )

            # Parse output
            output = result.stdout + result.stderr
            issues_found = self._count_issues(output)
            fixable_issues = self._count_fixable(output)

            return TrunkCheckResult(
                passed=result.returncode == 0,
                issues_found=issues_found,
                files_checked=len(self.files) if self.files else 0,
                output=output,
                fixable_issues=fixable_issues,
            )

        except subprocess.TimeoutExpired:
            return TrunkCheckResult(
                passed=False,
                issues_found=0,
                files_checked=0,
                output="Trunk check timed out (>5 minutes)",
                fixable_issues=0,
            )

    def format(self) -> TrunkCheckResult:
        """Format all files (auto-fix)."""
        return self.check(auto_fix=True)

    def _is_trunk_installed(self) -> bool:
        """Check if Trunk is installed."""
        try:
            subprocess.run(["trunk", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _install_trunk_prompt(self) -> TrunkCheckResult:
        """Return result prompting to install Trunk."""
        install_msg = """
Trunk.io not installed!

Install with:
  curl https://get.trunk.io -fsSL | bash

Or via Homebrew:
  brew install trunk-io

Or npm:
  npm install -g @trunkio/launcher

More info: https://trunk.io
"""
        return TrunkCheckResult(
            passed=False, issues_found=0, files_checked=0, output=install_msg, fixable_issues=0
        )

    def _count_issues(self, output: str) -> int:
        """Count issues in Trunk output."""
        # Trunk outputs issue counts
        import re

        match = re.search(r"(\d+) issue", output)
        if match:
            return int(match.group(1))
        return 0

    def _count_fixable(self, output: str) -> int:
        """Count fixable issues."""
        # Check for "run trunk check --fix" message
        if "--fix" in output:
            import re

            match = re.search(r"(\d+) fixable", output)
            if match:
                return int(match.group(1))
        return 0


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="WFC Universal Quality Checker (Trunk)")
    parser.add_argument("files", nargs="*", help="Files to check (default: all tracked)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--init", action="store_true", help="Initialize Trunk in project")

    args = parser.parse_args()

    if args.init:
        # Initialize Trunk
        result = subprocess.run(["trunk", "init"], capture_output=True, text=True)
        print(result.stdout)
        sys.exit(result.returncode)

    checker = UniversalQualityChecker(files=args.files if args.files else None)

    if args.fix:
        print("🔧 Running Trunk format (auto-fix)...")
        result = checker.format()
    else:
        print("🔍 Running Trunk check...")
        result = checker.check()

    print(result.output)

    if result.passed:
        print(f"✅ All checks passed ({result.files_checked} files)")
    else:
        print(f"❌ {result.issues_found} issues found")
        if result.fixable_issues > 0:
            print(f"   {result.fixable_issues} can be auto-fixed with: trunk check --fix")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
