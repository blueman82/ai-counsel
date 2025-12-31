"""CLI and HTTP adapter factory and exports."""
import logging
import shutil
from typing import Optional, Type, Union

from adapters.base import BaseCLIAdapter
from adapters.base_http import BaseHTTPAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters.droid import DroidAdapter
from adapters.gemini import GeminiAdapter
from adapters.llamacpp import LlamaCppAdapter
from adapters.lmstudio import LMStudioAdapter
from adapters.ollama import OllamaAdapter
from adapters.openai import OpenAIAdapter
from adapters.openrouter import NebiusAdapter, OpenRouterAdapter
from models.config import CLIAdapterConfig, CLIToolConfig, HTTPAdapterConfig, OpenAIAdapterConfig

logger = logging.getLogger(__name__)

# Cache for CLI availability checks (command -> is_available)
_cli_availability_cache: dict[str, bool] = {}


def is_cli_available(command: str) -> bool:
    """
    Check if a CLI command is available on the system.

    Uses shutil.which() to check if the command exists in PATH.
    Results are cached for performance.

    Args:
        command: The CLI command to check (e.g., 'claude', 'codex')

    Returns:
        True if command is available, False otherwise
    """
    if command in _cli_availability_cache:
        return _cli_availability_cache[command]

    is_available = shutil.which(command) is not None
    _cli_availability_cache[command] = is_available

    if not is_available:
        logger.info(f"CLI '{command}' not found in PATH")
    else:
        logger.debug(f"CLI '{command}' found: {shutil.which(command)}")

    return is_available


def clear_cli_cache() -> None:
    """Clear the CLI availability cache. Useful for testing."""
    _cli_availability_cache.clear()


# Mapping from CLI adapter names to their OpenRouter model equivalents.
# These are used as fallbacks when the CLI tool is not installed.
# Format: cli_name -> default OpenRouter model ID
CLI_TO_OPENROUTER_FALLBACK: dict[str, str] = {
    "claude": "anthropic/claude-sonnet-4",
    "codex": "openai/gpt-4o",
    "droid": "anthropic/claude-3.5-sonnet",
    "gemini": "google/gemini-2.0-flash-001",
    # llamacpp is local-only, no sensible fallback
}


def get_openrouter_fallback_config(
    cli_name: str,
    original_timeout: int = 30,
) -> Optional[HTTPAdapterConfig]:
    """
    Get OpenRouter HTTP adapter config as fallback for an unavailable CLI.

    Args:
        cli_name: Name of the CLI adapter that's not available
        original_timeout: Timeout from original config to preserve

    Returns:
        HTTPAdapterConfig for OpenRouter if fallback exists, None otherwise
    """
    import os

    if cli_name not in CLI_TO_OPENROUTER_FALLBACK:
        logger.warning(
            f"No OpenRouter fallback available for CLI '{cli_name}'"
        )
        return None

    # Check if OpenRouter API key is available
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning(
            f"Cannot use OpenRouter fallback for '{cli_name}': "
            "OPENROUTER_API_KEY environment variable not set"
        )
        return None

    return HTTPAdapterConfig(
        type="http",
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=original_timeout,
        max_retries=2,
    )


def create_adapter(
    name: str, config: Union[CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig]
) -> Union[BaseCLIAdapter, BaseHTTPAdapter]:
    """
    Factory function to create appropriate adapter (CLI or HTTP).

    Args:
        name: Adapter name (e.g., 'claude', 'ollama')
        config: Adapter configuration (CLI or HTTP)

    Returns:
        Appropriate adapter instance (CLI or HTTP)

    Raises:
        ValueError: If adapter is not supported
        TypeError: If config type doesn't match adapter type
    """
    # Registry of CLI adapters
    cli_adapters: dict[str, Type[BaseCLIAdapter]] = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "droid": DroidAdapter,
        "gemini": GeminiAdapter,
        "llamacpp": LlamaCppAdapter,
    }

    # Registry of HTTP adapters
    http_adapters: dict[str, Type[BaseHTTPAdapter]] = {
        "ollama": OllamaAdapter,
        "lmstudio": LMStudioAdapter,
        "openrouter": OpenRouterAdapter,
        "nebius": NebiusAdapter,
        "openai": OpenAIAdapter,
    }

    # Handle legacy CLIToolConfig (backward compatibility)
    if isinstance(config, CLIToolConfig):
        if name in cli_adapters:
            return cli_adapters[name](
                command=config.command,
                args=config.args,
                timeout=config.timeout,
                default_reasoning_effort=getattr(config, "default_reasoning_effort", None),
            )
        else:
            raise ValueError(
                f"Unsupported CLI tool: '{name}'. "
                f"Supported tools: {', '.join(cli_adapters.keys())}"
            )

    # Handle new typed configs
    if isinstance(config, CLIAdapterConfig):
        if name not in cli_adapters:
            raise ValueError(
                f"Unknown CLI adapter: '{name}'. "
                f"Supported CLI adapters: {', '.join(cli_adapters.keys())}"
            )

        return cli_adapters[name](
            command=config.command,
            args=config.args,
            timeout=config.timeout,
            default_reasoning_effort=config.default_reasoning_effort,
        )

    elif isinstance(config, HTTPAdapterConfig):
        if name not in http_adapters:
            raise ValueError(
                f"Unknown HTTP adapter: '{name}'. "
                f"Supported HTTP adapters: {', '.join(http_adapters.keys())} "
                f"(Note: HTTP adapters are being added in phases)"
            )

        # Special handling for OpenAI adapter with extended config
        if name == "openai" and isinstance(config, OpenAIAdapterConfig):
            return OpenAIAdapter(
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries,
                api_key=config.api_key,
                headers=config.headers,
                responses_api_prefixes=config.responses_api_prefixes,
                max_output_tokens=config.max_output_tokens,
                max_completion_tokens=config.max_completion_tokens,
            )

        return http_adapters[name](
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            api_key=config.api_key,
            headers=config.headers,
        )

    else:
        raise TypeError(
            f"Invalid config type: {type(config)}. "
            f"Expected CLIToolConfig, CLIAdapterConfig, or HTTPAdapterConfig"
        )


