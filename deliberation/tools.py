"""Tool execution infrastructure for evidence-based deliberation."""
import logging
import json
import re
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
        # Pattern to match TOOL_REQUEST: followed by JSON object
        # Uses greedy matching to handle nested JSON structures
        pattern = r"TOOL_REQUEST:\s*(\{.+?\}(?:\s*\})*))"
        
        # Alternative approach: find all occurrences line by line
        for line in response_text.split('\n'):
            if 'TOOL_REQUEST:' in line:
                try:
                    # Extract JSON part after TOOL_REQUEST:
                    json_start = line.find('{')
                    if json_start == -1:
                        continue
                    
                    # Find matching closing brace for nested JSON
                    json_part = line[json_start:]
                    brace_count = 0
                    end_idx = -1
                    
                    for i, char in enumerate(json_part):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    
                    if end_idx > 0:
                        request_json = json_part[:end_idx]
                        request_data = json.loads(request_json)
                        request = ToolRequest(**request_data)
                        requests.append(request)
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"Failed to parse tool request: {e}")
                    # Silently skip invalid requests
                    continue

        return requests

    async def execute_tool(self, request: ToolRequest) -> ToolResult:
        """
        Execute a tool request.

        Args:
            request: The tool request to execute

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
