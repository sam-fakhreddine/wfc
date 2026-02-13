"""
EARS (Easy Approach to Requirements Syntax) utilities for WFC.

Provides structured templates for writing clear, testable requirements.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class EARSType(Enum):
    """EARS requirement types"""

    UBIQUITOUS = "ubiquitous"  # Always active
    EVENT_DRIVEN = "event_driven"  # Triggered by event
    STATE_DRIVEN = "state_driven"  # Depends on state
    OPTIONAL = "optional"  # Conditional capability
    UNWANTED = "unwanted"  # Constraints/prevention


@dataclass
class EARSRequirement:
    """Structured EARS requirement"""

    type: EARSType
    system: str
    action: str
    trigger: Optional[str] = None  # For EVENT_DRIVEN
    state: Optional[str] = None  # For STATE_DRIVEN
    feature: Optional[str] = None  # For OPTIONAL
    condition: Optional[str] = None  # For UNWANTED
    rationale: Optional[str] = None
    priority: str = "medium"


class EARSFormatter:
    """
    Formats requirements using EARS templates.

    ELEGANT: Simple template matching.
    MULTI-TIER: Pure logic, no I/O.
    """

    @staticmethod
    def format(req: EARSRequirement) -> str:
        """Format requirement using appropriate EARS template"""

        if req.type == EARSType.UBIQUITOUS:
            return f"The {req.system} shall {req.action}"

        elif req.type == EARSType.EVENT_DRIVEN:
            return f"WHEN {req.trigger}, the {req.system} shall {req.action}"

        elif req.type == EARSType.STATE_DRIVEN:
            return f"WHILE {req.state}, the {req.system} shall {req.action}"

        elif req.type == EARSType.OPTIONAL:
            return f"WHERE {req.feature}, the {req.system} shall {req.action}"

        elif req.type == EARSType.UNWANTED:
            return f"IF {req.condition}, THEN the {req.system} shall {req.action}"

        return f"The {req.system} shall {req.action}"

    @staticmethod
    def parse_natural_language(text: str, system: str = "system") -> EARSRequirement:
        """
        Parse natural language into EARS requirement (best-effort).

        Args:
            text: Natural language requirement
            system: System name (default: "system")

        Returns:
            EARSRequirement with detected type
        """
        text_lower = text.lower()

        # Detect event-driven (when, after, on, upon)
        if any(keyword in text_lower for keyword in ["when ", "after ", "on ", "upon "]):
            # Extract trigger and action
            for keyword in ["when ", "after ", "on ", "upon "]:
                if keyword in text_lower:
                    parts = text.split(keyword, 1)
                    if len(parts) == 2:
                        trigger = parts[1].split(",")[0].strip()
                        action = (
                            parts[1].split(",", 1)[1].strip()
                            if "," in parts[1]
                            else parts[1].strip()
                        )
                        return EARSRequirement(
                            type=EARSType.EVENT_DRIVEN,
                            system=system,
                            trigger=trigger,
                            action=action,
                        )

        # Detect state-driven (while, during, as long as)
        if any(keyword in text_lower for keyword in ["while ", "during ", "as long as "]):
            for keyword in ["while ", "during ", "as long as "]:
                if keyword in text_lower:
                    parts = text.split(keyword, 1)
                    if len(parts) == 2:
                        state = parts[1].split(",")[0].strip()
                        action = (
                            parts[1].split(",", 1)[1].strip()
                            if "," in parts[1]
                            else parts[1].strip()
                        )
                        return EARSRequirement(
                            type=EARSType.STATE_DRIVEN, system=system, state=state, action=action
                        )

        # Detect unwanted (if, prevent, must not, should not)
        if any(
            keyword in text_lower for keyword in ["if ", "prevent ", "must not ", "should not "]
        ):
            # This is a constraint/prevention
            if "if " in text_lower:
                parts = text.split("if ", 1)
                if len(parts) == 2:
                    condition = parts[1].split(",")[0].split(" then")[0].strip()
                    action = (
                        parts[1].split("then", 1)[1].strip() if "then" in parts[1] else "prevent"
                    )
                    return EARSRequirement(
                        type=EARSType.UNWANTED, system=system, condition=condition, action=action
                    )

            # Generic prevention
            return EARSRequirement(
                type=EARSType.UNWANTED, system=system, condition="violation occurs", action=text
            )

        # Detect optional (if available, where supported, optional)
        if any(
            keyword in text_lower
            for keyword in ["if available", "where ", "optional", "if enabled"]
        ):
            for keyword in ["where ", "if available", "if enabled"]:
                if keyword in text_lower:
                    parts = text.split(keyword, 1)
                    if len(parts) == 2:
                        feature = parts[1].split(",")[0].strip()
                        action = (
                            parts[1].split(",", 1)[1].strip()
                            if "," in parts[1]
                            else parts[1].strip()
                        )
                        return EARSRequirement(
                            type=EARSType.OPTIONAL, system=system, feature=feature, action=action
                        )

        # Default: ubiquitous
        return EARSRequirement(type=EARSType.UBIQUITOUS, system=system, action=text)


class EARSPropertyMapper:
    """
    Maps formal properties (SAFETY, LIVENESS, etc.) to EARS templates.

    ELEGANT: Clear mapping rules.
    """

    @staticmethod
    def map_to_ears(prop_type: str, statement: str, system: str = "system") -> EARSRequirement:
        """
        Map formal property type to EARS requirement.

        Args:
            prop_type: SAFETY, LIVENESS, INVARIANT, PERFORMANCE
            statement: Property statement
            system: System name

        Returns:
            EARSRequirement with appropriate type
        """

        if prop_type == "SAFETY":
            # SAFETY → UNWANTED (prevention)
            return EARSRequirement(
                type=EARSType.UNWANTED,
                system=system,
                condition=statement,
                action="prevent and log violation",
                priority="critical",
            )

        elif prop_type == "LIVENESS":
            # LIVENESS → EVENT_DRIVEN (must eventually happen)
            return EARSRequirement(
                type=EARSType.EVENT_DRIVEN,
                system=system,
                trigger="required condition occurs",
                action=statement,
                priority="high",
            )

        elif prop_type == "INVARIANT":
            # INVARIANT → STATE_DRIVEN (must always be true)
            return EARSRequirement(
                type=EARSType.STATE_DRIVEN,
                system=system,
                state="system is running",
                action=f"maintain {statement}",
                priority="high",
            )

        elif prop_type == "PERFORMANCE":
            # PERFORMANCE → UBIQUITOUS or STATE_DRIVEN
            return EARSRequirement(
                type=EARSType.UBIQUITOUS, system=system, action=statement, priority="medium"
            )

        # Default: ubiquitous
        return EARSRequirement(type=EARSType.UBIQUITOUS, system=system, action=statement)


def generate_acceptance_criteria_ears(requirement: str, system: str = "system") -> List[str]:
    """
    Generate EARS-formatted acceptance criteria from a requirement.

    Args:
        requirement: Natural language requirement
        system: System name

    Returns:
        List of EARS-formatted acceptance criteria
    """
    # Parse requirement into EARS
    ears_req = EARSFormatter.parse_natural_language(requirement, system)

    criteria = []

    # Always include the main EARS requirement
    criteria.append(EARSFormatter.format(ears_req))

    # Add type-specific criteria
    if ears_req.type == EARSType.EVENT_DRIVEN:
        criteria.append(f"WHEN {ears_req.trigger} occurs multiple times, behavior is consistent")
        criteria.append(f"WHEN {ears_req.trigger} does NOT occur, no action is taken")

    elif ears_req.type == EARSType.STATE_DRIVEN:
        criteria.append(f"WHEN {ears_req.state} becomes false, the action stops")
        criteria.append(f"WHILE {ears_req.state}, the action is continuous")

    elif ears_req.type == EARSType.UNWANTED:
        criteria.append(f"IF {ears_req.condition} is prevented, system logs the attempt")
        criteria.append(f"System recovers gracefully from {ears_req.condition}")

    elif ears_req.type == EARSType.OPTIONAL:
        criteria.append(f"WHERE {ears_req.feature} is disabled, system functions without it")
        criteria.append(f"Feature {ears_req.feature} can be toggled without system restart")

    # Universal criteria
    criteria.append("Implementation is testable and verifiable")
    criteria.append("Edge cases are handled correctly")

    return criteria
