"""Deliberation engine for orchestrating multi-model discussions."""
from datetime import datetime
from typing import List, Dict
from adapters.base import BaseCLIAdapter
from models.schema import Participant, RoundResponse


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

        Raises:
            RuntimeError: If adapter invocation fails
        """
        responses = []

        # Build context from previous responses
        context = self._build_context(previous_responses) if previous_responses else None

        for participant in participants:
            # Get the appropriate adapter
            adapter = self.adapters[participant.cli]

            # Invoke the adapter
            response_text = await adapter.invoke(
                prompt=prompt,
                model=participant.model,
                context=context
            )

            # Create response object
            response = RoundResponse(
                round=round_num,
                participant=participant.cli,
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
