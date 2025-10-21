# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Counsel is an MCP (Model Context Protocol) server that enables true deliberative consensus between AI models. Unlike parallel opinion gathering, models see each other's responses and refine positions across multiple rounds of debate.

**Key differentiation**: Models engage in actual debate with cross-pollination (not just parallel aggregation).

## Architecture

### Core Components

**MCP Server Layer** (`server.py`)
- Entry point for MCP protocol communication via stdio
- Exposes single `deliberate` tool to MCP clients
- Handles JSON serialization and response truncation for token limits
- Logs to `mcp_server.log` (not stdout/stderr to avoid stdio interference)

**Deliberation Engine** (`deliberation/engine.py`)
- Orchestrates multi-round debates between models
- Manages context building from previous responses
- Coordinates convergence detection and early stopping
- Initializes AI summarizer with fallback chain: Claude Sonnet → GPT-5 Codex → Droid → Gemini

**CLI Adapters** (`adapters/base.py`, `adapters/claude.py`, etc.)
- Abstract base: `BaseCLIAdapter` handles subprocess execution, timeout, error handling
- Concrete adapters: `ClaudeAdapter`, `CodexAdapter`, `DroidAdapter`, `GeminiAdapter`
- Each adapter implements `parse_output()` for tool-specific response parsing
- Factory pattern in `adapters/__init__.py` creates adapters from config

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
   - Check model-controlled early stopping: if ≥66% want to stop → break
5. After round 2+: convergence detection compares current vs previous round
6. If converged/impasse/early-stop: stop early; else continue to max rounds
7. Aggregate voting results: determine winner, consensus status, final tally
8. AI summarizer generates structured summary of debate
9. Override convergence status with voting outcome if available (majority_decision > semantic refining)
10. `TranscriptManager` saves markdown to `transcripts/`
11. Result serialized and returned to MCP client

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
