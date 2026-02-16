"""Tests for TEAMCHARTER values manifest (TASK-001)."""

import json
from pathlib import Path

import pytest

VALUES_PATH = Path(__file__).parent.parent / "wfc" / "references" / "teamcharter_values.json"

REQUIRED_VALUE_IDS = {
    "innovation",
    "accountability",
    "teamwork",
    "learning",
    "customer_focus",
    "trust",
}
REQUIRED_FIELDS = {"id", "name", "description", "keywords"}


class TestTeamcharterValuesSchema:
    """Validate teamcharter_values.json structure and content."""

    def test_file_exists(self):
        assert VALUES_PATH.exists(), f"Values file not found at {VALUES_PATH}"

    def test_valid_json(self):
        data = json.loads(VALUES_PATH.read_text())
        assert isinstance(data, dict)

    def test_has_values_array(self):
        data = json.loads(VALUES_PATH.read_text())
        assert "values" in data
        assert isinstance(data["values"], list)

    def test_all_six_values_present(self):
        data = json.loads(VALUES_PATH.read_text())
        ids = {v["id"] for v in data["values"]}
        assert ids == REQUIRED_VALUE_IDS, f"Missing values: {REQUIRED_VALUE_IDS - ids}"

    def test_each_value_has_required_fields(self):
        data = json.loads(VALUES_PATH.read_text())
        for value in data["values"]:
            missing = REQUIRED_FIELDS - set(value.keys())
            assert not missing, f"Value '{value.get('id', '?')}' missing fields: {missing}"

    def test_keywords_non_empty(self):
        data = json.loads(VALUES_PATH.read_text())
        for value in data["values"]:
            assert len(value["keywords"]) > 0, f"Value '{value['id']}' has empty keywords"

    def test_no_extra_fields(self):
        data = json.loads(VALUES_PATH.read_text())
        allowed_top = {"$schema", "version", "values"}
        extra_top = set(data.keys()) - allowed_top
        assert not extra_top, f"Extra top-level fields: {extra_top}"
        for value in data["values"]:
            extra = set(value.keys()) - REQUIRED_FIELDS
            assert not extra, f"Value '{value['id']}' has extra fields: {extra}"

    def test_malformed_json_handling(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json")
        with pytest.raises(json.JSONDecodeError):
            json.loads(bad_file.read_text())

    def test_no_internal_team_name(self):
        content = VALUES_PATH.read_text()
        assert "Pod G" not in content, "Internal team name found in values file"


class TestTeamcharterMarkdown:
    """Validate TEAMCHARTER.md content."""

    MD_PATH = Path(__file__).parent.parent / "wfc" / "references" / "TEAMCHARTER.md"

    def test_file_exists(self):
        assert self.MD_PATH.exists()

    def test_contains_mission(self):
        content = self.MD_PATH.read_text()
        assert "Mission Statement" in content

    def test_contains_vision(self):
        content = self.MD_PATH.read_text()
        assert "Vision Statement" in content

    def test_contains_all_six_values(self):
        content = self.MD_PATH.read_text()
        for value_name in [
            "Innovation & Experimentation",
            "Accountability & Simplicity",
            "Teamwork & Collaboration",
            "Continuous Learning & Curiosity",
            "Customer Focus & Service Excellence",
            "Trust & Autonomy",
        ]:
            assert value_name in content, f"Missing value: {value_name}"

    def test_no_internal_team_name(self):
        content = self.MD_PATH.read_text()
        assert "Pod G" not in content, "Internal team name found in TEAMCHARTER.md"
