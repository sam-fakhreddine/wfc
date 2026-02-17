"""
Pull Request operations API

Handles GitHub PR creation via gh CLI with WFC review integration.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class PRResult:
    """Result of PR operation"""

    success: bool
    pr_url: Optional[str]
    pr_number: Optional[int]
    branch: str
    message: str
    pushed: bool = False


class PROperations:
    """Pull request operations for WFC"""

    PROTECTED_BRANCHES = ["main", "master", "develop", "production"]

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize PR operations.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()

    def check_gh_cli(self) -> Dict[str, Any]:
        """
        Check if gh CLI is installed and authenticated.

        Returns:
            Dict with:
                - installed: bool
                - authenticated: bool
                - message: str
                - install_instructions: Optional[str]
        """
        # Check if gh is installed
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {
                    "installed": False,
                    "authenticated": False,
                    "message": "gh CLI not found",
                    "install_instructions": self._get_install_instructions(),
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "installed": False,
                "authenticated": False,
                "message": "gh CLI not found",
                "install_instructions": self._get_install_instructions(),
            }

        # Check authentication
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, timeout=5
            )
            authenticated = result.returncode == 0

            return {
                "installed": True,
                "authenticated": authenticated,
                "message": "gh CLI ready" if authenticated else "gh CLI not authenticated",
                "install_instructions": None if authenticated else "Run: gh auth login",
            }
        except subprocess.TimeoutExpired:
            return {
                "installed": True,
                "authenticated": False,
                "message": "gh auth check timed out",
                "install_instructions": "Run: gh auth login",
            }

    def push_branch(
        self, branch: str, remote: str = "origin", force: bool = False
    ) -> Dict[str, Any]:
        """
        Push branch to remote.

        Args:
            branch: Branch name to push
            remote: Remote name (default: origin)
            force: Force push (default: False, requires explicit user request)

        Returns:
            Dict with success status and message
        """
        # Safety check: never force push to protected branches
        if force and branch in self.PROTECTED_BRANCHES:
            return {
                "success": False,
                "message": f"⚠️  BLOCKED: Cannot force push to protected branch '{branch}'",
            }

        try:
            cmd = ["git", "push"]

            # Add force flag if requested (and safe)
            if force:
                cmd.append("--force-with-lease")  # Safer than --force

            # Add upstream tracking
            cmd.extend(["-u", remote, branch])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Pushed {branch} to {remote}",
                    "output": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "message": f"Push failed: {result.stderr}",
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Push timed out (check network connection)"}
        except Exception as e:
            return {"success": False, "message": f"Push failed: {str(e)}"}

    def create_pr(
        self,
        branch: str,
        task: Dict[str, Any],
        review_report: Optional[Dict[str, Any]] = None,
        base: str = "main",
        draft: bool = True,
        auto_push: bool = True,
    ) -> PRResult:
        """
        Create GitHub PR with WFC review data.

        Args:
            branch: Feature branch name
            task: Task dict with id, title, description, acceptance_criteria
            review_report: Optional review report from consensus review
            base: Base branch (default: main)
            draft: Create as draft PR (default: True)
            auto_push: Automatically push branch before creating PR (default: True)

        Returns:
            PRResult with success status, PR URL, and details
        """
        # Check gh CLI
        gh_check = self.check_gh_cli()
        if not gh_check["installed"]:
            return PRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch=branch,
                message=f"❌ {gh_check['message']}\n\n{gh_check['install_instructions']}",
                pushed=False,
            )

        if not gh_check["authenticated"]:
            return PRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch=branch,
                message=f"❌ {gh_check['message']}\n\n{gh_check['install_instructions']}",
                pushed=False,
            )

        # Push branch if requested
        pushed = False
        if auto_push:
            push_result = self.push_branch(branch)
            if not push_result["success"]:
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    message=f"Failed to push branch: {push_result['message']}",
                    pushed=False,
                )
            pushed = True

        # Generate PR title and body
        pr_title = self._generate_pr_title(task)
        pr_body = self._generate_pr_body(task, review_report)

        # Create PR via gh CLI
        try:
            cmd = [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--base",
                base,
                "--head",
                branch,
            ]

            if draft:
                cmd.append("--draft")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=self.project_root
            )

            if result.returncode == 0:
                # Extract PR URL from output
                pr_url = result.stdout.strip()

                # Extract PR number from URL (e.g., https://github.com/user/repo/pull/123)
                pr_number = None
                if pr_url:
                    parts = pr_url.rstrip("/").split("/")
                    if parts[-2] == "pull" and parts[-1].isdigit():
                        pr_number = int(parts[-1])

                return PRResult(
                    success=True,
                    pr_url=pr_url,
                    pr_number=pr_number,
                    branch=branch,
                    message=f"✅ Created PR #{pr_number}: {pr_url}",
                    pushed=pushed,
                )
            else:
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    message=f"Failed to create PR: {result.stderr}",
                    pushed=pushed,
                )

        except subprocess.TimeoutExpired:
            return PRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch=branch,
                message="PR creation timed out (check network connection)",
                pushed=pushed,
            )
        except Exception as e:
            return PRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch=branch,
                message=f"Failed to create PR: {str(e)}",
                pushed=pushed,
            )

    def _generate_pr_title(self, task: Dict[str, Any]) -> str:
        """
        Generate PR title from task.

        Args:
            task: Task dict with id and title

        Returns:
            Formatted PR title
        """
        task_id = task.get("id", "TASK-XXX")
        title = task.get("title", task.get("description", "Implement task"))

        # Truncate title if too long (GitHub limit is 256 chars)
        max_length = 70  # Keep it short and readable
        if len(title) > max_length:
            title = title[: max_length - 3] + "..."

        return f"{task_id}: {title}"

    def _generate_pr_body(
        self, task: Dict[str, Any], review_report: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate PR body from task and review report.

        Args:
            task: Task dict with description, acceptance_criteria
            review_report: Optional consensus review report

        Returns:
            Formatted PR body in Markdown
        """
        lines = []

        # Task section
        task_id = task.get("id", "TASK-XXX")
        lines.append(f"## Task: {task_id}")
        lines.append("")

        description = task.get("description", "No description provided")
        lines.append(description)
        lines.append("")

        # Acceptance criteria
        criteria = task.get("acceptance_criteria", [])
        if criteria:
            lines.append("## Acceptance Criteria")
            lines.append("")
            for criterion in criteria:
                lines.append(f"- [x] {criterion}")
            lines.append("")

        # WFC Review section
        if review_report:
            lines.append("## WFC Consensus Review")
            lines.append("")

            # Overall status
            status = review_report.get("status", "UNKNOWN")
            score = review_report.get("overall_score", 0)
            lines.append(f"**Status**: {status}")
            lines.append(f"**Score**: {score:.1f}/10")
            lines.append("")

            # Agent reviews
            agent_reviews = review_report.get("agent_reviews", [])
            if agent_reviews:
                lines.append("### Agent Reviews")
                lines.append("")
                for review in agent_reviews:
                    agent = review.get("agent", "Unknown")
                    agent_score = review.get("score", 0)
                    domain = review.get("domain", "general")
                    lines.append(f"- **{agent}** ({domain}): {agent_score}/10")
                lines.append("")

            # Critical issues
            critical_issues = review_report.get("critical_issues", [])
            if critical_issues:
                lines.append("### ⚠️ Critical Issues")
                lines.append("")
                for issue in critical_issues:
                    lines.append(f"- {issue}")
                lines.append("")

        # Properties satisfied
        properties = task.get("properties_verified", [])
        if properties:
            lines.append("## Properties Satisfied")
            lines.append("")
            for prop in properties:
                lines.append(f"- ✅ {prop}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("🤖 Generated by **WFC** (World Fucking Class)")

        return "\n".join(lines)

    def _get_install_instructions(self) -> str:
        """Get platform-specific gh CLI install instructions."""
        return """
Install GitHub CLI:

macOS:
  brew install gh

Ubuntu/Debian:
  sudo apt install gh

Windows:
  winget install --id GitHub.cli

Or download from: https://cli.github.com

After install, authenticate:
  gh auth login
""".strip()


# Singleton instance
_pr_ops = None


def get_pr_operations(project_root: Optional[Path] = None) -> PROperations:
    """Get singleton PR operations instance."""
    global _pr_ops
    if _pr_ops is None or project_root is not None:
        _pr_ops = PROperations(project_root)
    return _pr_ops
