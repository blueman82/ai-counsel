"""Unit tests for response quality metrics tracking."""

import pytest

from deliberation.metrics import (
    ModelMetrics,
    ResponseQualityTracker,
    get_quality_tracker,
)


class TestModelMetrics:
    """Tests for ModelMetrics dataclass."""

    def test_initial_values(self):
        """Test that ModelMetrics initializes with correct defaults."""
        metrics = ModelMetrics(model_id="test-model")

        assert metrics.model_id == "test-model"
        assert metrics.total_responses == 0
        assert metrics.successful_votes == 0
        assert metrics.failed_votes == 0
        assert metrics.abstain_votes == 0
        assert metrics.total_response_length == 0
        assert metrics.truncated_responses == 0
        assert metrics.total_response_time_ms == 0.0

    def test_vote_success_rate_zero_responses(self):
        """Test vote success rate with no responses returns 0."""
        metrics = ModelMetrics(model_id="test-model")
        assert metrics.vote_success_rate == 0.0

    def test_vote_success_rate_calculation(self):
        """Test vote success rate calculation."""
        metrics = ModelMetrics(
            model_id="test-model",
            total_responses=10,
            successful_votes=7,
        )
        assert metrics.vote_success_rate == 70.0

    def test_avg_response_length_zero_responses(self):
        """Test average response length with no responses returns 0."""
        metrics = ModelMetrics(model_id="test-model")
        assert metrics.avg_response_length == 0.0

    def test_avg_response_length_calculation(self):
        """Test average response length calculation."""
        metrics = ModelMetrics(
            model_id="test-model",
            total_responses=4,
            total_response_length=4000,
        )
        assert metrics.avg_response_length == 1000.0

    def test_truncation_rate_zero_responses(self):
        """Test truncation rate with no responses returns 0."""
        metrics = ModelMetrics(model_id="test-model")
        assert metrics.truncation_rate == 0.0

    def test_truncation_rate_calculation(self):
        """Test truncation rate calculation."""
        metrics = ModelMetrics(
            model_id="test-model",
            total_responses=20,
            truncated_responses=4,
        )
        assert metrics.truncation_rate == 20.0

    def test_avg_response_time_zero_responses(self):
        """Test average response time with no responses returns 0."""
        metrics = ModelMetrics(model_id="test-model")
        assert metrics.avg_response_time_ms == 0.0

    def test_avg_response_time_calculation(self):
        """Test average response time calculation."""
        metrics = ModelMetrics(
            model_id="test-model",
            total_responses=5,
            total_response_time_ms=10000.0,
        )
        assert metrics.avg_response_time_ms == 2000.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metrics = ModelMetrics(
            model_id="test-model",
            total_responses=10,
            successful_votes=7,
            failed_votes=2,
            abstain_votes=1,
            total_response_length=10000,
            truncated_responses=1,
            total_response_time_ms=5000.0,
        )

        result = metrics.to_dict()

        assert result["model_id"] == "test-model"
        assert result["total_responses"] == 10
        assert result["successful_votes"] == 7
        assert result["failed_votes"] == 2
        assert result["abstain_votes"] == 1
        assert result["vote_success_rate"] == 70.0
        assert result["avg_response_length"] == 1000
        assert result["truncated_responses"] == 1
        assert result["truncation_rate"] == 10.0
        assert result["avg_response_time_ms"] == 500


