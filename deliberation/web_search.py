"""Web search tool for evidence-based deliberation."""
import html
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus

import httpx

from deliberation.tools import BaseTool
from models.tool_schema import ToolResult

logger = logging.getLogger(__name__)


class WebSearchResult:
    """A single web search result."""

    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

    def __str__(self) -> str:
        return f"**{self.title}**\n{self.url}\n{self.snippet}"


class DuckDuckGoBackend:
    """
    DuckDuckGo search backend using the HTML endpoint.

    Free, no API key required. Returns titles, URLs, and snippets.
    """

    SEARCH_URL = "https://html.duckduckgo.com/html/"
    TIMEOUT = 10

    async def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Execute a DuckDuckGo search and parse HTML results."""
        results = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.SEARCH_URL,
                    data={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; AI-Counsel/1.0)"
                    },
                    timeout=self.TIMEOUT,
                    follow_redirects=True,
                )
                response.raise_for_status()

            results = self._parse_html(response.text, max_results)
        except httpx.HTTPError as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        except Exception as e:
            logger.warning(f"DuckDuckGo parsing failed: {e}")

        return results

    def _parse_html(self, html_text: str, max_results: int) -> List[WebSearchResult]:
        """Parse DuckDuckGo HTML response to extract results."""
        results = []

        # Find result blocks: <a class="result__a" href="...">title</a>
        # and <a class="result__snippet" ...>snippet</a>
        result_blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html_text,
            re.DOTALL,
        )

        for url, title_html, snippet_html in result_blocks[:max_results]:
            title = self._strip_html(title_html).strip()
            snippet = self._strip_html(snippet_html).strip()
            url = html.unescape(url)

            if title and url:
                results.append(WebSearchResult(title=title, url=url, snippet=snippet))

        return results

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags and decode entities."""
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)


class TavilyBackend:
    """
    Tavily search backend — AI-optimized search with content extraction.

    Requires TAVILY_API_KEY. Returns cleaned content, relevance scores,
    and optional AI-generated summaries.
    """

    SEARCH_URL = "https://api.tavily.com/search"
    TIMEOUT = 15

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """Execute a Tavily search with content extraction."""
        results = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.SEARCH_URL,
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": max_results,
                        "include_answer": True,
                        "search_depth": "advanced",
                    },
                    timeout=self.TIMEOUT,
                )
                response.raise_for_status()

            data = response.json()

            # Include Tavily's AI-generated answer as first result if available
            ai_answer = data.get("answer")
            if ai_answer:
                results.append(
                    WebSearchResult(
                        title="AI Summary (Tavily)",
                        url="",
                        snippet=ai_answer,
                    )
                )

            # Parse individual results
            for item in data.get("results", [])[:max_results]:
                title = item.get("title", "")
                url = item.get("url", "")
                # Tavily provides full content — use it if available, fall back to snippet
                content = item.get("content", "")
                results.append(
                    WebSearchResult(title=title, url=url, snippet=content)
                )

        except httpx.HTTPError as e:
            logger.warning(f"Tavily search failed: {e}")
        except Exception as e:
            logger.warning(f"Tavily response parsing failed: {e}")

        return results


class WebSearchTool(BaseTool):
    """
    Web search tool for deliberation models.

    Supports DuckDuckGo (free) and Tavily (paid, AI-optimized) backends.
    Models invoke via: TOOL_REQUEST: {"name": "web_search", "arguments": {"query": "..."}}
    """

    def __init__(
        self,
        provider: str = "duckduckgo",
        tavily_api_key: Optional[str] = None,
        max_results: int = 5,
    ):
        if provider == "tavily":
            if not tavily_api_key:
                raise ValueError("Tavily backend requires TAVILY_API_KEY")
            self.backend = TavilyBackend(api_key=tavily_api_key)
        else:
            self.backend = DuckDuckGoBackend()

        self.max_results = max_results
        self._provider = provider

    @property
    def name(self) -> str:
        return "web_search"

    async def execute(self, arguments: dict) -> ToolResult:
        """
        Execute a web search.

        Args:
            arguments: Must contain 'query' key with search terms.
                       Optional 'max_results' (default: 5).

        Returns:
            ToolResult with formatted search results or error.
        """
        query = arguments.get("query")
        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required argument: 'query'",
            )

        max_results = arguments.get("max_results", self.max_results)

        try:
            results = await self.backend.search(query, max_results=max_results)

            if not results:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"No results found for: {query}",
                    error=None,
                )

            formatted = f"Web search results for: **{query}** ({self._provider})\n\n"
            for i, result in enumerate(results, 1):
                formatted += f"### Result {i}\n{result}\n\n"

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=formatted.strip(),
                error=None,
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Web search failed: {type(e).__name__}: {str(e)}",
            )
