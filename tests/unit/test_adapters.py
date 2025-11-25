"""Unit tests for CLI adapters."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from adapters import create_adapter
from adapters.base import BaseCLIAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters.droid import DroidAdapter
from adapters.gemini import GeminiAdapter
from models.config import CLIAdapterConfig, CLIToolConfig, HTTPAdapterConfig


class TestBaseCLIAdapter:
    """Tests for BaseCLIAdapter."""

    def test_cannot_instantiate_base_adapter(self):
        """Test that base adapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCLIAdapter(command="test", args=[], timeout=60)

    def test_subclass_must_implement_parse_output(self):
        """Test that subclasses must implement parse_output."""

        class IncompleteAdapter(BaseCLIAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter(command="test", args=[], timeout=60)


class TestClaudeAdapter:
    """Tests for ClaudeAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ],
            timeout=90,
        )
        assert adapter.command == "claude"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Claude Code output\n\nActual model response here", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ]
        )
        result = await adapter.invoke(
            prompt="What is 2+2?", model="claude-3-5-sonnet-20241022"
        )

        assert result == "Actual model response here"
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ],
            timeout=1,
        )

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Model not found")
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ]
        )

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_extracts_response(self):
        """Test output parsing extracts model response."""
        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ]
        )

        raw_output = """
        Claude Code v1.0
        Loading model...

        Here is the actual response from the model.
        This is what we want to extract.
        """

        result = adapter.parse_output(raw_output)
        assert "actual response" in result
        assert "Claude Code v1.0" not in result
        assert "Loading model" not in result


class TestCodexAdapter:
    """Tests for CodexAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = CodexAdapter(
            args=["exec", "--model", "{model}", "{prompt}"], timeout=90
        )
        assert adapter.command == "codex"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"This is the codex model response.", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])
        result = await adapter.invoke(prompt="What is 2+2?", model="gpt-4")

        assert result == "This is the codex model response."
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(
            args=["exec", "--model", "{model}", "{prompt}"], timeout=1
        )

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Model not available")
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_returns_cleaned_text(self):
        """Test output parsing returns cleaned text."""
        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])

        raw_output = "  Response with extra whitespace.  \n\n"
        result = adapter.parse_output(raw_output)

        assert result == "Response with extra whitespace."
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestGeminiAdapter:
    """Tests for GeminiAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"], timeout=90)
        assert adapter.command == "gemini"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"This is the gemini model response.", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"])
        result = await adapter.invoke(prompt="What is 2+2?", model="gemini-pro")

        assert result == "This is the gemini model response."
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"], timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Model not available")
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_returns_cleaned_text(self):
        """Test output parsing returns cleaned text."""
        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = "  Response with extra whitespace.  \n\n"
        result = adapter.parse_output(raw_output)

        assert result == "Response with extra whitespace."
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestDroidAdapter:
    """Tests for DroidAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = DroidAdapter(args=["exec", "{prompt}"], timeout=90)
        assert adapter.command == "droid"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"This is the droid model response.", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = DroidAdapter(args=["exec", "{prompt}"])
        result = await adapter.invoke(prompt="What is 2+2?", model="factory-1")

        assert result == "This is the droid model response."
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = DroidAdapter(args=["exec", "{prompt}"], timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Model not available")
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = DroidAdapter(args=["exec", "{prompt}"])

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_returns_cleaned_text(self):
        """Test output parsing returns cleaned text."""
        adapter = DroidAdapter(args=["exec", "{prompt}"])

        raw_output = "  Response with extra whitespace.  \n\n"
        result = adapter.parse_output(raw_output)

        assert result == "Response with extra whitespace."
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_droid_caches_skip_permissions_success(self, mock_subprocess):
        """Test that DroidAdapter caches successful skip-permissions method."""
        # Round 1: Mock --auto low/medium/high to fail, --skip-permissions-unsafe to succeed
        call_count = 0

        def subprocess_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_process = Mock()

            # Check if this invocation uses --skip-permissions-unsafe
            if "--skip-permissions-unsafe" in args:
                # Success with skip-permissions
                mock_process.communicate = AsyncMock(
                    return_value=(b"Response with skip-permissions", b"")
                )
                mock_process.returncode = 0
            else:
                # Fail for --auto attempts (permission denied)
                mock_process.communicate = AsyncMock(
                    return_value=(b"", b"Error: insufficient permission to proceed")
                )
                mock_process.returncode = 1

            return mock_process

        mock_subprocess.side_effect = subprocess_side_effect

        adapter = DroidAdapter(args=["exec", "-m", "{model}", "{prompt}"])

        # Round 1: Should try --auto low/medium/high, then fallback to --skip-permissions-unsafe
        result1 = await adapter.invoke(prompt="Round 1 prompt", model="factory-1")
        assert result1 == "Response with skip-permissions"

        # Should have tried 4 methods: auto low, auto medium, auto high, skip-permissions
        assert call_count == 4

        # Round 2: Should directly use skip-permissions (cache hit), no --auto attempts
        call_count = 0  # Reset counter
        result2 = await adapter.invoke(prompt="Round 2 prompt", model="factory-1")
        assert result2 == "Response with skip-permissions"

        # Should only try 1 method: skip-permissions (cached)
        assert call_count == 1

        # Verify the cached invocation used --skip-permissions-unsafe
        final_call_args = mock_subprocess.call_args[0]
        assert "--skip-permissions-unsafe" in final_call_args

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_droid_does_not_cache_auto_success(self, mock_subprocess):
        """Test that DroidAdapter does not cache when --auto succeeds normally."""
        call_count = 0

        def subprocess_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_process = Mock()

            # All invocations succeed (simulate --auto low working)
            mock_process.communicate = AsyncMock(
                return_value=(b"Response with auto low", b"")
            )
            mock_process.returncode = 0
            return mock_process

        mock_subprocess.side_effect = subprocess_side_effect

        adapter = DroidAdapter(args=["exec", "-m", "{model}", "{prompt}"])

        # Round 1: Should try --auto low and succeed immediately
        result1 = await adapter.invoke(prompt="Round 1 prompt", model="factory-1")
        assert result1 == "Response with auto low"
        assert call_count == 1  # Only tried --auto low

        # Round 2: Should try --auto low again (no cache)
        call_count = 0  # Reset counter
        result2 = await adapter.invoke(prompt="Round 2 prompt", model="factory-1")
        assert result2 == "Response with auto low"
        assert call_count == 1  # Tried --auto low again

        # Verify both rounds used --auto (not --skip-permissions-unsafe)
        first_call_args = mock_subprocess.call_args[0]
        assert "--auto" in first_call_args
        assert "--skip-permissions-unsafe" not in first_call_args


class TestCodexReasoningEffort:
    """Tests for CodexAdapter reasoning_effort injection."""

    def test_valid_reasoning_efforts(self):
        """Test CodexAdapter accepts all valid reasoning effort values."""
        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])

        # Valid Codex reasoning efforts
        assert "low" in adapter.VALID_REASONING_EFFORTS
        assert "medium" in adapter.VALID_REASONING_EFFORTS
        assert "high" in adapter.VALID_REASONING_EFFORTS
        assert "xhigh" in adapter.VALID_REASONING_EFFORTS

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_reasoning_effort_substituted_into_placeholder(self, mock_subprocess):
        """Test reasoning_effort is substituted into {reasoning_effort} placeholder."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Use config-style args with placeholder
        adapter = CodexAdapter(args=[
            "exec", "--model", "{model}",
            "-c", 'model_reasoning_effort="{reasoning_effort}"',
            "{prompt}"
        ])
        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort="high"
        )

        # Verify placeholder was substituted
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        assert "-c" in call_args
        # Find the index of -c and check next arg
        c_index = list(call_args).index("-c")
        config_value = call_args[c_index + 1]
        assert 'model_reasoning_effort="high"' in config_value

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invalid_reasoning_effort_raises_valueerror(self, mock_subprocess):
        """Test invalid reasoning_effort raises ValueError before subprocess call."""
        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])

        with pytest.raises(ValueError) as exc_info:
            await adapter.invoke(
                prompt="Test prompt",
                model="gpt-4",
                reasoning_effort="invalid-level"
            )

        assert "invalid reasoning_effort" in str(exc_info.value).lower()
        assert "invalid-level" in str(exc_info.value)
        # Subprocess should NOT have been called
        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_default_reasoning_effort_used_when_none(self, mock_subprocess):
        """Test default_reasoning_effort is used when reasoning_effort=None."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(
            args=["exec", "--model", "{model}", "-c", 'model_reasoning_effort="{reasoning_effort}"', "{prompt}"],
            default_reasoning_effort="medium"
        )
        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort=None  # Should use default
        )

        # Verify default was substituted
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)
        assert 'model_reasoning_effort="medium"' in args_str

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_reasoning_effort_overrides_default(self, mock_subprocess):
        """Test runtime reasoning_effort overrides default_reasoning_effort."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Has default of "low", but we pass "high" at runtime
        adapter = CodexAdapter(
            args=["exec", "-c", 'model_reasoning_effort="{reasoning_effort}"', "--model", "{model}", "{prompt}"],
            default_reasoning_effort="low"
        )

        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort="high"  # Override default
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)

        # Should have "high", not "low"
        assert '"high"' in args_str
        # Count occurrences - should only have one model_reasoning_effort
        assert args_str.count("model_reasoning_effort") == 1

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_empty_reasoning_effort_when_no_default(self, mock_subprocess):
        """Test empty string when no default and no runtime reasoning_effort."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # No default reasoning effort
        adapter = CodexAdapter(
            args=["exec", "-c", 'model_reasoning_effort="{reasoning_effort}"', "--model", "{model}", "{prompt}"]
        )

        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort=None
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)

        # Should have empty string substituted
        assert 'model_reasoning_effort=""' in args_str


