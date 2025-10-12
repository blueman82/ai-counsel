"""Codex CLI adapter."""
from adapters.base import BaseCLIAdapter


class CodexAdapter(BaseCLIAdapter):
    """Adapter for codex CLI tool."""

    def __init__(self, timeout: int = 60):
        """
        Initialize Codex adapter.

        Args:
            timeout: Timeout in seconds (default: 60)
        """
        super().__init__(
            command="codex",
            args=["{model}", "{prompt}"],
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        """
        Parse codex output.

        Codex outputs clean responses without header/footer text,
        so we simply strip whitespace.

        Args:
            raw_output: Raw stdout from codex

        Returns:
            Parsed model response
        """
        return raw_output.strip()
