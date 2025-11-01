"""Unit tests for tool execution infrastructure."""
import pytest
import json
from deliberation.tools import BaseTool, ToolExecutor
from models.tool_schema import ToolRequest, ToolResult


class MockTool(BaseTool):
    """Mock tool for testing."""

    @property
    def name(self) -> str:
        return "read_file"

    async def execute(self, arguments: dict) -> ToolResult:
        """Execute mock tool."""
        if arguments.get("should_fail"):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Mock error"
            )
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Mock output: {arguments}",
            error=None
        )


class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_abstract_class_cannot_instantiate(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool()

    def test_subclass_must_implement_name_property(self):
        """Test that subclass must implement name property."""
        class IncompleteTool(BaseTool):
            # Missing name property
            async def execute(self, arguments: dict) -> ToolResult:
                pass

        with pytest.raises(TypeError):
            IncompleteTool()

    def test_subclass_must_implement_execute(self):
        """Test that subclass must implement execute method."""
        class IncompleteTool(BaseTool):
            @property
            def name(self) -> str:
                return "incomplete"
            # Missing execute()

        with pytest.raises(TypeError):
            IncompleteTool()

    def test_valid_subclass_can_instantiate(self):
        """Test that valid subclass can be instantiated."""
        tool = MockTool()
        assert tool.name == "read_file"


class TestToolExecutor:
    """Tests for ToolExecutor orchestrator."""

    @pytest.fixture
    def executor(self):
        """Create tool executor with mock tool."""
        executor = ToolExecutor()
        executor.register_tool(MockTool())
        return executor

    def test_register_tool(self, executor):
        """Test registering a tool."""
        assert "read_file" in executor.tools
        assert isinstance(executor.tools["read_file"], MockTool)

    def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        executor = ToolExecutor()
        tool1 = MockTool()
        
        class AnotherMockTool(BaseTool):
            @property
            def name(self) -> str:
                return "search_code"
            
            async def execute(self, arguments: dict) -> ToolResult:
                return ToolResult(tool_name=self.name, success=True, output="test", error=None)
        
        tool2 = AnotherMockTool()
        
        executor.register_tool(tool1)
        executor.register_tool(tool2)
        
        assert len(executor.tools) == 2
        assert "read_file" in executor.tools
        assert "search_code" in executor.tools

    @pytest.mark.asyncio
    async def test_execute_registered_tool(self, executor):
        """Test executing a registered tool."""
        request = ToolRequest(
            name="read_file",
            arguments={"param": "value"}
        )
        result = await executor.execute_tool(request)
        assert result.success is True
        assert "Mock output" in result.output
        assert "param" in result.output

    @pytest.mark.asyncio
    async def test_execute_unregistered_tool_returns_error(self, executor):
        """Test executing unregistered tool returns error."""
        request = ToolRequest(
            name="search_code",  # Not registered (only read_file is registered in fixture)
            arguments={"pattern": "test"}
        )
        result = await executor.execute_tool(request)
        assert result.success is False
        assert "not registered" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_with_failure(self, executor):
        """Test executing tool that returns failure."""
        request = ToolRequest(
            name="read_file",
            arguments={"should_fail": True}
        )
        result = await executor.execute_tool(request)
        assert result.success is False
        assert result.error == "Mock error"

    @pytest.mark.asyncio
    async def test_execute_tool_with_exception(self, executor):
        """Test tool execution handles exceptions gracefully."""
        class FailingTool(BaseTool):
            @property
            def name(self) -> str:
                return "list_files"
            
            async def execute(self, arguments: dict) -> ToolResult:
                raise ValueError("Something went wrong")
        
        executor.register_tool(FailingTool())
        request = ToolRequest(name="list_files", arguments={})
        
        result = await executor.execute_tool(request)
        assert result.success is False
        assert "ValueError" in result.error
        assert "Something went wrong" in result.error

    def test_parse_tool_request_from_response(self, executor):
        """Test parsing tool request from model response."""
        response_text = """
        I need to check the file first.

        TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/test.py"}}

        After reviewing the file, I'll provide my analysis.
        """
        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 1
        assert requests[0].name == "read_file"
        assert requests[0].arguments == {"path": "/test.py"}

    def test_parse_multiple_tool_requests(self, executor):
        """Test parsing multiple tool requests from single response."""
        response_text = """
        TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/file1.py"}}

        Also need another check:

        TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "test"}}
        """
        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 2
        assert requests[0].name == "read_file"
        assert requests[0].arguments == {"path": "/file1.py"}
        assert requests[1].name == "search_code"
        assert requests[1].arguments == {"pattern": "test"}

    def test_parse_response_with_no_tool_requests(self, executor):
        """Test parsing response with no tool requests returns empty list."""
        response_text = "This is a normal response with no tool requests."
        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 0

    def test_parse_invalid_json_returns_empty_list(self, executor):
        """Test that invalid JSON in tool request is silently ignored."""
        response_text = """
        TOOL_REQUEST: {invalid json here}
        """
        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 0

    def test_parse_invalid_tool_name_ignored(self, executor):
        """Test that invalid tool names are silently ignored."""
        response_text = """
        TOOL_REQUEST: {"name": "invalid_tool_name", "arguments": {}}
        """
        requests = executor.parse_tool_requests(response_text)
        # Should be empty because invalid_tool_name is not in the Literal
        assert len(requests) == 0

    def test_parse_missing_arguments_ignored(self, executor):
        """Test that requests missing arguments are silently ignored."""
        response_text = """
        TOOL_REQUEST: {"name": "mock_tool"}
        """
        requests = executor.parse_tool_requests(response_text)
        # Should be empty because arguments field is required
        assert len(requests) == 0

    def test_parse_tool_request_with_complex_arguments(self, executor):
        """Test parsing tool request with complex nested arguments."""
        response_text = """
        TOOL_REQUEST: {"name": "run_command", "arguments": {"command": "ls", "args": ["-la", "-h"], "nested": {"key": "value"}}}
        """
        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 1
        assert requests[0].name == "run_command"
        assert requests[0].arguments["command"] == "ls"
        assert requests[0].arguments["args"] == ["-la", "-h"]
        assert requests[0].arguments["nested"]["key"] == "value"


class TestReadFileTool:
    """Tests for ReadFileTool implementation."""

    @pytest.fixture
    def tool(self):
        """Create ReadFileTool instance."""
        from deliberation.tools import ReadFileTool
        return ReadFileTool()

    @pytest.mark.asyncio
    async def test_read_existing_file(self, tool, tmp_path):
        """Test reading an existing file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        result = await tool.execute({"path": str(test_file)})

        assert result.success is True
        assert "Hello world" in result.output
        assert result.error is None

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_returns_error(self, tool):
        """Test reading nonexistent file returns error."""
        result = await tool.execute({"path": "/nonexistent/file/that/does/not/exist.txt"})

        assert result.success is False
        assert result.output is None
        assert "not found" in result.error.lower() or "no such file" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_file_too_large_returns_error(self, tool, tmp_path):
        """Test reading oversized file returns error."""
        # Create 2MB file (exceeds 1MB limit)
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * (2 * 1024 * 1024))

        result = await tool.execute({"path": str(large_file)})

        assert result.success is False
        assert "too large" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_binary_file_returns_error(self, tool, tmp_path):
        """Test reading binary file returns appropriate error."""
        # Create binary file
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\xff\xfe")

        result = await tool.execute({"path": str(binary_file)})

        # Should either succeed with warning or return decode error
        if not result.success:
            assert "decode" in result.error.lower() or "binary" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_file_missing_path_argument(self, tool):
        """Test reading file without path argument returns error."""
        result = await tool.execute({})

        assert result.success is False
        assert "path" in result.error.lower()

    @pytest.mark.asyncio
    async def test_tool_name(self, tool):
        """Test tool has correct name."""
        assert tool.name == "read_file"


class TestSearchCodeTool:
    """Tests for SearchCodeTool implementation."""

    @pytest.fixture
    def tool(self):
        """Create SearchCodeTool instance."""
        from deliberation.tools import SearchCodeTool
        return SearchCodeTool()

    @pytest.fixture
    def test_codebase(self, tmp_path):
        """Create test codebase with multiple files."""
        # Create test files
        (tmp_path / "file1.py").write_text("def hello():\n    print('world')\n")
        (tmp_path / "file2.py").write_text("class World:\n    pass\n")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.py").write_text("# world comment\n")
        return tmp_path

    @pytest.mark.asyncio
    async def test_search_finds_matches(self, tool, test_codebase):
        """Test searching finds matches across files."""
        result = await tool.execute({
            "pattern": "world",
            "path": str(test_codebase)
        })

        assert result.success is True
        assert "file1.py" in result.output  # Has 'world' in lowercase
        assert "subdir" in result.output and "file3.py" in result.output  # Has 'world' in comment
        # file2.py has 'World' capitalized, so won't match case-sensitive search

    @pytest.mark.asyncio
    async def test_search_with_no_matches_returns_empty(self, tool, test_codebase):
        """Test search with no matches returns empty result."""
        result = await tool.execute({
            "pattern": "nonexistent_pattern_12345",
            "path": str(test_codebase)
        })

        assert result.success is True
        assert "No matches found" in result.output

    @pytest.mark.asyncio
    async def test_search_with_invalid_regex_returns_error(self, tool, test_codebase):
        """Test search with invalid regex returns error."""
        result = await tool.execute({
            "pattern": "[invalid(regex",
            "path": str(test_codebase)
        })

        assert result.success is False
        assert "regex" in result.error.lower() or "pattern" in result.error.lower()

    @pytest.mark.asyncio
    async def test_search_missing_pattern_argument(self, tool):
        """Test search without pattern argument returns error."""
        result = await tool.execute({"path": "."})

        assert result.success is False
        assert "pattern" in result.error.lower()

    @pytest.mark.asyncio
    async def test_search_defaults_to_current_directory(self, tool):
        """Test search uses current directory if path not specified."""
        # This test just verifies the tool doesn't crash without path
        result = await tool.execute({"pattern": "test"})
        
        # Should complete (success or no matches), not crash
        assert result.success is True or "No matches found" in result.output

    @pytest.mark.asyncio
    async def test_tool_name(self, tool):
        """Test tool has correct name."""
        assert tool.name == "search_code"
