"""
Merge operations API

Serialized merges with pre-flight checks.
"""

import subprocess
from typing import Dict
from queue import Queue


class MergeOperations:
    """Merge operations for WFC"""
    
    def __init__(self):
        self.merge_queue = Queue()
        self.current_merge = None
    
    def execute(self, branch: str, strategy: str = "ff-only") -> Dict:
        """Execute merge with pre-flight checks"""
        try:
            # Pre-flight: check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch],
                capture_output=True
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Branch {branch} does not exist"
                }
            
            # Merge
            cmd = ["git", "merge"]
            if strategy == "ff-only":
                cmd.append("--ff-only")
            elif strategy == "no-ff":
                cmd.append("--no-ff")
            cmd.append(branch)
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Get merge SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )
            
            return {
                "success": True,
                "merge_sha": result.stdout.strip(),
                "message": f"Merged {branch}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Merge failed: {e.stderr.decode() if e.stderr else str(e)}"
            }
    
    def queue(self, task_id: str, branch: str) -> Dict:
        """Add merge to queue"""
        self.merge_queue.put({"task_id": task_id, "branch": branch})
        return {
            "success": True,
            "position": self.merge_queue.qsize()
        }
    
    def abort(self) -> Dict:
        """Abort current merge"""
        try:
            subprocess.run(
                ["git", "merge", "--abort"],
                check=True,
                capture_output=True
            )
            return {
                "success": True,
                "message": "Merge aborted"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to abort: {e.stderr.decode() if e.stderr else str(e)}"
            }
    
    def validate(self, branch: str) -> Dict:
        """Check if merge is ready"""
        try:
            # Check if branch is up to date with base
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", "main", branch],
                capture_output=True
            )
            up_to_date = result.returncode == 0
            
            return {
                "success": True,
                "ready": up_to_date,
                "message": "Ready to merge" if up_to_date else "Needs rebase"
            }
        except subprocess.CalledProcessError:
            return {
                "success": False,
                "ready": False,
                "message": "Failed to validate"
            }


# Singleton
_instance = MergeOperations()

def execute(branch: str, strategy: str = "ff-only") -> Dict:
    return _instance.execute(branch, strategy)

def queue(task_id: str, branch: str) -> Dict:
    return _instance.queue(task_id, branch)

def abort() -> Dict:
    return _instance.abort()

def validate(branch: str) -> Dict:
    return _instance.validate(branch)
