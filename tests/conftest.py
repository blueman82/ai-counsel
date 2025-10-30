"""Pytest fixtures for all test modules."""
from typing import Optional
from unittest.mock import AsyncMock

import pytest

from adapters.base import BaseCLIAdapter


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
        responses = [
            "After careful analysis, I believe the proposed approach has merit. It addresses the core concerns while maintaining practical feasibility. The implementation timeline seems reasonable.",
            "I see several valid points, though I'd like to emphasize the risk mitigation aspects. We should prioritize robustness and comprehensive testing.",
            "Both perspectives are valuable. I lean towards the collaborative approach as it balances innovation with stability. Let's proceed with Phase 1 as outlined.",
            "The discussion has been productive. I concur with the consensus emerging. The recommendations are sound and actionable.",
        ]
        self.invoke_mock.side_effect = lambda *args, **kwargs: responses[self.response_counter % len(responses)]
        self.response_counter = 0

    async def invoke(
        self, prompt: str, model: str, context: Optional[str] = None, is_deliberation: bool = True
    ) -> str:
        """Mock invoke method."""
        result = await self.invoke_mock(prompt, model, context, is_deliberation)
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
