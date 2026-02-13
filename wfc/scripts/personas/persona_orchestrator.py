"""
Persona Orchestrator for WFC Consensus Review System

This module provides intelligent persona selection and management for the WFC
consensus review system. It loads personas from the personas directory, indexes
them for fast lookup, and selects appropriate personas based on task context.
"""

import json
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import config for model mapping
try:
    sys.path.insert(0, str(Path.home() / ".claude/skills/wfc"))
    from shared.config.wfc_config import WFCConfig

    config = WFCConfig()
    MODEL_MAPPING = config.get(
        "llm.models",
        {
            "opus": "claude-opus-4-20250514",
            "sonnet": "claude-sonnet-4-20250514",
            "haiku": "claude-haiku-4-5-20251001",
        },
    )
except Exception:
    # Fallback if config not available
    MODEL_MAPPING = {
        "opus": "claude-opus-4-20250514",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-haiku-4-5-20251001",
    }


def resolve_model_name(model_ref: str) -> str:
    """
    Resolve a model reference to actual model ID.

    Args:
        model_ref: Either an alias (opus/sonnet/haiku) or full model ID

    Returns:
        Actual model ID
    """
    # If it's an alias, resolve it
    if model_ref in MODEL_MAPPING:
        return MODEL_MAPPING[model_ref]

    # If it looks like a full model ID, return as-is
    if model_ref.startswith("claude-"):
        return model_ref

    # Default to sonnet if unknown
    return MODEL_MAPPING.get("sonnet", "claude-sonnet-4-20250514")


@dataclass
class Persona:
    """Represents an expert persona for code review"""

    id: str
    name: str
    panel: str
    subpanel: Optional[str]
    skills: List[Dict]
    domain_knowledge: List[str]
    lens: Dict
    personality: Dict
    selection_criteria: Dict
    model_preference: Dict
    system_prompt_additions: str
    tags: List[str]
    version: str
    enabled: bool

    @classmethod
    def from_dict(cls, data: Dict) -> "Persona":
        """Create Persona from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            panel=data["panel"],
            subpanel=data.get("subpanel"),
            skills=data["skills"],
            domain_knowledge=data.get("domain_knowledge", []),
            lens=data["lens"],
            personality=data["personality"],
            selection_criteria=data["selection_criteria"],
            model_preference=data["model_preference"],
            system_prompt_additions=data["system_prompt_additions"],
            tags=data["tags"],
            version=data["version"],
            enabled=data["enabled"],
        )

    def to_dict(self) -> Dict:
        """Convert Persona to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "panel": self.panel,
            "subpanel": self.subpanel,
            "skills": self.skills,
            "domain_knowledge": self.domain_knowledge,
            "lens": self.lens,
            "personality": self.personality,
            "selection_criteria": self.selection_criteria,
            "model_preference": self.model_preference,
            "system_prompt_additions": self.system_prompt_additions,
            "tags": self.tags,
            "version": self.version,
            "enabled": self.enabled,
        }


@dataclass
class PersonaSelectionContext:
    """Context information for persona selection"""

    task_id: str
    files: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    task_type: Optional[str] = None
    complexity: str = "M"  # S, M, L, XL
    properties: List[str] = field(default_factory=list)
    domain_context: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    manual_personas: List[str] = field(default_factory=list)  # User override


@dataclass
class SelectedPersona:
    """A persona selected for review with relevance score"""

    persona: Persona
    relevance_score: float
    selection_reasons: List[str] = field(default_factory=list)


