<p align="center">
  <img src="assets/ai-counsel.png" alt="AI Counsel Logo" width="400">
</p>

# AI Counsel

| Item | Reference |
| --- | --- |
| Interface | MCP server over stdio |
| Function | Multi-model deliberation, structured votes, convergence detection |
| Runtime | Python 3.11; provider CLI or HTTP service |
| Configuration | [config.example.yaml](config.example.yaml) → `config.yaml`, loaded beside [server.py](server.py) |
| License | [MIT](LICENSE) |

## Installation

```bash
git clone https://github.com/blueman82/ai-counsel.git
cd ai-counsel
cp config.example.yaml config.yaml
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

| Provider type | Prerequisites |
| --- | --- |
| CLI | Installed executable; provider authentication; model access |
| Local HTTP | Running service; loaded model |
| Hosted HTTP | Provider account, API key, model access |
| Code search | Optional `rg`; Python fallback |

| Adapter | Transport | Shipped executable or endpoint |
| --- | --- | --- |
| `claude`, `codex`, `droid`, `gemini` | CLI | Corresponding executable name |
| `llamacpp` | CLI | `llama-cli` |
| `ollama` | HTTP | `http://localhost:11434` |
| `lmstudio` | HTTP | `http://localhost:1234` |
| `openrouter` | HTTP | `https://openrouter.ai/api/v1` |
| `nebius` | HTTP | `https://api.tokenfactory.nebius.com/v1` |
| `openai` | HTTP | `https://api.openai.com/v1` |

| Credentials | Configuration |
| --- | --- |
| Hosted HTTP | `OPENROUTER_API_KEY`, `NEBIUS_API_KEY`, `OPENAI_API_KEY` |
| Local file | Optional `.env` beside `config.yaml`; existing environment precedence |
| CLI authentication | Provider CLI configuration; separate from HTTP API keys |

## MCP client configuration

- Placeholder replacement: `/absolute/path/to/ai-counsel` → clone directory.
- Configuration key: `mcpServers`; client-specific configuration file.
- Transport: stdio; no HTTP listener.

```json
{
  "mcpServers": {
    "ai-counsel": {
      "command": "/absolute/path/to/ai-counsel/.venv/bin/python",
      "args": ["/absolute/path/to/ai-counsel/server.py"]
    }
  }
}
```

- Manual stdio launch, from clone directory:

```bash
.venv/bin/python server.py
```

## MCP tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `deliberate` | Required: `question`, `participants`, `working_directory` | Responses, synthesis, votes, transcript path, cost summary |
| `list_models` | Optional: `adapter` | Enabled registry models and defaults |
| `set_session_models` | Adapter keys mapped to model IDs or `null` | Server-process overrides; `null` clears override |
| `query_decisions` | `query_text`, `find_contradictions`, `decision_id`, `limit`, `threshold`, `format` | Decision search; registration conditional on graph enabled |
| `get_quality_metrics` | `include_problem_models`, `min_responses`, `reset_after` | Response-format metrics; optional reset |

### Deliberation arguments

| Field | Constraint / behavior |
| --- | --- |
| `question` | String; minimum 10 characters |
| `participants` | Minimum 2 entries; each with `cli`, optional `model`, optional `reasoning_effort` |
| `working_directory` | Required string; absolute existing project path recommended; file context and CLI cwd |
| `mode` | `quick` default: exactly one round; `conference`: requested round limit |
| `rounds` | Integer 1–5; default 2; conference early termination possible |
| `context` | Optional additional context string |
| Omitted model | Process override → registry default |
| Explicit model | Enabled registry ID where an allowlist is configured |
| Effort | Provider/model-specific; [CLI model reference](docs/CLI_MODEL_REFERENCE.md) |

- Tool: `deliberate`.
- Placeholder replacement: `/absolute/path/to/project` → target project directory.
- Prerequisites: authenticated Claude Code and Codex; access to selected models.

```json
{
  "question": "Which changes would improve test coverage in this repository?",
  "participants": [
    {"cli": "claude", "model": "claude-sonnet-5-5", "reasoning_effort": "high"},
    {"cli": "codex", "model": "gpt-6.1-sol", "reasoning_effort": "high"}
  ],
  "working_directory": "/absolute/path/to/project",
  "mode": "conference",
  "rounds": 2
}
```

### Model selection

| Adapter | Enabled current-family IDs in shipped registry |
| --- | --- |
| `claude` | `claude-opus-5-5` (default), `claude-fable-5-1`, `claude-sonnet-5-5`, `claude-haiku-5-5` |
| `codex` | `gpt-6.1-sol` (default), `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna` |
| `openrouter`, free entries | `google/gemma-4-26b-a4b-it:free`, `google/gemma-4-31b-it:free`, `nvidia/nemotron-3.5-lightning:free` |
| Other adapters | `list_models`; [full registry](config.example.yaml) |
| Availability | Account and upstream dependent; registry membership ≠ successful invocation |
| Prices / billing | [Dated sources and effort matrix](docs/CLI_MODEL_REFERENCE.md); separate API, subscription, and Codex-credit units |

- Tool: `list_models`.

```json
{"adapter": "claude"}
```

- Tool: `set_session_models`.

```json
{"claude": "claude-sonnet-5-5", "codex": "gpt-6.1-sol"}
```

- Tool: `set_session_models`; override removal.

```json
{"claude": null, "codex": null}
```

### Decision graph queries

- Tool: `query_decisions`.
- Prerequisite: enabled decision graph with stored deliberations.

