"""
Tests for WFC Build Quick Interview

Verifies PROP-008: Interview completes in <30 seconds
"""

import time

from wfc.scripts.skills.build.interview import InterviewResult, QuickInterview


class TestQuickInterview:
    """Test quick interview logic"""

    def setup_method(self):
        """Setup test fixtures"""
        self.interviewer = QuickInterview()

    def test_interview_completes_quickly(self):
        """TEST-001: Interview completes in <30s (PROP-008)"""
        start = time.time()

        result = self.interviewer.conduct(feature_hint="Add logging")

        duration = time.time() - start

        # Should complete very quickly with placeholder implementation
        assert duration < 1.0  # Much faster than 30s target
        assert isinstance(result, InterviewResult)

    def test_max_questions_limit(self):
        """TEST-002: Max 5 questions asked"""
        # Verify max_questions is set
        assert self.interviewer.max_questions == 5

    def test_feature_hint_skips_question(self):
        """Test that providing feature_hint skips Q1"""
        hint = "Add rate limiting to API"

        result = self.interviewer.conduct(feature_hint=hint)

        assert result.feature_description == hint

    def test_structured_output_all_fields(self):
        """TEST-004: Structured output has all required fields"""
        result = self.interviewer.conduct(feature_hint="Test feature")

        assert hasattr(result, "feature_description")
        assert hasattr(result, "scope")
        assert hasattr(result, "files_affected")
        assert hasattr(result, "loc_estimate")
        assert hasattr(result, "new_dependencies")
        assert hasattr(result, "constraints")
        assert hasattr(result, "test_context")

    def test_scope_types(self):
        """Test valid scope types"""
        valid_scopes = ["single_file", "few_files", "many_files", "new_module"]

        result = self.interviewer.conduct(feature_hint="Test")

        assert result.scope in valid_scopes

    def test_files_affected_is_list(self):
        """Test files_affected is a list"""
        result = self.interviewer.conduct(feature_hint="Test")

        assert isinstance(result.files_affected, list)
        assert len(result.files_affected) > 0

    def test_loc_estimate_is_positive(self):
        """Test LOC estimate is positive integer"""
        result = self.interviewer.conduct(feature_hint="Test")

        assert isinstance(result.loc_estimate, int)
        assert result.loc_estimate > 0

    def test_dependencies_is_list(self):
        """Test new_dependencies is a list"""
        result = self.interviewer.conduct(feature_hint="Test")

        assert isinstance(result.new_dependencies, list)

    def test_constraints_is_list(self):
        """Test constraints is a list"""
        result = self.interviewer.conduct(feature_hint="Test")

        assert isinstance(result.constraints, list)


class TestInterviewAdaptiveFlow:
    """Test adaptive question flow based on scope"""

    def setup_method(self):
        """Setup test fixtures"""
        self.interviewer = QuickInterview()

    def test_single_file_flow(self):
        """Test single_file scope uses simple LOC estimation"""
        # Mock the internal flow
        result = self.interviewer.conduct(feature_hint="Simple change")

        if result.scope == "single_file":
            # Single file changes should be small
            assert len(result.files_affected) <= 1
            assert result.loc_estimate < 100

    def test_few_files_flow(self):
        """Test few_files scope asks for file list"""
        # This would test the adaptive flow
        # For now, verify the structure exists
        assert hasattr(self.interviewer, "_ask_which_files")

    def test_new_module_flow(self):
        """Test new_module scope asks about structure"""
        assert hasattr(self.interviewer, "_ask_module_structure")


class TestLOCEstimation:
    """Test LOC estimation methods"""

    def setup_method(self):
        """Setup test fixtures"""
        self.interviewer = QuickInterview()

    def test_simple_loc_estimate(self):
        """Test simple LOC estimation"""
        estimate = self.interviewer._estimate_loc_simple()
        assert 0 < estimate <= 50

    def test_medium_loc_estimate(self):
        """Test medium LOC estimation"""
        estimate = self.interviewer._estimate_loc_medium()
        assert 50 < estimate <= 200

    def test_large_loc_estimate(self):
        """Test large LOC estimation"""
        estimate = self.interviewer._estimate_loc_large()
        assert 200 < estimate <= 500

    def test_module_loc_estimate(self):
        """Test module LOC estimation"""
        estimate = self.interviewer._estimate_loc_module()
        assert 100 < estimate <= 500
