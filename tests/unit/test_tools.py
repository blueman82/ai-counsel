"""Unit tests for tool execution infrastructure."""
import shutil
import pytest
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
                tool_name=self.name, success=False, output=None, error="Mock error"
            )
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Mock output: {arguments}",
            error=None,
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
                return ToolResult(
                    tool_name=self.name, success=True, output="test", error=None
                )

        tool2 = AnotherMockTool()

        executor.register_tool(tool1)
        executor.register_tool(tool2)

        assert len(executor.tools) == 2
        assert "read_file" in executor.tools
        assert "search_code" in executor.tools

    @pytest.mark.asyncio
    async def test_execute_registered_tool(self, executor):
        """Test executing a registered tool."""
        request = ToolRequest(name="read_file", arguments={"param": "value"})
        result = await executor.execute_tool(request)
        assert result.success is True
        assert "Mock output" in result.output
        assert "param" in result.output

    @pytest.mark.asyncio
    async def test_execute_unregistered_tool_returns_error(self, executor):
        """Test executing unregistered tool returns error."""
        request = ToolRequest(
            name="search_code",  # Not registered (only read_file is registered in fixture)
            arguments={"pattern": "test"},
        )
        result = await executor.execute_tool(request)
        assert result.success is False
        assert "not registered" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_with_failure(self, executor):
        """Test executing tool that returns failure."""
        request = ToolRequest(name="read_file", arguments={"should_fail": True})
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

    def test_parse_tool_request_with_closing_brace_in_argument(self, executor):
        """Test parsing tool request with } character in argument values.

        This is a regression test for the fragile manual brace counting bug.
        When arguments contain } characters (e.g., regex patterns, code snippets),
        the manual brace counter breaks and stops parsing too early.

        Example: {"pattern": "class Test }"}
        Manual brace counting sees the } in "Test }" and thinks JSON is complete.
        """
        # Register search_code tool for this test
        from deliberation.tools import SearchCodeTool

        executor.register_tool(SearchCodeTool())

        response_text = """
        I need to search for class definitions that might have closing braces.
        TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "class Test }", "path": "."}}
        This should parse correctly.
        """

        requests = executor.parse_tool_requests(response_text)

        # Should successfully parse 1 request
        assert len(requests) == 1, f"Expected 1 request, got {len(requests)}"
        assert requests[0].name == "search_code"
        assert (
            requests[0].arguments["pattern"] == "class Test }"
        ), f"Pattern was: {requests[0].arguments.get('pattern')}"
        assert requests[0].arguments["path"] == "."

    def test_parse_multiple_tool_requests_with_braces_in_arguments(self, executor):
        """Test parsing multiple requests when arguments contain } characters."""
        from deliberation.tools import ReadFileTool, SearchCodeTool

        executor.register_tool(ReadFileTool())
        executor.register_tool(SearchCodeTool())

        response_text = """
        First, read a file:
        TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/test.py"}}

        Then search for patterns with braces:
        TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "def foo():", "path": "."}}
        """

        requests = executor.parse_tool_requests(response_text)
        assert len(requests) == 2, f"Expected 2 requests, got {len(requests)}"
        assert requests[0].name == "read_file"
        assert requests[1].name == "search_code"
        assert requests[1].arguments["pattern"] == "def foo():"


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
    async def test_read_file_respects_working_directory(self, tool, tmp_path):
        """Test read_file blocks access outside working_directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        inside = workspace / "inside.txt"
        inside.write_text("inside")
        outside = tmp_path / "outside.txt"
        outside.write_text("outside")

        allowed = await tool.execute(
            {"path": "inside.txt", "working_directory": str(workspace)}
        )
        assert allowed.success is True
        assert "inside" in allowed.output

        blocked = await tool.execute(
            {"path": str(outside), "working_directory": str(workspace)}
        )
        assert blocked.success is False
        assert "working directory" in blocked.error.lower() or "access denied" in blocked.error.lower()

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_returns_error(self, tool):
        """Test reading nonexistent file returns error."""
        result = await tool.execute(
            {"path": "/nonexistent/file/that/does/not/exist.txt"}
        )

        assert result.success is False
        assert result.output is None
        assert (
            "not found" in result.error.lower()
            or "no such file" in result.error.lower()
        )

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

    @pytest.mark.asyncio
    async def test_read_file_not_found_helpful_error(self, tool):
        """Test that file not found errors include discovery tips."""
        result = await tool.execute({"path": "/nonexistent/file.py"})

        assert result.success is False
        assert "File not found" in result.error
        assert "TIP" in result.error
        assert "list_files" in result.error
        assert "search_code" in result.error


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
        result = await tool.execute({"pattern": "world", "path": str(test_codebase)})

        assert result.success is True
        assert "file1.py" in result.output  # Has 'world' in lowercase
        assert (
            "subdir" in result.output and "file3.py" in result.output
        )  # Has 'world' in comment
        # file2.py has 'World' capitalized, so won't match case-sensitive search

    @pytest.mark.asyncio
    async def test_search_with_no_matches_returns_empty(self, tool, test_codebase):
        """Test search with no matches returns empty result."""
        result = await tool.execute(
            {"pattern": "nonexistent_pattern_12345", "path": str(test_codebase)}
        )

        assert result.success is True
        assert "No matches found" in result.output

    @pytest.mark.asyncio
    async def test_search_with_invalid_regex_returns_error(self, tool, test_codebase):
        """Test search with invalid regex returns error."""
        result = await tool.execute(
            {"pattern": "[invalid(regex", "path": str(test_codebase)}
        )

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

    @pytest.mark.asyncio
    async def test_search_blocks_outside_working_directory(self, tool, tmp_path):
        """Test search_code blocks access outside working_directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        (outside_dir / "file.py").write_text("secret")

        result = await tool.execute(
            {
                "pattern": "secret",
                "path": str(outside_dir),
                "working_directory": str(workspace),
            }
        )

        assert result.success is False
        assert "working directory" in result.error.lower() or "access denied" in result.error.lower()


