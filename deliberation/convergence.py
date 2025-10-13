"""Convergence detection for deliberation rounds."""
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Similarity Backend Interface
# =============================================================================

class SimilarityBackend(ABC):
    """Abstract base class for similarity computation backends."""

    @abstractmethod
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)
        """
        pass


# =============================================================================
# Jaccard Backend (Zero Dependencies)
# =============================================================================

class JaccardBackend(SimilarityBackend):
    """
    Jaccard similarity backend using word overlap.

    Formula: |A ∩ B| / |A ∪ B|

    Example:
        text1 = "the quick brown fox"
        text2 = "the lazy brown dog"

        A = {the, quick, brown, fox}
        B = {the, lazy, brown, dog}

        Intersection = {the, brown} = 2 words
        Union = {the, quick, brown, fox, lazy, dog} = 6 words

        Similarity = 2 / 6 = 0.333

    Pros:
        - Zero dependencies
        - Fast computation
        - Easy to understand

    Cons:
        - Doesn't understand semantics
        - Order-independent
        - Case-sensitive unless normalized
    """

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        # Handle empty strings
        if not text1 or not text2:
            return 0.0

        # Normalize: lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Handle case where both are empty after normalization
        if not words1 or not words2:
            return 0.0

        # Compute Jaccard similarity
        intersection = words1 & words2  # Words in both
        union = words1 | words2          # All unique words

        # Avoid division by zero
        if not union:
            return 0.0

        similarity = len(intersection) / len(union)
        return similarity


# =============================================================================
# TF-IDF Backend (Requires scikit-learn)
# =============================================================================

class TFIDFBackend(SimilarityBackend):
    """
    TF-IDF similarity backend.

    Requires: scikit-learn

    Better than Jaccard because:
        - Weighs rare words higher (more discriminative)
        - Reduces impact of common words (the, a, is)
        - Still lightweight (~50MB)

    Example:
        text1 = "TypeScript has types"
        text2 = "TypeScript provides type safety"

        TF-IDF will weight "TypeScript" and "type(s)" highly,
        downweight "has" and "provides"
    """

    def __init__(self):
        """Initialize TF-IDF backend."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.vectorizer = TfidfVectorizer()
            self.cosine_similarity = cosine_similarity
        except ImportError as e:
            raise ImportError(
                "TFIDFBackend requires scikit-learn. "
                "Install with: pip install scikit-learn"
            ) from e

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        # Compute TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])

        # Compute cosine similarity
        similarity = self.cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

        return float(similarity)


# =============================================================================
# Sentence Transformer Backend (Requires sentence-transformers)
# =============================================================================

class SentenceTransformerBackend(SimilarityBackend):
    """
    Sentence transformer backend using neural embeddings.

    Requires: sentence-transformers (~500MB model download)

    Best accuracy because:
        - Understands semantics and context
        - Trained on billions of sentence pairs
        - Captures paraphrasing and synonyms

    Example:
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because it has types"

        These have similar meaning despite different words.
        Sentence transformers will give high similarity (~0.85).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence transformer backend.

        Args:
            model_name: Model to use (default: all-MiniLM-L6-v2)
                       This is a good balance of speed and accuracy.
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            logger.info(f"Loading sentence transformer model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.cosine_similarity = cosine_similarity
            logger.info("Sentence transformer model loaded successfully")

        except ImportError as e:
            raise ImportError(
                "SentenceTransformerBackend requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            ) from e

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity using sentence embeddings."""
        if not text1 or not text2:
            return 0.0

        # Generate embeddings (vectors that capture meaning)
        embeddings = self.model.encode([text1, text2])

        # Compute cosine similarity between embeddings
        similarity = self.cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1)
        )[0][0]

        return float(similarity)
