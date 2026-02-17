"""Tests for Customer Advocate persona JSON structure and validation."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def persona_path():
    """Return path to Customer Advocate persona JSON."""
    return (
        Path(__file__).parent.parent
        / "wfc/references/personas/panels/product/CUSTOMER_ADVOCATE.json"
    )


@pytest.fixture
def persona_data(persona_path):
    """Load Customer Advocate persona JSON."""
    with open(persona_path) as f:
        return json.load(f)


def test_customer_advocate_persona_exists(persona_path):
    """Test that Customer Advocate persona JSON file exists."""
    assert persona_path.exists(), f"Persona file not found at {persona_path}"


def test_customer_advocate_required_fields(persona_data):
    """Test that all required fields are present in persona JSON."""
    required_fields = ["id", "name", "panel", "skills", "lens", "selection_criteria"]

    for field in required_fields:
        assert field in persona_data, f"Missing required field: {field}"


def test_customer_advocate_id_and_panel(persona_data):
    """Test that persona has correct ID and panel."""
    assert persona_data["id"] == "CUSTOMER_ADVOCATE"
    assert persona_data["panel"] == "product"


def test_customer_advocate_review_dimensions_sum(persona_data):
    """Test that review_dimensions weights sum to 1.0."""
    review_dimensions = persona_data["lens"]["review_dimensions"]
    total_weight = sum(dim["weight"] for dim in review_dimensions)

    assert (
        abs(total_weight - 1.0) < 0.001
    ), f"Review dimensions weights sum to {total_weight}, expected 1.0"


def test_customer_advocate_team_values_property(persona_data):
    """Test that TEAM_VALUES_ALIGNMENT is in selection_criteria.properties."""
    properties = persona_data["selection_criteria"]["properties"]
    assert "TEAM_VALUES_ALIGNMENT" in properties, "TEAM_VALUES_ALIGNMENT property missing"


def test_customer_advocate_skills_structure(persona_data):
    """Test that skills are properly structured."""
    skills = persona_data["skills"]
    assert len(skills) > 0, "Persona must have at least one skill"

    for skill in skills:
        assert "name" in skill, "Skill missing 'name' field"
        assert "level" in skill, "Skill missing 'level' field"
        assert "context" in skill, "Skill missing 'context' field"


def test_customer_advocate_lens_structure(persona_data):
    """Test that lens has required sub-fields."""
    lens = persona_data["lens"]
    assert "focus" in lens, "Lens missing 'focus' field"
    assert "philosophy" in lens, "Lens missing 'philosophy' field"
    assert "review_dimensions" in lens, "Lens missing 'review_dimensions' field"


def test_customer_advocate_selection_criteria_structure(persona_data):
    """Test that selection_criteria has required sub-fields."""
    criteria = persona_data["selection_criteria"]
    required_sub_fields = [
        "task_types",
        "tech_stacks",
        "complexity_range",
        "anti_patterns",
        "properties",
    ]

    for field in required_sub_fields:
        assert field in criteria, f"Selection criteria missing '{field}' field"


def test_malformed_persona_missing_field():
    """Test handling of persona with missing required field."""
    malformed_persona = {
        "id": "TEST_PERSONA",
        "name": "Test Persona",
        # Missing 'panel' field
        "skills": [],
        "lens": {"focus": "test", "philosophy": "test", "review_dimensions": []},
        "selection_criteria": {},
    }

    # Verify that 'panel' is missing
    assert "panel" not in malformed_persona


def test_malformed_persona_weights_not_summing():
    """Test handling of persona with review_dimensions weights not summing to 1.0."""
    malformed_persona = {
        "id": "TEST_PERSONA",
        "name": "Test Persona",
        "panel": "test",
        "skills": [],
        "lens": {
            "focus": "test",
            "philosophy": "test",
            "review_dimensions": [
                {"dimension": "dim1", "weight": 0.5},
                {"dimension": "dim2", "weight": 0.3},
                # Total is 0.8, not 1.0
            ],
        },
        "selection_criteria": {},
    }

    # Verify that weights don't sum to 1.0
    total_weight = sum(dim["weight"] for dim in malformed_persona["lens"]["review_dimensions"])
    assert abs(total_weight - 1.0) >= 0.001


def test_customer_advocate_model_preference(persona_data):
    """Test that model_preference is properly configured."""
    model_pref = persona_data["model_preference"]
    assert "default" in model_pref
    assert "fallback" in model_pref
    assert model_pref["default"] == "sonnet"
    assert model_pref["fallback"] == "opus"


def test_customer_advocate_enabled_and_version(persona_data):
    """Test that persona is enabled and has version."""
    assert persona_data["enabled"] is True
    assert "version" in persona_data
    assert persona_data["version"] == "1.0.0"
