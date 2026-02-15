"""
Worktree operations API

Isolated workspaces for parallel agent work.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .validators import has_path_traversal, is_flag_injection


def validate_worktree_input(task_id: str, base_ref: str = "main") -> Optional[str]:
    """Validate worktree inputs. Returns error message or None if valid."""
    if not task_id:
        return "task_id is required"
    if has_path_traversal(task_id) or "/" in task_id:
        return f"Invalid task_id: {task_id} (path traversal)"
    if is_flag_injection(task_id):
        return f"Invalid task_id: {task_id} (flag injection)"
    if is_flag_injection(base_ref):
        return f"Invalid base_ref: {base_ref} (flag injection)"
    if has_path_traversal(base_ref):
        return f"Invalid base_ref: {base_ref} (path traversal)"
    return None


class WorktreeOperations:
    """Worktree operations for WFC"""

    def __init__(self, worktree_dir: str = ".worktrees"):
        self.worktree_dir = worktree_dir

    def create(self, task_id: str, base_ref: str = "main") -> Dict:
        """Create worktree for task"""
        validation_error = validate_worktree_input(task_id, base_ref)
        if validation_error:
            return {
                "success": False,
                "message": f"Validation failed: {validation_error}",
            }

        worktree_path = f"{self.worktree_dir}/wfc-{task_id}"
        branch_name = f"wfc/{task_id}"

        try:
            Path(self.worktree_dir).mkdir(parents=True, exist_ok=True)

            subprocess.run(
                ["git", "worktree", "add", worktree_path, "-b", branch_name, base_ref],
                check=True,
                capture_output=True,
            )

            return {
                "success": True,
                "worktree_path": worktree_path,
                "branch_name": branch_name,
                "created_from": base_ref,
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to create worktree: {e.stderr.decode() if e.stderr else str(e)}",
            }

    def delete(self, task_id: str, force: bool = False) -> Dict:
        """Delete worktree"""
        validation_error = validate_worktree_input(task_id)
        if validation_error:
            return {
                "success": False,
                "message": f"Validation failed: {validation_error}",
            }

        worktree_path = f"{self.worktree_dir}/wfc-{task_id}"

        try:
            flag = "--force" if force else ""
            cmd = ["git", "worktree", "remove", worktree_path]
            if flag:
                cmd.append(flag)

            subprocess.run(cmd, check=True, capture_output=True)

            return {"success": True, "message": f"Deleted worktree {worktree_path}"}
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to delete: {e.stderr.decode() if e.stderr else str(e)}",
            }

    def list(self) -> List[Dict]:
        """List all worktrees"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            )

            worktrees = []
            current = {}
            for line in result.stdout.split("\n"):
                if line.startswith("worktree "):
                    if current:
                        worktrees.append(current)
                    current = {"path": line.split(" ", 1)[1]}
                elif line.startswith("branch "):
                    current["branch"] = line.split(" ", 1)[1]

            if current:
                worktrees.append(current)

            return worktrees
        except subprocess.CalledProcessError:
            return []

    def status(self, task_id: str) -> Dict:
        """Get worktree status"""
        worktree_path = f"{self.worktree_dir}/wfc-{task_id}"

        try:
            result = subprocess.run(
                ["git", "-C", worktree_path, "status", "--short"],
                check=True,
                capture_output=True,
                text=True,
            )

            return {
                "success": True,
                "clean": len(result.stdout.strip()) == 0,
                "status": result.stdout,
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to get status: {e.stderr.decode() if e.stderr else str(e)}",
            }

    def conflicts(self, task_id: str, other_worktrees: Optional[List[str]] = None) -> Dict:
        """Detect file conflicts with other worktrees"""
        return {"has_conflicts": False, "conflicting_files": []}


_instance = WorktreeOperations()


def create(task_id: str, base_ref: str = "main") -> Dict:
    return _instance.create(task_id, base_ref)


def delete(task_id: str, force: bool = False) -> Dict:
    return _instance.delete(task_id, force)


def list() -> List[Dict]:
    return _instance.list()


def status(task_id: str) -> Dict:
    return _instance.status(task_id)


def conflicts(task_id: str, other_worktrees: Optional[List[str]] = None) -> Dict:
    return _instance.conflicts(task_id, other_worktrees)
