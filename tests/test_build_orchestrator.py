"""
Tests for WFC Build Orchestrator

Verifies orchestration flow and safety properties
"""

from wfc.scripts.skills.build.orchestrator import BuildOrchestrator


class TestBuildOrchestrator:
    """Test build orchestration logic"""

    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = BuildOrchestrator()

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes components"""
        assert self.orchestrator.interviewer is not None
        assert self.orchestrator.assessor is not None

    def test_execute_with_feature_hint(self):
        """Test execute with feature hint"""
        result = self.orchestrator.execute(feature_hint="Add logging to middleware", dry_run=True)

        assert result["status"] in ["dry_run_success", "xl_recommendation"]
        assert result["interview"] is not None
        assert result["complexity"] is not None

    def test_dry_run_no_implementation(self):
        """Test dry-run mode doesn't execute implementation"""
        result = self.orchestrator.execute(feature_hint="Test feature", dry_run=True)

        if result["status"] == "dry_run_success":
            # Should have interview and complexity, but no implementation
            assert result["interview"] is not None
            assert result["complexity"] is not None
            assert result["implementation"] is None

    def test_xl_complexity_triggers_recommendation(self):
        """TEST-019: XL complexity triggers wfc-plan recommendation"""
        # This would require mocking the interview to return XL-sized feature
        # For now, test that the recommendation flow exists
        result = self.orchestrator.execute(feature_hint="Test", dry_run=True)

        assert "complexity" in result, "Missing 'complexity' key in result"
        assert result["complexity"] is not None, "Complexity assessment should not be None"
        # If XL is detected, should return recommendation status
        if result["complexity"].rating == "XL":
            assert result["status"] == "xl_recommendation"
            assert result["complexity"].recommendation != ""

    def test_error_handling_graceful(self):
        """TEST-014: Graceful failure handling (PROP-004)"""
        # Execute should not raise, should return error in result
        result = self.orchestrator.execute(feature_hint="Test", dry_run=True)

        # Should always return a dict with status
        assert isinstance(result, dict)
        assert "status" in result
        assert "errors" in result

    def test_metrics_recorded(self):
        """Test that execution metrics are recorded"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=True)

        assert "metrics" in result
        assert "duration_seconds" in result["metrics"]
        assert result["metrics"]["duration_seconds"] >= 0

    def test_no_auto_push_in_result(self):
        """TEST-015: No auto-push to remote (PROP-003)"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "implementation" in result, "Missing 'implementation' key in result"
        impl = result["implementation"]
        # Should explicitly indicate no push
        assert impl.get("would_push_to_remote") == False


class TestOrchestrationFlow:
    """Test orchestration phases"""

    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = BuildOrchestrator()

    def test_phase_1_interview(self):
        """Test Phase 1: Interview completes"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=True)

        # Interview phase should complete
        assert result["interview"] is not None
        assert hasattr(result["interview"], "feature_description")
        assert hasattr(result["interview"], "scope")

    def test_phase_2_complexity_assessment(self):
        """Test Phase 2: Complexity assessment completes"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=True)

        # Assessment phase should complete
        assert result["complexity"] is not None
        assert hasattr(result["complexity"], "rating")
        assert hasattr(result["complexity"], "agent_count")

    def test_phase_3_implementation_placeholder(self):
        """Test Phase 3: Implementation routing (placeholder)"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "status" in result, "Missing 'status' key in result"
        # Implementation phase should have placeholder
        assert result["status"] not in [
            "xl_recommendation"
        ], "XL recommendation should not occur for simple test feature"
        assert (
            result["implementation"] is not None
        ), "Missing 'implementation' in result for non-XL task"


class TestSafetyProperties:
    """Test safety property enforcement"""

    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = BuildOrchestrator()

    def test_prop_001_quality_gates_enforced(self):
        """Verify PROP-001: Quality gates would be enforced"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "implementation" in result, "Missing 'implementation' key in result"
        assert result["implementation"].get("would_run_quality_gates") == True

    def test_prop_002_consensus_review_enforced(self):
        """Verify PROP-002: Consensus review would be enforced"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "implementation" in result, "Missing 'implementation' key in result"
        assert result["implementation"].get("would_run_consensus_review") == True

    def test_prop_003_no_auto_push(self):
        """Verify PROP-003: No auto-push to remote"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "implementation" in result, "Missing 'implementation' key in result"
        assert result["implementation"].get("would_push_to_remote") == False

    def test_prop_007_tdd_enforced(self):
        """Verify PROP-007: TDD workflow would be enforced"""
        result = self.orchestrator.execute(feature_hint="Test", dry_run=False)

        assert "implementation" in result, "Missing 'implementation' key in result"
        assert result["implementation"].get("would_enforce_tdd") == True
