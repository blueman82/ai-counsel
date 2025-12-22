# Adding a New Tool

Tools enable AI models to gather evidence during deliberation by reading files, searching code, listing directories, or executing safe commands. This guide walks through adding a new tool to the evidence-based deliberation system.

## Steps

### 1. Create Tool Class in `deliberation/tools.py`

Subclass `BaseTool` and implement the `execute()` method:

```python
from deliberation.tools import BaseTool
from models.tool_schema import ToolResult
import asyncio

class MyNewTool(BaseTool):
    """
    Description of what this tool does.

    Security considerations:
    - Describe any security measures (whitelist, size limits, etc.)
    - Explain what could go wrong and how you mitigate it
    """

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with provided arguments.

        Args:
            arg1: Description of argument 1
            arg2: Description of argument 2

        Returns:
            ToolResult with output or error message
        """
        try:
            # Validate arguments
            required_arg = kwargs.get("required_arg")
            if not required_arg:
                return ToolResult(
                    success=False,
                    output="",
                    error="Missing required argument: required_arg"
                )

            # Execute with timeout protection
            result = await asyncio.wait_for(
                self._do_work(required_arg),
                timeout=self.timeout
            )

            return ToolResult(
                success=True,
                output=result,
                error=None
            )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution timed out after {self.timeout}s"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution failed: {str(e)}"
            )

    async def _do_work(self, arg):
        """Helper method that does the actual work."""
        # Implementation here
        pass
```

**Key considerations**:
- Always use `asyncio.wait_for()` for timeout protection
- Return `ToolResult` with `success`, `output`, and `error` fields
- Validate all inputs before execution
- Handle errors gracefully with descriptive messages
- Follow security best practices (whitelist commands, limit file sizes, etc.)

### 2. Register Tool in `DeliberationEngine.__init__`

In `deliberation/engine.py`, add your tool to the `ToolExecutor`:

```python
from deliberation.tools import MyNewTool

# In DeliberationEngine.__init__():
self.tool_executor = ToolExecutor(tools={
    "read_file": ReadFileTool(),
    "search_code": SearchCodeTool(),
    "list_files": ListFilesTool(),
    "run_command": RunCommandTool(),
    "my_new_tool": MyNewTool(timeout=10),  # Add your tool here
})
```

### 3. Update Tool Schema in `models/tool_schema.py`

Add your tool's request/response schema:

```python
class MyNewToolRequest(BaseModel):
    """Schema for my_new_tool requests."""
    name: Literal["my_new_tool"]
    arguments: Dict[str, Any]  # Or create a typed model for arguments

# Update ToolRequest union type:
ToolRequest = Union[
    ReadFileRequest,
    SearchCodeRequest,
    ListFilesRequest,
    RunCommandRequest,
    MyNewToolRequest,  # Add your tool here
]
```

### 4. Document Tool in MCP Tool Description

Update `server.py` to document your tool for AI models:

```python
TOOL_USAGE_INSTRUCTIONS = """
Available tools (use TOOL_REQUEST markers):

1. read_file: Read file contents
   TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/path/to/file"}}

2. search_code: Search codebase with regex
   TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "regex", "path": "/search/path"}}

3. list_files: List files matching glob pattern
   TOOL_REQUEST: {"name": "list_files", "arguments": {"pattern": "**/*.py", "path": "/base/path"}}

4. run_command: Execute safe read-only command
   TOOL_REQUEST: {"name": "run_command", "arguments": {"command": "ls", "args": ["-la", "/path"]}}

5. my_new_tool: Description of what it does
   TOOL_REQUEST: {"name": "my_new_tool", "arguments": {"arg1": "value1", "arg2": "value2"}}

[Rest of instructions...]
"""
```

### 5. Write Tests

**Unit tests** in `tests/unit/test_tools.py`:

```python
import pytest
from deliberation.tools import MyNewTool
from models.tool_schema import ToolResult

@pytest.mark.asyncio
async def test_my_new_tool_success():
    """Test successful execution."""
    tool = MyNewTool()
    result = await tool.execute(required_arg="valid_value")

    assert result.success is True
    assert result.error is None
    assert "expected output" in result.output

@pytest.mark.asyncio
async def test_my_new_tool_missing_arg():
    """Test error handling for missing arguments."""
    tool = MyNewTool()
    result = await tool.execute()

    assert result.success is False
    assert "Missing required argument" in result.error

@pytest.mark.asyncio
async def test_my_new_tool_timeout():
    """Test timeout protection."""
    tool = MyNewTool(timeout=0.1)  # Very short timeout
    result = await tool.execute(required_arg="slow_operation")

    assert result.success is False
    assert "timed out" in result.error
```

**Integration tests** in `tests/integration/test_tool_context_injection.py`:

```python
@pytest.mark.asyncio
async def test_my_new_tool_in_deliberation(mock_config):
    """Test tool integration in actual deliberation."""
    engine = DeliberationEngine(config=mock_config)

    # Mock adapter responses with tool request
    mock_responses = {
        "participant1": "Let me check: TOOL_REQUEST: {\"name\": \"my_new_tool\", \"arguments\": {\"arg1\": \"value\"}}",
        "participant2": "I agree with the findings.",
    }

    # Execute round
    result = await engine.execute_round(
        question="Test question",
        round_num=1,
        previous_responses=[]
    )

    # Verify tool was executed and results visible
    assert len(result.tool_executions) > 0
    assert result.tool_executions[0].tool_name == "my_new_tool"
    assert result.tool_executions[0].result.success is True
```

### 6. Test End-to-End

Test your tool in a real deliberation:

```bash
# Start the MCP server
python server.py

# In another terminal, use your MCP client to invoke deliberate
# Include a question that would benefit from your new tool
```

## Security Checklist

Before deploying a new tool, verify:
- [ ] Input validation prevents injection attacks
- [ ] Timeout protection prevents hanging
- [ ] Error handling doesn't leak sensitive information
- [ ] File/command access is appropriately restricted
- [ ] Resource limits prevent DoS (file size, command output, etc.)
- [ ] Tool fails safely (returns error, doesn't crash engine)

## Common Patterns

### File System Access

```python
# Always validate paths
if not os.path.exists(path):
    return ToolResult(success=False, output="", error=f"Path not found: {path}")

# Check file size before reading
if os.path.getsize(path) > MAX_SIZE:
    return ToolResult(success=False, output="", error=f"File too large (max {MAX_SIZE} bytes)")
```

### Command Execution

```python
# Use whitelist, never trust input
ALLOWED_COMMANDS = {"ls", "grep", "find", "cat", "head", "tail"}
command_name = command.split()[0]
if command_name not in ALLOWED_COMMANDS:
    return ToolResult(success=False, output="", error=f"Command not allowed: {command_name}")
```

### Async Operations

```python
# Always wrap in wait_for for timeout protection
try:
    result = await asyncio.wait_for(
        slow_operation(),
        timeout=self.timeout
    )
except asyncio.TimeoutError:
    return ToolResult(success=False, output="", error="Operation timed out")
```

## How Tools Work in Deliberations

1. **Tool Request**: Model includes TOOL_REQUEST marker in response
2. **Parsing**: `ToolExecutor.parse_tool_requests()` extracts requests via regex
3. **Validation**: Each request validated against schema
4. **Execution**: Tool runs with timeout protection
5. **Recording**: Result stored in `ToolExecutionRecord`
6. **Context Injection**: Tool results visible to ALL participants in next round
7. **Transcript**: Tool executions recorded in separate section

## Example Tool Usage in Deliberations

**Evidence Gathering**:
```
Model response: "Let me check the implementation:
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/project/engine.py"}}

Based on the code, I recommend..."
```

**Code Search**:
```
Model response: "I'll search for usages:
TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "old_function\\(", "path": "/project"}}

Found 12 usages that need updating..."
```

**Multi-Tool Reasoning**:
```
Model response: "First, let me list the files:
TOOL_REQUEST: {"name": "list_files", "arguments": {"pattern": "test_*.py", "path": "/tests"}}

Now let me check the main file:
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/tests/test_engine.py"}}

Based on this evidence, I recommend..."
```

## Troubleshooting

**Tool Requests Not Being Parsed**:
- Check JSON syntax: Must be valid JSON on same line as `TOOL_REQUEST:`
- Verify tool name: Must match registered tool exactly (`read_file`, not `readFile`)
- Check arguments: Must match tool's expected schema

**Tool Execution Failures**:
- Read error message in `ToolResult.error` field
- Common causes: File not found, path invalid, command not whitelisted
- Check `mcp_server.log` for detailed error traces

**Performance Issues**:
- Reduce search scope: Use specific paths instead of searching entire codebase
- Limit tool requests: Only request evidence when necessary
- Check timeout settings: May need to increase for large files/codebases
