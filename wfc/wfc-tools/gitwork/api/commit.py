"""
Commit operations API

Conventional commits with task and property references.
Format: type(scope): description [TASK-XXX] [PROP-XXX]
"""

import re
import subprocess
from typing import Dict, List, Optional

from .validators import is_flag_injection, validate_file_path


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
        if message and is_flag_injection(message):
            return {
                "success": False,
                "message": "Invalid commit message: starts with '-'",
            }

        if files:
            for f in files:
                if not validate_file_path(f):
                    return {
                        "success": False,
                        "message": f"Invalid file path: {f}",
                    }

        formatted = self._format_message(message, task_id, properties, type, scope)

        validation = self.validate_message(formatted)
        if not validation["valid"]:
            return {
                "success": False,
                "message": f"Invalid commit message: {validation['violations']}",
            }

        try:
            if files:
                subprocess.run(["git", "add"] + files, check=True)

            subprocess.run(["git", "commit", "-m", formatted], check=True, capture_output=True)

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
        if message and is_flag_injection(message):
            return {"success": False, "message": "Invalid commit message: starts with '-'"}

        if files:
            for f in files:
                if not validate_file_path(f):
                    return {"success": False, "message": f"Invalid file path: {f}"}

        try:
            result = subprocess.run(["git", "log", "@{u}..HEAD"], capture_output=True, text=True)
            if not result.stdout.strip():
                return {"success": False, "message": "Cannot amend: commit already pushed"}

            if files:
                subprocess.run(["git", "add"] + files, check=True)

            cmd = ["git", "commit", "--amend"]
            if message:
                cmd.extend(["-m", message])
            else:
                cmd.append("--no-edit")

            subprocess.run(cmd, check=True, capture_output=True)

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
        if scope:
            formatted = f"{type}({scope}): {message}"
        else:
            formatted = f"{type}: {message}"

        if task_id:
            formatted += f" [{task_id}]"

        if properties and len(properties) > 0:
            props_str = ", ".join(properties)
            formatted += f" [{props_str}]"

        return formatted

    def _suggest_fix(self, message: str) -> str:
        """Suggest fix for invalid message"""
        return f"chore: {message}"


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
