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

**CLI Adapters** (`adapters/`)
- Abstract base: `BaseCLIAdapter` handles subprocess execution, timeout, error handling
- Concrete adapters: `ClaudeAdapter`, `CodexAdapter`, `DroidAdapter`, `GeminiAdapter`
- Each adapter implements `parse_output()` for tool-specific response parsing
- Factory pattern in `adapters/__init__.py` creates adapters from config

**Convergence Detection** (`deliberation/convergence.py`)
- Semantic similarity comparison between consecutive rounds
- Three backends with automatic fallback: SentenceTransformer (best) → TF-IDF → Jaccard (zero deps)
- Statuses: converged (≥85%), refining (40-85%), diverging (<40%), impasse (stable disagreement)
- Enables auto-stop when consensus reached or stable disagreement detected

**Transcript Management** (`deliberation/transcript.py`)
- Generates markdown transcripts in `transcripts/` directory
- Filename format: `YYYYMMDD_HHMMSS_Question_truncated.md`
- Includes AI-generated summary (consensus, agreements, disagreements, recommendation) and full debate

**AI Summarizer** (`deliberation/summarizer.py`)
- Uses AI models to analyze and summarize completed debates
- Preference order: Claude Sonnet → GPT-5 Codex → Droid → Gemini
- Generates structured summaries with consensus, agreements, disagreements, and recommendations

**Data Models** (`models/schema.py`)
- Pydantic models for validation: `Participant`, `DeliberateRequest`, `RoundResponse`, `Summary`, `ConvergenceInfo`, `DeliberationResult`
- Type-safe request/response handling throughout the system

**Configuration** (`models/config.py`, `config.yaml`)
- YAML-based configuration for CLI tools, timeouts, convergence thresholds
- Per-CLI command templates with `{model}` and `{prompt}` placeholders
- Hook disabling for Claude CLI: `--settings '{"disableAllHooks": true}'`

### Data Flow

1. MCP client invokes `deliberate` tool → `server.py::call_tool()`
2. Request validated against `DeliberateRequest` schema
3. `DeliberationEngine.execute()` orchestrates rounds
4. For each round: `execute_round()` → adapters invoke CLIs → responses collected
5. After round 2+: convergence detection compares current vs previous round
6. If converged/impasse: stop early; else continue to max rounds
7. AI summarizer generates structured summary of debate
8. `TranscriptManager` saves markdown to `transcripts/`
9. Result serialized and returned to MCP client

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
   cli_tools:
     your_cli:
       command: "your-cli"
       args: ["--model", "{model}", "{prompt}"]
       timeout: 60
   ```

3. **Register adapter** in `adapters/__init__.py`:
   - Import adapter class
   - Add to `adapters` dict in `create_adapter()`

4. **Update schema** in `models/schema.py`:
   - Add CLI name to `Participant.cli` Literal type
   - Update MCP tool description in `server.py`

5. **Add recommended models** in `server.py::RECOMMENDED_MODELS`

6. **Write tests** in `tests/unit/test_adapters.py` and `tests/integration/`

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

- ✅ 69 passing tests with comprehensive coverage
- ✅ Type-safe Pydantic validation
- ✅ Graceful error handling and adapter isolation
- ✅ Structured logging to file (no stdio contamination)
- ✅ Convergence detection with auto-stop
- ✅ AI-powered summary generation
- ✅ Full audit trail with markdown transcripts
