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
            raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}")
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
        logger.debug(f"Comparing query against {len(candidates)} candidate decisions")

        # 5. Find similar questions
        similar = self.similarity_detector.find_similar(
            query_question, candidates, threshold=threshold
        )

        if not similar:
            logger.info(f"No similar decisions found above threshold {threshold}")
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

    def format_context(self, decisions: List[DecisionNode], query: str) -> str:
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
            lines.append(f"**Convergence Status**: {decision.convergence_status}")
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
                                stance_line += f" (confidence: {confidence_pct:.0f}%)"

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
                lines.append("\n*[Error retrieving participant positions]*")

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
            logger.error(f"Error generating enriched context: {e}", exc_info=True)
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

    def _estimate_tokens(self, formatted_str: str) -> int:
        """Estimate token count for a formatted string.

        Uses rough heuristic: 1 token ≈ 4 characters (conservative estimate).

        Args:
            formatted_str: The formatted string to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(formatted_str) // 4

    def _format_strong_tier(self, decision: DecisionNode, score: float) -> str:
        """Format a strong similarity match with full details.

        Strong tier (≥0.75 similarity) gets comprehensive formatting:
        - Question, timestamp, convergence status, consensus
        - Winning option
        - Participants with detailed stances (votes, confidence, rationale)

        Args:
            decision: DecisionNode to format
            score: Similarity score (for display)

        Returns:
            Formatted markdown string with full details (~400-600 tokens)
        """
        lines = []

        # Header with score
        lines.append(f"### Strong Match (similarity: {score:.2f}): {decision.question}")
        lines.append(f"**Date**: {decision.timestamp.isoformat()}")
        lines.append(f"**Convergence Status**: {decision.convergence_status}")
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
                            stance_line += f" (confidence: {confidence_pct:.0f}%)"

                    # Rationale (if available)
                    if stance.rationale:
                        stance_line += f" - {stance.rationale}"

                    lines.append(stance_line)
        except Exception as e:
            logger.error(
                f"Error retrieving stances for decision {decision.id}: {e}",
                exc_info=True,
            )
            lines.append("\n*[Error retrieving participant positions]*")

        lines.append("")  # Blank line
        return "\n".join(lines)

    def _format_moderate_tier(self, decision: DecisionNode, score: float) -> str:
        """Format a moderate similarity match with summary details.

        Moderate tier (0.60-0.74 similarity) gets summary formatting:
        - Question, consensus, winning option
        - No detailed participant stances

        Args:
            decision: DecisionNode to format
            score: Similarity score (for display)

        Returns:
            Formatted markdown string with summary (~150-250 tokens)
        """
        lines = []

        # Header with score
        lines.append(f"### Moderate Match (similarity: {score:.2f}): {decision.question}")
        lines.append(f"**Consensus**: {decision.consensus}")

        # Winning option (optional)
        if decision.winning_option:
            lines.append(f"**Result**: {decision.winning_option}")

        lines.append("")  # Blank line
        return "\n".join(lines)

    def _format_brief_tier(self, decision: DecisionNode, score: float) -> str:
        """Format a brief similarity match with minimal details.

        Brief tier (<0.60 similarity, ≥0.40 noise floor) gets one-liner:
        - Question and winning option only

        Args:
            decision: DecisionNode to format
            score: Similarity score (for display)

        Returns:
            Formatted markdown string with minimal info (~30-70 tokens)
        """
        # One-liner format
        result = decision.winning_option or decision.consensus[:50]
        return f"- **Brief Match** ({score:.2f}): {decision.question} → {result}\n"

    def format_context_tiered(
        self,
        scored_decisions: List[tuple[DecisionNode, float]],
        tier_boundaries: dict[str, float],
        token_budget: int,
    ) -> dict:
        """Format decisions using tiered approach with token budget tracking.

        This method implements budget-aware context injection by formatting decisions
        based on their similarity scores (strong/moderate/brief tiers) and stopping
        when the token budget is exceeded.

        Tiers:
        - Strong (≥strong_threshold): Full formatting with stances (~500 tokens)
        - Moderate (≥moderate_threshold, <strong): Summary format (~200 tokens)
        - Brief (≥0.40, <moderate): One-liner format (~50 tokens)
        - Noise floor (<0.40): Filtered out entirely

        Args:
            scored_decisions: List of (DecisionNode, score) tuples sorted by score descending
            tier_boundaries: Dict with 'strong' and 'moderate' thresholds
            token_budget: Maximum tokens allowed for context injection

        Returns:
            Dict with:
            - formatted (str): Markdown-formatted context string
            - tokens_used (int): Total tokens used
            - tier_distribution (dict): Count of decisions in each tier
                {"strong": int, "moderate": int, "brief": int}

        Example:
            >>> scored = [(decision1, 0.85), (decision2, 0.65), (decision3, 0.45)]
            >>> result = retriever.format_context_tiered(
            ...     scored, {"strong": 0.75, "moderate": 0.60}, 1500
            ... )
            >>> print(result["formatted"])
            >>> print(f"Tokens used: {result['tokens_used']}/{1500}")
        """
        NOISE_FLOOR = 0.40

        # Initialize metrics
        tier_distribution = {"strong": 0, "moderate": 0, "brief": 0}
        tokens_used = 0
        formatted_parts = []

        # Early return for empty input
        if not scored_decisions:
            return {
                "formatted": "",
                "tokens_used": 0,
                "tier_distribution": tier_distribution,
            }

        # Add header
        header = "## Similar Past Deliberations (Tiered by Relevance)\n\n"
        formatted_parts.append(header)
        tokens_used += self._estimate_tokens(header)

        # Extract thresholds
        strong_threshold = tier_boundaries["strong"]
        moderate_threshold = tier_boundaries["moderate"]

        # Process decisions in order of similarity
        for decision, score in scored_decisions:
            # Apply noise floor filter
            if score < NOISE_FLOOR:
                logger.debug(
                    f"Skipping decision {decision.id} (score {score:.2f} below noise floor {NOISE_FLOOR})"
                )
                continue

            # Determine tier and format accordingly
            if score >= strong_threshold:
                formatted = self._format_strong_tier(decision, score)
                tier = "strong"
            elif score >= moderate_threshold:
                formatted = self._format_moderate_tier(decision, score)
                tier = "moderate"
            else:
                formatted = self._format_brief_tier(decision, score)
                tier = "brief"

            # Estimate tokens for this decision
            decision_tokens = self._estimate_tokens(formatted)

            # Check if adding this decision would exceed budget
            if tokens_used + decision_tokens > token_budget:
                logger.info(
                    f"Token budget reached: {tokens_used} + {decision_tokens} > {token_budget}. "
                    f"Stopping context injection (processed {sum(tier_distribution.values())} decisions)"
                )
                break

            # Add to context
            formatted_parts.append(formatted)
            tokens_used += decision_tokens
            tier_distribution[tier] += 1

            logger.debug(
                f"Added {tier} tier decision {decision.id} "
                f"(score: {score:.2f}, tokens: {decision_tokens}, total: {tokens_used}/{token_budget})"
            )

        # Combine all parts
        final_formatted = "\n".join(formatted_parts)

        # If all decisions were filtered by noise floor, return empty
        if sum(tier_distribution.values()) == 0:
            return {
                "formatted": "",
                "tokens_used": 0,
                "tier_distribution": tier_distribution,
            }

        logger.info(
            f"Formatted {sum(tier_distribution.values())} decisions "
            f"(strong: {tier_distribution['strong']}, moderate: {tier_distribution['moderate']}, "
            f"brief: {tier_distribution['brief']}) using {tokens_used} tokens"
        )

        return {
            "formatted": final_formatted,
            "tokens_used": tokens_used,
            "tier_distribution": tier_distribution,
        }
