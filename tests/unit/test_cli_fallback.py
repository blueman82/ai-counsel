"""Tests for CLI detection and OpenRouter fallback functionality."""
import os
from unittest.mock import patch

import pytest

from adapters import (
    is_cli_available,
    clear_cli_cache,
    get_openrouter_fallback_config,
    create_adapter_with_fallback,
    get_cli_status,
    CLI_TO_OPENROUTER_FALLBACK,
)
from adapters.openrouter import OpenRouterAdapter
from adapters.claude import ClaudeAdapter
from models.config import CLIAdapterConfig, CLIToolConfig, HTTPAdapterConfig


class TestIsCliAvailable:
    """Tests for is_cli_available() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cli_cache()

    def test_returns_true_for_available_command(self):
        """Test that available commands return True."""
        # 'python' should be available in most test environments
        with patch("adapters.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/python"
            assert is_cli_available("python") is True
            # Called twice: once for check, once for debug logging
            assert mock_which.call_count == 2

    def test_returns_false_for_unavailable_command(self):
        """Test that unavailable commands return False."""
        with patch("adapters.shutil.which") as mock_which:
            mock_which.return_value = None
            assert is_cli_available("nonexistent_command_xyz") is False

    def test_caches_results(self):
        """Test that results are cached."""
        with patch("adapters.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/test"

            # First call
            result1 = is_cli_available("test_cmd")
            # Second call (should use cache)
            result2 = is_cli_available("test_cmd")

            assert result1 is True
            assert result2 is True
            # shutil.which called twice on first call (check + logging),
            # but second call uses cache (no additional calls)
            assert mock_which.call_count == 2

    def test_cache_returns_false_consistently(self):
        """Test that False results are also cached."""
        with patch("adapters.shutil.which") as mock_which:
            mock_which.return_value = None

            result1 = is_cli_available("missing_cmd")
            result2 = is_cli_available("missing_cmd")

            assert result1 is False
            assert result2 is False
            # Only called once for unavailable (no debug logging with path)
            mock_which.assert_called_once_with("missing_cmd")


class TestClearCliCache:
    """Tests for clear_cli_cache() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cli_cache()

    def test_clears_cached_results(self):
        """Test that clearing cache allows re-checking."""
        with patch("adapters.shutil.which") as mock_which:
            # First: command not available
            mock_which.return_value = None
            assert is_cli_available("test") is False
            initial_call_count = mock_which.call_count  # 1 call
            assert initial_call_count == 1

            # Clear cache
            clear_cli_cache()

            # Now: command is available
            mock_which.return_value = "/usr/bin/test"
            assert is_cli_available("test") is True

            # After cache clear, shutil.which is called again:
            # - 1 for the unavailable check
            # - 2 for the available check (check + debug logging)
            assert mock_which.call_count == 3


class TestCliToOpenrouterFallback:
    """Tests for CLI_TO_OPENROUTER_FALLBACK mapping."""

    def test_mapping_contains_expected_clis(self):
        """Test that mapping contains expected CLI adapters."""
        assert "claude" in CLI_TO_OPENROUTER_FALLBACK
        assert "codex" in CLI_TO_OPENROUTER_FALLBACK
        assert "droid" in CLI_TO_OPENROUTER_FALLBACK
        assert "gemini" in CLI_TO_OPENROUTER_FALLBACK

    def test_llamacpp_has_no_fallback(self):
        """Test that llamacpp (local-only) has no fallback."""
        assert "llamacpp" not in CLI_TO_OPENROUTER_FALLBACK

    def test_fallback_models_are_valid_openrouter_ids(self):
        """Test that fallback model IDs follow OpenRouter format."""
        for cli_name, model_id in CLI_TO_OPENROUTER_FALLBACK.items():
            # OpenRouter model IDs are "provider/model-name" format
            assert "/" in model_id, f"Invalid model ID for {cli_name}: {model_id}"


