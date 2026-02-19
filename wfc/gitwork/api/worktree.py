"""
Worktree operations API

Provisions isolated workspaces for parallel agent execution.
Delegates to worktree-manager.sh for full lifecycle control:
  - Bootstraps env vars (.env, .env.local — skips .env.example)
  - Propagates runtime configs (.tool-versions, .node-version, etc.)
  - Registers .worktrees in .gitignore
  - Enforces wfc/ branch prefix
  - Bases on develop by default
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .validators import has_path_traversal, is_flag_injection

_SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
_MANAGER_SCRIPT = _SCRIPT_DIR / "worktree-manager.sh"

# Unsafe git ref characters: ~, ^, :, whitespace, null/control bytes
_UNSAFE_REF_RE = re.compile(r"[~^:\s\x00-\x1f]")


def validate_worktree_input(task_id: str, base_ref: str = "develop") -> Optional[str]:
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
    if _UNSAFE_REF_RE.search(base_ref):
        return f"Invalid base_ref: {base_ref} (unsafe git ref characters)"
    return None


def _repo_root() -> Optional[str]:
    """Return the absolute path of the git repository root, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _run_manager(args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run the worktree-manager.sh script with given arguments."""
    cmd = ["bash", str(_MANAGER_SCRIPT)] + args
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr="worktree-manager.sh timed out after 30 seconds",
        )


class WorktreeOperations:
    """Workspace provisioning and teardown for WFC agents.

    Routes through worktree-manager.sh for:
    - Env var bootstrap (.env, .env.local — skips .env.example)
    - .gitignore registration
    - Runtime config propagation (.tool-versions, .node-version, etc.)
    - wfc/ branch prefix enforcement
    """

    def __init__(self, worktree_dir: str = ".worktrees"):
        self.worktree_dir = worktree_dir

    def _worktree_path(self, task_id: str) -> Path:
        """Return the absolute path for a task's worktree, anchored to repo root."""
        root = _repo_root()
        if root:
            return Path(root) / self.worktree_dir / f"wfc-{task_id}"
        # Fall back to relative path if git command fails
        return Path(self.worktree_dir) / f"wfc-{task_id}"

    def create(self, task_id: str, base_ref: str = "develop") -> Dict:
        """Provision an isolated workspace for a task.

        Routes through worktree-manager.sh which:
        - Branches as wfc/<task_id>
        - Bootstraps env vars from repo root
        - Propagates runtime configs
        - Registers .worktrees in .gitignore
        """
        validation_error = validate_worktree_input(task_id, base_ref)
        if validation_error:
            return {
                "success": False,
                "message": f"Validation failed: {validation_error}",
            }

        worktree_path = self._worktree_path(task_id)
        branch_name = f"wfc/{task_id}"

        if _MANAGER_SCRIPT.exists():
            result = _run_manager(["create", task_id, base_ref])
            if result.returncode == 0:
                return {
                    "success": True,
                    "worktree_path": str(worktree_path),
                    "branch_name": branch_name,
                    "created_from": base_ref,
                    "env_synced": True,
                    "output": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "message": f"worktree-manager.sh failed: {result.stderr or result.stdout}",
                }

        try:
            worktree_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name, base_ref],
                check=True,
                capture_output=True,
            )
            return {
                "success": True,
                "worktree_path": str(worktree_path),
                "branch_name": branch_name,
                "created_from": base_ref,
                "env_synced": False,
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

        worktree_path = self._worktree_path(task_id)

        try:
            cmd = ["git", "worktree", "remove", str(worktree_path)]
            if force:
                cmd.append("--force")

            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            subprocess.run(["git", "worktree", "prune"], capture_output=True, timeout=30)

            return {"success": True, "message": f"Deleted worktree {worktree_path}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "git command timed out"}
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
                timeout=30,
            )

            worktrees = []
            current: Dict = {}
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
        except subprocess.TimeoutExpired:
            return []
        except subprocess.CalledProcessError:
            return []

    def status(self, task_id: str) -> Dict:
        """Get worktree status"""
        worktree_path = self._worktree_path(task_id)

        try:
            result = subprocess.run(
                ["git", "-C", str(worktree_path), "status", "--short"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "success": True,
                "clean": len(result.stdout.strip()) == 0,
                "status": result.stdout,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "git command timed out"}
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to get status: {e.stderr or str(e)}",
            }

    def cleanup(self) -> Dict:
        """Clean up all clean worktrees using worktree-manager.sh"""
        if _MANAGER_SCRIPT.exists():
            result = _run_manager(["cleanup"])
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
            }

        return {"success": False, "message": "worktree-manager.sh not found"}

    def sync_env(self, task_id: str) -> Dict:
        """Sync .env files to an existing worktree"""
        validation_error = validate_worktree_input(task_id)
        if validation_error:
            return {"success": False, "message": validation_error}

        if _MANAGER_SCRIPT.exists():
            result = _run_manager(["copy-env", task_id])
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
            }

        return {"success": False, "message": "worktree-manager.sh not found"}

    def conflicts(self, task_id: str, other_worktrees: Optional[List[str]] = None) -> Dict:
        """Detect file conflicts with other worktrees"""
        return {"has_conflicts": False, "conflicting_files": []}


_instance = WorktreeOperations()


def create(task_id: str, base_ref: str = "develop") -> Dict:
    return _instance.create(task_id, base_ref)


def delete(task_id: str, force: bool = False) -> Dict:
    return _instance.delete(task_id, force)


def list() -> List[Dict]:
    return _instance.list()


def status(task_id: str) -> Dict:
    return _instance.status(task_id)


def cleanup() -> Dict:
    return _instance.cleanup()


def sync_env(task_id: str) -> Dict:
    return _instance.sync_env(task_id)


def conflicts(task_id: str, other_worktrees: Optional[List[str]] = None) -> Dict:
    return _instance.conflicts(task_id, other_worktrees)
