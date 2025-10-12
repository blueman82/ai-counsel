"""Unit tests for CLI adapters."""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from adapters.base import BaseCLIAdapter
from adapters.claude_code import ClaudeCodeAdapter


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


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = ClaudeCodeAdapter(timeout=90)
        assert adapter.command == "claude-code"
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

        adapter = ClaudeCodeAdapter()
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="claude-3-5-sonnet-20241022"
        )

        assert result == "Actual model response here"
        mock_subprocess.assert_called_once()

    @patch('adapters.base.asyncio.create_subprocess_exec')
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCodeAdapter(timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

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

        adapter = ClaudeCodeAdapter()

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_extracts_response(self):
        """Test output parsing extracts model response."""
        adapter = ClaudeCodeAdapter()

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
