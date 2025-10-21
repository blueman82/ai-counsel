"""Unit tests for DecisionRetriever with caching integration."""

import time
from datetime import datetime, UTC
from unittest.mock import Mock, MagicMock, patch

import pytest

from decision_graph.cache import SimilarityCache
from decision_graph.retrieval import DecisionRetriever
from decision_graph.schema import DecisionNode
from decision_graph.storage import DecisionGraphStorage


@pytest.fixture
def mock_storage():
    """Create mock storage backend."""
    storage = Mock(spec=DecisionGraphStorage)
    return storage


@pytest.fixture
def sample_decisions():
    """Create sample decision nodes for testing."""
    return [
        DecisionNode(
            id="dec1",
            question="Should we use React or Vue?",
            timestamp=datetime.now(UTC),
            participants=["claude", "codex"],
            convergence_status="converged",
            consensus="React is preferred for larger applications",
            winning_option="React",
            transcript_path="transcripts/20240101_120000_React_or_Vue.md",
        ),
        DecisionNode(
            id="dec2",
            question="What database should we use?",
            timestamp=datetime.now(UTC),
            participants=["claude", "codex"],
            convergence_status="converged",
            consensus="PostgreSQL is recommended",
            winning_option="PostgreSQL",
            transcript_path="transcripts/20240101_120000_Database.md",
        ),
        DecisionNode(
            id="dec3",
            question="Should we adopt TypeScript?",
            timestamp=datetime.now(UTC),
            participants=["claude", "codex"],
            convergence_status="converged",
            consensus="TypeScript provides better type safety",
            winning_option="TypeScript",
            transcript_path="transcripts/20240101_120000_TypeScript.md",
        ),
    ]


