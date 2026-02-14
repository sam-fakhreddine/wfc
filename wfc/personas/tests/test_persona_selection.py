"""
Test Suite for Persona Selection

Tests the intelligent persona selection algorithm with various contexts.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path.home() / ".claude/skills/wfc"))

from personas.persona_orchestrator import (
    PersonaRegistry,
    PersonaSelector,
    PersonaSelectionContext,
    extract_tech_stack_from_files,
)


def test_python_api_task():
    """Test: Python FastAPI implementation should select Python/API experts"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    context = PersonaSelectionContext(
        task_id="TEST-001",
        files=["auth_service.py", "jwt_handler.py"],
        tech_stack=["python", "fastapi", "jwt", "postgresql"],
        task_type="api-implementation",
        complexity="L",
        properties=["SECURITY", "PERFORMANCE"],
        domain_context=["authentication"],
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    persona_names = [sp.persona.name for sp in selected]
    assert any(
        "Python" in name or "Backend" in name for name in persona_names
    ), "Should select Python backend expert"
    assert any(
        "Security" in name for name in persona_names
    ), "Should select security expert for SECURITY property"

    # Check diversity
    panels = [sp.persona.panel for sp in selected]
    panel_counts = {}
    for panel in panels:
        panel_counts[panel] = panel_counts.get(panel, 0) + 1

    assert all(
        count <= 2 for count in panel_counts.values()
    ), "No panel should have more than 2 personas (diversity check)"


def test_react_frontend_task():
    """Test: React UI implementation should select frontend experts"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    context = PersonaSelectionContext(
        task_id="TEST-002",
        files=["UserProfile.tsx", "LoginForm.tsx"],
        tech_stack=["react", "typescript", "css"],
        task_type="ui-implementation",
        complexity="M",
        properties=["USABILITY", "ACCESSIBILITY"],
        domain_context=[],
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    persona_names = [sp.persona.name for sp in selected]
    assert any(
        "React" in name or "Frontend" in name for name in persona_names
    ), "Should select React/Frontend expert"
    assert any(
        "Accessibility" in name for name in persona_names
    ), "Should select accessibility expert for ACCESSIBILITY property"


def test_payment_processing_task():
    """Test: Payment processing should select fintech + security experts"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    context = PersonaSelectionContext(
        task_id="TEST-003",
        files=["payment_service.py", "stripe_handler.py"],
        tech_stack=["python", "stripe", "postgresql"],
        task_type="feature-implementation",
        complexity="XL",
        properties=["SECURITY", "SAFETY", "CORRECTNESS"],
        domain_context=["fintech", "payments"],
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    persona_names = [sp.persona.name for sp in selected]
    panels = [sp.persona.panel for sp in selected]

    assert any(
        "Fintech" in name or "Payment" in name for name in persona_names
    ), "Should select fintech/payment expert"
    assert any("Security" in name for name in persona_names), "Should select security expert"
    assert "domain-experts" in panels, "Should include domain expert for fintech context"


def test_go_microservice_task():
    """Test: Go microservice should select Go backend + architecture experts"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    context = PersonaSelectionContext(
        task_id="TEST-004",
        files=["service.go", "handler.go"],
        tech_stack=["go", "grpc", "kubernetes"],
        task_type="microservices",
        complexity="XL",
        properties=["PERFORMANCE", "SCALABILITY", "RELIABILITY"],
        domain_context=[],
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    persona_names = [sp.persona.name for sp in selected]

    assert any("Go" in name for name in persona_names), "Should select Go expert"
    assert any(
        "Architect" in name or "SRE" in name for name in persona_names
    ), "Should select architecture/SRE expert for XL complexity"


def test_tech_stack_extraction():
    """Test: Tech stack extraction from file paths"""
    test_cases = [
        (["auth.py", "models.py"], ["python"]),
        (["App.tsx", "components/Button.tsx"], ["typescript", "react"]),
        (["service.go", "main.go"], ["go"]),
        (["styles.css", "index.html"], ["css", "html"]),
        (["api.py", "schema.sql"], ["python", "sql"]),
    ]

    for files, expected_techs in test_cases:
        result = extract_tech_stack_from_files(files)

        for tech in expected_techs:
            assert tech in result, f"Should extract {tech} from {files}"


def test_manual_persona_override():
    """Test: Manual persona selection override"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    context = PersonaSelectionContext(
        task_id="TEST-005", manual_personas=["APPSEC_SPECIALIST", "BACKEND_PYTHON_SENIOR"]
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    persona_ids = [sp.persona.id for sp in selected]
    assert "APPSEC_SPECIALIST" in persona_ids, "Should include manually selected APPSEC_SPECIALIST"
    assert (
        "BACKEND_PYTHON_SENIOR" in persona_ids
    ), "Should include manually selected BACKEND_PYTHON_SENIOR"


def test_relevance_scoring():
    """Test: Relevance scoring produces reasonable scores"""
    registry = PersonaRegistry(Path.home() / ".claude/skills/wfc/personas")
    selector = PersonaSelector(registry)

    # Perfect match context
    context = PersonaSelectionContext(
        task_id="TEST-006",
        tech_stack=["python", "fastapi", "postgresql"],
        task_type="api-implementation",
        complexity="L",
        properties=["SECURITY", "PERFORMANCE"],
    )

    selected = selector.select_personas(context, num_personas=5)

    # Assertions
    assert all(
        sp.relevance_score >= 0.3 for sp in selected
    ), "All selected personas should meet minimum relevance threshold"
    assert all(
        sp.relevance_score <= 1.0 for sp in selected
    ), "Relevance scores should not exceed 1.0"

    # Most relevant should have higher scores
    scores = [sp.relevance_score for sp in selected]
    assert scores[0] >= scores[-1], "Scores should be sorted in descending order"
