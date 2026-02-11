"""
History operations API

Search commits, audit changes, detect drift.
"""

import subprocess
from typing import Dict, List


def search(pattern: str, max_results: int = 100) -> List[Dict]:
    """Search commit history"""
    try:
        result = subprocess.run(
            ["git", "log", f"--grep={pattern}", f"--max-count={max_results}", 
             "--pretty=format:%H|%an|%ae|%ad|%s"],
            check=True,
            capture_output=True,
            text=True
        )
        
        commits = []
        for line in result.stdout.split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) == 5:
                    commits.append({
                        "sha": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
        
        return commits
    except subprocess.CalledProcessError:
        return []


def audit(since: str = "1 week ago") -> Dict:
    """Audit changes for drift detection"""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--numstat", "--pretty=format:%H"],
            check=True,
            capture_output=True,
            text=True
        )
        
        return {
            "success": True,
            "commits": len([l for l in result.stdout.split("\n") if len(l) == 40]),
            "changes": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Audit failed: {e.stderr.decode() if e.stderr else str(e)}"
        }


def blame(file: str) -> List[Dict]:
    """Get blame for file"""
    try:
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", file],
            check=True,
            capture_output=True,
            text=True
        )
        
        return [{"file": file, "blame": result.stdout}]
    except subprocess.CalledProcessError:
        return []


def search_content(pattern: str) -> List[Dict]:
    """Search file content in history (for secrets scanning)"""
    try:
        result = subprocess.run(
            ["git", "log", "-S", pattern, "--pretty=format:%H|%s", "--all"],
            check=True,
            capture_output=True,
            text=True
        )
        
        matches = []
        for line in result.stdout.split("\n"):
            if line:
                parts = line.split("|", 1)
                if len(parts) == 2:
                    matches.append({
                        "sha": parts[0],
                        "message": parts[1],
                        "pattern": pattern
                    })
        
        return matches
    except subprocess.CalledProcessError:
        return []
