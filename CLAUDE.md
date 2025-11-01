# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Counsel is an MCP (Model Context Protocol) server that enables true deliberative consensus between AI models. Unlike parallel opinion gathering, models see each other's responses and refine positions across multiple rounds of debate.

**Key differentiation**: Models engage in actual debate with cross-pollination (not just parallel aggregation).

## Architecture

### Core Components

**MCP Server Layer** (`server.py`)
- Entry point for MCP protocol communication via stdio
- Exposes 2 MCP tools: `deliberate` and `query_decisions` (when decision graph enabled)
- Handles JSON serialization and response truncation for token limits
- Logs to `mcp_server.log` (not stdout/stderr to avoid stdio interference)
- See "MCP Tool Architecture" section below for distinction between MCP-exposed and internal tools

**Deliberation Engine** (`deliberation/engine.py`)
- Orchestrates multi-round debates between models
- Manages context building from previous responses
- Coordinates convergence detection and early stopping
- Initializes AI summarizer with fallback chain: Claude Sonnet → GPT-5 Codex → Droid → Gemini
- Integrates tool execution system for evidence-based deliberation

**Tool Execution System** (`deliberation/tools.py`, `models/tool_schema.py`)
- Abstract base: `BaseTool` defines tool interface with `execute()` method and security controls
- Concrete tools: `ReadFileTool`, `SearchCodeTool`, `ListFilesTool`, `RunCommandTool`
- Orchestrator: `ToolExecutor` parses TOOL_REQUEST markers, validates requests, routes to tools
- Schema: `ToolRequest`, `ToolResult`, `ToolExecutionRecord` for type-safe execution tracking
- Security: `RunCommandTool` uses whitelist (ls, grep, find, cat, head, tail), `ReadFileTool` enforces 1MB size limit, all tools have timeout protection (10s default) and comprehensive error handling
- Context injection: Tool results automatically visible to all participants in subsequent rounds
- Transcript integration: Tool executions recorded in separate section with requests, results, timing

**CLI Adapters** (`adapters/base.py`, `adapters/claude.py`, etc.)
- Abstract base: `BaseCLIAdapter` handles subprocess execution, timeout, error handling
- Concrete adapters: `ClaudeAdapter`, `CodexAdapter`, `DroidAdapter`, `GeminiAdapter`, `LlamaCppAdapter`
- Each adapter implements `parse_output()` for tool-specific response parsing
- Factory pattern in `adapters/__init__.py` creates adapters from config
- **LlamaCpp Auto-Discovery** (`adapters/llamacpp.py`):
  - Resolves model names to file paths automatically (e.g., "llama-2-7b" → "llama-2-7b-chat.Q4_K_M.gguf")
  - Default search paths: `~/.cache/llama.cpp/models`, `~/models`, `~/.ollama/models`, `~/.lmstudio/models`, etc.
  - Environment variable: `LLAMA_CPP_MODEL_PATH` (colon-separated paths)
  - Supports fuzzy matching, recursive search, and helpful error messages with available models
  - Full paths and relative paths still work as before (backward compatible)
- **Model Size Recommendations for Deliberations**:
  - **Minimum: 7B-8B parameters** - Llama-3-8B, Mistral-7B, Qwen-2.5-7B provide reliable structured output
  - **Not recommended: <3B parameters** - Models like Llama-3.2-1B struggle with vote formatting and often echo prompts
  - **Why size matters**: Deliberations require valid JSON votes with specific formatting. Smaller models fail to follow complex instructions reliably.
  - **Token limits**: Use 2048+ tokens for deliberations (increased from 512 default) to allow complete responses
  - **Quality issues with small models**: Prompt echoing, incomplete JSON, missing VOTE markers, LaTeX wrappers that break parsing

**HTTP Adapter Layer** (`adapters/base_http.py`, `adapters/ollama.py`, etc.)
- Abstract base: `BaseHTTPAdapter` handles HTTP mechanics, retry logic, error handling
- Concrete adapters: `OllamaAdapter`, `LMStudioAdapter`, `OpenRouterAdapter` (to be added in Phase 2)
- Each adapter implements `build_request()` for request construction and `parse_response()` for response parsing
- Retry logic: exponential backoff on 5xx/429/network errors, fail-fast on 4xx client errors
- Authentication: environment variable substitution pattern `${VAR_NAME}` in config
- Uses `httpx` for async HTTP, `tenacity` for retry with exponential backoff

**Config Schema Migration** (`models/config.py`, `scripts/migrate_config.py`)
- New `adapters` section with explicit `type` field replaces `cli_tools`
- Type discrimination: `CLIAdapterConfig` (type: cli) vs `HTTPAdapterConfig` (type: http)
- Backward compatibility: both sections supported, deprecation warning on `cli_tools`
- Migration script: `python scripts/migrate_config.py config.yaml`
- Environment variable substitution in HTTP adapter configs for secure API key storage

