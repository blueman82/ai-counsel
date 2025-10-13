"""End-to-end tests for full deliberation workflow.

PREREQUISITES:
- claude-code CLI must be installed and configured
- codex CLI must be installed and configured
- Both must have valid API keys
- These tests make REAL API calls and incur REAL costs

Run with: pytest tests/e2e -v -m e2e
"""
import pytest
from pathlib import Path
from models.schema import DeliberateRequest, Participant
from models.config import load_config
from adapters import create_adapter
from deliberation.engine import DeliberationEngine
from deliberation.transcript import TranscriptManager


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_deliberation_workflow(tmp_path):
    """
    Full E2E test of deliberation workflow.

    Tests:
    - Loading configuration
    - Creating real adapters (no mocks)
    - Multi-round deliberation (2 rounds)
    - Two participants (claude-code + codex)
    - Transcript generation
    - Response validation

    This test makes REAL API calls to both claude-code and codex.
    """
    # ARRANGE: Load config and create real adapters
    config = load_config()

    adapters = {
        "claude-code": create_adapter("claude-code", config.cli_tools["claude-code"]),
        "codex": create_adapter("codex", config.cli_tools["codex"]),
    }

    # Create transcript manager with temp directory
    transcript_manager = TranscriptManager(output_dir=str(tmp_path))

    # Create engine
    engine = DeliberationEngine(
        adapters=adapters,
        transcript_manager=transcript_manager
    )

    # Create request
    request = DeliberateRequest(
        question="What is 2+2? Please answer briefly in one sentence.",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
            Participant(cli="codex", model="gpt-4"),
        ],
        rounds=2,
        mode="conference"
    )

    # ACT: Execute deliberation
    result = await engine.execute(request)

    # ASSERT: Verify result structure
    assert result.status == "complete"
    assert result.rounds_completed == 2
    assert result.mode == "conference"
    assert len(result.participants) == 2
    assert len(result.full_debate) == 4  # 2 rounds x 2 participants

    # Verify participant identifiers
    assert "claude-3-5-sonnet-20241022@claude-code" in result.participants
    assert "gpt-4@codex" in result.participants

    # Verify responses contain the answer (4 or "four")
    for response in result.full_debate:
        assert response.response, "Response should not be empty"
        # Basic sanity check - responses should mention "4" or "four"
        response_lower = response.response.lower()
        assert "4" in response_lower or "four" in response_lower, \
            f"Response should contain the answer: {response.response[:100]}"

    # Verify rounds are properly numbered
    round_1_responses = [r for r in result.full_debate if r.round == 1]
    round_2_responses = [r for r in result.full_debate if r.round == 2]
    assert len(round_1_responses) == 2, "Round 1 should have 2 responses"
    assert len(round_2_responses) == 2, "Round 2 should have 2 responses"

    # Verify transcript was created
    assert result.transcript_path, "Transcript path should be set"
    transcript_file = Path(result.transcript_path)
    assert transcript_file.exists(), f"Transcript file should exist: {result.transcript_path}"

    # Verify transcript content
    content = transcript_file.read_text()
    assert "What is 2+2?" in content
    assert "claude-3-5-sonnet-20241022@claude-code" in content
    assert "gpt-4@codex" in content
    assert "## Summary" in content
    assert "## Full Debate" in content
    assert "### Round 1" in content
    assert "### Round 2" in content

    # Verify summary structure
    assert result.summary.consensus, "Summary should have consensus"
    assert isinstance(result.summary.key_agreements, list)
    assert isinstance(result.summary.key_disagreements, list)
    assert result.summary.final_recommendation, "Summary should have recommendation"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_quick_mode_single_round(tmp_path):
    """
    Test quick mode with single participant.

    Tests:
    - Quick mode overrides rounds config (forces 1 round)
    - Single participant workflow
    - Simpler question for faster execution

    This test makes a REAL API call to claude-code.
    """
    # ARRANGE
    config = load_config()

    adapters = {
        "claude-code": create_adapter("claude-code", config.cli_tools["claude-code"]),
    }

    engine = DeliberationEngine(
        adapters=adapters,
        transcript_manager=TranscriptManager(output_dir=str(tmp_path))
    )

    request = DeliberateRequest(
        question="What is the capital of France? Answer in one word only.",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
        ],
        rounds=3,  # Should be overridden by quick mode
        mode="quick"
    )

    # ACT
    result = await engine.execute(request)

    # ASSERT
    assert result.status == "complete"
    assert result.rounds_completed == 1, "Quick mode should only execute 1 round"
    assert result.mode == "quick"
    assert len(result.full_debate) == 1  # 1 round x 1 participant

    # Verify response contains "Paris"
    response = result.full_debate[0].response
    assert "paris" in response.lower(), f"Response should contain 'Paris': {response}"

    # Verify transcript
    assert Path(result.transcript_path).exists()
    content = Path(result.transcript_path).read_text()
    assert "What is the capital of France?" in content


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_deliberation_with_context(tmp_path):
    """
    Test deliberation with additional context provided.

    Tests:
    - Context is passed to participants
    - Participants can reference context in responses
    """
    # ARRANGE
    config = load_config()

    adapters = {
        "claude-code": create_adapter("claude-code", config.cli_tools["claude-code"]),
    }

    engine = DeliberationEngine(
        adapters=adapters,
        transcript_manager=TranscriptManager(output_dir=str(tmp_path))
    )

    request = DeliberateRequest(
        question="Should we use this framework?",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
        ],
        rounds=1,
        mode="quick",
        context="Framework: FastAPI. Project: REST API with 100K requests/day. Team: 5 Python developers."
    )

    # ACT
    result = await engine.execute(request)

    # ASSERT
    assert result.status == "complete"
    assert len(result.full_debate) == 1

    # Response should reference the context (FastAPI, REST API, etc.)
    response = result.full_debate[0].response.lower()
    # At least one context element should be mentioned
    context_mentioned = any(term in response for term in ["fastapi", "rest", "api", "python"])
    assert context_mentioned, f"Response should reference context: {response[:200]}"
