"""Tool execution infrastructure for evidence-based deliberation."""
import asyncio
import logging
import json
import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List
from models.tool_schema import ToolRequest, ToolResult

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for deliberation tools.

    Subclasses must implement execute() and provide a name property.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (must be unique)."""
        pass

    @abstractmethod
    async def execute(self, arguments: dict) -> ToolResult:
        """
        Execute the tool with given arguments.

        Args:
            arguments: Tool-specific arguments

        Returns:
            ToolResult with success status and output/error
        """
        pass


class ToolExecutor:
    """
    Orchestrates tool execution during deliberation.

    Parses tool requests from model responses and routes to appropriate tools.
    """

    def __init__(self):
        """Initialize tool executor."""
        self.tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool for use in deliberation.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def parse_tool_requests(self, response_text: str) -> List[ToolRequest]:
        """
        Parse tool requests from model response.

        Looks for format: TOOL_REQUEST: {"name": "...", "arguments": {...}}

        Args:
            response_text: The model's response text

        Returns:
            List of ToolRequest objects (empty if none found)
        """
        requests = []

        # Find all occurrences of TOOL_REQUEST: marker
        for line in response_text.split('\n'):
            if 'TOOL_REQUEST:' in line:
                try:
                    # Extract JSON part after TOOL_REQUEST:
                    json_start = line.find('{')
                    if json_start == -1:
                        continue

                    # Use json.JSONDecoder.raw_decode() for robust JSON parsing
                    # This properly handles nested structures and } characters in strings
                    decoder = json.JSONDecoder()
                    request_data, end_idx = decoder.raw_decode(line, idx=json_start)

                    # Validate and create ToolRequest
                    request = ToolRequest(**request_data)
                    requests.append(request)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse tool request: {e}")
                    # Silently skip invalid requests
                    continue

        return requests

    async def execute_tool(self, request: ToolRequest, working_directory: str | None = None) -> ToolResult:
        """
        Execute a tool request.

        Args:
            request: The tool request to execute
            working_directory: Optional working directory to change to before executing tool

        Returns:
            ToolResult with execution outcome
        """
        tool = self.tools.get(request.name)

        if not tool:
            return ToolResult(
                tool_name=request.name,
                success=False,
                output=None,
                error=f"Tool '{request.name}' is not registered"
            )

        # Change to working directory if specified
        original_dir = None
        if working_directory:
            import os
            original_dir = os.getcwd()
            try:
                os.chdir(working_directory)
                logger.info(f"Tool execution: changed to working directory: {working_directory}")
            except Exception as e:
                return ToolResult(
                    tool_name=request.name,
                    success=False,
                    output=None,
                    error=f"Failed to change to working directory '{working_directory}': {e}"
                )

        try:
            result = await tool.execute(request.arguments)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=request.name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )
        finally:
            # Restore original directory
            if original_dir:
                try:
                    import os
                    os.chdir(original_dir)
                except Exception as e:
                    logger.error(f"Failed to restore working directory to {original_dir}: {e}", exc_info=True)


class ReadFileTool(BaseTool):
    """Tool for reading file contents during deliberation."""

    MAX_FILE_SIZE = 1024 * 1024  # 1MB limit

    @property
    def name(self) -> str:
        return "read_file"

    async def execute(self, arguments: dict) -> ToolResult:
        """
        Read file contents.

        Args:
            arguments: Must contain 'path' key with file path

        Returns:
            ToolResult with file contents or error
        """
        path_str = arguments.get("path")
        if not path_str:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required argument: 'path'"
            )

        try:
            path = Path(path_str).resolve()

            # Check file exists
            if not path.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"File not found: {path}"
                )

            # Check file size
            size = path.stat().st_size
            if size > self.MAX_FILE_SIZE:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"File too large: {size} bytes (max: {self.MAX_FILE_SIZE})"
                )

            # Read file
            content = path.read_text(encoding="utf-8")

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=content,
                error=None
            )

        except UnicodeDecodeError as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Cannot read binary file: {e}"
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )


class SearchCodeTool(BaseTool):
    """Tool for searching code patterns in codebase."""

    MAX_RESULTS = 100

    @property
    def name(self) -> str:
        return "search_code"

    async def execute(self, arguments: dict) -> ToolResult:
        """
        Search for pattern in codebase.

        Args:
            arguments: Must contain 'pattern' (regex) and optional 'path' (directory)

        Returns:
            ToolResult with matching lines or error
        """
        pattern = arguments.get("pattern")
        search_path = arguments.get("path", ".")

        if not pattern:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required argument: 'pattern'"
            )

        try:
            # Try ripgrep first (faster)
            result = await self._search_with_ripgrep(pattern, search_path)
            if result:
                return result

            # Fallback to Python regex
            return await self._search_with_python(pattern, search_path)

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )

    async def _search_with_ripgrep(self, pattern: str, search_path: str) -> ToolResult:
        """Search using ripgrep if available."""
        try:
            # Check if rg is available
            subprocess.run(["rg", "--version"], capture_output=True, timeout=1)

            # Run ripgrep
            proc = subprocess.run(
                ["rg", "--line-number", "--max-count", str(self.MAX_RESULTS), pattern, search_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if proc.returncode == 1:
                # No matches found
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output="No matches found",
                    error=None
                )
            elif proc.returncode != 0:
                # Error occurred (e.g., invalid regex)
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"Search error: {proc.stderr}"
                )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=proc.stdout.strip(),
                error=None
            )

        except FileNotFoundError:
            # ripgrep not available
            return None
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Search timed out after 10 seconds"
            )

    async def _search_with_python(self, pattern: str, search_path: str) -> ToolResult:
        """Fallback search using Python regex."""
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Invalid regex pattern: {e}"
            )

        matches = []
        path = Path(search_path)

        if not path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Path not found: {search_path}"
            )

        # Walk directory and search files
        for file_path in path.rglob("*.py"):  # Only search Python files
            if len(matches) >= self.MAX_RESULTS:
                break

            try:
                content = file_path.read_text(encoding="utf-8")
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        matches.append(f"{file_path}:{line_num}:{line.strip()}")
                        if len(matches) >= self.MAX_RESULTS:
                            break
            except (UnicodeDecodeError, PermissionError):
                # Skip binary or inaccessible files
                continue

        if not matches:
            output = "No matches found"
        else:
            output = "\n".join(matches)
            if len(matches) >= self.MAX_RESULTS:
                output += f"\n\n(Showing first {self.MAX_RESULTS} results)"

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=output,
            error=None
        )


class ListFilesTool(BaseTool):
    """Tool for listing files matching glob patterns."""

    MAX_FILES = 200

    @property
    def name(self) -> str:
        return "list_files"

    async def execute(self, arguments: dict) -> ToolResult:
        """
        List files matching glob pattern.

        Args:
            arguments: Must contain 'pattern' (glob) and optional 'path' (directory)

        Returns:
            ToolResult with file list or error
        """
        pattern = arguments.get("pattern", "*")
        search_path = arguments.get("path", ".")

        try:
            path = Path(search_path).resolve()

            if not path.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"Path not found: {path}"
                )

            # Use rglob for recursive patterns (e.g., **/*.py)
            if "**" in pattern:
                matches = list(path.glob(pattern))
            else:
                matches = list(path.rglob(pattern))

            # Limit results
            matches = matches[:self.MAX_FILES]

            if not matches:
                output = "No files found"
            else:
                output = "\n".join(str(f) for f in matches)
                if len(matches) >= self.MAX_FILES:
                    output += f"\n\n(Showing first {self.MAX_FILES} files)"

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                error=None
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )


class RunCommandTool(BaseTool):
    """Tool for running safe read-only commands."""

    # Whitelist of allowed commands (read-only operations)
    ALLOWED_COMMANDS = {
        "ls", "pwd", "cat", "head", "tail", "wc", "find",
        "git", "grep", "awk", "sed", "sort", "uniq",
        "tree", "file", "stat", "diff"
    }

    COMMAND_TIMEOUT = 10  # seconds

    @property
    def name(self) -> str:
        return "run_command"

    async def execute(self, arguments: dict) -> ToolResult:
        """
        Run whitelisted command.

        Args:
            arguments: Must contain 'command' and optional 'args' (list)

        Returns:
            ToolResult with command output or error
        """
        command = arguments.get("command")
        args = arguments.get("args", [])

        if not command:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="Missing required argument: 'command'"
            )

        # Check whitelist
        if command not in self.ALLOWED_COMMANDS:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"Command '{command}' is not whitelisted. Allowed: {', '.join(sorted(self.ALLOWED_COMMANDS))}"
            )

        try:
            # Execute command
            proc = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.COMMAND_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"Command timed out after {self.COMMAND_TIMEOUT}s"
                )

            # Check exit code
            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=None,
                    error=f"Command failed (exit {proc.returncode}): {error_msg}"
                )

            output = stdout.decode("utf-8", errors="replace").strip()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
                error=None
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )
