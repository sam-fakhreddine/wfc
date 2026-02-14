"""
Tests for WFC Vibe Scope Detection

Verifies smart detection of growing scope (PROP-006)
"""

from wfc.scripts.skills.vibe.detector import ScopeDetector


class TestScopeDetector:
    """Test scope detection heuristics"""

    def setup_method(self):
        """Setup test fixtures"""
        self.detector = ScopeDetector()

    def test_detector_initialization(self):
        """TEST-011: Detector initializes empty"""
        assert len(self.detector.features_mentioned) == 0
        assert len(self.detector.files_mentioned) == 0
        assert self.detector.architecture_keyword_count == 0
        assert self.detector.complexity_indicator_count == 0

    def test_detect_multiple_features(self):
        """TEST-012: Detects multiple distinct features"""
        messages = [
            "I want to add user authentication",
            "We also need role-based access control",
            "Plus audit logging would be good",
            "And email notifications",
        ]

        for msg in messages:
            self.detector.analyze_message(msg)

        assert len(self.detector.features_mentioned) >= 3
        assert self.detector.is_scope_growing_large() == True

    def test_detect_architecture_keywords(self):
        """TEST-013: Detects architecture discussion"""
        messages = [
            "We need to integrate with the existing system",
            "The architecture should support microservices",
        ]

        for msg in messages:
            self.detector.analyze_message(msg)

        assert self.detector.architecture_keyword_count >= 2
        assert self.detector.is_scope_growing_large() == True

    def test_detect_file_mentions(self):
        """TEST-014: Detects file/module mentions"""
        messages = [
            "We need auth.py for authentication",
            "Also user.py, role.py, and permission.py",
            "Plus middleware.py and database.py",
        ]

        for msg in messages:
            self.detector.analyze_message(msg)

        assert len(self.detector.files_mentioned) >= 5
        assert self.detector.is_scope_growing_large() == True

    def test_detect_complexity_indicators(self):
        """TEST-015: Detects complexity indicators"""
        messages = ["We should refactor the entire auth system", "And migrate to a new database"]

        for msg in messages:
            self.detector.analyze_message(msg)

        assert self.detector.complexity_indicator_count >= 2
        assert self.detector.is_scope_growing_large() == True

    def test_no_false_positives_simple_chat(self):
        """TEST-016: No false positives on simple conversation"""
        messages = ["Hello, how are you?", "I'm thinking about my project", "Just exploring ideas"]

        for msg in messages:
            self.detector.analyze_message(msg)

        assert self.detector.is_scope_growing_large() == False

    def test_scope_summary(self):
        """TEST-017: Scope summary provides complete info"""
        self.detector.analyze_message("I want to add auth, RBAC, and logging")

        summary = self.detector.get_scope_summary()

        assert "features" in summary
        assert "files" in summary
        assert "architecture_keywords" in summary
        assert "complexity_indicators" in summary
        assert "scope_growing" in summary
        assert isinstance(summary["scope_growing"], bool)


class TestDetectionThresholds:
    """Test detection threshold boundaries"""

    def test_exactly_3_features_no_trigger(self):
        """TEST-018: Exactly 3 features doesn't trigger (need >3)"""
        detector = ScopeDetector()

        # Manually set features to test boundary
        detector.features_mentioned = {"auth", "rbac", "logging"}

        # Should NOT trigger (need >3)
        assert detector.is_scope_growing_large() == False

    def test_4_features_triggers(self):
        """TEST-019: 4 features triggers detection"""
        detector = ScopeDetector()

        detector.features_mentioned = {"auth", "rbac", "logging", "email"}

        assert detector.is_scope_growing_large() == True

    def test_exactly_5_files_no_trigger(self):
        """TEST-020: Exactly 5 files doesn't trigger (need >5)"""
        detector = ScopeDetector()

        detector.files_mentioned = {f"file{i}.py" for i in range(5)}

        assert detector.is_scope_growing_large() == False

    def test_6_files_triggers(self):
        """TEST-021: 6 files triggers detection"""
        detector = ScopeDetector()

        detector.files_mentioned = {f"file{i}.py" for i in range(6)}

        assert detector.is_scope_growing_large() == True
