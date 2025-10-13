"""Unit tests for model-controlled early stopping."""
import pytest
from deliberation.engine import DeliberationEngine
from models.schema import Participant, DeliberateRequest
from models.config import Config, EarlyStoppingConfig, DeliberationConfig, ConvergenceDetectionConfig


class TestEarlyStopping:
    """Tests for model-controlled early stopping functionality."""

    @pytest.mark.asyncio
    async def test_early_stopping_when_all_models_want_to_stop(self, mock_adapters, tmp_path):
        """Test that deliberation stops early when all models set continue_debate=False."""
        from deliberation.transcript import TranscriptManager

        # Create config with early stopping enabled
        config = Config(
            version="1.0",
            cli_tools={},
            defaults={"mode": "conference", "rounds": 2, "max_rounds": 5, "timeout_per_round": 120},
            storage={"transcripts_dir": str(tmp_path), "format": "markdown", "auto_export": True},
            deliberation=DeliberationConfig(
                convergence_detection=ConvergenceDetectionConfig(
                    enabled=False,
                    semantic_similarity_threshold=0.85,
                    divergence_threshold=0.40,
                    min_rounds_before_check=1,
                    consecutive_stable_rounds=2,
                    stance_stability_threshold=0.80,
                    response_length_drop_threshold=0.40
                ),
                early_stopping=EarlyStoppingConfig(
                    enabled=True,
                    threshold=0.66,  # 66% must want to stop
                    respect_min_rounds=True
                ),
                convergence_threshold=0.8,
                enable_convergence_detection=False
            )
        )

        manager = TranscriptManager(output_dir=str(tmp_path))
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager, config=config)

        request = DeliberateRequest(
            question="Should we stop?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=5,  # Request 5 rounds
            mode="conference"
        )

        # Round 1: Models continue debating
        # Round 2: All models want to stop (continue_debate=False)
        mock_adapters["claude"].invoke_mock.side_effect = [
            'Round 1: Still thinking\n\nVOTE: {"option": "Yes", "confidence": 0.8, "rationale": "Initial thought", "continue_debate": true}',
            'Round 2: I am satisfied\n\nVOTE: {"option": "Yes", "confidence": 0.9, "rationale": "Final decision", "continue_debate": false}',
        ]
        mock_adapters["codex"].invoke_mock.side_effect = [
            'Round 1: Need more info\n\nVOTE: {"option": "Yes", "confidence": 0.7, "rationale": "First pass", "continue_debate": true}',
            'Round 2: Agreed, we can stop\n\nVOTE: {"option": "Yes", "confidence": 0.85, "rationale": "Confirmed", "continue_debate": false}',
        ]

        result = await engine.execute(request)

        # Should stop after round 2 (not continue to 5)
        assert result.rounds_completed == 2
        assert len(result.full_debate) == 4  # 2 rounds * 2 participants

    @pytest.mark.asyncio
    async def test_early_stopping_respects_min_rounds(self, mock_adapters, tmp_path):
        """Test that early stopping waits for minimum rounds."""
        from deliberation.transcript import TranscriptManager

        config = Config(
            version="1.0",
            cli_tools={},
            defaults={"mode": "conference", "rounds": 3, "max_rounds": 5, "timeout_per_round": 120},
            storage={"transcripts_dir": str(tmp_path), "format": "markdown", "auto_export": True},
            deliberation=DeliberationConfig(
                convergence_detection=ConvergenceDetectionConfig(
                    enabled=False,
                    semantic_similarity_threshold=0.85,
                    divergence_threshold=0.40,
                    min_rounds_before_check=1,
                    consecutive_stable_rounds=2,
                    stance_stability_threshold=0.80,
                    response_length_drop_threshold=0.40
                ),
                early_stopping=EarlyStoppingConfig(
                    enabled=True,
                    threshold=0.66,
                    respect_min_rounds=True  # Should respect min_rounds
                ),
                convergence_threshold=0.8,
                enable_convergence_detection=False
            )
        )

        manager = TranscriptManager(output_dir=str(tmp_path))
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager, config=config)

        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=3,  # Minimum 3 rounds
            mode="conference"
        )

        # All models want to stop immediately, but should wait for min_rounds
        mock_adapters["claude"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R2\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R3\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
        ]
        mock_adapters["codex"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R2\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R3\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
        ]

        result = await engine.execute(request)

        # Should complete all 3 rounds despite wanting to stop earlier
        assert result.rounds_completed == 3

    @pytest.mark.asyncio
    async def test_early_stopping_threshold_not_met(self, mock_adapters, tmp_path):
        """Test that deliberation continues when threshold not met."""
        from deliberation.transcript import TranscriptManager

        config = Config(
            version="1.0",
            cli_tools={},
            defaults={"mode": "conference", "rounds": 2, "max_rounds": 5, "timeout_per_round": 120},
            storage={"transcripts_dir": str(tmp_path), "format": "markdown", "auto_export": True},
            deliberation=DeliberationConfig(
                convergence_detection=ConvergenceDetectionConfig(
                    enabled=False,
                    semantic_similarity_threshold=0.85,
                    divergence_threshold=0.40,
                    min_rounds_before_check=1,
                    consecutive_stable_rounds=2,
                    stance_stability_threshold=0.80,
                    response_length_drop_threshold=0.40
                ),
                early_stopping=EarlyStoppingConfig(
                    enabled=True,
                    threshold=0.66,  # Need 66% (2/3) to stop
                    respect_min_rounds=True
                ),
                convergence_threshold=0.8,
                enable_convergence_detection=False
            )
        )

        manager = TranscriptManager(output_dir=str(tmp_path))
        mock_adapters["claude"] = mock_adapters["claude"]
        mock_adapters["gemini"] = mock_adapters["claude"]  # Add 3rd participant
        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager, config=config)

        request = DeliberateRequest(
            question="Continue debating?",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
                Participant(cli="gemini", model="gemini-2.5-pro", stance="neutral"),
            ],
            rounds=3,
            mode="conference"
        )

        # Only 1/3 want to stop (below 66% threshold)
        mock_adapters["claude"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R2\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R3\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
        ]
        mock_adapters["codex"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "B", "confidence": 0.8, "rationale": "Keep going", "continue_debate": true}',
            'R2\n\nVOTE: {"option": "B", "confidence": 0.8, "rationale": "Keep going", "continue_debate": true}',
            'R3\n\nVOTE: {"option": "B", "confidence": 0.8, "rationale": "Keep going", "continue_debate": true}',
        ]
        mock_adapters["gemini"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "B", "confidence": 0.7, "rationale": "Need more", "continue_debate": true}',
            'R2\n\nVOTE: {"option": "B", "confidence": 0.7, "rationale": "Need more", "continue_debate": true}',
            'R3\n\nVOTE: {"option": "B", "confidence": 0.7, "rationale": "Need more", "continue_debate": true}',
        ]

        result = await engine.execute(request)

        # Should complete all 3 rounds (threshold not met)
        assert result.rounds_completed == 3
        assert len(result.full_debate) == 9  # 3 rounds * 3 participants

    @pytest.mark.asyncio
    async def test_early_stopping_disabled(self, mock_adapters, tmp_path):
        """Test that early stopping can be disabled."""
        from deliberation.transcript import TranscriptManager

        config = Config(
            version="1.0",
            cli_tools={},
            defaults={"mode": "conference", "rounds": 2, "max_rounds": 5, "timeout_per_round": 120},
            storage={"transcripts_dir": str(tmp_path), "format": "markdown", "auto_export": True},
            deliberation=DeliberationConfig(
                convergence_detection=ConvergenceDetectionConfig(
                    enabled=False,
                    semantic_similarity_threshold=0.85,
                    divergence_threshold=0.40,
                    min_rounds_before_check=1,
                    consecutive_stable_rounds=2,
                    stance_stability_threshold=0.80,
                    response_length_drop_threshold=0.40
                ),
                early_stopping=EarlyStoppingConfig(
                    enabled=False,  # Disabled
                    threshold=0.66,
                    respect_min_rounds=True
                ),
                convergence_threshold=0.8,
                enable_convergence_detection=False
            )
        )

        manager = TranscriptManager(output_dir=str(tmp_path))
        mock_adapters["claude"] = mock_adapters["claude"]
        engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager, config=config)

        request = DeliberateRequest(
            question="Test",
            participants=[
                Participant(cli="claude", model="claude-3-5-sonnet", stance="neutral"),
                Participant(cli="codex", model="gpt-4", stance="neutral"),
            ],
            rounds=3,
            mode="conference"
        )

        # All models want to stop, but early stopping is disabled
        mock_adapters["claude"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R2\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R3\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
        ]
        mock_adapters["codex"].invoke_mock.side_effect = [
            'R1\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R2\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
            'R3\n\nVOTE: {"option": "A", "confidence": 0.9, "rationale": "Done", "continue_debate": false}',
        ]

        result = await engine.execute(request)

        # Should complete all rounds despite models wanting to stop
        assert result.rounds_completed == 3
