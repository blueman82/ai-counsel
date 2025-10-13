# AI Counsel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![MCP](https://img.shields.io/badge/MCP-Server-green.svg)](https://modelcontextprotocol.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

True deliberative consensus MCP server where AI models debate and refine positions across multiple rounds.

## What Makes This Different

Unlike existing tools (like Zen's consensus feature) that gather parallel opinions, **AI Counsel enables TRUE deliberation**:

- ✅ Models see each other's responses
- ✅ Models refine their positions based on other arguments
- ✅ Multi-round debates with convergence tracking
- ✅ Full audit trail with markdown transcripts

**Comparison:**
- **Zen Consensus**: Asks models separately, aggregates (no cross-pollination)
- **AI Counsel**: Models engage in actual debate (see and respond to each other)

## Features

- 🎯 **Two Modes:**
  - `quick`: Fast single-round opinions
  - `conference`: Multi-round deliberative debate
- 🤖 **Multi-Model Support:** Works with claude, codex, droid, gemini, and extensible to others
- 📝 **Full Transcripts:** Markdown exports with summary and complete debate
- 🎚️ **User Control:** Configure rounds, stances, and participants
- 🔍 **Transparent:** See exactly what each model said and when
- ⚡ **Auto-Convergence:** Automatically stops when opinions stabilize

## Quick Start

**TL;DR**: Install Python 3.9+, any AI CLI tools (claude/codex/droid/gemini) → Clone repo → Run setup → Add to Claude Code MCP config → Use!

## Installation

### Prerequisites

1. **Python 3.9 or higher**
   ```bash
   python3 --version  # Should show 3.9 or higher
   ```

2. **Claude CLI** (from Anthropic)
   - Install: https://docs.claude.com/claude-code/guides/cli
   - Verify: `claude --version`

3. **At least one AI CLI tool** (install any or all):
   - **Codex CLI** (OpenAI): `npm install -g @openai/codex-cli` - Verify: `codex --version`
   - **Droid CLI** (OpenAI): Visit https://github.com/openai/droid - Verify: `droid --version`
   - **Gemini CLI** (Google): `npm install -g @google/generative-ai-cli` - Verify: `gemini --version`

### Setup

```bash
# 1. Clone repository
git clone https://github.com/blueman82/ai-counsel.git
cd ai-counsel

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. (Optional) Install enhanced convergence detection backends
pip install -r requirements-optional.txt
# This adds scikit-learn (TF-IDF) and sentence-transformers (neural semantic similarity)
# These provide better quality convergence detection but aren't required

# 6. Verify installation (optional but recommended)
python3 -m pytest tests/unit -v
# Expected: All tests pass
```

**✅ That's it!** The server is ready to use.

### Optional: Enhanced Convergence Detection

By default, AI Counsel uses a lightweight Jaccard similarity backend for convergence detection (zero extra dependencies). For better quality detection, you can optionally install enhanced backends:

```bash
pip install -r requirements-optional.txt
```

This adds:
- **scikit-learn** (TF-IDF similarity) - Better than Jaccard, moderate accuracy
- **sentence-transformers** (Neural semantic similarity) - Best quality, ~500MB download

The system automatically uses the best available backend:
1. **SentenceTransformer** (best) - if sentence-transformers installed
2. **TF-IDF** (good) - if scikit-learn installed
3. **Jaccard** (basic) - always available

**Performance:**
- SentenceTransformer model cached in memory after first load (~3s)
- Subsequent MCP server restarts reuse cached model (instant)
- No performance impact on deliberations

**Note:** Optional backends are not required for core functionality. The base system works perfectly with zero extra dependencies.

## Configuration

Edit `config.yaml` to configure CLI tools, timeouts, and settings:

```yaml
cli_tools:
  claude:
    command: "claude"
    args: ["-p", "--model", "{model}", "--settings", "{{\"disableAllHooks\": true}}", "{prompt}"]
    timeout: 300  # 5 minutes for reasoning models

  codex:
    command: "codex"
    args: ["exec", "--model", "{model}", "{prompt}"]
    timeout: 180  # 3 minutes for codex

defaults:
  mode: "quick"
  rounds: 2
  max_rounds: 5
  timeout_per_round: 120

storage:
  transcripts_dir: "transcripts"
  format: "markdown"
  auto_export: true

deliberation:
  convergence_threshold: 0.8
  enable_convergence_detection: true
```

**Note:** Timeout values are per-invocation. Modern reasoning models (like Claude Sonnet 4.5 and GPT-5-Codex) can take 60-120+ seconds for complex prompts, so higher timeouts are recommended.

**Hook Management:** Claude CLI uses `--settings '{"disableAllHooks": true}'` to prevent user hooks from interfering with CLI invocations during deliberation.

### Convergence Detection

AI Counsel can automatically detect when models reach consensus and stop early, saving time and API costs.

**How it works:**

The system compares responses between consecutive rounds using semantic similarity:
- **Converged** (≥ 85% similarity): Models agree, stops early
- **Refining** (40-85% similarity): Still making progress, continues
- **Diverging** (< 40% similarity): Models disagree significantly
- **Impasse**: Stable disagreement after 2+ rounds, stops

**Similarity Backends:**

Three backends with automatic fallback:
1. **sentence-transformers** (best): Deep semantic understanding (~500MB)
2. **TF-IDF** (good): Statistical similarity (~50MB, requires scikit-learn)
3. **Jaccard** (fallback): Word overlap (zero dependencies)

**Configuration:**

```yaml
deliberation:
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85
    divergence_threshold: 0.40
    min_rounds_before_check: 2
    consecutive_stable_rounds: 2
```

**Example Result:**

```json
{
  "convergence_info": {
    "detected": true,
    "detection_round": 3,
    "final_similarity": 0.87,
    "status": "converged",
    "per_participant_similarity": {
      "claude@cli": 0.87,
      "codex@cli": 0.89
    }
  }
}
```

## Usage

### As MCP Server

1. **Start the server:**

```bash
python server.py
```

2. **Configure in your MCP client:**

**For Claude Code with selective MCP loading** (`clyo/clyor` functions):

The server is configured in `~/.claude/config/mcp.json`. Start sessions with:

```bash
# New session with AI Counsel only
clyo --ai-counsel

# Combine with other MCPs
clyo --ai-counsel --recallor

# Resume with AI Counsel
clyor --ai-counsel
```

**For standard Claude Code**, add to `~/.claude/config/mcp.json`:

```json
{
  "mcpServers": {
    "ai-counsel": {
      "type": "stdio",
      "command": "/absolute/path/to/ai-counsel/.venv/bin/python",
      "args": ["/absolute/path/to/ai-counsel/server.py"],
      "env": {}
    }
  }
}
```

**⚠️ IMPORTANT**: Replace `/absolute/path/to/ai-counsel` with your actual path!

**Examples:**
- macOS/Linux: `/Users/yourname/projects/ai-counsel`
- Windows: `C:/Users/yourname/projects/ai-counsel`

**💡 Pro tip**: Run `pwd` (macOS/Linux) or `cd` (Windows) inside the ai-counsel directory to get the full path.

Then **restart Claude Code** to load the server.

3. **Use the `deliberate` tool:**

**First time? Try this simple example:**

From Claude Code, simply ask:
```
Use the deliberate tool to answer: "Should I use microservices or a monolith for a new API?"
```

Claude Code will invoke the ai-counsel MCP server and you'll get a multi-model deliberation!

**Advanced usage:**

```javascript
// Quick mode (1 round)
mcp__ai-counsel__deliberate({
  question: "Should we migrate from JavaScript to TypeScript for our React components?",
  participants: [
    {cli: "claude", model: "sonnet"},
    {cli: "codex", model: "gpt-5-codex"}
  ],
  mode: "quick"
})

// Conference mode (multi-round debate)
mcp__ai-counsel__deliberate({
  question: "Should we refactor our authentication system from JWT to session-based auth?",
  participants: [
    {cli: "claude", model: "claude-sonnet-4-5-20250929", stance: "neutral"},
    {cli: "codex", model: "gpt-5-codex", stance: "for"}
  ],
  rounds: 3,
  mode: "conference",
  context: "Current system: JWT tokens with 30min expiration, 50K active users, Redis session store already in use"
})

// Mix models from different CLIs
mcp__ai-counsel__deliberate({
  question: "What's the best caching strategy?",
  participants: [
    {cli: "droid", model: "claude-sonnet-4-5-20250929"},
    {cli: "gemini", model: "gemini-2.5-pro"},
    {cli: "claude", model: "sonnet"}
  ],
  mode: "quick"
})
```

**Available Models:**
- **Claude CLI**: `sonnet`, `opus`, `haiku`, or full model names like `claude-sonnet-4-5-20250929`
- **Codex CLI**: `gpt-5-codex`, `o3`
- **Droid CLI**: `claude-sonnet-4-5-20250929`, `gpt-5-codex` (full model IDs only, no short aliases)
- **Gemini CLI**: `gemini-2.5-pro`, `gemini-2.0-flash`

See [CLI Model Reference](docs/CLI_MODEL_REFERENCE.md) for complete details on model parameter formats.

**Model Validation:**
The MCP server validates model choices and logs warnings if you use non-recommended models. If you encounter errors with a model name, check the logs at `mcp_server.log` for recommendations, or refer to the tool's description which includes the current list of recommended models for each CLI.

### Transcripts

All deliberations are automatically saved to `transcripts/` as markdown:

```
transcripts/
├── 20251013_153045_Should_we_migrate_from_JavaScript_to_TypeScript.md
└── 20251013_154230_Should_we_refactor_our_authentication.md
```

Each transcript includes:
- Summary with consensus, agreements, disagreements
- Final recommendation
- Full debate with all responses from all rounds

## Development

### Running Tests

```bash
# Unit tests (fast, no dependencies)
pytest tests/unit -v

# Integration tests (requires CLI tools)
pytest tests/integration -v -m integration

# E2E tests (full workflow, makes real API calls)
pytest tests/e2e -v -m e2e

# All tests with coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check (optional)
mypy .
```

### Adding a New CLI Tool

1. Create adapter in `adapters/your_tool.py`:

```python
from adapters.base import BaseCLIAdapter

class YourToolAdapter(BaseCLIAdapter):
    def __init__(self, timeout=60):
        super().__init__(
            command="your-tool",
            args=["--model", "{model}", "{prompt}"],
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        # Your parsing logic
        return parsed_response
```

2. Update `config.yaml`:

```yaml
cli_tools:
  your-tool:
    command: "your-tool"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

3. Register in `adapters/__init__.py`:

```python
from adapters.your_tool import YourToolAdapter

# Add to create_adapter() function
def create_adapter(cli_name: str, config: CLIToolConfig):
    adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "your-tool": YourToolAdapter,  # Add this line
    }
    # ...
