"""Unit tests for deliberation engine."""
import pytest
from datetime import datetime
from pathlib import Path
from deliberation.engine import DeliberationEngine
from models.schema import Participant, RoundResponse, Vote


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
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude"].invoke_mock.return_value = "This is Claude's response"

        responses = await engine.execute_round(
            round_num=1,
            prompt="What is 2+2?",
            participants=participants,
            previous_responses=[]
        )

        assert len(responses) == 1
        assert isinstance(responses[0], RoundResponse)
        assert responses[0].round == 1
        assert responses[0].participant == "claude-3-5-sonnet@claude"
        assert responses[0].stance == "neutral"
        assert responses[0].response == "This is Claude's response"
        assert responses[0].timestamp is not None

    @pytest.mark.asyncio
    async def test_execute_round_multiple_participants(self, mock_adapters):
        """Test executing single round with multiple participants."""
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="for"),
            Participant(cli="codex", model="gpt-4", stance="against"),
        ]

        mock_adapters["claude"].invoke_mock.return_value = "Claude says yes"
        mock_adapters["codex"].invoke_mock.return_value = "Codex says no"

        responses = await engine.execute_round(
            round_num=1,
            prompt="Should we use TDD?",
            participants=participants,
            previous_responses=[]
        )

        assert len(responses) == 2
        assert responses[0].participant == "claude-3-5-sonnet@claude"
        assert responses[0].stance == "for"
        assert responses[0].response == "Claude says yes"
        assert responses[1].participant == "gpt-4@codex"
        assert responses[1].stance == "against"
        assert responses[1].response == "Codex says no"

    @pytest.mark.asyncio
    async def test_execute_round_includes_previous_context(self, mock_adapters):
        """Test that previous responses are included in context."""
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral")
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

        mock_adapters["claude"].invoke_mock.return_value = "New response"

        await engine.execute_round(
            round_num=2,
            prompt="Continue discussion",
            participants=participants,
            previous_responses=previous
        )

        # Verify invoke was called with context
        mock_adapters["claude"].invoke_mock.assert_called_once()
        call_args = mock_adapters["claude"].invoke_mock.call_args
        # Args are: (prompt, model, context)
        assert call_args[0][2] is not None  # context is 3rd positional arg
        assert "Previous response" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_execute_round_adapter_error_handling(self, mock_adapters):
        """Test graceful error handling when adapter fails."""
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral")
        ]

        mock_adapters["claude"].invoke_mock.side_effect = RuntimeError("API Error")

        # Should not raise, but return response with error message
        responses = await engine.execute_round(
            round_num=1,
            prompt="Test prompt",
            participants=participants,
            previous_responses=[]
        )

        assert len(responses) == 1
        assert "[ERROR: RuntimeError: API Error]" in responses[0].response

    @pytest.mark.asyncio
    async def test_execute_round_passes_correct_model(self, mock_adapters):
        """Test that correct model is passed to adapter."""
        mock_adapters["claude"] = mock_adapters["claude"]
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
        # Args are: (prompt, model, context)
        assert call_args[0][1] == "claude-3-opus"  # model is 2nd positional arg

    @pytest.mark.asyncio
    async def test_execute_round_timestamp_format(self, mock_adapters):
        """Test that timestamp is in ISO format."""
        mock_adapters["claude"] = mock_adapters["claude"]
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


class TestDeliberationEngineMultiRound:
    """Tests for DeliberationEngine multi-round execution."""

    @pytest.mark.asyncio
    async def test_execute_multiple_rounds(self, mock_adapters):
        """Test executing multiple rounds of deliberation."""
        from models.schema import DeliberateRequest

        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="What is the best programming language?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=3,
            mode="conference"
        )

        mock_adapters["claude"].invoke_mock.return_value = "Claude response"
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

        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=2,
            mode="conference"
        )

        mock_adapters["claude"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        await engine.execute(request)

        # Claude is used for: round 1, round 2, and summary generation
        # So should have at least 2 calls (for the 2 rounds)
        assert mock_adapters["claude"].invoke_mock.call_count >= 2
        second_call = mock_adapters["claude"].invoke_mock.call_args_list[1]
        # Check that context is passed in second deliberation round call
        assert second_call[0][2] is not None  # context should be present

    @pytest.mark.asyncio
    async def test_quick_mode_overrides_rounds(self, mock_adapters):
        """Test that quick mode forces single round regardless of request.rounds."""
        from models.schema import DeliberateRequest

        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=5,  # Request 5 rounds
            mode="quick"  # But quick mode should override to 1
        )

        mock_adapters["claude"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        result = await engine.execute(request)

        # Quick mode should force 1 round, not 5
        assert result.rounds_completed == 1
        assert len(result.full_debate) == 2  # 1 round * 2 participants

    @pytest.mark.asyncio
    async def test_engine_saves_transcript(self, mock_adapters, tmp_path):
        """Test that engine saves transcript after execution."""
        from deliberation.transcript import TranscriptManager
        from models.schema import DeliberateRequest

        manager = TranscriptManager(output_dir=str(tmp_path))

        request = DeliberateRequest(
            question="Should we use TypeScript?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet-20241022", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=1
        )

        mock_adapters["claude"] = mock_adapters["claude"]
        mock_adapters["claude"].invoke_mock.return_value = "Claude response"
        mock_adapters["codex"].invoke_mock.return_value = "Codex response"

        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager)
        result = await engine.execute(request)

        # Verify transcript was saved
        assert result.transcript_path
        assert Path(result.transcript_path).exists()

        # Verify content
        content = Path(result.transcript_path).read_text()
        assert "Should we use TypeScript?" in content