class TestGetOpenrouterFallbackConfig:
    """Tests for get_openrouter_fallback_config() function."""

    def test_returns_none_for_unknown_cli(self):
        """Test that unknown CLI names return None."""
        result = get_openrouter_fallback_config("unknown_cli")
        assert result is None

    def test_returns_none_without_api_key(self):
        """Test that missing API key returns None."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure OPENROUTER_API_KEY is not set
            if "OPENROUTER_API_KEY" in os.environ:
                del os.environ["OPENROUTER_API_KEY"]
            result = get_openrouter_fallback_config("claude")
            assert result is None

    def test_returns_config_with_api_key(self):
        """Test that valid CLI with API key returns HTTPAdapterConfig."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}):
            result = get_openrouter_fallback_config("claude", original_timeout=60)

            assert result is not None
            assert isinstance(result, HTTPAdapterConfig)
            assert result.type == "http"
            assert result.base_url == "https://openrouter.ai/api/v1"
            assert result.api_key == "test-key-123"
            assert result.timeout == 60
            assert result.max_retries == 2

    def test_preserves_original_timeout(self):
        """Test that timeout from original config is preserved."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = get_openrouter_fallback_config("codex", original_timeout=120)
            assert result.timeout == 120


class TestCreateAdapterWithFallback:
    """Tests for create_adapter_with_fallback() function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cli_cache()

    def test_returns_cli_adapter_when_available(self):
        """Test that CLI adapter is returned when CLI is available."""
        config = CLIAdapterConfig(
            type="cli",
            command="claude",
            args=["-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = True

            adapter, fallback_model = create_adapter_with_fallback("claude", config)

            assert isinstance(adapter, ClaudeAdapter)
            assert fallback_model is None

    def test_returns_openrouter_adapter_when_cli_unavailable(self):
        """Test fallback to OpenRouter when CLI is not installed."""
        config = CLIAdapterConfig(
            type="cli",
            command="droid",
            args=["-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = False
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
                adapter, fallback_model = create_adapter_with_fallback("droid", config)

                assert isinstance(adapter, OpenRouterAdapter)
                assert fallback_model == "anthropic/claude-3.5-sonnet"

    def test_raises_runtime_error_without_api_key(self):
        """Test that RuntimeError is raised when CLI unavailable and no API key."""
        config = CLIAdapterConfig(
            type="cli",
            command="codex",
            args=["-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = False
            with patch.dict(os.environ, {}, clear=True):
                # Remove API key if present
                os.environ.pop("OPENROUTER_API_KEY", None)

                with pytest.raises(RuntimeError) as exc_info:
                    create_adapter_with_fallback("codex", config)

                assert "not installed" in str(exc_info.value)
                assert "OPENROUTER_API_KEY" in str(exc_info.value)

    def test_skips_check_when_disabled(self):
        """Test that check_cli_availability=False skips availability check."""
        config = CLIAdapterConfig(
            type="cli",
            command="nonexistent",
            args=["-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            # Even though CLI would be unavailable, we skip the check
            adapter, fallback_model = create_adapter_with_fallback(
                "claude", config, check_cli_availability=False
            )

            # Should create CLI adapter without checking
            assert isinstance(adapter, ClaudeAdapter)
            assert fallback_model is None
            mock_available.assert_not_called()

    def test_http_adapter_bypasses_fallback(self):
        """Test that HTTP adapters don't use fallback mechanism."""
        config = HTTPAdapterConfig(
            type="http",
            base_url="https://openrouter.ai/api/v1",
            api_key="test-key",
            timeout=60,
        )

        adapter, fallback_model = create_adapter_with_fallback("openrouter", config)

        assert isinstance(adapter, OpenRouterAdapter)
        assert fallback_model is None

    def test_legacy_cli_tool_config(self):
        """Test backward compatibility with CLIToolConfig."""
        config = CLIToolConfig(
            command="claude",
            args=["-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = True

            adapter, fallback_model = create_adapter_with_fallback("claude", config)

            assert isinstance(adapter, ClaudeAdapter)
            assert fallback_model is None

    def test_fallback_preserves_timeout(self):
        """Test that fallback adapter preserves original timeout."""
        config = CLIAdapterConfig(
            type="cli",
            command="gemini",
            args=["-p", "{prompt}"],
            timeout=180,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = False
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
                adapter, fallback_model = create_adapter_with_fallback("gemini", config)

                assert adapter.timeout == 180


class TestGetCliStatus:
    """Tests for get_cli_status() function."""

    def test_returns_status_for_all_known_clis(self):
        """Test that status includes all known CLI tools."""
        status = get_cli_status()

        assert "claude" in status
        assert "codex" in status
        assert "droid" in status
        assert "gemini" in status
        assert "llamacpp" in status

    def test_status_structure(self):
        """Test that each status has expected structure."""
        status = get_cli_status()

        for cli_name, cli_status in status.items():
            assert "available" in cli_status
            assert "path" in cli_status
            assert "fallback" in cli_status
            assert isinstance(cli_status["available"], bool)

    def test_fallback_info_matches_mapping(self):
        """Test that fallback info matches CLI_TO_OPENROUTER_FALLBACK."""
        status = get_cli_status()

        for cli_name, cli_status in status.items():
            expected_fallback = CLI_TO_OPENROUTER_FALLBACK.get(cli_name)
            assert cli_status["fallback"] == expected_fallback

    def test_available_cli_has_path(self):
        """Test that available CLI has a path."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/claude"

            status = get_cli_status()

            # At least one CLI should be reported as available
            assert any(cli_status["available"] for cli_status in status.values())
            # And at least one CLI should have the mocked path
            assert any(
                cli_status["path"] == "/usr/local/bin/claude"
                for cli_status in status.values()
            )

    def test_unavailable_cli_has_none_path(self):
        """Test that unavailable CLI has None path."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            status = get_cli_status()

            for cli_name, cli_status in status.items():
                assert cli_status["available"] is False
                assert cli_status["path"] is None


class TestFallbackIntegration:
    """Integration tests for fallback functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cli_cache()

    def test_fallback_chain_for_claude(self):
        """Test complete fallback chain for claude adapter."""
        config = CLIAdapterConfig(
            type="cli",
            command="claude",
            args=["--print", "-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = False
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-api-key"}):
                adapter, fallback_model = create_adapter_with_fallback("claude", config)

                assert isinstance(adapter, OpenRouterAdapter)
                assert fallback_model == "anthropic/claude-sonnet-4"
                assert adapter.api_key == "test-api-key"

    def test_no_fallback_for_llamacpp(self):
        """Test that llamacpp has no fallback and raises error."""
        config = CLIAdapterConfig(
            type="cli",
            command="llama-cli",
            args=["-m", "{model}", "-p", "{prompt}"],
            timeout=60,
        )

        with patch("adapters.is_cli_available") as mock_available:
            mock_available.return_value = False
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
                with pytest.raises(RuntimeError) as exc_info:
                    create_adapter_with_fallback("llamacpp", config)

                assert "no fallback available" in str(exc_info.value).lower()
