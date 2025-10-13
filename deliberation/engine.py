"""Deliberation engine for orchestrating multi-model discussions."""
import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING
from pydantic import ValidationError
from adapters.base import BaseCLIAdapter
from models.schema import Participant, RoundResponse, Vote, VotingResult
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

        # Enhance prompt with voting instructions
        enhanced_prompt = self._enhance_prompt_with_voting(prompt)

        # Build context from previous responses
        context = self._build_context(previous_responses) if previous_responses else None

        for participant in participants:
            # Get the appropriate adapter
            adapter = self.adapters[participant.cli]

            # Invoke the adapter with error handling
            try:
                response_text = await adapter.invoke(
                    prompt=enhanced_prompt,
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

    def _parse_vote(self, response_text: str) -> Optional[Vote]:
        """
        Parse vote from response text if present.

        Looks for vote in format: VOTE: {"option": "...", "confidence": 0.0-1.0, "rationale": "..."}

        Args:
            response_text: The response text to parse

        Returns:
            Vote object if valid vote found, None otherwise
        """
        # Look for VOTE: marker followed by JSON
        vote_pattern = r'VOTE:\s*(\{[^}]+\})'
        match = re.search(vote_pattern, response_text)

        if not match:
            return None

        vote_json = match.group(1)

        try:
            vote_data = json.loads(vote_json)
            # Validate using Pydantic model
            vote = Vote(**vote_data)
            return vote
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            logger.debug(f"Failed to parse vote from response: {e}")
            return None

    def _aggregate_votes(self, responses: List[RoundResponse]) -> Optional["VotingResult"]:
        """
        Aggregate votes from all responses into a VotingResult.

        Args:
            responses: List of all RoundResponse objects from deliberation

        Returns:
            VotingResult if any votes found, None otherwise
        """
        from models.schema import RoundVote, VotingResult

        votes_by_round = []
        tally = {}

        for response in responses:
            vote = self._parse_vote(response.response)
            if vote:
                # Create RoundVote
                round_vote = RoundVote(
                    round=response.round,
                    participant=response.participant,
                    vote=vote,
                    timestamp=response.timestamp
                )
                votes_by_round.append(round_vote)

                # Update tally
                tally[vote.option] = tally.get(vote.option, 0) + 1

        # If no votes found, return None
        if not votes_by_round:
            return None

        # Determine consensus and winning option
        if len(tally) == 1:
            # Unanimous vote
            consensus_reached = True
            winning_option = list(tally.keys())[0]
        elif len(tally) > 1:
            # Find option with most votes
            max_votes = max(tally.values())
            winners = [opt for opt, count in tally.items() if count == max_votes]
            if len(winners) == 1:
                # Clear winner
                consensus_reached = True
                winning_option = winners[0]
            else:
                # Tie
                consensus_reached = False
                winning_option = None
        else:
            consensus_reached = False
            winning_option = None

        return VotingResult(
            final_tally=tally,
            votes_by_round=votes_by_round,
            consensus_reached=consensus_reached,
            winning_option=winning_option
        )

    def _build_voting_instructions(self) -> str:
        """
        Build voting instructions for participants.

        Returns:
            Formatted voting instructions string
        """
        return """
## Voting Instructions

After your analysis, please cast your vote using the following format:

VOTE: {"option": "Your choice", "confidence": 0.85, "rationale": "Brief explanation"}

Where:
- option: Your chosen option (e.g., "Option A", "Yes", "Approve")
- confidence: Your confidence level from 0.0 (no confidence) to 1.0 (absolute certainty)
- rationale: Brief explanation for your vote

Example:
VOTE: {"option": "Option A", "confidence": 0.9, "rationale": "Lower risk and better architectural fit"}
""".strip()

    def _enhance_prompt_with_voting(self, prompt: str) -> str:
        """
        Enhance prompt with voting instructions.

        Args:
            prompt: Original question or prompt

        Returns:
            Enhanced prompt with voting instructions
        """
        voting_instructions = self._build_voting_instructions()
        return f"{prompt}\n\n{voting_instructions}"

    def _check_early_stopping(self, round_responses: List[RoundResponse], round_num: int, min_rounds: int) -> bool:
        """
        Check if models want to stop deliberating based on continue_debate votes.

        Args:
            round_responses: Responses from current round
            round_num: Current round number
            min_rounds: Minimum rounds to complete before allowing early stop

        Returns:
            True if deliberation should stop, False otherwise
        """
        # Check if early stopping is enabled
        if not self.config or not hasattr(self.config.deliberation, 'early_stopping'):
            return False

        early_stop_cfg = self.config.deliberation.early_stopping
        if not early_stop_cfg.enabled:
            return False

        # Respect minimum rounds if configured
        if early_stop_cfg.respect_min_rounds and round_num < min_rounds:
            return False

        # Parse votes from responses
        votes = []
        for response in round_responses:
            vote = self._parse_vote(response.response)
            if vote:
                votes.append(vote)

        # If no votes found, can't determine stopping preference
        if not votes:
            return False

        # Count how many models want to stop (continue_debate = False)
        want_to_stop = sum(1 for v in votes if not v.continue_debate)
        total_votes = len(votes)

        # Calculate fraction wanting to stop
        stop_fraction = want_to_stop / total_votes

        # Stop if threshold met (e.g., 66% = 2/3 consensus)
        if stop_fraction >= early_stop_cfg.threshold:
            logger.info(
                f"Early stopping triggered: {want_to_stop}/{total_votes} models "
                f"({stop_fraction:.1%}) want to stop (threshold: {early_stop_cfg.threshold:.1%})"
            )
            return True

        return False

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
        model_controlled_stop = False

        for round_num in range(1, rounds_to_execute + 1):
            round_responses = await self.execute_round(
                round_num=round_num,
                prompt=request.question,
                participants=request.participants,
                previous_responses=all_responses
            )
            all_responses.extend(round_responses)

            # Check for model-controlled early stopping
            if self._check_early_stopping(round_responses, round_num, request.rounds):
                logger.info(f"Models want to stop deliberating at round {round_num}")
                model_controlled_stop = True
                break

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
                         model_controlled_stop or
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

        # Aggregate voting results if any votes were cast
        voting_result = self._aggregate_votes(all_responses)
        if voting_result:
            logger.info(
                f"Voting results: {voting_result.final_tally} "
                f"(consensus: {voting_result.consensus_reached}, "
                f"winner: {voting_result.winning_option})"
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
            convergence_info=None,  # Will populate below if available
            voting_result=voting_result  # Add voting results
        )

        # Add convergence info if available
        if final_convergence_info or voting_result:
            from models.schema import ConvergenceInfo

            # Override convergence status based on voting outcome if available
            if voting_result:
                if voting_result.consensus_reached and len(voting_result.final_tally) == 1:
                    # Unanimous vote
                    convergence_status = "unanimous_consensus"
                    convergence_detected = True
                elif voting_result.consensus_reached and voting_result.winning_option:
                    # Majority vote (e.g., 2-1)
                    convergence_status = "majority_decision"
                    convergence_detected = True
                elif not voting_result.winning_option:
                    # Tie vote
                    convergence_status = "tie"
                    convergence_detected = False
                else:
                    # Fallback to semantic similarity status
                    convergence_status = final_convergence_info.status if final_convergence_info else "unknown"
                    convergence_detected = final_convergence_info.converged if final_convergence_info else False
            elif final_convergence_info:
                # No voting, use semantic similarity status
                convergence_status = final_convergence_info.status
                convergence_detected = final_convergence_info.converged
            else:
                convergence_status = "unknown"
                convergence_detected = False

            result.convergence_info = ConvergenceInfo(
                detected=convergence_detected,
                detection_round=actual_rounds_completed if convergence_detected else None,
                final_similarity=final_convergence_info.min_similarity if final_convergence_info else 0.0,
                status=convergence_status,
                scores_by_round=[],  # Could track all rounds if needed
                per_participant_similarity=final_convergence_info.per_participant_similarity if final_convergence_info else {}
            )

        # Save transcript
        transcript_path = self.transcript_manager.save(result, request.question)
        result.transcript_path = transcript_path

        return result
