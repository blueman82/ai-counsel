"""Claude CLI adapter."""
from __future__ import annotations

import logging

from adapters.base import BaseCLIAdapter

logger = logging.getLogger(__name__)

# Exact supported IDs; dated snapshots may append a suffix. Aliases select current models.
_EFFORT_MODELS = (
    "claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5",
    "claude-haiku-5-5", "claude-opus-4-7", "claude-sonnet-4-6",
)


class ClaudeAdapter(BaseCLIAdapter):
    """Adapter for claude CLI tool.

    The current Fable, Opus, Sonnet, and Haiku models support effort.
    """

    # Valid reasoning effort levels for current Claude models
    VALID_REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max"}

    def __init__(
        self,
        command: str = "claude",
        args: list[str] | None = None,
        timeout: int = 60,
        default_reasoning_effort: str | None = None,
    ) -> None:
        """Initialize Claude adapter.

        Args:
            command: Command to execute (default: "claude")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 60)
            default_reasoning_effort: Default reasoning effort for supported models. Can be overridden per-participant.
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        if (
            default_reasoning_effort is not None
            and default_reasoning_effort not in self.VALID_REASONING_EFFORTS
        ):
            raise ValueError(
                f"Invalid default_reasoning_effort '{default_reasoning_effort}' for Claude. "
                f"Valid values: {sorted(self.VALID_REASONING_EFFORTS)}"
            )
        super().__init__(
            command=command,
            args=args,
            timeout=timeout,
            default_reasoning_effort=default_reasoning_effort,
        )

    @staticmethod
    def _supports_effort(model: str) -> bool:
        """Check current model aliases and explicitly supported model IDs."""
        model_lower = model.lower()
        return model_lower in {"fable", "opus", "sonnet", "haiku"} or any(
            model_lower == name or model_lower.startswith(name + "-")
            for name in _EFFORT_MODELS
        )

    async def invoke(
        self,
        prompt: str,
        model: str,
        context: str | None = None,
        is_deliberation: bool = True,
        working_directory: str | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        """Invoke Claude with optional reasoning effort.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context
            is_deliberation: Whether this is part of a deliberation
            working_directory: Optional working directory for subprocess execution
            reasoning_effort: Optional reasoning effort level (low/medium/high/xhigh/max).
                Requires a supported model; older Haiku versions do not support effort.

        Returns:
            Parsed response from the model

        Raises:
            ValueError: If reasoning_effort is invalid or used with an unsupported model
            TimeoutError: If execution exceeds timeout
            RuntimeError: If CLI process fails
        """
        # Determine effective effort: runtime > config default > None
        effective_effort = reasoning_effort or self.default_reasoning_effort

        if effective_effort is not None:
            if effective_effort not in self.VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort '{effective_effort}' for Claude. "
                    f"Valid values: {sorted(self.VALID_REASONING_EFFORTS)}"
                )
            if not self._supports_effort(model):
                raise ValueError(
                    f"reasoning_effort is not supported for '{model}'. "
                    "Use a current Fable, Opus, Sonnet, or Haiku model."
                )

        # Base invoke formats arguments synchronously before its first await.
        # Concurrent calls therefore capture their own effort before this can change.
        self._pending_effort = effective_effort

        try:
            # Pass None for reasoning_effort — Claude's config has no {reasoning_effort}
            # placeholder. We dynamically inject the flag in _adjust_args_for_context.
            return await super().invoke(
                prompt=prompt,
                model=model,
                context=context,
                is_deliberation=is_deliberation,
                working_directory=working_directory,
                reasoning_effort=None,
            )
        finally:
            self._pending_effort = None

    def _adjust_args_for_context(self, is_deliberation: bool) -> list[str]:
        """Auto-detect context and adjust flags accordingly.

        For deliberations, removes -p flag so Claude engages fully.
        For supported models with reasoning effort, injects --effort flag.

        Args:
            is_deliberation: True if running as part of a deliberation

        Returns:
            Adjusted argument list
        """
        args = self.args.copy()

        if is_deliberation:
            # Remove -p flag for deliberations (we want full engagement)
            if "-p" in args:
                args.remove("-p")
        elif "-p" not in args:
            # Add -p flag for Claude Code work (project context awareness)
            if "--model" in args:
                model_idx = args.index("--model")
                args.insert(model_idx + 2, "-p")
            else:
                args.insert(0, "-p")

        # Inject --effort for supported models when effort is specified
        effort = getattr(self, "_pending_effort", None)
        if effort is not None:
            # Insert before the prompt placeholder (last arg)
            args.insert(-1, "--effort")
            args.insert(-1, effort)

        return args

    def parse_output(self, raw_output: str) -> str:
        """Parse claude CLI output.

        Claude CLI with -p flag typically outputs header/initialization text,
        blank lines, then actual model response. We extract everything after
        the first substantial block of text.

        Args:
            raw_output: Raw stdout from claude CLI

        Returns:
            Parsed model response
        """
        lines = raw_output.strip().split("\n")

        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not any(
                keyword in line.lower()
                for keyword in ["claude code", "loading", "version", "initializing"]
            ):
                start_idx = i
                break

        return "\n".join(lines[start_idx:]).strip()
