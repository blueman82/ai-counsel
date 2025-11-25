"""Base CLI adapter with subprocess management."""
import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseCLIAdapter(ABC):
    """
    Abstract base class for CLI tool adapters.

    Handles subprocess execution, timeout management, and error handling.
    Subclasses must implement parse_output() for tool-specific parsing.
    """

    # Transient error patterns that warrant retry
    TRANSIENT_ERROR_PATTERNS = [
        r"503.*overload",
        r"503.*over capacity",
        r"503.*too many requests",
        r"429.*rate limit",
        r"temporarily unavailable",
        r"service unavailable",
        r"connection.*reset",
        r"connection.*refused",
    ]

    def __init__(
        self,
        command: str,
        args: list[str],
        timeout: int = 60,
        max_retries: int = 2,
        default_reasoning_effort: Optional[str] = None,
    ):
        """
        Initialize CLI adapter.

        Args:
            command: CLI command to execute
            args: List of argument templates (may contain {model}, {prompt} placeholders)
            timeout: Timeout in seconds (default: 60)
            max_retries: Maximum retry attempts for transient errors (default: 2)
            default_reasoning_effort: Default reasoning effort level for this adapter.
                Only applicable to codex (low/medium/high/extra-high) and droid (off/low/medium/high).
                Ignored by other adapters. Can be overridden per-participant.
        """
        self.command = command
        self.args = args
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_reasoning_effort = default_reasoning_effort

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
        Invoke the CLI tool with the given prompt and model.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context
            is_deliberation: Whether this is part of a deliberation (auto-adjusts -p flag for Claude)
            working_directory: Optional working directory for subprocess execution (defaults to current directory)
            reasoning_effort: Optional reasoning effort level for models that support it.
                Subclasses may use this to pass adapter-specific flags (e.g., Codex --reasoning).
                Base implementation ignores this parameter.

        Returns:
            Parsed response from the model

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If CLI process fails
        """
        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"

        # Validate prompt length if adapter supports it
        if hasattr(self, "validate_prompt_length"):
            if not self.validate_prompt_length(full_prompt):
                raise ValueError(
                    f"Prompt too long ({len(full_prompt)} chars). "
                    f"Maximum allowed: {getattr(self, 'MAX_PROMPT_CHARS', 'unknown')} chars. "
                    "This prevents API rejection errors."
                )

        # Adjust args based on context (for auto-detecting deliberation mode)
        args = self._adjust_args_for_context(is_deliberation)

        # Determine working directory for subprocess
        # Use provided working_directory if specified, otherwise use current directory
        import os

        cwd = working_directory if working_directory else os.getcwd()

        # Determine effective reasoning effort: runtime > config > empty string
        effective_reasoning_effort = reasoning_effort or self.default_reasoning_effort or ""

        # Format arguments with {model}, {prompt}, {working_directory}, and {reasoning_effort} placeholders
        formatted_args = [
            arg.format(
                model=model,
                prompt=full_prompt,
                working_directory=cwd,
                reasoning_effort=effective_reasoning_effort,
            )
            for arg in args
        ]

        # Log the command being executed
        logger.info(
            f"Executing CLI adapter: command={self.command}, "
            f"model={model}, cwd={cwd}, "
            f"reasoning_effort={effective_reasoning_effort or '(none)'}, "
            f"prompt_length={len(full_prompt)} chars"
        )
        logger.debug(f"Full command: {self.command} {' '.join(formatted_args[:3])}... (args truncated)")

        # Execute with retry logic for transient errors
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                process = await asyncio.create_subprocess_exec(
                    self.command,
                    *formatted_args,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )

                if process.returncode != 0:
                    error_msg = stderr.decode("utf-8", errors="replace")

                    # Check if this is a transient error
                    is_transient = self._is_transient_error(error_msg)

                    if is_transient and attempt < self.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"Transient error detected (attempt {attempt + 1}/{self.max_retries + 1}): {error_msg[:100]}. "
                            f"Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        last_error = error_msg
                        continue

                    logger.error(
                        f"CLI process failed: command={self.command}, "
                        f"model={model}, returncode={process.returncode}, "
                        f"error={error_msg[:200]}"
                    )
                    raise RuntimeError(f"CLI process failed: {error_msg}")

                raw_output = stdout.decode("utf-8", errors="replace")
                if attempt > 0:
                    logger.info(
                        f"CLI adapter succeeded on retry attempt {attempt + 1}: "
                        f"command={self.command}, model={model}"
                    )
                logger.info(
                    f"CLI adapter completed successfully: command={self.command}, "
                    f"model={model}, output_length={len(raw_output)} chars"
                )
                logger.debug(f"Raw output preview: {raw_output[:500]}...")
                return self.parse_output(raw_output)

            except asyncio.TimeoutError:
                logger.error(
                    f"CLI invocation timed out: command={self.command}, "
                    f"model={model}, timeout={self.timeout}s"
                )
                raise TimeoutError(f"CLI invocation timed out after {self.timeout}s")

        # All retries exhausted
        raise RuntimeError(f"CLI failed after {self.max_retries + 1} attempts. Last error: {last_error}")

    def _is_transient_error(self, error_msg: str) -> bool:
        """
        Check if error message indicates a transient error worth retrying.

        Args:
            error_msg: Error message from stderr

        Returns:
            True if error is transient (503, 429, connection issues, etc.)
        """
        error_lower = error_msg.lower()
        return any(re.search(pattern, error_lower, re.IGNORECASE)
                   for pattern in self.TRANSIENT_ERROR_PATTERNS)

    def _adjust_args_for_context(self, is_deliberation: bool) -> list[str]:
        """
        Adjust CLI arguments based on context (deliberation vs regular Claude Code work).

        By default, returns args as-is. Subclasses can override for context-specific behavior.
        Example: Claude adapter adds -p flag for Claude Code work, removes it for deliberation.

        Args:
            is_deliberation: True if running as part of a multi-model deliberation

        Returns:
            Adjusted argument list
        """
        return self.args

    @abstractmethod
    def parse_output(self, raw_output: str) -> str:
        """
        Parse raw CLI output to extract model response.

        Must be implemented by subclasses based on their output format.

        Args:
            raw_output: Raw stdout from CLI tool

        Returns:
            Parsed model response text
        """
        pass
