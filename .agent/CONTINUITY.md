# CONTINUITY — AI-COUNSEL

## Goal (incl. success criteria)

**Current:** [Describe current task]

**Success criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Constraints/Assumptions

- Work in: `D:\Dev\_EXTRAS_\ai-counsel`
- Python 3.10+
- MCP server protocol

## Key decisions

- [Decision 1]
- [Decision 2]

## State

### Done

- [x] [Completed task]

### Now

- [Current task]

### Next

- [Next task]

## Open questions

1. [Question 1]

## Working set

**Key files:**
- `server.py` — MCP server entry point
- `adapters/` — Model adapters (CLI, HTTP, OpenAI)
- `models/` — Pydantic models and config
- `config.yaml` — Adapter configuration

**Key concepts:**
- `BaseCLIAdapter` — Base class for CLI adapters with activity-based timeout
- `OpenAIAdapter` — Adapter supporting both Chat Completions and Responses API
- `activity_timeout` — Timeout that resets on each output chunk
