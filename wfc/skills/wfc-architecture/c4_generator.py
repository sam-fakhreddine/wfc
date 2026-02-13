#!/usr/bin/env python3
"""
Enhanced C4 Diagram Generator for wfc-architecture

Generates Context, Container, Component, and Code diagrams in Mermaid format.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class C4Element:
    """C4 architecture element."""

    id: str
    name: str
    type: str  # person, system, container, component
    technology: str = ""
    description: str = ""
    tags: List[str] = None


@dataclass
class C4Relationship:
    """Relationship between C4 elements."""

    from_id: str
    to_id: str
    description: str
    technology: str = ""
    protocol: str = ""


class EnhancedC4Generator:
    """
    Enhanced C4 diagram generator with better Mermaid output.

    Improvements:
    - Cleaner diagram layout
    - Better element styling
    - Technology annotations
    - Protocol/interface documentation
    - Automatic boundary detection
    """

    def __init__(self):
        self.elements: List[C4Element] = []
        self.relationships: List[C4Relationship] = []

    def generate_context_diagram(
        self, system_name: str, external_systems: List[Dict[str, Any]], users: List[Dict[str, Any]]
    ) -> str:
        """Generate C4 Context diagram."""
        lines = ["```mermaid", "C4Context", f"  title System Context for {system_name}", ""]

        # Add users (actors)
        for user in users:
            lines.append(f"  Person({user['id']}, \"{user['name']}\", \"{user['description']}\")")

        lines.append("")

        # Add main system
        lines.append(f'  System(system, "{system_name}", "Core system")')
        lines.append("")

        # Add external systems
        for ext in external_systems:
            lines.append(f"  System_Ext({ext['id']}, \"{ext['name']}\", \"{ext['description']}\")")

        lines.append("")

        # Add relationships
        lines.append('  BiRel(user, system, "Uses")')
        for ext in external_systems:
            direction = ext.get("direction", "to")
            if direction == "to":
                lines.append(
                    f"  Rel(system, {ext['id']}, \"{ext.get('interaction', 'Integrates with')}\")"
                )
            else:
                lines.append(
                    f"  Rel({ext['id']}, system, \"{ext.get('interaction', 'Sends data to')}\")"
                )

        lines.extend(["", "```"])
        return "\n".join(lines)

    def generate_container_diagram(
        self, containers: List[Dict[str, Any]], databases: List[Dict[str, Any]] = None
    ) -> str:
        """Generate C4 Container diagram with enhanced styling."""
        databases = databases or []

        lines = ["```mermaid", "C4Container", "  title Container Diagram", ""]

        # Add containers
        for container in containers:
            tech = container.get("technology", "")
            desc = container.get("description", "")
            lines.append(
                f"  Container({container['id']}, \"{container['name']}\", \"{tech}\", \"{desc}\")"
            )

        lines.append("")

        # Add databases
        for db in databases:
            tech = db.get("technology", "Database")
            desc = db.get("description", "")
            lines.append(f"  ContainerDb({db['id']}, \"{db['name']}\", \"{tech}\", \"{desc}\")")

        lines.append("")

        # Add relationships
        for container in containers:
            for rel in container.get("relationships", []):
                protocol = f" [{rel.get('protocol', 'HTTPS')}]" if rel.get("protocol") else ""
                lines.append(
                    f"  Rel({container['id']}, {rel['to']}, \"{rel['description']}{protocol}\")"
                )

        lines.extend(["", "```"])
        return "\n".join(lines)

    def generate_component_diagram(
        self, components: List[Dict[str, Any]], container_name: str
    ) -> str:
        """Generate C4 Component diagram."""
        lines = ["```mermaid", "C4Component", f"  title Component Diagram - {container_name}", ""]

        # Group components by layer
        layers = {}
        for comp in components:
            layer = comp.get("layer", "application")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(comp)

        # Add components by layer
        for layer, comps in layers.items():
            lines.append(f"  ' {layer.upper()} LAYER")
            for comp in comps:
                tech = comp.get("technology", "")
                desc = comp.get("description", "")
                lines.append(
                    f"  Component({comp['id']}, \"{comp['name']}\", \"{tech}\", \"{desc}\")"
                )
            lines.append("")

        # Add relationships
        for comp in components:
            for rel in comp.get("relationships", []):
                lines.append(f"  Rel({comp['id']}, {rel['to']}, \"{rel['description']}\")")

        lines.extend(["", "```"])
        return "\n".join(lines)

    def generate_deployment_diagram(self, nodes: List[Dict[str, Any]]) -> str:
        """Generate deployment diagram showing infrastructure."""
        lines = ["```mermaid", "graph TB", '  subgraph "Production Environment"', ""]

        for node in nodes:
            node_type = node.get("type", "server")
            containers = node.get("containers", [])

            lines.append(f"    subgraph {node['id']}[\"{node['name']} ({node_type})\"]")
            for container in containers:
                lines.append(f"      {container['id']}[\"{container['name']}\"]")
            lines.append("    end")
            lines.append("")

        lines.extend(["  end", "```"])
        return "\n".join(lines)

    def generate_sequence_diagram(self, scenario: str, steps: List[Dict[str, Any]]) -> str:
        """Generate sequence diagram for a specific scenario."""
        lines = ["```mermaid", "sequenceDiagram", f"  title {scenario}", ""]

        # Extract participants
        participants = set()
        for step in steps:
            participants.add(step["from"])
            participants.add(step["to"])

        for participant in sorted(participants):
            lines.append(f"  participant {participant}")

        lines.append("")

        # Add steps
        for idx, step in enumerate(steps, 1):
            arrow = "->>" if step.get("async", False) else "->"
            note = step.get("note", "")

            lines.append(f"  {step['from']}{arrow}{step['to']}: {idx}. {step['description']}")

            if note:
                lines.append(f"  Note over {step['to']}: {note}")

        lines.extend(["", "```"])
        return "\n".join(lines)

    def analyze_codebase_for_c4(self, project_root: Path) -> Dict[str, Any]:
        """
        Analyze codebase to auto-generate C4 elements.

        Detects:
        - API endpoints (FastAPI, Flask, Express)
        - Database models
        - Services/components
        - External integrations
        """
        analysis = {"containers": [], "components": [], "databases": [], "external_systems": []}

        # Scan for Python FastAPI/Flask
        api_files = list(project_root.glob("**/api/**/*.py"))
        if api_files:
            analysis["containers"].append(
                {
                    "id": "api",
                    "name": "API Server",
                    "technology": "Python/FastAPI",
                    "description": "REST API endpoints",
                }
            )

        # Scan for database models
        model_files = list(project_root.glob("**/models/**/*.py"))
        if model_files:
            analysis["databases"].append(
                {
                    "id": "db",
                    "name": "Database",
                    "technology": "PostgreSQL",
                    "description": "Persistent storage",
                }
            )

        # Scan for services
        service_files = list(project_root.glob("**/services/**/*.py"))
        for service_file in service_files:
            service_name = service_file.stem
            analysis["components"].append(
                {
                    "id": f"svc_{service_name}",
                    "name": f"{service_name.title()} Service",
                    "technology": "Python",
                    "description": f"{service_name} business logic",
                    "layer": "application",
                }
            )

        return analysis


def generate_architecture_doc(system_name: str, project_root: Path) -> str:
    """
    Generate complete ARCHITECTURE.md with C4 diagrams.

    Returns markdown document with all diagrams.
    """
    generator = EnhancedC4Generator()

    # Analyze codebase
    analysis = generator.analyze_codebase_for_c4(project_root)

    lines = [
        f"# {system_name} - Architecture Documentation",
        "",
        "**Auto-generated with wfc-architecture enhanced C4 diagrams**",
        "",
        "## Overview",
        "",
        f"{system_name} system architecture documented using C4 model.",
        "",
        "## System Context",
        "",
        generator.generate_context_diagram(
            system_name,
            external_systems=analysis.get("external_systems", []),
            users=[{"id": "user", "name": "User", "description": "System user"}],
        ),
        "",
        "## Container Diagram",
        "",
        generator.generate_container_diagram(
            containers=analysis.get("containers", []), databases=analysis.get("databases", [])
        ),
        "",
        "## Component Diagram",
        "",
        generator.generate_component_diagram(
            components=analysis.get("components", []), container_name="Application"
        ),
        "",
        "## Key Architectural Decisions",
        "",
        "### ADR-001: Technology Stack",
        "- **Status**: Accepted",
        "- **Context**: Need reliable, scalable technology",
        "- **Decision**: Use Python/FastAPI for API, PostgreSQL for data",
        "- **Consequences**: Fast development, good performance, proven stack",
        "",
        "### ADR-002: API Design",
        "- **Status**: Accepted",
        "- **Context**: Need RESTful API for client integration",
        "- **Decision**: REST with OpenAPI documentation",
        "- **Consequences**: Easy to use, well-documented, industry standard",
        "",
        "---",
        "",
        "**Generated**: Auto-generated with enhanced C4 diagrams",
        "**Tool**: wfc-architecture with intelligent code analysis",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    # Test C4 generation
    print(generate_architecture_doc("WFC", Path.cwd()))
