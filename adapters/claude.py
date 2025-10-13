"""Claude CLI adapter."""
from adapters.base import BaseCLIAdapter


class ClaudeAdapter(BaseCLIAdapter):
    """Adapter for claude CLI tool."""

    def __init__(self, command: str = "claude", args: list[str] | None = None, timeout: int = 60):
        """
        Initialize Claude adapter.

        Args:
            command: Command to execute (default: "claude")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 60)
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
        Parse claude CLI output.

        Claude CLI with -p flag typically outputs:
        - Header/initialization text
        - Blank lines
        - Actual model response

        We extract everything after the first substantial block of text.

        Args:
            raw_output: Raw stdout from claude CLI

        Returns:
            Parsed model response
        """
        lines = raw_output.strip().split('\n')

        # Skip header lines (typically start with "Claude Code", "Loading", etc.)
        # Find first line that looks like model output (substantial content)
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not any(
                keyword in line.lower()
                for keyword in ['claude code', 'loading', 'version', 'initializing']
            ):
                start_idx = i
                break

        # Join remaining lines
        response = '\n'.join(lines[start_idx:]).strip()
        return response
