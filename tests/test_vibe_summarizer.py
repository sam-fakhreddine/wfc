"""
Tests for WFC Vibe Context Summarization

Verifies context extraction and complexity estimation (PROP-005, PROP-007)
"""

import pytest
import time
from wfc.scripts.skills.vibe.summarizer import (
    ContextSummarizer, Message, PlanningContext
)
from wfc.scripts.skills.vibe.detector import ScopeDetector


class TestContextSummarizer:
    """Test context summarization logic"""

    def setup_method(self):
        """Setup test fixtures"""
        self.summarizer = ContextSummarizer()

    def test_extract_goal(self):
        """TEST-022: Extracts goal from conversation"""
        messages = [
            Message("user", "I want to build a REST API for user management"),
            Message("assistant", "What features do you need?"),
            Message("user", "Authentication and RBAC")
        ]

        context = self.summarizer.summarize(messages)

        assert "REST API" in context.goal or "user management" in context.goal

    def test_extract_features(self):
        """TEST-023: Extracts features list"""
        messages = [
            Message("user", "I need authentication"),
            Message("user", "Also RBAC and audit logging"),
            Message("user", "Plus email notifications")
        ]

        context = self.summarizer.summarize(messages)

        # Should detect multiple features
        assert len(context.features) >= 3
        assert any("auth" in f.lower() for f in context.features)

    def test_extract_tech_stack(self):
        """TEST-024: Extracts tech stack mentions"""
        messages = [
            Message("user", "Using Python with FastAPI"),
            Message("user", "PostgreSQL for database"),
            Message("user", "Redis for caching")
        ]

        context = self.summarizer.summarize(messages)

        assert len(context.tech_stack) >= 3
        assert "python" in [t.lower() for t in context.tech_stack]

    def test_extract_constraints(self):
        """TEST-025: Extracts constraints"""
        messages = [
            Message("user", "It must be secure"),
            Message("user", "Performance is critical"),
            Message("user", "Need backward compatibility")
        ]

        context = self.summarizer.summarize(messages)

        assert len(context.constraints) >= 2

    def test_complexity_estimation_simple(self):
        """TEST-026: Estimates S complexity correctly"""
        messages = [
            Message("user", "Add logging to one file")
        ]

        context = self.summarizer.summarize(messages)

        assert context.estimated_complexity == "S"

    def test_complexity_estimation_medium(self):
        """TEST-027: Estimates M complexity correctly"""
        messages = [
            Message("user", "Add auth, RBAC, and logging")
        ]

        context = self.summarizer.summarize(messages)

        assert context.estimated_complexity in ["M", "L"]

    def test_complexity_estimation_large(self):
        """TEST-028: Estimates L/XL complexity correctly"""
        messages = [
            Message("user", "Build complete user management system"),
            Message("user", "With auth, RBAC, logging, email, dashboard, API")
        ]

        context = self.summarizer.summarize(messages)

        assert context.estimated_complexity in ["L", "XL"]

    def test_routing_decision_simple(self):
        """TEST-029: Routes simple features to wfc-build"""
        context = PlanningContext(
            goal="Add logging",
            features=["logging"],
            constraints=[],
            tech_stack=[],
            files_mentioned=[],
            estimated_complexity="S",
            scope_size=1
        )

        assert self.summarizer.should_route_to_plan(context) == False

    def test_routing_decision_complex(self):
        """TEST-030: Routes complex features to wfc-plan"""
        context = PlanningContext(
            goal="Build system",
            features=["auth", "rbac", "logging", "email", "api", "dashboard"],
            constraints=[],
            tech_stack=[],
            files_mentioned=[],
            estimated_complexity="L",
            scope_size=6
        )

        assert self.summarizer.should_route_to_plan(context) == True

    def test_format_preview(self):
        """TEST-031: Formats preview for user"""
        context = PlanningContext(
            goal="Build REST API",
            features=["auth", "rbac"],
            constraints=["security"],
            tech_stack=["python", "fastapi"],
            files_mentioned=[],
            estimated_complexity="M",
            scope_size=2
        )

        preview = self.summarizer.format_preview(context)

        assert "📋" in preview
        assert "REST API" in preview
        assert "auth" in preview.lower()
        assert "M" in preview
        assert "wfc-build" in preview.lower()

    def test_filters_irrelevant_content(self):
        """TEST-032: Excludes irrelevant chat (PROP-005)"""
        messages = [
            Message("user", "I want to build an API"),
            Message("user", "Haha that's funny"),
            Message("user", "By the way, how's the weather?"),
            Message("user", "Need authentication and RBAC")
        ]

        context = self.summarizer.summarize(messages)

        # Should extract relevant features, ignore jokes/off-topic
        assert len(context.features) >= 2
        # Goal should not include irrelevant content
        assert "weather" not in context.goal.lower()
        assert "funny" not in context.goal.lower()

    def test_integration_with_scope_detector(self):
        """TEST-033: Integrates with ScopeDetector"""
        detector = ScopeDetector()
        detector.analyze_message("Need auth, RBAC, and logging")
        detector.analyze_message("Files: auth.py, user.py, role.py")

        messages = [
            Message("user", "Need auth, RBAC, and logging"),
            Message("user", "Files: auth.py, user.py, role.py")
        ]

        context = self.summarizer.summarize(messages, scope_detector=detector)

        # Should use detector's analysis
        assert len(context.features) >= 3
        assert len(context.files_mentioned) >= 3


class TestPerformance:
    """Test performance requirements (PROP-007)"""

    def test_summarization_performance(self):
        """TEST-034: Summarization completes in <5 seconds (PROP-007)"""
        summarizer = ContextSummarizer()

        # Create large conversation (50 messages)
        messages = []
        for i in range(50):
            if i % 2 == 0:
                messages.append(Message("user", f"Feature {i}: need authentication and logging"))
            else:
                messages.append(Message("assistant", "I understand, what else?"))

        start = time.time()
        context = summarizer.summarize(messages)
        duration = time.time() - start

        assert duration < 5.0  # Must complete in <5 seconds
        assert context is not None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_conversation(self):
        """TEST-035: Handles empty conversation gracefully"""
        summarizer = ContextSummarizer()
        messages = []

        context = summarizer.summarize(messages)

        assert context is not None
        assert context.goal != ""
        assert isinstance(context.features, list)

    def test_single_message(self):
        """TEST-036: Handles single message"""
        summarizer = ContextSummarizer()
        messages = [Message("user", "Build API")]

        context = summarizer.summarize(messages)

        assert context is not None
        assert "API" in context.goal

    def test_very_long_messages(self):
        """TEST-037: Handles very long messages"""
        summarizer = ContextSummarizer()
        long_text = "Build API " * 100  # Very long message
        messages = [Message("user", long_text)]

        context = summarizer.summarize(messages)

        # Goal should be truncated to reasonable length
        assert len(context.goal) < 300
