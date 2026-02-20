"""Type definitions for wfc-doctor skill."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class CheckResult:
    """Result from a single health check."""

    name: str
    status: str
    issues: List[str]
    fixes_applied: List[str]


@dataclass
class HealthCheckResult:
    """Complete health check result."""

    status: str
    checks: Dict[str, CheckResult]
    report_path: Path
    timestamp: str
