"""
Allowlist generator - creates categorized safe command lists
"""

from dataclasses import dataclass
from typing import List

from .scanner import ProjectProfile


@dataclass
class AllowlistCategories:
    """Categorized allowlist"""

    universal: List[str]
    git_read: List[str]
    git_write: List[str]
    language_specific: List[str]
    build_ci: List[str]
    file_patterns: List[str]


class AllowlistGenerator:
    """Generates safe allowlists based on project profile"""

    UNIVERSAL_SAFE = [
        "ls",
        "ll",
        "la",
        "tree",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "wc",
        "sort",
        "uniq",
        "diff",
        "grep",
        "rg",
        "ag",
        "find",
        "fd",
        "echo",
        "printf",
        "pwd",
        "cd",
        "env",
        "printenv",
        "date",
        "cal",
        "file",
        "stat",
        "du",
        "df",
        "which",
        "whereis",
        "type",
    ]

    GIT_READ = [
        "git status",
        "git log",
        "git diff",
        "git show",
        "git branch",
        "git remote -v",
        "git ls-files",
    ]

    GIT_WRITE = [
        "git add",
        "git commit",
        "git push",
        "git pull",
        "git checkout",
        "git merge",
        "git rebase",
    ]

    def generate(self, profile: ProjectProfile, strict_mode: bool = False) -> AllowlistCategories:
        """Generate allowlist from project profile"""

        allowlist = AllowlistCategories(
            universal=self.UNIVERSAL_SAFE.copy(),
            git_read=self.GIT_READ.copy(),
            git_write=[] if strict_mode else self.GIT_WRITE.copy(),
            language_specific=self._language_commands(profile),
            build_ci=self._build_ci_commands(profile, strict_mode),
            file_patterns=self._file_patterns(profile, strict_mode),
        )

        return allowlist

    def _language_commands(self, profile: ProjectProfile) -> List[str]:
        """Generate language-specific commands"""
        commands = []

        if profile.project_type == "nodejs":
            commands.extend(
                [
                    f"{profile.package_manager} install",
                    f"{profile.package_manager} test",
                    f"{profile.package_manager} run",
                    "node",
                    "npx",
                ]
            )
        elif profile.project_type == "python":
            commands.extend(["python", "pip", "pytest", "ruff", "black"])
        elif profile.project_type == "rust":
            commands.extend(["cargo build", "cargo test", "cargo run", "rustfmt", "clippy"])
        elif profile.project_type == "go":
            commands.extend(["go build", "go test", "go run", "go fmt"])

        return commands

    def _build_ci_commands(self, profile: ProjectProfile, strict_mode: bool) -> List[str]:
        """Generate build/CI commands"""
        if strict_mode:
            return []

        commands = []

        if profile.test_command:
            commands.append(profile.test_command)
        if profile.build_command:
            commands.append(profile.build_command)

        if profile.has_docker:
            commands.extend(["docker ps", "docker images", "docker logs"])

        if profile.has_ci == "github-actions":
            commands.append("gh")

        return commands

    def _file_patterns(self, profile: ProjectProfile, strict_mode: bool) -> List[str]:
        """Generate file access patterns"""
        patterns = []

        # Source directories (read/write)
        if not strict_mode:
            for d in profile.directories.get("source", []):
                patterns.append(f"{d}**")
            for d in profile.directories.get("tests", []):
                patterns.append(f"{d}**")

        # Config (read only)
        for d in profile.directories.get("config", []):
            patterns.append(f"{d}** (read-only)")

        # Generated (never write)
        for d in profile.directories.get("generated", []):
            patterns.append(f"{d}** (read-only)")

        # Never allow
        patterns.append(".env (read-only)")
        patterns.append(".env.* (read-only)")

        return patterns
