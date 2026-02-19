"""Tests for wfc.observability.config — ObservabilityConfig loading."""

from __future__ import annotations

from wfc.observability.config import ObservabilityConfig


class TestObservabilityConfigDefaults:
    """Test default configuration values."""

    def test_defaults_providers_null(self):
        config = ObservabilityConfig()
        assert config.providers == ["null"]

    def test_defaults_session_id_generated(self):
        config = ObservabilityConfig()
        assert config.session_id
        assert len(config.session_id) == 36

    def test_defaults_console_verbosity(self):
        config = ObservabilityConfig()
        assert config.console_verbosity == 1

    def test_defaults_file_output_dir(self):
        config = ObservabilityConfig()
        assert config.file_output_dir == ".development/observability"


class TestObservabilityConfigSessionID:
    """Test hierarchical session ID generation."""

    def test_uuid4_when_no_env(self, monkeypatch):
        monkeypatch.delenv("WFC_SESSION_ID", raising=False)
        config = ObservabilityConfig()
        assert len(config.session_id) == 36
        assert config.parent_session_id == ""

    def test_inherits_parent_from_env(self, monkeypatch):
        monkeypatch.setenv("WFC_SESSION_ID", "parent-abc-123")
        config = ObservabilityConfig()
        assert config.parent_session_id == "parent-abc-123"
        assert config.session_id != "parent-abc-123"

    def test_unique_ids_per_invocation(self):
        c1 = ObservabilityConfig()
        c2 = ObservabilityConfig()
        assert c1.session_id != c2.session_id


class TestObservabilityConfigLoadToml:
    """Test TOML config file loading."""

    def test_load_from_toml(self, tmp_path):
        toml_file = tmp_path / "observability.toml"
        toml_file.write_text('providers = ["file", "console"]\nconsole_verbosity = 2\n')
        config = ObservabilityConfig.load(str(toml_file))
        assert config.providers == ["file", "console"]
        assert config.console_verbosity == 2

    def test_load_missing_file_uses_defaults(self):
        config = ObservabilityConfig.load("/nonexistent/path/observability.toml")
        assert config.providers == ["null"]

    def test_load_malformed_toml_uses_defaults(self, tmp_path):
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text("this is not valid [[[toml")
        config = ObservabilityConfig.load(str(toml_file))
        assert config.providers == ["null"]

    def test_load_partial_toml_fills_defaults(self, tmp_path):
        toml_file = tmp_path / "partial.toml"
        toml_file.write_text('providers = ["memory"]\n')
        config = ObservabilityConfig.load(str(toml_file))
        assert config.providers == ["memory"]
        assert config.console_verbosity == 1


class TestObservabilityConfigEnvOverrides:
    """Test environment variable overrides."""

    def test_providers_env_overrides_toml(self, tmp_path, monkeypatch):
        toml_file = tmp_path / "observability.toml"
        toml_file.write_text('providers = ["file"]\n')
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "console,memory")
        config = ObservabilityConfig.load(str(toml_file))
        assert config.providers == ["console", "memory"]

    def test_providers_env_overrides_defaults(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "file")
        config = ObservabilityConfig.load()
        assert config.providers == ["file"]

    def test_verbosity_env_override(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_VERBOSITY", "2")
        config = ObservabilityConfig.load()
        assert config.console_verbosity == 2

    def test_output_dir_env_override(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_OUTPUT_DIR", "/tmp/wfc-obs")
        config = ObservabilityConfig.load()
        assert config.file_output_dir == "/tmp/wfc-obs"

    def test_invalid_verbosity_env_ignored(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_VERBOSITY", "not-a-number")
        config = ObservabilityConfig.load()
        assert config.console_verbosity == 1


class TestObservabilityConfigFindFile:
    """Test config file discovery."""

    def test_find_config_in_cwd(self, tmp_path, monkeypatch):
        wfc_dir = tmp_path / ".wfc"
        wfc_dir.mkdir()
        (wfc_dir / "observability.toml").write_text('providers = ["file"]\n')
        monkeypatch.chdir(tmp_path)
        path = ObservabilityConfig._find_config_file()
        assert path is not None
        assert path.exists()

    def test_find_config_returns_none_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = ObservabilityConfig._find_config_file()
        assert path is None
