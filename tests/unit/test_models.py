"""Unit tests for Pydantic models."""
import pytest
from pydantic import ValidationError
from models.schema import (
    Participant,
    DeliberateRequest,
    RoundResponse,
    DeliberationResult,
)


class TestParticipant:
    """Tests for Participant model."""

    def test_valid_participant(self):
        """Test creating a valid participant."""
        p = Participant(
            cli="claude",
            model="claude-3-5-sonnet-20241022",
            stance="neutral"
        )
        assert p.cli == "claude"
        assert p.model == "claude-3-5-sonnet-20241022"
        assert p.stance == "neutral"

    def test_participant_defaults_to_neutral_stance(self):
        """Test that stance defaults to neutral."""
        p = Participant(cli="codex", model="gpt-4")
        assert p.stance == "neutral"

    def test_invalid_cli_raises_error(self):
        """Test that invalid CLI tool raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Participant(cli="invalid-cli", model="gpt-4")
        assert "cli" in str(exc_info.value)

    def test_invalid_stance_raises_error(self):
        """Test that invalid stance raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Participant(cli="codex", model="gpt-4", stance="maybe")
        assert "stance" in str(exc_info.value)


class TestDeliberateRequest:
    """Tests for DeliberateRequest model."""

    def test_valid_request_minimal(self):
        """Test valid request with minimal fields."""
        req = DeliberateRequest(
            question="Should we use TypeScript?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet-20241022"),
                Participant(cli="codex", model="gpt-4"),
            ]
        )
        assert req.question == "Should we use TypeScript?"
        assert len(req.participants) == 2
        assert req.rounds == 2  # Default
        assert req.mode == "quick"  # Default

    def test_valid_request_full(self):
        """Test valid request with all fields."""
        req = DeliberateRequest(
            question="Should we refactor?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet-20241022", stance="for"),
                Participant(cli="codex", model="gpt-4", stance="against"),
            ],
            rounds=3,
            mode="conference",
            context="Legacy codebase, 50K LOC"
        )
        assert req.rounds == 3
        assert req.mode == "conference"
        assert req.context == "Legacy codebase, 50K LOC"

    def test_requires_at_least_two_participants(self):
        """Test that at least 2 participants are required."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[Participant(cli="codex", model="gpt-4")]
            )
        assert "participants" in str(exc_info.value)

    def test_rounds_must_be_positive(self):
        """Test that rounds must be >= 1."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[
                    Participant(cli="claude", model="claude-3-5-sonnet-20241022"),
                    Participant(cli="codex", model="gpt-4"),
                ],
                rounds=0
            )
        assert "rounds" in str(exc_info.value)

    def test_rounds_capped_at_five(self):
        """Test that rounds cannot exceed 5."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[
                    Participant(cli="claude", model="claude-3-5-sonnet-20241022"),
                    Participant(cli="codex", model="gpt-4"),
                ],
                rounds=10
            )
        assert "rounds" in str(exc_info.value)


class TestRoundResponse:
    """Tests for RoundResponse model."""

    def test_valid_round_response(self):
        """Test creating a valid round response."""
        resp = RoundResponse(
            round=1,
            participant="claude-3-5-sonnet@claude-code",
            stance="neutral",
            response="I think we should consider...",
            timestamp="2025-10-12T15:30:00Z"
        )
        assert resp.round == 1
        assert "claude-3-5-sonnet" in resp.participant


class TestDeliberationResult:
    """Tests for DeliberationResult model."""

    def test_valid_result(self):
        """Test creating a valid deliberation result."""
        result = DeliberationResult(
            status="complete",
            mode="conference",
            rounds_completed=2,
            participants=["claude-3-5-sonnet@claude-code", "gpt-4@codex"],
            summary={
                "consensus": "Strong agreement",
                "key_agreements": ["Point 1", "Point 2"],
                "key_disagreements": ["Detail A"],
                "final_recommendation": "Proceed with approach X"
            },
            transcript_path="/path/to/transcript.md",
            full_debate=[]
        )
        assert result.status == "complete"
        assert result.rounds_completed == 2