class TestDecisionRetrieverCacheIntegration:
    """Test DecisionRetriever cache integration."""

    def test_init_with_cache_enabled_default(self, mock_storage):
        """Test initialization with caching enabled by default."""
        retriever = DecisionRetriever(mock_storage)

        assert retriever.cache is not None
        assert isinstance(retriever.cache, SimilarityCache)
        assert retriever.cache.query_cache.maxsize == 200
        assert retriever.cache.embedding_cache.maxsize == 500
        assert retriever.cache.query_ttl == 300

    def test_init_with_cache_disabled(self, mock_storage):
        """Test initialization with caching disabled."""
        retriever = DecisionRetriever(mock_storage, enable_cache=False)

        assert retriever.cache is None

    def test_init_with_custom_cache(self, mock_storage):
        """Test initialization with custom cache instance."""
        custom_cache = SimilarityCache(
            query_cache_size=100,
            embedding_cache_size=250,
            query_ttl=600,
        )

        retriever = DecisionRetriever(mock_storage, cache=custom_cache)

        assert retriever.cache is custom_cache
        assert retriever.cache.query_cache.maxsize == 100
        assert retriever.cache.embedding_cache.maxsize == 250
        assert retriever.cache.query_ttl == 600

    def test_find_relevant_decisions_cache_miss_then_hit(
        self, mock_storage, sample_decisions
    ):
        """Test cache miss followed by cache hit."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage)

        # Mock similarity detector to return predictable results
        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
            {"id": "dec3", "question": sample_decisions[2].question, "score": 0.75},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First call - cache miss
            results1 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )

            assert len(results1) == 2
            assert results1[0].id == "dec1"
            assert results1[1].id == "dec3"

            # Verify storage was accessed
            assert mock_storage.get_all_decisions.call_count == 1

            # Second call with same params - cache hit
            results2 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )

            assert len(results2) == 2
            assert results2[0].id == "dec1"
            assert results2[1].id == "dec3"

            # Storage should NOT be accessed again for similarity computation
            # (still 1 call from before, but get_decision_node called to reconstruct)
            assert mock_storage.get_all_decisions.call_count == 1

    def test_find_relevant_decisions_different_params_different_cache_keys(
        self, mock_storage, sample_decisions
    ):
        """Test different query parameters create different cache keys."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage)

        similar_results_1 = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]
        similar_results_2 = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
            {"id": "dec3", "question": sample_decisions[2].question, "score": 0.75},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar"
        ) as mock_find_similar:
            mock_find_similar.side_effect = [similar_results_1, similar_results_2]

            # Query with threshold=0.8
            results1 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.8, max_results=3
            )
            assert len(results1) == 1

            # Query with threshold=0.7 (different cache key)
            results2 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert len(results2) == 2

            # Both should trigger similarity computation (different cache keys)
            assert mock_find_similar.call_count == 2

    def test_find_relevant_decisions_cache_disabled(
        self, mock_storage, sample_decisions
    ):
        """Test find_relevant_decisions works with cache disabled."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage, enable_cache=False)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First call
            results1 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert len(results1) == 1

            # Second call - should recompute (no cache)
            results2 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert len(results2) == 1

            # Storage accessed both times
            assert mock_storage.get_all_decisions.call_count == 2

    def test_find_relevant_decisions_empty_result_cached(
        self, mock_storage, sample_decisions
    ):
        """Test empty results are cached to avoid recomputation."""
        mock_storage.get_all_decisions.return_value = sample_decisions

        retriever = DecisionRetriever(mock_storage)

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=[]
        ):
            # First call - no matches
            results1 = retriever.find_relevant_decisions(
                "Completely unrelated question?", threshold=0.7, max_results=3
            )
            assert len(results1) == 0

            # Second call - should hit cache (empty result cached)
            results2 = retriever.find_relevant_decisions(
                "Completely unrelated question?", threshold=0.7, max_results=3
            )
            assert len(results2) == 0

            # Storage accessed only once
            assert mock_storage.get_all_decisions.call_count == 1

    def test_find_relevant_decisions_cached_decision_deleted(
        self, mock_storage, sample_decisions
    ):
        """Test handling when cached decision has been deleted from storage."""
        mock_storage.get_all_decisions.return_value = sample_decisions

        retriever = DecisionRetriever(mock_storage)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
            {"id": "dec_deleted", "question": "Deleted decision", "score": 0.80},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First call - cache miss
            mock_storage.get_decision_node.side_effect = lambda id: (
                sample_decisions[0] if id == "dec1" else None
            )

            results1 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )

            # Should only return dec1 (dec_deleted not found)
            assert len(results1) == 1
            assert results1[0].id == "dec1"

            # Second call - cache hit, but dec_deleted still not found
            results2 = retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )

            assert len(results2) == 1
            assert results2[0].id == "dec1"

    def test_invalidate_cache(self, mock_storage, sample_decisions):
        """Test cache invalidation."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First query - cache miss
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert mock_storage.get_all_decisions.call_count == 1

            # Second query - cache hit
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert mock_storage.get_all_decisions.call_count == 1

            # Invalidate cache
            retriever.invalidate_cache()

            # Third query - cache miss again (invalidated)
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert mock_storage.get_all_decisions.call_count == 2

    def test_invalidate_cache_with_cache_disabled(self, mock_storage):
        """Test invalidate_cache does nothing when cache disabled."""
        retriever = DecisionRetriever(mock_storage, enable_cache=False)

        # Should not raise error
        retriever.invalidate_cache()

    def test_get_cache_stats_enabled(self, mock_storage, sample_decisions):
        """Test get_cache_stats with caching enabled."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # Generate some cache activity
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )  # miss
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )  # hit

            stats = retriever.get_cache_stats()

            assert stats is not None
            assert "l1_query_cache" in stats
            assert "l2_embedding_cache" in stats
            assert stats["l1_query_cache"]["hits"] == 1
            assert stats["l1_query_cache"]["misses"] == 1

    def test_get_cache_stats_disabled(self, mock_storage):
        """Test get_cache_stats returns None when cache disabled."""
        retriever = DecisionRetriever(mock_storage, enable_cache=False)

        stats = retriever.get_cache_stats()

        assert stats is None

    def test_cache_ttl_expiration(self, mock_storage, sample_decisions):
        """Test cache TTL expiration causes recomputation."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        # Create retriever with very short TTL for testing
        retriever = DecisionRetriever(
            mock_storage,
            cache=SimilarityCache(query_ttl=0.1),  # 100ms TTL
        )

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First query - cache miss
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert mock_storage.get_all_decisions.call_count == 1

            # Wait for TTL to expire
            time.sleep(0.15)

            # Second query - cache miss due to TTL expiration
            retriever.find_relevant_decisions(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert mock_storage.get_all_decisions.call_count == 2

    def test_get_enriched_context_uses_cache(self, mock_storage, sample_decisions):
        """Test get_enriched_context benefits from caching."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )
        mock_storage.get_participant_stances.return_value = []

        retriever = DecisionRetriever(mock_storage)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # First call - cache miss
            context1 = retriever.get_enriched_context(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert "React or Vue" in context1
            assert mock_storage.get_all_decisions.call_count == 1

            # Second call - cache hit
            context2 = retriever.get_enriched_context(
                "Should we use React?", threshold=0.7, max_results=3
            )
            assert context1 == context2
            assert mock_storage.get_all_decisions.call_count == 1

    def test_cache_hit_rate_tracking(self, mock_storage, sample_decisions):
        """Test cache hit rate is tracked correctly."""
        mock_storage.get_all_decisions.return_value = sample_decisions
        mock_storage.get_decision_node.side_effect = lambda id: next(
            (d for d in sample_decisions if d.id == id), None
        )

        retriever = DecisionRetriever(mock_storage)

        similar_results = [
            {"id": "dec1", "question": sample_decisions[0].question, "score": 0.85},
        ]

        with patch.object(
            retriever.similarity_detector, "find_similar", return_value=similar_results
        ):
            # 1 miss
            retriever.find_relevant_decisions(
                "Question 1?", threshold=0.7, max_results=3
            )

            # 3 hits
            retriever.find_relevant_decisions(
                "Question 1?", threshold=0.7, max_results=3
            )
            retriever.find_relevant_decisions(
                "Question 1?", threshold=0.7, max_results=3
            )
            retriever.find_relevant_decisions(
                "Question 1?", threshold=0.7, max_results=3
            )

            stats = retriever.get_cache_stats()

            assert stats["l1_query_cache"]["hits"] == 3
            assert stats["l1_query_cache"]["misses"] == 1
            assert stats["l1_query_cache"]["hit_rate"] == 0.75  # 3/4

    def test_empty_query_question_bypasses_cache(self, mock_storage):
        """Test empty query question returns empty list without cache access."""
        retriever = DecisionRetriever(mock_storage)

        results = retriever.find_relevant_decisions("", threshold=0.7, max_results=3)

        assert results == []
        mock_storage.get_all_decisions.assert_not_called()

        # Verify cache wasn't accessed
        stats = retriever.get_cache_stats()
        assert stats["l1_query_cache"]["hits"] == 0
        assert stats["l1_query_cache"]["misses"] == 0

    def test_no_decisions_in_storage_cached(self, mock_storage):
        """Test no decisions scenario is handled correctly."""
        mock_storage.get_all_decisions.return_value = []

        retriever = DecisionRetriever(mock_storage)

        # First call - cache miss
        results1 = retriever.find_relevant_decisions(
            "Any question?", threshold=0.7, max_results=3
        )
        assert results1 == []
        assert mock_storage.get_all_decisions.call_count == 1

        # Second call - should still check storage (no caching when storage empty)
        results2 = retriever.find_relevant_decisions(
            "Any question?", threshold=0.7, max_results=3
        )
        assert results2 == []
        # Note: Empty storage returns immediately, so no cache hit/miss logged
        assert mock_storage.get_all_decisions.call_count == 2