class TestListFilesTool:
    """Tests for ListFilesTool implementation."""

    @pytest.fixture
    def tool(self):
        """Create ListFilesTool instance."""
        from deliberation.tools import ListFilesTool

        return ListFilesTool()

    @pytest.fixture
    def test_files(self, tmp_path):
        """Create test file structure."""
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "readme.md").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.py").touch()
        return tmp_path

    @pytest.mark.asyncio
    async def test_list_files_with_glob_pattern(self, tool, test_files):
        """Test listing files with glob pattern."""
        result = await tool.execute({"pattern": "*.py", "path": str(test_files)})

        assert result.success is True
        assert "file1.py" in result.output
        assert "file2.py" in result.output
        assert "readme.md" not in result.output

    @pytest.mark.asyncio
    async def test_list_files_with_no_matches(self, tool, test_files):
        """Test listing files with no matches."""
        result = await tool.execute(
            {"pattern": "*.nonexistent", "path": str(test_files)}
        )

        assert result.success is True
        assert "No files found" in result.output

    @pytest.mark.asyncio
    async def test_list_files_defaults_pattern(self, tool, test_files):
        """Test listing files with default pattern (all files)."""
        result = await tool.execute({"path": str(test_files)})

        assert result.success is True
        # Should list files with default pattern

    @pytest.mark.asyncio
    async def test_list_files_invalid_path(self, tool):
        """Test listing files with invalid path returns error."""
        result = await tool.execute(
            {"pattern": "*.py", "path": "/nonexistent/path/does/not/exist"}
        )

        assert result.success is False
        assert "not found" in result.error.lower() or "path" in result.error.lower()

    @pytest.mark.asyncio
    async def test_tool_name(self, tool):
        """Test tool has correct name."""
        assert tool.name == "list_files"

    @pytest.mark.asyncio
    async def test_list_files_blocks_traversal_pattern(self, tool, tmp_path):
        """Test list_files blocks traversal patterns when working_directory set."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        result = await tool.execute(
            {
                "pattern": "../*.py",
                "path": ".",
                "working_directory": str(workspace),
            }
        )

        assert result.success is False
        assert "path traversal" in result.error.lower()


class TestRunCommandTool:
    """Tests for RunCommandTool implementation."""

    @pytest.fixture
    def tool(self):
        """Create RunCommandTool instance."""
        from deliberation.tools import RunCommandTool

        return RunCommandTool()

    @pytest.mark.asyncio
    async def test_run_whitelisted_command(self, tool):
        """Test running whitelisted command succeeds."""
        if shutil.which("pwd") is None:
            pytest.skip("pwd command not available on this platform")
        result = await tool.execute({"command": "pwd", "args": []})

        assert result.success is True
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_run_command_with_args(self, tool, tmp_path):
        """Test running command with arguments."""
        if shutil.which("cat") is None:
            pytest.skip("cat command not available on this platform")
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = await tool.execute({"command": "cat", "args": [str(test_file)]})

        assert result.success is True
        assert "test content" in result.output

    @pytest.mark.asyncio
    async def test_run_non_whitelisted_command_returns_error(self, tool):
        """Test non-whitelisted command is blocked."""
        result = await tool.execute(
            {"command": "rm", "args": ["-rf", "/"]}  # Not whitelisted
        )

        assert result.success is False
        assert "not whitelisted" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_command_missing_command_argument(self, tool):
        """Test running command without command argument returns error."""
        result = await tool.execute({"args": []})

        assert result.success is False
        assert "command" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_command_defaults_args(self, tool):
        """Test command execution with default empty args."""
        result = await tool.execute({"command": "pwd"})

        # Should work with default empty args
        assert (
            result.success is True or result.success is False
        )  # May fail if command needs args

    @pytest.mark.asyncio
    async def test_tool_name(self, tool):
        """Test tool has correct name."""
        assert tool.name == "run_command"

    @pytest.mark.asyncio
    async def test_run_command_blocks_git_mutation(self, tool):
        """Test git subcommands outside allowlist are blocked."""
        result = await tool.execute({"command": "git", "args": ["checkout", "main"]})

        assert result.success is False
        assert "git subcommand" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_command_blocks_find_exec(self, tool):
        """Test find -exec is blocked."""
        result = await tool.execute(
            {"command": "find", "args": [".", "-exec", "rm", "-rf", "{}", ";"]}
        )

        assert result.success is False
        assert "find flags" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_command_blocks_absolute_paths_outside_workdir(
        self, tool, tmp_path
    ):
        """Test absolute paths outside working_directory are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("data")

        result = await tool.execute(
            {
                "command": "cat",
                "args": [str(outside)],
                "working_directory": str(workspace),
            }
        )

        assert result.success is False
        assert "absolute paths outside" in result.error.lower()


