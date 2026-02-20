"""
TRAIL failure type classification.

Adds a FailureType taxonomy (Reasoning, Planning, System) alongside WFC's
existing FailureSeverity.  Classifies exceptions by type and message patterns,
then emits structured events to the observability bus.

White paper reference: E = R (Reasoning) | P (Planning) | S (System)

Fail-open: Classification errors default to UNKNOWN and never block.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from wfc.observability.instrument import emit_event, incr

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """TRAIL failure type taxonomy."""

    REASONING = "reasoning"
    PLANNING = "planning"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClassifiedFailure:
    """Result of classifying an exception into the TRAIL taxonomy."""

    failure_type: FailureType
    exception_type: str
    message: str
    retryable: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for event payloads."""
        return {
            "failure_type": self.failure_type.value,
            "exception_type": self.exception_type,
            "message": self.message,
            "retryable": self.retryable,
        }


_TYPE_MAP: dict[type, FailureType] = {
    AssertionError: FailureType.REASONING,
    ValueError: FailureType.REASONING,
    TypeError: FailureType.REASONING,
    KeyError: FailureType.REASONING,
    IndexError: FailureType.REASONING,
    ImportError: FailureType.PLANNING,
    ModuleNotFoundError: FailureType.PLANNING,
    AttributeError: FailureType.PLANNING,
    RecursionError: FailureType.PLANNING,
    OSError: FailureType.SYSTEM,
    FileNotFoundError: FailureType.SYSTEM,
    PermissionError: FailureType.SYSTEM,
    TimeoutError: FailureType.SYSTEM,
    ConnectionError: FailureType.SYSTEM,
    MemoryError: FailureType.SYSTEM,
}

_MESSAGE_PATTERNS: list[tuple[re.Pattern[str], FailureType]] = [
    (re.compile(r"timed?\s*out|timeout", re.IGNORECASE), FailureType.SYSTEM),
    (
        re.compile(r"network|connection|refused|unreachable|dns", re.IGNORECASE),
        FailureType.SYSTEM,
    ),
    (
        re.compile(r"disk\s*(full|space)|no\s*space\s*left", re.IGNORECASE),
        FailureType.SYSTEM,
    ),
    (
        re.compile(r"test\s*fail|assertion\s*fail|expected\s*\w+\s*got", re.IGNORECASE),
        FailureType.REASONING,
    ),
    (
        re.compile(r"parse\s*(error|fail)|invalid\s*(json|xml|yaml)", re.IGNORECASE),
        FailureType.REASONING,
    ),
    (
        re.compile(r"dependency|circular\s*import|resolution\s*fail", re.IGNORECASE),
        FailureType.PLANNING,
    ),
    (
        re.compile(r"max\s*(retries|iterations|recursion)\s*(exceeded|reached)", re.IGNORECASE),
        FailureType.PLANNING,
    ),
]

_RETRYABLE: dict[FailureType, bool] = {
    FailureType.SYSTEM: True,
    FailureType.PLANNING: False,
    FailureType.REASONING: False,
    FailureType.UNKNOWN: False,
}


def classify(error: BaseException) -> ClassifiedFailure:
    """Classify an exception into the TRAIL taxonomy.

    Fail-open: returns UNKNOWN on any internal error.
    """
    try:
        return _classify_impl(error)
    except Exception:
        return ClassifiedFailure(
            failure_type=FailureType.UNKNOWN,
            exception_type=type(error).__name__,
            message=str(error),
            retryable=False,
        )


def _classify_impl(error: BaseException) -> ClassifiedFailure:
    """Internal classification logic."""
    exc_type = type(error)
    message = str(error)

    ft = FailureType.UNKNOWN
    for mapped_type, mapped_ft in _TYPE_MAP.items():
        if isinstance(error, mapped_type):
            ft = mapped_ft
            break

    if ft is FailureType.UNKNOWN:
        for pattern, pattern_ft in _MESSAGE_PATTERNS:
            if pattern.search(message):
                ft = pattern_ft
                break

    return ClassifiedFailure(
        failure_type=ft,
        exception_type=exc_type.__name__,
        message=message,
        retryable=_RETRYABLE.get(ft, False),
    )


def emit_classified_failure(
    error: Any,
    source: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Classify an error and emit to the observability bus.

    Never raises -- swallows all internal errors.
    """
    try:
        if not isinstance(error, BaseException):
            error = RuntimeError(str(error))

        classified = classify(error)
        payload = classified.to_dict()
        if context:
            payload.update(context)

        emit_event(
            event_type="failure.classified",
            source=source,
            payload=payload,
            level="warning",
        )
        incr(
            "failure.classified",
            labels={
                "type": classified.failure_type.value,
                "retryable": str(classified.retryable).lower(),
            },
        )
    except Exception:
        logger.debug("Failed to emit classified failure", exc_info=True)
