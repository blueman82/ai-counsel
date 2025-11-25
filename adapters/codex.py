"""Codex CLI adapter."""

from typing import Optional

from adapters.base import BaseCLIAdapter


class CodexAdapter(BaseCLIAdapter):
    """Adapter for codex CLI tool.

    Reasoning effort is configured via the {reasoning_effort} placeholder in config.yaml.
    The base class handles substitution - this adapter just validates the value.
    """

    # Valid reasoning effort levels for Codex CLI
    # See: codex exec --help for current options
    VALID_REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}

    def __init__(
        self,
        command: str = "codex",
        args: list[str] | None = None,
        timeout: int = 60,
        default_reasoning_effort: Optional[str] = None,
    ):
        """
        Initialize Codex adapter.

        Args:
            command: Command to execute (default: "codex")
            args: List of argument templates (from config.yaml with {reasoning_effort} placeholder)
            timeout: Timeout in seconds (default: 60)
            default_reasoning_effort: Default reasoning effort level (none/minimal/low/medium/high/xhigh).
                Used when {reasoning_effort} placeholder is in args. Can be overridden per-participant.
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        super().__init__(
            command=command,
            args=args,
            timeout=timeout,
            default_reasoning_effort=default_reasoning_effort,
        )

    async def invoke(
        self,
        prompt: str,
        model: str,
        context: Optional[str] = None,
        is_deliberation: bool = True,
        working_directory: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """
        Invoke Codex with optional reasoning_effort.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context
            is_deliberation: Whether this is part of a deliberation
            working_directory: Optional working directory for subprocess execution
            reasoning_effort: Optional reasoning effort level (none, minimal, low, medium, high, xhigh).
                Substituted into {reasoning_effort} placeholder by base class.

        Returns:
            Parsed response from the model

        Raises:
            ValueError: If reasoning_effort is invalid
            TimeoutError: If execution exceeds timeout
            RuntimeError: If CLI process fails
        """
        # Validate reasoning_effort if provided
        if reasoning_effort is not None and reasoning_effort not in self.VALID_REASONING_EFFORTS:
            raise ValueError(
                f"Invalid reasoning_effort '{reasoning_effort}' for Codex. "
                f"Valid values: {sorted(self.VALID_REASONING_EFFORTS)}"
            )

        # Base class handles {reasoning_effort} substitution via .format()
        return await super().invoke(
            prompt=prompt,
            model=model,
            context=context,
            is_deliberation=is_deliberation,
            working_directory=working_directory,
            reasoning_effort=reasoning_effort,
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
