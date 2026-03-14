"""Utility functions for the deliberation module."""

import re

# Common filler/stop words to strip from questions when generating slugs
_STOP_WORDS = frozenset({
    "review", "these", "the", "for", "and", "documents", "please", "can",
    "you", "should", "we", "is", "are", "what", "how", "do", "does", "this",
    "that", "with", "from", "about", "our", "my", "a", "an", "of", "in",
    "on", "to", "or",
})

_FALLBACK_SLUG = "deliberation"


def generate_slug(question: str) -> str:
    """Generate a 3-5 word slug from a deliberation question.

    Strips stop/filler words, takes the first 4-5 meaningful words,
    and returns a lowercase hyphenated slug with no special characters.
    The caller is responsible for prepending a timestamp.

    Args:
        question: The deliberation question text.

    Returns:
        A short slug like "architecture-docs-risks".
    """
    if not question or not question.strip():
        return _FALLBACK_SLUG

    # Lowercase and strip special characters (keep only alphanumeric and spaces)
    cleaned = re.sub(r"[^a-z0-9\s]", "", question.lower())

    # Split into words and filter out stop words
    words = [w for w in cleaned.split() if w and w not in _STOP_WORDS]

    if not words:
        return _FALLBACK_SLUG

    # Take first 5 meaningful words (targeting 3-5 word slugs)
    slug = "-".join(words[:5])

    return slug
