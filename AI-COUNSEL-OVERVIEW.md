# AI Counsel - Technical Overview

## What It Is

AI Counsel is a Model Context Protocol (MCP) server that enables true deliberative consensus between AI models. Unlike parallel opinion gathering systems, models see each other's responses and refine positions across multiple rounds of structured debate with voting and convergence detection.

## Purpose

Enable AI systems to make better architectural and technical decisions by leveraging multiple model perspectives in collaborative debate rather than aggregating independent opinions. Particularly useful for design decisions, code reviews, and technical strategy where evidence-based reasoning improves outcomes.

## Key Features

- **Multi-Round Deliberation**: Models debate across configurable rounds (quick single-round or conference multi-round modes) with cross-pollination of ideas
- **Structured Voting**: Models vote with confidence levels, rationale, and continue_debate signals; automatic consensus detection (unanimous/majority/tie)
- **Evidence-Based Deliberation**: Models can read files, search code, list files, and run commands to ground decisions in actual codebase reality
- **Auto-Convergence**: Stops early when opinions stabilize or models indicate readiness, reducing API costs while maintaining quality
- **Decision Graph Memory**: Persistent SQLite database learns from past deliberations, automatically injects similar past decisions into new debates for institutional knowledge retention

## Architecture

```
server.py (MCP entry point)
  └─ DeliberationEngine (orchestration)
      ├─ Adapter Layer (CLI + HTTP)
      │  ├─ CLI: Claude, Codex, Droid, Gemini, LlamaCpp
      │  └─ HTTP: Ollama, LM Studio, OpenRouter
      ├─ Tool Execution System (evidence gathering)
      │  ├─ ReadFileTool, SearchCodeTool, ListFilesTool, RunCommandTool
      │  └─ ToolExecutor (parsing, validation, isolation)
      ├─ Convergence Detection (semantic similarity)
      │  └─ Backends: SentenceTransformer → TF-IDF → Jaccard
      ├─ Structured Voting (consensus aggregation)
      ├─ Transcript Manager (markdown generation + AI summaries)
      └─ Decision Graph (optional memory system)
          └─ QueryEngine (search_similar, find_contradictions, trace_evolution)
```

**Key Design**: Subprocess isolation ensures models analyze the correct repository via `working_directory` parameter. CLI adapters run from client's directory; HTTP adapters receive paths explicitly. Tool execution validates paths, enforces whitelists (allowed commands: ls, grep, find, cat, head, tail), and applies timeouts.

## Technology Stack

- **Language**: Python 3.11+
- **MCP Protocol**: Model Context Protocol via stdio transport
- **Data Validation**: Pydantic (type-safe schemas)
- **CLI Adapters**: Subprocess execution with context isolation
- **HTTP Adapters**: httpx async client with tenacity exponential backoff
- **Convergence**: sentence-transformers (best), scikit-learn TF-IDF (good), Jaccard fallback (zero deps)
- **Database**: SQLite3 for decision graph persistence
- **Testing**: pytest with unit/integration/E2E coverage
- **Code Quality**: black, ruff, mypy type checking

## Installation

```bash
# Clone and setup
git clone https://github.com/blueman82/ai-counsel.git
cd ai-counsel
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-optional.txt  # Convergence backends (recommended)

# Verify
python3 -m pytest tests/unit -v
```

## Integration Points

### With Claude Code / Conductor

- **MCP Server Mode**: Runs as stdio-based MCP server for Claude Code IDE integration
- **Config**: Add to `.mcp.json` or `~/.claude.json` with Python interpreter path
- **MCP Tools**: Exposes `deliberate` and `query_decisions` tools callable from Claude Code
- **Working Directory**: Requires `working_directory` parameter from client (typically `process.cwd()`) for proper file isolation

### Model-to-Model Collaboration

- Models invoke internal tools via `TOOL_REQUEST` markers in responses
- Engine parses markers, executes tools, makes results visible to all participants in next round
- Evidence grounds decisions in actual code state, not assumptions

### Decision Memory

- Automatically queries past decisions similar to current question
- Injects top-3 matching decisions into Round 1 prompt for context
- Optional query tool: `query_decisions` for searching decision history by question, finding contradictions, or tracing opinion evolution

## Command Interface

### MCP-Callable Tools

**deliberate**
```json
{
  "question": "Should we migrate from SQLite to PostgreSQL?",
  "participants": [
    {"cli": "claude", "model": "claude-sonnet-4-5-20250929"},
    {"cli": "codex", "model": "gpt-5-codex"}
  ],
  "mode": "conference",
  "rounds": 3,
  "working_directory": "/path/to/project"
}
```

**query_decisions**
```json
{
  "query": "database migration",
  "operation": "search_similar",
  "limit": 5
}
```

### Model-Invoked Internal Tools (via TOOL_REQUEST)

Models include these in responses to gather evidence during deliberation:

```
TOOL_REQUEST: {"name": "read_file", "arguments": {"path": "config.yaml"}}
TOOL_REQUEST: {"name": "search_code", "arguments": {"pattern": "SELECT.*FROM", "path": "."}}
TOOL_REQUEST: {"name": "list_files", "arguments": {"pattern": "*.sql"}}
TOOL_REQUEST: {"name": "run_command", "arguments": {"command": "git", "args": ["log", "--oneline", "-10"]}}
```

## Configuration

**config.yaml** sections:

```yaml
adapters:
  claude:
    type: cli
    command: claude
    args: ["-p", "--model", "{model}", "{prompt}"]
    timeout: 300
  ollama:
    type: http
    base_url: http://localhost:11434
    timeout: 120

defaults:
  mode: quick
  rounds: 2
  max_rounds: 5

deliberation:
  convergence_detection:
    enabled: true
    threshold: 0.85
  early_stopping:
    enabled: true
    threshold: 0.66
  tool_security:
    exclude_patterns: [transcripts/, .git/, node_modules/]
    max_file_size_bytes: 1048576  # 1MB
    command_whitelist: [ls, grep, find, cat, head, tail]

decision_graph:
  enabled: true
  db_path: decision_graph.db
  similarity_threshold: 0.6
  max_context_decisions: 3

model_registry:
  claude:
    - id: claude-sonnet-4-5-20250929
      enabled: true
      default: true
```

**Environment**: Optional `.env` file for HTTP adapter API keys (OpenRouter, etc.)

## Current Status

**Production Ready** - 113+ passing tests, comprehensive error handling, type-safe validation via Pydantic throughout. Core features (deliberation engine, structured voting, convergence detection, evidence-based tools, decision memory) fully implemented and tested. No known major issues. Actively maintained with documentation covering all features.

**Latest Version**: 1.2.1 | **Build**: Passing | **Tests**: 130+ passing | **Code Quality**: black, ruff, mypy clean

---

## Quick Reference

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Adapter System** | Multi-model orchestration (CLI + HTTP) | `adapters/base.py`, `adapters/*.py` |
| **Deliberation Engine** | Round orchestration, convergence logic | `deliberation/engine.py` |
| **Tool Execution** | Evidence gathering during debate | `deliberation/tools.py` |
| **Convergence** | Detect when opinions stabilize | `deliberation/convergence.py` |
| **Decision Graph** | Memory of past decisions | `decision_graph/` |
| **Transcripts** | Markdown export with AI summaries | `deliberation/transcript.py` |
| **Configuration** | YAML + Pydantic schemas | `config.yaml`, `models/config.py` |
| **Testing** | 113+ unit/integration/E2E tests | `tests/` |
