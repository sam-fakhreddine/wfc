"""
Adaptive Interview System

Gathers requirements through intelligent questioning.
Adapts questions based on previous answers.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


@dataclass
class Question:
    """Single interview question"""

    id: str
    text: str
    type: str  # "text", "choice", "multi_choice"
    options: Optional[List[str]] = None
    depends_on: Optional[str] = None  # Question ID dependency
    condition: Optional[str] = None  # Answer condition to trigger


@dataclass
class InterviewResult:
    """Complete interview results"""

    goal: str
    context: str
    requirements: List[str]
    constraints: List[str]
    technologies: List[str]
    properties: List[Dict[str, Any]]
    raw_answers: Dict[str, Any]
    team_values_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "context": self.context,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "technologies": self.technologies,
            "properties": self.properties,
            "raw_answers": self.raw_answers,
            "team_values_context": self.team_values_context,
        }

    def save(self, path: Path) -> None:
        """Save interview results to JSON"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class AdaptiveInterviewer:
    """
    Adaptive interview system for requirements gathering.

    Asks intelligent questions and adapts based on answers.
    Follows ELEGANT principles: simple, focused questions.
    """

    def __init__(self):
        self.questions = self._build_questions()
        self.answers: Dict[str, Any] = {}

    def _build_questions(self) -> List[Question]:
        """Build the question tree"""
        return [
            # Core questions
            Question(id="goal", text="What are you trying to build? (1-2 sentences)", type="text"),
            Question(
                id="context",
                text="Why are you building this? What problem does it solve?",
                type="text",
            ),
            Question(
                id="users",
                text="Who will use this? (developers, end-users, internal team, etc.)",
                type="text",
            ),
            # Requirements
            Question(
                id="core_features",
                text="What are the 3-5 core features this must have?",
                type="text",
            ),
            Question(
                id="nice_to_have",
                text="What features are nice-to-have but not critical?",
                type="text",
            ),
            # Technical
            Question(
                id="tech_stack",
                text="What technologies/languages/frameworks should we use?",
                type="text",
            ),
            Question(
                id="existing_code",
                text="Is this a new project or adding to existing code?",
                type="choice",
                options=["new_project", "existing_codebase"],
            ),
            Question(
                id="codebase_path",
                text="Where is the existing codebase?",
                type="text",
                depends_on="existing_code",
                condition="existing_codebase",
            ),
            # Constraints
            Question(
                id="performance",
                text="Are there specific performance requirements? (response time, throughput, etc.)",
                type="text",
            ),
            Question(
                id="scale",
                text="What scale do you expect? (users, requests/sec, data volume)",
                type="text",
            ),
            Question(
                id="security",
                text="What security requirements exist? (authentication, authorization, data sensitivity)",
                type="text",
            ),
            # Properties (formal)
            Question(
                id="safety_critical",
                text="Are there critical safety properties? (e.g., 'unauthenticated user must never access X')",
                type="text",
            ),
            Question(
                id="liveness_required",
                text="Are there liveness properties? (e.g., 'system must respond within N ms')",
                type="text",
            ),
            # Testing
            Question(
                id="testing_approach",
                text="What testing approach do you prefer?",
                type="choice",
                options=["unit_only", "unit_integration", "full_e2e"],
            ),
            Question(
                id="coverage_target",
                text="What test coverage target? (e.g., 80%, critical paths only)",
                type="text",
            ),
            # TEAMCHARTER Alignment
            Question(
                id="teamcharter_values",
                text="Which TEAMCHARTER values are most relevant to this feature? (innovation, accountability, teamwork, learning, customer_focus, trust)",
                type="multi_choice",
                options=[
                    "innovation",
                    "accountability",
                    "teamwork",
                    "learning",
                    "customer_focus",
                    "trust",
                ],
            ),
            Question(
                id="customer_stakeholder",
                text="Who is the primary customer/stakeholder for this work?",
                type="text",
            ),
            Question(
                id="customer_success",
                text="What does success look like from the customer's perspective?",
                type="text",
                depends_on="teamcharter_values",
                condition="customer_focus",
            ),
            Question(
                id="speed_quality_tradeoff",
                text="What trade-offs between speed and quality are acceptable?",
                type="choice",
                options=["speed_first", "balanced", "quality_first"],
            ),
        ]

    def should_ask(self, question: Question) -> bool:
        """Determine if question should be asked based on dependencies"""
        if not question.depends_on:
            return True

        if question.depends_on not in self.answers:
            return False

        if question.condition:
            return self.answers[question.depends_on] == question.condition

        return True

    def ask(self, question: Question) -> Any:
        """
        Ask a question and get answer.
        In real implementation, this would use AskUserQuestion tool.
        For now, returns placeholder.
        """
        # This is a mock for now - real implementation would use Claude's AskUserQuestion
        return f"[Answer to: {question.text}]"

    def run_interview(self) -> InterviewResult:
        """
        Run complete adaptive interview.

        Returns structured interview results.
        """
        for question in self.questions:
            if self.should_ask(question):
                answer = self.ask(question)
                self.answers[question.id] = answer

        # Parse answers into structured result
        return self._parse_results()

    def _parse_results(self) -> InterviewResult:
        """Parse raw answers into structured InterviewResult"""

        # Extract core info
        goal = self.answers.get("goal", "")
        context = self.answers.get("context", "")

        # Extract requirements
        core_features = self.answers.get("core_features", "")
        nice_to_have = self.answers.get("nice_to_have", "")
        requirements = []
        if core_features:
            requirements.extend([f.strip() for f in core_features.split("\n") if f.strip()])
        if nice_to_have:
            requirements.extend(
                [f"[Nice-to-have] {f.strip()}" for f in nice_to_have.split("\n") if f.strip()]
            )

        # Extract constraints
        constraints = []
        if perf := self.answers.get("performance"):
            constraints.append(f"Performance: {perf}")
        if scale := self.answers.get("scale"):
            constraints.append(f"Scale: {scale}")
        if sec := self.answers.get("security"):
            constraints.append(f"Security: {sec}")

        # Extract technologies
        tech_stack = self.answers.get("tech_stack", "")
        technologies = [t.strip() for t in tech_stack.split(",") if t.strip()]

        # Extract formal properties
        properties = []
        if safety := self.answers.get("safety_critical"):
            properties.append({"type": "SAFETY", "statement": safety, "priority": "critical"})
        if liveness := self.answers.get("liveness_required"):
            properties.append({"type": "LIVENESS", "statement": liveness, "priority": "high"})

        # Extract TEAMCHARTER values context
        team_values_context = {}
        if tc_values := self.answers.get("teamcharter_values"):
            team_values_context["primary_values"] = (
                tc_values if isinstance(tc_values, list) else [tc_values]
            )
        if customer := self.answers.get("customer_stakeholder"):
            team_values_context["customer"] = customer
        if success := self.answers.get("customer_success"):
            team_values_context["success_metric"] = success
        if tradeoff := self.answers.get("speed_quality_tradeoff"):
            team_values_context["speed_quality_tradeoff"] = tradeoff

        return InterviewResult(
            goal=goal,
            context=context,
            requirements=requirements,
            constraints=constraints,
            technologies=technologies,
            properties=properties,
            raw_answers=self.answers,
            team_values_context=team_values_context,
        )


# CLI for testing
if __name__ == "__main__":
    interviewer = AdaptiveInterviewer()
    result = interviewer.run_interview()
    print("Interview Results:")
    print(json.dumps(result.to_dict(), indent=2))
