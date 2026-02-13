"""
Consensus Algorithm

Combines reviews from agents into consensus decision.
Supports both fixed 4-agent mode and variable persona mode.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import sys

# Handle both relative imports (when used as package) and standalone execution
try:
    from .agents import AgentReview, ReviewComment
except ImportError:
    # Standalone execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from agents import AgentReview, ReviewComment


@dataclass
class ConsensusResult:
    """Result of consensus algorithm"""

    overall_score: float
    passed: bool  # True if consensus is to accept
    agent_reviews: Dict[str, AgentReview]
    all_comments: List[ReviewComment]
    summary: str
    consensus_areas: Optional[List[str]] = None  # Issues mentioned by 3+ reviewers
    unique_insights: Optional[List[str]] = None  # Issues only 1 reviewer caught
    divergent_views: Optional[List[str]] = None  # Disagreement areas
    filtered_count: int = 0  # Comments filtered by confidence

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "agent_reviews": {
                agent_type: {
                    "agent": review.agent.value,
                    "score": review.score,
                    "passed": review.passed,
                    "summary": review.summary,
                    "comment_count": len(review.comments),
                }
                for agent_type, review in self.agent_reviews.items()
            },
            "total_comments": len(self.all_comments),
            "summary": self.summary,
        }

        result["filtered_count"] = self.filtered_count

        if self.consensus_areas:
            result["consensus_areas"] = self.consensus_areas
        if self.unique_insights:
            result["unique_insights"] = self.unique_insights
        if self.divergent_views:
            result["divergent_views"] = self.divergent_views

        return result


class ConsensusAlgorithm:
    """
    Consensus algorithm for multi-agent review.

    Supports two modes:
    1. Fixed weights (legacy 4-agent mode)
    2. Relevance-based weights (persona mode)

    Rules:
    - All agents must pass (score >= 7)
    - Overall score = weighted average
    - Any critical severity comment = fail
    - Tie-breaker: majority vote
    """

    # Agent weights for legacy mode (sum = 1.0)
    WEIGHTS = {
        "CR": 0.3,  # Code review: 30%
        "SEC": 0.35,  # Security: 35% (highest priority)
        "PERF": 0.20,  # Performance: 20%
        "COMP": 0.15,  # Complexity: 15%
    }

    def calculate(
        self,
        reviews: List[AgentReview],
        relevance_scores: Optional[Dict[str, float]] = None,
        weight_by_relevance: bool = False,
        confidence_threshold: int = 80,
    ) -> ConsensusResult:
        """
        Calculate consensus from agent reviews.

        Args:
            reviews: List of agent reviews
            relevance_scores: Optional dict of agent_id -> relevance score
            weight_by_relevance: If True, use relevance scores for weighting

        Returns:
            ConsensusResult with overall decision
        """

        # Organize by agent type
        agent_reviews = {review.agent.name: review for review in reviews}

        # Calculate weighted score
        if weight_by_relevance and relevance_scores:
            overall_score = self._calculate_relevance_weighted_score(reviews, relevance_scores)
        else:
            overall_score = self._calculate_fixed_weighted_score(reviews)

        # Collect all comments with confidence filtering
        all_comments_unfiltered = []
        for review in reviews:
            all_comments_unfiltered.extend(review.comments)

        # Filter by confidence (critical severity bypasses filter)
        all_comments = [
            c
            for c in all_comments_unfiltered
            if c.confidence >= confidence_threshold or c.severity == "critical"
        ]
        filtered_count = len(all_comments_unfiltered) - len(all_comments)

        # Check for critical issues
        has_critical = any(comment.severity == "critical" for comment in all_comments)

        # Determine if passed
        all_agents_passed = all(review.passed for review in reviews)
        passed = all_agents_passed and not has_critical and overall_score >= 7.0

        # Generate summary
        summary = self._generate_summary(reviews, overall_score, passed, has_critical)

        # Detect consensus patterns (for persona mode)
        consensus_areas = None
        unique_insights = None
        divergent_views = None

        if len(reviews) > 4:  # Only for persona mode
            consensus_areas = self._find_consensus_areas(all_comments, len(reviews))
            unique_insights = self._find_unique_insights(all_comments)
            divergent_views = self._find_divergent_views(reviews)

        return ConsensusResult(
            overall_score=overall_score,
            passed=passed,
            agent_reviews=agent_reviews,
            all_comments=all_comments,
            summary=summary,
            consensus_areas=consensus_areas,
            unique_insights=unique_insights,
            divergent_views=divergent_views,
            filtered_count=filtered_count,
        )

    def _calculate_fixed_weighted_score(self, reviews: List[AgentReview]) -> float:
        """Calculate score using fixed weights (legacy mode)"""
        return sum(review.score * self.WEIGHTS.get(review.agent.name, 0.25) for review in reviews)

    def _calculate_relevance_weighted_score(
        self, reviews: List[AgentReview], relevance_scores: Dict[str, float]
    ) -> float:
        """Calculate score using relevance-based weights"""
        # Normalize relevance scores to sum to 1.0
        total_relevance = sum(relevance_scores.values())
        if total_relevance == 0:
            return self._calculate_fixed_weighted_score(reviews)

        weighted_sum = 0.0
        for review in reviews:
            relevance = relevance_scores.get(review.agent.name, 0.0)
            weight = relevance / total_relevance
            weighted_sum += review.score * weight

        return weighted_sum

    def _find_consensus_areas(self, comments: List[ReviewComment], num_reviewers: int) -> List[str]:
        """Find issues mentioned by 3+ reviewers"""
        # Group comments by message similarity (simplified)
        message_counts = defaultdict(int)
        for comment in comments:
            # Use first 50 chars as key for grouping
            key = comment.message[:50]
            message_counts[key] += 1

        # Find consensus (mentioned by at least 3 reviewers or half, whichever is smaller)
        threshold = min(3, num_reviewers // 2)
        consensus = [msg for msg, count in message_counts.items() if count >= threshold]

        return consensus if consensus else None

    def _find_unique_insights(self, comments: List[ReviewComment]) -> List[str]:
        """Find issues mentioned by only 1 reviewer"""
        # Group comments by message
        message_counts = defaultdict(int)
        message_examples = {}

        for comment in comments:
            key = comment.message[:50]
            message_counts[key] += 1
            if key not in message_examples:
                message_examples[key] = comment  # Store comment object, not just message

        # Find unique (mentioned only once)
        unique = [
            message_examples[msg].message
            for msg, count in message_counts.items()
            if count == 1 and message_examples[msg].severity in ["high", "critical"]
        ]

        return unique[:5] if unique else None  # Limit to top 5

    def _find_divergent_views(self, reviews: List[AgentReview]) -> List[str]:
        """Find areas where reviewers significantly disagree"""
        divergent = []

        # Check score variance
        scores = [r.score for r in reviews]
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

            if variance > 4.0:  # High variance (std dev > 2.0)
                divergent.append(
                    f"Reviewers disagree on overall quality (scores range: {min(scores):.1f}-{max(scores):.1f})"
                )

        return divergent if divergent else None

    def _generate_summary(
        self, reviews: List[AgentReview], score: float, passed: bool, has_critical: bool
    ) -> str:
        """Generate consensus summary"""
        if has_critical:
            return "❌ REJECTED: Critical issues found"

        if not passed:
            failing = [r.agent.name for r in reviews if not r.passed]
            return f"❌ REJECTED: Failed agents: {', '.join(failing)}"

        if score >= 9.0:
            return "✅ APPROVED: Excellent quality"
        elif score >= 8.0:
            return "✅ APPROVED: Good quality with minor suggestions"
        else:
            return "✅ APPROVED: Acceptable quality"
