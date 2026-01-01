"""Pytest fixtures for all test modules."""

from typing import Optional
from unittest.mock import AsyncMock, Mock

import pytest

from adapters.base import BaseCLIAdapter


def create_mock_process(
    stdout_data: bytes = b"",
    stderr_data: bytes = b"",
    returncode: int = 0,
    timeout_on_read: bool = False,
    hang_on_read: bool = False,
) -> Mock:
    """
    Create a mock process compatible with _read_with_activity_timeout().

    This helper creates mocks for stdout.read(), stderr.read(), and wait()
    that work with asyncio.wait_for() and the chunked reading pattern.

    Args:
        stdout_data: Data to return from stdout
        stderr_data: Data to return from stderr
        returncode: Process return code
        timeout_on_read: If True, raise TimeoutError on read (deprecated, use hang_on_read)
        hang_on_read: If True, read() blocks forever (triggers activity timeout)

    Returns:
        Mock process object with properly configured async methods
    """
    import asyncio

    mock_process = Mock()

    # For stdout
    stdout_mock = Mock()
    stdout_read_called = [False]

    async def stdout_read(n: int = -1) -> bytes:
        if hang_on_read:
            # Block forever - will be cancelled by activity timeout
            await asyncio.sleep(3600)  # 1 hour, will be cancelled
            return b""
        if timeout_on_read:
            raise asyncio.TimeoutError()
        if not stdout_read_called[0]:
            stdout_read_called[0] = True
            return stdout_data
        return b""

    stdout_mock.read = stdout_read
    mock_process.stdout = stdout_mock

    # For stderr
    stderr_mock = Mock()
    stderr_read_called = [False]

    async def stderr_read(n: int = -1) -> bytes:
        if hang_on_read:
            # Block forever - will be cancelled by activity timeout
            await asyncio.sleep(3600)  # 1 hour, will be cancelled
            return b""
        if timeout_on_read:
            raise asyncio.TimeoutError()
        if not stderr_read_called[0]:
            stderr_read_called[0] = True
            return stderr_data
        return b""

    stderr_mock.read = stderr_read
    mock_process.stderr = stderr_mock

    # Mock wait() and kill()
    mock_process.wait = AsyncMock(return_value=returncode)
    mock_process.kill = Mock()
    mock_process.returncode = returncode

    # Keep communicate for backward compatibility (some tests may still use it)
    mock_process.communicate = AsyncMock(return_value=(stdout_data, stderr_data))

    return mock_process


class MockAdapter(BaseCLIAdapter):
    """Mock adapter for testing."""

    def __init__(self, name: str, timeout: int = 60):
        """Initialize mock adapter."""
        super().__init__(command=f"mock-{name}", args=[], timeout=timeout)
        self.name = name
        self.invoke_mock = AsyncMock()
        self.response_counter = 0
        # Set a default return value
        self._set_default_responses()

    def _set_default_responses(self):
        """Set sensible default responses for mock deliberations."""
        # Default response when no specific mock is configured
        # Use return_value instead of side_effect so tests can override easily
        default_response = "After careful analysis, I believe the proposed approach has merit. It addresses the core concerns while maintaining practical feasibility. The implementation timeline seems reasonable."
        self.invoke_mock.return_value = default_response
        self.response_counter = 0

    async def invoke(
        self,
        prompt: str,
        model: str,
        context: Optional[str] = None,
        is_deliberation: bool = True,
        working_directory: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """Mock invoke method."""
        result = await self.invoke_mock(
            prompt,
            model,
            context,
            is_deliberation,
            working_directory=working_directory,
            reasoning_effort=reasoning_effort,
        )
        self.response_counter += 1
        return result

    def parse_output(self, raw_output: str) -> str:
        """Mock parse_output method."""
        return raw_output.strip()


@pytest.fixture
def mock_adapters():
    """
    Create mock adapters for testing deliberation engine.

    Returns:
        dict: Dictionary of mock adapters by name
    """
    claude = MockAdapter("claude")
    codex = MockAdapter("codex")

    # Set default return values
    claude.invoke_mock.return_value = "Claude response"
    codex.invoke_mock.return_value = "Codex response"

    return {
        "claude": claude,
        "codex": codex,
    }


@pytest.fixture
def sample_config():
    """
    Sample configuration for testing.

    Returns:
        dict: Sample configuration dict
    """
    return {
        "defaults": {
            "mode": "quick",
            "rounds": 2,
            "max_rounds": 5,
            "timeout_per_round": 60,
        },
        "storage": {
            "transcripts_dir": "transcripts",
            "format": "markdown",
            "auto_export": True,
        },
        "deliberation": {
            "convergence_threshold": 0.8,
            "enable_convergence_detection": True,
        },
    }
