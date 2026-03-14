"""Tests for deliberation.utils — generate_slug."""

import pytest

from deliberation.utils import generate_slug


class TestGenerateSlug:
    """Tests for the generate_slug utility."""

    def test_normal_question_produces_slug(self):
        """A typical question yields a 3-5 word slug with stop words removed."""
        result = generate_slug("Review these architecture docs for risks")
        assert result == "architecture-docs-risks"

    def test_question_with_alternatives(self):
        """Questions with 'or' and '?' produce clean slugs."""
        result = generate_slug("Should we use Redis or Memcached for caching?")
        assert result == "use-redis-memcached-caching"

    def test_short_question(self):
        """Short questions with some stop words still produce a slug."""
        result = generate_slug("Is the AI Council MCP ready?")
        assert result == "ai-council-mcp-ready"

    def test_only_stop_words_returns_fallback(self):
        """A question made entirely of stop words falls back gracefully."""
        result = generate_slug("Can you please review these for us?")
        assert result == "deliberation"

    def test_empty_string_returns_fallback(self):
        """An empty string returns the fallback slug."""
        assert generate_slug("") == "deliberation"

    def test_whitespace_only_returns_fallback(self):
        """Whitespace-only input returns the fallback slug."""
        assert generate_slug("   ") == "deliberation"

    def test_none_returns_fallback(self):
        """None input returns the fallback slug."""
        assert generate_slug(None) == "deliberation"

    def test_very_long_question_limited_to_five_words(self):
        """A long question is truncated to at most 5 meaningful words."""
        long_q = (
            "Analyze the performance bottlenecks in our distributed "
            "microservice architecture spanning multiple cloud regions"
        )
        result = generate_slug(long_q)
        words = result.split("-")
        assert len(words) <= 5
        assert result == "analyze-performance-bottlenecks-distributed-microservice"

    def test_special_characters_stripped(self):
        """Special characters (quotes, brackets, etc.) are removed."""
        result = generate_slug('What about "best practices" for CI/CD pipelines?')
        assert result == "best-practices-cicd-pipelines"

    def test_slug_is_lowercase(self):
        """Output is always lowercase."""
        result = generate_slug("Compare AWS Lambda vs Azure Functions")
        assert result == result.lower()

    def test_no_leading_trailing_hyphens(self):
        """Slug has no leading or trailing hyphens."""
        result = generate_slug("the and or")
        # All stop words → fallback
        assert not result.startswith("-")
        assert not result.endswith("-")