```

## Architecture

```
ai-counsel/
├── server.py              # MCP server entry point
├── config.yaml           # Configuration
├── adapters/             # CLI tool adapters
│   ├── base.py          # Abstract base
│   ├── claude.py        # Claude CLI adapter
│   └── codex.py         # Codex adapter
├── deliberation/         # Core engine
│   ├── engine.py        # Orchestration
│   └── transcript.py    # Markdown generation
├── models/               # Data models
│   ├── schema.py        # Pydantic models
│   └── config.py        # Config loading
├── tests/               # Test suite
│   ├── unit/           # Fast unit tests
│   ├── integration/    # CLI integration tests
│   └── e2e/           # End-to-end tests
└── transcripts/        # Generated transcripts
```

## Principles

- **DRY**: No code duplication - extract common logic to base classes
- **YAGNI**: Build only what's needed - no premature optimization
- **TDD**: Tests first, implementation second - red, green, refactor
- **Simple**: Prefer simple solutions over clever ones

## Roadmap

### Current Features ✅

- ✅ 4 CLI adapters: claude, codex, droid, gemini
- ✅ Quick and conference modes
- ✅ Markdown transcripts with full debate history
- ✅ MCP server integration
- ✅ Structured summaries
- ✅ Hook interference prevention
- ✅ Convergence detection (auto-stop when opinions stabilize)
- ✅ AI-powered summary generation (uses Claude to analyze and summarize debates)

### Future Enhancements
- [ ] More CLI tool adapters (ollama, llama-cpp, etc.)
- [ ] Web UI for viewing transcripts
- [ ] Structured voting mechanisms
- [ ] Real-time streaming of deliberation progress

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests first (TDD workflow)
4. Implement feature
5. Ensure all tests pass (`pytest tests/unit -v`)
6. Format and lint (`black .` and `ruff check .`)
7. Submit PR with clear description

## License

MIT License - see LICENSE file

## Credits

Built with:
- [MCP SDK](https://modelcontextprotocol.io/) - Model Context Protocol
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [pytest](https://pytest.org/) - Testing framework

Inspired by the need for true deliberative AI consensus beyond parallel opinion gathering.

---

## Status

[![Build](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-69%20passing-green)]()
[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()

**Production Ready** - Multi-model deliberative consensus for critical technical decisions!