class PersonaRegistry:
    """
    Registry for loading and indexing personas.

    Provides fast lookup by ID, tags, tech stack, and complexity.
    Loads personas from JSON files and maintains indexes.
    """

    def __init__(self, personas_dir: Path):
        """
        Initialize the persona registry.

        Args:
            personas_dir: Path to the personas directory
        """
        self.personas_dir = Path(personas_dir)
        self.personas: Dict[str, Persona] = {}

        # Indexes for fast lookup
        self.by_tag: Dict[str, List[str]] = defaultdict(list)
        self.by_tech_stack: Dict[str, List[str]] = defaultdict(list)
        self.by_panel: Dict[str, List[str]] = defaultdict(list)
        self.by_complexity: Dict[str, List[str]] = defaultdict(list)
        self.by_property: Dict[str, List[str]] = defaultdict(list)

        self._load_personas()
        self._build_indexes()

    def _load_personas(self):
        """Load all persona JSON files from the panels directory"""
        # NEW PATH: references/personas/panels
        panels_dir = self.personas_dir / "panels"

        # Fallback to references if old path doesn't exist
        if not panels_dir.exists():
            panels_dir = (
                Path(str(self.personas_dir).replace("/personas", "/references/personas")) / "panels"
            )

        if not panels_dir.exists():
            raise FileNotFoundError(f"Panels directory not found: {panels_dir}")

        # Load from all panel subdirectories
        for panel_dir in panels_dir.iterdir():
            if not panel_dir.is_dir():
                continue

            # Load all JSON files in this panel
            for persona_file in panel_dir.glob("*.json"):
                try:
                    with open(persona_file, "r") as f:
                        data = json.load(f)

                    persona = Persona.from_dict(data)

                    # Only load enabled personas
                    if persona.enabled:
                        self.personas[persona.id] = persona

                except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                    logger.warning(
                        "Failed to load persona from %s: %s", persona_file, e, exc_info=True
                    )

        # Also load custom personas if they exist
        custom_dir = self.personas_dir / "custom"
        if custom_dir.exists():
            for persona_file in custom_dir.glob("*.json"):
                try:
                    with open(persona_file, "r") as f:
                        data = json.load(f)

                    persona = Persona.from_dict(data)

                    if persona.enabled:
                        self.personas[persona.id] = persona

                except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                    logger.warning(
                        "Failed to load custom persona from %s: %s", persona_file, e, exc_info=True
                    )

    def _build_indexes(self):
        """Build indexes for fast lookup"""
        for persona_id, persona in self.personas.items():
            # Index by tags
            for tag in persona.tags:
                self.by_tag[tag.lower()].append(persona_id)

            # Index by tech stack
            for tech in persona.selection_criteria.get("tech_stacks", []):
                self.by_tech_stack[tech.lower()].append(persona_id)

            # Index by panel
            self.by_panel[persona.panel].append(persona_id)

            # Index by complexity
            for complexity in persona.selection_criteria.get("complexity_range", []):
                self.by_complexity[complexity].append(persona_id)

            # Index by property
            for prop in persona.selection_criteria.get("properties", []):
                self.by_property[prop.upper()].append(persona_id)

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """
        Get a persona by ID.

        Args:
            persona_id: The persona ID

        Returns:
            Persona object or None if not found
        """
        return self.personas.get(persona_id)

    def search_by_tags(self, tags: List[str]) -> List[str]:
        """
        Search personas by tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of persona IDs matching any of the tags
        """
        persona_ids = set()
        for tag in tags:
            persona_ids.update(self.by_tag.get(tag.lower(), []))
        return list(persona_ids)

    def search_by_tech_stack(self, tech_stack: List[str]) -> List[str]:
        """
        Search personas by tech stack.

        Args:
            tech_stack: List of technologies

        Returns:
            List of persona IDs matching any of the technologies
        """
        persona_ids = set()
        for tech in tech_stack:
            persona_ids.update(self.by_tech_stack.get(tech.lower(), []))
        return list(persona_ids)

    def search_by_panel(self, panel: str) -> List[str]:
        """
        Get all personas in a panel.

        Args:
            panel: Panel name

        Returns:
            List of persona IDs in the panel
        """
        return self.by_panel.get(panel, [])

    def search_by_complexity(self, complexity: str) -> List[str]:
        """
        Search personas suitable for a complexity level.

        Args:
            complexity: Complexity level (S, M, L, XL)

        Returns:
            List of persona IDs suitable for this complexity
        """
        return self.by_complexity.get(complexity, [])

    def search_by_property(self, property_name: str) -> List[str]:
        """
        Search personas specialized in a property.

        Args:
            property_name: Property name (e.g., SAFETY, SECURITY)

        Returns:
            List of persona IDs specialized in this property
        """
        return self.by_property.get(property_name.upper(), [])

    def get_all_personas(self) -> List[Persona]:
        """Get all loaded personas"""
        return list(self.personas.values())

    def get_panel_summary(self) -> Dict[str, int]:
        """Get summary of persona counts by panel"""
        summary = {}
        for panel, persona_ids in self.by_panel.items():
            summary[panel] = len(persona_ids)
        return summary

    def rebuild_registry_file(self):
        """
        Rebuild the registry.json file from loaded personas.

        This is useful after adding new personas to generate the index.
        """
        registry = {
            "version": "1.0.0",
            "panels": {},
            "index": {
                "by_tag": {k: list(v) for k, v in self.by_tag.items()},
                "by_tech_stack": {k: list(v) for k, v in self.by_tech_stack.items()},
                "by_complexity": {k: list(v) for k, v in self.by_complexity.items()},
                "by_property": {k: list(v) for k, v in self.by_property.items()},
            },
        }

        # Build panels section
        for panel, persona_ids in self.by_panel.items():
            # Get panel description from first persona in panel
            if persona_ids:
                registry["panels"][panel] = {
                    "description": f"Expert panel for {panel}",
                    "count": len(persona_ids),
                    "personas": persona_ids,
                }

        # Write registry file
        registry_path = self.personas_dir / "registry.json"
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        return registry_path


