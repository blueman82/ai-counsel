"""Pydantic models for AI Counsel."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Participant(BaseModel):
    """Model representing a deliberation participant."""

    cli: Literal["claude-code", "codex"] = Field(
        ...,
        description="CLI tool to use for this participant"
    )
    model: str = Field(
        ...,
        description="Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'gpt-4')"
    )
    stance: Literal["neutral", "for", "against"] = Field(
        default="neutral",
        description="Stance for this participant"
    )


class DeliberateRequest(BaseModel):
    """Model for deliberation request."""

    question: str = Field(
        ...,
        min_length=10,
        description="The question or proposal to deliberate on"
    )
    participants: list[Participant] = Field(
        ...,
        min_length=2,
        description="List of participants (minimum 2)"
    )
    rounds: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of deliberation rounds (1-5)"
    )
    mode: Literal["quick", "conference"] = Field(
        default="quick",
        description="Deliberation mode"
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional additional context"
    )


class RoundResponse(BaseModel):
    """Model for a single round response from a participant."""

    round: int = Field(..., description="Round number")
    participant: str = Field(..., description="Participant identifier")
    stance: str = Field(..., description="Participant's stance")
    response: str = Field(..., description="The response text")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class Summary(BaseModel):
    """Model for deliberation summary."""

    consensus: str = Field(..., description="Overall consensus description")
    key_agreements: list[str] = Field(..., description="Points of agreement")
    key_disagreements: list[str] = Field(..., description="Points of disagreement")
    final_recommendation: str = Field(..., description="Final recommendation")


class DeliberationResult(BaseModel):
    """Model for complete deliberation result."""

    status: Literal["complete", "partial", "failed"] = Field(..., description="Status")
    mode: str = Field(..., description="Mode used")
    rounds_completed: int = Field(..., description="Rounds completed")
    participants: list[str] = Field(..., description="Participant identifiers")
    summary: Summary = Field(..., description="Deliberation summary")
    transcript_path: str = Field(..., description="Path to full transcript")
    full_debate: list[RoundResponse] = Field(..., description="Full debate history")
