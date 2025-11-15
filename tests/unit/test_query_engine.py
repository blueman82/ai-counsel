"""Tests for the decision graph query engine.

This module tests the QueryEngine class which provides a unified interface
for querying and analyzing the decision graph, used by both MCP tools and CLI.
"""

from datetime import datetime

import pytest

from decision_graph.schema import DecisionNode, ParticipantStance
from decision_graph.storage import DecisionGraphStorage
from deliberation.query_engine import QueryEngine, Timeline


@pytest.fixture
def storage():
    """Create in-memory database for testing."""
    return DecisionGraphStorage(":memory:")


@pytest.fixture
def sample_decisions(storage):
    """Create sample decisions for testing."""
    decisions = [
        DecisionNode(
            id="dec-1",
            question="Should we use TypeScript?",
            timestamp=datetime(2025, 10, 1, 10, 0, 0),
            consensus="TypeScript improves type safety",
            winning_option="Yes, adopt TypeScript",
            convergence_status="unanimous_consensus",
            participants=["opus@claude", "gpt4@codex"],
            transcript_path="/transcripts/dec1.md",
        ),
        DecisionNode(
            id="dec-2",
            question="Should we migrate to TypeScript?",
            timestamp=datetime(2025, 10, 2, 10, 0, 0),
            consensus="Phased migration approach recommended",
            winning_option="Gradual migration with 12-month timeline",
            convergence_status="majority_decision",
            participants=["opus@claude", "gpt4@codex", "gemini@google"],
            transcript_path="/transcripts/dec2.md",
        ),
        DecisionNode(
            id="dec-3",
            question="Should we use JavaScript for frontend?",
            timestamp=datetime(2025, 10, 3, 10, 0, 0),
            consensus="JavaScript remains standard for web",
            winning_option="JavaScript with type checking",
            convergence_status="converged",
            participants=["opus@claude", "gemini@google"],
            transcript_path="/transcripts/dec3.md",
        ),
    ]

    for decision in decisions:
        storage.save_decision_node(decision)

    return decisions


@pytest.fixture
def sample_stances(storage, sample_decisions):
    """Create sample participant stances."""
    stances = [
        ParticipantStance(
            decision_id="dec-1",
            participant="opus@claude",
            vote_option="Yes",
            confidence=0.95,
            rationale="Strong type safety benefits",
            final_position="TypeScript is the clear choice",
        ),
        ParticipantStance(
            decision_id="dec-1",
            participant="gpt4@codex",
            vote_option="Yes",
            confidence=0.85,
            rationale="Reduces runtime errors",
            final_position="Agree with TypeScript adoption",
        ),
        ParticipantStance(
            decision_id="dec-2",
            participant="opus@claude",
            vote_option="Gradual",
            confidence=0.9,
            rationale="Preserve existing code",
            final_position="Phased migration is best",
        ),
        ParticipantStance(
            decision_id="dec-3",
            participant="opus@claude",
            vote_option="Yes",
            confidence=0.88,
            rationale="Ecosystem maturity",
            final_position="JavaScript with types",
        ),
    ]

    for stance in stances:
        storage.save_participant_stance(stance)

    return stances


class TestQueryEngineSimilarSearch:
    """Test similar decision search functionality."""

    async def test_search_similar_basic(self, storage, sample_decisions):
        """Test basic similar search returns results."""
        engine = QueryEngine(storage)
        results = await engine.search_similar(
            query="TypeScript migration strategy", limit=5, threshold=0.5
        )

        assert results is not None
        assert isinstance(results, list)
        # Should find at least the TypeScript-related decisions
        assert len(results) > 0
        # Results should have required fields
        for result in results:
            assert hasattr(result, "decision")
            assert hasattr(result, "score")
            assert 0.0 <= result.score <= 1.0

    async def test_search_similar_with_threshold(self, storage, sample_decisions):
        """Test threshold filtering in similarity search."""
        engine = QueryEngine(storage)

        # High threshold should return fewer results
        high_threshold_results = await engine.search_similar(
            query="TypeScript", limit=10, threshold=0.9
        )

        # Lower threshold should return more results
        low_threshold_results = await engine.search_similar(
            query="TypeScript", limit=10, threshold=0.3
        )

        assert len(low_threshold_results) >= len(high_threshold_results)

    async def test_search_similar_respects_limit(self, storage, sample_decisions):
        """Test that limit parameter is respected."""
        engine = QueryEngine(storage)

        results = await engine.search_similar(
            query="TypeScript", limit=2, threshold=0.0
        )

        assert len(results) <= 2

    async def test_search_similar_returns_ordered_by_score(
        self, storage, sample_decisions
    ):
        """Test results are ordered by similarity score descending."""
        engine = QueryEngine(storage)

        results = await engine.search_similar(
            query="TypeScript", limit=10, threshold=0.0
        )

        if len(results) > 1:
            # Verify scores are in descending order
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score


