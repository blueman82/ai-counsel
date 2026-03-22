"""Unit tests for web search tool and backends."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from deliberation.web_search import (
    WebSearchTool,
    DuckDuckGoBackend,
    TavilyBackend,
    WebSearchResult,
)
from models.tool_schema import ToolResult


class TestWebSearchResult:
    """Tests for WebSearchResult."""

    def test_str_representation(self):
        result = WebSearchResult(
            title="Test Title", url="https://example.com", snippet="A snippet."
        )
        text = str(result)
        assert "Test Title" in text
        assert "https://example.com" in text
        assert "A snippet." in text


class TestDuckDuckGoBackend:
    """Tests for DuckDuckGo backend."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        backend = DuckDuckGoBackend()

        # Mock the HTTP response with typical DDG HTML
        mock_html = '''
        <div class="result">
            <a class="result__a" href="https://example.com/page1">Example Page</a>
            <a class="result__snippet" href="#">This is a test snippet about the topic.</a>
        </div>
        '''

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            results = await backend.search("test query")

        assert len(results) == 1
        assert results[0].title == "Example Page"
        assert results[0].url == "https://example.com/page1"

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self):
        backend = DuckDuckGoBackend()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            results = await backend.search("test query")

        assert results == []

    def test_strip_html(self):
        assert DuckDuckGoBackend._strip_html("<b>bold</b> &amp; text") == "bold & text"


class TestTavilyBackend:
    """Tests for Tavily backend."""

    @pytest.mark.asyncio
    async def test_search_returns_results_with_ai_answer(self):
        backend = TavilyBackend(api_key="test-key")

        mock_response_data = {
            "answer": "AI-generated summary of results.",
            "results": [
                {
                    "title": "Tavily Result",
                    "url": "https://example.com/tavily",
                    "content": "Full extracted content from the page.",
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            results = await backend.search("test query")

        # Should have AI summary + 1 result
        assert len(results) == 2
        assert results[0].title == "AI Summary (Tavily)"
        assert "AI-generated summary" in results[0].snippet
        assert results[1].title == "Tavily Result"

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self):
        backend = TavilyBackend(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("API error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            results = await backend.search("test query")

        assert results == []


class TestWebSearchTool:
    """Tests for WebSearchTool."""

    def test_name_is_web_search(self):
        tool = WebSearchTool(provider="duckduckgo")
        assert tool.name == "web_search"

    def test_tavily_requires_api_key(self):
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            WebSearchTool(provider="tavily", tavily_api_key=None)

    def test_tavily_accepts_api_key(self):
        tool = WebSearchTool(provider="tavily", tavily_api_key="test-key")
        assert tool.name == "web_search"
        assert isinstance(tool.backend, TavilyBackend)

    def test_duckduckgo_is_default(self):
        tool = WebSearchTool()
        assert isinstance(tool.backend, DuckDuckGoBackend)

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        tool = WebSearchTool(provider="duckduckgo")
        result = await tool.execute({})
        assert not result.success
        assert "query" in result.error

    @pytest.mark.asyncio
    async def test_execute_returns_formatted_results(self):
        tool = WebSearchTool(provider="duckduckgo")

        mock_results = [
            WebSearchResult(title="Result 1", url="https://example.com", snippet="Snippet 1"),
        ]

        with patch.object(tool.backend, "search", new_callable=AsyncMock, return_value=mock_results):
            result = await tool.execute({"query": "test"})

        assert result.success
        assert "Result 1" in result.output
        assert "duckduckgo" in result.output

    @pytest.mark.asyncio
    async def test_execute_no_results(self):
        tool = WebSearchTool(provider="duckduckgo")

        with patch.object(tool.backend, "search", new_callable=AsyncMock, return_value=[]):
            result = await tool.execute({"query": "obscure query"})

        assert result.success
        assert "No results found" in result.output

    @pytest.mark.asyncio
    async def test_execute_handles_backend_exception(self):
        tool = WebSearchTool(provider="duckduckgo")

        with patch.object(
            tool.backend, "search", new_callable=AsyncMock, side_effect=RuntimeError("boom")
        ):
            result = await tool.execute({"query": "test"})

        assert not result.success
        assert "RuntimeError" in result.error
