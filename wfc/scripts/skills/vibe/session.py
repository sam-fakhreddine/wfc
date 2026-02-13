"""
WFC Vibe - Session Management

SOLID: Single Responsibility - Manages vibe session state
"""

import random
from dataclasses import dataclass


@dataclass
class VibeState:
    """Minimal vibe session state"""

    message_count: int = 0
    reminder_shown: bool = False
    scope_suggestion_shown: bool = False
    reminder_threshold: int = 10


class VibeSession:
    """
    Manages vibe session state with minimal overhead.

    Philosophy:
    - No persistence (session-based only)
    - Minimal state (message count + flags)
    - Natural feel (randomized reminders)
    """

    def __init__(self):
        self.state = VibeState()
        self._set_random_reminder_threshold()

    def _set_random_reminder_threshold(self):
        """Set randomized reminder threshold (8-12 for naturalness)"""
        self.state.reminder_threshold = random.randint(8, 12)

    def increment_message_count(self):
        """Increment message counter per user message"""
        self.state.message_count += 1

    def should_show_reminder(self) -> bool:
        """
        Determine if passive reminder should be shown.

        Rules (PROP-003):
        - No reminder in first 5 messages
        - Show reminder at threshold (8-12 messages)
        - Only show once per threshold period
        """
        if self.state.message_count < 5:
            return False  # Don't interrupt early conversation

        if self.state.reminder_shown:
            return False  # Already shown this cycle

        return self.state.message_count >= self.state.reminder_threshold

    def mark_reminder_shown(self):
        """Reset after showing reminder"""
        self.state.reminder_shown = True
        self.state.message_count = 0  # Reset counter
        self._set_random_reminder_threshold()  # New random threshold

    def should_show_scope_suggestion(self) -> bool:
        """
        Determine if scope suggestion should be shown.

        Rules (PROP-006):
        - Max 1 suggestion per conversation
        """
        return not self.state.scope_suggestion_shown

    def mark_scope_suggestion_shown(self):
        """Mark scope suggestion as shown"""
        self.state.scope_suggestion_shown = True

    def get_passive_reminder(self) -> str:
        """
        Get passive reminder message.

        Style: Subtle, not pushy
        """
        return "💡 *Tip: Say 'let's plan this' anytime to move to implementation*"

    def get_scope_suggestion(self) -> str:
        """
        Get scope suggestion message.

        Style: Thoughtful, not eager
        """
        return "💭 *This is growing into a sizable project. Consider using /wfc-plan to structure it when ready.*"
