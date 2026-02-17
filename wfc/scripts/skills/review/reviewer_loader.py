"""
Reviewer Loader

Loads the 5 fixed reviewer prompts and knowledge files from wfc/reviewers/.
Each reviewer has a PROMPT.md (required) and KNOWLEDGE.md (optional).

Replaces PersonaOrchestrator's dynamic selection with deterministic loading
of exactly 5 reviewers: security, correctness, performance, maintainability,
reliability.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

REVIEWER_IDS: list[str] = [
    "security",
    "correctness",
    "performance",
    "maintainability",
    "reliability",
]

DOMAIN_EXTENSIONS: dict[str, set[str]] = {
    "security": {
        ".py",
        ".js",
        ".ts",
        ".go",
        ".java",
        ".rb",
        ".php",
        ".sh",
        ".sql",
        ".yml",
        ".yaml",
        ".json",
        ".env",
        ".toml",
    },
    "correctness": {
        ".py",
        ".js",
        ".ts",
        ".go",
        ".java",
        ".rb",
        ".rs",
        ".c",
        ".cpp",
        ".cs",
    },
    "performance": {
        ".py",
        ".js",
        ".ts",
        ".go",
        ".java",
        ".rs",
        ".sql",
        ".c",
        ".cpp",
    },
    "maintainability": {"*"},
    "reliability": {
        ".py",
        ".js",
        ".ts",
        ".go",
        ".java",
        ".rs",
        ".c",
        ".cpp",
    },
}

DEFAULT_TEMPERATURES: dict[str, float] = {
    "security": 0.3,
    "correctness": 0.5,
    "performance": 0.4,
    "maintainability": 0.6,
    "reliability": 0.4,
}


@dataclass
class ReviewerConfig:
    """Configuration for a single reviewer loaded from disk."""

    id: str
    prompt: str
    knowledge: str
    temperature: float
    relevant: bool


class ReviewerLoader:
    """
    Loads the 5 fixed reviewer configurations from wfc/reviewers/.

    Each reviewer directory contains:
    - PROMPT.md (required) - The reviewer's system prompt
    - KNOWLEDGE.md (optional) - Accumulated domain knowledge
    """

    def __init__(self, reviewers_dir: Path | None = None):
        """
        Initialize the loader.

        Args:
            reviewers_dir: Path to wfc/reviewers/. Defaults to the standard
                           location relative to this file's project root.
        """
        if reviewers_dir is not None:
            self.reviewers_dir = Path(reviewers_dir)
        else:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.reviewers_dir = project_root / "reviewers"

    def load_all(self, diff_files: list[str] | None = None) -> list[ReviewerConfig]:
        """
        Load all 5 reviewers with relevance gate based on diff files.

        Args:
            diff_files: List of file paths in the diff. Used to determine
                        relevance. If None, all reviewers are marked relevant.

        Returns:
            List of 5 ReviewerConfig objects (one per reviewer).

        Raises:
            FileNotFoundError: If reviewers_dir does not exist.
        """
        if not self.reviewers_dir.exists():
            raise FileNotFoundError(f"Reviewers directory not found: {self.reviewers_dir}")

        configs: list[ReviewerConfig] = []
        for reviewer_id in REVIEWER_IDS:
            config = self.load_one(reviewer_id, diff_files=diff_files)
            configs.append(config)

        return configs

    def load_one(
        self,
        reviewer_id: str,
        diff_files: list[str] | None = None,
    ) -> ReviewerConfig:
        """
        Load a single reviewer by ID.

        Args:
            reviewer_id: One of the REVIEWER_IDS.
            diff_files: Optional list of diff file paths for relevance check.

        Returns:
            ReviewerConfig for the requested reviewer.

        Raises:
            ValueError: If reviewer_id is not in REVIEWER_IDS.
            FileNotFoundError: If PROMPT.md is missing for the reviewer.
        """
        if reviewer_id not in REVIEWER_IDS:
            raise ValueError(f"Unknown reviewer '{reviewer_id}'. Valid reviewers: {REVIEWER_IDS}")

        reviewer_dir = self.reviewers_dir / reviewer_id

        prompt_path = reviewer_dir / "PROMPT.md"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"PROMPT.md not found for reviewer '{reviewer_id}': {prompt_path}"
            )
        prompt = prompt_path.read_text(encoding="utf-8")

        knowledge_path = reviewer_dir / "KNOWLEDGE.md"
        knowledge = ""
        if knowledge_path.exists():
            knowledge = knowledge_path.read_text(encoding="utf-8")

        temperature = self._parse_temperature(prompt, reviewer_id)

        if diff_files is not None:
            relevant = self._check_relevance(reviewer_id, diff_files)
        else:
            relevant = True

        return ReviewerConfig(
            id=reviewer_id,
            prompt=prompt,
            knowledge=knowledge,
            temperature=temperature,
            relevant=relevant,
        )

    def _parse_temperature(self, prompt_content: str, reviewer_id: str) -> float:
        """
        Extract temperature value from PROMPT.md content.

        Looks for a ## Temperature section with a float value.
        Falls back to DEFAULT_TEMPERATURES if not found.
        """
        match = re.search(
            r"##\s+Temperature\s*\n+\s*([\d.]+)",
            prompt_content,
        )
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return DEFAULT_TEMPERATURES.get(reviewer_id, 0.5)

    def _check_relevance(self, reviewer_id: str, diff_files: list[str]) -> bool:
        """
        Check if a reviewer's domain is relevant to the changed files.

        Args:
            reviewer_id: The reviewer to check.
            diff_files: List of changed file paths.

        Returns:
            True if the reviewer should review these files.
        """
        if not diff_files:
            return True

        extensions = DOMAIN_EXTENSIONS.get(reviewer_id, set())

        if "*" in extensions:
            return True

        for file_path in diff_files:
            suffix = Path(file_path).suffix.lower()
            if suffix in extensions:
                return True

        return False
