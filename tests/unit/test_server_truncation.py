"""Unit tests for server.py round truncation logic."""

import pytest
from models.schema import DeliberationResult, RoundResponse, Summary, ConvergenceInfo
from server import truncate_debate_rounds


class TestRoundTruncation:
    """Test deliberation round truncation for MCP responses."""

    def test_truncation_keeps_last_n_rounds(self):
        """Test truncation keeps only the last N round numbers."""
        # Create deliberation result with 5 rounds
        rounds = []
        for i in range(1, 6):
            rounds.append(
                RoundResponse(
                    round=i,
                    participant="claude",
                    response=f"Response from round {i}",
                    timestamp=f"2025-01-01T00:0{i}:00",
                )
            )

        result = DeliberationResult(
            status="complete",
            mode="standard",
            rounds_completed=5,
            participants=["claude"],
            full_debate=rounds,
            summary=Summary(
                consensus="Test consensus",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test recommendation",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=5,
                final_similarity=0.9,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=3)

        # Verify truncation
        assert result_dict["full_debate_truncated"] is True
        assert result_dict["total_rounds"] == 5
        assert len(result_dict["full_debate"]) == 3

        # Verify kept rounds are 3, 4, 5
        kept_rounds = {r["round"] for r in result_dict["full_debate"]}
        assert kept_rounds == {3, 4, 5}

    def test_truncation_with_multiple_responses_per_round(self):
        """Test truncation handles multiple participants per round."""
        # Create result with 2 participants over 4 rounds (8 responses)
        rounds = []
        for round_num in range(1, 5):
            for participant in ["claude", "gpt4"]:
                rounds.append(
                    RoundResponse(
                        round=round_num,
                        participant=participant,
                        response=f"{participant} response in round {round_num}",
                        timestamp=f"2025-01-01T00:{round_num:02d}:00",
                    )
                )

        result = DeliberationResult(
            status="complete",
            mode="standard",
            rounds_completed=4,
            participants=["claude", "gpt4"],
            full_debate=rounds,
            summary=Summary(
                consensus="Test consensus",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=4,
                final_similarity=0.9,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=2)

        # Should keep 4 responses (2 rounds x 2 participants)
        assert len(result_dict["full_debate"]) == 4
        assert result_dict["total_rounds"] == 4

        # Verify kept rounds are 3 and 4
        kept_rounds = {r["round"] for r in result_dict["full_debate"]}
        assert kept_rounds == {3, 4}

        # Verify both participants are in kept rounds
        kept_participants = {r["participant"] for r in result_dict["full_debate"]}
        assert kept_participants == {"claude", "gpt4"}

    def test_no_truncation_when_under_limit(self):
        """Test no truncation occurs when rounds <= max_rounds."""
        rounds = []
        for i in range(1, 3):
            rounds.append(
                RoundResponse(
                    round=i,
                    participant="claude",
                    response=f"Response {i}",
                    timestamp=f"2025-01-01T00:0{i}:00",
                )
            )

        result = DeliberationResult(
            status="complete",
            mode="quick",
            rounds_completed=2,
            participants=["claude"],
            full_debate=rounds,
            summary=Summary(
                consensus="Test",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=2,
                final_similarity=0.9,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=3)

        # Verify no truncation
        assert result_dict["full_debate_truncated"] is False
        assert "total_rounds" not in result_dict
        assert len(result_dict["full_debate"]) == 2

    def test_truncation_flag_set_correctly(self):
        """Test truncated flag is set correctly."""
        # Exactly at limit
        rounds_at_limit = [
            RoundResponse(
                round=i,
                participant="claude",
                response=f"Response {i}",
                timestamp=f"2025-01-01T00:0{i}:00",
            )
            for i in range(1, 4)
        ]

        result_at_limit = DeliberationResult(
            status="complete",
            mode="quick",
            rounds_completed=3,
            participants=["claude"],
            full_debate=rounds_at_limit,
            summary=Summary(
                consensus="Test",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=3,
                final_similarity=0.9,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result_at_limit, max_rounds=3)

        assert result_dict["full_debate_truncated"] is False

    def test_truncation_with_single_round(self):
        """Test truncation with only one round."""
        rounds = [
            RoundResponse(
                round=1,
                participant="claude",
                response="Single round",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = DeliberationResult(
            status="complete",
            mode="quick",
            rounds_completed=1,
            participants=["claude"],
            full_debate=rounds,
            summary=Summary(
                consensus="Quick decision",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Proceed",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=1,
                final_similarity=1.0,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=3)

        assert result_dict["full_debate_truncated"] is False
        assert len(result_dict["full_debate"]) == 1

    def test_truncation_preserves_round_order(self):
        """Test that truncation preserves the order of kept rounds."""
        rounds = []
        for i in range(1, 6):
            rounds.append(
                RoundResponse(
                    round=i,
                    participant="claude",
                    response=f"Response {i}",
                    timestamp=f"2025-01-01T00:0{i}:00",
                )
            )

        result = DeliberationResult(
            status="complete",
            mode="standard",
            rounds_completed=5,
            participants=["claude"],
            full_debate=rounds,
            summary=Summary(
                consensus="Test",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test",
            ),
            convergence_info=ConvergenceInfo(
                detected=True,
                detection_round=5,
                final_similarity=0.9,
                status="converged",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=2)

        # Verify order is preserved (4, 5)
        kept_round_numbers = [r["round"] for r in result_dict["full_debate"]]
        assert kept_round_numbers == [4, 5]

    def test_empty_debate_no_truncation(self):
        """Test truncation handles empty debate list."""
        result = DeliberationResult(
            status="complete",
            mode="quick",
            rounds_completed=0,
            participants=[],
            full_debate=[],
            summary=Summary(
                consensus="No deliberation",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="N/A",
            ),
            convergence_info=ConvergenceInfo(
                detected=False,
                detection_round=0,
                final_similarity=0.0,
                status="unknown",
                scores_by_round=[],
                per_participant_similarity={},
            ),
            transcript_path="/tmp/test.md",
        )

        # Use the production truncation helper
        result_dict = truncate_debate_rounds(result, max_rounds=3)

        assert result_dict["full_debate_truncated"] is False
        assert len(result_dict["full_debate"]) == 0
