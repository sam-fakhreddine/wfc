"""Tests for wfc.scripts.security.refusal_agent."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from wfc.scripts.security.refusal_agent import (
    _SUGGESTION_MAP,
    emit_and_exit,
    format_block_response,
)


class TestFormatBlockResponse:
    """Tests for format_block_response."""

    def test_returns_valid_json(self) -> None:
        result = format_block_response("Security violation: [eval-injection] eval()")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_has_required_keys(self) -> None:
        result = json.loads(format_block_response("Security violation: [eval-injection] eval()"))
        for key in ("blocked", "reason", "suggestion", "event_id", "pattern_id"):
            assert key in result, f"Missing key: {key}"

    def test_blocked_is_true(self) -> None:
        result = json.loads(format_block_response("Security violation: [eval-injection] eval()"))
        assert result["blocked"] is True

    def test_event_id_is_uuid4(self) -> None:
        result = json.loads(format_block_response("Security violation: [eval-injection] eval()"))
        parsed_uuid = uuid.UUID(result["event_id"], version=4)
        assert parsed_uuid.version == 4

    def test_includes_reason(self) -> None:
        reason = "Security violation: [eval-injection] eval()"
        result = json.loads(format_block_response(reason))
        assert result["reason"] == reason

    def test_includes_pattern_id(self) -> None:
        result = json.loads(
            format_block_response("Security violation: eval()", pattern_id="eval-injection")
        )
        assert result["pattern_id"] == "eval-injection"

    def test_custom_suggestion(self) -> None:
        result = json.loads(
            format_block_response(
                "Security violation",
                pattern_id="eval-injection",
                suggestion="Use X instead",
            )
        )
        assert result["suggestion"] == "Use X instead"

    def test_generates_suggestion_for_eval_injection(self) -> None:
        result = json.loads(
            format_block_response("Security violation: eval()", pattern_id="eval-injection")
        )
        assert "ast.literal_eval" in result["suggestion"]

    def test_generates_suggestion_for_os_system(self) -> None:
        result = json.loads(
            format_block_response("Security violation: os.system()", pattern_id="os-system")
        )
        assert "subprocess.run" in result["suggestion"]

    def test_generates_suggestion_for_subprocess_shell(self) -> None:
        result = json.loads(
            format_block_response(
                "Security violation: subprocess shell=True",
                pattern_id="subprocess-shell",
            )
        )
        assert "list" in result["suggestion"].lower()

    def test_generic_suggestion_for_unknown_pattern(self) -> None:
        result = json.loads(format_block_response("Something happened", pattern_id="unknown-thing"))
        assert isinstance(result["suggestion"], str)
        assert len(result["suggestion"]) > 0

    def test_generic_suggestion_for_security_reason(self) -> None:
        result = json.loads(
            format_block_response("A security concern was detected", pattern_id="unknown-thing")
        )
        assert "security" in result["suggestion"].lower()


class TestEmitAndExit:
    """Tests for emit_and_exit."""

    def test_exits_code_2(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit_and_exit("Security violation: eval()", pattern_id="eval-injection")
        assert exc_info.value.code == 2

    def test_prints_json_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit_and_exit("Security violation: eval()", pattern_id="eval-injection")
        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())
        assert isinstance(parsed, dict)

    def test_stderr_has_required_keys(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit_and_exit("Security violation: eval()", pattern_id="eval-injection")
        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())
        for key in ("blocked", "reason", "suggestion", "event_id", "pattern_id"):
            assert key in parsed, f"Missing key in stderr JSON: {key}"

    def test_fallback_on_format_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        import wfc.scripts.security.refusal_agent as mod

        def _boom(*args: object, **kwargs: object) -> str:
            raise RuntimeError("format failed")

        monkeypatch.setattr(mod, "format_block_response", _boom)

        with pytest.raises(SystemExit) as exc_info:
            emit_and_exit("plain text reason")
        assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "plain text reason" in captured.err


class TestGenerateSuggestion:
    """Tests for _generate_suggestion and suggestion map coverage."""

    def test_all_security_json_block_patterns_have_suggestions(self) -> None:
        """Every pattern with action=='block' in security.json must have a
        corresponding entry in _SUGGESTION_MAP."""
        security_json_path = Path(__file__).resolve().parent.parent / (
            "wfc/scripts/hooks/patterns/security.json"
        )
        data = json.loads(security_json_path.read_text())
        block_ids = [p["id"] for p in data["patterns"] if p.get("action") == "block"]
        assert len(block_ids) > 0, "Expected at least one block pattern"
        missing = [pid for pid in block_ids if pid not in _SUGGESTION_MAP]
        assert missing == [], f"Missing suggestions for block patterns: {missing}"
