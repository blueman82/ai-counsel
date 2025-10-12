"""CLI adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.claude_code import ClaudeCodeAdapter
from adapters.codex import CodexAdapter


def create_adapter(cli: str, timeout: int = 60) -> BaseCLIAdapter:
    """
    Factory function to create appropriate CLI adapter.

    Args:
        cli: CLI tool name ('claude-code' or 'codex')
        timeout: Timeout in seconds (default: 60)

    Returns:
        Appropriate adapter instance

    Raises:
        ValueError: If CLI tool is not supported
    """
    if cli == "claude-code":
        return ClaudeCodeAdapter(timeout=timeout)
    elif cli == "codex":
        return CodexAdapter(timeout=timeout)
    else:
        raise ValueError(
            f"Unsupported CLI tool: '{cli}'. "
            f"Supported tools: 'claude-code', 'codex'"
        )


__all__ = ["BaseCLIAdapter", "ClaudeCodeAdapter", "CodexAdapter", "create_adapter"]
