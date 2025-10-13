"""Unit tests for configuration loading."""
import pytest
from models.config import load_config


class TestConfigLoading:
    """Tests for config loading."""

    def test_load_default_config(self):
        """Test loading default config.yaml."""
        config = load_config()
        assert config is not None
        assert config.version == "1.0"
        assert "claude" in config.cli_tools
        assert "codex" in config.cli_tools

    def test_cli_tool_config_structure(self):
        """Test CLI tool config has required fields."""
        config = load_config()
        claude = config.cli_tools["claude"]
        assert claude.command == "claude"
        assert isinstance(claude.args, list)
        assert claude.timeout == 300  # 5 minutes for reasoning models

    def test_defaults_loaded(self):
        """Test default settings are loaded."""
        config = load_config()
        assert config.defaults.mode == "quick"
        assert config.defaults.rounds == 2
        assert config.defaults.max_rounds == 5

    def test_storage_config_loaded(self):
        """Test storage configuration is loaded."""
        config = load_config()
        assert config.storage.transcripts_dir == "transcripts"
        assert config.storage.format == "markdown"
        assert config.storage.auto_export is True

    def test_invalid_config_path_raises_error(self):
        """Test that invalid config path raises error."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