class TestDroidReasoningEffort:
    """Tests for DroidAdapter reasoning_effort injection."""

    def test_valid_reasoning_efforts(self):
        """Test DroidAdapter accepts all valid reasoning effort values."""
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "{prompt}"])

        # Valid Droid reasoning efforts
        assert "off" in adapter.VALID_REASONING_EFFORTS
        assert "low" in adapter.VALID_REASONING_EFFORTS
        assert "medium" in adapter.VALID_REASONING_EFFORTS
        assert "high" in adapter.VALID_REASONING_EFFORTS

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_reasoning_effort_injected_as_r_flag(self, mock_subprocess):
        """Test reasoning_effort is substituted into {reasoning_effort} placeholder."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Use config.yaml format with {reasoning_effort} placeholder
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"])
        await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort="high"
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        assert "-r" in call_args
        r_index = list(call_args).index("-r")
        assert call_args[r_index + 1] == "high"

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_invalid_reasoning_effort_raises_valueerror(self, mock_subprocess):
        """Test invalid reasoning_effort raises ValueError before subprocess call."""
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "{prompt}"])

        with pytest.raises(ValueError) as exc_info:
            await adapter.invoke(
                prompt="Test prompt",
                model="factory-1",
                reasoning_effort="xhigh"  # Invalid for Droid (valid for Codex)
            )

        assert "invalid reasoning_effort" in str(exc_info.value).lower()
        assert "xhigh" in str(exc_info.value)
        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_reasoning_effort_off_injected(self, mock_subprocess):
        """Test 'off' reasoning_effort is correctly substituted."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Use config.yaml format with {reasoning_effort} placeholder
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"])
        await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort="off"
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        assert "-r" in call_args
        r_index = list(call_args).index("-r")
        assert call_args[r_index + 1] == "off"

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_reasoning_effort_with_permission_degradation(self, mock_subprocess):
        """Test reasoning_effort works correctly with permission degradation."""
        call_count = 0

        def subprocess_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_process = Mock()

            # First call (--auto low) fails with permission error
            if call_count == 1:
                mock_process.communicate = AsyncMock(
                    return_value=(b"", b"Error: insufficient permission to proceed")
                )
                mock_process.returncode = 1
            else:
                # Second call (--auto medium) succeeds
                mock_process.communicate = AsyncMock(
                    return_value=(b"Response with reasoning", b"")
                )
                mock_process.returncode = 0

            return mock_process

        mock_subprocess.side_effect = subprocess_side_effect

        # Use config.yaml format with {reasoning_effort} placeholder
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"])
        result = await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort="medium"
        )

        assert result == "Response with reasoning"
        assert call_count == 2  # Tried twice (low failed, medium succeeded)

        # Verify -r flag was substituted correctly in both calls
        for call in mock_subprocess.call_args_list:
            call_args = call[0]
            assert "-r" in call_args
            r_index = list(call_args).index("-r")
            assert call_args[r_index + 1] == "medium"

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_none_reasoning_effort_uses_empty_string(self, mock_subprocess):
        """Test None reasoning_effort substitutes empty string into placeholder."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Use config.yaml format with {reasoning_effort} placeholder
        adapter = DroidAdapter(args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"])
        await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort=None
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        # -r flag IS present (from config), value is empty string
        assert "-r" in call_args
        r_index = list(call_args).index("-r")
        assert call_args[r_index + 1] == ""  # Empty string when no reasoning_effort


class TestAdapterFactory:
    """Tests for create_adapter factory function."""

    def test_create_claude_code_adapter(self):
        """Test creating ClaudeAdapter via factory."""
        config = CLIToolConfig(
            command="claude",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=90,
        )
        adapter = create_adapter("claude", config)
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.command == "claude"
        assert adapter.timeout == 90

    def test_factory_passes_default_reasoning_effort_from_cli_adapter_config(self):
        """Test factory passes default_reasoning_effort from CLIAdapterConfig to adapter."""
        config = CLIAdapterConfig(
            type="cli",
            command="codex",
            args=["exec", "--model", "{model}", "-c", 'model_reasoning_effort="{reasoning_effort}"', "{prompt}"],
            timeout=120,
            default_reasoning_effort="high",
        )
        adapter = create_adapter("codex", config)

        assert isinstance(adapter, CodexAdapter)
        assert adapter.default_reasoning_effort == "high"

    def test_factory_passes_none_reasoning_effort_when_not_specified(self):
        """Test factory passes None when default_reasoning_effort not in config."""
        config = CLIAdapterConfig(
            type="cli",
            command="codex",
            args=["exec", "--model", "{model}", "{prompt}"],
            timeout=120,
        )
        adapter = create_adapter("codex", config)

        assert isinstance(adapter, CodexAdapter)
        assert adapter.default_reasoning_effort is None

    def test_factory_passes_default_reasoning_effort_to_droid(self):
        """Test factory passes default_reasoning_effort to DroidAdapter."""
        config = CLIAdapterConfig(
            type="cli",
            command="droid",
            args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"],
            timeout=180,
            default_reasoning_effort="medium",
        )
        adapter = create_adapter("droid", config)

        assert isinstance(adapter, DroidAdapter)
        assert adapter.default_reasoning_effort == "medium"

    def test_create_codex_adapter(self):
        """Test creating CodexAdapter via factory."""
        config = CLIToolConfig(
            command="codex", args=["--model", "{model}", "{prompt}"], timeout=120
        )
        adapter = create_adapter("codex", config)
        assert isinstance(adapter, CodexAdapter)
        assert adapter.command == "codex"
        assert adapter.timeout == 120

    def test_create_gemini_adapter(self):
        """Test creating GeminiAdapter via factory."""
        config = CLIToolConfig(
            command="gemini", args=["-m", "{model}", "-p", "{prompt}"], timeout=180
        )
        adapter = create_adapter("gemini", config)
        assert isinstance(adapter, GeminiAdapter)
        assert adapter.command == "gemini"
        assert adapter.timeout == 180

    def test_create_droid_adapter(self):
        """Test creating DroidAdapter via factory."""
        config = CLIToolConfig(command="droid", args=["exec", "{prompt}"], timeout=180)
        adapter = create_adapter("droid", config)
        assert isinstance(adapter, DroidAdapter)
        assert adapter.command == "droid"
        assert adapter.timeout == 180

    def test_create_llamacpp_adapter(self):
        """Test creating LlamaCppAdapter via factory."""
        from adapters.llamacpp import LlamaCppAdapter

        config = CLIToolConfig(
            command="llama-cli", args=["-m", "{model}", "-p", "{prompt}"], timeout=120
        )
        adapter = create_adapter("llamacpp", config)
        assert isinstance(adapter, LlamaCppAdapter)
        assert adapter.command == "llama-cli"
        assert adapter.timeout == 120

    def test_create_llamacpp_adapter_with_cli_adapter_config(self):
        """Test creating LlamaCppAdapter with new CLIAdapterConfig."""
        from adapters.llamacpp import LlamaCppAdapter

        config = CLIAdapterConfig(
            type="cli",
            command="llama-cli",
            args=["-m", "{model}", "-p", "{prompt}", "-n", "512"],
            timeout=180,
        )
        adapter = create_adapter("llamacpp", config)
        assert isinstance(adapter, LlamaCppAdapter)
        assert adapter.command == "llama-cli"
        assert adapter.timeout == 180

    def test_create_lmstudio_adapter(self):
        """Test creating LMStudioAdapter via factory."""
        from adapters.lmstudio import LMStudioAdapter

        config = HTTPAdapterConfig(
            type="http", base_url="http://localhost:1234", timeout=60, max_retries=3
        )

        adapter = create_adapter("lmstudio", config)
        assert isinstance(adapter, LMStudioAdapter)
        assert adapter.base_url == "http://localhost:1234"
        assert adapter.timeout == 60
        assert adapter.max_retries == 3

    def test_factory_rejects_cli_config_for_lmstudio(self):
        """Test LM Studio with CLI config raises error."""
        config = CLIAdapterConfig(type="cli", command="lmstudio", args=[], timeout=60)

        with pytest.raises(ValueError) as exc_info:
            create_adapter("lmstudio", config)

        # Should fail because lmstudio is not in CLI adapters
        assert "lmstudio" in str(exc_info.value).lower()
        assert "unknown cli adapter" in str(exc_info.value).lower()

    def test_create_ollama_adapter(self):
        """Test creating OllamaAdapter via factory."""
        from adapters.ollama import OllamaAdapter

        config = HTTPAdapterConfig(
            type="http", base_url="http://localhost:11434", timeout=120, max_retries=3
        )

        adapter = create_adapter("ollama", config)
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.base_url == "http://localhost:11434"
        assert adapter.timeout == 120
        assert adapter.max_retries == 3

    def test_factory_rejects_cli_config_for_ollama(self):
        """Test Ollama with CLI config raises error."""
        config = CLIAdapterConfig(type="cli", command="ollama", args=[], timeout=60)

        with pytest.raises(ValueError) as exc_info:
            create_adapter("ollama", config)

        # Should fail because ollama is not in CLI adapters
        assert "ollama" in str(exc_info.value).lower()
        assert "unknown cli adapter" in str(exc_info.value).lower()

    def test_create_openrouter_adapter(self):
        """Test creating OpenRouterAdapter via factory."""
        from adapters.openrouter import OpenRouterAdapter

        config = HTTPAdapterConfig(
            type="http",
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-test-key",
            timeout=90,
            max_retries=3,
        )

        adapter = create_adapter("openrouter", config)
        assert isinstance(adapter, OpenRouterAdapter)
        assert adapter.base_url == "https://openrouter.ai/api/v1"
        assert adapter.api_key == "sk-test-key"
        assert adapter.timeout == 90
        assert adapter.max_retries == 3

    def test_factory_rejects_cli_config_for_openrouter(self):
        """Test OpenRouter with CLI config raises error."""
        config = CLIAdapterConfig(type="cli", command="openrouter", args=[], timeout=60)

        with pytest.raises(ValueError) as exc_info:
            create_adapter("openrouter", config)

        # Should fail because openrouter is not in CLI adapters
        assert "openrouter" in str(exc_info.value).lower()
        assert "unknown cli adapter" in str(exc_info.value).lower()

    def test_create_adapter_with_default_timeout(self):
        """Test factory uses timeout from config object."""
        config = CLIToolConfig(
            command="claude",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=60,
        )
        adapter = create_adapter("claude", config)
        assert adapter.timeout == 60

    def test_create_adapter_invalid_cli(self):
        """Test factory raises error for invalid CLI tool name."""
        config = CLIToolConfig(
            command="invalid-cli", args=["--model", "{model}", "{prompt}"], timeout=60
        )
        with pytest.raises(ValueError) as exc_info:
            create_adapter("invalid-cli", config)

        assert "unsupported" in str(exc_info.value).lower()
        assert "invalid-cli" in str(exc_info.value)

    def test_create_adapter_with_cli_adapter_config(self):
        """Test creating adapter with new CLIAdapterConfig."""
        config = CLIAdapterConfig(
            type="cli", command="claude", args=["--model", "{model}"], timeout=60
        )
        adapter = create_adapter("claude", config)
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.command == "claude"
        assert adapter.timeout == 60

    def test_create_adapter_with_http_adapter_config_unknown_adapter(self):
        """Test HTTP adapter raises error for unknown adapter name."""
        config = HTTPAdapterConfig(
            type="http", base_url="http://localhost:9999", timeout=60
        )

        # Should raise because "unknown-http-adapter" is not registered
        with pytest.raises(ValueError) as exc_info:
            create_adapter("unknown-http-adapter", config)

        assert "unknown http adapter" in str(exc_info.value).lower()

    def test_factory_type_checking(self):
        """Test factory validates config type matches adapter expectations."""
        # This will be important when we add actual HTTP adapters
        # For now, just verify the factory can handle both config types
        cli_config = CLIAdapterConfig(
            type="cli", command="claude", args=["--model", "{model}"], timeout=60
        )
        adapter = create_adapter("claude", cli_config)
        assert isinstance(adapter, ClaudeAdapter)


class TestConfigBasedReasoningDefaults:
    """Tests for config-based reasoning effort defaults and priority (runtime > config > empty)."""

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_runtime_reasoning_effort_overrides_config_default(self, mock_subprocess):
        """Test runtime reasoning_effort takes priority over config default."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create adapter with config default of "low"
        adapter = CodexAdapter(
            args=["exec", "-c", 'model_reasoning_effort="{reasoning_effort}"', "--model", "{model}", "{prompt}"],
            default_reasoning_effort="low",
        )

        # Call with runtime reasoning_effort="high" (should override config default)
        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort="high",
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)

        # Should have "high" from runtime, NOT "low" from config
        assert 'model_reasoning_effort="high"' in args_str
        assert 'model_reasoning_effort="low"' not in args_str

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_config_default_used_when_runtime_is_none(self, mock_subprocess):
        """Test config default is used when reasoning_effort=None at runtime."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create adapter with config default
        adapter = CodexAdapter(
            args=["exec", "-c", 'model_reasoning_effort="{reasoning_effort}"', "--model", "{model}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        # Call without specifying reasoning_effort (should use config default)
        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort=None,
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)

        # Should have "medium" from config default
        assert 'model_reasoning_effort="medium"' in args_str

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_empty_string_when_no_default_and_no_runtime(self, mock_subprocess):
        """Test empty string is used when no config default and no runtime value."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create adapter WITHOUT config default
        adapter = CodexAdapter(
            args=["exec", "-c", 'model_reasoning_effort="{reasoning_effort}"', "--model", "{model}", "{prompt}"],
            # No default_reasoning_effort
        )

        # Call without specifying reasoning_effort
        await adapter.invoke(
            prompt="Test prompt",
            model="gpt-4",
            reasoning_effort=None,
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        args_str = " ".join(str(arg) for arg in call_args)

        # Should have empty string
        assert 'model_reasoning_effort=""' in args_str

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_droid_runtime_overrides_config_default(self, mock_subprocess):
        """Test Droid runtime reasoning_effort overrides config default."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create adapter with config default of "low"
        adapter = DroidAdapter(
            args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"],
            default_reasoning_effort="low",
        )

        # Call with runtime reasoning_effort="high"
        await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort="high",
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]

        # Find -r flag and check value
        assert "-r" in call_args
        r_index = list(call_args).index("-r")
        assert call_args[r_index + 1] == "high"

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_droid_config_default_used_when_runtime_none(self, mock_subprocess):
        """Test Droid uses config default when runtime reasoning_effort=None."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Response", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create adapter with config default
        adapter = DroidAdapter(
            args=["exec", "-m", "{model}", "-r", "{reasoning_effort}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        # Call without specifying reasoning_effort
        await adapter.invoke(
            prompt="Test prompt",
            model="factory-1",
            reasoning_effort=None,
        )

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]

        # Find -r flag and check value
        assert "-r" in call_args
        r_index = list(call_args).index("-r")
        assert call_args[r_index + 1] == "medium"

    def test_codex_invalid_reasoning_effort_validation(self):
        """Test CodexAdapter validates reasoning_effort values."""
        adapter = CodexAdapter(
            args=["exec", "--model", "{model}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        # Valid values should be accepted
        assert "low" in adapter.VALID_REASONING_EFFORTS
        assert "medium" in adapter.VALID_REASONING_EFFORTS
        assert "high" in adapter.VALID_REASONING_EFFORTS
        assert "xhigh" in adapter.VALID_REASONING_EFFORTS

        # Invalid values should not be in the set
        assert "off" not in adapter.VALID_REASONING_EFFORTS  # off is only valid for droid
        assert "invalid" not in adapter.VALID_REASONING_EFFORTS

    def test_droid_invalid_reasoning_effort_validation(self):
        """Test DroidAdapter validates reasoning_effort values."""
        adapter = DroidAdapter(
            args=["exec", "-m", "{model}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        # Valid values should be accepted
        assert "off" in adapter.VALID_REASONING_EFFORTS
        assert "low" in adapter.VALID_REASONING_EFFORTS
        assert "medium" in adapter.VALID_REASONING_EFFORTS
        assert "high" in adapter.VALID_REASONING_EFFORTS

        # Invalid values should not be in the set
        assert "xhigh" not in adapter.VALID_REASONING_EFFORTS  # xhigh is only valid for codex
        assert "invalid" not in adapter.VALID_REASONING_EFFORTS

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_codex_invalid_runtime_reasoning_effort_raises(self, mock_subprocess):
        """Test CodexAdapter raises ValueError for invalid runtime reasoning_effort."""
        adapter = CodexAdapter(
            args=["exec", "--model", "{model}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        with pytest.raises(ValueError) as exc_info:
            await adapter.invoke(
                prompt="Test",
                model="gpt-4",
                reasoning_effort="invalid-level",
            )

        assert "invalid reasoning_effort" in str(exc_info.value).lower()
        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    @patch("adapters.droid.asyncio.create_subprocess_exec")
    async def test_droid_invalid_runtime_reasoning_effort_raises(self, mock_subprocess):
        """Test DroidAdapter raises ValueError for invalid runtime reasoning_effort."""
        adapter = DroidAdapter(
            args=["exec", "-m", "{model}", "{prompt}"],
            default_reasoning_effort="medium",
        )

        with pytest.raises(ValueError) as exc_info:
            await adapter.invoke(
                prompt="Test",
                model="factory-1",
                reasoning_effort="xhigh",  # Invalid for droid (valid for codex)
            )

        assert "invalid reasoning_effort" in str(exc_info.value).lower()
        mock_subprocess.assert_not_called()


class TestWorkingDirectoryIsolation:
    """Tests for working_directory isolation in CLI adapters."""

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_uses_working_directory_as_cwd(self, mock_subprocess):
        """Test that invoke() uses working_directory as subprocess cwd."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Response from working directory", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(
            args=[
                "-p",
                "--model",
                "{model}",
                "--settings",
                '{{"disableAllHooks": true}}',
                "{prompt}",
            ]
        )

        # Invoke with working_directory parameter
        working_dir = "/tmp/test-repo"
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="claude-3-5-sonnet-20241022",
            working_directory=working_dir,
        )

        assert result == "Response from working directory"

        # Verify subprocess was called with correct cwd
        mock_subprocess.assert_called_once()
        call_kwargs = mock_subprocess.call_args[1]
        assert call_kwargs["cwd"] == working_dir

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_invoke_without_working_directory_uses_current_dir(
        self, mock_subprocess
    ):
        """Test that invoke() without working_directory uses current directory."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Response from current dir", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])

        # Invoke without working_directory parameter
        result = await adapter.invoke(prompt="What is 2+2?", model="gpt-4")

        assert result == "Response from current dir"

        # Verify subprocess was called with current directory as cwd
        mock_subprocess.assert_called_once()
        call_kwargs = mock_subprocess.call_args[1]
        # Should use current directory (getcwd equivalent)
        import os

        assert call_kwargs["cwd"] == os.getcwd()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_gemini_adapter_uses_working_directory(self, mock_subprocess):
        """Test that GeminiAdapter uses working_directory."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Gemini response from working dir", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = GeminiAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        working_dir = "/tmp/gemini-test"
        result = await adapter.invoke(
            prompt="Analyze this code",
            model="gemini-2.5-pro",
            working_directory=working_dir,
        )

        assert result == "Gemini response from working dir"

        # Verify subprocess was called with correct cwd
        mock_subprocess.assert_called_once()
        call_kwargs = mock_subprocess.call_args[1]
        assert call_kwargs["cwd"] == working_dir
