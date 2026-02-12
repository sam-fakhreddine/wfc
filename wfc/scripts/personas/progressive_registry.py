"""
Progressive Disclosure Persona Registry

Implements lightweight persona loading for both Claude Code and Kiro:
- Loads minimal registry (IDs + summaries) initially
- Fetches full persona details on-demand
- Reduces initial context from ~50K to ~3K tokens

Compatible with:
- Claude Code (uses Read tool for on-demand loading)
- Kiro (progressive disclosure pattern)
- Any Agent Skills compliant platform
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PersonaSummary:
    """Lightweight persona metadata for registry"""
    id: str
    name: str
    panel: str
    skills: List[str]
    description: str  # Short 1-line description

    @property
    def summary_tokens(self) -> int:
        """Estimate token count for summary"""
        return len(self.id) + len(self.name) + len(self.description) + 20


class ProgressiveRegistry:
    """
    Lightweight persona registry with on-demand loading.

    Usage:
        registry = ProgressiveRegistry()

        # Initial load: ~3K tokens (summaries only)
        summaries = registry.get_all_summaries()

        # On-demand: Load full details when selected
        persona = registry.load_persona("APPSEC_SPECIALIST")
    """

    def __init__(self, personas_dir: Optional[Path] = None):
        self.personas_dir = personas_dir or self._get_default_personas_dir()
        self._summary_cache: Dict[str, PersonaSummary] = {}
        self._full_cache: Dict[str, dict] = {}

    def _get_default_personas_dir(self) -> Path:
        """Find personas directory (works in Claude Code and Kiro)"""
        # Try multiple locations
        locations = [
            Path.home() / ".claude" / "skills" / "wfc" / "personas",
            Path.home() / ".kiro" / "skills" / "wfc" / "personas",
            Path.home() / ".wfc" / "personas",
            Path(__file__).parent.parent.parent / "personas",
        ]

        for loc in locations:
            if loc.exists():
                return loc

        # Fallback to relative path
        return Path(__file__).parent.parent.parent / "references" / "personas"

    def build_lightweight_registry(self) -> Dict[str, PersonaSummary]:
        """
        Build lightweight registry from full persona files.

        Extracts minimal metadata:
        - ID, name, panel, skills
        - First sentence of description

        Returns:
            Dict mapping persona_id -> PersonaSummary
        """
        registry = {}
        panels_dir = self.personas_dir / "panels"

        if not panels_dir.exists():
            return registry

        for panel_dir in panels_dir.iterdir():
            if not panel_dir.is_dir():
                continue

            panel_name = panel_dir.name

            for persona_file in panel_dir.glob("*.json"):
                try:
                    with open(persona_file) as f:
                        full_persona = json.load(f)

                    # Extract minimal summary
                    persona_id = full_persona["id"]

                    # Get first sentence of description for summary
                    full_desc = full_persona.get("description", "")
                    summary_desc = full_desc.split(".")[0] + "." if full_desc else ""

                    summary = PersonaSummary(
                        id=persona_id,
                        name=full_persona["name"],
                        panel=panel_name,
                        skills=full_persona.get("skills", [])[:3],  # First 3 skills only
                        description=summary_desc[:100]  # Max 100 chars
                    )

                    registry[persona_id] = summary

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Failed to load {persona_file}: {e}")
                    continue

        return registry

    def get_all_summaries(self) -> Dict[str, PersonaSummary]:
        """
        Get lightweight summaries for all personas.

        This is loaded initially (progressive disclosure).
        ~3K tokens vs ~50K for full personas.
        """
        if not self._summary_cache:
            self._summary_cache = self.build_lightweight_registry()
        return self._summary_cache

    def load_persona(self, persona_id: str) -> Optional[dict]:
        """
        Load full persona details on-demand.

        Args:
            persona_id: Persona identifier (e.g., "APPSEC_SPECIALIST")

        Returns:
            Full persona dict or None if not found
        """
        # Check cache first
        if persona_id in self._full_cache:
            return self._full_cache[persona_id]

        # Find persona file
        summary = self._summary_cache.get(persona_id)
        if not summary:
            return None

        persona_path = self.personas_dir / "panels" / summary.panel / f"{persona_id}.json"

        if not persona_path.exists():
            return None

        try:
            with open(persona_path) as f:
                full_persona = json.load(f)

            # Cache it
            self._full_cache[persona_id] = full_persona
            return full_persona

        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def get_by_panel(self, panel: str) -> List[PersonaSummary]:
        """Get all persona summaries for a specific panel"""
        summaries = self.get_all_summaries()
        return [s for s in summaries.values() if s.panel == panel]

    def search(self, query: str, max_results: int = 10) -> List[PersonaSummary]:
        """
        Search personas by keyword (lightweight).

        Searches:
        - Persona name
        - Skills
        - Description summary

        Does NOT load full personas (progressive).
        """
        query_lower = query.lower()
        summaries = self.get_all_summaries()

        matches = []
        for summary in summaries.values():
            # Check if query matches
            if (query_lower in summary.name.lower() or
                query_lower in summary.description.lower() or
                any(query_lower in skill.lower() for skill in summary.skills)):
                matches.append(summary)

        return matches[:max_results]

    def estimate_context_savings(self) -> dict:
        """
        Estimate token savings from progressive disclosure.

        Returns:
            Dict with before/after token estimates
        """
        summaries = self.get_all_summaries()

        # Estimate summary tokens
        summary_tokens = sum(s.summary_tokens for s in summaries.values())

        # Estimate full persona tokens (rough)
        # Average persona: ~800 tokens
        full_tokens = len(summaries) * 800

        return {
            "summaries_only": summary_tokens,
            "all_full_personas": full_tokens,
            "savings": full_tokens - summary_tokens,
            "savings_percent": round((1 - summary_tokens / full_tokens) * 100, 1)
        }


def generate_static_registry(output_path: Path):
    """
    Generate static registry.json for even faster loading.

    Run this when personas change to pre-generate the registry.
    """
    registry = ProgressiveRegistry()
    summaries = registry.get_all_summaries()

    # Convert to serializable format
    registry_data = {
        "version": "0.1.0",
        "count": len(summaries),
        "personas": {
            pid: {
                "id": s.id,
                "name": s.name,
                "panel": s.panel,
                "skills": s.skills,
                "description": s.description
            }
            for pid, s in summaries.items()
        }
    }

    with open(output_path, "w") as f:
        json.dump(registry_data, f, indent=2)

    print(f"✓ Generated registry: {output_path}")
    print(f"  Personas: {len(summaries)}")
    print(f"  Estimated tokens: ~{sum(s.summary_tokens for s in summaries.values())}")


if __name__ == "__main__":
    # Generate static registry
    registry = ProgressiveRegistry()

    # Show context savings
    savings = registry.estimate_context_savings()
    print("\n📊 Progressive Disclosure Savings:")
    print(f"   Summaries only: ~{savings['summaries_only']} tokens")
    print(f"   Full personas:  ~{savings['all_full_personas']} tokens")
    print(f"   Savings:        ~{savings['savings']} tokens ({savings['savings_percent']}%)")

    # Generate static registry
    output = Path(__file__).parent.parent.parent / "references" / "personas" / "registry-progressive.json"
    generate_static_registry(output)
