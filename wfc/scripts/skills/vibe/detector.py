"""
WFC Vibe - Scope Detection

SOLID: Single Responsibility - Detects when scope is growing large
"""

from typing import List, Dict, Any
import re


class ScopeDetector:
    """
    Detects when feature scope is growing large enough to warrant planning.

    Philosophy:
    - Not annoying (low false positive rate)
    - One suggestion max per conversation
    - Multiple detection heuristics
    """

    # Detection thresholds
    FEATURE_THRESHOLD = 3  # >3 distinct features
    FILE_THRESHOLD = 5     # >5 file/module mentions
    ARCHITECTURE_KEYWORD_THRESHOLD = 2  # >2 architecture keywords

    # Keywords for detection
    ARCHITECTURE_KEYWORDS = [
        "architecture", "architect", "integrate", "integration",
        "system", "distributed", "microservice", "service",
        "api", "endpoint", "database", "schema"
    ]

    COMPLEXITY_INDICATORS = [
        "refactor", "refactoring", "migrate", "migration",
        "rewrite", "redesign", "restructure", "overhaul"
    ]

    def __init__(self):
        self.features_mentioned = set()
        self.files_mentioned = set()
        self.architecture_keyword_count = 0
        self.complexity_indicator_count = 0

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Analyze a message for scope indicators.

        Returns:
            Dict with detection results
        """
        message_lower = message.lower()

        # Detect features (look for "add", "need", "want" + noun)
        features = self._extract_features(message)
        self.features_mentioned.update(features)

        # Detect file mentions (look for .py, .js, etc or "file" keyword)
        files = self._extract_file_mentions(message)
        self.files_mentioned.update(files)

        # Count architecture keywords
        arch_keywords_found = sum(
            1 for keyword in self.ARCHITECTURE_KEYWORDS
            if keyword in message_lower
        )
        self.architecture_keyword_count += arch_keywords_found

        # Count complexity indicators
        complexity_found = sum(
            1 for indicator in self.COMPLEXITY_INDICATORS
            if indicator in message_lower
        )
        self.complexity_indicator_count += complexity_found

        return {
            "features_count": len(self.features_mentioned),
            "files_count": len(self.files_mentioned),
            "architecture_keywords": self.architecture_keyword_count,
            "complexity_indicators": self.complexity_indicator_count,
            "scope_growing": self.is_scope_growing_large()
        }

    def _extract_features(self, message: str) -> List[str]:
        """
        Extract potential features from message.

        Heuristic: Look for common feature keywords and patterns
        """
        features = []
        message_lower = message.lower()

        # Common feature keywords (direct mentions)
        feature_keywords = [
            "authentication", "auth", "authorization",
            "logging", "log", "audit",
            "email", "notification", "notif",
            "rbac", "role", "permission", "access control",
            "dashboard", "admin", "panel",
            "api", "endpoint", "rest",
            "database", "storage", "cache",
            "search", "filter", "sort"
        ]

        # Check for feature keywords
        for keyword in feature_keywords:
            if keyword in message_lower:
                features.append(keyword)

        # Also extract explicit feature patterns
        patterns = [
            r"(?:add|need|want|build|create|implement)\s+(\w+(?:\s+\w+){0,2})",
            r"(\w+(?:\s+\w+){0,2})\s+(?:feature|functionality|capability)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message_lower)
            features.extend(matches)

        return features

    def _extract_file_mentions(self, message: str) -> List[str]:
        """
        Extract file/module mentions from message.

        Patterns:
        - file.ext (any extension)
        - "file" keyword followed by name
        - module.submodule patterns
        """
        files = []

        # Pattern 1: file.ext
        file_pattern = r'\b(\w+\.\w+)\b'
        files.extend(re.findall(file_pattern, message))

        # Pattern 2: explicit "file" mentions
        file_keyword_pattern = r'file\s+(\w+)'
        files.extend(re.findall(file_keyword_pattern, message.lower()))

        # Pattern 3: module paths (foo.bar.baz)
        module_pattern = r'\b(\w+\.\w+\.\w+)\b'
        files.extend(re.findall(module_pattern, message))

        return files

    def is_scope_growing_large(self) -> bool:
        """
        Determine if scope has grown large enough to suggest planning.

        Returns True if ANY of these conditions met:
        - >3 distinct features mentioned
        - >5 files mentioned
        - >2 architecture keywords
        - >2 complexity indicators
        """
        return (
            len(self.features_mentioned) > self.FEATURE_THRESHOLD or
            len(self.files_mentioned) > self.FILE_THRESHOLD or
            self.architecture_keyword_count > self.ARCHITECTURE_KEYWORD_THRESHOLD or
            self.complexity_indicator_count > 1
        )

    def get_scope_summary(self) -> Dict[str, Any]:
        """Get current scope analysis summary"""
        return {
            "features": list(self.features_mentioned),
            "files": list(self.files_mentioned),
            "architecture_keywords": self.architecture_keyword_count,
            "complexity_indicators": self.complexity_indicator_count,
            "scope_growing": self.is_scope_growing_large()
        }
