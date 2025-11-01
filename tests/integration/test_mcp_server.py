"""Integration tests for MCP server.

These tests require the MCP server to be running and may require
real CLI tools (claude-code, codex) to be installed for full testing.

For MVP, these are placeholder tests to establish the structure.
Full implementation would use MCP test utilities or client libraries.
"""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_lists_tools():
    """
    Test that server lists the deliberate tool.

    This test requires the server to be running and would use
    MCP client libraries to connect and list available tools.

    For MVP, this is a placeholder. Manual testing can be done by:
    1. Starting server: python server.py
    2. Using MCP inspector or client to list tools
    3. Verifying 'deliberate' tool appears with correct schema
    """
    # TODO: Implement when MCP client test utilities are available
    # Expected: server.list_tools() returns Tool with name='deliberate'
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deliberate_tool_execution():
    """
    Test executing the deliberate tool end-to-end.

    This test requires:
    - Server running
    - Real CLI tools (claude-code, codex) installed and configured
    - Valid API keys set up

    For MVP, this is a placeholder. Manual testing can be done by:
    1. Starting server: python server.py
    2. Using MCP client to call deliberate tool with sample request
    3. Verifying DeliberationResult is returned with correct structure

    Note: This test would incur API costs when fully implemented.
    """
    # TODO: Implement when real CLI tools are configured
    # Sample request structure:
    # {
    #     "question": "What is 2+2?",
    #     "participants": [
    #         {"cli": "claude", "model": "claude-3-5-sonnet-20241022"},
    #         {"cli": "codex", "model": "gpt-4"}
    #     ],
    #     "rounds": 1,
    #     "mode": "quick"
    # }
    # Expected: Returns DeliberationResult with status='complete'
    pass


@pytest.mark.integration
class TestMCPToolSchema:
    """Tests for MCP tool schema documentation."""

    @pytest.mark.asyncio
    async def test_deliberate_tool_description_includes_tool_usage(self):
        """Test deliberate tool description documents tool invocation."""
        from server import list_tools

        tools = await list_tools()
        deliberate_tool = next(t for t in tools if t.name == "deliberate")

        description = deliberate_tool.description

        # Check for tool documentation
        assert "TOOL_REQUEST" in description
        assert "read_file" in description
        assert "search_code" in description
        assert "evidence" in description.lower() or "query" in description.lower()

    @pytest.mark.asyncio
    async def test_tool_list_includes_supported_tools(self):
        """Test tool description lists all supported tools."""
        from server import list_tools

        tools = await list_tools()
        deliberate_tool = next(t for t in tools if t.name == "deliberate")

        description = deliberate_tool.description

        # All Phase 1 tools should be mentioned
        assert "read_file" in description
        assert "search_code" in description
        assert "list_files" in description
        assert "run_command" in description
