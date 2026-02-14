"""WFC Telemetry System - re-exports from canonical telemetry_auto module.

All consumers should import directly from wfc.shared.telemetry_auto.
This __init__.py exists for backwards compatibility only.
"""

from wfc.shared.telemetry_auto import (
    AutoTelemetry,
    get_telemetry,
    log_event,
    get_workflow_metrics,
    print_workflow_metrics,
)

__all__ = [
    "AutoTelemetry",
    "get_telemetry",
    "log_event",
    "get_workflow_metrics",
    "print_workflow_metrics",
]
