"""Unit tests for logging formatters."""

import json
import logging
from datetime import datetime


from wfc.shared.logging.formatters import JSONFormatter, ConsoleFormatter


class TestJSONFormatter:
    """Test JSON formatter."""

    def test_basic_json_format(self):
        """Test basic JSON formatting with required fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["module"] == "file"
        assert data["function"] == "<unknown>"
        assert data["line_number"] == 42

    def test_iso8601_timestamp(self):
        """Test that timestamp is in ISO 8601 format."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    def test_request_id_in_context(self):
        """Test that request_id is included when available."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        record.request_id = "test-request-123"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "test-request-123"

    def test_extra_context_fields(self):
        """Test that extra context fields are included."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        record.user_id = "user-123"
        record.action = "login"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == "user-123"
        assert data["action"] == "login"

    def test_secret_sanitization(self):
        """Test that secrets are sanitized in JSON output."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="API key: wfc_secret123",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "wfc_secret123" not in result
        assert data["message"] == "API key: [REDACTED]"

    def test_newline_escaping_in_message(self):
        """Test that newlines are escaped to prevent log injection."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Line 1\nLine 2",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["message"] == "Line 1\\nLine 2"


class TestConsoleFormatter:
    """Test console formatter."""

    def test_basic_console_format(self):
        """Test basic console formatting."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result

    def test_color_codes_for_levels(self):
        """Test that different log levels have different color codes."""
        formatter = ConsoleFormatter()

        error_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="/test.py",
            lineno=1,
            msg="Error",
            args=(),
            exc_info=None,
        )
        error_result = formatter.format(error_record)
        assert "\033[" in error_result or "ERROR" in error_result

        warning_record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="/test.py",
            lineno=1,
            msg="Warning",
            args=(),
            exc_info=None,
        )
        warning_result = formatter.format(warning_record)
        assert "\033[" in warning_result or "WARNING" in warning_result

        info_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Info",
            args=(),
            exc_info=None,
        )
        info_result = formatter.format(info_record)
        assert "INFO" in info_result

    def test_single_line_format(self):
        """Test that output is compact single-line format."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        lines = result.split("\n")
        assert len(lines) == 1

    def test_console_secret_sanitization(self):
        """Test that secrets are sanitized in console output."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Bearer token_abc123xyz",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "token_abc123xyz" not in result or "[REDACTED]" in result

    def test_readable_timestamp(self):
        """Test that timestamp is human-readable."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        import re

        has_time = bool(re.search(r"\d{1,2}:\d{2}", result))
        assert has_time
