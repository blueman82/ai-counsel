"""Unit tests for CLI adapters."""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from adapters.base import BaseCLIAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters import create_adapter
from models.config import CLIToolConfig


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
            args=["-p", "--model", "{model}", "--settings", '{{"disableAllHooks": true}}', "{prompt}"],
            timeout=90
        )
        assert adapter.command == "claude"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"Claude Code output\n\nActual model response here",
            b""
        ))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(args=["-p", "--model", "{model}", "--settings", '{{"disableAllHooks": true}}', "{prompt}"])
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="claude-3-5-sonnet-20241022"
        )

        assert result == "Actual model response here"
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(args=["-p", "--model", "{model}", "--settings", '{{"disableAllHooks": true}}', "{prompt}"], timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"",
            b"Error: Model not found"
        ))
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = ClaudeAdapter(args=["-p", "--model", "{model}", "--settings", '{{"disableAllHooks": true}}', "{prompt}"])

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_extracts_response(self):
        """Test output parsing extracts model response."""
        adapter = ClaudeAdapter(args=["-p", "--model", "{model}", "--settings", '{{"disableAllHooks": true}}', "{prompt}"])

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
        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"], timeout=90)
        assert adapter.command == "codex"
        assert adapter.timeout == 90

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"This is the codex model response.",
            b""
        ))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"])
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="gpt-4"
        )

        assert result == "This is the codex model response."
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter(args=["exec", "--model", "{model}", "{prompt}"], timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"",
            b"Error: Model not available"
        ))
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


class TestAdapterFactory:
    """Tests for create_adapter factory function."""

    def test_create_claude_code_adapter(self):
        """Test creating ClaudeAdapter via factory."""
        config = CLIToolConfig(
            command="claude",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=90
        )
        adapter = create_adapter("claude", config)
        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.command == "claude"
        assert adapter.timeout == 90

    def test_create_codex_adapter(self):
        """Test creating CodexAdapter via factory."""
        config = CLIToolConfig(
            command="codex",
            args=["--model", "{model}", "{prompt}"],
            timeout=120
        )
        adapter = create_adapter("codex", config)
        assert isinstance(adapter, CodexAdapter)
        assert adapter.command == "codex"
        assert adapter.timeout == 120

    def test_create_adapter_with_default_timeout(self):
        """Test factory uses timeout from config object."""
        config = CLIToolConfig(
            command="claude",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=60
        )
        adapter = create_adapter("claude", config)
        assert adapter.timeout == 60

    def test_create_adapter_invalid_cli(self):
        """Test factory raises error for invalid CLI tool name."""
        config = CLIToolConfig(
            command="invalid-cli",
            args=["--model", "{model}", "{prompt}"],
            timeout=60
        )
        with pytest.raises(ValueError) as exc_info:
            create_adapter("invalid-cli", config)

        assert "unsupported" in str(exc_info.value).lower()
        assert "invalid-cli" in str(exc_info.value)