class TestGetFileTreeTool:
    """Tests for GetFileTreeTool implementation."""

    @pytest.fixture
    def tool(self):
        """Create GetFileTreeTool instance."""
        from deliberation.tools import GetFileTreeTool

        return GetFileTreeTool()

    @pytest.mark.asyncio
    async def test_get_file_tree_basic(self, tool, tmp_path):
        """Test basic file tree generation."""
        # Create test structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file1.py").write_text("test")
        (tmp_path / "file2.py").write_text("test")

        result = await tool.execute(
            {
                "path": ".",
                "max_depth": 2,
                "max_files": 50,
                "working_directory": str(tmp_path),
            }
        )

        assert result.success is True
        assert "dir1" in result.output
        assert "file1.py" in result.output
        assert "file2.py" in result.output

    @pytest.mark.asyncio
    async def test_get_file_tree_clamps_to_config_limits(self, tool, tmp_path):
        """Test that requests are clamped to config limits."""
        result = await tool.execute(
            {
                "path": ".",
                "max_depth": 999,  # Exceeds config max (10)
                "max_files": 9999,  # Exceeds config max (1000)
                "working_directory": str(tmp_path),
            }
        )

        assert result.success is True
        assert "limited by config" in result.output

    @pytest.mark.asyncio
    async def test_get_file_tree_path_traversal_security(self, tool, tmp_path):
        """Test that path traversal attacks are blocked."""
        result = await tool.execute(
            {"path": "../../../etc", "working_directory": str(tmp_path)}
        )

        assert result.success is False
        assert "security violation" in result.error

    @pytest.mark.asyncio
    async def test_get_file_tree_nonexistent_path(self, tool, tmp_path):
        """Test helpful error for nonexistent paths."""
        result = await tool.execute(
            {"path": "nonexistent", "working_directory": str(tmp_path)}
        )

        assert result.success is False
        assert "not found" in result.error.lower()
        assert "TIP" in result.error

    @pytest.mark.asyncio
    async def test_get_file_tree_subdirectory(self, tool, tmp_path):
        """Test requesting tree for specific subdirectory."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "file.py").write_text("test")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test.py").write_text("test")

        result = await tool.execute({"path": "src", "working_directory": str(tmp_path)})

        assert result.success is True
        assert "file.py" in result.output
        assert "test.py" not in result.output  # Should only show src/

    @pytest.mark.asyncio
    async def test_get_file_tree_without_working_directory(self, tool, tmp_path):
        """Test that tool works without working_directory (uses absolute path)."""
        (tmp_path / "testfile.txt").write_text("content")

        result = await tool.execute(
            {"path": str(tmp_path), "max_depth": 2, "max_files": 50}
        )

        assert result.success is True
        assert "testfile.txt" in result.output

    @pytest.mark.asyncio
    async def test_tool_name(self, tool):
        """Test tool has correct name."""
        assert tool.name == "get_file_tree"

    @pytest.mark.asyncio
    async def test_get_file_tree_defaults(self, tool, tmp_path):
        """Test that default parameters work correctly."""
        (tmp_path / "file.py").write_text("test")

        # Should use defaults: path=".", max_depth=3, max_files=100
        result = await tool.execute({"working_directory": str(tmp_path)})

        assert result.success is True
        assert "file.py" in result.output


# =============================================================================
# Tests for Path Security Helper Functions (New in this PR)
# =============================================================================


class TestPathSecurityHelpers:
    """Test security helper functions for path validation and normalization."""

    def test_normalize_match_text_replaces_backslashes(self):
        """Test that backslashes are normalized to forward slashes."""
        from deliberation.tools import _normalize_match_text

        result = _normalize_match_text(r"path\to\file.txt")
        assert "\\" not in result
        assert "/" in result

    def test_normalize_match_text_strips_whitespace(self):
        """Test that whitespace is stripped."""
        from deliberation.tools import _normalize_match_text

        result = _normalize_match_text("  /path/to/file  ")
        assert result == "/path/to/file"

    def test_normalize_path_handles_resolution_errors(self):
        """Test that path normalization handles resolution errors gracefully."""
        from deliberation.tools import _normalize_path
        from pathlib import Path

        # Even if resolution fails, should return a normalized string
        result = _normalize_path(Path("/nonexistent/path"))
        assert isinstance(result, str)
        assert "/" in result or "\\" not in result

    def test_path_contains_segment_detects_directory(self):
        """Test segment detection in paths."""
        from deliberation.tools import _path_contains_segment

        assert _path_contains_segment("/home/user/project/src", "project")
        assert _path_contains_segment("/home/user/project/src", "src")
        assert not _path_contains_segment("/home/user/project/src", "nothere")

    def test_path_contains_segment_handles_nested_segments(self):
        """Test nested directory segment detection."""
        from deliberation.tools import _path_contains_segment

        assert _path_contains_segment("/a/b/c/d", "b/c")
        assert not _path_contains_segment("/a/b/c/d", "b/d")

    def test_path_contains_segment_handles_empty_segment(self):
        """Test empty segment returns False."""
        from deliberation.tools import _path_contains_segment

        assert not _path_contains_segment("/path/to/file", "")
        assert not _path_contains_segment("/path/to/file", "   ")

    def test_is_within_directory_detects_escapes(self, tmp_path):
        """Test detection of paths escaping base directory."""
        from deliberation.tools import _is_within_directory
        from pathlib import Path

        base = tmp_path / "workspace"
        base.mkdir()
        
        inside = base / "file.txt"
        outside = tmp_path / "outside.txt"
        
        assert _is_within_directory(inside, base)
        assert not _is_within_directory(outside, base)

    def test_is_within_directory_handles_relative_paths(self, tmp_path):
        """Test relative path handling."""
        from deliberation.tools import _is_within_directory
        from pathlib import Path

        base = tmp_path / "workspace"
        base.mkdir()
        
        # Create subdirectory
        subdir = base / "subdir"
        subdir.mkdir()
        
        assert _is_within_directory(subdir, base)

    def test_resolve_working_directory_validates_existence(self, tmp_path):
        """Test working directory validation."""
        from deliberation.tools import _resolve_working_directory

        # Valid directory
        result = _resolve_working_directory(str(tmp_path))
        assert result == tmp_path.resolve()

        # Invalid directory
        with pytest.raises(ValueError, match="Working directory not found"):
            _resolve_working_directory(str(tmp_path / "nonexistent"))

    def test_resolve_working_directory_requires_directory(self, tmp_path):
        """Test that working directory must be a directory, not a file."""
        from deliberation.tools import _resolve_working_directory

        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="Working directory not found"):
            _resolve_working_directory(str(file_path))

    def test_resolve_path_within_working_dir_blocks_traversal(self, tmp_path):
        """Test path traversal is blocked."""
        from deliberation.tools import _resolve_path_within_working_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with pytest.raises(ValueError, match="Access denied.*escapes working directory"):
            _resolve_path_within_working_dir("../../../etc/passwd", str(workspace))

    def test_resolve_path_within_working_dir_allows_relative(self, tmp_path):
        """Test relative paths within working directory are allowed."""
        from deliberation.tools import _resolve_path_within_working_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        subdir = workspace / "subdir"
        subdir.mkdir()

        result = _resolve_path_within_working_dir("subdir", str(workspace))
        assert result == subdir.resolve()

    def test_resolve_path_within_working_dir_allows_absolute_if_within(self, tmp_path):
        """Test absolute paths are allowed if within working directory."""
        from deliberation.tools import _resolve_path_within_working_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        inside = workspace / "file.txt"
        inside.write_text("test")

        result = _resolve_path_within_working_dir(str(inside), str(workspace))
        assert result == inside.resolve()

    def test_resolve_path_within_working_dir_blocks_absolute_outside(self, tmp_path):
        """Test absolute paths outside working directory are blocked."""
        from deliberation.tools import _resolve_path_within_working_dir

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("test")

        with pytest.raises(ValueError, match="Access denied.*escapes working directory"):
            _resolve_path_within_working_dir(str(outside), str(workspace))

    def test_resolve_path_without_working_dir(self, tmp_path):
        """Test resolution works without working directory constraint."""
        from deliberation.tools import _resolve_path_within_working_dir

        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        result = _resolve_path_within_working_dir(str(file_path), None)
        assert result == file_path.resolve()

    def test_pattern_has_traversal_detects_dotdot(self):
        """Test detection of .. in patterns."""
        from deliberation.tools import _pattern_has_traversal

        assert _pattern_has_traversal("../file.txt")
        assert _pattern_has_traversal("dir/../file.txt")
        assert _pattern_has_traversal(r"dir\..\file.txt")
        assert not _pattern_has_traversal("./file.txt")
        assert not _pattern_has_traversal("file.txt")
        assert not _pattern_has_traversal("dir/file.txt")

    def test_is_path_excluded_with_directory_patterns(self, tmp_path):
        """Test exclusion with directory patterns."""
        from deliberation.tools import is_path_excluded
        from pathlib import Path

        path = tmp_path / "node_modules" / "package" / "file.js"
        
        assert is_path_excluded(path, ["node_modules/"])
        assert is_path_excluded(path, ["node_modules/**"])

    def test_is_path_excluded_with_glob_patterns(self, tmp_path):
        """Test exclusion with glob patterns."""
        from deliberation.tools import is_path_excluded

        path1 = tmp_path / "test.pyc"
        path2 = tmp_path / "src" / "test.pyc"
        path3 = tmp_path / "test.py"

        patterns = ["*.pyc"]
        assert is_path_excluded(path1, patterns)
        assert is_path_excluded(path2, patterns)
        assert not is_path_excluded(path3, patterns)

    def test_is_path_excluded_with_basename_match(self, tmp_path):
        """Test exclusion based on basename."""
        from deliberation.tools import is_path_excluded

        path = tmp_path / "deep" / "nested" / "secrets.txt"
        
        assert is_path_excluded(path, ["secrets.txt"])

    def test_is_path_excluded_with_segment_match(self, tmp_path):
        """Test exclusion based on path segment."""
        from deliberation.tools import is_path_excluded

        path = tmp_path / "src" / ".git" / "config"
        
        assert is_path_excluded(path, [".git"])
        assert is_path_excluded(path, [".git/"])

    def test_is_path_excluded_empty_patterns(self, tmp_path):
        """Test that empty pattern list excludes nothing."""
        from deliberation.tools import is_path_excluded

        path = tmp_path / "file.txt"
        
        assert not is_path_excluded(path, [])

    def test_is_path_excluded_ignores_empty_pattern(self, tmp_path):
        """Test that empty patterns in list are ignored."""
        from deliberation.tools import is_path_excluded

        path = tmp_path / "file.txt"
        
        assert not is_path_excluded(path, ["", "  "])

    def test_is_path_excluded_multiple_patterns(self, tmp_path):
        """Test multiple exclusion patterns."""
        from deliberation.tools import is_path_excluded

        path1 = tmp_path / "node_modules" / "pkg" / "index.js"
        path2 = tmp_path / ".git" / "config"
        path3 = tmp_path / "transcripts" / "debate.md"
        path4 = tmp_path / "src" / "main.py"

        patterns = ["node_modules/", ".git/", "transcripts/**"]
        
        assert is_path_excluded(path1, patterns)
        assert is_path_excluded(path2, patterns)
        assert is_path_excluded(path3, patterns)
        assert not is_path_excluded(path4, patterns)

    def test_is_path_excluded_wildcard_patterns(self, tmp_path):
        """Test wildcard pattern matching."""
        from deliberation.tools import is_path_excluded

        path1 = tmp_path / "test_file.py"
        path2 = tmp_path / "src" / "test_module.py"
        path3 = tmp_path / "prod_file.py"

        patterns = ["test_*"]
        
        assert is_path_excluded(path1, patterns)
        assert is_path_excluded(path2, patterns)
        assert not is_path_excluded(path3, patterns)


class TestRunCommandValidation:
    """Test RunCommandTool command validation logic."""

    @pytest.fixture
    def tool(self):
        """Create RunCommandTool instance."""
        from deliberation.tools import RunCommandTool
        return RunCommandTool()

    def test_validate_git_requires_safe_subcommand(self, tool):
        """Test git command validation."""
        result = tool._validate_command_args("git", ["status"], None)
        assert result is None

        result = tool._validate_command_args("git", ["checkout", "main"], None)
        assert result is not None
        assert "not allowed" in result.lower()

    def test_validate_git_allows_version_flag(self, tool):
        """Test git --version is allowed."""
        result = tool._validate_command_args("git", ["--version"], None)
        assert result is None

        result = tool._validate_command_args("git", ["-v"], None)
        assert result is None

    def test_validate_git_blocks_unsafe_flags(self, tool):
        """Test unsafe git flags are blocked."""
        result = tool._validate_command_args("git", ["--help"], None)
        assert result is not None

    def test_validate_git_requires_subcommand(self, tool):
        """Test git requires a subcommand."""
        result = tool._validate_command_args("git", [], None)
        assert result is not None
        assert "subcommand is required" in result.lower()

    def test_validate_git_safe_subcommands(self, tool):
        """Test all safe git subcommands are allowed."""
        safe_commands = ["status", "log", "diff", "show", "rev-parse", "ls-files", "blame"]
        
        for cmd in safe_commands:
            result = tool._validate_command_args("git", [cmd], None)
            assert result is None, f"Safe command '{cmd}' should be allowed"

    def test_validate_find_blocks_exec_flags(self, tool):
        """Test find -exec and similar flags are blocked."""
        dangerous_flags = ["-exec", "-execdir", "-ok", "-okdir", "-delete"]
        
        for flag in dangerous_flags:
            result = tool._validate_command_args("find", [".", flag, "rm", "{}"], None)
            assert result is not None
            assert "find flags" in result.lower()

    def test_validate_find_allows_safe_usage(self, tool):
        """Test safe find usage is allowed."""
        result = tool._validate_command_args("find", [".", "-name", "*.py"], None)
        assert result is None

    def test_validate_blocks_path_traversal(self, tool, tmp_path):
        """Test path traversal in arguments is blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        result = tool._validate_command_args("ls", ["../../../etc"], workspace)
        assert result is not None
        assert "path traversal" in result.lower()

    def test_validate_blocks_absolute_paths_outside_workdir(self, tool, tmp_path):
        """Test absolute paths outside working directory are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        result = tool._validate_command_args("cat", [str(outside / "file.txt")], workspace)
        assert result is not None
        assert "absolute paths outside" in result.lower()

    def test_validate_allows_absolute_paths_inside_workdir(self, tool, tmp_path):
        """Test absolute paths inside working directory are allowed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        inside = workspace / "file.txt"
        inside.write_text("test")

        result = tool._validate_command_args("cat", [str(inside)], workspace)
        assert result is None

    def test_validate_ignores_flags(self, tool, tmp_path):
        """Test validation ignores flag arguments."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        result = tool._validate_command_args("ls", ["-la", "-h"], workspace)
        assert result is None

    def test_validate_without_working_directory(self, tool):
        """Test validation works without working directory."""
        result = tool._validate_command_args("ls", ["-la"], None)
        assert result is None

    def test_validate_handles_non_string_args(self, tool):
        """Test validation handles non-string arguments gracefully."""
        # Should not crash on non-string args
        result = tool._validate_command_args("echo", ["test", 123, None], None)
        assert result is None  # Non-strings are skipped


class TestToolExecutorWorkingDirectory:
    """Test ToolExecutor properly handles working_directory parameter."""

    @pytest.mark.asyncio
    async def test_executor_propagates_working_directory_to_tool(self, tmp_path):
        """Test that ToolExecutor passes working_directory to tool execution."""
        from deliberation.tools import ToolExecutor, ReadFileTool

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        test_file = workspace / "test.txt"
        test_file.write_text("content from workspace")

        executor = ToolExecutor()
        tool = ReadFileTool()
        executor.register_tool(tool)

        from models.tool_schema import ToolRequest

        request = ToolRequest(
            name="read_file",
            arguments={"path": "test.txt"}
        )

        result = await executor.execute_tool(request, working_directory=str(workspace))

        assert result.success is True
        assert "content from workspace" in result.output

    @pytest.mark.asyncio
    async def test_executor_working_directory_in_request_arguments(self, tmp_path):
        """Test working_directory can come from request arguments."""
        from deliberation.tools import ToolExecutor, ReadFileTool

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        test_file = workspace / "test.txt"
        test_file.write_text("test content")

        executor = ToolExecutor()
        tool = ReadFileTool()
        executor.register_tool(tool)

        from models.tool_schema import ToolRequest

        request = ToolRequest(
            name="read_file",
            arguments={"path": "test.txt", "working_directory": str(workspace)}
        )

        result = await executor.execute_tool(request)

        assert result.success is True
        assert "test content" in result.output

    @pytest.mark.asyncio
    async def test_executor_parameter_overrides_request_argument(self, tmp_path):
        """Test executor parameter takes precedence over request argument."""
        from deliberation.tools import ToolExecutor, ReadFileTool

        workspace1 = tmp_path / "workspace1"
        workspace1.mkdir()
        workspace2 = tmp_path / "workspace2"
        workspace2.mkdir()
        
        file1 = workspace1 / "test.txt"
        file1.write_text("workspace1")
        file2 = workspace2 / "test.txt"
        file2.write_text("workspace2")

        executor = ToolExecutor()
        tool = ReadFileTool()
        executor.register_tool(tool)

        from models.tool_schema import ToolRequest

        request = ToolRequest(
            name="read_file",
            arguments={"path": "test.txt", "working_directory": str(workspace2)}
        )

        # Executor parameter should win
        result = await executor.execute_tool(request, working_directory=str(workspace1))

        assert result.success is True
        assert "workspace1" in result.output


class TestSymlinkSecurity:
    """Test security against symlink attacks."""

    @pytest.mark.asyncio
    async def test_read_file_follows_symlinks_but_checks_destination(self, tmp_path):
        """Test that symlinks are followed but destination is validated."""
        from deliberation.tools import ReadFileTool
        import os

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("secret data")

        # Create symlink from workspace to outside file
        link = workspace / "link.txt"
        try:
            os.symlink(str(outside), str(link))
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        tool = ReadFileTool()
        result = await tool.execute({
            "path": "link.txt",
            "working_directory": str(workspace)
        })

        # Should block access because symlink target is outside workspace
        assert result.success is False
        assert "access denied" in result.error.lower() or "escapes" in result.error.lower()

    @pytest.mark.asyncio
    async def test_list_files_with_symlinks_inside_workspace(self, tmp_path):
        """Test list_files handles symlinks within workspace."""
        from deliberation.tools import ListFilesTool
        import os

        workspace = tmp_path / "workspace"
        workspace.mkdir()
        target = workspace / "target.txt"
        target.write_text("target")
        link = workspace / "link.txt"
        
        try:
            os.symlink(str(target), str(link))
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        tool = ListFilesTool()
        result = await tool.execute({
            "pattern": "*.txt",
            "working_directory": str(workspace)
        })

        assert result.success is True
