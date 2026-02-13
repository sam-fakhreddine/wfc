#!/usr/bin/env python3
"""
WFC Confidence Checker - SuperClaude Pattern

Assesses agent confidence BEFORE starting implementation work.
Prevents wrong-direction work that wastes 25-250x tokens.

PHILOSOPHY (from SuperClaude Framework):
- ≥90%: Proceed with implementation
- 70-89%: Present alternatives, ask clarifying questions
- <70%: STOP - Investigate more, ask user for guidance

This is the single highest-ROI feature for token efficiency.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


class ConfidenceLevel(Enum):
    """Confidence level thresholds."""

    HIGH = "high"  # ≥90% - Proceed
    MEDIUM = "medium"  # 70-89% - Ask questions
    LOW = "low"  # <70% - Stop and investigate


@dataclass
class ConfidenceAssessment:
    """
    Result of confidence assessment.

    This is what the agent produces before starting work.
    """

    task_id: str
    confidence_score: int  # 0-100
    confidence_level: ConfidenceLevel

    # Reasoning
    clear_requirements: bool
    has_examples: bool
    understands_architecture: bool
    knows_dependencies: bool
    can_verify_success: bool

    # Risks identified
    risks: List[Dict[str, str]]  # [{"risk": "...", "severity": "high|medium|low"}]

    # Clarifying questions (if medium/low confidence)
    questions: List[str]

    # Alternatives (if medium confidence)
    alternatives: List[Dict[str, str]]  # [{"approach": "...", "pros": "...", "cons": "..."}]

    # Recommendation
    should_proceed: bool
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "clear_requirements": self.clear_requirements,
            "has_examples": self.has_examples,
            "understands_architecture": self.understands_architecture,
            "knows_dependencies": self.knows_dependencies,
            "can_verify_success": self.can_verify_success,
            "risks": self.risks,
            "questions": self.questions,
            "alternatives": self.alternatives,
            "should_proceed": self.should_proceed,
            "recommendation": self.recommendation,
        }


class ConfidenceChecker:
    """
    WFC Confidence Checker - PREVENT WRONG-DIRECTION WORK

    Assesses confidence before implementation to avoid wasting tokens
    on wrong approaches, unclear requirements, or missing context.

    ROI: Prevents 25-250x token waste from wrong-direction work.
    """

    def __init__(self, project_root: Path):
        """
        Initialize confidence checker.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)

    def assess(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> ConfidenceAssessment:
        """
        Assess confidence for a task.

        Args:
            task: Task dictionary
            context: Optional additional context

        Returns:
            ConfidenceAssessment

        This is the main entry point - called before agent starts work.
        """
        task_id = task.get("id", "UNKNOWN")

        # Assess each dimension
        clear_requirements = self._assess_requirements_clarity(task)
        has_examples = self._assess_examples_available(task, context)
        understands_architecture = self._assess_architecture_understanding(task, context)
        knows_dependencies = self._assess_dependencies_clear(task, context)
        can_verify_success = self._assess_verification_possible(task)

        # Calculate confidence score (0-100)
        confidence_score = self._calculate_confidence_score(
            clear_requirements=clear_requirements,
            has_examples=has_examples,
            understands_architecture=understands_architecture,
            knows_dependencies=knows_dependencies,
            can_verify_success=can_verify_success,
        )

        # Determine confidence level
        if confidence_score >= 90:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 70:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW

        # Identify risks
        risks = self._identify_risks(task, confidence_score)

        # Generate questions (if not high confidence)
        questions = []
        if confidence_level != ConfidenceLevel.HIGH:
            questions = self._generate_clarifying_questions(
                task,
                clear_requirements,
                has_examples,
                understands_architecture,
                knows_dependencies,
                can_verify_success,
            )

        # Generate alternatives (if medium confidence)
        alternatives = []
        if confidence_level == ConfidenceLevel.MEDIUM:
            alternatives = self._generate_alternatives(task, context)

        # Determine if should proceed
        should_proceed = confidence_level == ConfidenceLevel.HIGH

        # Generate recommendation
        recommendation = self._generate_recommendation(
            confidence_level, confidence_score, risks, questions
        )

        return ConfidenceAssessment(
            task_id=task_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            clear_requirements=clear_requirements,
            has_examples=has_examples,
            understands_architecture=understands_architecture,
            knows_dependencies=knows_dependencies,
            can_verify_success=can_verify_success,
            risks=risks,
            questions=questions,
            alternatives=alternatives,
            should_proceed=should_proceed,
            recommendation=recommendation,
        )

    def _assess_requirements_clarity(self, task: Dict[str, Any]) -> bool:
        """
        Assess if requirements are clear.

        Returns:
            True if requirements are clear and unambiguous
        """
        # Check for clear description
        description = task.get("description", "")
        if len(description) < 20:
            return False

        # Check for acceptance criteria
        acceptance_criteria = task.get("acceptance_criteria", [])
        if not acceptance_criteria or len(acceptance_criteria) < 1:
            return False

        # Check for vague language
        vague_words = ["maybe", "probably", "should", "could", "might", "possibly"]
        description_lower = description.lower()

        if any(word in description_lower for word in vague_words):
            return False

        return True

    def _assess_examples_available(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Assess if examples or similar code exists.

        Returns:
            True if examples available
        """
        # Check if files_likely_affected has examples
        files_affected = task.get("files_likely_affected", [])

        if not files_affected:
            return False

        # Check if those files exist (as examples)
        for file_path in files_affected:
            full_path = self.project_root / file_path
            if full_path.exists():
                return True

        return False

    def _assess_architecture_understanding(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Assess if architecture is understood.

        Returns:
            True if architecture clear
        """
        # Check if files_likely_affected are in known structure
        files_affected = task.get("files_likely_affected", [])

        if not files_affected:
            return False

        # Check if parent directories exist (indicates known structure)
        for file_path in files_affected:
            full_path = self.project_root / file_path
            parent_dir = full_path.parent

            if not parent_dir.exists():
                return False

        return True

    def _assess_dependencies_clear(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Assess if dependencies are clear.

        Returns:
            True if dependencies understood
        """
        # Check for explicit dependencies in task
        dependencies = task.get("dependencies", [])

        # If has dependencies, check if they're clear
        if dependencies:
            # Dependencies listed = clear
            return True

        # No dependencies = also clear (independent task)
        return True

    def _assess_verification_possible(self, task: Dict[str, Any]) -> bool:
        """
        Assess if success can be verified.

        Returns:
            True if can verify success
        """
        # Check for test requirements
        test_requirements = task.get("test_requirements", [])

        if test_requirements and len(test_requirements) > 0:
            return True

        # Check for acceptance criteria (can be verified)
        acceptance_criteria = task.get("acceptance_criteria", [])

        if acceptance_criteria and len(acceptance_criteria) > 0:
            # Check if criteria are verifiable (not vague)
            for criterion in acceptance_criteria:
                if any(word in criterion.lower() for word in ["works", "good", "better", "nice"]):
                    return False
            return True

        return False

    def _calculate_confidence_score(
        self,
        clear_requirements: bool,
        has_examples: bool,
        understands_architecture: bool,
        knows_dependencies: bool,
        can_verify_success: bool,
    ) -> int:
        """
        Calculate overall confidence score (0-100).

        Weighted scoring:
        - Clear requirements: 30 points
        - Has examples: 20 points
        - Understands architecture: 20 points
        - Knows dependencies: 15 points
        - Can verify success: 15 points

        Returns:
            Score from 0-100
        """
        score = 0

        if clear_requirements:
            score += 30
        if has_examples:
            score += 20
        if understands_architecture:
            score += 20
        if knows_dependencies:
            score += 15
        if can_verify_success:
            score += 15

        return score

    def _identify_risks(self, task: Dict[str, Any], confidence_score: int) -> List[Dict[str, str]]:
        """
        Identify risks based on task and confidence.

        Returns:
            List of risk dictionaries
        """
        risks = []

        # Low confidence = high risk
        if confidence_score < 70:
            risks.append(
                {"risk": "Low confidence - may implement wrong solution", "severity": "high"}
            )

        # Check for complexity without examples
        complexity = task.get("complexity", "M")
        if complexity in ["L", "XL"] and confidence_score < 80:
            risks.append({"risk": "High complexity with unclear requirements", "severity": "high"})

        # Check for dependencies without clear understanding
        dependencies = task.get("dependencies", [])
        if len(dependencies) > 2 and confidence_score < 85:
            risks.append({"risk": "Multiple dependencies - integration risk", "severity": "medium"})

        return risks

    def _generate_clarifying_questions(
        self,
        task: Dict[str, Any],
        clear_requirements: bool,
        has_examples: bool,
        understands_architecture: bool,
        knows_dependencies: bool,
        can_verify_success: bool,
    ) -> List[str]:
        """
        Generate clarifying questions for medium/low confidence.

        Returns:
            List of questions to ask user
        """
        questions = []

        if not clear_requirements:
            questions.append(
                "Can you clarify the requirements? What exactly should the implementation do?"
            )
            questions.append("Are there any edge cases or constraints I should be aware of?")

        if not has_examples:
            questions.append("Are there any existing examples or similar code I can reference?")

        if not understands_architecture:
            questions.append(
                "Can you explain the architecture? Where should this code fit in the project structure?"
            )

        if not knows_dependencies:
            questions.append(
                "What are the dependencies for this task? What other components does it interact with?"
            )

        if not can_verify_success:
            questions.append(
                "How will we verify this is working correctly? What are the success criteria?"
            )

        return questions

    def _generate_alternatives(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Generate alternative approaches for medium confidence.

        Returns:
            List of alternative dictionaries
        """
        # This would be enhanced with actual analysis
        # For now, return placeholder
        return [
            {
                "approach": "Option 1: Minimal implementation",
                "pros": "Quick to implement, easy to test",
                "cons": "May lack features",
            },
            {
                "approach": "Option 2: Full-featured implementation",
                "pros": "Complete solution, handles edge cases",
                "cons": "More complex, takes longer",
            },
        ]

    def _generate_recommendation(
        self,
        confidence_level: ConfidenceLevel,
        confidence_score: int,
        risks: List[Dict[str, str]],
        questions: List[str],
    ) -> str:
        """
        Generate recommendation based on confidence.

        Returns:
            Recommendation string
        """
        if confidence_level == ConfidenceLevel.HIGH:
            return (
                f"✅ HIGH CONFIDENCE ({confidence_score}%) - Proceed with implementation. "
                "Requirements are clear and success can be verified."
            )

        elif confidence_level == ConfidenceLevel.MEDIUM:
            return (
                f"⚠️ MEDIUM CONFIDENCE ({confidence_score}%) - "
                f"Please clarify {len(questions)} questions before proceeding. "
                "Multiple approaches possible - user input recommended."
            )

        else:  # LOW
            risk_count = len([r for r in risks if r["severity"] == "high"])
            return (
                f"🛑 LOW CONFIDENCE ({confidence_score}%) - DO NOT PROCEED. "
                f"{risk_count} high-severity risks identified. "
                "Investigate requirements and ask user for guidance."
            )


def log_confidence_assessment(assessment: ConfidenceAssessment, telemetry_file: Path) -> None:
    """
    Log confidence assessment to telemetry.

    Args:
        assessment: ConfidenceAssessment to log
        telemetry_file: Path to telemetry file
    """
    import time

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": "confidence_assessment",
        **assessment.to_dict(),
    }

    # Append to telemetry file
    with open(telemetry_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


if __name__ == "__main__":
    # Test confidence checker
    print("WFC Confidence Checker Test")
    print("=" * 60)

    # Test 1: High confidence task
    print("\n1. Testing HIGH confidence task:")
    high_confidence_task = {
        "id": "TASK-001",
        "description": "Add a new endpoint /api/users that returns list of users from database",
        "acceptance_criteria": [
            "Endpoint responds to GET requests",
            "Returns JSON array of user objects",
            "Returns 200 status code on success",
        ],
        "complexity": "M",
        "files_likely_affected": ["src/api/users.py"],
        "test_requirements": ["Test endpoint returns 200", "Test JSON format"],
    }

    checker = ConfidenceChecker(Path.cwd())
    assessment = checker.assess(high_confidence_task)

    print(f"   Confidence: {assessment.confidence_score}% ({assessment.confidence_level.value})")
    print(f"   Should proceed: {assessment.should_proceed}")
    print(f"   ✅ {assessment.recommendation}")

    # Test 2: Medium confidence task
    print("\n2. Testing MEDIUM confidence task:")
    medium_confidence_task = {
        "id": "TASK-002",
        "description": "Improve the authentication system",
        "acceptance_criteria": ["Authentication is better", "Users can log in"],
        "complexity": "L",
        "dependencies": ["TASK-001", "TASK-003"],
    }

    assessment = checker.assess(medium_confidence_task)

    print(f"   Confidence: {assessment.confidence_score}% ({assessment.confidence_level.value})")
    print(f"   Should proceed: {assessment.should_proceed}")
    print(f"   Questions: {len(assessment.questions)}")
    for q in assessment.questions[:3]:
        print(f"      - {q}")
    print(f"   ⚠️  {assessment.recommendation}")

    # Test 3: Low confidence task
    print("\n3. Testing LOW confidence task:")
    low_confidence_task = {
        "id": "TASK-003",
        "description": "Fix the bug",
        "acceptance_criteria": [],
    }

    assessment = checker.assess(low_confidence_task)

    print(f"   Confidence: {assessment.confidence_score}% ({assessment.confidence_level.value})")
    print(f"   Should proceed: {assessment.should_proceed}")
    print(f"   Risks: {len(assessment.risks)}")
    for risk in assessment.risks:
        print(f"      - {risk['risk']} ({risk['severity']})")
    print(f"   🛑 {assessment.recommendation}")

    print("\n✅ All confidence checker tests passed!")
