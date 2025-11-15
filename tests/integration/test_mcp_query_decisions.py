"""Integration tests for MCP query_decisions tool."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import TextContent

from decision_graph.storage import DecisionGraphStorage
from deliberation.query_engine import QueryEngine


@pytest.fixture
def mock_storage():
    """Mock decision graph storage."""
    storage = DecisionGraphStorage(":memory:")
    return storage


@pytest.fixture
def mock_engine(mock_storage):
    """Mock query engine."""
    return QueryEngine(mock_storage)


class TestMCPQueryDecisionsThreshold:
    """Test threshold parameter in query_decisions MCP tool."""

    @pytest.mark.integration
    async def test_threshold_parameter_in_schema(self):
        """Test threshold parameter exists in MCP tool schema."""
        from server import list_tools

        tools = await list_tools()

        query_tool = None
        for tool in tools:
            if tool.name == "query_decisions":
                query_tool = tool
                break

        assert query_tool is not None, "query_decisions tool not found"

        # Check threshold parameter exists in schema
        schema = query_tool.inputSchema
        assert "properties" in schema
        assert "threshold" in schema["properties"]

        threshold_spec = schema["properties"]["threshold"]
        assert threshold_spec["type"] == "number"
        assert threshold_spec["minimum"] == 0.0
        assert threshold_spec["maximum"] == 1.0
        assert threshold_spec["default"] == 0.6

    @pytest.mark.integration
    async def test_custom_threshold_passed_to_engine(self, mock_engine):
        """Test custom threshold value is used in query."""
        from server import call_tool

        with patch('server.QueryEngine', return_value=mock_engine):
            mock_engine.search_similar = AsyncMock(return_value=[])

            # Call with custom threshold
            arguments = {
                "query_text": "test query",
                "threshold": 0.4,
                "limit": 5
            }

            await call_tool("query_decisions", arguments)

            # Verify search_similar was called with custom threshold
            mock_engine.search_similar.assert_called_once()
            call_args = mock_engine.search_similar.call_args
            assert call_args.kwargs["threshold"] == 0.4

    @pytest.mark.integration
    async def test_empty_results_include_diagnostics(self, mock_storage):
        """Test empty results include diagnostic information."""
        from server import call_tool

        # Mock query engine to return empty results
        with patch('server.DecisionGraphStorage', return_value=mock_storage):
            engine = QueryEngine(mock_storage)

            # Mock diagnostics
            mock_diagnostics = {
                "matched_above_threshold": [],
                "total_decisions": 125,
                "best_match_score": 0.653,
                "near_misses": [],
                "suggested_threshold": 0.65
            }

            with patch.object(engine, 'get_search_diagnostics', return_value=mock_diagnostics):
                with patch('server.QueryEngine', return_value=engine):
                    engine.search_similar = AsyncMock(return_value=[])

                    arguments = {
                        "query_text": "test query",
                        "threshold": 0.7
                    }

                    response = await call_tool("query_decisions", arguments)

                    # Parse response
                    response_text = response[0].text
                    response_data = json.loads(response_text)

                    # Verify diagnostics included
                    assert "diagnostics" in response_data
                    assert response_data["diagnostics"]["total_decisions"] == 125
                    assert response_data["diagnostics"]["best_match_score"] == 0.653
