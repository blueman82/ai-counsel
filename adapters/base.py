"""Base CLI adapter with subprocess management."""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional


class BaseCLIAdapter(ABC):
    """
    Abstract base class for CLI tool adapters.

    Handles subprocess execution, timeout management, and error handling.
    Subclasses must implement parse_output() for tool-specific parsing.
    """

    def __init__(self, command: str, args: list[str], timeout: int = 60):
        """
        Initialize CLI adapter.

        Args:
            command: CLI command to execute
            args: List of argument templates (may contain {model}, {prompt} placeholders)
            timeout: Timeout in seconds (default: 60)
        """
        self.command = command
        self.args = args
        self.timeout = timeout

    async def invoke(self, prompt: str, model: str, context: Optional[str] = None) -> str:
        """
        Invoke the CLI tool with the given prompt and model.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context

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
        if hasattr(self, 'validate_prompt_length'):
            if not self.validate_prompt_length(full_prompt):
                raise ValueError(
                    f"Prompt too long ({len(full_prompt)} chars). "
                    f"Maximum allowed: {getattr(self, 'MAX_PROMPT_CHARS', 'unknown')} chars. "
                    "This prevents API rejection errors."
                )

        # Format arguments
        formatted_args = [
            arg.format(model=model, prompt=full_prompt)
            for arg in self.args
        ]

        # Execute subprocess
        try:
            # Set cwd to ensure local .claude settings are used if they exist
            from pathlib import Path
            cwd = Path(__file__).parent.parent.absolute()

            process = await asyncio.create_subprocess_exec(
                self.command,
                *formatted_args,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd)
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise RuntimeError(f"CLI process failed: {error_msg}")

            raw_output = stdout.decode('utf-8', errors='replace')
            return self.parse_output(raw_output)

        except asyncio.TimeoutError:
            raise TimeoutError(f"CLI invocation timed out after {self.timeout}s")

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
