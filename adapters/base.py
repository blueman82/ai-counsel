"""Base CLI adapter with subprocess management."""
import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Configure progress logger for CLI adapter activity tracking
progress_logger = logging.getLogger("ai_counsel.progress")
if not progress_logger.handlers:
    project_dir = Path(__file__).parent.parent
    progress_file = project_dir / "deliberation_progress.log"
    progress_handler = logging.FileHandler(
        progress_file, mode="a", encoding="utf-8"
    )
    progress_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))
    progress_logger.addHandler(progress_handler)
    progress_logger.setLevel(logging.DEBUG)


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
        activity_timeout: int = 120,
        max_retries: int = 2,
        default_reasoning_effort: Optional[str] = None,
    ):
        """
        Initialize CLI adapter.

        Args:
            command: CLI command to execute
            args: List of argument templates (may contain {model}, {prompt} placeholders)
            timeout: Maximum total execution time in seconds (default: 60).
                     This is the hard limit - process will be killed after this time.
            activity_timeout: Seconds without new output before considering process hung (default: 120).
                     If model is actively generating output, this timer resets on each chunk.
                     This allows long-running but active processes to complete.
            max_retries: Maximum retry attempts for transient errors (default: 2)
            default_reasoning_effort: Default reasoning effort level for this adapter.
                Only applicable to codex (low/medium/high/extra-high) and droid (off/low/medium/high).
                Ignored by other adapters. Can be overridden per-participant.
        """
        self.command = command
        self.args = args
        self.timeout = timeout
        self.activity_timeout = activity_timeout
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

                # Use activity-based timeout instead of fixed timeout
                stdout, stderr, timed_out = await self._read_with_activity_timeout(
                    process, model
                )

                if timed_out:
                    # Process was killed due to inactivity
                    raise asyncio.TimeoutError()

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

                    # Clean error for logging (first line only, truncated)
                    clean_error = error_msg.split('\n')[0][:150]
                    logger.error(
                        f"CLI process failed: command={self.command}, "
                        f"model={model}, returncode={process.returncode}, "
                        f"error={clean_error}"
                    )
                    raise RuntimeError(f"CLI process failed: {clean_error}")

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
                    f"model={model}, activity_timeout={self.activity_timeout}s"
                )
                raise TimeoutError(
                    f"CLI invocation timed out: no output for {self.activity_timeout}s "
                    f"(model may be hung or unresponsive)"
                )

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

    async def _read_with_activity_timeout(
        self,
        process: asyncio.subprocess.Process,
        model: str,
    ) -> tuple[bytes, bytes, bool]:
        """
        Read process output with activity-based timeout.

        Instead of a fixed total timeout, this monitors output activity.
        The timeout only triggers if no new output is received for `activity_timeout` seconds.
        This allows long-running but active processes to complete.

        Args:
            process: The subprocess to read from
            model: Model name (for logging)

        Returns:
            Tuple of (stdout_bytes, stderr_bytes, timed_out)
            timed_out is True if process was killed due to inactivity
        """
        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        last_activity = time.time()
        start_time = time.time()
        total_bytes = 0
        last_log_time = start_time

        progress_logger.info(
            f"[CLI_START] {model} | Starting process | "
            f"activity_timeout={self.activity_timeout}s, max_timeout={self.timeout}s"
        )

        async def read_stream(stream, chunks: list[bytes], name: str):
            """Read from a stream and track activity."""
            nonlocal last_activity, total_bytes, last_log_time
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        stream.read(4096),
                        timeout=1.0  # Check every second
                    )
                    if not chunk:
                        break  # EOF
                    chunks.append(chunk)
                    last_activity = time.time()
                    total_bytes += len(chunk)

                    # Log progress every 10 seconds
                    now = time.time()
                    if now - last_log_time >= 10:
                        elapsed = now - start_time
                        progress_logger.info(
                            f"[CLI_PROGRESS] {model} | "
                            f"elapsed={elapsed:.1f}s | "
                            f"bytes={total_bytes} | "
                            f"stream={name} | "
                            f"last_chunk={len(chunk)}b"
                        )
                        last_log_time = now

                except asyncio.TimeoutError:
                    # No data this second, but check if we should continue
                    pass

        # Start reading both streams concurrently
        stdout_task = asyncio.create_task(
            read_stream(process.stdout, stdout_chunks, "stdout")
        )
        stderr_task = asyncio.create_task(
            read_stream(process.stderr, stderr_chunks, "stderr")
        )

        timed_out = False
        try:
            while not stdout_task.done() or not stderr_task.done():
                await asyncio.sleep(0.5)

                now = time.time()
                elapsed = now - start_time
                inactive_time = now - last_activity

                # Check activity timeout (no output for too long)
                if inactive_time > self.activity_timeout:
                    progress_logger.warning(
                        f"[CLI_TIMEOUT] {model} | "
                        f"No activity for {inactive_time:.1f}s | "
                        f"Killing process"
                    )
                    timed_out = True
                    break

                # Check hard timeout (total time exceeded)
                if elapsed > self.timeout:
                    progress_logger.warning(
                        f"[CLI_TIMEOUT] {model} | "
                        f"Hard timeout after {elapsed:.1f}s | "
                        f"Killing process"
                    )
                    timed_out = True
                    break

        finally:
            if timed_out:
                # Kill the process
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

            # Cancel any remaining tasks
            stdout_task.cancel()
            stderr_task.cancel()
            try:
                await stdout_task
            except (asyncio.CancelledError, Exception):
                pass
            try:
                await stderr_task
            except (asyncio.CancelledError, Exception):
                pass

        # Wait for process to finish (if not killed)
        if not timed_out:
            await process.wait()

        elapsed = time.time() - start_time
        progress_logger.info(
            f"[CLI_DONE] {model} | "
            f"elapsed={elapsed:.1f}s | "
            f"bytes={total_bytes} | "
            f"returncode={process.returncode} | "
            f"timed_out={timed_out}"
        )

        return b"".join(stdout_chunks), b"".join(stderr_chunks), timed_out

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
