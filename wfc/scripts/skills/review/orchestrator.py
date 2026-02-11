"""
Review Orchestrator

Coordinates agents → consensus → report.
Supports both legacy 4-agent mode and persona-based mode.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)

# Handle both relative imports (when used as package) and standalone execution
try:
    from .agents import CodeReviewAgent, SecurityAgent, PerformanceAgent, ComplexityAgent
    from .consensus import ConsensusAlgorithm, ConsensusResult
except ImportError:
    # Standalone execution - add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from agents import CodeReviewAgent, SecurityAgent, PerformanceAgent, ComplexityAgent
    from consensus import ConsensusAlgorithm, ConsensusResult

# Import persona system if available (NEW PATHS)
try:
    sys.path.insert(0, str(Path.home() / ".claude/skills/wfc"))
    from scripts.personas.persona_orchestrator import (
        PersonaRegistry,
        PersonaSelector,
        PersonaSelectionContext,
        extract_tech_stack_from_files
    )
    from scripts.personas.persona_executor import PersonaReviewExecutor
    PERSONAS_AVAILABLE = True
except ImportError:
    PERSONAS_AVAILABLE = False


@dataclass
class ReviewRequest:
    """Request for code review"""
    task_id: str
    files: List[str]
    properties: List[Dict[str, Any]]
    test_results: Dict[str, Any]

    # Persona-specific fields
    use_personas: bool = False
    manual_personas: List[str] = field(default_factory=list)
    num_personas: int = 5
    task_type: Optional[str] = None
    complexity: str = "M"  # S, M, L, XL
    domain_context: List[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    """Complete review result"""
    task_id: str
    consensus: ConsensusResult
    report_path: Path

    def __str__(self) -> str:
        status = "✅ PASSED" if self.consensus.passed else "❌ FAILED"
        return f"""
Review Result: {status}

Task: {self.task_id}
Overall Score: {self.consensus.overall_score:.1f}/10
Agents: CR={self.consensus.agent_reviews['CR'].score:.1f} SEC={self.consensus.agent_reviews['SEC'].score:.1f} PERF={self.consensus.agent_reviews['PERF'].score:.1f} COMP={self.consensus.agent_reviews['COMP'].score:.1f}
Comments: {len(self.consensus.all_comments)}

