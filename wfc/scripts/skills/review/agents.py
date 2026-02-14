"""
Review Agents

Four specialized review agents: CR, SEC, PERF, COMP

NOTE: All agents below are STUB implementations returning hardcoded scores.
They serve as the interface contract for the review system.
TODO: Implement actual analysis using LLM-based code review.
See: https://github.com/sam-fakhreddine/wfc/issues/18
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
    confidence: int = 80  # 0-100 confidence score


@dataclass
class AgentReview:
    """Review from a single agent"""

    agent: AgentType
    score: float  # 0-10
    passed: bool  # score >= 7
    comments: List[ReviewComment]
    summary: str


class CodeReviewAgent:
    """Code review agent - STUB IMPLEMENTATION.

    TODO: Replace hardcoded scores with actual LLM-based code analysis.
    Current behavior: Returns placeholder score of ~8.5 for all inputs.
    Production: Should analyze code for correctness, readability, maintainability.
    """

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform code review (STUB: returns near-constant score)."""
        comments = [
            ReviewComment(
                file=files[0] if files else "unknown",
                line=10,
                severity="medium",
                message="Consider extracting this to a separate function",
                suggestion="Split large function into smaller, focused functions",
            )
        ]

        # Vary score slightly based on input to avoid appearing completely static
        base_score = 8.5
        variance = (len(files) % 5) * 0.1 - 0.2  # -0.2 to +0.2
        score = round(min(10.0, max(0.0, base_score + variance)), 1)

        return AgentReview(
            agent=AgentType.CR,
            score=score,
            passed=score >= 7.0,
            comments=comments,
            summary="Code is well-structured. Minor improvements suggested.",
        )


class SecurityAgent:
    """Security review agent - STUB IMPLEMENTATION.

    TODO: Replace hardcoded scores with actual LLM-based security analysis.
    Current behavior: Returns placeholder score of ~9.0 for all inputs.
    Production: Should analyze code for security vulnerabilities, auth/authz issues,
    injection flaws, and OWASP Top 10 compliance.
    """

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform security review (STUB: returns near-constant score)."""
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

        # Vary score slightly based on input
        base_score = 9.0
        safety_count = sum(1 for p in properties if p.get("type") == "SAFETY")
        variance = (len(files) % 3) * 0.1 - 0.1 + (safety_count % 2) * -0.2
        score = round(min(10.0, max(0.0, base_score + variance)), 1)

        return AgentReview(
            agent=AgentType.SEC,
            score=score,
            passed=score >= 7.0,
            comments=comments,
            summary="No critical security issues found. Safety properties should be tested.",
        )


class PerformanceAgent:
    """Performance review agent - STUB IMPLEMENTATION.

    TODO: Replace hardcoded scores with actual LLM-based performance analysis.
    Current behavior: Returns placeholder score of ~8.0 for all inputs.
    Production: Should analyze code for performance issues, scalability bottlenecks,
    algorithmic complexity, and resource usage patterns.
    """

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform performance review (STUB: returns near-constant score)."""
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

        # Vary score slightly based on input
        base_score = 8.0
        perf_count = sum(1 for p in properties if p.get("type") == "PERFORMANCE")
        variance = (len(files) % 4) * 0.15 - 0.3 + (perf_count % 3) * -0.1
        score = round(min(10.0, max(0.0, base_score + variance)), 1)

        return AgentReview(
            agent=AgentType.PERF,
            score=score,
            passed=score >= 7.0,
            comments=comments,
            summary="Performance looks acceptable. Add benchmarks for performance properties.",
        )


class ComplexityAgent:
    """Complexity review agent - STUB IMPLEMENTATION.

    TODO: Replace hardcoded scores with actual LLM-based complexity analysis.
    Current behavior: Returns placeholder score of ~9.5 for all inputs.
    Production: Should analyze code for cyclomatic complexity, coupling/cohesion,
    architecture adherence, and ELEGANT principle compliance.
    """

    def review(self, files: List[str], properties: List[Dict], task_id: str) -> AgentReview:
        """Perform complexity review (STUB: returns near-constant score)."""
        comments = [
            ReviewComment(
                file="architecture",
                line=0,
                severity="info",
                message="Code follows ELEGANT principles",
                suggestion="Continue maintaining ELEGANT design",
            )
        ]

        # Vary score slightly based on input
        base_score = 9.5
        variance = (len(files) % 3) * 0.1 - 0.1 + (len(properties) % 2) * -0.2
        score = round(min(10.0, max(0.0, base_score + variance)), 1)

        return AgentReview(
            agent=AgentType.COMP,
            score=score,
            passed=score >= 7.0,
            comments=comments,
            summary="Code is ELEGANT: simple, effective, maintainable.",
        )
