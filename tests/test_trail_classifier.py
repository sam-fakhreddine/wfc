"""Tests for wfc.observability.trail -- TRAIL failure type classification."""

from __future__ import annotations


class TestFailureTypeEnum:
    """Test the FailureType enum exists and has correct values."""

    def test_reasoning_value(self):
        from wfc.observability.trail import FailureType

        assert FailureType.REASONING.value == "reasoning"

    def test_planning_value(self):
        from wfc.observability.trail import FailureType

        assert FailureType.PLANNING.value == "planning"

    def test_system_value(self):
        from wfc.observability.trail import FailureType

        assert FailureType.SYSTEM.value == "system"

    def test_unknown_value(self):
        from wfc.observability.trail import FailureType

        assert FailureType.UNKNOWN.value == "unknown"

    def test_all_members(self):
        from wfc.observability.trail import FailureType

        assert len(FailureType) == 4


class TestClassify:
    """Test the classify() function that maps errors to failure types."""

    def test_assertion_error_is_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(AssertionError("expected 5, got 3"))
        assert result.failure_type.value == "reasoning"

    def test_value_error_is_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(ValueError("invalid literal for int()"))
        assert result.failure_type.value == "reasoning"

    def test_type_error_is_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(TypeError("expected str, got int"))
        assert result.failure_type.value == "reasoning"

    def test_key_error_is_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(KeyError("missing_field"))
        assert result.failure_type.value == "reasoning"

    def test_json_decode_error_is_reasoning(self):
        import json

        from wfc.observability.trail import classify

        try:
            json.loads("not json")
        except json.JSONDecodeError as e:
            result = classify(e)
            assert result.failure_type.value == "reasoning"

    def test_import_error_is_planning(self):
        from wfc.observability.trail import classify

        result = classify(ImportError("No module named 'foo'"))
        assert result.failure_type.value == "planning"

    def test_module_not_found_is_planning(self):
        from wfc.observability.trail import classify

        result = classify(ModuleNotFoundError("No module named 'bar'"))
        assert result.failure_type.value == "planning"

    def test_attribute_error_is_planning(self):
        from wfc.observability.trail import classify

        result = classify(AttributeError("module 'x' has no attribute 'y'"))
        assert result.failure_type.value == "planning"

    def test_recursion_error_is_planning(self):
        from wfc.observability.trail import classify

        result = classify(RecursionError("maximum recursion depth exceeded"))
        assert result.failure_type.value == "planning"

    def test_os_error_is_system(self):
        from wfc.observability.trail import classify

        result = classify(OSError("disk full"))
        assert result.failure_type.value == "system"

    def test_file_not_found_is_system(self):
        from wfc.observability.trail import classify

        result = classify(FileNotFoundError("/tmp/missing"))
        assert result.failure_type.value == "system"

    def test_permission_error_is_system(self):
        from wfc.observability.trail import classify

        result = classify(PermissionError("access denied"))
        assert result.failure_type.value == "system"

    def test_timeout_error_is_system(self):
        from wfc.observability.trail import classify

        result = classify(TimeoutError("connection timed out"))
        assert result.failure_type.value == "system"

    def test_connection_error_is_system(self):
        from wfc.observability.trail import classify

        result = classify(ConnectionError("refused"))
        assert result.failure_type.value == "system"

    def test_memory_error_is_system(self):
        from wfc.observability.trail import classify

        result = classify(MemoryError())
        assert result.failure_type.value == "system"

    def test_runtime_error_is_unknown(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("something went wrong"))
        assert result.failure_type.value == "unknown"

    def test_generic_exception_is_unknown(self):
        from wfc.observability.trail import classify

        result = classify(Exception("generic"))
        assert result.failure_type.value == "unknown"

    def test_timeout_in_message_overrides_to_system(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("operation timed out after 30s"))
        assert result.failure_type.value == "system"

    def test_network_in_message_overrides_to_system(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("network unreachable"))
        assert result.failure_type.value == "system"

    def test_test_failed_in_message_overrides_to_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("test failed: expected True"))
        assert result.failure_type.value == "reasoning"

    def test_assertion_in_message_overrides_to_reasoning(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("assertion failed in test_foo"))
        assert result.failure_type.value == "reasoning"

    def test_dependency_in_message_overrides_to_planning(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("dependency resolution failed"))
        assert result.failure_type.value == "planning"

    def test_circular_import_in_message_overrides_to_planning(self):
        from wfc.observability.trail import classify

        result = classify(RuntimeError("circular import detected"))
        assert result.failure_type.value == "planning"


class TestClassifiedFailure:
    """Test the ClassifiedFailure result object."""

    def test_has_failure_type(self):
        from wfc.observability.trail import classify

        result = classify(ValueError("x"))
        assert hasattr(result, "failure_type")

    def test_has_exception_type(self):
        from wfc.observability.trail import classify

        result = classify(ValueError("x"))
        assert result.exception_type == "ValueError"

    def test_has_message(self):
        from wfc.observability.trail import classify

        result = classify(ValueError("bad value"))
        assert result.message == "bad value"

    def test_has_retryable(self):
        from wfc.observability.trail import classify

        system_result = classify(TimeoutError("timed out"))
        assert system_result.retryable is True
        reasoning_result = classify(AssertionError("expected 5"))
        assert reasoning_result.retryable is False

    def test_to_dict(self):
        from wfc.observability.trail import classify

        result = classify(OSError("disk full"))
        d = result.to_dict()
        assert d["failure_type"] == "system"
        assert d["exception_type"] == "OSError"
        assert d["message"] == "disk full"
        assert d["retryable"] is True


class TestEmitClassifiedFailure:
    """Test the convenience function that classifies + emits to observability bus."""

    def test_emits_event(self):
        from unittest.mock import patch

        from wfc.observability.trail import emit_classified_failure

        with (
            patch("wfc.observability.trail.emit_event") as mock_emit,
            patch("wfc.observability.trail.incr"),
        ):
            emit_classified_failure(
                error=ValueError("bad"),
                source="test_module",
                context={"task_id": "TASK-001"},
            )
            mock_emit.assert_called_once()
            call_kwargs = mock_emit.call_args
            assert call_kwargs[1]["event_type"] == "failure.classified"
            assert call_kwargs[1]["source"] == "test_module"
            payload = call_kwargs[1]["payload"]
            assert payload["failure_type"] == "reasoning"
            assert payload["task_id"] == "TASK-001"

    def test_increments_counter(self):
        from unittest.mock import patch

        from wfc.observability.trail import emit_classified_failure

        with (
            patch("wfc.observability.trail.emit_event"),
            patch("wfc.observability.trail.incr") as mock_incr,
        ):
            emit_classified_failure(
                error=TimeoutError("timed out"),
                source="test",
            )
            mock_incr.assert_called_once_with(
                "failure.classified",
                labels={"type": "system", "retryable": "true"},
            )

    def test_never_raises(self):
        from unittest.mock import patch

        from wfc.observability.trail import emit_classified_failure

        with patch("wfc.observability.trail.emit_event", side_effect=RuntimeError("boom")):
            emit_classified_failure(error=ValueError("x"), source="test")

    def test_handles_non_exception(self):
        from wfc.observability.trail import emit_classified_failure

        emit_classified_failure(error="not an exception", source="test")
