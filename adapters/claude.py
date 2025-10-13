"""Claude CLI adapter."""
from adapters.base import BaseCLIAdapter


class ClaudeAdapter(BaseCLIAdapter):
    """Adapter for claude CLI tool."""

    def __init__(self, timeout: int = 60):
        """
        Initialize Claude Code adapter.

        Args:
            timeout: Timeout in seconds (default: 60)
        """
        super().__init__(
            command="claude-code",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        """
        Parse claude-code output.

        Claude code typically outputs:
        - Header/initialization text
        - Blank lines
        - Actual model response

        We extract everything after the first substantial block of text.

        Args:
            raw_output: Raw stdout from claude-code

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