Summary: {self.consensus.summary}
Report: {self.report_path}
"""


class ReviewOrchestrator:
    """
    Orchestrates consensus review.

    Supports two modes:
    1. Legacy: 4 fixed agents (CR, SEC, PERF, COMP)
    2. Persona: Intelligent selection from persona pool

    ELEGANT: Simple coordination logic.
    MULTI-TIER: Logic layer only.
    PARALLEL: Can run agents concurrently (future).
    """

    def __init__(self, personas_dir: Optional[Path] = None):
        # Legacy 4-agent system
        self.agents = {
            "CR": CodeReviewAgent(),
            "SEC": SecurityAgent(),
            "PERF": PerformanceAgent(),
            "COMP": ComplexityAgent(),
        }
        self.consensus = ConsensusAlgorithm()

        # Persona system (optional)
        self.persona_registry = None
        self.persona_selector = None
        self.persona_executor = None

        if PERSONAS_AVAILABLE:
            try:
                if personas_dir is None:
                    personas_dir = Path.home() / ".claude/skills/wfc/personas"
                self.persona_registry = PersonaRegistry(personas_dir)
                self.persona_selector = PersonaSelector(self.persona_registry)
                self.persona_executor = PersonaReviewExecutor()
            except (ImportError, FileNotFoundError, ValueError) as e:
                logger.warning("Could not initialize persona system: %s", e, exc_info=True)

    @staticmethod
    def _validate_output_path(path: Path) -> None:
        """
        Validate output path for security.

        Raises:
            ValueError: If path is unsafe or invalid
        """
        # Ensure path is absolute
        if not path.is_absolute():
            raise ValueError(f"Output path must be absolute: {path}")

        # Resolve to canonical path (eliminates .., symlinks)
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Cannot resolve path {path}: {e}")

        # Block sensitive system directories
        sensitive_dirs = [
            Path("/etc"),
            Path("/bin"),
            Path("/sbin"),
            Path("/usr/bin"),
            Path("/usr/sbin"),
            Path("/System"),  # macOS
            Path.home() / ".ssh",
            Path.home() / ".aws",
        ]

        for sensitive in sensitive_dirs:
            if resolved.is_relative_to(sensitive):
                raise ValueError(f"Cannot write to sensitive directory: {resolved}")

        # Ensure parent directory exists or can be created
        if not resolved.parent.exists():
            try:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise ValueError(f"Cannot create parent directory {resolved.parent}: {e}")

    def review(self, request: ReviewRequest, output_dir: Path) -> Union[ReviewResult, Dict[str, Any]]:
        """
        Perform complete review.

        NOTE: Persona-based reviews now use a two-phase approach:
        1. Call prepare_persona_review() to get task specs
        2. Execute Task tools for each persona (Claude Code does this)
        3. Call finalize_persona_review() with results

        Returns:
            ReviewResult: For legacy 4-agent mode (use_personas=False)
            Dict[str, Any]: For persona mode - contains task_specs, selected_personas,
                           and metadata for async Task tool execution
        """

        # Choose review mode
        if request.use_personas and self.persona_registry:
            # Return preparation data for async execution
            prep_data = self.prepare_persona_review(request)
            prep_data["output_dir"] = output_dir
            prep_data["mode"] = "persona_async"
            return prep_data
        else:
            return self._review_with_legacy_agents(request, output_dir)

    def _review_with_legacy_agents(self, request: ReviewRequest, output_dir: Path) -> ReviewResult:
        """Legacy 4-agent review (backward compatible)"""

        # Run all agents (sequential for now, parallel in future)
        reviews = []
        for agent_name, agent in self.agents.items():
            review = agent.review(request.files, request.properties, request.task_id)
            reviews.append(review)

        # Calculate consensus
        consensus = self.consensus.calculate(reviews)

        # Generate report
        report_path = output_dir / f"REVIEW-{request.task_id}.md"
        self._generate_report(request, consensus, report_path)

        return ReviewResult(
            task_id=request.task_id,
            consensus=consensus,
            report_path=report_path
        )

    def prepare_persona_review(self, request: ReviewRequest):
        """
        Phase 1: Prepare persona review by selecting personas and building task specs.

        Returns task specifications for Claude Code to execute via Task tool.
        After executing tasks, call finalize_persona_review() with results.
        """

        # Extract tech stack from files
        tech_stack = extract_tech_stack_from_files(request.files)

        # Extract property names
        property_names = [prop.get("type", "") for prop in request.properties]

        # Build selection context
        context = PersonaSelectionContext(
            task_id=request.task_id,
            files=request.files,
            tech_stack=tech_stack,
            task_type=request.task_type,
            complexity=request.complexity,
            properties=property_names,
            domain_context=request.domain_context,
            manual_personas=request.manual_personas
        )

        # Select personas
        selected = self.persona_selector.select_personas(
            context=context,
            num_personas=request.num_personas,
            require_diversity=True,
            min_relevance=0.3
        )

        logger.info("Selected %d personas for %s:", len(selected), request.task_id)
        for sp in selected:
            logger.info("  • %s (relevance: %.2f)", sp.persona.name, sp.relevance_score)
            logger.debug("    └─ %s", ', '.join(sp.selection_reasons[:2]))

        # Prepare persona review tasks for Claude Code to execute
        personas_with_relevance = [
            (sp.persona.to_dict(), sp.relevance_score)
            for sp in selected
        ]

        # Get task specifications for subagent execution
        task_specs = self.persona_executor.prepare_subagent_tasks(
            personas_with_relevance=personas_with_relevance,
            files=request.files,
            properties=request.properties
        )

        logger.info("Prepared %d persona review tasks.", len(task_specs))
        logger.debug("Task specs ready for Claude Code to execute via Task tool.")

        return {
            "task_specs": task_specs,
            "selected_personas": selected,
            "request": request
        }

    def finalize_persona_review(
        self,
        request: ReviewRequest,
        selected_personas,
        subagent_responses: List[Dict[str, Any]],
        output_dir: Path
    ) -> ReviewResult:
        """
        Phase 2: Synthesize persona reviews and generate final report.

        Call this after executing all Task tools and collecting results.

        Args:
            request: Original review request
            selected_personas: Selected personas from prepare_persona_review()
            subagent_responses: List of dicts with persona_id, persona_name, relevance_score, response
            output_dir: Directory for output files
        """

        # Parse subagent results
        persona_results = self.persona_executor.parse_subagent_results(subagent_responses)

        logger.info("Persona reviews completed:")
        for result in persona_results:
            status = "✅" if result.passed else "❌"
            logger.info("  %s %s: %.1f/10", status, result.persona_name, result.score)

        # Convert persona results to AgentReview format for consensus
        agent_reviews = self._convert_persona_results_to_agent_reviews(persona_results)

        # Build relevance scores dict for consensus weighting
        relevance_scores = {
            result.persona_id: result.relevance_score
            for result in persona_results
        }

        # Calculate consensus with relevance weighting
        consensus = self.consensus.calculate(
            reviews=agent_reviews,
            relevance_scores=relevance_scores,
            weight_by_relevance=True
        )

        # Generate report
        report_path = output_dir / f"REVIEW-{request.task_id}.md"
        self._generate_persona_report(request, consensus, selected_personas, persona_results, report_path)

        return ReviewResult(
            task_id=request.task_id,
            consensus=consensus,
            report_path=report_path
        )

    def _convert_persona_results_to_agent_reviews(self, persona_results):
        """Convert PersonaReviewResult to AgentReview format"""
        from .agents import AgentReview, AgentType, ReviewComment

        agent_reviews = []
        for result in persona_results:
            # Create a dynamic agent type
            agent_type = type('PersonaAgentType', (), {
                'name': result.persona_id,
                'value': result.persona_name
            })()

            # Convert comments
            comments = [
                ReviewComment(
                    file=c.get("file", "unknown"),
                    line=c.get("line", 0),
                    severity=c.get("severity", "info"),
                    message=c.get("message", ""),
                    suggestion=c.get("suggestion", "")
                )
                for c in result.comments
            ]

            agent_review = AgentReview(
                agent=agent_type,
                score=result.score,
                passed=result.passed,
                comments=comments,
                summary=result.summary
            )

            agent_reviews.append(agent_review)

        return agent_reviews

    def _generate_persona_report(self, request, consensus, selected_personas, persona_results, path):
        """Generate markdown review report for persona-based review"""
        lines = [
            f"# 🎯 Persona Review Report: {request.task_id}",
            "",
            f"**Status**: {'✅ APPROVED' if consensus.passed else '❌ REJECTED'}",
            f"**Overall Score**: {consensus.overall_score:.1f}/10",
            f"**Reviewers**: {len(selected_personas)} expert personas",
            "",
            "---",
            "",
            "## 👥 Selected Personas",
            "",
        ]

        # Persona selection summary
        for sp in selected_personas:
            lines.extend([
                f"### {sp.persona.name}",
                f"**Panel**: {sp.persona.panel}",
                f"**Relevance**: {sp.relevance_score:.2f}",
                f"**Selection Reasons**: {', '.join(sp.selection_reasons)}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 📝 Individual Reviews",
            "",
        ])

        # Individual persona reviews
        for result in persona_results:
            status = "✅" if result.passed else "❌"
            lines.extend([
                f"### {status} {result.persona_name}: {result.score:.1f}/10",
                f"**Summary**: {result.summary}",
                f"**Reasoning**: {result.reasoning}",
                f"**Comments**: {len(result.comments)}",
                "",
            ])

            # Show comments
            for comment in result.comments[:5]:  # Limit to top 5
                lines.extend([
                    f"#### {comment['severity'].upper()}: {comment['file']}:{comment.get('line', 0)}",
                    f"- **Issue**: {comment['message']}",
                    f"- **Fix**: {comment['suggestion']}",
                    "",
                ])

        # Consensus insights
        if consensus.consensus_areas:
            lines.extend([
                "---",
                "",
                "## 🤝 Consensus Areas",
                "",
                "Issues mentioned by multiple reviewers:",
                "",
            ])
            for area in consensus.consensus_areas:
                lines.append(f"- {area}")
            lines.append("")

        if consensus.unique_insights:
            lines.extend([
                "---",
                "",
                "## 💡 Unique Insights",
                "",
                "Critical issues caught by individual specialists:",
                "",
            ])
            for insight in consensus.unique_insights:
                lines.append(f"- {insight}")
            lines.append("")

        # Final consensus
        lines.extend([
            "---",
            "",
            "## ✨ Final Consensus",
            "",
            consensus.summary,
            "",
        ])

        # Write report
        self._validate_output_path(path)
        with open(path, 'w') as f:
            f.write('\n'.join(lines))

    def _generate_report(self, request: ReviewRequest,
                         consensus: ConsensusResult, path: Path) -> None:
        """Generate markdown review report"""
        lines = [
            f"# Code Review Report: {request.task_id}",
            "",
            f"**Status**: {'✅ APPROVED' if consensus.passed else '❌ REJECTED'}",
            f"**Overall Score**: {consensus.overall_score:.1f}/10",
            "",
            "---",
            "",
            "## Agent Reviews",
            "",
        ]

        # Agent summaries
        for agent_name, review in consensus.agent_reviews.items():
            status = "✅" if review.passed else "❌"
            lines.extend([
                f"### {status} {agent_name}: {review.agent.value}",
                f"**Score**: {review.score:.1f}/10",
                f"**Summary**: {review.summary}",
                f"**Comments**: {len(review.comments)}",
                "",
            ])

        # All comments
        if consensus.all_comments:
            lines.extend([
                "---",
                "",
                "## Detailed Comments",
                "",
            ])

            for comment in consensus.all_comments:
                lines.extend([
                    f"### {comment.severity.upper()}: {comment.file}:{comment.line}",
                    f"**Message**: {comment.message}",
                    f"**Suggestion**: {comment.suggestion}",
                    "",
                ])

        # Consensus summary
        lines.extend([
            "---",
            "",
            "## Consensus",
            "",
            consensus.summary,
            "",
        ])

        # Write report
        self._validate_output_path(path)
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
