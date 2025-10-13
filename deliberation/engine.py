"""Deliberation engine for orchestrating multi-model discussions."""
import logging
from datetime import datetime
from typing import List, Dict, TYPE_CHECKING
from adapters.base import BaseCLIAdapter
from models.schema import Participant, RoundResponse

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from models.schema import DeliberateRequest, DeliberationResult


class DeliberationEngine:
    """
    Engine for orchestrating deliberative discussions between AI models.

    Manages round execution, context building, and response collection.
    """

    def __init__(self, adapters: Dict[str, BaseCLIAdapter]):
        """
        Initialize deliberation engine.

        Args:
            adapters: Dictionary mapping CLI names to adapter instances
        """
        self.adapters = adapters

    async def execute_round(
        self,
        round_num: int,
        prompt: str,
        participants: List[Participant],
        previous_responses: List[RoundResponse]
    ) -> List[RoundResponse]:
        """
        Execute a single deliberation round.

        Args:
            round_num: Current round number (1-indexed)
            prompt: The question or topic for deliberation
            participants: List of participants for this round
            previous_responses: Responses from previous rounds for context

        Returns:
            List of RoundResponse objects from this round

        Note:
            If an adapter fails, an error message is logged and included
            in the response, allowing other participants to continue.
        """
        responses = []

        # Build context from previous responses
        context = self._build_context(previous_responses) if previous_responses else None

        for participant in participants:
            # Get the appropriate adapter
            adapter = self.adapters[participant.cli]

            # Invoke the adapter with error handling
            try:
                response_text = await adapter.invoke(
                    prompt=prompt,
                    model=participant.model,
                    context=context
                )
            except Exception as e:
                # Log error but continue with other participants
                logger.error(
                    f"Adapter {participant.cli} failed for model {participant.model}: {e}",
                    exc_info=True
                )
                response_text = f"[ERROR: {type(e).__name__}: {str(e)}]"

            # Create response object
            response = RoundResponse(
                round=round_num,
                participant=f"{participant.model}@{participant.cli}",
                stance=participant.stance,
                response=response_text,
                timestamp=datetime.now().isoformat()
            )

            responses.append(response)

        return responses

    def _build_context(self, previous_responses: List[RoundResponse]) -> str:
        """
        Build context string from previous responses.

        Args:
            previous_responses: List of responses from previous rounds

        Returns:
            Formatted context string
        """
        context_parts = ["Previous discussion:\n"]

        for resp in previous_responses:
            context_parts.append(
                f"Round {resp.round} - {resp.participant} ({resp.stance}): "
                f"{resp.response}\n"
            )

        return "\n".join(context_parts)

    async def execute(self, request: "DeliberateRequest") -> "DeliberationResult":
        """
        Execute full deliberation with multiple rounds.

        Args:
            request: Deliberation request

        Returns:
            Complete deliberation result

        Note:
            Quick mode forces single round regardless of request.rounds value.
            Conference mode respects the requested number of rounds.
        """
        from models.schema import DeliberationResult, Summary

        # Determine actual rounds to execute
        # Quick mode forces single round for fast deliberation
        if request.mode == "quick":
            rounds_to_execute = 1
        else:
            rounds_to_execute = request.rounds

        # Execute rounds sequentially
        all_responses = []
        for round_num in range(1, rounds_to_execute + 1):
            round_responses = await self.execute_round(
                round_num=round_num,
                prompt=request.question,
                participants=request.participants,
                previous_responses=all_responses
            )
            all_responses.extend(round_responses)

        # Generate summary (placeholder for now)
        summary = Summary(
            consensus="Generated summary placeholder",
            key_agreements=["Agreement 1", "Agreement 2"],
            key_disagreements=["Disagreement 1"],
            final_recommendation="Recommendation placeholder"
        )

        # Build participant list
        participant_ids = [
            f"{p.model}@{p.cli}"
            for p in request.participants
        ]

        return DeliberationResult(
            status="complete",
            mode=request.mode,
            rounds_completed=rounds_to_execute,
            participants=participant_ids,
            summary=summary,
            transcript_path="",  # Will be set by transcript manager
            full_debate=all_responses
        )
