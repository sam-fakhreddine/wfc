"""
PROPERTIES.md Generator

Extracts formal properties from interview results.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
from .interview import InterviewResult
from .ears import EARSPropertyMapper, EARSFormatter


@dataclass
class Property:
    """Single formal property"""
    id: str
    type: str  # SAFETY, LIVENESS, INVARIANT, PERFORMANCE
    statement: str
    rationale: str
    priority: str  # critical, high, medium, low
    observables: List[str]


class PropertiesGenerator:
    """
    Generates PROPERTIES.md from interview results.

    Extracts formal properties (SAFETY, LIVENESS, INVARIANT, PERFORMANCE).
    """

    def __init__(self, interview_result: InterviewResult):
        self.result = interview_result
        self.properties: List[Property] = []
        self.prop_counter = 1

    def generate(self) -> str:
        """Generate complete PROPERTIES.md content"""
        self._extract_properties()
        return self._render_markdown()

    def _extract_properties(self) -> None:
        """Extract properties from interview results"""

        # Properties from interview
        for prop_data in self.result.properties:
            self.properties.append(Property(
                id=self._next_id(),
                type=prop_data.get("type", "INVARIANT"),
                statement=prop_data.get("statement", ""),
                rationale=f"User requirement: {prop_data.get('statement', '')}",
                priority=prop_data.get("priority", "medium"),
                observables=self._suggest_observables(prop_data.get("type", "INVARIANT"))
            ))

        # Infer additional properties from constraints
        for constraint in self.result.constraints:
            if "Performance" in constraint:
                self.properties.append(Property(
                    id=self._next_id(),
                    type="PERFORMANCE",
                    statement=constraint,
                    rationale="Performance requirement",
                    priority="high",
                    observables=["response_time_ms", "throughput_rps"]
                ))
            elif "Security" in constraint:
                self.properties.append(Property(
                    id=self._next_id(),
                    type="SAFETY",
                    statement=constraint,
                    rationale="Security requirement",
                    priority="critical",
                    observables=["auth_failures", "unauthorized_access_attempts"]
                ))

    def _next_id(self) -> str:
        """Generate next property ID"""
        prop_id = f"PROP-{self.prop_counter:03d}"
        self.prop_counter += 1
        return prop_id

    def _suggest_observables(self, prop_type: str) -> List[str]:
        """Suggest observables for property type"""
        mapping = {
            "SAFETY": ["error_count", "assertion_failures", "security_violations"],
            "LIVENESS": ["health_check_status", "response_times", "timeout_count"],
            "INVARIANT": ["data_integrity_checks", "state_validation"],
            "PERFORMANCE": ["latency_p99", "throughput", "resource_utilization"],
        }
        return mapping.get(prop_type, [])

    def _render_markdown(self) -> str:
        """Render properties as markdown with EARS format"""
        lines = [
            "# Formal Properties",
            "",
            "Properties that must hold across the implementation.",
            "",
            "**Format**: Using [EARS](https://alistairmavin.com/ears/) (Easy Approach to Requirements Syntax)",
            "",
            "---",
            "",
        ]

        for prop in self.properties:
            # Convert property to EARS format
            ears_req = EARSPropertyMapper.map_to_ears(
                prop.type,
                prop.statement,
                system=self.result.goal if hasattr(self.result, 'goal') else "system"
            )
            ears_formatted = EARSFormatter.format(ears_req)

            lines.extend([
                f"## {prop.id}: {prop.type}",
                f"- **EARS Statement**: {ears_formatted}",
                f"- **Original**: {prop.statement}",
                f"- **Rationale**: {prop.rationale}",
                f"- **Priority**: {prop.priority}",
                f"- **Observables**: {', '.join(prop.observables)}",
                "",
            ])

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save PROPERTIES.md to file"""
        content = self.generate()
        with open(path, 'w') as f:
            f.write(content)
