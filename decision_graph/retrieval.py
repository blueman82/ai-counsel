"""Context retrieval for deliberations using Decision Graph Memory.

This module provides the DecisionRetriever class, which finds relevant past
deliberations and formats them as enriched context for new deliberations.
"""

import logging
from typing import List, Optional

from decision_graph.cache import SimilarityCache
from decision_graph.schema import DecisionNode
from decision_graph.similarity import QuestionSimilarityDetector
from decision_graph.storage import DecisionGraphStorage

logger = logging.getLogger(__name__)


class DecisionRetriever:
    """Retrieves relevant past decisions and formats them as deliberation context.

    DecisionRetriever combines similarity detection with storage retrieval to find
    past deliberations that are semantically related to a new question, then formats
    them as markdown context that can be prepended to deliberation prompts.

    Example:
        >>> storage = DecisionGraphStorage(":memory:")
        >>> retriever = DecisionRetriever(storage)
        >>> context = retriever.get_enriched_context(
        ...     "Should we adopt TypeScript?",
        ...     threshold=0.7,
        ...     max_results=3
        ... )
        >>> print(context)  # Markdown-formatted past decisions
    """

    def __init__(
        self,
        storage: DecisionGraphStorage,
        cache: Optional[SimilarityCache] = None,
        enable_cache: bool = True,
    ):
        """Initialize with storage backend and optional caching.

        Args:
            storage: DecisionGraphStorage instance for database access
            cache: Optional SimilarityCache instance. If None and enable_cache=True,
                   creates a default cache.
            enable_cache: Whether to enable caching (default: True)
        """
        self.storage = storage
        self.similarity_detector = QuestionSimilarityDetector()

        # Initialize cache
        if enable_cache:
            self.cache = cache or SimilarityCache(
                query_cache_size=200,
                embedding_cache_size=500,
                query_ttl=300,  # 5 minutes
            )
            logger.info(
                f"Initialized DecisionRetriever with caching enabled "
                f"(L1: {self.cache.query_cache.maxsize}, L2: {self.cache.embedding_cache.maxsize})"
            )
        else:
            self.cache = None
            logger.info("Initialized DecisionRetriever with caching disabled")

        logger.info(
            f"Using similarity backend: {self.similarity_detector.backend.__class__.__name__}"
        )

    def find_relevant_decisions(
        self,
        query_question: str,
        threshold: float = 0.7,
        max_results: int = 3,
    ) -> List[DecisionNode]:
        """Find relevant past decisions for a new question.

        Uses semantic similarity to compare the query question against all past
        deliberations in the database. Returns the most similar decisions above
        the threshold.

        Args:
            query_question: The new deliberation question
            threshold: Minimum similarity score (0.0-1.0). Defaults to 0.7.
            max_results: Maximum number of results to return. Defaults to 3.

        Returns:
            List of DecisionNode objects, sorted by similarity descending

        Raises:
            ValueError: If threshold is not in range [0.0, 1.0] or max_results < 1

        Example:
            >>> retriever = DecisionRetriever(storage)
            >>> decisions = retriever.find_relevant_decisions(
            ...     "Should we use React or Vue?",
            ...     threshold=0.7,
            ...     max_results=5
            ... )
            >>> for decision in decisions:
            ...     print(f"{decision.question}: {decision.consensus}")
        """
        # Validate parameters
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(
                f"threshold must be between 0.0 and 1.0, got {threshold}"
            )
        if max_results < 1:
            raise ValueError(f"max_results must be >= 1, got {max_results}")

        if not query_question or not query_question.strip():
            logger.warning("Empty query_question provided to find_relevant_decisions")
            return []

        # 1. Try L1 cache hit (query results)
        if self.cache:
            cached_similar = self.cache.get_cached_result(
                query_question, threshold, max_results
            )
            if cached_similar is not None:
                logger.info(
                    f"L1 cache hit for query: {query_question[:50]}... "
                    f"(threshold={threshold}, max={max_results})"
                )
                # Reconstruct DecisionNode objects from cached results
                results = []
                for match in cached_similar:
                    decision = self.storage.get_decision_node(match["id"])
                    if decision:
                        results.append(decision)
                    else:
                        logger.warning(
                            f"Cached decision {match['id']} not found in storage "
                            "(may have been deleted)"
                        )
                return results

        # 2. Cache miss - proceed with similarity computation
        logger.debug("L1 cache miss - computing similarities")

        # 3. Get all past decisions
        logger.debug("Retrieving all past decisions for similarity comparison")
        all_decisions = self.storage.get_all_decisions(limit=1000)

        if not all_decisions:
            logger.info("No past decisions found in database")
            return []

        # 4. Extract candidates as (id, question) tuples
        candidates = [(d.id, d.question) for d in all_decisions]
        logger.debug(
            f"Comparing query against {len(candidates)} candidate decisions"
        )

        # 5. Find similar questions
        similar = self.similarity_detector.find_similar(
            query_question, candidates, threshold=threshold
        )

        if not similar:
            logger.info(
                f"No similar decisions found above threshold {threshold}"
            )
            # Cache empty result to avoid recomputation
            if self.cache:
                self.cache.cache_result(query_question, threshold, max_results, [])
            return []

        # 6. Cache the similarity results (L1)
        if self.cache:
            self.cache.cache_result(
                query_question, threshold, max_results, similar[:max_results]
            )
            logger.debug(
                f"Cached L1 result for query: {query_question[:50]}... "
                f"({len(similar[:max_results])} results)"
            )

        # 7. Fetch full DecisionNode objects for similar questions
        results = []
        for match in similar[:max_results]:
            decision = self.storage.get_decision_node(match["id"])
            if decision:
                results.append(decision)
                logger.debug(
                    f"Found relevant decision: {decision.id} "
                    f"(similarity: {match['score']:.2f})"
                )
            else:
                logger.warning(
                    f"Decision {match['id']} not found during retrieval "
                    "(possible race condition)"
                )

        logger.info(
            f"Found {len(results)} relevant decisions for query "
            f"(threshold={threshold}, max_results={max_results})"
        )
        return results

    def format_context(
        self, decisions: List[DecisionNode], query: str
    ) -> str:
        """Format relevant decisions as context string for deliberation.

        Generates a markdown-formatted context string that includes:
        - Section header explaining context source
        - For each decision: question, date, status, consensus, winning option,
          participants, and their individual stances

        Args:
            decisions: List of relevant DecisionNode objects
            query: The current deliberation question (for context)

        Returns:
            Markdown-formatted context string (empty if no decisions provided)

        Example:
            >>> decisions = [decision1, decision2]
            >>> context = retriever.format_context(decisions, "Should we use React?")
            >>> print(context)
            ## Similar Past Deliberations (Decision Graph Memory)
            ...
        """
        if not decisions:
            logger.debug("No decisions to format")
            return ""

        lines = []
        lines.append("## Similar Past Deliberations (Decision Graph Memory)\n")
        lines.append(
            f'*The following similar deliberations may provide useful context for: "{query}"*\n'
        )

        for i, decision in enumerate(decisions, 1):
            logger.debug(f"Formatting decision {i}/{len(decisions)}: {decision.id}")

            # Basic decision metadata
            lines.append(f"### Past Deliberation {i}: {decision.question}")
            lines.append(f"**Date**: {decision.timestamp.isoformat()}")
            lines.append(
                f"**Convergence Status**: {decision.convergence_status}"
            )
            lines.append(f"**Consensus**: {decision.consensus}")

            # Winning option (optional)
            if decision.winning_option:
                lines.append(f"**Winning Option**: {decision.winning_option}")

            # Participants
            participants_str = ", ".join(decision.participants)
            lines.append(f"**Participants**: {participants_str}")

            # Get stances for this decision
            try:
                stances = self.storage.get_participant_stances(decision.id)
                if stances:
                    lines.append("\n**Participant Positions**:")
                    for stance in stances:
                        stance_line = f"- **{stance.participant}**: "

                        # Vote information (if available)
                        if stance.vote_option:
                            stance_line += f"Voted for '{stance.vote_option}'"
                            if stance.confidence is not None:
                                confidence_pct = stance.confidence * 100
                                stance_line += (
                                    f" (confidence: {confidence_pct:.0f}%)"
                                )

                        # Rationale (if available)
                        if stance.rationale:
                            stance_line += f" - {stance.rationale}"

                        lines.append(stance_line)
                else:
                    logger.debug(
                        f"No participant stances found for decision {decision.id}"
                    )
            except Exception as e:
                logger.error(
                    f"Error retrieving stances for decision {decision.id}: {e}",
                    exc_info=True,
                )
                lines.append(
                    "\n*[Error retrieving participant positions]*"
                )

            lines.append("")  # Blank line between decisions

        formatted = "\n".join(lines)
        logger.debug(
            f"Formatted {len(decisions)} decisions into {len(formatted)} char context"
        )
        return formatted

    def get_enriched_context(
        self,
        query_question: str,
        threshold: float = 0.7,
        max_results: int = 3,
    ) -> str:
        """One-stop method: find relevant decisions and format as context.

        Convenience method that combines find_relevant_decisions() and
        format_context() into a single call. Use this when you want to
        retrieve and format context in one step.

        Args:
            query_question: The new deliberation question
            threshold: Minimum similarity score (0.0-1.0). Defaults to 0.7.
            max_results: Maximum past decisions to include. Defaults to 3.

        Returns:
            Markdown-formatted context string (empty if no similar decisions found)

        Raises:
            ValueError: If threshold or max_results are invalid

        Example:
            >>> retriever = DecisionRetriever(storage)
            >>> context = retriever.get_enriched_context(
            ...     "Should we adopt GraphQL?",
            ...     threshold=0.75,
            ...     max_results=2
            ... )
            >>> if context:
            ...     print("Found relevant past decisions:")
            ...     print(context)
            ... else:
            ...     print("No relevant past decisions found")
        """
        logger.info(
            f"Retrieving enriched context for query: '{query_question[:50]}...'"
        )

        try:
            # Find relevant decisions
            decisions = self.find_relevant_decisions(
                query_question, threshold=threshold, max_results=max_results
            )

            # Format as context
            context = self.format_context(decisions, query_question)

            if context:
                logger.info(
                    f"Generated enriched context with {len(decisions)} decisions"
                )
            else:
                logger.info("No relevant context found for query")

            return context

        except Exception as e:
            logger.error(
                f"Error generating enriched context: {e}", exc_info=True
            )
            # Return empty context on error (fail gracefully)
            return ""

    def invalidate_cache(self) -> None:
        """Invalidate L1 query cache when new decisions are added.

        Call this method after adding new decisions to the graph to ensure
        subsequent queries reflect the updated decision set.

        Note: Does not invalidate L2 embedding cache (embeddings are immutable).
        """
        if self.cache:
            self.cache.invalidate_all_queries()
            logger.info("Invalidated L1 query cache (new decision added)")
        else:
            logger.debug("Cache invalidation called but caching is disabled")

    def get_cache_stats(self):
        """Get cache statistics.

        Returns:
            Dict with cache statistics if caching enabled, None otherwise
        """
        if self.cache:
            return self.cache.get_stats()
        return None
