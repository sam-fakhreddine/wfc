"""Unit tests for logging configuration."""

import pytest

from wfc.shared.logging.config import LoggingConfig


class TestLoggingConfig:
    """Test logging configuration module."""

    def test_default_config(self, monkeypatch):
        """Test default configuration values."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        monkeypatch.delenv("ENV", raising=False)

        config = LoggingConfig()

        assert config.log_level == "INFO"
        assert config.log_format == "console"
        assert config.env == "development"

    def test_log_level_from_env(self, monkeypatch):
        """Test LOG_LEVEL environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        config = LoggingConfig()

        assert config.log_level == "DEBUG"

    def test_log_level_validation(self, monkeypatch):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in valid_levels:
            monkeypatch.setenv("LOG_LEVEL", level)
            config = LoggingConfig()
            assert config.log_level == level

    def test_log_level_case_insensitive(self, monkeypatch):
        """Test log level is case insensitive."""
        monkeypatch.setenv("LOG_LEVEL", "debug")

        config = LoggingConfig()

        assert config.log_level == "DEBUG"

    def test_invalid_log_level_falls_back_to_info(self, monkeypatch):
        """Test invalid log level falls back to INFO."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        config = LoggingConfig()

        assert config.log_level == "INFO"

    def test_log_format_from_env(self, monkeypatch):
        """Test LOG_FORMAT environment variable."""
        monkeypatch.setenv("LOG_FORMAT", "json")

        config = LoggingConfig()

        assert config.log_format == "json"

    def test_log_format_validation(self, monkeypatch):
        """Test log format validation."""
        valid_formats = ["json", "console"]

        for fmt in valid_formats:
            monkeypatch.setenv("LOG_FORMAT", fmt)
            config = LoggingConfig()
            assert config.log_format == fmt

    def test_invalid_log_format_falls_back_to_console(self, monkeypatch):
        """Test invalid log format falls back to console."""
        monkeypatch.setenv("LOG_FORMAT", "invalid")

        config = LoggingConfig()

        assert config.log_format == "console"

    def test_env_from_env_var(self, monkeypatch):
        """Test ENV environment variable."""
        monkeypatch.setenv("ENV", "production")

        config = LoggingConfig()

        assert config.env == "production"

    def test_env_validation(self, monkeypatch):
        """Test environment validation."""
        valid_envs = ["development", "production"]

        for env in valid_envs:
            monkeypatch.setenv("ENV", env)
            config = LoggingConfig()
            assert config.env == env

    def test_invalid_env_falls_back_to_development(self, monkeypatch):
        """Test invalid env falls back to development."""
        monkeypatch.setenv("ENV", "invalid")

        config = LoggingConfig()

        assert config.env == "development"

    def test_production_defaults_to_json_format(self, monkeypatch):
        """Test production environment defaults to JSON format."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.delenv("LOG_FORMAT", raising=False)

        config = LoggingConfig()

        assert config.log_format == "json"

    def test_development_defaults_to_console_format(self, monkeypatch):
        """Test development environment defaults to console format."""
        monkeypatch.setenv("ENV", "development")
        monkeypatch.delenv("LOG_FORMAT", raising=False)

        config = LoggingConfig()

        assert config.log_format == "console"

    def test_explicit_format_overrides_env_default(self, monkeypatch):
        """Test explicit LOG_FORMAT overrides environment default."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("LOG_FORMAT", "console")

        config = LoggingConfig()

        assert config.log_format == "console"

    def test_config_is_immutable(self, monkeypatch):
        """Test config object is immutable after creation."""
        config = LoggingConfig()

        with pytest.raises(AttributeError):
            config.log_level = "DEBUG"
