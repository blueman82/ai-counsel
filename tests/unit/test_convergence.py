"""Unit tests for convergence detection."""
import pytest

try:
    from deliberation.convergence import ConvergenceDetector
except ImportError:
    ConvergenceDetector = None

from deliberation.convergence import (JaccardBackend,
                                      SentenceTransformerBackend, TFIDFBackend)

# =============================================================================
# Jaccard Similarity Backend Tests
# =============================================================================


class TestJaccardBackend:
    """Test Jaccard similarity computation."""

    def test_identical_text_returns_one(self):
        """Identical text should have similarity of 1.0."""
        backend = JaccardBackend()
        text = "The quick brown fox jumps over the lazy dog"
        similarity = backend.compute_similarity(text, text)
        assert similarity == 1.0

    def test_completely_different_text_returns_zero(self):
        """Completely different text should have similarity near 0.0."""
        backend = JaccardBackend()
        text1 = "The quick brown fox"
        text2 = "airplane engine turbulence"
        similarity = backend.compute_similarity(text1, text2)
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Partially overlapping text should have intermediate similarity."""
        backend = JaccardBackend()
        text1 = "the quick brown fox"
        text2 = "the lazy brown dog"
        similarity = backend.compute_similarity(text1, text2)
        # Shared: {the, brown} = 2 words
        # Total: {the, quick, brown, fox, lazy, dog} = 6 words
        # Expected: 2/6 = 0.333...
        assert 0.3 <= similarity <= 0.4

    def test_case_insensitive(self):
        """Similarity should be case-insensitive."""
        backend = JaccardBackend()
        text1 = "The Quick Brown Fox"
        text2 = "the quick brown fox"
        similarity = backend.compute_similarity(text1, text2)
        assert similarity == 1.0

    def test_handles_empty_strings(self):
        """Empty strings should return 0.0 similarity."""
        backend = JaccardBackend()
        similarity = backend.compute_similarity("", "some text")
        assert similarity == 0.0


# =============================================================================
# TF-IDF Backend Tests (optional dependency)
# =============================================================================


class TestTFIDFBackend:
    """Test TF-IDF similarity computation."""

    def test_import_skipped_if_sklearn_missing(self):
        """Should skip if scikit-learn not installed."""
        try:
            import sklearn  # noqa: F401  # Import used to check availability

            pytest.skip("scikit-learn is installed, skip this test")
        except ImportError:
            with pytest.raises(ImportError):
                TFIDFBackend()

    def test_identical_text_returns_one(self):
        """Identical text should have similarity of 1.0."""
        pytest.importorskip("sklearn", minversion="1.0")
        backend = TFIDFBackend()
        text = "The quick brown fox jumps over the lazy dog"
        similarity = backend.compute_similarity(text, text)
        assert similarity == pytest.approx(1.0, abs=0.01)

    def test_semantic_similarity(self):
        """TF-IDF should capture some semantic similarity."""
        pytest.importorskip("sklearn", minversion="1.0")
        backend = TFIDFBackend()
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because of types"
        similarity = backend.compute_similarity(text1, text2)
        # TF-IDF with small corpus gives lower scores, just verify it computes
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.0  # Should have some overlap


# =============================================================================
# Sentence Transformer Backend Tests (optional dependency)
# =============================================================================


class TestSentenceTransformerBackend:
    """Test sentence transformer similarity."""

    def test_identical_text_returns_one(self):
        """Identical text should have similarity near 1.0."""
        pytest.importorskip("sentence_transformers", minversion="2.0")
        backend = SentenceTransformerBackend()
        text = "The quick brown fox"
        similarity = backend.compute_similarity(text, text)
        assert similarity > 0.99

    def test_semantic_understanding(self):
        """Should understand semantic similarity."""
        pytest.importorskip("sentence_transformers", minversion="2.0")
        backend = SentenceTransformerBackend()
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because it has types"
        similarity = backend.compute_similarity(text1, text2)
        # Should be high - same meaning
        assert similarity > 0.7


# =============================================================================
# Convergence Detector Tests
# =============================================================================


class TestConvergenceDetector:
    """Test convergence detection logic."""

    def test_detects_convergence_all_participants_stable(self):
        """Should detect convergence when all participants stabilize."""
        from models.schema import RoundResponse

        # Mock config
        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 1,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Round 2 responses
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is better for large projects",
                timestamp="2025-01-01T00:00:00",
            ),
            RoundResponse(
                round=2,
                participant="codex@cli",
                response="I agree TypeScript scales better",
                timestamp="2025-01-01T00:00:01",
            ),
        ]

        # Round 3 responses (very similar to round 2 - nearly identical)
        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="TypeScript is better for large projects",
                timestamp="2025-01-01T00:01:00",
            ),
            RoundResponse(
                round=3,
                participant="codex@cli",
                response="I agree TypeScript scales better",
                timestamp="2025-01-01T00:01:01",
            ),
        ]

        result = detector.check_convergence(
            current_round=round3, previous_round=round2, round_number=3
        )

        # With Jaccard similarity, these should be similar enough
        # to detect convergence (shared key words)
        assert result.converged is True
        assert result.status == "converged"
        assert result.min_similarity > 0.5  # At least moderate similarity

    def test_no_convergence_when_opinions_change(self):
        """Should not detect convergence when opinions change significantly."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 1,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Round 2: One participant says TypeScript
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is better",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        # Round 3: Same participant now says JavaScript
        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Actually JavaScript is more flexible",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = detector.check_convergence(
            current_round=round3, previous_round=round2, round_number=3
        )

        assert result.converged is False
        assert result.status in ["refining", "diverging"]

    def test_detects_divergence_with_different_opinions(self):
        """Should detect divergence when models have different opinions."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 1,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Round 2: Completely different responses with no word overlap
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="Static typing provides safety",
                timestamp="2025-01-01T00:00:00",
            ),
            RoundResponse(
                round=2,
                participant="codex@cli",
                response="Dynamic flexibility enables rapid prototyping",
                timestamp="2025-01-01T00:00:01",
            ),
        ]

        # Round 3: Still different responses
        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Compile-time checking catches bugs early",
                timestamp="2025-01-01T00:01:00",
            ),
            RoundResponse(
                round=3,
                participant="codex@cli",
                response="Runtime freedom allows creative solutions",
                timestamp="2025-01-01T00:01:01",
            ),
        ]

        result = detector.check_convergence(round3, round2, round_number=3)

        # Should detect low similarity (diverging or refining, not converged)
        assert result.converged is False
        assert result.status in ["diverging", "refining"]
        assert result.min_similarity < 0.50  # Very different responses

    def test_detects_impasse_after_consecutive_divergence(self):
        """Should detect impasse after repeated divergent rounds."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 2,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Use completely different topics to ensure low semantic similarity
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is the best programming language for enterprise applications",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Cooking Italian pasta requires fresh ingredients and olive oil",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        round4 = [
            RoundResponse(
                round=4,
                participant="claude@cli",
                response="Mountain hiking in winter demands proper equipment and training",
                timestamp="2025-01-01T00:02:00",
            )
        ]

        result_round3 = detector.check_convergence(
            current_round=round3, previous_round=round2, round_number=3
        )
        assert result_round3.status == "diverging"

        result_round4 = detector.check_convergence(
            current_round=round4, previous_round=round3, round_number=4
        )
        assert result_round4.converged is False
        assert result_round4.status == "impasse"

    def test_skips_check_before_min_rounds(self):
        """Should not check convergence before min_rounds_before_check."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,  # Don't check until round 3
                                "consecutive_stable_rounds": 1,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        round1 = [
            RoundResponse(
                round=1,
                participant="claude@cli",
                response="Initial response",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="Initial response",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        # Should not check at round 2
        result = detector.check_convergence(round2, round1, round_number=2)
        assert result is None or result.status == "refining"


class TestImpasseDetection:
    """Test impasse detection for stable disagreement scenarios."""

    def test_consecutive_divergent_count_increments_on_divergence(self):
        """Test consecutive_divergent_count increments correctly."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 2,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)
        assert detector.consecutive_divergent_count == 0

        # Create two completely unrelated responses to ensure divergence
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is the best programming language for enterprise applications",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Cooking Italian pasta requires fresh ingredients and olive oil",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = detector.check_convergence(round3, round2, round_number=3)

        assert result.status == "diverging"
        assert detector.consecutive_divergent_count == 1

    def test_consecutive_divergent_count_resets_on_convergence(self):
        """Test consecutive_divergent_count resets when convergence detected."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 2,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)
        detector.consecutive_divergent_count = 3

        # Create identical responses (converged)
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="We should proceed with option A",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="We should proceed with option A",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = detector.check_convergence(round3, round2, round_number=3)

        # Status should indicate non-divergence (converged or refining)
        assert result.status in ("converged", "refining")
        assert detector.consecutive_divergent_count == 0

    def test_consecutive_divergent_count_resets_on_refining(self):
        """Test consecutive_divergent_count resets when status is refining."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 2,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)
        detector.consecutive_divergent_count = 2

        # Create moderately similar responses (refining, not converged or diverging)
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="I think we should consider option A because it has merit",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="I think we should consider option A with some modifications",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = detector.check_convergence(round3, round2, round_number=3)
        
        # Should be refining (similarity between thresholds)
        assert result.status == "refining"
        assert detector.consecutive_divergent_count == 0

    def test_impasse_threshold_calculation(self):
        """Test impasse threshold uses max of 2 or consecutive_stable_rounds."""
        from models.schema import RoundResponse

        # Test with consecutive_stable_rounds = 1
        config1 = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 1,
                            },
                        )()
                    },
                )()
            },
        )()

        detector1 = ConvergenceDetector(config1)

        # Create completely unrelated responses to ensure divergence
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is the best programming language for enterprise applications",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Cooking Italian pasta requires fresh ingredients and olive oil",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        round4 = [
            RoundResponse(
                round=4,
                participant="claude@cli",
                response="Mountain hiking in winter demands proper equipment and training",
                timestamp="2025-01-01T00:02:00",
            )
        ]

        detector1.check_convergence(round3, round2, round_number=3)
        result = detector1.check_convergence(round4, round3, round_number=4)

        # Should require 2 rounds minimum (max(2, 1) = 2)
        assert result.status == "impasse"

    def test_impasse_not_triggered_before_threshold(self):
        """Test impasse requires consecutive divergent rounds."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 3,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Only 2 divergent rounds (threshold is 3) - use completely unrelated topics
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is the best programming language for enterprise applications",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Cooking Italian pasta requires fresh ingredients and olive oil",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        result = detector.check_convergence(round3, round2, round_number=3)

        assert result.status == "diverging"
        assert result.status != "impasse"

    def test_status_progression_to_impasse(self):
        """Test full progression: refining -> diverging -> impasse."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 2,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        rounds = [
            [
                RoundResponse(
                    round=2,
                    participant="claude@cli",
                    response="Initial consideration of options",
                    timestamp="2025-01-01T00:00:00",
                )
            ],
            [
                RoundResponse(
                    round=3,
                    participant="claude@cli",
                    response="Completely different approach",
                    timestamp="2025-01-01T00:01:00",
                )
            ],
            [
                RoundResponse(
                    round=4,
                    participant="claude@cli",
                    response="Yet another divergent path",
                    timestamp="2025-01-01T00:02:00",
                )
            ],
        ]

        # Round 3 should be diverging
        result3 = detector.check_convergence(rounds[1], rounds[0], round_number=3)
        assert result3.status == "diverging"

        # Round 4 should be impasse
        result4 = detector.check_convergence(rounds[2], rounds[1], round_number=4)
        assert result4.status == "impasse"

    def test_impasse_with_different_config_values(self):
        """Test impasse detection with various configuration values."""
        from models.schema import RoundResponse

        # Test with consecutive_stable_rounds = 5
        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 5,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Create 6 rounds of divergence with completely unrelated topics
        # (rounds 3-7 = 5 divergent checks since min_rounds_before_check=2 skips round 2)
        divergent_topics = [
            "TypeScript is the best programming language for enterprise applications",
            "Cooking Italian pasta requires fresh ingredients and olive oil",
            "Mountain hiking in winter demands proper equipment and training",
            "Classical music composition follows strict harmonic principles",
            "Deep sea diving requires specialized certification and gear",
            "Ancient Egyptian pyramids demonstrate remarkable engineering",
            "Quantum computing will revolutionize cryptography and security",
        ]

        for i in range(2, 8):  # rounds 2-7, but round 2 returns None (min_rounds_before_check)
            curr = [
                RoundResponse(
                    round=i,
                    participant="claude@cli",
                    response=divergent_topics[i - 1],
                    timestamp=f"2025-01-01T00:0{i}:00",
                )
            ]
            prev = [
                RoundResponse(
                    round=i - 1,
                    participant="claude@cli",
                    response=divergent_topics[i - 2],
                    timestamp=f"2025-01-01T00:0{i-1}:00",
                )
            ]
            result = detector.check_convergence(curr, prev, round_number=i)

        # After 5 divergent rounds (3, 4, 5, 6, 7), should be impasse
        assert result.status == "impasse"
        assert detector.consecutive_divergent_count == 5

    def test_impasse_interruption_resets_counter(self):
        """Test that a refining round interrupts impasse progression."""
        from models.schema import RoundResponse

        config = type(
            "Config",
            (),
            {
                "deliberation": type(
                    "Delib",
                    (),
                    {
                        "convergence_detection": type(
                            "Conv",
                            (),
                            {
                                "enabled": True,
                                "semantic_similarity_threshold": 0.85,
                                "divergence_threshold": 0.40,
                                "min_rounds_before_check": 2,
                                "consecutive_stable_rounds": 3,
                            },
                        )()
                    },
                )()
            },
        )()

        detector = ConvergenceDetector(config)

        # Two divergent rounds - use completely unrelated topics
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                response="TypeScript is the best programming language for enterprise applications",
                timestamp="2025-01-01T00:00:00",
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                response="Cooking Italian pasta requires fresh ingredients and olive oil",
                timestamp="2025-01-01T00:01:00",
            )
        ]

        detector.check_convergence(round3, round2, round_number=3)
        assert detector.consecutive_divergent_count == 1

        # Then a refining round (moderate similarity - same topic, different wording)
        round4 = [
            RoundResponse(
                round=4,
                participant="claude@cli",
                response="Making pasta at home needs quality ingredients like olive oil",
                timestamp="2025-01-01T00:02:00",
            )
        ]

        result = detector.check_convergence(round4, round3, round_number=4)
        
        # Should reset counter
        assert result.status == "refining"
        assert detector.consecutive_divergent_count == 0
