"""
WFC Vibe - Context Summarization

SOLID: Single Responsibility - Extract relevant planning context from conversations
"""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Message:
    """Simple message structure"""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class PlanningContext:
    """Structured planning context extracted from conversation"""

    goal: str
    features: List[str]
    constraints: List[str]
    tech_stack: List[str]
    files_mentioned: List[str]
    estimated_complexity: str  # S, M, L, XL
    scope_size: int  # Number of features


class ContextSummarizer:
    """
    Extracts relevant planning information from vibe conversation.

    Philosophy (PROP-005):
    - Include: goal, features, constraints, tech stack
    - Exclude: jokes, off-topic chat, meta-discussion
    - Fast: <5 seconds (PROP-007)
    """

    def __init__(self):
        self.tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "django",
            "flask",
            "fastapi",
            "postgresql",
            "mysql",
            "redis",
            "mongodb",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "jwt",
            "oauth",
            "graphql",
            "rest",
            "grpc",
        ]

        self.constraint_keywords = [
            "performance",
            "security",
            "scalability",
            "reliability",
            "compatibility",
            "backward compatible",
            "migration",
            "deadline",
            "budget",
            "team size",
        ]

    def summarize(
        self, messages: List[Message], scope_detector: Optional[Any] = None
    ) -> PlanningContext:
        """
        Extract planning context from conversation.

        Args:
            messages: Conversation history
            scope_detector: Optional ScopeDetector with analysis

        Returns:
            PlanningContext with structured summary

        Performance: Must complete in <5 seconds (PROP-007)
        """
        # Extract goal (first meaningful user message)
        goal = self._extract_goal(messages)

        # Extract features from user messages
        features = self._extract_features(messages, scope_detector)

        # Extract constraints
        constraints = self._extract_constraints(messages)

        # Extract tech stack mentions
        tech_stack = self._extract_tech_stack(messages)

        # Extract file mentions
        files = self._extract_files(messages, scope_detector)

        # Estimate complexity based on scope
        complexity = self._estimate_complexity(len(features), len(files))

        return PlanningContext(
            goal=goal,
            features=features,
            constraints=constraints,
            tech_stack=tech_stack,
            files_mentioned=files,
            estimated_complexity=complexity,
            scope_size=len(features),
        )

    def _extract_goal(self, messages: List[Message]) -> str:
        """
        Extract primary goal from conversation.

        Strategy: Look for first substantial user message about building something
        """
        goal_keywords = ["build", "create", "make", "develop", "implement", "add", "want"]

        for msg in messages:
            if msg.role != "user":
                continue

            msg_lower = msg.content.lower()

            # Look for goal indicators
            if any(keyword in msg_lower for keyword in goal_keywords):
                # This is likely the goal statement
                # Clean it up (remove filler words)
                return self._clean_goal(msg.content)

        # Fallback: first user message
        for msg in messages:
            if msg.role == "user" and len(msg.content) > 20:
                return self._clean_goal(msg.content)

        return "Feature implementation"

    def _clean_goal(self, text: str) -> str:
        """Clean up goal statement (remove filler, keep essence)"""
        # Remove common filler phrases
        fillers = [
            "I want to",
            "I'd like to",
            "We need to",
            "Can you help me",
            "I'm thinking about",
            "I was wondering if",
        ]

        cleaned = text
        for filler in fillers:
            cleaned = cleaned.replace(filler, "").strip()

        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned[:200]  # Limit length

    def _extract_features(
        self, messages: List[Message], scope_detector: Optional[Any]
    ) -> List[str]:
        """
        Extract feature list from conversation.

        Strategy: Use scope detector if available, otherwise extract from messages
        """
        features = set()

        # If scope detector provided, use its analysis
        if scope_detector:
            features.update(scope_detector.features_mentioned)

        # Also extract from messages directly
        feature_keywords = [
            "authentication",
            "auth",
            "authorization",
            "login",
            "logging",
            "audit",
            "monitoring",
            "email",
            "notification",
            "alert",
            "rbac",
            "role",
            "permission",
            "access",
            "dashboard",
            "admin",
            "panel",
            "api",
            "endpoint",
            "rest",
            "graphql",
            "database",
            "storage",
            "cache",
            "redis",
            "search",
            "filter",
            "sort",
            "pagination",
        ]

        for msg in messages:
            if msg.role != "user":
                continue

            msg_lower = msg.content.lower()
            for keyword in feature_keywords:
                if keyword in msg_lower:
                    features.add(keyword)

        return list(features)[:10]  # Limit to top 10

    def _extract_constraints(self, messages: List[Message]) -> List[str]:
        """Extract technical/business constraints"""
        constraints = set()

        for msg in messages:
            if msg.role != "user":
                continue

            msg_lower = msg.content.lower()

            for keyword in self.constraint_keywords:
                if keyword in msg_lower:
                    constraints.add(keyword)

            # Also look for explicit constraint statements
            if "must" in msg_lower or "required" in msg_lower or "need" in msg_lower:
                # This message likely contains constraints
                # Extract key phrases (simplified)
                if "performance" in msg_lower:
                    constraints.add("performance requirements")
                if "security" in msg_lower or "secure" in msg_lower:
                    constraints.add("security requirements")
                if "compatible" in msg_lower:
                    constraints.add("compatibility requirements")

        return list(constraints)[:5]  # Limit to top 5

    def _extract_tech_stack(self, messages: List[Message]) -> List[str]:
        """Extract technology stack mentions"""
        tech = set()

        for msg in messages:
            msg_lower = msg.content.lower()

            for keyword in self.tech_keywords:
                if keyword in msg_lower:
                    tech.add(keyword)

        return list(tech)[:8]  # Limit to top 8

    def _extract_files(self, messages: List[Message], scope_detector: Optional[Any]) -> List[str]:
        """Extract file/module mentions"""
        files = set()

        # Use scope detector if available
        if scope_detector:
            files.update(scope_detector.files_mentioned)

        return list(files)[:10]  # Limit to top 10

    def _estimate_complexity(self, feature_count: int, file_count: int) -> str:
        """
        Estimate complexity based on scope.

        Heuristics:
        - S: 1-2 features, 0-1 files
        - M: 3-5 features, 2-5 files
        - L: 6-10 features, 6-10 files
        - XL: >10 features or >10 files
        """
        if feature_count > 10 or file_count > 10:
            return "XL"
        elif feature_count > 5 or file_count > 5:
            return "L"
        elif feature_count > 2 or file_count > 1:
            return "M"
        else:
            return "S"

    def should_route_to_plan(self, context: PlanningContext) -> bool:
        """
        Determine if should route to wfc-plan (complex) or wfc-build (simple).

        Logic:
        - wfc-build: S/M complexity (1-5 features)
        - wfc-plan: L/XL complexity (>5 features)
        """
        return context.estimated_complexity in ["L", "XL"] or context.scope_size > 5

    def format_preview(self, context: PlanningContext) -> str:
        """
        Format context summary for user preview.

        Returns human-readable summary before transition
        """
        preview = "📋 I'll help you plan this. Here's what I captured:\n\n"
        preview += f"**Goal:** {context.goal}\n\n"

        if context.features:
            preview += f"**Features:** {', '.join(context.features)}\n\n"

        if context.tech_stack:
            preview += f"**Tech Stack:** {', '.join(context.tech_stack)}\n\n"

        if context.constraints:
            preview += f"**Constraints:** {', '.join(context.constraints)}\n\n"

        preview += f"**Estimated Complexity:** {context.estimated_complexity}"

        if context.scope_size > 5:
            preview += " (recommend wfc-plan)"
        else:
            preview += " (recommend wfc-build)"

        return preview
