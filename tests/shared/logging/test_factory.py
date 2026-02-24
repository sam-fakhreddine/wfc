"""Unit tests for logger factory."""

import logging
import time

import pytest

from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context


@pytest.fixture(autouse=True)
def clear_logger_cache():
    """Clear logger cache before each test."""
    import wfc.shared.logging

    wfc.shared.logging._logger_cache.clear()

    logging.root.manager.loggerDict.clear()

    yield

    wfc.shared.logging._logger_cache.clear()
    logging.root.manager.loggerDict.clear()


class TestLoggerFactory:
    """Test logger factory."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_logger_name_namespacing(self):
        """Test that logger names are namespaced with wfc."""
        logger = get_logger("test.module")
        assert logger.name == "wfc.test.module"

    def test_logger_name_already_namespaced(self):
        """Test that already namespaced names are not double-prefixed."""
        logger = get_logger("wfc.test.module")
        assert logger.name == "wfc.test.module"

    def test_development_uses_console_formatter(self, monkeypatch):
        """Test that development environment uses console formatter."""
        monkeypatch.setenv("ENV", "development")
        monkeypatch.delenv("LOG_FORMAT", raising=False)

        logger = get_logger("test")

        assert len(logger.handlers) > 0

        from wfc.shared.logging.formatters import ConsoleFormatter

        has_console = any(isinstance(h.formatter, ConsoleFormatter) for h in logger.handlers)
        assert has_console

    def test_production_uses_json_formatter(self, monkeypatch):
        """Test that production environment uses JSON formatter."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.delenv("LOG_FORMAT", raising=False)

        logger = get_logger("test")

        assert len(logger.handlers) > 0

        from wfc.shared.logging.formatters import JSONFormatter

        has_json = any(isinstance(h.formatter, JSONFormatter) for h in logger.handlers)
        assert has_json

    def test_log_level_configuration(self, monkeypatch):
        """Test that log level is configured from environment."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        logger = get_logger("test")

        assert logger.level == logging.DEBUG

    def test_factory_performance(self):
        """Test that logger creation is fast (<5ms)."""
        iterations = 100
        start = time.perf_counter()

        for i in range(iterations):
            get_logger(f"test.module{i}")

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        assert avg_time < 5.0, f"Logger creation took {avg_time:.2f}ms (>5ms)"

    def test_same_logger_reused(self):
        """Test that getting the same logger returns the same instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")

        assert logger1 is logger2

    def test_logger_with_request_context(self):
        """Test logger includes request_id from context."""
        logger = get_logger("test")

        with request_context() as request_id:
            captured_request_id = None

            class RequestIDFilter(logging.Filter):
                def filter(self, record):
                    nonlocal captured_request_id
                    from wfc.shared.logging.context import get_request_id

                    record.request_id = get_request_id()
                    captured_request_id = record.request_id
                    return True

            filter_instance = RequestIDFilter()
            logger.addFilter(filter_instance)

            logger.info("Test message")

            assert captured_request_id == request_id

            logger.removeFilter(filter_instance)

    def test_explicit_format_override(self, monkeypatch):
        """Test that LOG_FORMAT can override environment default."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("LOG_FORMAT", "console")

        logger = get_logger("test")

        from wfc.shared.logging.formatters import ConsoleFormatter

        has_console = any(isinstance(h.formatter, ConsoleFormatter) for h in logger.handlers)
        assert has_console
