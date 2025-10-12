"""Unit tests for deliberation engine."""
import pytest
from datetime import datetime
from deliberation.engine import DeliberationEngine
from models.schema import Participant, RoundResponse


class TestDeliberationEngine:
    """Tests for DeliberationEngine single-round execution."""

    def test_engine_initialization(self, mock_adapters):
        """Test engine initializes with adapters."""
        engine = DeliberationEngine(mock_adapters)
        assert engine.adapters == mock_adapters
        assert len(engine.adapters) == 2

    @pytest.mark.asyncio
    async def test_execute_round_single_participant(self, mock_adapters):
        """Test executing single round with one participant."""
        # Add claude-code adapter for this test
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude-code"].invoke_mock.return_value = "This is Claude's response"

        responses = await engine.execute_round(
            round_num=1,
            prompt="What is 2+2?",
            participants=participants,
            previous_responses=[]
        )

        assert len(responses) == 1
        assert isinstance(responses[0], RoundResponse)
        assert responses[0].round == 1
        assert responses[0].participant == "claude-code"
        assert responses[0].stance == "neutral"
        assert responses[0].response == "This is Claude's response"
        assert responses[0].timestamp is not None

    @pytest.mark.asyncio
    async def test_execute_round_multiple_participants(self, mock_adapters):
        """Test executing single round with multiple participants."""
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-5-sonnet", stance="for"),
            Participant(cli="codex", model="gpt-4", stance="against"),
        ]

        mock_adapters["claude-code"].invoke_mock.return_value = "Claude says yes"
        mock_adapters["codex"].invoke_mock.return_value = "Codex says no"

        responses = await engine.execute_round(
            round_num=1,
            prompt="Should we use TDD?",
            participants=participants,
            previous_responses=[]
        )

        assert len(responses) == 2
        assert responses[0].participant == "claude-code"
        assert responses[0].stance == "for"
        assert responses[0].response == "Claude says yes"
        assert responses[1].participant == "codex"
        assert responses[1].stance == "against"
        assert responses[1].response == "Codex says no"

    @pytest.mark.asyncio
    async def test_execute_round_includes_previous_context(self, mock_adapters):
        """Test that previous responses are included in context."""
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral")
        ]

        previous = [
            RoundResponse(
                round=1,
                participant="codex",
                stance="for",
                response="Previous response",
                timestamp=datetime.now().isoformat()
            )
        ]

        mock_adapters["claude-code"].invoke_mock.return_value = "New response"

        await engine.execute_round(
            round_num=2,
            prompt="Continue discussion",
            participants=participants,
            previous_responses=previous
        )

        # Verify invoke was called with context
        mock_adapters["claude-code"].invoke_mock.assert_called_once()
        call_args = mock_adapters["claude-code"].invoke_mock.call_args
        assert call_args[1]["context"] is not None
        assert "Previous response" in call_args[1]["context"]

    @pytest.mark.asyncio
    async def test_execute_round_adapter_error_handling(self, mock_adapters):
        """Test error handling when adapter fails."""
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude-code"].invoke_mock.side_effect = RuntimeError("API Error")

        with pytest.raises(RuntimeError) as exc_info:
            await engine.execute_round(
                round_num=1,
                prompt="Test prompt",
                participants=participants,
                previous_responses=[]
            )

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_round_passes_correct_model(self, mock_adapters):
        """Test that correct model is passed to adapter."""
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-opus", stance="neutral")
        ]

        mock_adapters["claude"].invoke_mock.return_value = "Response"

        await engine.execute_round(
            round_num=1,
            prompt="Test",
            participants=participants,
            previous_responses=[]
        )

        call_args = mock_adapters["claude"].invoke_mock.call_args
        assert call_args[1]["model"] == "claude-3-opus"

    @pytest.mark.asyncio
    async def test_execute_round_timestamp_format(self, mock_adapters):
        """Test that timestamp is in ISO format."""
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude"].invoke_mock.return_value = "Response"

        responses = await engine.execute_round(
            round_num=1,
            prompt="Test",
            participants=participants,
            previous_responses=[]
        )

        timestamp = responses[0].timestamp
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(timestamp)
