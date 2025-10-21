"""Integration layer connecting decision graph memory to deliberation engine.

This module provides the DecisionGraphIntegration class, which acts as a facade
for all decision graph operations. It handles storing completed deliberations,
computing similarities between decisions, and retrieving enriched context for
new deliberations.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
import logging

from decision_graph.storage import DecisionGraphStorage
from decision_graph.schema import DecisionNode, ParticipantStance, DecisionSimilarity
from decision_graph.retrieval import DecisionRetriever
from decision_graph.similarity import QuestionSimilarityDetector
from models.schema import DeliberationResult

logger = logging.getLogger(__name__)


class DecisionGraphIntegration:
    """Integration layer connecting decision graph memory to deliberation engine.

    This class provides a high-level API for:
    - Storing completed deliberations in the decision graph
    - Computing semantic similarities between decisions
    - Retrieving enriched context for new deliberations

    It acts as a facade, coordinating between storage, retrieval, and similarity
    detection components while providing graceful error handling to ensure that
    decision graph issues never break deliberation execution.

    Example:
        >>> storage = DecisionGraphStorage("decisions.db")
        >>> integration = DecisionGraphIntegration(storage)
        >>>
        >>> # After deliberation completes
        >>> decision_id = integration.store_deliberation(question, result)
        >>>
        >>> # Before starting new deliberation
        >>> context = integration.get_context_for_deliberation(new_question)
        >>> # Use context to enrich prompts
    """

    def __init__(self, storage: DecisionGraphStorage):
        """Initialize integration with storage backend.

        Args:
            storage: DecisionGraphStorage instance for persistence
        """
        self.storage = storage
        self.retriever = DecisionRetriever(storage)
        logger.info("Initialized DecisionGraphIntegration")

    def store_deliberation(
        self, question: str, result: DeliberationResult
    ) -> str:
        """Store completed deliberation in decision graph.

        Extracts data from DeliberationResult and saves:
        - Decision node with metadata, consensus, and convergence status
        - Participant stances with votes, confidence, and rationale
        - Similarity relationships to past decisions (async computation)

        Args:
            question: The deliberation question
            result: DeliberationResult from deliberation engine

        Returns:
            The decision node ID (UUID)

        Raises:
            Exception: Re-raises storage errors after logging (caller should handle)

        Example:
            >>> integration = DecisionGraphIntegration(storage)
            >>> result = await engine.execute(request)
            >>> decision_id = integration.store_deliberation(
            ...     request.question,
            ...     result
            ... )
            >>> print(f"Stored decision: {decision_id}")
        """
        try:
            # Extract winning option from voting result
            winning_option = None
            if result.voting_result and result.voting_result.winning_option:
                winning_option = result.voting_result.winning_option

            # Extract consensus from summary
            consensus = ""
            if result.summary and result.summary.consensus:
                consensus = result.summary.consensus

            # Extract convergence status
            convergence_status = "unknown"
            if result.convergence_info and result.convergence_info.status:
                convergence_status = result.convergence_info.status

            # Create decision node
            node = DecisionNode(
                id=str(uuid4()),
                question=question,
                timestamp=datetime.now(),
                consensus=consensus,
                winning_option=winning_option,
                convergence_status=convergence_status,
                participants=result.participants,
                transcript_path=result.transcript_path or "",
            )

            # Save decision node
            decision_id = self.storage.save_decision_node(node)
            logger.info(f"Stored decision {decision_id} for question: {question[:50]}...")

            # Extract and save participant stances from final round
            stances_saved = 0
            if result.rounds_completed > 0 and result.full_debate:
                # Get final round responses (last N responses where N = number of participants)
                num_participants = len(result.participants)
                final_round_responses = result.full_debate[-num_participants:]

                # Build map of participant -> final response
                final_responses = {}
                for resp in final_round_responses:
                    final_responses[resp.participant] = resp.response

                # Extract votes from voting result if available
                vote_map = {}
                if result.voting_result and result.voting_result.votes_by_round:
                    # Get votes from final round
                    final_round_num = result.rounds_completed
                    for round_vote in result.voting_result.votes_by_round:
                        if round_vote.round == final_round_num:
                            vote_map[round_vote.participant] = round_vote.vote

                # Save stance for each participant
                for participant in result.participants:
                    # Get vote info
                    vote = vote_map.get(participant)

                    # Get final position (truncate to 500 chars)
                    final_position = final_responses.get(participant, "")[:500]

                    # Create and save stance
                    stance = ParticipantStance(
                        decision_id=decision_id,
                        participant=participant,
                        vote_option=vote.option if vote else None,
                        confidence=vote.confidence if vote else None,
                        rationale=vote.rationale if vote else None,
                        final_position=final_position,
                    )
                    self.storage.save_participant_stance(stance)
                    stances_saved += 1

            logger.info(f"Saved {stances_saved} participant stances for decision {decision_id}")

            # Compute similarities to past decisions
            try:
                self._compute_similarities(node)
            except Exception as e:
                # Log but don't fail if similarity computation fails
                logger.error(
                    f"Error computing similarities for decision {decision_id}: {e}",
                    exc_info=True
                )

            return decision_id

        except Exception as e:
            logger.error(
                f"Error storing deliberation in decision graph: {e}",
                exc_info=True
            )
            raise  # Re-raise to let caller handle

    def _compute_similarities(self, new_node: DecisionNode) -> None:
        """Compute similarities between new decision and existing decisions.

        Compares the new decision against all existing decisions in the database
        and stores similarity relationships above a threshold. This enables fast
        retrieval of related past deliberations.

        Args:
            new_node: The newly created DecisionNode

        Note:
            - Limits comparison to 100 most recent decisions to avoid O(n^2) growth
            - Stores similarities >= 0.5 for potential future use
            - Logs errors but does not raise to avoid breaking deliberation flow
        """
        try:
            # Get recent decisions (limit to avoid O(n^2) growth)
            all_decisions = self.storage.get_all_decisions(limit=100)

            if not all_decisions:
                logger.debug("No existing decisions to compare against")
                return

            # Initialize similarity detector
            detector = QuestionSimilarityDetector()

            similarities_stored = 0
            for existing in all_decisions:
                # Skip self-comparison
                if existing.id == new_node.id:
                    continue

                # Compute similarity score
                try:
                    score = detector.compute_similarity(
                        new_node.question,
                        existing.question
                    )

                    # Store similarity if above threshold (0.5 = moderate similarity)
                    if score >= 0.5:
                        similarity = DecisionSimilarity(
                            source_id=new_node.id,
                            target_id=existing.id,
                            similarity_score=score,
                            computed_at=datetime.now()
                        )
                        self.storage.save_similarity(similarity)
                        similarities_stored += 1
                        logger.debug(
                            f"Stored similarity: {new_node.id} -> {existing.id} "
                            f"(score={score:.3f})"
                        )
                except Exception as e:
                    logger.error(
                        f"Error computing similarity with decision {existing.id}: {e}",
                        exc_info=True
                    )
                    continue

            logger.info(
                f"Computed and stored {similarities_stored} similarities "
                f"for decision {new_node.id}"
            )

        except Exception as e:
            logger.error(
                f"Error in similarity computation: {e}",
                exc_info=True
            )
            # Don't raise - this is a non-critical operation

    def get_context_for_deliberation(
        self,
        question: str,
        threshold: float = 0.7,
        max_context_decisions: int = 3,
    ) -> str:
        """Get enriched context for a new deliberation.

        Finds past deliberations that are semantically similar to the new question
        and formats them as markdown context. This context can be prepended to
        deliberation prompts to provide historical perspective.

        Args:
            question: The deliberation question
            threshold: Minimum similarity threshold (0.0-1.0). Defaults to 0.7 (high similarity).
            max_context_decisions: Maximum past decisions to include. Defaults to 3.

        Returns:
            Markdown-formatted context string. Empty string if no similar decisions
            found or if any error occurs (graceful degradation).

        Example:
            >>> integration = DecisionGraphIntegration(storage)
            >>> context = integration.get_context_for_deliberation(
            ...     "Should we adopt TypeScript?",
            ...     threshold=0.75,
            ...     max_context_decisions=2
            ... )
            >>> if context:
            ...     print("Found relevant context:")
            ...     print(context)
            ... else:
            ...     print("No relevant context found")
        """
        try:
            # Validate parameters
            if not question or not question.strip():
                logger.warning("Empty question provided to get_context_for_deliberation")
                return ""

            if not (0.0 <= threshold <= 1.0):
                logger.warning(
                    f"Invalid threshold {threshold}, clamping to [0.0, 1.0]"
                )
                threshold = max(0.0, min(1.0, threshold))

            if max_context_decisions < 1:
                logger.warning(
                    f"Invalid max_context_decisions {max_context_decisions}, using 1"
                )
                max_context_decisions = 1

            # Retrieve enriched context
            context = self.retriever.get_enriched_context(
                question,
                threshold=threshold,
                max_results=max_context_decisions
            )

            if context:
                logger.info(
                    f"Retrieved enriched context for question: {question[:50]}... "
                    f"(threshold={threshold}, max_results={max_context_decisions})"
                )
            else:
                logger.debug(
                    f"No relevant context found for question: {question[:50]}... "
                    f"(threshold={threshold})"
                )

            return context

        except Exception as e:
            # Log error but return empty string for graceful degradation
            logger.error(
                f"Error retrieving context for deliberation: {e}",
                exc_info=True
            )
            return ""  # Never break deliberation due to context retrieval failure
