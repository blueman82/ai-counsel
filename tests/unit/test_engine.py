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
        assert responses[0].participant == "claude-3-5-sonnet@claude-code"
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
        assert responses[0].participant == "claude-3-5-sonnet@claude-code"
        assert responses[0].stance == "for"
        assert responses[0].response == "Claude says yes"
        assert responses[1].participant == "gpt-4@codex"
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
        # Args are: (prompt, model, context)
        assert call_args[0][2] is not None  # context is 3rd positional arg
        assert "Previous response" in call_args[0][2]

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
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-opus", stance="neutral")
        ]

        mock_adapters["claude-code"].invoke_mock.return_value = "Response"

        await engine.execute_round(
            round_num=1,
            prompt="Test",
            participants=participants,
            previous_responses=[]
        )

        call_args = mock_adapters["claude-code"].invoke_mock.call_args
        # Args are: (prompt, model, context)
        assert call_args[0][1] == "claude-3-opus"  # model is 2nd positional arg

    @pytest.mark.asyncio
    async def test_execute_round_timestamp_format(self, mock_adapters):
        """Test that timestamp is in ISO format."""
        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude-code"].invoke_mock.return_value = "Response"

        responses = await engine.execute_round(
            round_num=1,
            prompt="Test",
            participants=participants,
            previous_responses=[]
        )

        timestamp = responses[0].timestamp
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(timestamp)


class TestDeliberationEngineMultiRound:
    """Tests for DeliberationEngine multi-round execution."""

    @pytest.mark.asyncio
    async def test_execute_multiple_rounds(self, mock_adapters):
        """Test executing multiple rounds of deliberation."""
        from models.schema import DeliberateRequest

        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="What is the best programming language?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=3,
            mode="conference"
        )

        mock_adapters["claude-code"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        result = await engine.execute(request)

        # Verify result structure
        assert result.status == "complete"
        assert result.rounds_completed == 3
        assert len(result.full_debate) == 6  # 3 rounds * 2 participants
        assert len(result.participants) == 2

    @pytest.mark.asyncio
    async def test_execute_context_builds_across_rounds(self, mock_adapters):
        """Test that context accumulates across rounds."""
        from models.schema import DeliberateRequest

        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=2,
            mode="conference"
        )

        mock_adapters["claude-code"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        await engine.execute(request)

        # Second round should have context from first round
        assert mock_adapters["claude-code"].invoke_mock.call_count == 2
        second_call = mock_adapters["claude-code"].invoke_mock.call_args_list[1]
        # Check that context is passed in second call
        assert second_call[0][2] is not None  # context should be present

    @pytest.mark.asyncio
    async def test_quick_mode_overrides_rounds(self, mock_adapters):
        """Test that quick mode forces single round regardless of request.rounds."""
        from models.schema import DeliberateRequest

        mock_adapters["claude-code"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=5,  # Request 5 rounds
            mode="quick"  # But quick mode should override to 1
        )

        mock_adapters["claude-code"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        result = await engine.execute(request)

        # Quick mode should force 1 round, not 5
        assert result.rounds_completed == 1
        assert len(result.full_debate) == 2  # 1 round * 2 participants
