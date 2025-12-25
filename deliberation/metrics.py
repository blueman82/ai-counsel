"""Response quality metrics tracking for deliberation."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Metrics for a single model's performance in deliberations."""

    model_id: str  # e.g., "anthropic/claude-sonnet-4@openrouter"

    # Vote tracking
    total_responses: int = 0
    successful_votes: int = 0
    failed_votes: int = 0
    abstain_votes: int = 0

    # Response quality
    total_response_length: int = 0
    truncated_responses: int = 0

    # Timing
    total_response_time_ms: float = 0.0

    @property
    def vote_success_rate(self) -> float:
        """Calculate vote success rate as a percentage."""
        if self.total_responses == 0:
            return 0.0
        return (self.successful_votes / self.total_responses) * 100

    @property
    def avg_response_length(self) -> float:
        """Calculate average response length in characters."""
        if self.total_responses == 0:
            return 0.0
        return self.total_response_length / self.total_responses

    @property
    def truncation_rate(self) -> float:
        """Calculate truncation rate as a percentage."""
        if self.total_responses == 0:
            return 0.0
        return (self.truncated_responses / self.total_responses) * 100

    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds."""
        if self.total_responses == 0:
            return 0.0
        return self.total_response_time_ms / self.total_responses

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "total_responses": self.total_responses,
            "successful_votes": self.successful_votes,
            "failed_votes": self.failed_votes,
            "abstain_votes": self.abstain_votes,
            "vote_success_rate": round(self.vote_success_rate, 1),
            "avg_response_length": round(self.avg_response_length, 0),
            "truncated_responses": self.truncated_responses,
            "truncation_rate": round(self.truncation_rate, 1),
            "avg_response_time_ms": round(self.avg_response_time_ms, 0),
        }


@dataclass
class ResponseQualityTracker:
    """
    Tracks response quality metrics across all models in deliberations.

    This tracker accumulates statistics about:
    - Vote success rate per model
    - Average response length
    - Truncation frequency
    - Response timing

    Metrics are stored in memory and can be exported for analysis.
    """

    # Per-model metrics
    model_metrics: Dict[str, ModelMetrics] = field(default_factory=dict)

    # Session-level tracking
    session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    total_deliberations: int = 0

    def get_or_create_model(self, model_id: str) -> ModelMetrics:
        """Get existing model metrics or create new entry."""
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = ModelMetrics(model_id=model_id)
        return self.model_metrics[model_id]

    def record_response(
        self,
        model_id: str,
        response_length: int,
        vote_success: bool,
        is_abstain: bool = False,
        was_truncated: bool = False,
        response_time_ms: float = 0.0,
    ) -> None:
        """
        Record metrics for a single model response.

        Args:
            model_id: Model identifier (e.g., "anthropic/claude-sonnet-4@openrouter")
            response_length: Length of response in characters
            vote_success: Whether a valid vote was extracted
            is_abstain: Whether this was marked as an abstain vote
            was_truncated: Whether the response was truncated (finish_reason=length)
            response_time_ms: Response time in milliseconds
        """
        metrics = self.get_or_create_model(model_id)

        metrics.total_responses += 1
        metrics.total_response_length += response_length
        metrics.total_response_time_ms += response_time_ms

        if vote_success:
            metrics.successful_votes += 1
        elif is_abstain:
            metrics.abstain_votes += 1
        else:
            metrics.failed_votes += 1

        if was_truncated:
            metrics.truncated_responses += 1

        logger.debug(
            f"Recorded metrics for {model_id}: "
            f"vote={'success' if vote_success else ('abstain' if is_abstain else 'failed')}, "
            f"length={response_length}, truncated={was_truncated}"
        )

    def get_summary(self) -> Dict:
        """
        Get summary of all model metrics.

        Returns:
            Dictionary with per-model metrics and aggregate statistics
        """
        if not self.model_metrics:
            return {
                "session_start": self.session_start,
                "total_deliberations": self.total_deliberations,
                "models": {},
                "aggregate": {
                    "total_responses": 0,
                    "overall_vote_success_rate": 0.0,
                    "overall_truncation_rate": 0.0,
                },
            }

        # Aggregate statistics
        total_responses = sum(m.total_responses for m in self.model_metrics.values())
        total_successful = sum(m.successful_votes for m in self.model_metrics.values())
        total_truncated = sum(
            m.truncated_responses for m in self.model_metrics.values()
        )

        overall_vote_rate = (
            (total_successful / total_responses * 100) if total_responses > 0 else 0.0
        )
        overall_truncation_rate = (
            (total_truncated / total_responses * 100) if total_responses > 0 else 0.0
        )

        return {
            "session_start": self.session_start,
            "total_deliberations": self.total_deliberations,
            "models": {
                model_id: metrics.to_dict()
                for model_id, metrics in self.model_metrics.items()
            },
            "aggregate": {
                "total_responses": total_responses,
                "overall_vote_success_rate": round(overall_vote_rate, 1),
                "overall_truncation_rate": round(overall_truncation_rate, 1),
            },
        }

    def get_problem_models(self, min_responses: int = 3) -> List[Dict]:
        """
        Identify models with quality issues.

        Args:
            min_responses: Minimum responses required to be included

        Returns:
            List of models with issues (low vote rate or high truncation)
        """
        problems = []

        for model_id, metrics in self.model_metrics.items():
            if metrics.total_responses < min_responses:
                continue

            issues = []

            # Low vote success rate (<50%)
            if metrics.vote_success_rate < 50:
                issues.append(f"low vote rate ({metrics.vote_success_rate:.0f}%)")

            # High truncation rate (>10%)
            if metrics.truncation_rate > 10:
                issues.append(f"high truncation ({metrics.truncation_rate:.0f}%)")

            # Short responses (avg < 500 chars)
            if metrics.avg_response_length < 500:
                issues.append(
                    f"short responses ({metrics.avg_response_length:.0f} chars avg)"
                )

            if issues:
                problems.append(
                    {
                        "model_id": model_id,
                        "issues": issues,
                        "metrics": metrics.to_dict(),
                    }
                )

        return problems

    def reset(self) -> None:
        """Reset all metrics (e.g., for new session)."""
        self.model_metrics.clear()
        self.session_start = datetime.now().isoformat()
        self.total_deliberations = 0
        logger.info("Response quality metrics reset")


# Global tracker instance for use across the application
_global_tracker: Optional[ResponseQualityTracker] = None


def get_quality_tracker() -> ResponseQualityTracker:
    """Get the global response quality tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ResponseQualityTracker()
    return _global_tracker
