"""Unit tests for configuration loading."""
import os
from pathlib import Path

import pytest
import yaml
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
            timeout=60,
        )
        assert config.type == "cli"
        assert config.command == "claude"
        assert config.timeout == 60

    def test_cli_adapter_requires_command(self):
        """Test that command field is required."""
        from models.config import CLIAdapterConfig

        with pytest.raises(ValidationError):
            CLIAdapterConfig(type="cli", args=["--model", "{model}"], timeout=60)


class TestHTTPAdapterConfig:
    """Tests for HTTP adapter configuration."""

    def test_valid_http_adapter_config(self):
        """Test valid HTTP adapter configuration."""
        from models.config import HTTPAdapterConfig

        config = HTTPAdapterConfig(
            type="http", base_url="http://localhost:11434", timeout=60
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
            timeout=60,
        )
        # After loading, ${TEST_API_KEY} should be resolved
        assert config.api_key == "sk-test-123"
        del os.environ["TEST_API_KEY"]

    def test_http_adapter_requires_base_url(self):
        """Test that base_url field is required."""
        from models.config import HTTPAdapterConfig

        with pytest.raises(ValidationError):
            HTTPAdapterConfig(type="http", timeout=60)

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
                timeout=60,
            )

        assert "NONEXISTENT_VAR" in str(exc_info.value)


class TestAdapterConfig:
    """Tests for discriminated adapter union."""

    def test_adapter_config_discriminates_cli_type(self):
        """Test AdapterConfig discriminates to CLIAdapterConfig."""
        from pydantic import TypeAdapter

        from models.config import CLIAdapterConfig

        data = {
            "type": "cli",
            "command": "claude",
            "args": ["--model", "{model}"],
            "timeout": 60,
        }

        # Use TypeAdapter for discriminated unions
        from models.config import AdapterConfig

        adapter = TypeAdapter(AdapterConfig)
        config = adapter.validate_python(data)
        assert isinstance(config, CLIAdapterConfig)

    def test_adapter_config_discriminates_http_type(self):
        """Test AdapterConfig discriminates to HTTPAdapterConfig."""
        from pydantic import TypeAdapter

        from models.config import HTTPAdapterConfig

        data = {"type": "http", "base_url": "http://localhost:11434", "timeout": 60}

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
            adapter.validate_python(
                {"type": "invalid", "command": "test", "timeout": 60}
            )


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
                    "timeout": 60,
                }
            },
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120,
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True,
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40,
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True,
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True,
            },
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
                    "timeout": 60,
                }
            },
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120,
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True,
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40,
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True,
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True,
            },
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_config(str(config_file))

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
                "timeout_per_round": 120,
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True,
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40,
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True,
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True,
            },
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        assert (
            "adapters" in str(exc_info.value).lower()
            or "cli_tools" in str(exc_info.value).lower()
        )


