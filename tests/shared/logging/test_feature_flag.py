"""Unit tests for centralized logging feature flag."""

import logging


class TestFeatureFlag:
    """Test USE_CENTRALIZED_LOGGING feature flag."""

    def test_feature_flag_enabled_by_default(self, monkeypatch):
        """Test that centralized logging is enabled by default."""
        monkeypatch.delenv("USE_CENTRALIZED_LOGGING", raising=False)

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger = get_logger("test")

        assert logger.name.startswith("wfc.")

    def test_feature_flag_explicitly_enabled(self, monkeypatch):
        """Test that feature flag can be explicitly enabled."""
        monkeypatch.setenv("USE_CENTRALIZED_LOGGING", "true")

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger = get_logger("test")

        assert logger.name.startswith("wfc.")

    def test_feature_flag_disabled(self, monkeypatch):
        """Test that feature flag can disable centralized logging."""
        monkeypatch.setenv("USE_CENTRALIZED_LOGGING", "false")

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger = get_logger("test")

        assert logger.name == "test"

    def test_feature_flag_case_insensitive(self, monkeypatch):
        """Test that feature flag is case insensitive."""
        test_cases = [
            ("TRUE", True),
            ("True", True),
            ("true", True),
            ("FALSE", False),
            ("False", False),
            ("false", False),
        ]

        for value, should_be_centralized in test_cases:
            monkeypatch.setenv("USE_CENTRALIZED_LOGGING", value)

            import wfc.shared.logging

            wfc.shared.logging._logger_cache.clear()
            logging.root.manager.loggerDict.clear()

            from wfc.shared.logging import get_logger

            logger = get_logger("test")

            if should_be_centralized:
                assert logger.name.startswith("wfc."), f"Expected centralized for {value}"
            else:
                assert logger.name == "test", f"Expected standard logging for {value}"

    def test_feature_flag_invalid_value_defaults_to_enabled(self, monkeypatch):
        """Test that invalid flag values default to enabled."""
        monkeypatch.setenv("USE_CENTRALIZED_LOGGING", "invalid")

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger = get_logger("test")

        assert logger.name == "test"

    def test_standard_logging_fallback_behavior(self, monkeypatch):
        """Test that standard logging fallback works correctly."""
        monkeypatch.setenv("USE_CENTRALIZED_LOGGING", "false")

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger1 = get_logger("module.submodule")
        logger2 = logging.getLogger("module.submodule")

        assert logger1 is logger2

    def test_centralized_logging_behavior(self, monkeypatch):
        """Test that centralized logging adds wfc namespace."""
        monkeypatch.setenv("USE_CENTRALIZED_LOGGING", "true")

        import wfc.shared.logging

        wfc.shared.logging._logger_cache.clear()

        from wfc.shared.logging import get_logger

        logger = get_logger("module.submodule")

        assert logger.name == "wfc.module.submodule"
        assert any(f.__class__.__name__ == "RequestIDFilter" for f in logger.filters)
