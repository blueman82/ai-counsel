"""CLI adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.claude_code import ClaudeCodeAdapter
from adapters.codex import CodexAdapter
from models.config import CLIToolConfig


def create_adapter(cli: str, config: CLIToolConfig) -> BaseCLIAdapter:
    """
    Factory function to create appropriate CLI adapter.

    Args:
        cli: CLI tool name ('claude-code' or 'codex')
        config: CLI tool configuration object

    Returns:
        Appropriate adapter instance

    Raises:
        ValueError: If CLI tool is not supported
    """
    if cli == "claude-code":
        return ClaudeCodeAdapter(timeout=config.timeout)
    elif cli == "codex":
        return CodexAdapter(timeout=config.timeout)
    else:
        raise ValueError(
            f"Unsupported CLI tool: '{cli}'. "
            f"Supported tools: 'claude-code', 'codex'"
        )


__all__ = ["BaseCLIAdapter", "ClaudeCodeAdapter", "CodexAdapter", "create_adapter"]
