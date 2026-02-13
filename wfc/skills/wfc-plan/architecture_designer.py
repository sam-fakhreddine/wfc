"""
Architecture Designer

Generates 2-3 architecture approaches with trade-offs
for user selection during the planning phase.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ArchitectureApproach:
    """A single architecture approach with trade-offs."""

    name: str
    summary: str
    pros: List[str]
    cons: List[str]
    effort: str  # S, M, L, XL
    risk: str  # low, medium, high
    files_affected: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    considerations: List[str] = field(default_factory=list)


class ArchitectureDesigner:
    """
    Generates 2-3 architecture approaches with trade-offs.

    Three standard approaches (inspired by feature-dev plugin):
    1. Minimal Changes - smallest diff, maximum reuse of existing code
    2. Clean Architecture - proper abstractions, maintainability-first
    3. Pragmatic Balance - speed + quality tradeoff

    The designer produces structured approach descriptions that
    Claude presents to the user for selection before task generation.
    """

    APPROACH_TEMPLATES = [
        {
            "name": "Minimal Changes",
            "philosophy": "Smallest diff, maximum reuse of existing code",
            "default_pros": [
                "Lowest risk - minimal code changes",
                "Fastest to implement",
                "Easy to review and understand diff",
            ],
            "default_cons": [
                "May accumulate tech debt",
                "Might not scale well",
                "Could miss opportunity for better design",
            ],
            "effort": "S",
            "risk": "low",
        },
        {
            "name": "Clean Architecture",
            "philosophy": "Proper abstractions, maintainability-first",
            "default_pros": [
                "Best long-term maintainability",
                "Clear separation of concerns",
                "Easier to test and extend",
            ],
            "default_cons": [
                "More code to write and review",
                "Higher initial effort",
                "May be over-engineered for simple features",
            ],
            "effort": "L",
            "risk": "medium",
        },
        {
            "name": "Pragmatic Balance",
            "philosophy": "Speed + quality tradeoff - good enough architecture",
            "default_pros": [
                "Balanced effort vs quality",
                "Addresses key architectural concerns",
                "Practical for most features",
            ],
            "default_cons": [
                "Compromises on both extremes",
                "Requires good judgment on trade-offs",
                "May need future refinement",
            ],
            "effort": "M",
            "risk": "low",
        },
    ]

    def design(
        self,
        goal: str,
        context: str,
        constraints: Optional[List[str]] = None,
        existing_patterns: Optional[List[str]] = None,
    ) -> List[ArchitectureApproach]:
        """
        Generate architecture approaches based on interview results.

        Args:
            goal: What we're building
            context: Why we're building it
            constraints: Technical constraints
            existing_patterns: Patterns already in the codebase

        Returns:
            List of 2-3 ArchitectureApproach options
        """
        approaches = []

        # Extract technology mentions from context for tailoring descriptions
        tech_keywords = []
        if context:
            # Common technology terms to detect in context
            known_techs = [
                "react",
                "vue",
                "angular",
                "django",
                "flask",
                "fastapi",
                "node",
                "express",
                "redis",
                "postgres",
                "postgresql",
                "mysql",
                "mongodb",
                "docker",
                "kubernetes",
                "k8s",
                "graphql",
                "rest",
                "grpc",
                "kafka",
                "rabbitmq",
                "aws",
                "gcp",
                "azure",
                "terraform",
                "celery",
                "sqlalchemy",
                "prisma",
                "nextjs",
                "typescript",
                "python",
                "go",
                "rust",
                "java",
            ]
            context_lower = context.lower()
            tech_keywords = [t for t in known_techs if t in context_lower]

        for template in self.APPROACH_TEMPLATES:
            summary = f"{template['philosophy']} for: {goal}"

            # Tailor the Minimal Changes approach if existing_patterns are provided
            if template["name"] == "Minimal Changes" and existing_patterns:
                patterns_str = ", ".join(existing_patterns[:3])
                summary = (
                    f"{template['philosophy']} for: {goal} "
                    f"(building on existing patterns: {patterns_str})"
                )

            # Reflect detected technologies in approach descriptions
            if tech_keywords:
                tech_str = ", ".join(tech_keywords[:3])
                summary += f" [tech: {tech_str}]"

            approach = ArchitectureApproach(
                name=template["name"],
                summary=summary,
                pros=list(template["default_pros"]),
                cons=list(template["default_cons"]),
                effort=template["effort"],
                risk=template["risk"],
            )

            # If constraints are provided, add them to considerations
            if constraints:
                for constraint in constraints:
                    approach.considerations.append(constraint)

            approaches.append(approach)

        return approaches

    def format_comparison(self, approaches: List[ArchitectureApproach]) -> str:
        """Format approaches as markdown comparison for user selection."""
        lines = [
            "## Architecture Approaches",
            "",
            "Choose an approach for implementation:",
            "",
        ]

        for i, approach in enumerate(approaches, 1):
            lines.extend(
                [
                    f"### Option {i}: {approach.name}",
                    f"**Summary**: {approach.summary}",
                    f"**Effort**: {approach.effort} | **Risk**: {approach.risk}",
                    "",
                    "**Pros:**",
                ]
            )
            for pro in approach.pros:
                lines.append(f"- {pro}")

            lines.append("")
            lines.append("**Cons:**")
            for con in approach.cons:
                lines.append(f"- {con}")

            if approach.considerations:
                lines.append("")
                lines.append("**Considerations:**")
                for consideration in approach.considerations:
                    lines.append(f"- {consideration}")

            if approach.key_decisions:
                lines.append("")
                lines.append("**Key Decisions:**")
                for decision in approach.key_decisions:
                    lines.append(f"- {decision}")

            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "| Aspect | " + " | ".join(a.name for a in approaches) + " |",
                "| --- | " + " | ".join("---" for _ in approaches) + " |",
                "| Effort | " + " | ".join(a.effort for a in approaches) + " |",
                "| Risk | " + " | ".join(a.risk for a in approaches) + " |",
                "| Pros | " + " | ".join(str(len(a.pros)) for a in approaches) + " |",
                "| Cons | " + " | ".join(str(len(a.cons)) for a in approaches) + " |",
                "",
            ]
        )

        return "\n".join(lines)
