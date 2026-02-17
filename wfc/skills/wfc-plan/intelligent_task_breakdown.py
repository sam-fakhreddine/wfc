#!/usr/bin/env python3
"""
Intelligent Task Breakdown for wfc-plan

Enhanced task generation with:
- Smart dependency detection
- Critical path analysis
- Risk assessment
- Complexity estimation from code patterns
- File inference from task descriptions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class TaskRisk:
    """Risk assessment for a task."""

    level: str  # low, medium, high, critical
    description: str
    mitigation: str


@dataclass
class IntelligentTask:
    """Enhanced task with intelligence."""

    id: str
    title: str
    description: str
    complexity: str  # S, M, L, XL
    dependencies: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)

    # Enhanced fields
    estimated_hours: float = 0.0
    critical_path: bool = False
    parallelizable: bool = True
    risks: List[TaskRisk] = field(default_factory=list)
    suggested_approach: str = ""
    test_strategy: str = ""


class IntelligentTaskBreakdown:
    """
    Intelligent task breakdown engine.

    Uses pattern matching and heuristics to generate smart task breakdowns.
    """

    # Complexity patterns (keywords that indicate complexity)
    COMPLEXITY_PATTERNS = {
        "XL": [
            "distributed",
            "microservice",
            "architecture",
            "scalable",
            "real-time",
            "streaming",
            "machine learning",
            "ai",
            "blockchain",
            "consensus",
            "sharding",
        ],
        "L": [
            "authentication",
            "authorization",
            "payment",
            "integration",
            "migration",
            "refactor",
            "optimize",
            "security",
            "encryption",
            "caching",
            "queue",
            "async",
            "concurrent",
        ],
        "M": [
            "api",
            "endpoint",
            "crud",
            "database",
            "model",
            "service",
            "component",
            "feature",
            "validation",
            "middleware",
        ],
        "S": [
            "fix",
            "update",
            "add",
            "remove",
            "logging",
            "config",
            "documentation",
            "format",
            "lint",
            "test",
        ],
    }

    # Risk indicators
    RISK_PATTERNS = {
        "critical": ["security", "auth", "payment", "data loss", "privacy"],
        "high": ["migration", "breaking change", "backward incompatible", "deprecated"],
        "medium": ["performance", "scaling", "complexity", "refactor"],
        "low": ["logging", "documentation", "formatting", "config"],
    }

    # File patterns (infer files from task description)
    FILE_PATTERNS = {
        "api": ["api/{name}.py", "tests/test_api_{name}.py"],
        "model": ["models/{name}.py", "tests/test_{name}.py"],
        "service": ["services/{name}.py", "tests/test_{name}_service.py"],
        "auth": ["auth/{name}.py", "middleware/auth.py", "tests/test_auth.py"],
        "database": ["models/{name}.py", "migrations/", "tests/test_db.py"],
        "frontend": ["components/{name}.tsx", "tests/{name}.test.tsx"],
        "config": ["config/{name}.yml", "config/{name}.json"],
    }

    def __init__(self):
        self.tasks: List[IntelligentTask] = []
        self.task_graph: Dict[str, Set[str]] = {}  # task_id -> dependencies

    def analyze_and_break_down(
        self, requirements: List[str], tech_stack: List[str] = None
    ) -> List[IntelligentTask]:
        """
        Intelligently break down requirements into tasks.

        Args:
            requirements: List of requirement descriptions
            tech_stack: Optional technology stack for context

        Returns:
            List of intelligent tasks with dependencies and analysis
        """
        tech_stack = tech_stack or []

        # Phase 1: Create initial tasks
        for idx, req in enumerate(requirements):
            task = self._create_task_from_requirement(req, idx + 1)
            self.tasks.append(task)

        # Phase 2: Detect dependencies
        self._detect_dependencies()

        # Phase 3: Critical path analysis
        self._analyze_critical_path()

        # Phase 4: Risk assessment
        self._assess_risks()

        # Phase 5: Add infrastructure tasks if needed
        self._add_infrastructure_tasks(tech_stack)

        return self.tasks

    def _create_task_from_requirement(self, requirement: str, task_num: int) -> IntelligentTask:
        """Create task from requirement with intelligent analysis."""
        task_id = f"TASK-{task_num:03d}"

        # Extract title (first sentence or first 50 chars)
        title = requirement.split(".")[0][:100]

        # Estimate complexity
        complexity = self._estimate_complexity(requirement)

        # Infer files
        files = self._infer_files(requirement)

        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(requirement, complexity)

        # Match properties
        properties = self._match_properties(requirement)

        # Estimate hours
        hours = self._estimate_hours(complexity)

        # Generate test strategy
        test_strategy = self._generate_test_strategy(requirement, complexity)

        # Suggest approach
        approach = self._suggest_approach(requirement, complexity)

        return IntelligentTask(
            id=task_id,
            title=title,
            description=requirement,
            complexity=complexity,
            files=files,
            acceptance_criteria=acceptance_criteria,
            properties=properties,
            estimated_hours=hours,
            test_strategy=test_strategy,
            suggested_approach=approach,
        )

    def _estimate_complexity(self, text: str) -> str:
        """Estimate task complexity using pattern matching."""
        text_lower = text.lower()

        # Check patterns in order (XL -> L -> M -> S)
        for complexity in ["XL", "L", "M", "S"]:
            patterns = self.COMPLEXITY_PATTERNS[complexity]
            if any(pattern in text_lower for pattern in patterns):
                return complexity

        # Default to M if no pattern matches
        return "M"

    def _infer_files(self, text: str) -> List[str]:
        """Infer likely files from task description."""
        text_lower = text.lower()
        files = []

        # Check file patterns
        for pattern_type, file_templates in self.FILE_PATTERNS.items():
            if pattern_type in text_lower:
                # Extract entity name (e.g., "user api" -> "user")
                words = text_lower.split()
                if pattern_type in words:
                    idx = words.index(pattern_type)
                    if idx > 0:
                        name = words[idx - 1]
                        files.extend([t.format(name=name) for t in file_templates])

        return files if files else ["src/"]  # Default to src/ if no specific files

    def _generate_acceptance_criteria(self, requirement: str, complexity: str) -> List[str]:
        """Generate smart acceptance criteria based on requirement."""
        criteria = []

        text_lower = requirement.lower()

        # Always include basic criteria
        criteria.append("Implementation matches requirement")
        criteria.append("All tests pass")

        # Complexity-specific criteria
        if complexity in ["L", "XL"]:
            criteria.append("Architecture documented")
            criteria.append("Performance benchmarked")

        # Pattern-specific criteria
        if "api" in text_lower:
            criteria.extend(
                [
                    "API endpoints respond correctly",
                    "Error handling implemented",
                    "API documentation updated",
                ]
            )

        if "database" in text_lower or "model" in text_lower:
            criteria.extend(
                [
                    "Database schema created/updated",
                    "Migrations tested",
                    "Data validation implemented",
                ]
            )

        if "security" in text_lower or "auth" in text_lower:
            criteria.extend(
                ["Security review passed", "Authentication tested", "Authorization rules validated"]
            )

        if "test" in text_lower:
            criteria.extend(["Test coverage > 80%", "Edge cases covered"])

        return criteria

    def _match_properties(self, text: str) -> List[str]:
        """Match formal properties to requirement."""
        text_lower = text.lower()
        properties = []

        # SAFETY
        if any(kw in text_lower for kw in ["safe", "validate", "check", "guard"]):
            properties.append("SAFETY")

        # SECURITY
        if any(kw in text_lower for kw in ["secure", "auth", "encrypt", "protect"]):
            properties.append("SECURITY")

        # PERFORMANCE
        if any(kw in text_lower for kw in ["fast", "optimize", "performance", "cache"]):
            properties.append("PERFORMANCE")

        # LIVENESS
        if any(kw in text_lower for kw in ["eventually", "async", "queue", "retry"]):
            properties.append("LIVENESS")

        # CORRECTNESS (default for most tasks)
        properties.append("CORRECTNESS")

        return list(set(properties))  # Remove duplicates

    def _estimate_hours(self, complexity: str) -> float:
        """Estimate hours based on complexity."""
        hours_map = {"S": 2.0, "M": 4.0, "L": 8.0, "XL": 16.0}
        return hours_map.get(complexity, 4.0)

    def _generate_test_strategy(self, requirement: str, complexity: str) -> str:
        """Generate testing strategy for the task."""
        text_lower = requirement.lower()

        if "api" in text_lower:
            return "Unit tests for API logic + Integration tests for endpoints + Contract tests"
        elif "database" in text_lower:
            return "Unit tests with mocked DB + Integration tests with test DB + Migration tests"
        elif "ui" in text_lower or "frontend" in text_lower:
            return "Component tests + E2E tests + Visual regression tests"
        elif complexity in ["L", "XL"]:
            return "Unit tests + Integration tests + E2E tests + Performance tests"
        else:
            return "Unit tests + Integration tests"

    def _suggest_approach(self, requirement: str, complexity: str) -> str:
        """Suggest implementation approach."""
        text_lower = requirement.lower()

        if "migration" in text_lower:
            return "1. Create migration script 2. Test on copy of prod data 3. Rollback plan 4. Execute with monitoring"
        elif "refactor" in text_lower:
            return "1. Write tests first 2. Refactor incrementally 3. Keep tests passing 4. Benchmark performance"
        elif "api" in text_lower:
            return "1. Define API contract 2. Implement handler 3. Add validation 4. Write tests 5. Document"
        elif complexity == "XL":
            return "1. Break into subtasks 2. Prototype approach 3. Get architecture review 4. Implement incrementally"
        else:
            return "TDD: Write tests first, implement to pass tests, refactor"

    def _detect_dependencies(self) -> None:
        """Detect task dependencies using heuristics."""
        for i, task in enumerate(self.tasks):
            deps = set()

            text_lower = task.description.lower()

            # Check if task mentions other tasks
            for j, other_task in enumerate(self.tasks):
                if i == j:
                    continue

                other_lower = other_task.description.lower()

                # Check for explicit dependency keywords
                if any(kw in text_lower for kw in ["after", "depends on", "requires", "uses"]):
                    # Look for words from other task in current task
                    other_words = set(other_lower.split())
                    current_words = set(text_lower.split())

                    if len(other_words & current_words) > 3:  # Significant overlap
                        deps.add(other_task.id)

                # Infer logical dependencies
                # API implementation depends on model definition
                if "api" in text_lower and "model" in other_lower:
                    if j < i:  # Only depend on earlier tasks
                        deps.add(other_task.id)

                # Testing depends on implementation
                if "test" in text_lower and "implement" in other_lower:
                    if j < i:
                        deps.add(other_task.id)

            task.dependencies = list(deps)

    def _analyze_critical_path(self) -> None:
        """Identify critical path tasks."""
        # Build dependency graph
        for task in self.tasks:
            self.task_graph[task.id] = set(task.dependencies)

        # Tasks with no dependents are on critical path
        all_deps = set()
        for deps in self.task_graph.values():
            all_deps.update(deps)

        for task in self.tasks:
            # Mark as critical if:
            # 1. Has many dependencies
            # 2. Is high complexity
            # 3. Is blocking (many tasks depend on it)
            blocking_count = sum(1 for deps in self.task_graph.values() if task.id in deps)

            task.critical_path = (
                len(task.dependencies) > 2 or task.complexity in ["L", "XL"] or blocking_count > 2
            )

            # Mark as non-parallelizable if has dependencies
            task.parallelizable = len(task.dependencies) == 0

    def _assess_risks(self) -> None:
        """Assess risks for each task."""
        for task in self.tasks:
            text_lower = task.description.lower()

            risks = []

            # Check risk patterns
            for level, patterns in self.RISK_PATTERNS.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        risks.append(
                            TaskRisk(
                                level=level,
                                description=f"{pattern.title()} implementation carries {level} risk",
                                mitigation=self._suggest_mitigation(pattern, level),
                            )
                        )

            # Complexity-based risks
            if task.complexity == "XL":
                risks.append(
                    TaskRisk(
                        level="high",
                        description="Very large task - may take longer than estimated",
                        mitigation="Break into smaller subtasks, implement incrementally",
                    )
                )

            task.risks = risks

    def _suggest_mitigation(self, risk_keyword: str, level: str) -> str:
        """Suggest risk mitigation strategies."""
        mitigations = {
            "security": "Security review + penetration testing + code audit",
            "auth": "Use proven library + multi-factor auth + audit logging",
            "payment": "Use payment provider + test with test cards + rollback plan",
            "migration": "Test on copy + incremental rollout + rollback script",
            "performance": "Benchmark before/after + load testing + monitoring",
            "breaking change": "Deprecation period + migration guide + backwards compatibility layer",
        }

        return mitigations.get(risk_keyword, "Thorough testing + code review + monitoring")

    def _add_infrastructure_tasks(self, tech_stack: List[str]) -> None:
        """Add necessary infrastructure tasks based on tech stack."""
        # Check if we need setup tasks
        has_setup = any("setup" in t.title.lower() for t in self.tasks)

        if not has_setup:
            setup_task = IntelligentTask(
                id="TASK-000",
                title="Initial project setup",
                description="Set up project structure, dependencies, and configuration",
                complexity="S",
                files=["README.md", "pyproject.toml", ".gitignore"],
                acceptance_criteria=[
                    "Project structure created",
                    "Dependencies documented",
                    "CI/CD configured",
                ],
                properties=["CORRECTNESS"],
                estimated_hours=1.0,
                parallelizable=False,
                critical_path=True,
                test_strategy="Installation test + smoke tests",
                suggested_approach="Follow language/framework best practices",
            )

            # Insert at beginning
            self.tasks.insert(0, setup_task)

            # All other tasks depend on setup
            for task in self.tasks[1:]:
                if "TASK-000" not in task.dependencies:
                    task.dependencies.insert(0, "TASK-000")


def render_intelligent_tasks(tasks: List[IntelligentTask]) -> str:
    """Render intelligent tasks to TASKS.md format."""
    lines = ["# Implementation Tasks", "", "**Generated with Intelligent Task Breakdown**", ""]

    # Summary
    total_hours = sum(t.estimated_hours for t in tasks)
    critical_tasks = [t for t in tasks if t.critical_path]
    parallel_tasks = [t for t in tasks if t.parallelizable]

    lines.extend(
        [
            "## Summary",
            f"- Total tasks: {len(tasks)}",
            f"- Estimated hours: {total_hours:.1f}h ({total_hours/8:.1f} days)",
            f"- Critical path tasks: {len(critical_tasks)}",
            f"- Parallelizable tasks: {len(parallel_tasks)}",
            "",
        ]
    )

    # Tasks
    lines.append("## Tasks")
    lines.append("")

    for task in tasks:
        lines.extend(
            [
                f"### {task.id}: {task.title}",
                f"- **Complexity**: {task.complexity} ({task.estimated_hours}h)",
                f"- **Dependencies**: {', '.join(task.dependencies) if task.dependencies else 'None'}",
                f"- **Properties**: {', '.join(task.properties)}",
                f"- **Files**: {', '.join(task.files) if task.files else 'TBD'}",
                f"- **Critical Path**: {'Yes' if task.critical_path else 'No'}",
                f"- **Parallelizable**: {'Yes' if task.parallelizable else 'No'}",
                "",
                f"**Description**: {task.description}",
                "",
                "**Acceptance Criteria**:",
            ]
        )

        for criterion in task.acceptance_criteria:
            lines.append(f"- {criterion}")

        lines.append("")
        lines.append(f"**Test Strategy**: {task.test_strategy}")
        lines.append("")
        lines.append(f"**Suggested Approach**: {task.suggested_approach}")

        if task.risks:
            lines.append("")
            lines.append("**Risks**:")
            for risk in task.risks:
                lines.append(f"- [{risk.level.upper()}] {risk.description}")
                lines.append(f"  - Mitigation: {risk.mitigation}")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test intelligent task breakdown
    requirements = [
        "Implement user authentication with JWT tokens",
        "Create REST API for user management (CRUD operations)",
        "Add database migrations for user schema",
        "Implement authorization middleware for protected routes",
        "Add comprehensive test suite with >80% coverage",
    ]

    tech_stack = ["Python", "FastAPI", "PostgreSQL", "JWT"]

    breakdown = IntelligentTaskBreakdown()
    tasks = breakdown.analyze_and_break_down(requirements, tech_stack)

    markdown = render_intelligent_tasks(tasks)
    print(markdown)
