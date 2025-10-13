"""CLI adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from models.config import CLIToolConfig


def create_adapter(cli: str, config: CLIToolConfig) -> BaseCLIAdapter:
    """
    Factory function to create appropriate CLI adapter.

    Args:
        cli: CLI tool name ('claude' or 'codex')
        config: CLI tool configuration object

    Returns:
        Appropriate adapter instance

    Raises:
        ValueError: If CLI tool is not supported
    """
    if cli == "claude":
        return ClaudeAdapter(
            command=config.command,
            args=config.args,
            timeout=config.timeout
        )
    elif cli == "codex":
        return CodexAdapter(
            command=config.command,
            args=config.args,
            timeout=config.timeout
        )
    else:
        raise ValueError(
            f"Unsupported CLI tool: '{cli}'. "
            f"Supported tools: 'claude', 'codex'"
        )


__all__ = ["BaseCLIAdapter", "ClaudeAdapter", "CodexAdapter", "create_adapter"]