class PersonaSelector:
    """
    Intelligent persona selection based on task context.

    Selects the most relevant personas for a review using:
    - Tech stack matching
    - Task type classification
    - Complexity filtering
    - Property alignment
    - Panel diversity enforcement
    """

    def __init__(self, registry: PersonaRegistry):
        """
        Initialize the persona selector.

        Args:
            registry: PersonaRegistry instance
        """
        self.registry = registry

    def select_personas(
        self,
        context: PersonaSelectionContext,
        num_personas: int = 5,
        require_diversity: bool = True,
        min_relevance: float = 0.3,
    ) -> List[SelectedPersona]:
        """
        Select personas for a review based on context.

        Args:
            context: Selection context with task information
            num_personas: Number of personas to select
            require_diversity: Whether to enforce panel diversity
            min_relevance: Minimum relevance score threshold

        Returns:
            List of selected personas with relevance scores
        """
        # If manual personas specified, use those
        if context.manual_personas:
            return self._select_manual(context.manual_personas)

        # Score all personas
        scored_personas = []
        for persona in self.registry.get_all_personas():
            score, reasons = self._score_persona(persona, context)

            if score >= min_relevance:
                scored_personas.append(
                    SelectedPersona(
                        persona=persona, relevance_score=score, selection_reasons=reasons
                    )
                )

        # Sort by relevance score
        scored_personas.sort(key=lambda x: x.relevance_score, reverse=True)

        # Apply diversity if required
        if require_diversity:
            selected = self._enforce_diversity(scored_personas, num_personas)
        else:
            selected = scored_personas[:num_personas]

        return selected

    def _select_manual(self, persona_ids: List[str]) -> List[SelectedPersona]:
        """Select manually specified personas"""
        selected = []
        for persona_id in persona_ids:
            persona = self.registry.get_persona(persona_id)
            if persona:
                selected.append(
                    SelectedPersona(
                        persona=persona, relevance_score=1.0, selection_reasons=["Manual selection"]
                    )
                )
        return selected

    def _score_persona(
        self, persona: Persona, context: PersonaSelectionContext
    ) -> tuple[float, List[str]]:
        """
        Score a persona's relevance to the context.

        Returns:
            (score, reasons) tuple
        """
        score = 0.0
        reasons = []

        criteria = persona.selection_criteria

        # Tech stack matching (40% weight)
        tech_match = self._match_tech_stack(criteria.get("tech_stacks", []), context.tech_stack)
        if tech_match > 0:
            score += tech_match * 0.4
            reasons.append(f"Tech stack match: {tech_match:.2f}")

        # Property alignment (30% weight)
        prop_match = self._match_properties(criteria.get("properties", []), context.properties)
        if prop_match > 0:
            score += prop_match * 0.3
            reasons.append(f"Property alignment: {prop_match:.2f}")

        # Complexity suitability (15% weight)
        if context.complexity in criteria.get("complexity_range", []):
            score += 0.15
            reasons.append(f"Suitable for {context.complexity} complexity")

        # Task type matching (10% weight)
        if context.task_type and context.task_type in criteria.get("task_types", []):
            score += 0.10
            reasons.append(f"Task type: {context.task_type}")

        # Domain context (5% weight)
        domain_match = self._match_domain(persona.domain_knowledge, context.domain_context)
        if domain_match > 0:
            score += domain_match * 0.05
            reasons.append(f"Domain expertise: {domain_match:.2f}")

        return score, reasons

    def _match_tech_stack(self, persona_tech: List[str], context_tech: List[str]) -> float:
        """Calculate tech stack match score (0-1)"""
        if not context_tech or not persona_tech:
            return 0.0

        persona_tech_lower = {t.lower() for t in persona_tech}
        context_tech_lower = {t.lower() for t in context_tech}

        matches = persona_tech_lower & context_tech_lower
        return len(matches) / len(context_tech_lower) if context_tech_lower else 0.0

    def _match_properties(self, persona_props: List[str], context_props: List[str]) -> float:
        """Calculate property match score (0-1)"""
        if not context_props or not persona_props:
            return 0.0

        persona_props_upper = {p.upper() for p in persona_props}
        context_props_upper = {p.upper() for p in context_props}

        matches = persona_props_upper & context_props_upper
        return len(matches) / len(context_props_upper) if context_props_upper else 0.0

    def _match_domain(self, persona_domain: List[str], context_domain: List[str]) -> float:
        """Calculate domain knowledge match score (0-1)"""
        if not context_domain or not persona_domain:
            return 0.0

        persona_domain_lower = {d.lower() for d in persona_domain}
        context_domain_lower = {d.lower() for d in context_domain}

        matches = persona_domain_lower & context_domain_lower
        return len(matches) / len(context_domain_lower) if context_domain_lower else 0.0

    def _enforce_diversity(
        self, scored_personas: List[SelectedPersona], num_personas: int
    ) -> List[SelectedPersona]:
        """
        Enforce panel diversity in selection.

        Ensures no more than 2 personas from the same panel.
        """
        selected = []
        panel_counts = defaultdict(int)
        max_per_panel = 2

        for sp in scored_personas:
            panel = sp.persona.panel

            if panel_counts[panel] < max_per_panel:
                selected.append(sp)
                panel_counts[panel] += 1

                if len(selected) >= num_personas:
                    break

        # If we didn't get enough, relax diversity and fill remaining
        if len(selected) < num_personas:
            for sp in scored_personas:
                if sp not in selected:
                    selected.append(sp)
                    if len(selected) >= num_personas:
                        break

        return selected


def extract_tech_stack_from_files(files: List[str]) -> List[str]:
    """
    Extract technology stack from file paths.

    Args:
        files: List of file paths

    Returns:
        List of detected technologies
    """
    tech_stack = set()

    # Extension to tech mapping
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".sql": "sql",
        ".sh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".vue": "vue",
        ".svelte": "svelte",
    }

    for file_path in files:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext in ext_map:
            tech_stack.add(ext_map[ext])

        # Check for framework indicators in path
        path_str = str(path).lower()

        if "react" in path_str or "jsx" in path_str or "tsx" in path_str:
            tech_stack.add("react")
        if "vue" in path_str:
            tech_stack.add("vue")
        if "fastapi" in path_str:
            tech_stack.add("fastapi")
        if "django" in path_str:
            tech_stack.add("django")
        if "flask" in path_str:
            tech_stack.add("flask")
        if "postgres" in path_str or "postgresql" in path_str:
            tech_stack.add("postgresql")
        if "redis" in path_str:
            tech_stack.add("redis")
        if "kafka" in path_str:
            tech_stack.add("kafka")
        if "kubernetes" in path_str or "k8s" in path_str:
            tech_stack.add("kubernetes")

    return list(tech_stack)
