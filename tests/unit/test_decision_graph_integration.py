"""Unit tests for DecisionGraphIntegration with maintenance monitoring."""
from datetime import datetime
from unittest.mock import patch

import pytest

from decision_graph.integration import DecisionGraphIntegration
from decision_graph.schema import DecisionNode
from decision_graph.storage import DecisionGraphStorage
from models.schema import ConvergenceInfo, DeliberationResult, Summary


class TestDecisionGraphIntegrationMaintenance:
    """Test maintenance/monitoring integration in DecisionGraphIntegration."""

    @pytest.fixture
    def storage(self):
        """Create in-memory storage for testing."""
        return DecisionGraphStorage(":memory:")

    @pytest.fixture
    def integration(self, storage):
        """Create integration instance with background worker disabled."""
        return DecisionGraphIntegration(storage, enable_background_worker=False)

    @pytest.fixture
    def sample_result(self):
        """Create sample DeliberationResult for testing."""
        return DeliberationResult(
            status="complete",
            mode="test",
            participants=["test@cli"],
            rounds_completed=2,
            full_debate=[],
            summary=Summary(
                consensus="Test consensus",
                key_agreements=["Agreement 1"],
                key_disagreements=[],
                final_recommendation="Test recommendation",
            ),
            convergence_info=ConvergenceInfo(
                detected=True, status="converged", final_similarity=0.95
            ),
            voting_result=None,
            transcript_path="/test/transcript.md",
        )

    def test_should_initialize_maintenance_on_startup(self, integration):
        """Test that maintenance is initialized during integration startup."""
        assert integration.maintenance is not None
        assert integration._decision_count == 0

    def test_should_track_decision_count_on_store(self, integration, sample_result):
        """Test that decision count increments when storing deliberations."""
        # Initial count
        assert integration._decision_count == 0

        # Store first decision
        integration.store_deliberation("Question 1", sample_result)
        assert integration._decision_count == 1

        # Store second decision
        integration.store_deliberation("Question 2", sample_result)
        assert integration._decision_count == 2

        # Store third decision
        integration.store_deliberation("Question 3", sample_result)
        assert integration._decision_count == 3

    def test_should_log_stats_every_100_decisions(
        self, integration, sample_result, caplog
    ):
        """Test that stats are logged every 100 decisions."""
        import logging

        caplog.set_level(logging.INFO)

        # Store 99 decisions - no stats logged yet
        for i in range(99):
            integration.store_deliberation(f"Question {i}", sample_result)

        # No stats logging yet
        stats_logs = [r for r in caplog.records if "Decision graph stats" in r.message]
        assert len(stats_logs) == 0

        # Store 100th decision - should trigger stats logging
        integration.store_deliberation("Question 99", sample_result)

        # Should now have stats log
        stats_logs = [r for r in caplog.records if "Decision graph stats" in r.message]
        assert len(stats_logs) == 1
        assert "100 stored" in stats_logs[0].message
        assert "decisions" in stats_logs[0].message

    def test_should_warn_when_approaching_archival_threshold(
        self, integration, sample_result, caplog
    ):
        """Test that warning is logged when approaching 5000 decision threshold."""
        import logging

        caplog.set_level(logging.WARNING)

        # Mock stats to return 4500+ decisions
        with patch.object(integration.maintenance, "get_database_stats") as mock_stats:
            mock_stats.return_value = {
                "total_decisions": 4600,
                "total_stances": 13800,
                "total_similarities": 50000,
                "db_size_bytes": 10485760,
                "db_size_mb": 10.0,
            }

            # Manually set counter to 100 to trigger stats check
            integration._decision_count = 99
            integration.store_deliberation("Question", sample_result)

            # Should have warning about threshold
            warnings = [r for r in caplog.records if r.levelname == "WARNING"]
            threshold_warnings = [
                w for w in warnings if "approaching archival threshold" in w.message
            ]
            assert len(threshold_warnings) == 1
            assert "4600 decisions" in threshold_warnings[0].message
            assert "threshold: 5000" in threshold_warnings[0].message

    def test_should_not_warn_when_below_threshold(
        self, integration, sample_result, caplog
    ):
        """Test no warning when below 4500 decision threshold."""
        import logging

        caplog.set_level(logging.WARNING)

        # Mock stats to return <4500 decisions
        with patch.object(integration.maintenance, "get_database_stats") as mock_stats:
            mock_stats.return_value = {
                "total_decisions": 3000,
                "total_stances": 9000,
                "total_similarities": 20000,
                "db_size_bytes": 5242880,
                "db_size_mb": 5.0,
            }

            # Manually set counter to 100 to trigger stats check
            integration._decision_count = 99
            integration.store_deliberation("Question", sample_result)

            # Should NOT have warning about threshold
            warnings = [r for r in caplog.records if r.levelname == "WARNING"]
            threshold_warnings = [
                w for w in warnings if "approaching archival threshold" in w.message
            ]
            assert len(threshold_warnings) == 0

    def test_should_log_growth_analysis_every_500_decisions(
        self, integration, sample_result, caplog
    ):
        """Test that growth analysis is logged every 500 decisions."""
        import logging

        caplog.set_level(logging.INFO)

        # Mock stats and growth to avoid actual computation
        with patch.object(
            integration.maintenance, "get_database_stats"
        ) as mock_stats, patch.object(
            integration.maintenance, "analyze_growth"
        ) as mock_growth:
            mock_stats.return_value = {
                "total_decisions": 500,
                "total_stances": 1500,
                "total_similarities": 5000,
                "db_size_bytes": 2097152,
                "db_size_mb": 2.0,
            }

            mock_growth.return_value = {
                "analysis_period_days": 30,
                "decisions_in_period": 200,
                "avg_decisions_per_day": 6.67,
                "projected_decisions_30d": 200,
                "oldest_decision_date": "2025-01-01T00:00:00",
                "newest_decision_date": "2025-01-30T00:00:00",
            }

            # Manually set counter to 500 to trigger growth analysis
            integration._decision_count = 499
            integration.store_deliberation("Question", sample_result)

            # Should have growth analysis log
            growth_logs = [r for r in caplog.records if "Growth analysis" in r.message]
            assert len(growth_logs) == 1
            assert "200 decisions in 30 days" in growth_logs[0].message
            assert "avg 6.67/day" in growth_logs[0].message

    def test_should_handle_stats_collection_errors_gracefully(
        self, integration, sample_result, caplog
    ):
        """Test that errors in stats collection don't break deliberation storage."""
        import logging

        caplog.set_level(logging.ERROR)

        # Mock stats to raise exception
        with patch.object(integration.maintenance, "get_database_stats") as mock_stats:
            mock_stats.side_effect = Exception("Database error")

            # Manually set counter to 100 to trigger stats check
            integration._decision_count = 99

            # Should NOT raise exception, just log error
            decision_id = integration.store_deliberation("Question", sample_result)
            assert decision_id is not None

            # Should have error log
            errors = [r for r in caplog.records if r.levelname == "ERROR"]
            stats_errors = [
                e for e in errors if "Error collecting maintenance stats" in e.message
            ]
            assert len(stats_errors) == 1

    def test_get_graph_stats_returns_stats(self, integration):
        """Test get_graph_stats() returns database statistics."""
        # Store some decisions
        sample_result = DeliberationResult(
            status="complete",
            mode="test",
            participants=["test@cli"],
            rounds_completed=1,
            full_debate=[],
            summary=Summary(
                consensus="Test",
                key_agreements=[],
                key_disagreements=[],
                final_recommendation="Test",
            ),
            convergence_info=ConvergenceInfo(
                detected=False, status="unknown", final_similarity=0.0
            ),
            voting_result=None,
            transcript_path="/test.md",
        )

        integration.store_deliberation("Q1", sample_result)
        integration.store_deliberation("Q2", sample_result)

        # Get stats
        stats = integration.get_graph_stats()

        # Verify structure
        assert "total_decisions" in stats
        assert "total_stances" in stats
        assert "total_similarities" in stats
        assert "db_size_bytes" in stats
        assert "db_size_mb" in stats

        # Verify counts (should have 2 decisions)
        assert stats["total_decisions"] == 2

    def test_get_graph_stats_handles_errors_gracefully(self, integration):
        """Test get_graph_stats() returns empty dict on error."""
        # Mock maintenance to raise exception
        with patch.object(integration.maintenance, "get_database_stats") as mock_stats:
            mock_stats.side_effect = Exception("Database error")

            # Should return empty dict, not raise
            stats = integration.get_graph_stats()
            assert stats == {}

    def test_health_check_returns_healthy_status(self, integration):
        """Test health_check() returns healthy status for clean database."""
        # Get health check
        health = integration.health_check()

        # Verify structure
        assert "healthy" in health
        assert "checks_passed" in health
        assert "checks_failed" in health
        assert "issues" in health
        assert "details" in health

        # Should be healthy (empty database has no issues)
        assert health["healthy"] is True
        assert health["checks_failed"] == 0
        assert len(health["issues"]) == 0

    def test_health_check_detects_unhealthy_status(self, integration):
        """Test health_check() detects issues in database."""
        # Mock health check to return issues
        with patch.object(integration.maintenance, "health_check") as mock_health:
            mock_health.return_value = {
                "healthy": False,
                "checks_passed": 4,
                "checks_failed": 2,
                "issues": [
                    "Found 5 orphaned participant stances",
                    "Found 3 similarities with invalid scores",
                ],
                "details": {"orphaned_stances": 5, "invalid_similarity_scores": 3},
            }

            # Get health check
            health = integration.health_check()

            # Should report unhealthy
            assert health["healthy"] is False
            assert health["checks_failed"] == 2
            assert len(health["issues"]) == 2

    def test_health_check_handles_errors_gracefully(self, integration):
        """Test health_check() returns error status on exception."""
        # Mock health check to raise exception
        with patch.object(integration.maintenance, "health_check") as mock_health:
            mock_health.side_effect = Exception("Database error")

            # Should return error status, not raise
            health = integration.health_check()

            assert health["healthy"] is False
            assert health["checks_failed"] == 1
            assert len(health["issues"]) == 1
            assert "Health check error" in health["issues"][0]

    def test_periodic_checks_use_decision_count_not_db_count(
        self, integration, sample_result
    ):
        """Test that periodic checks use stored decision count, not DB query count."""
        # This ensures we don't trigger on decision 100 in DB if we've only stored 50
        # via this integration instance (e.g., after restart)

        # Manually set DB to have 150 decisions
        for i in range(150):
            node = DecisionNode(
                id=f"dec-{i}",
                question=f"Question {i}",
                timestamp=datetime.now(),
                consensus="Test",
                winning_option=None,
                convergence_status="converged",
                participants=["test@cli"],
                transcript_path="/test.md",
            )
            integration.storage.save_decision_node(node)

        # Reset integration counter to 0
        integration._decision_count = 0

        # Store decisions via integration
        import logging

        # Capture logs
        log_capture = []
        handler = logging.Handler()
        handler.emit = lambda record: log_capture.append(record)
        logger = logging.getLogger("decision_graph.integration")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            # Store 99 decisions - should NOT trigger stats (count is 99, not 100)
            for i in range(99):
                integration.store_deliberation(f"New Question {i}", sample_result)

            stats_logs_before = [
                r for r in log_capture if "Decision graph stats" in r.message
            ]
            assert (
                len(stats_logs_before) == 0
            ), "Should not log stats before 100 stored decisions"

            # Store 100th decision - should trigger stats
            integration.store_deliberation("New Question 99", sample_result)

            stats_logs_after = [
                r for r in log_capture if "Decision graph stats" in r.message
            ]
            assert (
                len(stats_logs_after) == 1
            ), "Should log stats at 100 stored decisions"

        finally:
            logger.removeHandler(handler)

    def test_stats_logging_includes_all_metrics(
        self, integration, sample_result, caplog
    ):
        """Test that stats logging includes all expected metrics."""
        import logging

        caplog.set_level(logging.INFO)

        # Manually set counter to trigger stats
        integration._decision_count = 99
        integration.store_deliberation("Question", sample_result)

        # Find stats log
        stats_logs = [r for r in caplog.records if "Decision graph stats" in r.message]
        assert len(stats_logs) == 1

        message = stats_logs[0].message

        # Verify all metrics present
        assert "decisions" in message
        assert "stances" in message
        assert "similarities" in message
        assert "MB" in message