def create_adapter_with_fallback(
    name: str,
    config: Union[CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig],
    check_cli_availability: bool = True,
) -> tuple[Union[BaseCLIAdapter, BaseHTTPAdapter], Optional[str]]:
    """
    Create adapter with automatic fallback to OpenRouter when CLI is unavailable.

    This function checks if CLI tools are installed before creating CLI adapters.
    If a CLI tool is not found, it automatically falls back to OpenRouter using
    an equivalent model.

    Args:
        name: Adapter name (e.g., 'claude', 'codex')
        config: Adapter configuration
        check_cli_availability: Whether to check CLI availability (default: True).
            Set to False to skip availability check.

    Returns:
        Tuple of (adapter, fallback_model) where:
        - adapter: The created adapter instance
        - fallback_model: OpenRouter model ID if fallback was used, None otherwise

    Raises:
        ValueError: If adapter is not supported and no fallback is available
        RuntimeError: If fallback is needed but OPENROUTER_API_KEY is not set

    Example:
        adapter, fallback = create_adapter_with_fallback("claude", config)
        if fallback:
            print(f"Using OpenRouter fallback: {fallback}")
    """
    # HTTP adapters don't need fallback checking
    if isinstance(config, HTTPAdapterConfig):
        return create_adapter(name, config), None

    # For CLI configs, check if the CLI tool is available
    if check_cli_availability and isinstance(config, (CLIToolConfig, CLIAdapterConfig)):
        command = config.command
        if not is_cli_available(command):
            logger.warning(
                f"CLI '{command}' (adapter: {name}) not installed, "
                f"attempting OpenRouter fallback"
            )

            # Try to get OpenRouter fallback config
            fallback_config = get_openrouter_fallback_config(
                name, original_timeout=config.timeout
            )

            if fallback_config is None:
                raise RuntimeError(
                    f"CLI '{command}' not installed and no fallback available. "
                    f"Install the CLI tool or set OPENROUTER_API_KEY for fallback."
                )

            # Get the fallback model ID
            fallback_model = CLI_TO_OPENROUTER_FALLBACK[name]

            logger.info(
                f"Using OpenRouter fallback for '{name}': {fallback_model}"
            )

            # Create OpenRouter adapter with fallback
            adapter = OpenRouterAdapter(
                base_url=fallback_config.base_url,
                timeout=fallback_config.timeout,
                max_retries=fallback_config.max_retries,
                api_key=fallback_config.api_key,
            )
            return adapter, fallback_model

    # CLI is available or check is disabled, create normally
    return create_adapter(name, config), None


def get_cli_status() -> dict[str, dict[str, Union[bool, Optional[str]]]]:
    """
    Get availability status for all known CLI tools.

    Returns:
        Dictionary mapping CLI names to their status:
        {
            "claude": {"available": True, "path": "/usr/local/bin/claude"},
            "codex": {"available": False, "path": None, "fallback": "openai/gpt-4o"},
            ...
        }
    """
    cli_commands = {
        "claude": "claude",
        "codex": "codex",
        "droid": "droid",
        "gemini": "gemini",
        "llamacpp": "llama-cli",  # Common llama.cpp binary name
    }

    status = {}
    for name, command in cli_commands.items():
        path = shutil.which(command)
        status[name] = {
            "available": path is not None,
            "path": path,
            "fallback": CLI_TO_OPENROUTER_FALLBACK.get(name),
        }

    return status


__all__ = [
    "BaseCLIAdapter",
    "BaseHTTPAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "DroidAdapter",
    "GeminiAdapter",
    "LlamaCppAdapter",
    "LMStudioAdapter",
    "NebiusAdapter",
    "OllamaAdapter",
    "OpenAIAdapter",
    "OpenRouterAdapter",
    "create_adapter",
    "create_adapter_with_fallback",
    "is_cli_available",
    "clear_cli_cache",
    "get_cli_status",
    "get_openrouter_fallback_config",
    "CLI_TO_OPENROUTER_FALLBACK",
]