class TestVoteParsing:
    """Tests for vote parsing from model responses."""

    def test_parse_vote_from_response_valid_json(self):
        """Test parsing valid vote from response text."""
        response_text = '''
        I think Option A is better because it has lower risk.

        VOTE: {"option": "Option A", "confidence": 0.85, "rationale": "Lower risk and better fit"}
        '''

        engine = DeliberationEngine({})
        vote = engine._parse_vote(response_text)

        assert vote is not None
        assert isinstance(vote, Vote)
        assert vote.option == "Option A"
        assert vote.confidence == 0.85
        assert vote.rationale == "Lower risk and better fit"

    def test_parse_vote_from_response_no_vote(self):
        """Test parsing when no vote marker present."""
        response_text = "This is just a regular response without a vote"

        engine = DeliberationEngine({})
        vote = engine._parse_vote(response_text)

        assert vote is None

    def test_parse_vote_from_response_invalid_json(self):
        """Test parsing when vote JSON is malformed."""
        response_text = '''
        My analysis here.

        VOTE: {invalid json}
        '''

        engine = DeliberationEngine({})
        vote = engine._parse_vote(response_text)

        assert vote is None

    def test_parse_vote_from_response_missing_fields(self):
        """Test parsing when vote JSON missing required fields."""
        response_text = '''
        My analysis.

        VOTE: {"option": "Option A"}
        '''

        engine = DeliberationEngine({})
        vote = engine._parse_vote(response_text)

        assert vote is None

    def test_parse_vote_confidence_out_of_range(self):
        """Test parsing when confidence is out of valid range."""
        response_text = '''
        Analysis here.

        VOTE: {"option": "Yes", "confidence": 1.5, "rationale": "Test"}
        '''

        engine = DeliberationEngine({})
        vote = engine._parse_vote(response_text)

        assert vote is None

    @pytest.mark.asyncio
    async def test_execute_round_collects_votes(self, mock_adapters):
        """Test that votes are collected when present in responses."""
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(mock_adapters)

        participants = [
            Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral")
        ]

        # Response includes a vote
        response_with_vote = '''
        I recommend Option A because it has lower risk.

        VOTE: {"option": "Option A", "confidence": 0.9, "rationale": "Lower risk"}
        '''
        mock_adapters["claude"].invoke_mock.return_value = response_with_vote

        responses = await engine.execute_round(
            round_num=1,
            prompt="Which option?",
            participants=participants,
            previous_responses=[]
        )

        # Verify the response includes the full text
        assert len(responses) == 1
        assert "Option A" in responses[0].response

    @pytest.mark.asyncio
    async def test_execute_aggregates_voting_results(self, mock_adapters, tmp_path):
        """Test that votes are aggregated into VotingResult during execution."""
        from deliberation.transcript import TranscriptManager
        from models.schema import DeliberateRequest

        manager = TranscriptManager(output_dir=str(tmp_path))
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager)

        request = DeliberateRequest(
            question="Should we implement Option A or Option B?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=2,
            mode="conference"
        )

        # Both vote for Option A in round 1
        mock_adapters["claude"].invoke_mock.side_effect = [
            'Analysis: Option A is better\n\nVOTE: {"option": "Option A", "confidence": 0.9, "rationale": "Lower risk"}',
            'After review, still Option A\n\nVOTE: {"option": "Option A", "confidence": 0.95, "rationale": "Confirmed"}',
        ]
        mock_adapters["codex"].invoke_mock.side_effect = [
            'I agree with Option A\n\nVOTE: {"option": "Option A", "confidence": 0.85, "rationale": "Better performance"}',
            'Final vote: Option A\n\nVOTE: {"option": "Option A", "confidence": 0.9, "rationale": "Final decision"}',
        ]

        result = await engine.execute(request)

        # Verify voting_result is present
        assert result.voting_result is not None
        assert result.voting_result.consensus_reached is True
        assert result.voting_result.winning_option == "Option A"
        assert result.voting_result.final_tally["Option A"] == 4  # 2 participants x 2 rounds
        assert len(result.voting_result.votes_by_round) == 4


class TestVotingPrompts:
    """Tests for voting instruction prompts."""

    def test_build_voting_instructions(self):
        """Test that voting instructions are properly formatted."""
        engine = DeliberationEngine({})

        instructions = engine._build_voting_instructions()

        # Verify voting instructions contain key elements
        assert "VOTE:" in instructions
        assert "option" in instructions
        assert "confidence" in instructions
        assert "rationale" in instructions
        assert "0.0" in instructions or "0-1" in instructions or "between 0 and 1" in instructions.lower()

    def test_enhance_prompt_with_voting(self):
        """Test that prompt enhancement adds voting instructions."""
        engine = DeliberationEngine({})

        base_question = "Should we use TypeScript?"
        enhanced = engine._enhance_prompt_with_voting(base_question)

        # Verify enhanced prompt contains original question
        assert base_question in enhanced

        # Verify voting instructions are included
        assert "VOTE:" in enhanced
        assert "option" in enhanced.lower()
        assert "confidence" in enhanced.lower()
