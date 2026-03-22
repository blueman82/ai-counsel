# CLAUDE.md
Last updated: 2026-03-22

## Project Overview

AI Counsel is an MCP server enabling true deliberative consensus between AI models. Models see each other's responses and refine positions across multiple rounds of debate (not just parallel aggregation).

**Status**: 113+ passing tests, type-safe validation, structured logging, convergence detection, AI-powered summaries, evidence-based deliberation with secure tool execution.

## Architecture (Key Files)

| Component | Location | Role |
|-----------|----------|------|
| MCP Server | `server.py` | Entry point, exposes `deliberate` + `query_decisions` tools via stdio |
| Engine | `deliberation/engine.py` | Orchestrates multi-round debates, convergence, early stopping |
| Tools | `deliberation/tools.py` | ReadFile, SearchCode, ListFiles, RunCommand (whitelist-only) |
| Adapters | `adapters/` | CLI (`claude`, `codex`, `droid`, `gemini`, `llamacpp`) + HTTP (`ollama`, `lmstudio`) |
| Config | `config.yaml`, `models/config.py` | All settings — Pydantic-validated |
| Convergence | `deliberation/convergence.py` | Semantic similarity: SentenceTransformer > TF-IDF > Jaccard |
| Decision Graph | `decision_graph/` | SQLite persistent learning from deliberations |
| Transcripts | `deliberation/transcript.py` | Markdown output in `transcripts/` |
| Models | `models/schema.py` | Pydantic: Participant, Vote, DeliberateRequest, etc. |

## Development Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Test
pytest tests/unit -v
pytest tests/integration -v -m integration

# Quality
black . && ruff check .
```

## Design Principles

- **TDD**: Red-green-refactor. Write test first.
- **NO TODOs**: All config in `config.yaml` with Pydantic schemas in `models/config.py`. Never hardcode.
- **DRY**: Common logic in base classes, specific parsing in subclasses.
- **Error Isolation**: Adapter/tool failures don't halt deliberation.
- **Type Safety**: Pydantic validation throughout.

## Critical Gotchas

1. **Stdio**: Server uses stdio for MCP. All logging to file/stderr, never stdout.
2. **Working Directory**: `deliberate` requires `working_directory` param. Without it, models analyze the wrong repo. Adapters run subprocesses from this dir.
3. **Hook Interference**: Claude CLI: `--settings '{"disableAllHooks": true}'` prevents hook breakage.
4. **Nested Sessions**: Base adapter strips `CLAUDECODE` env var to prevent "nested session" errors.
5. **Timeouts**: Reasoning models need 180-300s. Default 60s causes spurious failures.
6. **Path Exclusions**: Tools exclude `transcripts/`, `.git/`, etc. to prevent context contamination.
7. **Claude Reasoning Effort**: Only Opus 4.6+ supports effort levels. Sonnet/Haiku raise ValueError.
8. **Codex Isolation**: Known limitation — can access any file regardless of working_directory.

## Extension Guides

See `docs/adding-cli-adapter.md`, `docs/adding-http-adapter.md`, `docs/adding-tool.md`.
