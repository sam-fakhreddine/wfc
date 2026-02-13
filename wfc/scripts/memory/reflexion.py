"""
WFC Reflexion Logger - Error Learning

SOLID: Single Responsibility - Only handles reflexion entries
"""

import json
from pathlib import Path
from typing import List
from .schemas import ReflexionEntry


class ReflexionLogger:
    """
    Logs and searches reflexion entries (errors and fixes).

    Single Responsibility: Reflexion entry management
    """

    def __init__(self, reflexion_file: Path):
        """
        Initialize reflexion logger.

        Args:
            reflexion_file: Path to reflexion.jsonl
        """
        self.reflexion_file = reflexion_file

    def log(self, entry: ReflexionEntry) -> None:
        """
        Log a reflexion entry.

        Args:
            entry: ReflexionEntry to log
        """
        with open(self.reflexion_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def search_similar(self, task_description: str, max_results: int = 5) -> List[ReflexionEntry]:
        """
        Search for similar past errors.

        Args:
            task_description: Description of current task
            max_results: Maximum number of results

        Returns:
            List of similar ReflexionEntries
        """
        if not self.reflexion_file.exists():
            return []

        keywords = self._extract_keywords(task_description)
        matches = []

        with open(self.reflexion_file, "r") as f:
            for line in f:
                try:
                    entry_data = json.loads(line.strip())
                    entry = ReflexionEntry.from_dict(entry_data)

                    mistake_lower = entry.mistake.lower()
                    fix_lower = entry.fix.lower()

                    if any(kw in mistake_lower or kw in fix_lower for kw in keywords):
                        matches.append(entry)

                except (json.JSONDecodeError, Exception):
                    continue

        return matches[-max_results:]

    def get_common_patterns(self, limit: int = 10) -> List[dict]:
        """
        Get most common failure patterns.

        Args:
            limit: Maximum number of patterns

        Returns:
            List of pattern dicts with count
        """
        if not self.reflexion_file.exists():
            return []

        pattern_counts = {}
        pattern_examples = {}

        with open(self.reflexion_file, "r") as f:
            for line in f:
                try:
                    entry_data = json.loads(line.strip())
                    entry = ReflexionEntry.from_dict(entry_data)

                    rule = entry.rule

                    if rule not in pattern_counts:
                        pattern_counts[rule] = 0
                        pattern_examples[rule] = entry

                    pattern_counts[rule] += 1

                except (json.JSONDecodeError, Exception):
                    continue

        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {"pattern": rule, "count": count, "example": pattern_examples[rule].to_dict()}
            for rule, count in sorted_patterns
        ]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for matching."""
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in common_words]

        return keywords[:10]