**Convergence Detection** (`deliberation/convergence.py`)
- Semantic similarity comparison between consecutive rounds
- Three backends with automatic fallback: SentenceTransformer (best) → TF-IDF → Jaccard (zero deps)
- Statuses: converged (≥85%), refining (40-85%), diverging (<40%), impasse (stable disagreement)
- Voting-aware: overrides semantic status with voting outcomes (unanimous_consensus, majority_decision, tie)
- Enables auto-stop when consensus reached or stable disagreement detected

**Structured Voting** (`models/schema.py`)
- Vote model: option, confidence (0.0-1.0), rationale, continue_debate flag
- Aggregates votes across rounds into VotingResult with tally and winning option
- Voting outcomes take precedence over semantic similarity for convergence status
- 2-1 vote → "majority_decision", 3-0 vote → "unanimous_consensus", 1-1-1 → "tie"

**Model-Controlled Early Stopping** (`deliberation/engine.py`, `config.yaml`)
- Models signal readiness to stop via `continue_debate: false` in votes
- Engine checks after each round if threshold met (default: 66% consensus)
- Respects min_rounds configuration before allowing early stop
- Adaptive round counts: stop at round 2 if all satisfied, or continue to max rounds
- Configuration: `deliberation.early_stopping.enabled`, `threshold`, `respect_min_rounds`

**Transcript Management** (`deliberation/transcript.py`)
- Generates markdown transcripts in `transcripts/` directory
- Filename format: `YYYYMMDD_HHMMSS_Question_truncated.md`
- Includes AI-generated summary (consensus, agreements, disagreements, recommendation) and full debate
- **Voting section** (when votes present): final tally with winning indicator (✓), consensus status, votes by round with confidence/rationale/continue_debate flag

**AI Summarizer** (`deliberation/summarizer.py`)
- Uses AI models to analyze and summarize completed debates
- Preference order: Claude Sonnet → GPT-5 Codex → Droid → Gemini
- Generates structured summaries with consensus, agreements, disagreements, and recommendations

**Data Models** (`models/schema.py`)
- Pydantic models for validation: `Participant`, `DeliberateRequest`, `RoundResponse`, `Summary`, `ConvergenceInfo`, `DeliberationResult`
- Voting models: `Vote` (option, confidence, rationale, continue_debate), `RoundVote`, `VotingResult`
- Type-safe request/response handling throughout the system

**Configuration** (`models/config.py`, `config.yaml`)
- YAML-based configuration for adapters (CLI and HTTP), timeouts, convergence thresholds
- Adapter section with explicit `type` field: `cli` or `http`
- Per-CLI command templates with `{model}` and `{prompt}` placeholders
- HTTP adapter support with environment variable substitution: `${ENV_VAR}`
- Hook disabling for Claude CLI: `--settings '{"disableAllHooks": true}'`
- Migration from legacy `cli_tools` to `adapters`: `python scripts/migrate_config.py`

### Data Flow

1. MCP client invokes `deliberate` tool → `server.py::call_tool()`
2. Request validated against `DeliberateRequest` schema
3. `DeliberationEngine.execute()` orchestrates rounds
4. For each round:
   - `execute_round()` → prompts enhanced with voting instructions → adapters invoke CLIs
   - Responses collected and votes parsed from "VOTE: {json}" markers
   - **Tool request parsing**: `ToolExecutor.parse_tool_requests()` extracts TOOL_REQUEST markers from responses
   - **Tool execution**: Each tool request validated against schema, executed with timeout/error handling
   - **Context injection**: Tool results appended to round context, visible to all participants in next round
   - **Recording**: Tool executions tracked in `ToolExecutionRecord` for transcript
   - Check model-controlled early stopping: if ≥66% want to stop → break
5. After round 2+: convergence detection compares current vs previous round
6. If converged/impasse/early-stop: stop early; else continue to max rounds
7. Aggregate voting results: determine winner, consensus status, final tally
8. AI summarizer generates structured summary of debate
9. Override convergence status with voting outcome if available (majority_decision > semantic refining)
10. `TranscriptManager` saves markdown to `transcripts/` with "Tool Executions" section (if tools used)
11. Result serialized and returned to MCP client

### MCP Tool Architecture

**MCP-Exposed Tools** (callable by MCP clients):
- `deliberate`: Orchestrate multi-round AI deliberation
- `query_decisions`: Search decision graph memory (when enabled in config)

**Internal Tools** (callable by AI models during deliberation via TOOL_REQUEST):
- `read_file`: Read file contents (max 1MB)
- `search_code`: Search codebase with regex patterns
- `list_files`: List files matching glob patterns
- `run_command`: Execute safe read-only commands

