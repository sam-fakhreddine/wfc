"""
Semver operations API

Semantic versioning from conventional commits.
"""

import subprocess
import re
from typing import Dict, Optional


def current() -> Optional[str]:
    """Get current version from git tags"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"], check=True, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def calculate(since: Optional[str] = None) -> Dict:
    """Calculate version bump from commits"""
    try:
        # Get commits since last tag or since specified ref
        if since is None:
            since = current() or "HEAD~10"

        result = subprocess.run(
            ["git", "log", f"{since}..HEAD", "--pretty=format:%s"],
            check=True,
            capture_output=True,
            text=True,
        )

        has_breaking = False
        has_feat = False
        has_fix = False

        for line in result.stdout.split("\n"):
            if "BREAKING CHANGE" in line or line.startswith("!"):
                has_breaking = True
            elif line.startswith("feat"):
                has_feat = True
            elif line.startswith("fix"):
                has_fix = True

        if has_breaking:
            bump_type = "major"
        elif has_feat:
            bump_type = "minor"
        elif has_fix:
            bump_type = "patch"
        else:
            bump_type = "none"

        return {
            "success": True,
            "bump_type": bump_type,
            "has_breaking": has_breaking,
            "has_feat": has_feat,
            "has_fix": has_fix,
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Calculate failed: {e.stderr.decode() if e.stderr else str(e)}",
        }


def bump(bump_type: str = "patch") -> Dict:
    """Bump version"""
    current_version = current()
    if not current_version:
        new_version = "0.1.0"
    else:
        # Parse version
        match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", current_version)
        if not match:
            return {"success": False, "message": "Invalid version format"}

        major, minor, patch = map(int, match.groups())

        if bump_type == "major":
            new_version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{major}.{minor + 1}.0"
        else:  # patch
            new_version = f"{major}.{minor}.{patch + 1}"

    try:
        # Create tag
        subprocess.run(
            ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
            check=True,
            capture_output=True,
        )

        return {"success": True, "old_version": current_version, "new_version": f"v{new_version}"}
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"Bump failed: {e.stderr.decode() if e.stderr else str(e)}",
        }