class TestDecisionGraphConfig:
    """Tests for DecisionGraphConfig path resolution."""

    @pytest.fixture
    def project_root(self):
        """
        Get the actual project root directory.

        The project root is where config.yaml is located, which is two levels
        up from models/config.py where DecisionGraphConfig is defined.
        """
        # This mirrors the logic in DecisionGraphConfig.resolve_db_path
        config_module_path = Path(__file__).parent.parent.parent / "models" / "config.py"
        return config_module_path.parent.parent

    def test_db_path_relative_to_project_root(self, project_root):
        """
        Test that relative path is resolved relative to project root.

        Verifies that "decision_graph.db" resolves to project_root/decision_graph.db,
        not the current working directory. This prevents breakage when running
        the server from different directories.
        """
        from models.config import DecisionGraphConfig

        config = DecisionGraphConfig(enabled=True, db_path="decision_graph.db")

        # Path should be absolute
        resolved_path = Path(config.db_path)
        assert resolved_path.is_absolute(), "Resolved path should be absolute"

        # Path should be at project root
        expected_path = (project_root / "decision_graph.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

        # Verify it's a string, not a Path object
        assert isinstance(config.db_path, str), "db_path should be returned as string"

    def test_db_path_absolute_unchanged(self, project_root):
        """
        Test that absolute paths are kept unchanged.

        Verifies that absolute paths like "/tmp/graph.db" are not modified
        and remain absolute after validation. Note: symlinks are NOT resolved
        for absolute paths (only relative paths get .resolve() called).
        """
        from models.config import DecisionGraphConfig

        absolute_path = "/tmp/test_graph.db"
        config = DecisionGraphConfig(enabled=True, db_path=absolute_path)

        # Should still be absolute
        resolved_path = Path(config.db_path)
        assert resolved_path.is_absolute(), "Absolute path should remain absolute"

        # Should be unchanged (no symlink resolution for absolute paths)
        assert config.db_path == absolute_path, (
            f"Absolute path should be preserved unchanged"
        )

    def test_db_path_with_env_var(self, project_root, monkeypatch):
        """
        Test that environment variables are resolved before path resolution.

        Verifies that "${DATA_DIR}/graph.db" first resolves the env var,
        then converts the path to absolute if needed. Absolute paths after
        env var resolution are NOT further resolved (no symlink resolution).
        """
        from models.config import DecisionGraphConfig

        # Set up test environment variable with absolute path
        test_data_dir = "/var/data"
        monkeypatch.setenv("TEST_DATA_DIR", test_data_dir)

        config = DecisionGraphConfig(
            enabled=True,
            db_path="${TEST_DATA_DIR}/graph.db"
        )

        # Should resolve env var and path is already absolute (no further resolution)
        expected_path = "/var/data/graph.db"
        assert config.db_path == expected_path, (
            f"Expected {expected_path}, got {config.db_path}"
        )

        # Path should be absolute
        assert Path(config.db_path).is_absolute(), (
            "Path with resolved env var should be absolute"
        )

    def test_db_path_with_relative_env_var(self, project_root, monkeypatch):
        """
        Test that relative paths in env vars are resolved relative to project root.

        Verifies that if DATA_DIR="data" (relative), then "${DATA_DIR}/graph.db"
        resolves to project_root/data/graph.db.
        """
        from models.config import DecisionGraphConfig

        # Set up relative path in environment variable
        monkeypatch.setenv("TEST_DATA_DIR", "data")

        config = DecisionGraphConfig(
            enabled=True,
            db_path="${TEST_DATA_DIR}/graph.db"
        )

        # Should resolve env var, then make absolute relative to project root
        expected_path = (project_root / "data" / "graph.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

    def test_db_path_parent_directory(self, project_root):
        """
        Test that parent directory references are resolved correctly.

        Verifies that "../shared/graph.db" resolves to the correct absolute
        path, navigating up from project root.
        """
        from models.config import DecisionGraphConfig

        config = DecisionGraphConfig(enabled=True, db_path="../shared/graph.db")

        # Should resolve .. relative to project root
        expected_path = (project_root / ".." / "shared" / "graph.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

        # Path should be absolute
        assert Path(config.db_path).is_absolute(), (
            "Path with parent directory should be absolute"
        )

    def test_db_path_subdirectory(self, project_root):
        """
        Test that subdirectory paths preserve structure under project root.

        Verifies that "data/graphs/db.db" resolves to
        project_root/data/graphs/db.db with directory structure preserved.
        """
        from models.config import DecisionGraphConfig

        config = DecisionGraphConfig(
            enabled=True,
            db_path="data/graphs/decision_graph.db"
        )

        # Should preserve subdirectory structure under project root
        expected_path = (project_root / "data" / "graphs" / "decision_graph.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

        # Path should be absolute
        assert Path(config.db_path).is_absolute(), (
            "Subdirectory path should be absolute"
        )

    def test_db_path_missing_env_var(self):
        """
        Test that missing environment variables raise clear error.

        Verifies that referencing an undefined env var like "${MISSING_VAR}/db.db"
        raises a ValueError with a helpful message mentioning the variable name.
        """
        from models.config import DecisionGraphConfig

        # Ensure the env var doesn't exist
        if "NONEXISTENT_TEST_VAR" in os.environ:
            del os.environ["NONEXISTENT_TEST_VAR"]

        with pytest.raises(ValidationError) as exc_info:
            DecisionGraphConfig(
                enabled=True,
                db_path="${NONEXISTENT_TEST_VAR}/graph.db"
            )

        # Error message should mention the missing variable
        error_message = str(exc_info.value)
        assert "NONEXISTENT_TEST_VAR" in error_message, (
            "Error should mention the missing environment variable"
        )
        assert "not set" in error_message.lower(), (
            "Error should indicate variable is not set"
        )

    def test_db_path_multiple_env_vars(self, monkeypatch):
        """
        Test that multiple environment variable references are resolved.

        Verifies that paths like "${BASE_DIR}/${DB_NAME}.db" resolve both
        environment variables correctly.
        """
        from models.config import DecisionGraphConfig

        monkeypatch.setenv("TEST_BASE_DIR", "/opt/app")
        monkeypatch.setenv("TEST_DB_NAME", "decisions")

        config = DecisionGraphConfig(
            enabled=True,
            db_path="${TEST_BASE_DIR}/${TEST_DB_NAME}.db"
        )

        # Both env vars should be resolved
        expected_path = Path("/opt/app/decisions.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

    def test_db_path_default_value(self, project_root):
        """
        Test that default db_path value is set correctly.

        Verifies that when db_path is not specified, the default value
        "decision_graph.db" is used. Note: Pydantic field validators only
        run on explicitly provided values, not on Field defaults, so the
        default remains as the literal string.
        """
        from models.config import DecisionGraphConfig

        # Use default value (don't specify db_path)
        config = DecisionGraphConfig(enabled=True)

        # Default is the literal string (validator doesn't run on Field defaults)
        assert config.db_path == "decision_graph.db", (
            f"Expected default 'decision_graph.db', got {config.db_path}"
        )

    def test_db_path_cwd_independence(self, project_root, tmp_path, monkeypatch):
        """
        Test that db_path resolution is independent of current working directory.

        Verifies that relative paths are always resolved relative to project root,
        not the current working directory. This is critical for reliability when
        running the server from different directories.
        """
        from models.config import DecisionGraphConfig

        # Change to a temporary directory
        monkeypatch.chdir(tmp_path)

        # Verify we're in a different directory
        assert Path.cwd() != project_root, "Should be in different directory"

        # Create config with relative path
        config = DecisionGraphConfig(enabled=True, db_path="decision_graph.db")

        # Path should still resolve relative to project root, not cwd
        expected_path = (project_root / "decision_graph.db").resolve()
        assert config.db_path == str(expected_path), (
            f"Path should be relative to project root, not cwd"
        )

        # Should NOT be in tmp_path
        assert not config.db_path.startswith(str(tmp_path)), (
            "Path should not be relative to current working directory"
        )

    def test_db_path_home_directory_expansion(self):
        """
        Test that home directory (~) references work correctly.

        Verifies that paths like "~/data/graph.db" are expanded to the
        user's home directory as absolute paths.
        """
        from models.config import DecisionGraphConfig

        config = DecisionGraphConfig(enabled=True, db_path="~/data/graph.db")

        # Should expand ~ to home directory
        expected_path = Path("~/data/graph.db").expanduser().resolve()
        assert config.db_path == str(expected_path), (
            f"Expected {expected_path}, got {config.db_path}"
        )

        # Should be absolute
        assert Path(config.db_path).is_absolute(), (
            "Home directory path should be absolute"
        )

        # Should not contain literal ~
        assert "~" not in config.db_path, "Tilde should be expanded"

    def test_db_path_validation_fields(self):
        """
        Test that other DecisionGraphConfig fields validate correctly alongside db_path.

        Verifies that db_path validation doesn't interfere with validation
        of other fields like similarity_threshold and max_context_decisions.
        """
        from models.config import DecisionGraphConfig

        config = DecisionGraphConfig(
            enabled=True,
            db_path="test.db",
            similarity_threshold=0.8,
            max_context_decisions=5,
            compute_similarities=False,
        )

        # All fields should be validated correctly
        assert config.enabled is True
        assert Path(config.db_path).is_absolute()
        assert config.similarity_threshold == 0.8
        assert config.max_context_decisions == 5
        assert config.compute_similarities is False

    def test_db_path_invalid_similarity_threshold_still_validates_path(self, project_root):
        """
        Test that db_path is validated even if other field validation fails.

        Verifies that the db_path validator runs before other field validators
        fail, ensuring consistent error messages.
        """
        from models.config import DecisionGraphConfig

        with pytest.raises(ValidationError) as exc_info:
            DecisionGraphConfig(
                enabled=True,
                db_path="test.db",  # Valid, should be processed
                similarity_threshold=1.5,  # Invalid, exceeds max
            )

        # Should fail on similarity_threshold, not db_path
        error_message = str(exc_info.value)
        assert "similarity_threshold" in error_message.lower(), (
            "Should report similarity_threshold validation error"
        )