**Important**: The 4 internal tools are NOT directly exposed via MCP protocol.
They are invoked by AI models during deliberation by including TOOL_REQUEST
markers in their responses. The DeliberationEngine parses these markers and
executes the tools, making results visible to all participants in subsequent rounds.

**Example Tool Request**:
```
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/path/to/file.py"}}
```

**Why Two Tool Types?**
- MCP tools enable clients to start deliberations and query results
- Internal tools enable AI models to gather evidence during deliberation
- Separation keeps MCP interface clean while empowering models with research capabilities

## Development Commands

### Virtual Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Optional: Enhanced convergence detection backends
pip install -r requirements-optional.txt
```

### Testing
```bash
# Unit tests (fast, no external dependencies)
pytest tests/unit -v

# Integration tests (requires CLI tools installed)
pytest tests/integration -v -m integration

# E2E tests (makes real API calls)
pytest tests/e2e -v -m e2e

# All tests with coverage report
pytest --cov=. --cov-report=html
```

### Code Quality
```bash
# Format code (black)
black .

# Lint (ruff)
ruff check .

# Type check (mypy, optional)
mypy .
```

### Running the Server

**Development Mode** (standalone testing):
```bash
python server.py
# Logs to mcp_server.log and stderr
```

**Production Mode** (via MCP client):
- Configure in `~/.claude/config/mcp.json`
- Server runs as stdio subprocess, managed by MCP client
- Check `mcp_server.log` for debugging

## Configuration Notes

### Timeouts
- Default per-invocation timeout: 60s
- Reasoning models (Claude Sonnet 4.5, GPT-5-Codex): 180-300s recommended
- Configure per-CLI in `config.yaml::cli_tools::<cli>::timeout`

### Convergence Detection
- Enabled by default: `deliberation.convergence_detection.enabled: true`
- Semantic similarity threshold: 0.85 (85% similarity = converged)
- Minimum rounds before checking: `min_rounds_before_check: 1` (checks starting from round 2, since you need 2 rounds to compare)
- Backend selection: automatic fallback based on installed dependencies
- **Important**: `min_rounds_before_check` must be `<= rounds - 1` for convergence info to appear. For 2-round deliberations, use `min_rounds_before_check: 1`
- **Voting override**: When structured voting produces a result, convergence status reflects voting outcome instead of semantic similarity

### Model-Controlled Early Stopping
- Enabled by default: `deliberation.early_stopping.enabled: true`
- Stop threshold: `0.66` (66% of models must want to stop)
- Respects minimum rounds: `respect_min_rounds: true` (won't stop before `defaults.rounds`)
- Models signal via `continue_debate: false` in their vote JSON
- Example: 3 models, 2 say `continue_debate: false` → stops after that round (2/3 = 66%)
- Use case: Models converge at round 2 but config says 5 rounds → stops at 2, saves API costs

### Hook Management
Claude CLI uses `--settings '{"disableAllHooks": true}'` to prevent user hooks from interfering with deliberation invocations. This is critical for reliable execution.

### MCP Response Truncation
`mcp.max_rounds_in_response: 3` limits rounds returned in MCP response (to avoid token limits). Full transcript always saved to file regardless.

## Adding a New CLI Adapter

1. **Create adapter file** in `adapters/your_cli.py`:
   - Subclass `BaseCLIAdapter`
   - Implement `parse_output(raw_output: str) -> str`
   - Handle any tool-specific output formatting

2. **Update config** in `config.yaml`:
   ```yaml
   adapters:
     your_cli:
       type: cli
       command: "your-cli"
       args: ["--model", "{model}", "{prompt}"]
       timeout: 60
   ```

3. **Register adapter** in `adapters/__init__.py`:
   - Import adapter class
   - Add to `cli_adapters` dict in `create_adapter()`

4. **Update schema** in `models/schema.py`:
   - Add CLI name to `Participant.cli` Literal type
   - Update MCP tool description in `server.py`

5. **Add recommended models** in `server.py::RECOMMENDED_MODELS`

6. **Write tests** in `tests/unit/test_adapters.py` and `tests/integration/`

## Adding a New HTTP Adapter

1. **Create adapter file** in `adapters/your_adapter.py`:
   - Subclass `BaseHTTPAdapter`
   - Implement `build_request(model, prompt) -> (endpoint, headers, body)`
   - Implement `parse_response(response_json) -> str`
   - Example:
   ```python
   from adapters.base_http import BaseHTTPAdapter
   from typing import Tuple

   class YourAdapter(BaseHTTPAdapter):
       def build_request(self, model: str, prompt: str) -> Tuple[str, dict, dict]:
           endpoint = "/api/generate"
           headers = {"Content-Type": "application/json"}
           body = {"model": model, "prompt": prompt}
           return (endpoint, headers, body)

       def parse_response(self, response_json: dict) -> str:
           return response_json["response"]
   ```

2. **Update config** in `config.yaml`:
   ```yaml
   adapters:
     your_adapter:
       type: http
       base_url: "https://api.example.com"
       api_key: "${YOUR_API_KEY}"  # Environment variable substitution
       timeout: 60
       max_retries: 3
   ```

3. **Register adapter** in `adapters/__init__.py`:
   - Import adapter class
   - Add to `http_adapters` dict in `create_adapter()`

4. **Set environment variables** (if using API keys):
   ```bash
   export YOUR_API_KEY="your-key-here"
   ```

5. **Write tests**:
   - Unit tests in `tests/unit/test_your_adapter.py`
   - Use VCR for HTTP response recording: `tests/fixtures/vcr_cassettes/your_adapter/`
   - Integration tests optional (requires running service)

6. **Test with deliberation**:
   ```python
   from adapters.your_adapter import YourAdapter
   import asyncio

   async def test():
       adapter = YourAdapter(
           base_url="https://api.example.com",
           api_key="your-key",
           timeout=60
       )
       result = await adapter.invoke(prompt="Hello", model="model-name")
       print(result)

   asyncio.run(test())
   ```

## Adding a New Tool

Tools enable AI models to gather evidence during deliberation by reading files, searching code, listing directories, or executing safe commands. Follow this guide to add a new tool to the evidence-based deliberation system.

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
   TOOL_REQUEST: {"name": "run_command", "arguments": {"command": "ls -la /path"}}

5. my_new_tool: Description of what it does
   TOOL_REQUEST: {"name": "my_new_tool", "arguments": {"arg1": "value1", "arg2": "value2"}}

[Rest of instructions...]
"""
```

