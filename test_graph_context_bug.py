#!/usr/bin/env python3
"""Test to reproduce graph_context_summary null issue after 2 deliberations."""

import tempfile
import os
from decision_graph.integration import DecisionGraphIntegration
from decision_graph.storage import DecisionGraphStorage
from models.schema import (
    DeliberationResult,
    RoundResponse,
    Summary,
    ConvergenceInfo,
)


def make_result(consensus: str, participants=None, transcript_path="/tmp/t.md"):
    """Helper to create minimal DeliberationResult for testing."""
    if participants is None:
        participants = ["p1"]

    return DeliberationResult(
        status="complete",
        mode="quick",
        rounds_completed=1,
        participants=participants,
        full_debate=[
            RoundResponse(
                round=1,
                participant=p,
                stance="neutral",
                response=f"Response from {p}",
                timestamp="2024-01-01T00:00:00Z",
            )
            for p in participants
        ],
        summary=Summary(
            consensus=consensus,
            key_agreements=[],
            key_disagreements=[],
            final_recommendation=consensus,
        ),
        convergence_info=ConvergenceInfo(
            detected=True,
            detection_round=1,
            final_similarity=0.95,
            status="converged",
            similarity_scores={},
        ),
        transcript_path=transcript_path,
    )


def test_graph_context_summary_after_two_deliberations():
    """Reproduce the bug: graph_context_summary is null after 2 deliberations."""

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Create integration with storage
        storage = DecisionGraphStorage(db_path)
        integration = DecisionGraphIntegration(storage, enable_background_worker=False)

        # First deliberation
        print("\n=== First Deliberation ===")
        result1 = make_result(
            consensus="Python is recommended for backend",
            participants=["model1", "model2"],
            transcript_path="/tmp/t1.md"
        )

        q1 = "Should we use Python for backend development?"
        decision_id_1 = integration.store_deliberation(q1, result1)
        print(f"Stored decision 1: {decision_id_1}")

        # Verify decision was stored
        node1 = storage.get_decision_node(decision_id_1)
        print(f"Retrieved decision 1: {node1.question if node1 else 'NOT FOUND'}")

        # Check what's in the database
        all_decisions_1 = storage.get_all_decisions(limit=100)
        print(f"Total decisions in DB after deliberation 1: {len(all_decisions_1)}")

        # Second deliberation
        print("\n=== Second Deliberation ===")
        q2 = "Should we use Python for API development?"

        # This is what the engine does - retrieve context BEFORE storing
        context = integration.get_context_for_deliberation(q2, threshold=0.7, max_context_decisions=3)
        print(f"Context retrieved for deliberation 2 (threshold=0.7): {repr(context)}")
        print(f"Context is empty: {not context}")

        # Try with lower threshold
        context_low = integration.get_context_for_deliberation(q2, threshold=0.5, max_context_decisions=3)
        print(f"Context retrieved for deliberation 2 (threshold=0.5): {repr(context_low)}")
        print(f"Context is empty: {not context_low}")

        # Try with even lower threshold
        context_lower = integration.get_context_for_deliberation(q2, threshold=0.3, max_context_decisions=3)
        print(f"Context retrieved for deliberation 2 (threshold=0.3): {repr(context_lower)}")
        print(f"Context is empty: {not context_lower}")

        # Store second result
        result2 = make_result(
            consensus="Python is good for APIs",
            participants=["model1", "model2"],
            transcript_path="/tmp/t2.md"
        )
        decision_id_2 = integration.store_deliberation(q2, result2)
        print(f"\nStored decision 2: {decision_id_2}")

        # Check what's in the database
        all_decisions_2 = storage.get_all_decisions(limit=100)
        print(f"Total decisions in DB after deliberation 2: {len(all_decisions_2)}")

        # Third deliberation - ask a VERY similar question to Q2
        # This should find context from Q2 since they're 95%+ similar
        print("\n=== Third Deliberation (Same Question as 2nd) ===")
        q3 = "Should we use Python for API development?"  # Exact same as Q2

        # Check what find_relevant_decisions returns
        from decision_graph.retrieval import DecisionRetriever
        retriever = integration.retriever
        relevant = retriever.find_relevant_decisions(q3, threshold=0.7, max_results=3)
        print(f"find_relevant_decisions returned {len(relevant)} decisions for Q3")
        for i, dec in enumerate(relevant):
            print(f"  {i+1}. {dec.question}")

        context3 = integration.get_context_for_deliberation(q3, threshold=0.7, max_context_decisions=3)
        print(f"Context retrieved for deliberation 3 (threshold=0.7): {repr('POPULATED' if context3 else 'EMPTY')}")
        print(f"Context is empty: {not context3}")

        # Compute similarity between Q2 and Q3
        from decision_graph.similarity import QuestionSimilarityDetector
        detector = QuestionSimilarityDetector()
        sim_q2_q3 = detector.compute_similarity(q2, q3)
        print(f"Similarity between Q2 and Q3: {sim_q2_q3:.3f} (should be 1.0 - same question)")

        # ANALYSIS
        print("\n=== ANALYSIS ===")
        print("Deliberation 1 question:", q1)
        print("Deliberation 2 question:", q2)

        # Check similarity detection
        from decision_graph.similarity import QuestionSimilarityDetector
        detector = QuestionSimilarityDetector()
        similarity = detector.compute_similarity(q1, q2)
        print(f"\nSimilarity between Q1 and Q2: {similarity:.3f}")

        print(f"\nBUG REPRODUCED: {not context and similarity > 0.5}")
        print("Expected: context should be populated if similarity > 0.5")
        print(f"Actual: context={'EMPTY' if not context else 'POPULATED'}, similarity={similarity:.3f}")

        # Check if decisions are even being retrieved
        print(f"\nDecisions in DB: {len(all_decisions_2)}")
        for i, decision in enumerate(all_decisions_2):
            print(f"  {i+1}. {decision.question}")

    finally:
        # Cleanup
        storage.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_graph_context_summary_after_two_deliberations()
