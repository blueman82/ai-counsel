"""Unit tests for configuration loading."""
import os
import pytest
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError
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


class TestCLIAdapterConfig:
    """Tests for CLI adapter configuration."""

    def test_valid_cli_adapter_config(self):
        """Test valid CLI adapter configuration."""
        from models.config import CLIAdapterConfig

        config = CLIAdapterConfig(
            type="cli",
            command="claude",
            args=["--model", "{model}", "{prompt}"],
            timeout=60
        )
        assert config.type == "cli"
        assert config.command == "claude"
        assert config.timeout == 60

    def test_cli_adapter_requires_command(self):
        """Test that command field is required."""
        from models.config import CLIAdapterConfig

        with pytest.raises(ValidationError):
            CLIAdapterConfig(
                type="cli",
                args=["--model", "{model}"],
                timeout=60
            )


class TestHTTPAdapterConfig:
    """Tests for HTTP adapter configuration."""

    def test_valid_http_adapter_config(self):
        """Test valid HTTP adapter configuration."""
        from models.config import HTTPAdapterConfig

        config = HTTPAdapterConfig(
            type="http",
            base_url="http://localhost:11434",
            timeout=60
        )
        assert config.type == "http"
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 60

    def test_http_adapter_with_api_key_env_var(self):
        """Test HTTP adapter with environment variable substitution."""
        from models.config import HTTPAdapterConfig

        os.environ["TEST_API_KEY"] = "sk-test-123"
        config = HTTPAdapterConfig(
            type="http",
            base_url="https://api.example.com",
            api_key="${TEST_API_KEY}",
            timeout=60
        )
        # After loading, ${TEST_API_KEY} should be resolved
        assert config.api_key == "sk-test-123"
        del os.environ["TEST_API_KEY"]

    def test_http_adapter_requires_base_url(self):
        """Test that base_url field is required."""
        from models.config import HTTPAdapterConfig

        with pytest.raises(ValidationError):
            HTTPAdapterConfig(
                type="http",
                timeout=60
            )

    def test_http_adapter_missing_env_var_raises_error(self):
        """Test that missing environment variable raises clear error."""
        from models.config import HTTPAdapterConfig

        # Make sure the env var doesn't exist
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]

        with pytest.raises(ValidationError) as exc_info:
            HTTPAdapterConfig(
                type="http",
                base_url="http://test",
                api_key="${NONEXISTENT_VAR}",
                timeout=60
            )

        assert "NONEXISTENT_VAR" in str(exc_info.value)


class TestAdapterConfig:
    """Tests for discriminated adapter union."""

    def test_adapter_config_discriminates_cli_type(self):
        """Test AdapterConfig discriminates to CLIAdapterConfig."""
        from models.config import CLIAdapterConfig
        from pydantic import TypeAdapter

        data = {
            "type": "cli",
            "command": "claude",
            "args": ["--model", "{model}"],
            "timeout": 60
        }

        # Use TypeAdapter for discriminated unions
        from models.config import AdapterConfig
        adapter = TypeAdapter(AdapterConfig)
        config = adapter.validate_python(data)
        assert isinstance(config, CLIAdapterConfig)

    def test_adapter_config_discriminates_http_type(self):
        """Test AdapterConfig discriminates to HTTPAdapterConfig."""
        from models.config import HTTPAdapterConfig
        from pydantic import TypeAdapter

        data = {
            "type": "http",
            "base_url": "http://localhost:11434",
            "timeout": 60
        }

        from models.config import AdapterConfig
        adapter = TypeAdapter(AdapterConfig)
        config = adapter.validate_python(data)
        assert isinstance(config, HTTPAdapterConfig)

    def test_invalid_adapter_type_raises_error(self):
        """Test that invalid type raises ValidationError."""
        from pydantic import TypeAdapter

        from models.config import AdapterConfig
        adapter = TypeAdapter(AdapterConfig)

        with pytest.raises(ValidationError):
            adapter.validate_python({
                "type": "invalid",
                "command": "test",
                "timeout": 60
            })


class TestConfigLoader:
    """Tests for config loader with adapter migration."""

    def test_load_config_with_adapters_section(self, tmp_path):
        """Test loading config with new adapters section."""
        config_data = {
            "version": "1.0",
            "adapters": {
                "claude": {
                    "type": "cli",
                    "command": "claude",
                    "args": ["--model", "{model}"],
                    "timeout": 60
                }
            },
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config.adapters is not None
        assert "claude" in config.adapters
        assert config.cli_tools is None

    def test_load_config_with_cli_tools_emits_warning(self, tmp_path):
        """Test that cli_tools section triggers deprecation warning."""
        config_data = {
            "version": "1.0",
            "cli_tools": {
                "claude": {
                    "command": "claude",
                    "args": ["--model", "{model}"],
                    "timeout": 60
                }
            },
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = load_config(str(config_file))

            # Check warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "cli_tools" in str(w[0].message).lower()
            assert "deprecated" in str(w[0].message).lower()

    def test_load_config_fails_without_adapter_section(self, tmp_path):
        """Test config without adapters or cli_tools raises error."""
        config_data = {
            "version": "1.0",
            # Missing both adapters and cli_tools
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        assert "adapters" in str(exc_info.value).lower() or "cli_tools" in str(exc_info.value).lower()