### 5. Write Tests

Create unit tests in `tests/unit/test_tools.py`:

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

Create integration tests in `tests/integration/test_tool_context_injection.py`:

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

### Security Checklist

Before deploying a new tool, verify:
- [ ] Input validation prevents injection attacks
- [ ] Timeout protection prevents hanging
- [ ] Error handling doesn't leak sensitive information
- [ ] File/command access is appropriately restricted
- [ ] Resource limits prevent DoS (file size, command output, etc.)
- [ ] Tool fails safely (returns error, doesn't crash engine)

### Common Patterns

**File system access**:
```python
# Always validate paths
if not os.path.exists(path):
    return ToolResult(success=False, output="", error=f"Path not found: {path}")

# Check file size before reading
if os.path.getsize(path) > MAX_SIZE:
    return ToolResult(success=False, output="", error=f"File too large (max {MAX_SIZE} bytes)")
```

**Command execution**:
```python
# Use whitelist, never trust input
ALLOWED_COMMANDS = {"ls", "grep", "find", "cat", "head", "tail"}
command_name = command.split()[0]
if command_name not in ALLOWED_COMMANDS:
    return ToolResult(success=False, output="", error=f"Command not allowed: {command_name}")
```

**Async operations**:
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

## Key Design Principles

- **DRY**: Common subprocess logic in `BaseCLIAdapter`, tool-specific parsing in subclasses
- **YAGNI**: Build only what's needed, no premature optimization
- **TDD**: Red-green-refactor cycle for all new features
- **Simple**: Prefer straightforward solutions over clever abstractions
- **Type Safety**: Pydantic validation throughout for runtime safety
- **Error Isolation**: Adapter failures don't halt entire deliberation (other participants continue)

## Common Gotchas

1. **Stdio Contamination**: Server uses stdio for MCP protocol. All logging MUST go to file or stderr, never stdout.

2. **Timeout Tuning**: Reasoning models can take 60-120+ seconds. Undersized timeouts cause spurious failures.

3. **Convergence Backend**: Optional backends (TF-IDF, SentenceTransformer) improve quality but add dependencies. Zero-dep Jaccard backend always available.

4. **Model ID Format**: Some CLIs (droid) require full model IDs like `claude-sonnet-4-5-20250929`, not aliases like `sonnet`.

5. **Context Building**: Previous responses passed as context to subsequent rounds. Large debates = large context. Monitor token usage.

6. **Async Execution**: Engine uses `asyncio` for subprocess management. All adapter invocations are async.

7. **Hook Interference**: Claude CLI hooks can break CLI invocations during deliberation. Always disable with `--settings` flag.

8. **Prompt Length Limits**: Gemini adapter validates prompts ≤100k chars (prevents "invalid argument" API errors). `BaseCLIAdapter.invoke()` checks `validate_prompt_length()` if adapter implements it and raises `ValueError` with helpful message before making API call. Other adapters can implement similar validation.

9. **Tool Execution Errors**: Tool failures are isolated - they don't halt deliberation. Models receive error messages in tool results and can adapt their reasoning. Always check `ToolResult.success` before using `output`.

## Testing Strategy

- **Unit Tests**: Mock adapters, test engine logic, convergence detection, transcript generation
- **Integration Tests**: Real CLI invocations (requires tools installed), convergence detection with real adapters
- **E2E Tests**: Full workflow with real API calls (slow, expensive, use sparingly)
- **Fixtures**: `tests/conftest.py` provides shared fixtures for adapter mocking

## MCP Integration

This server implements MCP protocol for Claude Code integration:
- **Transport**: stdio (stdin/stdout)
- **Tools**: Single `deliberate` tool with structured JSON input/output
- **Initialization**: Handled by `mcp.server.stdio.stdio_server()`
- **Error Handling**: Errors serialized to JSON with `error_type` and `status` fields

## Development Workflow

1. Write test first (TDD)
2. Implement feature
3. Run unit tests: `pytest tests/unit -v`
4. Format/lint: `black . && ruff check .`
5. Integration test if needed: `pytest tests/integration -v`
6. Update CLAUDE.md if architecture changes
7. Commit with clear message

## Production Readiness

- ✅ 113+ passing tests with comprehensive coverage (unit, integration, e2e)
- ✅ Type-safe Pydantic validation
- ✅ Graceful error handling and adapter isolation
- ✅ Structured logging to file (no stdio contamination)
- ✅ Convergence detection with auto-stop
- ✅ Structured voting with confidence and rationale
- ✅ Model-controlled early stopping for adaptive round counts
- ✅ AI-powered summary generation
- ✅ Full audit trail with markdown transcripts
- ✅ Evidence-based deliberation with secure tool execution (read files, search code, list files, run commands)
- ✅ Tool result context injection for all participants
- ✅ Comprehensive security: whitelisted commands, file size limits, timeout protection

---

## Decision Graph Memory Architecture

### Overview

The decision graph module (`decision_graph/`) enables persistent learning from deliberations. It stores completed deliberations, finds similar past decisions, and injects context into new deliberations to accelerate convergence.

### Module Structure

```
decision_graph/
├── schema.py           # Pydantic models (DecisionNode, ParticipantStance, DecisionSimilarity)
├── storage.py          # SQLite persistence layer with CRUD operations
├── similarity.py       # Semantic similarity detection for questions
├── retrieval.py        # Context retrieval and formatting
├── integration.py      # Integration with deliberation engine
├── cache.py           # Two-tier caching (L1 query results, L2 embeddings)
├── workers.py         # Async background processing for similarity computation
├── maintenance.py     # Health monitoring and graph analytics
├── query_engine.py    # Unified query interface (search_similar, find_contradictions, etc.)
└── exporters.py       # Export to JSON, GraphML, DOT, Markdown formats
```

### Core Components

**Schema** (`decision_graph/schema.py`)
- **DecisionNode**: Completed deliberation with question, consensus, participants, timestamp
- **ParticipantStance**: Individual participant's position (vote option, confidence, rationale)
- **DecisionSimilarity**: Relationships between decisions with similarity scores (0.0-1.0)

**Storage** (`decision_graph/storage.py`)
- SQLite3 backend with schema: `decision_nodes`, `participant_stances`, `decision_similarities`
- CRUD operations: save/retrieve decisions, compute similarities, query by threshold
- Indexes: timestamp (recency), question_hash (duplicates), decision_id (joins)
- Atomic transactions for data consistency

**Retrieval** (`decision_graph/retrieval.py`)
- Uses convergence detection backend (SentenceTransformer/TF-IDF/Jaccard fallback)
- Configurable similarity threshold (default: 0.7) and max results (default: 3)
- Formats retrieved decisions as markdown context for injection into prompts
- Two-tier cache: query results (L1) and embeddings (L2)

**Integration** (`decision_graph/integration.py`)
- **store_deliberation()**: Extracts data from DeliberationResult, saves to graph
- **get_context_for_deliberation()**: Retrieves and formats context for new questions
- Async background worker enqueued on deliberation completion
- Graceful degradation: graph failures don't halt deliberations

**Performance** (`decision_graph/cache.py`, `decision_graph/workers.py`, `decision_graph/maintenance.py`)
- **Cache**: LRU query result cache (200 entries) + embedding cache (500 entries)
- **Workers**: Async background similarity computation (non-blocking, 10 jobs/sec)
- **Maintenance**: Health monitoring, growth tracking, periodic stats logging
- **Latency**: p95 deliberation start <450ms (cache-hit and miss scenarios)

**Query Engine** (`decision_graph/query_engine.py`)
- Unified interface for decision graph queries
- Methods: search_similar(), find_contradictions(), trace_evolution(), analyze_patterns()
- Shared by MCP tools and CLI commands (no duplication)

**Export** (`decision_graph/exporters.py`)
- Multiple formats: JSON (programmatic), GraphML (Gephi), DOT (Graphviz), Markdown (human)
- JSON metadata sidecars alongside transcripts for Claude interpretation

### Integration with Deliberation Engine

**In `deliberation/engine.py`:**

1. **Initialization**: DecisionGraphIntegration created if enabled in config
2. **Before deliberation**: Call `get_context_for_deliberation()` to retrieve relevant past decisions
3. **Round 1 injection**: Prepend graph context to first round prompt if available
4. **After deliberation**: Call `store_deliberation()` to save result (async background processing)

**Configuration** (`models/config.py`, `config.yaml`):
```yaml
decision_graph:
  enabled: false              # Opt-in feature
  db_path: "decision_graph.db"
  similarity_threshold: 0.7   # Min similarity to retrieve
  max_context_decisions: 3    # Max past decisions to inject
```

### Data Flow

1. **Write Path** (after deliberation):
   - Extract question, consensus, participants, votes from `DeliberationResult`
   - Create `DecisionNode`, save to SQLite
   - Create `ParticipantStance` records for each participant
   - Queue async background job to compute similarities (deferred, non-blocking)

2. **Read Path** (before deliberation):
   - Query recent decisions (~100-500 based on growth)
   - Compute similarity to current question
   - Sort by score, take top-k above threshold
   - Format as markdown context string
   - Prepend to Round 1 prompt

3. **Background Processing**:
   - Async worker receives similarity computation job
   - Batch compute against recent decisions (bounded set)
   - Store only top-20 most similar relationships
   - Expected time: <10s per decision

### Testing Strategy

**Unit Tests** (`tests/unit/test_decision_graph*.py`):
- Schema validation, storage CRUD, similarity detection
- Cache behavior (hits, misses, TTL)
- Worker scheduling and fallback paths
- 150+ test cases, 100% coverage

**Integration Tests** (`tests/integration/test_*memory*.py`, `test_*worker*.py`):
- Memory persistence across deliberations
- Context injection correctness
- Backward compatibility
- Concurrent writes and edge cases
- 155+ test cases, 98%+ coverage

**Performance Tests** (`tests/integration/test_performance.py`):
- Query latency benchmarks (target: <100ms for 1000 nodes)
- Cache hit rate after warmup (target: 60%+)
- Background worker throughput (target: 10+ jobs/sec)
- Storage efficiency (target: ~5KB per decision)

### Extension Points

1. **Custom Similarity Metrics**: Subclass `SimilarityDetector` for domain-specific matching
2. **Alternative Backends**: Replace SQLite with Neo4j, PostgreSQL, or vector database
3. **Custom Retrieval**: Override `DecisionRetriever.find_relevant_decisions()` for ranking strategy
4. **Export Formats**: Add new exporters to `decision_graph/exporters.py`

### Common Patterns

**Accessing the Graph**:
```python
# From integration layer
integration = DecisionGraphIntegration()
context = await integration.get_context_for_deliberation(question)
await integration.store_deliberation(question, result)

# From query engine (MCP/CLI)
engine = QueryEngine()
results = await engine.search_similar("vector database choice", limit=5)
contradictions = await engine.find_contradictions()
```

**Configuration in YAML**:
- Default: `enabled: false` (graph is optional)
- Threshold tuning: Higher (0.8+) = fewer but more relevant results
- Performance vs. Recall: Trade-off via `max_context_decisions` (default: 3)

### Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Store decision | <100ms | Async background similarity (non-blocking) |
| Query (cache hit) | <2μs | LRU lookup, instant |
| Query (cache miss) | <100ms | Compute similarity vs 50-100 recent decisions |
| Background similarity | <10s | Batch compute, 50-100 comparisons per decision |
| Memory per decision | ~5KB | Excludes embeddings; scales with context size |
| Index overhead | 0.61× | Total: ~1.6× data size with indexes |

### Monitoring & Health

**Automatic Monitoring** (`decision_graph/maintenance.py`):
- Periodic stats logging (every 100 decisions)
- Growth rate analysis (every 500 decisions)
- Threshold warnings (approaching 5k decision archival)
- Health checks: database connectivity, schema validation

**Public API**:
```python
stats = maintenance.get_graph_stats()  # Returns: node_count, edge_count, avg_similarity
health = maintenance.health_check()     # Returns: {"status": "healthy", ...}
```

---

## Evidence-Based Deliberation Architecture

### Overview

Evidence-based deliberation enables AI models to gather concrete evidence during debates by executing tools (reading files, searching code, listing directories, running commands). This transforms deliberations from opinion-based exchanges into evidence-backed reasoning with shared context.

**Key Innovation**: Tool results are visible to ALL participants in subsequent rounds, creating a shared knowledge base that grounds the debate in facts rather than assumptions.

### Tool System Architecture

**Tool Interface** (`deliberation/tools.py`)
- Abstract base class: `BaseTool` with `execute(**kwargs) -> ToolResult` method
- Timeout protection: All tools accept `timeout` parameter (default: 10s)
- Error isolation: Tool failures return `ToolResult(success=False, error=...)` without crashing deliberation
- Async execution: All tools use `asyncio.wait_for()` for non-blocking operation

**Available Tools**:

1. **ReadFileTool**: Read file contents with security limits
   - Max file size: 1MB (prevents DoS)
   - Path validation: Checks file exists before reading
   - Error handling: Returns descriptive errors for missing/oversized files
   - Example: `TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/path/to/file.py"}}`

2. **SearchCodeTool**: Search codebase with regex patterns
   - Uses `rg` (ripgrep) for fast searching (falls back to `grep` if unavailable)
   - Configurable depth and context lines
   - Output truncation: Limits results to prevent token overflow
   - Example: `TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "class.*Engine", "path": "/project"}}`

3. **ListFilesTool**: List files matching glob patterns
   - Uses Python's `glob` module for pattern matching
   - Recursive search support (`**` patterns)
   - Directory validation: Ensures base path exists
   - Example: `TOOL_REQUEST: {"name": "list_files", "arguments": {"pattern": "**/*.py", "path": "/project"}}`

4. **RunCommandTool**: Execute safe read-only commands
   - **Whitelist**: Only allows `ls`, `grep`, `find`, `cat`, `head`, `tail`
   - No write/delete operations permitted
   - Shell escape protection: Uses subprocess with shell=False
   - Output capture: Returns stdout, logs stderr
   - Example: `TOOL_REQUEST: {"name": "run_command", "arguments": {"command": "ls -la /path"}}`

**Tool Orchestration** (`deliberation/tools.py::ToolExecutor`)
- Parses TOOL_REQUEST markers from model responses using regex
- Validates requests against Pydantic schemas (`models/tool_schema.py`)
- Routes to appropriate tool implementation
- Collects results and formats for context injection
- Records execution history with timestamps and metadata

**Schema Validation** (`models/tool_schema.py`)
- `ToolRequest`: Union type for all tool request schemas
- `ToolResult`: Standard result format (success, output, error)
- `ToolExecutionRecord`: Audit trail with participant, tool_name, request, result, timestamp
- Type-safe execution prevents malformed requests

### Integration with Deliberation Flow

**Prompt Enhancement** (`deliberation/engine.py`)
- Round 1 prompt includes tool usage instructions
- Instructions list available tools with JSON examples
- Guidelines: Request only when evidence needed, cite tool results in responses

**Execution Flow**:
1. Model includes TOOL_REQUEST marker in response
2. `ToolExecutor.parse_tool_requests()` extracts requests via regex: `TOOL_REQUEST:\s*({.*?})`
3. Validate each request against schema (fails fast on invalid JSON/schema)
4. Execute tool with timeout protection
5. Append result to `ToolExecutionRecord` list
6. Format results as markdown section

**Context Injection** (`deliberation/engine.py::execute_round()`):
```python
# After collecting responses and executing tools
if tool_executions:
    tool_context = "\n\n## Tool Results from Round {round_num}\n\n"
    for exec in tool_executions:
        tool_context += f"### {exec.participant} used {exec.tool_name}\n"
        tool_context += f"Request: {exec.request}\n"
        tool_context += f"Result: {exec.result.output if exec.result.success else exec.result.error}\n\n"

    # Prepend to next round context
    next_round_context = tool_context + previous_responses
```

**Transcript Integration** (`deliberation/transcript.py`)
- Separate "## Tool Executions" section in markdown transcripts
- Shows: participant, tool name, arguments, result (truncated if large), success status
- Enables audit trail: Who requested what evidence? What did they find?

### Security Model

**Defense in Depth**:

1. **Input Validation**
   - Pydantic schema validation prevents malformed requests
   - Path validation: No symlinks, no parent directory traversal (planned)
   - Command whitelist: Only safe read-only commands

2. **Resource Limits**
   - File size: 1MB max (ReadFileTool)
   - Timeout: 10s default, prevents hanging operations
   - Output truncation: Prevents token/memory exhaustion

3. **Isolation**
   - Tool failures don't halt deliberation
   - Errors returned as ToolResult, models can adapt
   - No shell injection: Uses subprocess without shell

4. **Audit Trail**
   - All executions recorded with timestamps
   - Transcripts show who requested what
   - Enables post-deliberation security review

**Known Limitations**:
- No sandboxing: Tools run with MCP server's privileges
- Path traversal: Not yet blocked (planned for future)
- Rate limiting: Not implemented (could DoS with many requests)

### Usage Patterns

**Evidence Gathering**:
```python
# Model wants to read implementation before recommending changes
response = """
Let me check the current implementation:
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/project/engine.py"}}

Based on the code, I recommend...
"""
```

**Code Search**:
```python
# Model wants to find all usages of a function
response = """
I'll search for usages of the deprecated function:
TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "old_function\\(", "path": "/project"}}

Found 12 usages that need updating...
"""
```

**Multi-Tool Reasoning**:
```python
# Model uses multiple tools to build comprehensive answer
response = """
First, let me list the test files:
TOOL_REQUEST: {"name": "list_files", "arguments": {"pattern": "test_*.py", "path": "/project/tests"}}

Now let me check the main test file:
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/project/tests/test_engine.py"}}

Based on this evidence, I recommend...
"""
```

### Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Parse tool requests | <1ms | Regex extraction from response text |
| Validate request | <1ms | Pydantic schema validation |
| Execute read_file | <10ms | Depends on file size (1MB max) |
| Execute search_code | 50-200ms | Depends on codebase size, uses ripgrep |
| Execute list_files | <20ms | Depends on directory size |
| Execute run_command | 10-100ms | Depends on command complexity |
| Context injection | <5ms | String formatting and prepending |

**Optimization Tips**:
- Use specific paths to reduce search/list scope
- Request evidence only when necessary (not every round)
- Combine related evidence requests in one response

### Testing Strategy

**Unit Tests** (`tests/unit/test_tools.py`):
- Tool execution success/failure cases
- Timeout protection
- Error handling (missing files, invalid paths)
- Security validation (command whitelist, file size limits)
- Schema validation

**Integration Tests** (`tests/integration/test_tool_context_injection.py`):
- End-to-end tool execution in deliberations
- Context injection verification (tool results visible to all models)
- Multi-tool workflows
- Transcript recording accuracy

**Security Tests** (`tests/unit/test_tools.py`):
- Command whitelist enforcement (blocked: `rm`, `curl`, `python`)
- File size limit enforcement
- Path validation (existing/non-existing files)
- Error message safety (no sensitive data leakage)

### Extension Points

**Adding New Tools**: See "Adding a New Tool" section above for step-by-step guide

**Custom Security Policies**:
```python
# Subclass BaseTool to add custom validation
class RestrictedReadFileTool(ReadFileTool):
    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")

        # Custom policy: only allow reading from /safe directory
        if not path.startswith("/safe"):
            return ToolResult(
                success=False,
                output="",
                error="Access denied: Can only read from /safe directory"
            )

        return await super().execute(**kwargs)
```

**Tool Result Processing**:
```python
# Post-process tool results before context injection
def sanitize_tool_output(result: ToolResult) -> ToolResult:
    """Remove sensitive data from tool outputs."""
    if result.success:
        sanitized = result.output.replace("SECRET_KEY=", "SECRET_KEY=***")
        return ToolResult(success=True, output=sanitized, error=None)
    return result
```

### Common Patterns

**Conditional Evidence Gathering**:
```python
# Models request evidence only when needed
response = """
I need to verify the claim about performance.
TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "TODO.*performance", "path": "/project"}}

If evidence supports the claim, I'll vote for optimization.
"""
```

**Evidence-Based Voting**:
```python
# Models cite tool results in their votes
response = """
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "/config.yaml"}}

Based on the config showing max_connections=100, I vote for:
VOTE: {"option": "increase_limit", "confidence": 0.9, "rationale": "Config shows current limit is 100, logs show hitting limit", "continue_debate": false}
"""
```

**Collaborative Evidence Review**:
```python
# Round 1: Model A requests evidence
model_a = "Let me check: TOOL_REQUEST: {...}"

# Round 2: Model B sees tool result and builds on it
model_b = "Thanks for checking that file. I notice line 42 has a TODO. Let me search for related issues: TOOL_REQUEST: {...}"

# Round 3: Model C synthesizes both pieces of evidence
model_c = "Combining the evidence from rounds 1-2, I conclude..."
```

### Migration Guide

**Upgrading from Opinion-Based to Evidence-Based Deliberation**:

1. **No breaking changes**: Tool system is opt-in, models can ignore it
2. **Prompt updates**: Engine automatically adds tool instructions to Round 1
3. **Schema changes**: None required, `DeliberationResult` already includes `tool_executions`
4. **Transcript format**: Now includes "Tool Executions" section (backward compatible)

**Best Practices**:
- Start with simple questions to test tool usage
- Monitor transcript "Tool Executions" section to see what models request
- Adjust timeouts if tools frequently time out
- Add custom tools for domain-specific evidence needs

### Troubleshooting

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

**Security Concerns**:
- Review transcript "Tool Executions" section after each deliberation
- Ensure command whitelist is enforced (test with `rm` command, should fail)
- Monitor file size limits (test with >1MB file, should fail)
- Check for path traversal attempts in logs
