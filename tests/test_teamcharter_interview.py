"""
Test TEAMCHARTER integration in adaptive interview system.

Tests the new TEAMCHARTER questions and team_values_context extraction.
"""

import sys
from pathlib import Path

# Add wfc/skills/wfc-plan to path for hyphenated directory import
wfc_plan_path = Path(__file__).parent.parent / "wfc" / "skills" / "wfc-plan"
sys.path.insert(0, str(wfc_plan_path))

from interview import AdaptiveInterviewer, InterviewResult


class TestTEAMCHARTERQuestions:
    """Test TEAMCHARTER question integration"""

    def test_teamcharter_questions_exist(self):
        """Test that all 4 TEAMCHARTER questions are present"""
        interviewer = AdaptiveInterviewer()
        question_ids = [q.id for q in interviewer.questions]

        # Verify all 4 TEAMCHARTER questions exist
        assert "teamcharter_values" in question_ids
        assert "customer_stakeholder" in question_ids
        assert "customer_success" in question_ids
        assert "speed_quality_tradeoff" in question_ids

    def test_teamcharter_question_count(self):
        """Test that exactly 4 TEAMCHARTER questions were added"""
        interviewer = AdaptiveInterviewer()
        teamcharter_questions = [
            q
            for q in interviewer.questions
            if q.id
            in [
                "teamcharter_values",
                "customer_stakeholder",
                "customer_success",
                "speed_quality_tradeoff",
            ]
        ]
        assert len(teamcharter_questions) == 4

    def test_teamcharter_question_types(self):
        """Test that TEAMCHARTER questions have correct types"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        assert questions["teamcharter_values"].type == "multi_choice"
        assert questions["customer_stakeholder"].type == "text"
        assert questions["customer_success"].type == "text"
        assert questions["speed_quality_tradeoff"].type == "choice"

    def test_teamcharter_values_options(self):
        """Test that teamcharter_values has correct options"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        teamcharter_q = questions["teamcharter_values"]
        assert teamcharter_q.options is not None
        assert set(teamcharter_q.options) == {
            "innovation",
            "accountability",
            "teamwork",
            "learning",
            "customer_focus",
            "trust",
        }

    def test_speed_quality_tradeoff_options(self):
        """Test that speed_quality_tradeoff has correct options"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        tradeoff_q = questions["speed_quality_tradeoff"]
        assert tradeoff_q.options is not None
        assert set(tradeoff_q.options) == {"speed_first", "balanced", "quality_first"}

    def test_customer_success_dependency(self):
        """Test that customer_success depends on teamcharter_values with customer_focus condition"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        customer_success_q = questions["customer_success"]
        assert customer_success_q.depends_on == "teamcharter_values"
        assert customer_success_q.condition == "customer_focus"

    def test_customer_success_asked_when_customer_focus_selected(self):
        """Test that customer_success is asked when customer_focus is in teamcharter_values"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # Simulate selecting customer_focus in a multi_choice answer (list)
        interviewer.answers["teamcharter_values"] = ["innovation", "customer_focus"]

        customer_success_q = questions["customer_success"]
        assert interviewer.should_ask(customer_success_q) is True

    def test_customer_success_not_asked_when_customer_focus_not_selected(self):
        """Test that customer_success is NOT asked when customer_focus is NOT selected"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # Simulate NOT selecting customer_focus (list without customer_focus)
        interviewer.answers["teamcharter_values"] = ["innovation", "accountability"]

        customer_success_q = questions["customer_success"]
        assert interviewer.should_ask(customer_success_q) is False

    def test_should_ask_with_multi_choice_list_answer(self):
        """Test should_ask handles list answers (multi_choice) correctly"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # Test with customer_focus in list
        interviewer.answers["teamcharter_values"] = ["innovation", "customer_focus", "trust"]
        customer_success_q = questions["customer_success"]
        assert interviewer.should_ask(customer_success_q) is True

        # Test with customer_focus not in list
        interviewer.answers["teamcharter_values"] = ["innovation", "trust"]
        assert interviewer.should_ask(customer_success_q) is False

        # Test with customer_focus as only item
        interviewer.answers["teamcharter_values"] = ["customer_focus"]
        assert interviewer.should_ask(customer_success_q) is True

    def test_should_ask_with_scalar_answer(self):
        """Test should_ask still handles scalar answers correctly (existing_code dependency)"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # Test existing scalar dependency (existing_code -> codebase_path)
        codebase_path_q = questions["codebase_path"]

        # Scalar match
        interviewer.answers["existing_code"] = "existing_codebase"
        assert interviewer.should_ask(codebase_path_q) is True

        # Scalar no match
        interviewer.answers["existing_code"] = "new_project"
        assert interviewer.should_ask(codebase_path_q) is False

    def test_unconditional_teamcharter_questions(self):
        """Test that 3 TEAMCHARTER questions are unconditional (always asked)"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # These should have no dependencies
        assert questions["teamcharter_values"].depends_on is None
        assert questions["customer_stakeholder"].depends_on is None
        assert questions["speed_quality_tradeoff"].depends_on is None

        # These should always be asked
        assert interviewer.should_ask(questions["teamcharter_values"]) is True
        assert interviewer.should_ask(questions["customer_stakeholder"]) is True
        assert interviewer.should_ask(questions["speed_quality_tradeoff"]) is True


class TestInterviewResultTEAMCHARTER:
    """Test InterviewResult integration with TEAMCHARTER"""

    def test_interview_result_has_team_values_context_field(self):
        """Test that InterviewResult includes team_values_context field"""
        result = InterviewResult(
            goal="test goal",
            context="test context",
            requirements=["req1"],
            constraints=["const1"],
            technologies=["Python"],
            properties=[],
            raw_answers={},
            team_values_context={"primary_values": ["innovation"]},
        )

        assert hasattr(result, "team_values_context")
        assert result.team_values_context == {"primary_values": ["innovation"]}

    def test_interview_result_team_values_context_defaults_to_empty_dict(self):
        """Test that team_values_context defaults to empty dict"""
        result = InterviewResult(
            goal="test goal",
            context="test context",
            requirements=["req1"],
            constraints=["const1"],
            technologies=["Python"],
            properties=[],
            raw_answers={},
        )

        assert result.team_values_context == {}

    def test_interview_result_to_dict_includes_team_values_context(self):
        """Test that to_dict() includes team_values_context"""
        result = InterviewResult(
            goal="test goal",
            context="test context",
            requirements=["req1"],
            constraints=["const1"],
            technologies=["Python"],
            properties=[],
            raw_answers={},
            team_values_context={"customer": "Engineering Team"},
        )

        result_dict = result.to_dict()
        assert "team_values_context" in result_dict
        assert result_dict["team_values_context"] == {"customer": "Engineering Team"}

    def test_interview_result_to_dict_with_empty_team_values_context(self):
        """Test to_dict() with empty team_values_context"""
        result = InterviewResult(
            goal="test goal",
            context="test context",
            requirements=["req1"],
            constraints=["const1"],
            technologies=["Python"],
            properties=[],
            raw_answers={},
        )

        result_dict = result.to_dict()
        assert "team_values_context" in result_dict
        assert result_dict["team_values_context"] == {}


class TestParseResultsTEAMCHARTER:
    """Test _parse_results() populates team_values_context"""

    def test_parse_results_extracts_teamcharter_values_as_list(self):
        """Test that teamcharter_values is extracted as a list"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "teamcharter_values": ["innovation", "accountability"],
        }

        result = interviewer._parse_results()
        assert "primary_values" in result.team_values_context
        assert result.team_values_context["primary_values"] == ["innovation", "accountability"]

    def test_parse_results_converts_single_value_to_list(self):
        """Test that single teamcharter_value is converted to list"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "teamcharter_values": "trust",
        }

        result = interviewer._parse_results()
        assert "primary_values" in result.team_values_context
        assert result.team_values_context["primary_values"] == ["trust"]

    def test_parse_results_extracts_customer_stakeholder(self):
        """Test that customer_stakeholder is extracted"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "customer_stakeholder": "Product Team",
        }

        result = interviewer._parse_results()
        assert "customer" in result.team_values_context
        assert result.team_values_context["customer"] == "Product Team"

    def test_parse_results_extracts_customer_success(self):
        """Test that customer_success is extracted as success_metric"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "customer_success": "Reduced onboarding time by 50%",
        }

        result = interviewer._parse_results()
        assert "success_metric" in result.team_values_context
        assert result.team_values_context["success_metric"] == "Reduced onboarding time by 50%"

    def test_parse_results_extracts_speed_quality_tradeoff(self):
        """Test that speed_quality_tradeoff is extracted"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "speed_quality_tradeoff": "balanced",
        }

        result = interviewer._parse_results()
        assert "speed_quality_tradeoff" in result.team_values_context
        assert result.team_values_context["speed_quality_tradeoff"] == "balanced"

    def test_parse_results_extracts_all_teamcharter_fields(self):
        """Test that all TEAMCHARTER fields are extracted together"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "teamcharter_values": ["innovation", "customer_focus"],
            "customer_stakeholder": "Engineering Team",
            "customer_success": "API response time < 100ms",
            "speed_quality_tradeoff": "quality_first",
        }

        result = interviewer._parse_results()
        assert result.team_values_context == {
            "primary_values": ["innovation", "customer_focus"],
            "customer": "Engineering Team",
            "success_metric": "API response time < 100ms",
            "speed_quality_tradeoff": "quality_first",
        }

    def test_parse_results_empty_when_no_teamcharter_answers(self):
        """Test that team_values_context is empty when no TEAMCHARTER answers provided"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
        }

        result = interviewer._parse_results()
        assert result.team_values_context == {}

    def test_parse_results_partial_teamcharter_answers(self):
        """Test that partial TEAMCHARTER answers work correctly"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build API",
            "context": "For customers",
            "teamcharter_values": ["learning"],
            "speed_quality_tradeoff": "speed_first",
            # customer_stakeholder and customer_success not provided
        }

        result = interviewer._parse_results()
        assert result.team_values_context == {
            "primary_values": ["learning"],
            "speed_quality_tradeoff": "speed_first",
        }


class TestExistingFunctionalityRegression:
    """Test that existing questions still work (no regressions)"""

    def test_existing_questions_count_increased_by_4(self):
        """Test that question count increased by exactly 4"""
        interviewer = AdaptiveInterviewer()
        # Original questions: 15 (goal through coverage_target)
        # New questions: 4 TEAMCHARTER
        # Total: 19
        assert len(interviewer.questions) == 19

    def test_existing_core_questions_still_exist(self):
        """Test that all original questions still exist"""
        interviewer = AdaptiveInterviewer()
        question_ids = [q.id for q in interviewer.questions]

        # Original questions
        original_ids = [
            "goal",
            "context",
            "users",
            "core_features",
            "nice_to_have",
            "tech_stack",
            "existing_code",
            "codebase_path",
            "performance",
            "scale",
            "security",
            "safety_critical",
            "liveness_required",
            "testing_approach",
            "coverage_target",
        ]

        for qid in original_ids:
            assert qid in question_ids, f"Original question '{qid}' missing"

    def test_existing_parse_results_fields_still_populated(self):
        """Test that existing InterviewResult fields are still populated correctly"""
        interviewer = AdaptiveInterviewer()
        interviewer.answers = {
            "goal": "Build REST API",
            "context": "Customer needs data access",
            "core_features": "GET /users\nPOST /users",
            "tech_stack": "Python, FastAPI, PostgreSQL",
            "performance": "< 100ms response time",
            "safety_critical": "Unauthenticated users cannot access /admin",
            "liveness_required": "System must respond within 200ms",
        }

        result = interviewer._parse_results()

        # Check existing fields
        assert result.goal == "Build REST API"
        assert result.context == "Customer needs data access"
        assert "GET /users" in result.requirements
        assert "POST /users" in result.requirements
        assert "Python" in result.technologies
        assert "FastAPI" in result.technologies
        assert "Performance: < 100ms response time" in result.constraints
        assert len(result.properties) == 2
        assert result.properties[0]["type"] == "SAFETY"
        assert result.properties[1]["type"] == "LIVENESS"

    def test_existing_to_dict_fields_preserved(self):
        """Test that existing to_dict() fields are preserved"""
        result = InterviewResult(
            goal="test goal",
            context="test context",
            requirements=["req1"],
            constraints=["const1"],
            technologies=["Python"],
            properties=[{"type": "SAFETY", "statement": "test"}],
            raw_answers={"goal": "test goal"},
        )

        result_dict = result.to_dict()

        # Verify all original fields exist
        assert "goal" in result_dict
        assert "context" in result_dict
        assert "requirements" in result_dict
        assert "constraints" in result_dict
        assert "technologies" in result_dict
        assert "properties" in result_dict
        assert "raw_answers" in result_dict
        # Plus new field
        assert "team_values_context" in result_dict

    def test_existing_dependency_logic_still_works(self):
        """Test that existing question dependency logic (e.g., codebase_path) still works"""
        interviewer = AdaptiveInterviewer()
        questions = {q.id: q for q in interviewer.questions}

        # codebase_path depends on existing_code == "existing_codebase"
        codebase_path_q = questions["codebase_path"]

        # Should not be asked when no answer
        assert interviewer.should_ask(codebase_path_q) is False

        # Should not be asked when condition not met
        interviewer.answers["existing_code"] = "new_project"
        assert interviewer.should_ask(codebase_path_q) is False

        # Should be asked when condition met
        interviewer.answers["existing_code"] = "existing_codebase"
        assert interviewer.should_ask(codebase_path_q) is True
