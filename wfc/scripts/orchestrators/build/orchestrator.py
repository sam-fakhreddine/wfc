"""
WFC Build - Build Orchestrator

SOLID: Single Responsibility - Orchestrates interview → assessment → implementation flow
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .interview import QuickInterview, InterviewResult
from .complexity_assessor import ComplexityAssessor, ComplexityRating


class BuildOrchestrator:
    """
    Coordinates wfc-build workflow.

    Flow: Interview → Complexity Assessment → Implementation

    PROPERTIES:
    - PROP-001: Never bypass quality gates
    - PROP-002: Never skip consensus review
    - PROP-003: Never auto-push to remote
    - PROP-004: Always complete or fail gracefully
    - PROP-007: TDD workflow enforced
    """

    def __init__(self):
        self.interviewer = QuickInterview()
        self.assessor = ComplexityAssessor()

    def execute(self, feature_hint: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute wfc-build workflow.

        Args:
            feature_hint: Optional pre-provided feature description
            dry_run: If True, preview only (no actual implementation)

        Returns:
            Result dict with status, outputs, metrics
        """
        start_time = datetime.now()
        result = {
            "status": "unknown",
            "interview": None,
            "complexity": None,
            "implementation": None,
            "metrics": {},
            "errors": [],
        }

        try:
            # PHASE 1: Interview
            print("🎯 WFC-BUILD: Quick Feature Builder\n")
            print("[INTERVIEW]")

            interview = self.interviewer.conduct(feature_hint=feature_hint)
            result["interview"] = interview
            print(f"✅ Feature: {interview.feature_description}")
            print(f"✅ Scope: {interview.scope}")
            print(f"✅ Files: {len(interview.files_affected)} file(s)")
            print()

            # PHASE 2: Complexity Assessment
            print("[ASSESSMENT]")
            complexity = self.assessor.assess(interview)
            result["complexity"] = complexity

            print(f"✅ Complexity: {complexity.rating}")
            print(f"✅ Agent count: {complexity.agent_count}")
            print(f"✅ Rationale: {complexity.rationale}")

            # If XL, recommend wfc-plan instead
            if complexity.rating == "XL":
                print(f"\n⚠️  RECOMMENDATION: {complexity.recommendation}")
                result["status"] = "xl_recommendation"
                return result

            print()

            # PHASE 3: Implementation (if not dry-run)
            if dry_run:
                print("[DRY RUN]")
                print("✅ Preview complete - no implementation executed")
                result["status"] = "dry_run_success"
                return result

            print("[IMPLEMENTATION]")
            impl_result = self._execute_implementation(interview, complexity)
            result["implementation"] = impl_result

            if impl_result["status"] == "success":
                print("✅ Implementation complete")
                result["status"] = "success"
            else:
                print(f"❌ Implementation failed: {impl_result.get('error', 'Unknown')}")
                result["status"] = "implementation_failed"
                result["errors"].append(impl_result.get("error", "Unknown"))

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            result["status"] = "error"
            result["errors"].append(str(e))

        finally:
            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            result["metrics"]["duration_seconds"] = duration

        return result

    def _execute_implementation(
        self, interview: InterviewResult, complexity: ComplexityRating
    ) -> Dict[str, Any]:
        """
        Execute implementation via wfc-implement infrastructure.

        This is where we would:
        1. Create lightweight task spec
        2. Spawn agents (based on complexity.agent_count)
        3. Each agent follows TDD workflow
        4. Route through quality gates (PROP-001)
        5. Route through consensus review (PROP-002)
        6. Merge to local main (PROP-003 - no auto-push)

        For now, returns placeholder showing the workflow.
        """
        return {
            "status": "placeholder",
            "message": "Implementation routing not yet connected to wfc-implement",
            "would_spawn_agents": complexity.agent_count,
            "would_enforce_tdd": True,
            "would_run_quality_gates": True,
            "would_run_consensus_review": True,
            "would_merge_to_main": True,
            "would_push_to_remote": False,  # PROP-003
        }
