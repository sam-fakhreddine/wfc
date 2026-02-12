"""
WFC Vibe - Transition Handling

SOLID: Single Responsibility - Detect transition commands and orchestrate workflow
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from .summarizer import Message, ContextSummarizer, PlanningContext
from .detector import ScopeDetector


@dataclass
class TransitionResult:
    """Result of transition attempt"""
    should_transition: bool
    target_workflow: Optional[str]  # "wfc-build" or "wfc-plan"
    context: Optional[PlanningContext]
    preview: Optional[str]


class TransitionHandler:
    """
    Detects transition commands and orchestrates workflow transitions.

    Philosophy (PROP-004):
    - Must successfully transition when user requests
    - Clear preview before transition
    - User can confirm or decline
    """

    # Transition command patterns
    TRANSITION_PHRASES = [
        "let's plan this",
        "lets plan this",
        "let's plan",
        "i want to implement this",
        "i want to implement",
        "let's build this",
        "lets build this",
        "let's build",
        "time to plan",
        "ready to implement",
        "let's make this real",
        "lets make this real",
        "start planning",
        "begin implementation"
    ]

    def __init__(self):
        self.summarizer = ContextSummarizer()

    def detect_transition_command(self, message: str) -> bool:
        """
        Detect if message contains transition command.

        Args:
            message: User message

        Returns:
            True if transition command detected
        """
        message_lower = message.lower().strip()

        # Check all transition phrases
        for phrase in self.TRANSITION_PHRASES:
            if phrase in message_lower:
                return True

        return False

    def prepare_transition(
        self,
        messages: List[Message],
        scope_detector: Optional[ScopeDetector] = None
    ) -> TransitionResult:
        """
        Prepare transition by extracting context and determining target workflow.

        Args:
            messages: Conversation history
            scope_detector: Optional scope detector with analysis

        Returns:
            TransitionResult with context and preview
        """
        # Extract context summary
        context = self.summarizer.summarize(messages, scope_detector)

        # Determine target workflow
        if self.summarizer.should_route_to_plan(context):
            target = "wfc-plan"
        else:
            target = "wfc-build"

        # Format preview
        preview = self.summarizer.format_preview(context)

        # Add confirmation prompt
        preview += f"\n\nReady to start with /{target}? (yes/no)"

        return TransitionResult(
            should_transition=True,
            target_workflow=target,
            context=context,
            preview=preview
        )

    def parse_confirmation(self, message: str) -> bool:
        """
        Parse user confirmation response.

        Args:
            message: User response

        Returns:
            True if user confirms, False if declines
        """
        message_lower = message.lower().strip()

        # Check negative first (more specific)
        negative = ["no", "n", "nope", "nah", "cancel", "not yet", "wait", "not now"]
        for phrase in negative:
            if phrase == message_lower or f" {phrase} " in f" {message_lower} ":
                return False

        # Positive confirmations
        positive = ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "let's go", "proceed"]
        if any(word in message_lower for word in positive):
            return True

        # Default: ambiguous, treat as confirmation (user said something positive-ish)
        # Better to proceed with user in control than block them
        return True

    def format_workflow_input(self, context: PlanningContext) -> str:
        """
        Format context as input for wfc-plan or wfc-build.

        Args:
            context: Planning context

        Returns:
            Formatted string for workflow input
        """
        # For wfc-build: Simple feature hint
        if context.estimated_complexity in ["S", "M"]:
            return context.goal

        # For wfc-plan: More detailed context
        lines = [f"Goal: {context.goal}"]

        if context.features:
            lines.append(f"Features: {', '.join(context.features)}")

        if context.tech_stack:
            lines.append(f"Tech: {', '.join(context.tech_stack)}")

        if context.constraints:
            lines.append(f"Constraints: {', '.join(context.constraints)}")

        return "\n".join(lines)


class TransitionOrchestrator:
    """
    Orchestrates the full transition flow from vibe to planning.

    Handles:
    1. Command detection
    2. Context extraction
    3. Preview display
    4. Confirmation
    5. Workflow invocation
    """

    def __init__(self):
        self.handler = TransitionHandler()
        self.awaiting_confirmation = False
        self.pending_transition: Optional[TransitionResult] = None

    def process_message(
        self,
        message: str,
        conversation: List[Message],
        scope_detector: Optional[ScopeDetector] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Process user message for transition handling.

        Args:
            message: User message
            conversation: Full conversation history
            scope_detector: Optional scope detector

        Returns:
            (should_respond, response_text)
            - should_respond: False if normal vibe continues
            - response_text: Transition preview or None
        """
        # Check if awaiting confirmation
        if self.awaiting_confirmation:
            confirmed = self.handler.parse_confirmation(message)

            if confirmed:
                # User confirmed - proceed with transition
                self.awaiting_confirmation = False
                return (True, self._execute_transition())
            else:
                # User declined - continue vibing
                self.awaiting_confirmation = False
                self.pending_transition = None
                return (True, "No problem! Let's keep brainstorming. 🎯")

        # Check for transition command
        if self.handler.detect_transition_command(message):
            # Prepare transition
            result = self.handler.prepare_transition(conversation, scope_detector)

            # Store pending transition
            self.pending_transition = result
            self.awaiting_confirmation = True

            # Return preview
            return (True, result.preview)

        # Normal vibe continues
        return (False, None)

    def _execute_transition(self) -> str:
        """
        Execute the pending transition.

        In reality, this would invoke wfc-plan or wfc-build.
        For now, returns instruction message.
        """
        if not self.pending_transition:
            return "Error: No pending transition"

        result = self.pending_transition
        workflow = result.target_workflow
        input_text = self.handler.format_workflow_input(result.context)

        # Clear pending transition
        self.pending_transition = None

        # Return transition instruction
        return f"✅ Transitioning to {workflow}...\n\nInput:\n```\n{input_text}\n```\n\n(In production, this would invoke `/{workflow}` automatically)"