class TestQueryEngineContradictions:
    """Test contradiction detection functionality."""

    async def test_find_contradictions_basic(self, storage, sample_decisions):
        """Test finding contradictions returns results."""
        engine = QueryEngine(storage)

        contradictions = await engine.find_contradictions()

        assert contradictions is not None
        assert isinstance(contradictions, list)

    async def test_find_contradictions_with_scope(self, storage, sample_decisions):
        """Test filtering contradictions by scope."""
        engine = QueryEngine(storage)

        contradictions = await engine.find_contradictions(scope="TypeScript")

        assert contradictions is not None
        assert isinstance(contradictions, list)

    async def test_find_contradictions_with_threshold(self, storage, sample_decisions):
        """Test contradiction threshold filtering."""
        engine = QueryEngine(storage)

        tight_contradictions = await engine.find_contradictions(threshold=0.9)

        loose_contradictions = await engine.find_contradictions(threshold=0.3)

        # Tighter threshold should find fewer contradictions
        assert len(tight_contradictions) <= len(loose_contradictions)


class TestQueryEngineEvolution:
    """Test decision evolution tracing functionality."""

    async def test_trace_evolution_basic(self, storage, sample_decisions):
        """Test tracing decision evolution."""
        engine = QueryEngine(storage)

        timeline = await engine.trace_evolution("dec-1")

        assert timeline is not None
        assert isinstance(timeline, Timeline)
        assert timeline.decision_id == "dec-1"

    async def test_trace_evolution_includes_metadata(self, storage, sample_decisions):
        """Test evolution timeline includes decision metadata."""
        engine = QueryEngine(storage)

        timeline = await engine.trace_evolution("dec-1")

        assert timeline.question is not None
        assert timeline.consensus is not None
        assert len(timeline.rounds) > 0

    async def test_trace_evolution_with_related(self, storage, sample_decisions):
        """Test evolution can include related decisions."""
        engine = QueryEngine(storage)

        timeline = await engine.trace_evolution("dec-1", include_related=True)

        assert timeline is not None
        # Related decisions should be populated
        if timeline.related_decisions:
            assert len(timeline.related_decisions) > 0

    async def test_trace_evolution_invalid_id(self, storage):
        """Test handling of non-existent decision ID."""
        engine = QueryEngine(storage)

        with pytest.raises(ValueError):
            await engine.trace_evolution("nonexistent-id")