```json
{"query_text": "test coverage strategy", "limit": 5, "threshold": 0.6, "format": "summary"}
```

## Configuration and output

| Setting / artifact | Behavior |
| --- | --- |
| `adapters` | Typed configuration; precedence over duplicate legacy `cli_tools` entries |
| `cli_tools` | Supported legacy CLI configuration; deprecation warning |
| `model_registry` | IDs, labels, defaults, enabled flags; disabled entries hidden from discovery |
| `deliberation.file_tree` | Initial tree injection; shipped depth 2, maximum 50 files |
| `deliberation.vote_retry` | Missing-vote retry; shipped maximum 1, minimum response length 100 |
| `deliberation.early_stopping` | Participant stop votes; shipped threshold 0.66 |
| `deliberation.convergence_detection` | Semantic convergence checks; configurable thresholds |
| Vote option grouping | Similarity threshold 0.85; separate convergence thresholds |
| `decision_graph.enabled` | Shipped `true`; stored decisions and retrieved context |
| `free_model_fallback.enabled` | Default `false`; opt-in fallback among enabled free models |
| `adapters.openrouter.rate_limiting` | Free-model spacing; bounded Retry-After handling |
| `cost_comparison` | Illustrative rate comparison; [coverage and exclusions](docs/cost-report.md) |
| `mcp.max_rounds_in_response` | Shipped 3; implementation caps entries in `full_debate` |
| Transcripts | `transcripts/` beneath server launch directory; result `transcript_path` |
| Decision database | Relative path: deliberation storage from launch directory; query lookup beside `server.py`; absolute `decision_graph.db_path` for consistent resolution |
| Logs | `mcp_server.log` beside `server.py`; stderr logging |

## File access and execution

| Surface | Actual boundary |
| --- | --- |
| `working_directory` | Context/cwd selection; no filesystem sandbox |
| `read_file` | UTF-8; configured exclusions; shipped 1 MiB limit; paths outside cwd possible |
| `search_code` | Pattern search; configured exclusions; `rg` or Python fallback |
| `list_files` | Glob discovery; configured exclusions |
| `get_file_tree` | Tree generation; configured depth/file limits |
| `run_command` | Executable allowlist; unrestricted arguments; 10-second timeout; no shell interpolation |
| Allowed commands | `ls`, `pwd`, `cat`, `head`, `tail`, `wc`, `find`, `git`, `grep`, `awk`, `sed`, `sort`, `uniq`, `tree`, `file`, `stat`, `diff` |
| Command side effects | Writes/network operations possible through allowed programs and arguments |
| Cwd handling | Process-wide directory changes during internal tool execution |
| Native CLI permissions | Provider-specific; shipped Codex `workspace-write`; Droid permission escalation |
| Provider data | Questions, context, retrieved decisions, responses, requested file content |
| Summary generation | Additional calls through enabled-model fallback chain; possible hosted-provider use with local participants |
| Credentials | Environment/`.env`; no secret-file exclusion guarantee |
| Persistence | Questions and arguments in logs; deliberation content in transcripts/database |
| Internal tool interface | Model-generated `TOOL_REQUEST` markers; not separate public MCP tools |

## Free-model probe

| Evidence, 2026-10-10 | Measured outcome |
| --- | --- |
| [Nemotron report](docs/http-adapters/nemotron-free-votes-2026-10-10.json) | 3/3 valid vote-format rounds; small sample |
| [Gemma report](docs/http-adapters/free-model-votes-2026-10-10.json) | Both variants: 3/3 HTTP 429; no successful vote-quality measurement |
| Interpretation | Format acceptance only; no uptime, answer-quality, or future availability guarantee |
| Authentication | `OPENROUTER_API_KEY`; missing key → skipped report |
| Price guard | Live catalogue check; nonzero-priced models rejected |
| Automation | [Weekly/manual workflow](.github/workflows/free-model-votes.yml); repository secret required |

```bash
.venv/bin/python -m scripts.probe_free_model_votes --help
```

- Optional live requests; provider quota consumption:

```bash
.venv/bin/python -m scripts.probe_free_model_votes \
  --model nvidia/nemotron-3.5-lightning:free \
  --rounds 3 --timeout 90 --output /tmp/free-model-votes.json
```

## Development

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/unit
```

| Area | Reference |
| --- | --- |
| MCP handlers and schemas | [server.py](server.py) |
| Request/result models | [models/schema.py](models/schema.py) |
| Configuration validation | [models/config.py](models/config.py) |
| Execution and tools | [Engine](deliberation/engine.py), [tools](deliberation/tools.py) |
| Adapter extension | [CLI](docs/adding-cli-adapter.md), [HTTP](docs/adding-http-adapter.md) |
| Tool extension | [Adding a tool](docs/adding-tool.md) |
| Voting and convergence | [Voting](docs/structured-voting.md), [convergence](docs/convergence-detection.md) |
| Model selection | [Registry and picker](docs/model-registry-and-picker.md) |
| HTTP setup | [Ollama](docs/http-adapters/ollama-quickstart.md), [LM Studio](docs/http-adapters/lmstudio-quickstart.md), [OpenRouter](docs/http-adapters/openrouter-guide.md) |
| Decision memory | [Configuration](docs/decision-graph/configuration.md), [troubleshooting](docs/decision-graph/troubleshooting.md) |
| HTTP failures | [Troubleshooting](docs/troubleshooting/http-adapters.md) |