class TestResponseQualityTracker:
    """Tests for ResponseQualityTracker class."""

    def test_get_or_create_model_new(self):
        """Test creating a new model entry."""
        tracker = ResponseQualityTracker()

        metrics = tracker.get_or_create_model("new-model")

        assert metrics.model_id == "new-model"
        assert "new-model" in tracker.model_metrics

    def test_get_or_create_model_existing(self):
        """Test getting an existing model entry."""
        tracker = ResponseQualityTracker()

        first = tracker.get_or_create_model("model-a")
        first.total_responses = 5

        second = tracker.get_or_create_model("model-a")

        assert second.total_responses == 5
        assert first is second

    def test_record_response_success(self):
        """Test recording a successful vote response."""
        tracker = ResponseQualityTracker()

        tracker.record_response(
            model_id="claude",
            response_length=1500,
            vote_success=True,
            is_abstain=False,
            was_truncated=False,
            response_time_ms=500.0,
        )

        metrics = tracker.model_metrics["claude"]
        assert metrics.total_responses == 1
        assert metrics.successful_votes == 1
        assert metrics.failed_votes == 0
        assert metrics.abstain_votes == 0
        assert metrics.total_response_length == 1500
        assert metrics.truncated_responses == 0
        assert metrics.total_response_time_ms == 500.0

    def test_record_response_failed(self):
        """Test recording a failed vote response."""
        tracker = ResponseQualityTracker()

        tracker.record_response(
            model_id="codex",
            response_length=200,
            vote_success=False,
            is_abstain=False,
            was_truncated=False,
        )

        metrics = tracker.model_metrics["codex"]
        assert metrics.total_responses == 1
        assert metrics.successful_votes == 0
        assert metrics.failed_votes == 1
        assert metrics.abstain_votes == 0

    def test_record_response_abstain(self):
        """Test recording an abstain vote response."""
        tracker = ResponseQualityTracker()

        tracker.record_response(
            model_id="gemini",
            response_length=300,
            vote_success=False,
            is_abstain=True,
            was_truncated=False,
        )

        metrics = tracker.model_metrics["gemini"]
        assert metrics.total_responses == 1
        assert metrics.successful_votes == 0
        assert metrics.failed_votes == 0
        assert metrics.abstain_votes == 1

    def test_record_response_truncated(self):
        """Test recording a truncated response."""
        tracker = ResponseQualityTracker()

        tracker.record_response(
            model_id="droid",
            response_length=4000,
            vote_success=True,
            was_truncated=True,
        )

        metrics = tracker.model_metrics["droid"]
        assert metrics.truncated_responses == 1

    def test_record_multiple_responses_same_model(self):
        """Test recording multiple responses for the same model."""
        tracker = ResponseQualityTracker()

        # Record 3 responses for same model
        tracker.record_response("model-a", 1000, True, False, False, 100.0)
        tracker.record_response("model-a", 1200, True, False, False, 120.0)
        tracker.record_response("model-a", 800, False, False, True, 80.0)

        metrics = tracker.model_metrics["model-a"]
        assert metrics.total_responses == 3
        assert metrics.successful_votes == 2
        assert metrics.failed_votes == 1
        assert metrics.total_response_length == 3000
        assert metrics.truncated_responses == 1
        assert metrics.total_response_time_ms == 300.0

    def test_get_summary_empty(self):
        """Test getting summary with no data."""
        tracker = ResponseQualityTracker()

        summary = tracker.get_summary()

        assert "session_start" in summary
        assert summary["total_deliberations"] == 0
        assert summary["models"] == {}
        assert summary["aggregate"]["total_responses"] == 0
        assert summary["aggregate"]["overall_vote_success_rate"] == 0.0
        assert summary["aggregate"]["overall_truncation_rate"] == 0.0

    def test_get_summary_with_data(self):
        """Test getting summary with recorded data."""
        tracker = ResponseQualityTracker()
        tracker.total_deliberations = 2

        # Model A: 2 successful, 1 failed, 1 truncated
        tracker.record_response("model-a", 1000, True, False, False)
        tracker.record_response("model-a", 1200, True, False, False)
        tracker.record_response("model-a", 800, False, False, True)

        # Model B: 1 successful, 0 failed
        tracker.record_response("model-b", 1500, True, False, False)

        summary = tracker.get_summary()

        assert summary["total_deliberations"] == 2
        assert len(summary["models"]) == 2
        assert "model-a" in summary["models"]
        assert "model-b" in summary["models"]

        # Aggregate: 3 successful / 4 total = 75%
        assert summary["aggregate"]["total_responses"] == 4
        assert summary["aggregate"]["overall_vote_success_rate"] == 75.0
        # 1 truncated / 4 total = 25%
        assert summary["aggregate"]["overall_truncation_rate"] == 25.0

    def test_get_problem_models_none(self):
        """Test get_problem_models returns empty with good data."""
        tracker = ResponseQualityTracker()

        # Model with good metrics (high vote rate, no truncation, long responses)
        for _ in range(5):
            tracker.record_response("good-model", 2000, True, False, False)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 0

    def test_get_problem_models_low_vote_rate(self):
        """Test get_problem_models flags low vote success rate."""
        tracker = ResponseQualityTracker()

        # Model with 40% vote success rate (below 50% threshold)
        tracker.record_response("bad-voter", 2000, True, False, False)
        tracker.record_response("bad-voter", 2000, True, False, False)
        tracker.record_response("bad-voter", 2000, False, False, False)
        tracker.record_response("bad-voter", 2000, False, False, False)
        tracker.record_response("bad-voter", 2000, False, False, False)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 1
        assert problems[0]["model_id"] == "bad-voter"
        assert any("low vote rate" in issue for issue in problems[0]["issues"])

    def test_get_problem_models_high_truncation(self):
        """Test get_problem_models flags high truncation rate."""
        tracker = ResponseQualityTracker()

        # Model with 20% truncation rate (above 10% threshold)
        tracker.record_response("truncated", 2000, True, False, False)
        tracker.record_response("truncated", 2000, True, False, False)
        tracker.record_response("truncated", 2000, True, False, False)
        tracker.record_response("truncated", 2000, True, False, True)
        tracker.record_response("truncated", 2000, True, False, True)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 1
        assert problems[0]["model_id"] == "truncated"
        assert any("high truncation" in issue for issue in problems[0]["issues"])

    def test_get_problem_models_short_responses(self):
        """Test get_problem_models flags short responses."""
        tracker = ResponseQualityTracker()

        # Model with average 200 chars (below 500 char threshold)
        tracker.record_response("short", 150, True, False, False)
        tracker.record_response("short", 200, True, False, False)
        tracker.record_response("short", 250, True, False, False)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 1
        assert problems[0]["model_id"] == "short"
        assert any("short responses" in issue for issue in problems[0]["issues"])

    def test_get_problem_models_min_responses(self):
        """Test get_problem_models respects min_responses threshold."""
        tracker = ResponseQualityTracker()

        # Model with issues but only 2 responses (below min_responses=3)
        tracker.record_response("too-few", 100, False, False, True)
        tracker.record_response("too-few", 100, False, False, True)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 0  # Should not be flagged

    def test_get_problem_models_multiple_issues(self):
        """Test get_problem_models reports multiple issues for one model."""
        tracker = ResponseQualityTracker()

        # Model with all problems: low vote rate, high truncation, short responses
        tracker.record_response("bad-all", 100, False, False, True)
        tracker.record_response("bad-all", 100, False, False, True)
        tracker.record_response("bad-all", 100, False, False, True)

        problems = tracker.get_problem_models(min_responses=3)

        assert len(problems) == 1
        assert problems[0]["model_id"] == "bad-all"
        assert len(problems[0]["issues"]) == 3  # All 3 issues

    def test_reset(self):
        """Test resetting the tracker."""
        tracker = ResponseQualityTracker()
        tracker.total_deliberations = 5
        tracker.record_response("model-a", 1000, True, False, False)
        tracker.record_response("model-b", 1200, True, False, False)

        # Manually set an old session start to ensure reset changes it
        tracker.session_start = "2020-01-01T00:00:00.000000"
        tracker.reset()

        assert len(tracker.model_metrics) == 0
        assert tracker.total_deliberations == 0
        # Session start should be updated to a recent timestamp
        assert tracker.session_start.startswith("202")  # Year 2020s
        assert tracker.session_start != "2020-01-01T00:00:00.000000"


class TestGlobalTracker:
    """Tests for global tracker instance."""

    def test_get_quality_tracker_singleton(self):
        """Test that get_quality_tracker returns the same instance."""
        # Note: This test may be affected by other tests using the global tracker
        tracker1 = get_quality_tracker()
        tracker2 = get_quality_tracker()

        assert tracker1 is tracker2

    def test_get_quality_tracker_creates_if_none(self):
        """Test that get_quality_tracker creates a new instance if needed."""
        tracker = get_quality_tracker()

        assert tracker is not None
        assert isinstance(tracker, ResponseQualityTracker)
