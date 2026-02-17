"""
WFC Property Schema - ELEGANT & SIMPLE

Defines the structure for formal properties (SAFETY, LIVENESS, INVARIANT, PERFORMANCE)
used across WFC skills.

Design: Simple dataclasses, no magic, clear validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PropertyType(Enum):
    """Property types following formal verification categories."""

    SAFETY = "SAFETY"  # "Bad things never happen"
    LIVENESS = "LIVENESS"  # "Good things eventually happen"
    INVARIANT = "INVARIANT"  # "This always holds true"
    PERFORMANCE = "PERFORMANCE"  # "Within these bounds"


@dataclass
class Property:
    """
    A formal property that the system must satisfy.

    Used by: wfc-plan, wfc-implement, wfc-test, wfc-observe
    """

    id: str  # e.g., "PROP-001"
    type: PropertyType  # SAFETY, LIVENESS, INVARIANT, PERFORMANCE
    statement: str  # Human-readable property statement
    rationale: str  # Why this property matters

    # Optional fields
    formal_spec: Optional[str] = None  # Formal logic specification (if applicable)
    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Links to other artifacts
    requirements: List[str] = field(default_factory=list)  # FR-001, NFR-002, etc.
    tests: List[str] = field(default_factory=list)  # Test IDs that verify this
    tasks: List[str] = field(default_factory=list)  # TASK-001, etc.

    def __post_init__(self):
        """Validate property on creation."""
        if not self.id.startswith("PROP-"):
            raise ValueError(f"Property ID must start with 'PROP-': {self.id}")

        if not self.statement.strip():
            raise ValueError(f"Property {self.id} must have a non-empty statement")

        if not self.rationale.strip():
            raise ValueError(f"Property {self.id} must have a non-empty rationale")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "statement": self.statement,
            "rationale": self.rationale,
            "formal_spec": self.formal_spec,
            "acceptance_criteria": self.acceptance_criteria,
            "tags": self.tags,
            "requirements": self.requirements,
            "tests": self.tests,
            "tasks": self.tasks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Property":
        """Create Property from dictionary."""
        data = data.copy()
        data["type"] = PropertyType(data["type"])
        return cls(**data)


@dataclass
class PropertySet:
    """
    A collection of properties for a project.

    Used by: wfc-plan (creates), wfc-implement (consumes), wfc-test (verifies)
    """

    properties: List[Property] = field(default_factory=list)

    def add(self, prop: Property) -> None:
        """Add a property to the set."""
        # Ensure no duplicate IDs
        if any(p.id == prop.id for p in self.properties):
            raise ValueError(f"Property {prop.id} already exists")
        self.properties.append(prop)

    def get(self, prop_id: str) -> Optional[Property]:
        """Get property by ID."""
        return next((p for p in self.properties if p.id == prop_id), None)

    def by_type(self, prop_type: PropertyType) -> List[Property]:
        """Get all properties of a given type."""
        return [p for p in self.properties if p.type == prop_type]

    def by_task(self, task_id: str) -> List[Property]:
        """Get all properties linked to a task."""
        return [p for p in self.properties if task_id in p.tasks]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"properties": [p.to_dict() for p in self.properties]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertySet":
        """Create PropertySet from dictionary."""
        props = [Property.from_dict(p) for p in data.get("properties", [])]
        return cls(properties=props)


# Example usage
if __name__ == "__main__":
    # Create a property
    prop = Property(
        id="PROP-001",
        type=PropertyType.SAFETY,
        statement="Unauthenticated user must never access protected endpoints",
        rationale="Security: prevent unauthorized data access",
        acceptance_criteria=[
            "All protected endpoints reject requests without valid auth token",
            "Auth middleware runs before any protected handler",
            "Token validation includes expiry and signature checks",
        ],
        requirements=["FR-001", "NFR-002"],
        tags=["security", "authentication"],
    )

    print(f"Property: {prop.id} ({prop.type.value})")
    print(f"Statement: {prop.statement}")
    print(f"Dict: {prop.to_dict()}")
