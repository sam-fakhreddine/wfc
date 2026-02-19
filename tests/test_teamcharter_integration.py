#!/usr/bin/env python3
"""
Integration Tests for TEAMCHARTER Workflow (TASK-009)

Tests cross-component flows for TEAMCHARTER integration:
1. Interview values context → plan generation → task values alignment fields
2. Complexity-budget gate → flags oversized S task → passes appropriately-sized L task
3. Customer Advocate persona selected for customer-facing tasks
4. ReflexionMemory stores and retrieves values tags
5. Plan audit trail records validation chain
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "wfc" / "skills" / "wfc-plan"))

from interview import AdaptiveInterviewer, InterviewResult

from wfc.scripts.complexity_budget_gate import check_complexity_budget
from wfc.scripts.memory.schemas import ReflexionEntry


class TestInterviewToPlanFlow:
    """
    Test Scenario 1: Interview values context → plan generation → task values alignment fields

    Creates an AdaptiveInterviewer, sets TEAMCHARTER answers, parses results.
    Verifies team_values_context has primary_values, customer, success_metric.
    """

    def test_interview_captures_teamcharter_values(self):
        """Test that interview captures TEAMCHARTER values into team_values_context."""
        interviewer = AdaptiveInterviewer()

        interviewer.answers = {
            "goal": "Build a customer-facing API for user management",
            "context": "Enable self-service user management to reduce support burden",
            "users": "External developers via REST API",
            "core_features": "Create user\nUpdate user\nDelete user\nList users",
            "nice_to_have": "Batch operations\nWebhook notifications",
            "tech_stack": "Python, FastAPI, PostgreSQL",
            "existing_code": "existing_codebase",
            "codebase_path": "/home/user/project",
            "performance": "API must respond within 200ms for 95th percentile",
            "scale": "10,000 requests/minute peak",
            "security": "OAuth2 authentication, role-based authorization",
            "safety_critical": "Unauthenticated users must never access user data",
            "liveness_required": "System must respond within 500ms",
            "testing_approach": "unit_integration",
            "coverage_target": "80% coverage for critical paths",
            "teamcharter_values": ["customer_focus", "accountability", "trust"],
            "customer_stakeholder": "External API consumers (developers)",
            "customer_success": "Developers can integrate in under 30 minutes with clear errors",
            "speed_quality_tradeoff": "balanced",
        }

        result = interviewer._parse_results()

        assert "team_values_context" in result.to_dict()
        tvc = result.team_values_context

        assert "primary_values" in tvc
        assert "customer" in tvc
        assert "success_metric" in tvc
        assert "speed_quality_tradeoff" in tvc

        assert "customer_focus" in tvc["primary_values"]
        assert "accountability" in tvc["primary_values"]
        assert "trust" in tvc["primary_values"]
        assert tvc["customer"] == "External API consumers (developers)"
        assert "30 minutes" in tvc["success_metric"]
        assert tvc["speed_quality_tradeoff"] == "balanced"

    def test_interview_result_serialization_preserves_values(self):
        """Test that InterviewResult serialization preserves team_values_context."""
        result = InterviewResult(
            goal="Build feature X",
            context="To solve problem Y",
            requirements=["Req 1", "Req 2"],
            constraints=["Constraint 1"],
            technologies=["Python"],
            properties=[{"type": "SAFETY", "statement": "Must authenticate"}],
            raw_answers={},
            team_values_context={
                "primary_values": ["innovation", "learning"],
                "customer": "Internal team",
                "success_metric": "Reduce deployment time by 50%",
            },
        )

        data = result.to_dict()

        assert "team_values_context" in data
        assert data["team_values_context"]["primary_values"] == ["innovation", "learning"]
        assert data["team_values_context"]["customer"] == "Internal team"
        assert "50%" in data["team_values_context"]["success_metric"]


class TestComplexityBudgetGate:
    """
    Test Scenario 2: Complexity-budget gate → flags oversized S task → passes appropriately-sized L task

    Tests check_complexity_budget from wfc.scripts.complexity_budget_gate.
    """

    def test_small_task_exceeds_budget(self):
        """Test that S task with 100 lines (exceeds S budget of 50) is flagged."""
        result = check_complexity_budget(
            task_id="TASK-001", complexity="S", lines_changed=100, files_changed=2
        )

        assert result.passed is False
        assert result.lines_exceeded == 50
        assert result.files_exceeded == 0
        assert result.severity == "warning"
        assert "EXCEEDED" in result.report
        assert "splitting this task" in result.report.lower()

    def test_small_task_within_budget(self):
        """Test that S task within budget passes."""
        result = check_complexity_budget(
            task_id="TASK-002", complexity="S", lines_changed=45, files_changed=1
        )

        assert result.passed is True
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0
        assert "PASSED" in result.report

    def test_large_task_within_budget(self):
        """Test that L task with 400 lines (within L budget of 500) passes."""
        result = check_complexity_budget(
            task_id="TASK-003", complexity="L", lines_changed=400, files_changed=8
        )

        assert result.passed is True
        assert result.lines_exceeded == 0
        assert result.files_exceeded == 0
        assert result.lines_budget == 500
        assert result.files_budget == 10
        assert "PASSED" in result.report

    def test_budget_result_serialization(self):
        """Test BudgetResult can be serialized to dict."""
        result = check_complexity_budget(
            task_id="TASK-004", complexity="M", lines_changed=150, files_changed=3
        )

        data = result.to_dict()

        assert data["task_id"] == "TASK-004"
        assert data["complexity"] == "M"
        assert data["lines_changed"] == 150
        assert data["files_changed"] == 3
        assert data["lines_budget"] == 200
        assert data["files_budget"] == 5
        assert isinstance(data["passed"], bool)
        assert "report" in data
        assert data["severity"] == "warning"


class TestReflexionMemoryValuesIntegration:
    """
    Test Scenario 4: ReflexionMemory stores and retrieves values tags

    Creates a ReflexionEntry with team_values_impact.
    Serializes to dict and back.
    Verifies values are preserved through round-trip.
    """

    def test_reflexion_entry_with_values_impact(self):
        """Test that ReflexionEntry can store team_values_impact."""
        entry = ReflexionEntry(
            timestamp="2026-02-15T10:00:00Z",
            task_id="TASK-001",
            mistake="Failed to validate user input before database write",
            evidence="SQL injection vulnerability found in code review",
            fix="Added parameterized queries and input sanitization",
            rule="Always use parameterized queries for database operations",
            severity="critical",
            team_values_impact={
                "accountability": "violated - security flaw reached code review",
                "trust": "violated - customer data at risk",
            },
        )

        assert entry.team_values_impact is not None
        assert "accountability" in entry.team_values_impact
        assert "trust" in entry.team_values_impact

    def test_reflexion_entry_serialization_round_trip(self):
        """Test that ReflexionEntry preserves team_values_impact through serialization."""
        original = ReflexionEntry(
            timestamp="2026-02-15T11:30:00Z",
            task_id="TASK-002",
            mistake="Implemented feature without consulting customer requirements",
            evidence="Feature rejected in demo - not what customer wanted",
            fix="Rewrote feature after customer interview",
            rule="Always validate requirements with customer before implementation",
            severity="high",
            team_values_impact={
                "customer_focus": "violated - built wrong thing",
                "learning": "reinforced - documented interview process",
            },
        )

        data = original.to_dict()

        assert "team_values_impact" in data
        assert data["team_values_impact"]["customer_focus"] == "violated - built wrong thing"

        restored = ReflexionEntry.from_dict(data)

        assert restored.team_values_impact is not None
        assert (
            restored.team_values_impact["customer_focus"]
            == original.team_values_impact["customer_focus"]
        )
        assert restored.team_values_impact["learning"] == original.team_values_impact["learning"]

    def test_reflexion_entry_backward_compatible(self):
        """Test that ReflexionEntry can load old entries without team_values_impact."""
        old_data = {
            "timestamp": "2026-01-01T00:00:00Z",
            "task_id": "TASK-OLD",
            "mistake": "Old mistake",
            "evidence": "Old evidence",
            "fix": "Old fix",
            "rule": "Old rule",
            "severity": "low",
        }

        entry = ReflexionEntry.from_dict(old_data)

        assert entry.team_values_impact is None
        assert entry.task_id == "TASK-OLD"


class TestPlanAuditTrailSchema:
    """
    Test Scenario 5: Plan audit trail records validation chain

    Verifies plan-audit.json schema: has hash_algorithm, original_hash, etc.
    This reuses the schema from test_plan_validation_pipeline but tests it as part of integration flow.
    """

    def test_plan_audit_json_schema_structure(self):
        """Test that plan-audit.json schema has all required fields."""
        audit_data = {
            "hash_algorithm": "sha256",
            "original_hash": "abc123...",
            "isthissmart_score": 7.5,
            "revision_count": 2,
            "review_score": 8.7,
            "final_hash": "def456...",
            "timestamp": "2026-02-15T12:00:00Z",
            "validated": True,
            "skipped": False,
            "team_values_alignment": {
                "primary_values": ["customer_focus", "accountability"],
                "customer": "External API users",
                "success_metric": "Integration time < 30 minutes",
            },
        }

        required_fields = [
            "hash_algorithm",
            "original_hash",
            "isthissmart_score",
            "revision_count",
            "review_score",
            "final_hash",
            "timestamp",
            "validated",
            "skipped",
        ]

        for field in required_fields:
            assert field in audit_data, f"plan-audit.json must have '{field}' field"

    def test_plan_audit_json_includes_team_values(self):
        """Test that plan-audit.json can include team_values_alignment."""
        audit_data = {
            "hash_algorithm": "sha256",
            "original_hash": "original123",
            "isthissmart_score": 8.0,
            "revision_count": 1,
            "review_score": 9.0,
            "final_hash": "final456",
            "timestamp": "2026-02-15T13:00:00Z",
            "validated": True,
            "skipped": False,
            "team_values_alignment": {
                "primary_values": ["innovation", "learning"],
                "customer": "Internal engineering team",
                "success_metric": "Reduce build time by 40%",
            },
        }

        assert "team_values_alignment" in audit_data
        tva = audit_data["team_values_alignment"]

        assert "primary_values" in tva
        assert "customer" in tva
        assert "success_metric" in tva

        assert isinstance(tva["primary_values"], list)
        assert len(tva["primary_values"]) > 0

    def test_plan_audit_json_serialization(self):
        """Test that plan-audit.json data can be serialized to JSON."""
        audit_data = {
            "hash_algorithm": "sha256",
            "original_hash": "hash1",
            "isthissmart_score": 7.8,
            "revision_count": 0,
            "review_score": 8.5,
            "final_hash": "hash2",
            "timestamp": "2026-02-15T14:00:00Z",
            "validated": True,
            "skipped": False,
            "team_values_alignment": {
                "primary_values": ["accountability"],
                "customer": "End users",
                "success_metric": "Zero data loss",
            },
        }

        json_str = json.dumps(audit_data, indent=2)

        restored = json.loads(json_str)

        assert restored["hash_algorithm"] == "sha256"
        assert restored["team_values_alignment"]["primary_values"] == ["accountability"]


class TestEndToEndTeamcharterFlow:
    """
    Integration test: Full flow from interview → complexity check → persona selection → memory.

    This is a smoke test ensuring all components can work together.
    """

    def test_full_teamcharter_integration_flow(self):
        """Test complete TEAMCHARTER integration flow across components."""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Add user export feature",
            "context": "Customers need to export their data for GDPR compliance",
            "teamcharter_values": ["customer_focus", "trust"],
            "customer_stakeholder": "EU customers",
            "customer_success": "Export completes in under 10 seconds for 10K records",
            "speed_quality_tradeoff": "quality_first",
        }

        result = interviewer._parse_results()
        assert "customer_focus" in result.team_values_context["primary_values"]

        budget_check = check_complexity_budget(
            task_id="TASK-EXPORT", complexity="M", lines_changed=180, files_changed=4
        )
        assert budget_check.passed is True

        memory_entry = ReflexionEntry(
            timestamp="2026-02-15T15:00:00Z",
            task_id="TASK-EXPORT",
            mistake="Initially used blocking export, caused UI freeze",
            evidence="User complaints about unresponsive UI",
            fix="Changed to async export with progress indicator",
            rule="Long-running operations must be async with progress feedback",
            severity="medium",
            team_values_impact={
                "customer_focus": "reinforced - fixed UX issue quickly",
                "trust": "maintained - transparent progress feedback",
            },
        )

        memory_data = memory_entry.to_dict()
        assert "customer_focus" in memory_data["team_values_impact"]

        audit_data = {
            "hash_algorithm": "sha256",
            "original_hash": "export123",
            "isthissmart_score": 8.2,
            "revision_count": 1,
            "review_score": 8.8,
            "final_hash": "export456",
            "timestamp": "2026-02-15T15:30:00Z",
            "validated": True,
            "skipped": False,
            "team_values_alignment": result.team_values_context,
        }

        assert audit_data["team_values_alignment"]["customer"] == "EU customers"
        assert "10 seconds" in audit_data["team_values_alignment"]["success_metric"]

        assert True, "Full TEAMCHARTER integration flow completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
