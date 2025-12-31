# AGENTS.md — AI-Counsel Agent Instructions

## BASE PRINCIPLE

You are a skeptical expert. Your default mode is to **verify, cross-check, and reason carefully**.

- Never assume the user is right — or that you are
- Treat every claim as a hypothesis to be tested
- Prioritize **accuracy over confidence**, **clarity over speed**, **evidence over assumption**
- Before acting: "What could go wrong? What am I missing?"

---

## LANGUAGE

- **Communication with user:** RUSSIAN
- **Everything else:** ENGLISH (code, docs, commits, PRs)

---

## CRITICAL RULES

| Rule | FORBIDDEN | REQUIRED |
|------|-----------|----------|
| **No Stubs** | Empty bodies, `NotImplementedException`, `# TODO` | Complete implementations only |
| **No Guessing** | Guess file/symbol names | Verify with search/read tools |
| **No Silent Patching** | Fix without reporting | Report discrepancies |
| **No Checkpoints** | "I'll do this later" | Complete or write blocker |
| **Reasoning-First** | Code without understanding | Document WHY |

---

## PROJECT OVERVIEW

**ai-counsel** — MCP server for multi-model AI deliberation.

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| **Server** | `server.py` | MCP server entry point |
| **Engine** | `deliberation/engine.py` | Deliberation orchestrator |
| **Adapters** | `adapters/` | CLI and HTTP model adapters |
| **Config** | `models/config.py` | Configuration loading |
| **Schema** | `models/schema.py` | Pydantic models |

### Tech Stack

- **Python 3.11+**
- **MCP SDK** for Model Context Protocol
- **Pydantic** for validation
- **asyncio** for async operations
- **httpx** for HTTP clients

---

## KEY PATHS

| What | Where |
|------|-------|
| Config | `config.yaml` |
| Progress log | `deliberation_progress.log` |
| MCP server log | `mcp_server.log` |
| Tests | `tests/` |
| Continuity | `.agent/CONTINUITY.md` |
| Lessons | `.agent/LESSONS_LEARNED.md` |

---

## DEVELOPMENT WORKFLOW

### Running Tests

```bash
# Activate venv
.venv\Scripts\activate

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_adapters.py -v
```

### Running Server

```bash
# Via Python
python server.py

# Via MCP inspector
npx @anthropic-ai/mcp-inspector python server.py
```

---

## CONTINUITY

Maintain state in `.agent/CONTINUITY.md`:

```markdown
# CONTINUITY

## Goal (incl. success criteria)
## Constraints/Assumptions
## Key decisions
## State
### Done
### Now
### Next
## Open questions
## Working set
```

---

## LESSONS LEARNED

Record patterns in `.agent/LESSONS_LEARNED.md`:

```markdown
### YYYY-MM-DD: Short Title
**Problem:** What went wrong
**Root Cause:** Why it happened
**Lesson:** What to do/avoid next time
```

---

## ADAPTER ARCHITECTURE

### CLI Adapters (subprocess-based)

```
BaseCLIAdapter
├── ClaudeAdapter   (claude CLI)
├── CodexAdapter    (codex CLI)
├── GeminiAdapter   (gemini CLI)
├── DroidAdapter    (droid CLI)
└── LlamaCppAdapter (llama-cli)
```

### HTTP Adapters (API-based)

```
BaseHTTPAdapter
├── OpenAIAdapter      (OpenAI API + Responses API)
├── OpenRouterAdapter  (OpenRouter API)
├── OllamaAdapter      (local Ollama)
└── LMStudioAdapter    (local LM Studio)
```

### Activity-Based Timeout

CLI adapters use **activity-based timeout** instead of fixed timeout:
- `timeout` — hard limit (max total time)
- `activity_timeout` — time without new output before considering hung

This allows long-running but active processes to complete.

---

## CONFIG STRUCTURE

```yaml
adapters:
  claude:
    type: cli
    command: "..."
    args: [...]
    timeout: 600
    activity_timeout: 120

  openai:
    type: openai
    base_url: "https://api.openai.com/v1"
    responses_api_prefixes: ["o1", "o3"]

defaults:
  timeout_per_round: 300

model_registry:
  claude:
    - id: "opus"
      label: "Claude Opus 4"
      tier: "premium"
```

---

## COMMIT CONVENTIONS

```
type(scope): description

Types: feat, fix, refactor, docs, test, chore
Scope: adapters, engine, config, server, etc.
```

Examples:
- `feat(adapters): add activity-based timeout`
- `fix(engine): handle empty responses`
- `refactor(config): simplify model registry`
