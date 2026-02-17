"""
Tests for WFC Vibe Transition Handling

Verifies command detection and workflow orchestration (PROP-004)
"""

from wfc.scripts.skills.vibe.detector import ScopeDetector
from wfc.scripts.skills.vibe.summarizer import Message
from wfc.scripts.skills.vibe.transitions import (
    TransitionHandler,
    TransitionOrchestrator,
)


class TestTransitionHandler:
    """Test transition command detection"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = TransitionHandler()

    def test_detect_lets_plan_this(self):
        """TEST-038: Detects 'let's plan this'"""
        assert self.handler.detect_transition_command("let's plan this") == True
        assert self.handler.detect_transition_command("lets plan this") == True

    def test_detect_i_want_to_implement(self):
        """TEST-039: Detects 'I want to implement this'"""
        assert self.handler.detect_transition_command("I want to implement this") == True
        assert self.handler.detect_transition_command("i want to implement") == True

    def test_detect_lets_build_this(self):
        """TEST-040: Detects 'let's build this'"""
        assert self.handler.detect_transition_command("let's build this") == True
        assert self.handler.detect_transition_command("lets build this") == True

    def test_detect_all_variants(self):
        """TEST-041: Detects all transition phrase variants"""
        phrases = [
            "time to plan",
            "ready to implement",
            "let's make this real",
            "start planning",
            "begin implementation",
        ]

        for phrase in phrases:
            assert self.handler.detect_transition_command(phrase) == True

    def test_no_false_positives(self):
        """TEST-042: No false positives on normal chat"""
        messages = [
            "I'm thinking about this",
            "What do you think?",
            "This is interesting",
            "Let's discuss more",
        ]

        for msg in messages:
            assert self.handler.detect_transition_command(msg) == False

    def test_prepare_transition_simple(self):
        """TEST-043: Prepares transition for simple feature"""
        messages = [Message("user", "I want to add logging")]

        result = self.handler.prepare_transition(messages)

        assert result.should_transition == True
        assert result.target_workflow == "wfc-build"
        assert result.context is not None
        assert result.preview is not None
        assert "wfc-build" in result.preview.lower()

    def test_prepare_transition_complex(self):
        """TEST-044: Prepares transition for complex feature"""
        messages = [
            Message("user", "Build complete system"),
            Message("user", "With auth, RBAC, logging, email, API, dashboard"),
        ]

        result = self.handler.prepare_transition(messages)

        assert result.should_transition == True
        assert result.target_workflow == "wfc-plan"
        assert result.context is not None
        assert "wfc-plan" in result.preview.lower()

    def test_preview_contains_key_info(self):
        """TEST-045: Preview contains goal, features, complexity"""
        messages = [Message("user", "Build API with auth and RBAC")]

        result = self.handler.prepare_transition(messages)

        preview = result.preview

        assert "📋" in preview
        assert "Goal:" in preview or "goal" in preview.lower()
        assert "Features:" in preview or "features" in preview.lower()
        assert "Complexity:" in preview or "complexity" in preview.lower()

    def test_parse_confirmation_positive(self):
        """TEST-046: Parses positive confirmations"""
        positive_responses = [
            "yes",
            "y",
            "yeah",
            "yep",
            "sure",
            "ok",
            "okay",
            "let's go",
            "proceed",
        ]

        for response in positive_responses:
            assert self.handler.parse_confirmation(response) == True

    def test_parse_confirmation_negative(self):
        """TEST-047: Parses negative confirmations"""
        negative_responses = ["no", "n", "nope", "nah", "cancel", "not yet", "wait"]

        for response in negative_responses:
            assert self.handler.parse_confirmation(response) == False

    def test_format_workflow_input_simple(self):
        """TEST-048: Formats input for wfc-build"""
        from wfc.scripts.skills.vibe.summarizer import PlanningContext

        context = PlanningContext(
            goal="Add logging to API",
            features=["logging"],
            constraints=[],
            tech_stack=[],
            files_mentioned=[],
            estimated_complexity="S",
            scope_size=1,
        )

        input_text = self.handler.format_workflow_input(context)

        assert "Add logging" in input_text

    def test_format_workflow_input_complex(self):
        """TEST-049: Formats input for wfc-plan"""
        from wfc.scripts.skills.vibe.summarizer import PlanningContext

        context = PlanningContext(
            goal="Build user management system",
            features=["auth", "rbac", "logging"],
            constraints=["security"],
            tech_stack=["python", "fastapi"],
            files_mentioned=[],
            estimated_complexity="L",
            scope_size=3,
        )

        input_text = self.handler.format_workflow_input(context)

        assert "Goal:" in input_text
        assert "Features:" in input_text
        assert "auth" in input_text.lower()


class TestTransitionOrchestrator:
    """Test full transition orchestration flow"""

    def setup_method(self):
        """Setup test fixtures"""
        self.orchestrator = TransitionOrchestrator()

    def test_normal_message_no_transition(self):
        """TEST-050: Normal messages continue vibe"""
        messages = [Message("user", "I'm thinking about this")]

        should_respond, response = self.orchestrator.process_message("What do you think?", messages)

        assert should_respond == False
        assert response is None

    def test_transition_command_shows_preview(self):
        """TEST-051: Transition command shows preview"""
        messages = [Message("user", "I want to build an API with auth")]

        should_respond, response = self.orchestrator.process_message("let's plan this", messages)

        assert should_respond == True
        assert response is not None
        assert "📋" in response
        assert self.orchestrator.awaiting_confirmation == True

    def test_user_confirms_transition(self):
        """TEST-052: User confirmation proceeds with transition"""
        messages = [Message("user", "Build API")]

        # First: trigger transition
        self.orchestrator.process_message("let's plan this", messages)

        # Then: confirm
        should_respond, response = self.orchestrator.process_message("yes", messages)

        assert should_respond == True
        assert "Transitioning" in response or "transition" in response.lower()
        assert self.orchestrator.awaiting_confirmation == False

    def test_user_declines_transition(self):
        """TEST-053: User decline continues vibe (PROP-001)"""
        messages = [Message("user", "Build API")]

        # First: trigger transition
        self.orchestrator.process_message("let's plan this", messages)

        # Then: decline
        should_respond, response = self.orchestrator.process_message("no", messages)

        assert should_respond == True
        assert "brainstorm" in response.lower() or "vibe" in response.lower()
        assert self.orchestrator.awaiting_confirmation == False
        assert self.orchestrator.pending_transition is None


class TestIntegration:
    """Test integration with other components"""

    def test_integration_with_scope_detector(self):
        """TEST-054: Uses scope detector analysis"""
        handler = TransitionHandler()
        detector = ScopeDetector()

        # Populate detector
        detector.analyze_message("Need auth, RBAC, logging, email")

        messages = [Message("user", "Need auth, RBAC, logging, email")]

        result = handler.prepare_transition(messages, scope_detector=detector)

        assert result.context.scope_size >= 3
