"""Gemini CLI adapter."""
from adapters.base import BaseCLIAdapter


class GeminiAdapter(BaseCLIAdapter):
    """Adapter for gemini CLI tool (Google AI)."""

    def __init__(self, command: str = "gemini", args: list[str] | None = None, timeout: int = 60):
        """
        Initialize Gemini adapter.

        Args:
            command: Command to execute (default: "gemini")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 60)

        Note:
            The gemini CLI uses `gemini -p "prompt"` or `gemini -m model -p "prompt"` syntax.
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        super().__init__(
            command=command,
            args=args,
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        """
        Parse gemini output.

        Gemini outputs clean responses without header/footer text,
        so we simply strip whitespace.

        Args:
            raw_output: Raw stdout from gemini

        Returns:
            Parsed model response
        """
        return raw_output.strip()
