"""Droid CLI adapter."""
from adapters.base import BaseCLIAdapter


class DroidAdapter(BaseCLIAdapter):
    """Adapter for droid CLI tool (Factory AI)."""

    def __init__(
        self, command: str = "droid", args: list[str] | None = None, timeout: int = 60
    ):
        """
        Initialize Droid adapter.

        Args:
            command: Command to execute (default: "droid")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 60)

        Note:
            The droid CLI uses `droid exec "prompt"` syntax for non-interactive mode.
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        super().__init__(command=command, args=args, timeout=timeout)

    def parse_output(self, raw_output: str) -> str:
        """
        Parse droid output.

        Droid outputs clean responses without header/footer text,
        so we simply strip whitespace.

        Args:
            raw_output: Raw stdout from droid

        Returns:
            Parsed model response
        """
        return raw_output.strip()
