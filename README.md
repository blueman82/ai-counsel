# AI Counsel

True deliberative consensus MCP server where AI models debate and refine positions across multiple rounds.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)
![MCP](https://img.shields.io/badge/MCP-Server-green.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

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
- 🗳️ **Structured Voting:** Models cast votes with confidence levels and rationale
- 🧮 **Vote Semantic Grouping:** Semantically similar vote options automatically merged (0.70+ similarity)
- 🎛️ **Model-Controlled Stopping:** Models decide when to stop deliberating (adaptive rounds)

## Quick Start

**TL;DR**: Install Python 3.11+, any AI CLI tools (claude/codex/droid/gemini) → Clone repo → Run setup → Add to Claude Code MCP config → Use!

## Installation

### Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python3 --version  # Should show 3.11 or higher
   ```

2. **At least one authenticated AI CLI tool** (install and authenticate any or all):
   - **Claude CLI** (Anthropic): https://docs.claude.com/en/docs/claude-code/setup - Verify: `claude --version`
   - **Codex CLI** (OpenAI): https://github.com/openai/codex - Install: `npm install -g @openai/codex` - Verify: `codex --version`
   - **Droid CLI** (Factory AI): https://github.com/Factory-AI/factory - Verify: `droid --version`
   - **Gemini CLI** (Google): https://github.com/google-gemini/gemini-cli - Install: `npm install -g @google/gemini-cli` - Verify: `gemini --version`

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
# This includes core dependencies (mcp, pydantic, pyyaml) plus enhanced
# convergence detection backends (scikit-learn, sentence-transformers)
# for best accuracy and vote grouping

# 5. Verify installation (recommended)
python3 -m pytest tests/unit -v
# Expected: All tests pass
```

**✅ That's it!** The server is ready to use with enhanced convergence detection and vote grouping.

### Convergence Detection Backends

The installation includes two high-quality similarity backends for convergence detection and vote option grouping:

1. **SentenceTransformer** (primary) - Deep semantic understanding using neural embeddings
   - Best accuracy for detecting when models truly converge
   - Used for vote semantic grouping (0.70+ threshold)
   - Model cached after first load (~3s), instant on restart

2. **TF-IDF** (fallback) - Statistical similarity using term frequency
   - Good accuracy, faster than neural embeddings
   - Used if sentence-transformers initialization fails

3. **Jaccard** (emergency fallback) - Word overlap matching
   - Always available as zero-dependency fallback
   - Ensures convergence detection never fails

The system automatically selects the best available backend and gracefully falls back if dependencies have issues.

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

The system compares responses between consecutive rounds using semantic similarity **and structured voting**:
- **Unanimous Consensus** (3-0 vote): All models vote for same option
- **Majority Decision** (2-1 vote): Clear winner from voting
- **Converged** (≥ 85% similarity): Models agree semantically, stops early
- **Refining** (40-85% similarity): Still making progress, continues
- **Diverging** (< 40% similarity): Models disagree significantly
- **Impasse**: Stable disagreement after 2+ rounds, stops
- **Tie**: No clear winner from voting (1-1-1)

**Voting takes precedence**: When models cast votes, the convergence status reflects the voting outcome rather than semantic similarity.

**Vote Option Grouping:**

Semantically similar vote options are automatically grouped together using the same similarity backend:
- **Threshold**: 0.70 (70% similarity or higher merges options)
- **Example**: "Self-documenting code" and "Prioritize self-documenting code" merged into single vote
- **Visible in logs**: Vote similarity scores logged at INFO level in `mcp_server.log` for transparency

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

  # Model-controlled early stopping
  early_stopping:
    enabled: true
    threshold: 0.66  # 66% of models must want to stop
    respect_min_rounds: true  # Wait for min_rounds before stopping
```

**Example Result:**

```json
{
  "convergence_info": {
    "detected": true,
    "detection_round": 2,
    "final_similarity": 0.73,
    "status": "majority_decision",
    "per_participant_similarity": {
      "claude@cli": 0.73,
      "codex@cli": 0.85,
      "gemini@cli": 0.70
    }
  },
  "voting_result": {
    "final_tally": {"Option A": 2, "Option B": 1},
    "consensus_reached": true,
    "winning_option": "Option A",
    "votes_by_round": [...]
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

**For Claude Code**, you have two options:

**Option A: Project Config (Recommended)** - Create `.mcp.json` in the ai-counsel project root:

```bash
# Inside the ai-counsel directory
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "ai-counsel": {
      "type": "stdio",
      "command": ".venv/bin/python",
      "args": ["server.py"],
      "env": {}
    }
  }
}
EOF
```

This file can be committed to your repo and works for all users. Paths are relative to the project root.

**Option B: User Config (Global)** - Add to `~/.claude.json`:

Open `~/.claude.json` and add the `ai-counsel` server to the `mcpServers` field:

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

**After configuration**, restart Claude Code to load the server.

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
- **AI-Generated Summary**: An AI model analyzes the full debate to extract:
  - Overall consensus or areas of disagreement
  - Key agreements between participants
  - Key disagreements or points of contention
  - Final recommendation synthesizing all perspectives
- **Full Debate**: Complete responses from all rounds with timestamps and participant stances

**AI Summarizer Selection:**

The system automatically selects the best available adapter for summary generation in this priority order:
1. **Claude Sonnet** (best for summarization)
2. **GPT-5 Codex** (excellent reasoning)
3. **Droid with Claude Sonnet** (Claude via Droid)
4. **Gemini 2.5 Pro** (good quality)

If no CLI adapters are available, placeholder summaries are used. Check server logs to see which summarizer was selected.

## Development

**For Claude Code users**: See [CLAUDE.md](CLAUDE.md) for detailed architecture notes, development workflow, and common gotchas when working with this codebase.

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

## Roadmap

### Current Features ✅

- ✅ 4 CLI adapters: claude, codex, droid, gemini
- ✅ Quick and conference modes
- ✅ Markdown transcripts with full debate history
- ✅ MCP server integration
- ✅ Structured summaries
- ✅ Hook interference prevention
- ✅ Convergence detection (auto-stop when opinions stabilize)
- ✅ Structured voting mechanisms with confidence and rationale
- ✅ Model-controlled early stopping (adaptive round counts)
- ✅ Voting-aware convergence status (majority_decision, unanimous_consensus, tie)
- ✅ Vote semantic grouping (auto-merge similar options at 0.70+ threshold)
- ✅ Enhanced logging (INFO-level vote similarity scores in mcp_server.log)
- ✅ AI-powered summary generation (uses Claude to analyze and summarize debates)

### Future Enhancements
- [ ] More CLI tool adapters (ollama, llama-cpp, etc.)
- [ ] Web UI for viewing transcripts
- [ ] Real-time streaming of deliberation progress

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests first (TDD workflow)
4. Implement feature
5. Ensure all tests pass (`pytest tests/unit -v`)
6. Submit PR with clear description

## License

MIT License - see LICENSE file

## Credits

Built with:
- [MCP SDK](https://modelcontextprotocol.io/) - Model Context Protocol
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [pytest](https://pytest.org/) - Testing framework

Inspired by the need for true deliberative AI consensus beyond parallel opinion gathering.

---

## 🚦 Status

![GitHub stars](https://img.shields.io/github/stars/blueman82/ai-counsel)
![GitHub forks](https://img.shields.io/github/forks/blueman82/ai-counsel)
![GitHub last commit](https://img.shields.io/github/last-commit/blueman82/ai-counsel)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-113%20passing-green)
![Version](https://img.shields.io/badge/version-1.2.0-blue)

**Production Ready** - Multi-model deliberative consensus with structured voting and adaptive early stopping for critical technical decisions!
