"""Deliberation engine for orchestrating multi-model discussions."""
import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING
from pydantic import ValidationError
from adapters.base import BaseCLIAdapter
from models.schema import Participant, RoundResponse, Vote
from deliberation.convergence import ConvergenceDetector

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from models.schema import DeliberateRequest, DeliberationResult
    from deliberation.transcript import TranscriptManager


class DeliberationEngine:
    """
    Engine for orchestrating deliberative discussions between AI models.

    Manages round execution, context building, and response collection.
    """

    def __init__(
        self,
        adapters: Dict[str, BaseCLIAdapter],
        transcript_manager: Optional["TranscriptManager"] = None,
        config=None
    ):
        """
        Initialize deliberation engine.

        Args:
            adapters: Dictionary mapping CLI names to adapter instances
            transcript_manager: Optional transcript manager (creates default if None)
            config: Optional configuration object for convergence detection
        """
        self.adapters = adapters
        self.transcript_manager = transcript_manager
        self.config = config

        # Import here to avoid circular dependency
        if transcript_manager is None:
            from deliberation.transcript import TranscriptManager
            self.transcript_manager = TranscriptManager()

        # Initialize convergence detector if enabled
        self.convergence_detector = None
        if config and hasattr(config, 'deliberation'):
            convergence_cfg = config.deliberation.convergence_detection
            if hasattr(config.deliberation, 'convergence_detection') and convergence_cfg.enabled:
                self.convergence_detector = ConvergenceDetector(config)
                logger.info("Convergence detection enabled")
            else:
                logger.info("Convergence detection disabled")
        else:
            logger.debug("No config provided, convergence detection disabled")

        # Initialize summarizer with fallback chain
        # Try adapters in order of quality for summarization
        self.summarizer = None
        self.summarizer_info = None

        summarizer_preferences = [
            ('claude', 'sonnet', 'Claude Sonnet'),
            ('codex', 'gpt-5-codex', 'GPT-5 Codex'),
            ('droid', 'claude-sonnet-4-5-20250929', 'Droid with Claude Sonnet'),
            ('gemini', 'gemini-2.5-pro', 'Gemini 2.5 Pro')
        ]

        for cli_name, model_name, display_name in summarizer_preferences:
            if cli_name in adapters:
                from deliberation.summarizer import DeliberationSummarizer
                self.summarizer = DeliberationSummarizer(adapters[cli_name], model_name)
                self.summarizer_info = {'cli': cli_name, 'model': model_name, 'name': display_name}
                logger.info(f"AI-powered summary generation enabled (using {display_name})")
                break

        if not self.summarizer:
            logger.warning(
                "No suitable adapter available for summary generation. "
                "Install at least one CLI (claude, codex, droid, or gemini) for AI-powered summaries."
            )

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
        Execute full deliberation with multiple rounds and optional convergence detection.

        Args:
            request: Deliberation request containing question, participants, rounds, and mode

        Returns:
            Complete deliberation result with optional convergence_info

        Note:
            Quick mode forces single round regardless of request.rounds value.
            Conference mode respects the requested number of rounds but may stop early
            if convergence is detected.

        Convergence Behavior:
            - Checks convergence starting from round 2 (need previous round for comparison)
            - Stops early if models reach consensus (converged status)
            - Stops early if models reach stable disagreement (impasse status)
            - Continues for diverging/refining statuses until max rounds
            - All convergence data is included in result.convergence_info
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
        final_convergence_info = None
        converged = False

        for round_num in range(1, rounds_to_execute + 1):
            round_responses = await self.execute_round(
                round_num=round_num,
                prompt=request.question,
                participants=request.participants,
                previous_responses=all_responses
            )
            all_responses.extend(round_responses)

            # Check convergence after round 2+
            if self.convergence_detector and round_num >= 2:
                prev_round = [r for r in all_responses if r.round == round_num - 1]
                curr_round = round_responses

                convergence_result = self.convergence_detector.check_convergence(
                    current_round=curr_round,
                    previous_round=prev_round,
                    round_number=round_num
                )

                if convergence_result:
                    logger.info(
                        f"Round {round_num}: {convergence_result.status} "
                        f"(min_sim={convergence_result.min_similarity:.2f}, "
                        f"avg_sim={convergence_result.avg_similarity:.2f})"
                    )

                    # Store convergence info for result
                    final_convergence_info = convergence_result

                    # Stop if converged or impasse
                    if convergence_result.converged:
                        logger.info(f"✓ Convergence detected at round {round_num}, stopping early")
                        converged = True
                        break
                    elif convergence_result.status == "impasse":
                        logger.info(f"✗ Impasse detected at round {round_num}, stopping")
                        break

        # Determine actual rounds completed
        is_early_stop = (converged or
                         (final_convergence_info and final_convergence_info.status == "impasse"))
        actual_rounds_completed = round_num if is_early_stop else rounds_to_execute

        # Generate AI-powered summary
        if self.summarizer:
            try:
                logger.info("Generating AI-powered summary of deliberation...")
                summary = await self.summarizer.generate_summary(
                    question=request.question,
                    responses=all_responses
                )
                logger.info("Summary generation completed successfully")
            except Exception as e:
                logger.error(f"Summary generation failed: {e}", exc_info=True)
                # Fallback to placeholder on error
                summary = Summary(
                    consensus="[Summary generation failed]",
                    key_agreements=["Error occurred during summary generation"],
                    key_disagreements=[],
                    final_recommendation="Please review the full debate below."
                )
        else:
            # No summarizer available, use placeholder
            summary = Summary(
                consensus="[Summary generation not available - Claude adapter required]",
                key_agreements=["No summary available"],
                key_disagreements=[],
                final_recommendation="Please review the full debate below."
            )

        # Build participant list
        participant_ids = [
            f"{p.model}@{p.cli}"
            for p in request.participants
        ]

        # Create result
        result = DeliberationResult(
            status="complete",
            mode=request.mode,
            rounds_completed=actual_rounds_completed,
            participants=participant_ids,
            summary=summary,
            transcript_path="",  # Will be set below
            full_debate=all_responses,
            convergence_info=None  # Will populate below if available
        )

        # Add convergence info if available
        if final_convergence_info:
            from models.schema import ConvergenceInfo

            result.convergence_info = ConvergenceInfo(
                detected=final_convergence_info.converged,
                detection_round=actual_rounds_completed if final_convergence_info.converged else None,
                final_similarity=final_convergence_info.min_similarity,
                status=final_convergence_info.status,
                scores_by_round=[],  # Could track all rounds if needed
                per_participant_similarity=final_convergence_info.per_participant_similarity
            )

        # Save transcript
        transcript_path = self.transcript_manager.save(result, request.question)
        result.transcript_path = transcript_path

        return result
