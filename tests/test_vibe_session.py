"""
Tests for WFC Vibe Session Management

Verifies message counting and reminder system (PROP-003)
"""

from wfc.scripts.orchestrators.vibe.session import VibeSession


class TestVibeSession:
    """Test vibe session state management"""

    def setup_method(self):
        """Setup test fixtures"""
        self.session = VibeSession()

    def test_session_initialization(self):
        """TEST-001: Session initializes with correct state"""
        assert self.session.state.message_count == 0
        assert self.session.state.reminder_shown == False
        assert self.session.state.scope_suggestion_shown == False
        assert 8 <= self.session.state.reminder_threshold <= 12

    def test_message_counter_increments(self):
        """TEST-002: Message counter increments correctly"""
        self.session.increment_message_count()
        assert self.session.state.message_count == 1

        self.session.increment_message_count()
        self.session.increment_message_count()
        assert self.session.state.message_count == 3

    def test_no_reminder_first_5_messages(self):
        """TEST-003: No reminder during first 5 messages (PROP-002)"""
        for i in range(5):
            self.session.increment_message_count()
            assert self.session.should_show_reminder() == False

    def test_reminder_appears_after_threshold(self):
        """TEST-004: Reminder appears after threshold (PROP-003)"""
        # Set deterministic threshold for testing
        self.session.state.reminder_threshold = 10

        for i in range(10):
            self.session.increment_message_count()

        assert self.session.should_show_reminder() == True

    def test_reminder_resets_counter(self):
        """TEST-005: Reminder resets message counter"""
        self.session.state.message_count = 10
        self.session.mark_reminder_shown()

        assert self.session.state.reminder_shown == True
        assert self.session.state.message_count == 0
        # Threshold should be randomized again
        assert 8 <= self.session.state.reminder_threshold <= 12

    def test_reminder_only_once_per_cycle(self):
        """TEST-006: Reminder shown only once per cycle"""
        self.session.state.message_count = 10
        self.session.state.reminder_threshold = 8

        # First check: should show
        assert self.session.should_show_reminder() == True

        # Mark as shown
        self.session.mark_reminder_shown()

        # Second check: should not show (counter reset)
        assert self.session.should_show_reminder() == False

    def test_passive_reminder_message(self):
        """TEST-007: Passive reminder has correct format"""
        reminder = self.session.get_passive_reminder()

        assert "💡" in reminder
        assert "let's plan this" in reminder.lower()
        assert "?" not in reminder  # Not a question (passive)

    def test_scope_suggestion_only_once(self):
        """TEST-008: Scope suggestion shown only once (PROP-006)"""
        assert self.session.should_show_scope_suggestion() == True

        self.session.mark_scope_suggestion_shown()

        assert self.session.should_show_scope_suggestion() == False

    def test_scope_suggestion_message(self):
        """TEST-009: Scope suggestion has correct format"""
        suggestion = self.session.get_scope_suggestion()

        assert "💭" in suggestion
        assert "project" in suggestion.lower() or "plan" in suggestion.lower()
        assert "?" not in suggestion  # Not a question (subtle)


class TestRandomization:
    """Test reminder randomization for naturalness"""

    def test_threshold_randomized(self):
        """TEST-010: Reminder threshold randomized (8-12)"""
        thresholds = set()

        # Create 20 sessions to get distribution
        for _ in range(20):
            session = VibeSession()
            thresholds.add(session.state.reminder_threshold)

        # Should have some variety (not always same)
        assert len(thresholds) > 1
        # All should be in valid range
        assert all(8 <= t <= 12 for t in thresholds)