class TestQueryEngineDiagnostics:
    """Test search diagnostics for empty/poor results."""

    def test_diagnostics_for_empty_results(self, storage):
        """Test diagnostics when no results above threshold."""
        # Create decision that will score below threshold
        decision = DecisionNode(
            id="dec-1",
            question="Should we use TypeScript?",
            timestamp=datetime(2025, 10, 1, 10, 0, 0),
            consensus="Yes",
            winning_option="Yes",
            convergence_status="converged",
            participants=["opus@claude"],
            transcript_path="/transcripts/dec1.md",
        )
        storage.save_decision_node(decision)

        engine = QueryEngine(storage)

        # Query unrelated topic with high threshold
        diagnostics = engine.get_search_diagnostics(
            "Python database optimization", limit=5, threshold=0.9
        )

        # Verify diagnostics structure
        assert "total_decisions" in diagnostics
        assert diagnostics["total_decisions"] == 1

        assert "best_match_score" in diagnostics
        assert diagnostics["best_match_score"] >= 0.0

        assert "near_misses" in diagnostics
        assert isinstance(diagnostics["near_misses"], list)

        assert "suggested_threshold" in diagnostics
        assert diagnostics["suggested_threshold"] < 0.9

        assert "matched_above_threshold" in diagnostics
        assert isinstance(diagnostics["matched_above_threshold"], list)

    def test_diagnostics_shows_near_misses(self, storage):
        """Test near-misses list includes decisions within 0.1 of threshold."""
        # Create decisions with varying similarity to query
        decisions = [
            DecisionNode(
                id="dec-close",
                question="autonomous agent evolution implementation",
                timestamp=datetime(2025, 10, 1, 10, 0, 0),
                consensus="Should implement Phase 1",
                winning_option="Yes",
                convergence_status="converged",
                participants=["opus@claude"],
                transcript_path="/transcripts/close.md",
            ),
            DecisionNode(
                id="dec-far",
                question="Database optimization strategies",
                timestamp=datetime(2025, 10, 2, 10, 0, 0),
                consensus="Use indexes",
                winning_option="Yes",
                convergence_status="converged",
                participants=["opus@claude"],
                transcript_path="/transcripts/far.md",
            ),
        ]

        for decision in decisions:
            storage.save_decision_node(decision)

        engine = QueryEngine(storage)

        # Query should score ~0.65-0.70 with "dec-close", low with "dec-far"
        diagnostics = engine.get_search_diagnostics(
            "autonomous agent",
            limit=5,
            threshold=0.75,  # High threshold to force near-miss
        )

        # Near-misses should exist (if close enough to threshold)
        assert "near_misses" in diagnostics
        assert isinstance(diagnostics["near_misses"], list)

        # Verify near-misses are within 0.1 of threshold (if any exist)
        for decision, score in diagnostics["near_misses"]:
            assert (
                score >= 0.65
            ), f"Near-miss score {score} should be >= threshold-0.1 (0.65)"
            assert score < 0.75, f"Near-miss score {score} should be < threshold (0.75)"

    def test_diagnostics_suggests_lower_threshold(self, storage):
        """Test suggested_threshold is adaptive based on best match."""
        # Create decision with known content
        decision = DecisionNode(
            id="dec-1",
            question="Python testing best practices",
            timestamp=datetime(2025, 10, 1, 10, 0, 0),
            consensus="Use pytest",
            winning_option="pytest",
            convergence_status="converged",
            participants=["opus@claude"],
            transcript_path="/transcripts/dec1.md",
        )
        storage.save_decision_node(decision)

        engine = QueryEngine(storage)

        # Query with very high threshold
        diagnostics = engine.get_search_diagnostics(
            "Python testing", limit=5, threshold=0.95
        )

        # Suggested threshold should be lower than current threshold
        assert diagnostics["suggested_threshold"] < 0.95

        # Suggested threshold should be at least 0.3 (min value)
        assert diagnostics["suggested_threshold"] >= 0.3

        # Should be rounded to nearest 0.05
        suggestion = diagnostics["suggested_threshold"]
        assert (suggestion * 20) == int(
            suggestion * 20
        ), f"Suggested threshold {suggestion} should be rounded to nearest 0.05"

    def test_diagnostics_with_results(self, storage):
        """Test diagnostics when results exist above threshold."""
        # Create decision that will match well
        decision = DecisionNode(
            id="dec-1",
            question="Should we use TypeScript for the project?",
            timestamp=datetime(2025, 10, 1, 10, 0, 0),
            consensus="Yes, TypeScript is recommended",
            winning_option="Yes",
            convergence_status="converged",
            participants=["opus@claude"],
            transcript_path="/transcripts/dec1.md",
        )
        storage.save_decision_node(decision)

        engine = QueryEngine(storage)

        # Query with low threshold (should find result)
        diagnostics = engine.get_search_diagnostics(
            "TypeScript project", limit=5, threshold=0.3
        )

        # Should have matched results
        assert diagnostics["matched_above_threshold"] is not None
        assert isinstance(diagnostics["matched_above_threshold"], list)

        # Best match score should be high
        assert diagnostics["best_match_score"] > 0.3

        # Total decisions should be 1
        assert diagnostics["total_decisions"] == 1

    def test_diagnostics_handles_empty_database(self, storage):
        """Test diagnostics gracefully handles empty database."""
        engine = QueryEngine(storage)

        # Query empty database
        diagnostics = engine.get_search_diagnostics("any query", limit=5, threshold=0.6)

        # Should return safe defaults
        assert diagnostics["total_decisions"] == 0
        assert diagnostics["best_match_score"] == 0.0
        assert diagnostics["matched_above_threshold"] == []
        assert diagnostics["near_misses"] == []
        assert diagnostics["suggested_threshold"] == 0.6


class TestQueryEngineIntegration:
    """Integration tests for query engine."""

    async def test_full_workflow(self, storage, sample_decisions, sample_stances):
        """Test complete query workflow."""
        engine = QueryEngine(storage)

        # 1. Search similar
        similar = await engine.search_similar("TypeScript", limit=5)
        assert len(similar) > 0

        # 2. Get details on first result
        if similar:
            timeline = await engine.trace_evolution(similar[0].decision.id)
            assert timeline is not None

        # 3. Find contradictions
        contradictions = await engine.find_contradictions()
        assert contradictions is not None

    async def test_performance_acceptable(
        self, storage, sample_decisions, sample_stances
    ):
        """Test that query performance is acceptable."""
        import time

        engine = QueryEngine(storage)

        # All queries should complete in reasonable time
        start = time.time()
        await engine.search_similar("test", limit=5)
        search_time = time.time() - start
        assert search_time < 1.0  # Should be fast with small dataset
