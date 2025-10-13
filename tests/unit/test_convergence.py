"""Unit tests for convergence detection."""
import pytest

try:
    from deliberation.convergence import ConvergenceDetector
except ImportError:
    ConvergenceDetector = None

from deliberation.convergence import (
    JaccardBackend,
    TFIDFBackend,
    SentenceTransformerBackend,
)


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
            import sklearn
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
        # Should be higher than Jaccard due to TF-IDF weighting
        assert similarity > 0.3


# =============================================================================
# Sentence Transformer Backend Tests (optional dependency)
# =============================================================================

class TestSentenceTransformerBackend:
    """Test sentence transformer similarity."""

    @pytest.mark.skipif(
        not pytest.importorskip("sentence_transformers", minversion="2.0"),
        reason="sentence-transformers not installed"
    )
    def test_identical_text_returns_one(self):
        """Identical text should have similarity near 1.0."""
        backend = SentenceTransformerBackend()
        text = "The quick brown fox"
        similarity = backend.compute_similarity(text, text)
        assert similarity > 0.99

    @pytest.mark.skipif(
        not pytest.importorskip("sentence_transformers", minversion="2.0"),
        reason="sentence-transformers not installed"
    )
    def test_semantic_understanding(self):
        """Should understand semantic similarity."""
        backend = SentenceTransformerBackend()
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because it has types"
        similarity = backend.compute_similarity(text1, text2)
        # Should be high - same meaning
        assert similarity > 0.7


# =============================================================================
# Convergence Detector Tests (we'll add these in later tasks)
# =============================================================================

class TestConvergenceDetector:
    """Test convergence detection logic."""

    def test_placeholder(self):
        """Placeholder - will implement in Phase 3."""
        pass
