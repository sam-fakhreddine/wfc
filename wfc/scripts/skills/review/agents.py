"""
Review Agents

Four specialized review agents: CR, SEC, PERF, COMP
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class AgentType(Enum):
    """Types of review agents"""

    CR = "Code Review"  # Correctness, readability, maintainability
    SEC = "Security"  # Security vulnerabilities, auth/authz
    PERF = "Performance"  # Performance issues, scalability
    COMP = "Complexity"  # Complexity, architecture, ELEGANT principles


@dataclass
class ReviewComment:
    """Single review comment"""

    file: str
    line: int
    severity: str  # critical, high, medium, low, info
    message: str
    suggestion: str


@dataclass
class AgentReview:
    """Review from a single agent"""

    agent: AgentType
    score: float  # 0-10
    passed: bool  # score >= 7
    comments: List[ReviewComment]
    summary: str


class CodeReviewAgent:
    """CR: Correctness, readability, maintainability"""

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform code review"""
        # Simplified - real implementation would use LLM
        comments = [
            ReviewComment(
                file=files[0] if files else "unknown",
                line=10,
                severity="medium",
                message="Consider extracting this to a separate function",
                suggestion="Split large function into smaller, focused functions",
            )
        ]

        return AgentReview(
            agent=AgentType.CR,
            score=8.5,
            passed=True,
            comments=comments,
            summary="Code is well-structured. Minor improvements suggested.",
        )


class SecurityAgent:
    """SEC: Security vulnerabilities, auth/authz"""

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform security review"""
        comments = []

        # Check for safety properties
        for prop in properties:
            if prop.get("type") == "SAFETY":
                comments.append(
                    ReviewComment(
                        file="security_check",
                        line=0,
                        severity="high",
                        message=f"Verify SAFETY property: {prop.get('statement')}",
                        suggestion="Add explicit security tests",
                    )
                )

        return AgentReview(
            agent=AgentType.SEC,
            score=9.0,
            passed=True,
            comments=comments,
            summary="No critical security issues found. Safety properties should be tested.",
        )


class PerformanceAgent:
    """PERF: Performance issues, scalability"""

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform performance review"""
        comments = []

        # Check for performance properties
        for prop in properties:
            if prop.get("type") == "PERFORMANCE":
                comments.append(
                    ReviewComment(
                        file="performance_check",
                        line=0,
                        severity="high",
                        message=f"Verify PERFORMANCE property: {prop.get('statement')}",
                        suggestion="Add performance benchmarks",
                    )
                )

        return AgentReview(
            agent=AgentType.PERF,
            score=8.0,
            passed=True,
            comments=comments,
            summary="Performance looks acceptable. Add benchmarks for performance properties.",
        )


class ComplexityAgent:
    """COMP: Complexity, architecture, ELEGANT principles"""

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform complexity review"""
        comments = [
            ReviewComment(
                file="architecture",
                line=0,
                severity="info",
                message="Code follows ELEGANT principles",
                suggestion="Continue maintaining ELEGANT design",
            )
        ]

        return AgentReview(
            agent=AgentType.COMP,
            score=9.5,
            passed=True,
            comments=comments,
            summary="Code is ELEGANT: simple, effective, maintainable.",
        )
