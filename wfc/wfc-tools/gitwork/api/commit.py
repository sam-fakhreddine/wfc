"""
Commit operations API

Conventional commits with task and property references.
Format: type(scope): description [TASK-XXX] [PROP-XXX]
"""

import subprocess
import re
from typing import List, Optional, Dict

_FLAG_PATTERN = re.compile(r"^-")


def validate_file_path(path: str) -> bool:
    """Validate file path - no traversal or injection."""
    if not path:
        return False
    if ".." in path:
        return False
    if _FLAG_PATTERN.match(path):
        return False
    # Reject null bytes
    if "\x00" in path:
        return False
    return True


class CommitOperations:
    """Commit operations for WFC"""

    def create(
        self,
        message: str,
        files: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        properties: Optional[List[str]] = None,
        type: str = "chore",
        scope: Optional[str] = None,
    ) -> Dict:
        """
        Create conventional commit.

        Format: type(scope): description [TASK-XXX] [PROP-XXX, PROP-YYY]
        """
        # Validate message doesn't start with '-' (flag injection)
        if message and _FLAG_PATTERN.match(message):
            return {
                "success": False,
                "message": "Invalid commit message: starts with '-'",
            }

        # Validate file paths
        if files:
            for f in files:
                if not validate_file_path(f):
                    return {
                        "success": False,
                        "message": f"Invalid file path: {f}",
                    }

        # Build formatted message
        formatted = self._format_message(message, task_id, properties, type, scope)

        # Validate
        validation = self.validate_message(formatted)
        if not validation["valid"]:
            return {
                "success": False,
                "message": f"Invalid commit message: {validation['violations']}",
            }

        try:
            # Stage files if provided
            if files:
                subprocess.run(["git", "add"] + files, check=True)

            # Commit
            subprocess.run(["git", "commit", "-m", formatted], check=True, capture_output=True)

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            )
            sha = result.stdout.strip()

            return {"success": True, "sha": sha, "formatted_message": formatted}
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to commit: {e.stderr.decode() if e.stderr else str(e)}",
            }

    def validate_message(self, message: str) -> Dict:
        """Validate commit message format"""
        # Pattern: type(scope): description [TASK-XXX] [PROP-XXX]
        # Scope and refs are optional
        pattern = (
            r"^(feat|fix|chore|refactor|test|docs|ci|security|perf|style)(\([a-z0-9-]+\))?: .+"
        )

        violations = []
        if not re.match(pattern, message):
            violations.append("Message must start with type(scope): description")
            violations.append(
                "Valid types: feat, fix, chore, refactor, test, docs, ci, security, perf, style"
            )

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "suggested_fix": self._suggest_fix(message) if violations else None,
        }

    def amend(self, message: Optional[str] = None, files: Optional[List[str]] = None) -> Dict:
        """Amend last commit (safe - checks if pushed)"""
        # Validate message if provided
        if message and _FLAG_PATTERN.match(message):
            return {"success": False, "message": "Invalid commit message: starts with '-'"}

        # Validate file paths
        if files:
            for f in files:
                if not validate_file_path(f):
                    return {"success": False, "message": f"Invalid file path: {f}"}

        try:
            # Check if commit is pushed
            result = subprocess.run(["git", "log", "@{u}..HEAD"], capture_output=True, text=True)
            if not result.stdout.strip():
                return {"success": False, "message": "Cannot amend: commit already pushed"}

            # Stage files if provided
            if files:
                subprocess.run(["git", "add"] + files, check=True)

            # Amend
            cmd = ["git", "commit", "--amend"]
            if message:
                cmd.extend(["-m", message])
            else:
                cmd.append("--no-edit")

            subprocess.run(cmd, check=True, capture_output=True)

            # Get new SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            )

            return {"success": True, "sha": result.stdout.strip()}
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to amend: {e.stderr.decode() if e.stderr else str(e)}",
            }

    def _format_message(
        self,
        message: str,
        task_id: Optional[str],
        properties: Optional[List[str]],
        type: str,
        scope: Optional[str],
    ) -> str:
        """Format message with task and property refs"""
        # Base format
        if scope:
            formatted = f"{type}({scope}): {message}"
        else:
            formatted = f"{type}: {message}"

        # Add task ref
        if task_id:
            formatted += f" [{task_id}]"

        # Add property refs
        if properties and len(properties) > 0:
            props_str = ", ".join(properties)
            formatted += f" [{props_str}]"

        return formatted

    def _suggest_fix(self, message: str) -> str:
        """Suggest fix for invalid message"""
        return f"chore: {message}"


# Singleton
_instance = CommitOperations()


def create(
    message: str,
    files: Optional[List[str]] = None,
    task_id: Optional[str] = None,
    properties: Optional[List[str]] = None,
    type: str = "chore",
    scope: Optional[str] = None,
) -> Dict:
    return _instance.create(message, files, task_id, properties, type, scope)


def validate_message(message: str) -> Dict:
    return _instance.validate_message(message)


def amend(message: Optional[str] = None, files: Optional[List[str]] = None) -> Dict:
    return _instance.amend(message, files)
