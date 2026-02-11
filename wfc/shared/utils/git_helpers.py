"""
WFC Git Helpers - ELEGANT & SIMPLE

Simple wrappers around subprocess git commands for worktree management.

Design: Thin wrappers, no git library dependency, subprocess only.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


class GitHelper:
    """
    Simple git operations via subprocess.

    Used by: wfc:implement (worktree management)

    Design philosophy: Thin wrapper around git CLI, nothing fancy.
    """

    def __init__(self, repo_path: Path):
        """
        Initialize git helper for a repository.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path)

    def run(self, *args: str, check: bool = True) -> Tuple[int, str, str]:
        """
        Run a git command.

        Args:
            *args: Git command arguments (e.g., "status", "--short")
            check: Raise GitError if command fails

        Returns:
            Tuple of (return_code, stdout, stderr)

        Raises:
            GitError: If check=True and command fails
        """
        cmd = ["git", "-C", str(self.repo_path)] + list(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if check and result.returncode != 0:
                raise GitError(
                    f"Git command failed: {' '.join(cmd)}\n"
                    f"Exit code: {result.returncode}\n"
                    f"Stderr: {result.stderr}"
                )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            raise GitError(f"Git command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            raise GitError("Git not found in PATH")

    def worktree_add(self, path: Path, branch: str, from_branch: str = "main") -> None:
        """
        Create a new worktree.

        Args:
            path: Path for new worktree
            branch: Branch name to create
            from_branch: Branch to branch from (default: main)
        """
        self.run("worktree", "add", "-b", branch, str(path), from_branch)

    def worktree_remove(self, path: Path, force: bool = False) -> None:
        """
        Remove a worktree.

        Args:
            path: Path to worktree
            force: Force removal even if dirty
        """
        args = ["worktree", "remove", str(path)]
        if force:
            args.append("--force")
        self.run(*args)

    def worktree_list(self) -> List[str]:
        """
        List all worktrees.

        Returns:
            List of worktree paths
        """
        _, stdout, _ = self.run("worktree", "list", "--porcelain")
        worktrees = []
        for line in stdout.splitlines():
            if line.startswith("worktree "):
                worktrees.append(line.split(" ", 1)[1])
        return worktrees

    def current_branch(self) -> str:
        """Get current branch name."""
        _, stdout, _ = self.run("rev-parse", "--abbrev-ref", "HEAD")
        return stdout.strip()

    def current_commit(self) -> str:
        """Get current commit SHA."""
        _, stdout, _ = self.run("rev-parse", "HEAD")
        return stdout.strip()

    def create_branch(self, branch: str, from_ref: str = "HEAD") -> None:
        """Create a new branch."""
        self.run("branch", branch, from_ref)

    def checkout(self, ref: str) -> None:
        """Checkout a branch or commit."""
        self.run("checkout", ref)

    def merge(self, branch: str, ff_only: bool = True) -> None:
        """
        Merge a branch.

        Args:
            branch: Branch to merge
            ff_only: Only allow fast-forward merges
        """
        args = ["merge"]
        if ff_only:
            args.append("--ff-only")
        args.append(branch)
        self.run(*args)

    def rebase(self, onto: str) -> None:
        """Rebase current branch onto another branch."""
        self.run("rebase", onto)

    def revert(self, commit: str, no_edit: bool = True) -> None:
        """
        Revert a commit.

        Args:
            commit: Commit SHA to revert
            no_edit: Don't open editor for commit message
        """
        args = ["revert", commit]
        if no_edit:
            args.append("--no-edit")
        self.run(*args)

    def is_clean(self) -> bool:
        """Check if working directory is clean."""
        _, stdout, _ = self.run("status", "--porcelain")
        return len(stdout.strip()) == 0

    def has_conflicts(self) -> bool:
        """Check if there are merge conflicts."""
        returncode, stdout, _ = self.run("diff", "--name-only", "--diff-filter=U", check=False)
        return len(stdout.strip()) > 0


# Convenience function
def get_git(repo_path: Path) -> GitHelper:
    """
    Get GitHelper instance.

    Args:
        repo_path: Path to git repository

    Returns:
        GitHelper instance
    """
    return GitHelper(repo_path)


if __name__ == "__main__":
    # Simple test (requires being in a git repo)
    try:
        git = get_git(Path.cwd())
        print(f"Current branch: {git.current_branch()}")
        print(f"Current commit: {git.current_commit()}")
        print(f"Working directory clean: {git.is_clean()}")
        print(f"Worktrees: {git.worktree_list()}")
    except GitError as e:
        print(f"Git error: {e}")
