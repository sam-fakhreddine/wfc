"""Unit tests for logging decorators."""

import asyncio
import logging
import time

import pytest

from wfc.shared.logging.decorators import log_execution_time


@pytest.fixture(autouse=True)
def clear_logger_cache(monkeypatch):
    """Clear logger cache before each test."""
    import wfc.shared.logging

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    wfc.shared.logging._logger_cache.clear()
    logging.root.manager.loggerDict.clear()

    yield

    wfc.shared.logging._logger_cache.clear()
    logging.root.manager.loggerDict.clear()


class TestLogExecutionTime:
    """Test log_execution_time decorator."""

    def test_decorator_on_sync_function(self, caplog):
        """Test decorator works on synchronous functions."""

        @log_execution_time
        def test_func():
            return "result"

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            result = test_func()

        assert result == "result"
        assert len(caplog.records) >= 2

        messages = [r.message for r in caplog.records]
        assert any("test_func" in msg for msg in messages)
        assert any("Completed" in msg and "ms" in msg for msg in messages)

    def test_decorator_logs_duration(self, caplog):
        """Test that decorator logs execution duration."""

        @log_execution_time
        def slow_func():
            time.sleep(0.01)
            return "done"

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            slow_func()

        exit_logs = [r for r in caplog.records if "Completed" in r.message]
        assert len(exit_logs) > 0

        exit_log = exit_logs[0]
        assert hasattr(exit_log, "duration_ms")
        assert exit_log.duration_ms >= 10.0

    def test_decorator_includes_function_name(self, caplog):
        """Test that logs include function name and module."""

        @log_execution_time
        def my_custom_function():
            return 42

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            my_custom_function()

        messages = [r.message for r in caplog.records]
        assert any("my_custom_function" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_decorator_on_async_function(self, caplog):
        """Test decorator works on async functions."""

        @log_execution_time
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            result = await async_func()

        assert result == "async_result"
        assert len(caplog.records) >= 2

        messages = [r.message for r in caplog.records]
        assert any("async_func" in msg for msg in messages)
        assert any("Completed" in msg and "ms" in msg for msg in messages)

    def test_decorator_with_custom_log_level(self, caplog):
        """Test decorator with custom log level."""

        @log_execution_time(level=logging.INFO)
        def info_func():
            return "info"

        with caplog.at_level(logging.INFO, logger="wfc"):
            info_func()

        assert len(caplog.records) >= 2
        assert all(r.levelno == logging.INFO for r in caplog.records)

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @log_execution_time
        def documented_func():
            """This is a test function."""
            return "metadata"

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == """This is a test function."""

    def test_decorator_with_arguments(self, caplog):
        """Test decorator on function with arguments."""

        @log_execution_time
        def func_with_args(a, b, c=3):
            return a + b + c

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            result = func_with_args(1, 2, c=4)

        assert result == 7
        messages = [r.message for r in caplog.records]
        assert any("func_with_args" in msg for msg in messages)

    def test_decorator_exception_propagation(self, caplog):
        """Test that exceptions are properly propagated."""

        @log_execution_time
        def failing_func():
            raise ValueError("Test error")

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            with pytest.raises(ValueError, match="Test error"):
                failing_func()

        messages = [r.message for r in caplog.records]
        assert any("failing_func" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_async_decorator_exception_propagation(self, caplog):
        """Test that async exceptions are properly propagated."""

        @log_execution_time
        async def failing_async_func():
            raise ValueError("Async error")

        with caplog.at_level(logging.DEBUG, logger="wfc"):
            with pytest.raises(ValueError, match="Async error"):
                await failing_async_func()

        messages = [r.message for r in caplog.records]
        assert any("failing_async_func" in msg for msg in messages)

    def test_decorator_performance_overhead(self):
        """Test that decorator overhead is minimal."""

        @log_execution_time
        def fast_func():
            return 1 + 1

        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            fast_func()

        elapsed = (time.perf_counter() - start) * 1000
        avg_overhead = elapsed / iterations

        assert avg_overhead < 1.0, f"Decorator overhead {avg_overhead:.3f}ms > 1ms"
