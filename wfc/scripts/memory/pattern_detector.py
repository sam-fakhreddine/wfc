"""
WFC Pattern Detector - SEE SOMETHING SAY SOMETHING

SOLID: Single Responsibility - Only detects and tracks patterns
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from .schemas import OperationalPattern, ReflexionEntry


class PatternDetector:
    """
    Detects recurring operational patterns.

    Single Responsibility: Pattern detection and tracking
    """

    # Known pattern signatures (built-in knowledge)
    KNOWN_PATTERNS = {
        "docker-compose-version": {
            "signature": "version:",
            "context": ["docker-compose.yml", "docker-compose.yaml"],
            "error_type": "Docker Compose version field obsolete",
            "description": "Using deprecated 'version:' field in docker-compose.yml",
            "fix": "Remove 'version:' field from docker-compose files (obsolete since v1.27.0 in 2020)",
            "impact": "Generates warnings, uses outdated syntax",
            "severity": "low",
        },
        "pytest-no-verbose": {
            "signature": "pytest tests/",
            "exclude": ["-v", "--verbose"],
            "context": ["bash", "command"],
            "error_type": "pytest run without verbose flag",
            "description": "Running pytest without -v flag makes debugging harder",
            "fix": "Always use 'uv run pytest -v' instead of 'uv run pytest'",
            "impact": "Harder to debug test failures",
            "severity": "low",
        },
    }

    def __init__(self, patterns_file: Path, threshold: int = 3):
        """
        Initialize pattern detector.

        Args:
            patterns_file: Path to operational_patterns.jsonl
            threshold: Minimum occurrences to create pattern
        """
        self.patterns_file = patterns_file
        self.threshold = threshold

    def scan_content(self, content: str, context: str = "") -> List[str]:
        """
        Scan content for known pattern signatures.

        Args:
            content: Content to scan (command, file content, etc.)
            context: Context (filename, command type, etc.)

        Returns:
            List of detected pattern IDs
        """
        detected = []

        for pattern_id, pattern_def in self.KNOWN_PATTERNS.items():
            signature = pattern_def["signature"]
            pattern_context = pattern_def.get("context", [])
            exclude = pattern_def.get("exclude", [])

            # Check if context matches
            context_match = not pattern_context or any(ctx in context for ctx in pattern_context)

            if not context_match:
                continue

            # Check if signature present
            if signature in content:
                # Check excludes
                excluded = any(exc in content for exc in exclude)

                if not excluded:
                    detected.append(pattern_id)

        return detected

    def detect_from_reflexion(self, common_patterns: List[dict]) -> List[OperationalPattern]:
        """
        Detect operational patterns from reflexion entries.

        Args:
            common_patterns: List of common failure patterns with counts

        Returns:
            List of detected operational patterns
        """
        detected_patterns = []
        pattern_counter = 1

        for pattern_data in common_patterns:
            count = pattern_data["count"]

            # Only create pattern if threshold met
            if count >= self.threshold:
                example = ReflexionEntry.from_dict(pattern_data["example"])

                pattern = OperationalPattern(
                    pattern_id=f"PATTERN-{pattern_counter:03d}",
                    first_detected=example.timestamp,
                    last_detected=datetime.now().isoformat(),
                    occurrence_count=count,
                    error_type=pattern_data["pattern"],
                    description=example.mistake,
                    fix=example.fix,
                    impact=f"Occurred {count} times - prevents systematic improvement",
                    status="READY_FOR_PLAN",
                    severity=example.severity,
                )

                detected_patterns.append(pattern)
                pattern_counter += 1

        return detected_patterns

    def save_pattern(self, pattern: OperationalPattern) -> None:
        """
        Save a pattern to file.

        Args:
            pattern: OperationalPattern to save
        """
        with open(self.patterns_file, "a") as f:
            f.write(json.dumps(pattern.to_dict()) + "\n")

    def get_all_patterns(self) -> List[OperationalPattern]:
        """
        Get all saved patterns.

        Returns:
            List of all operational patterns
        """
        if not self.patterns_file.exists():
            return []

        patterns = []
        with open(self.patterns_file, "r") as f:
            for line in f:
                try:
                    pattern_data = json.loads(line.strip())
                    pattern = OperationalPattern.from_dict(pattern_data)
                    patterns.append(pattern)
                except (json.JSONDecodeError, Exception):
                    continue

        return patterns

    def get_pattern_definition(self, pattern_id: str) -> Dict[str, Any]:
        """
        Get pattern definition by ID.

        Args:
            pattern_id: Known pattern ID

        Returns:
            Pattern definition dict
        """
        return self.KNOWN_PATTERNS.get(pattern_id, {})
