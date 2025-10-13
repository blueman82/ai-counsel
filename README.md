# AI Counsel

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
- 🤖 **CLI-Based:** Works with claude, codex, and extensible to others
- 📝 **Full Transcripts:** Markdown exports with summary and complete debate
- 🎚️ **User Control:** Configure rounds, stances, and participants
- 🔍 **Transparent:** See exactly what each model said and when

## Installation

### Prerequisites

```bash
# Python 3.9 or higher required
python3 --version

# Install CLI tools you want to use
# For claude: https://docs.claude.com/en/docs/claude
# For codex: (your installation instructions)
```

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai-counsel.git
cd ai-counsel

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -m pytest tests/unit -v
# Expected: All tests pass
```

## Configuration

Edit `config.yaml` to configure CLI tools, timeouts, and settings:

```yaml
cli_tools:
  claude:
    command: "claude"
    args: ["-p", "--model", "{model}", "{prompt}"]
    timeout: 60

  codex:
    command: "codex"
    args: ["exec", "--model", "{model}", "{prompt}"]
    timeout: 60

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

## Usage

### As MCP Server

1. **Start the server:**

```bash
python server.py
```

2. **Configure in your MCP client** (e.g., Claude Code):

Add to your MCP client config:

```json
{
  "mcpServers": {
    "ai-counsel": {
      "command": "python",
      "args": ["/absolute/path/to/ai-counsel/server.py"]
    }
  }
}
```

3. **Use the `deliberate` tool:**

```javascript
// Quick mode (1 round)
await use_mcp_tool("deliberate", {
  question: "Should we migrate from JavaScript to TypeScript for our React components?",
  participants: [
    {cli: "claude", model: "claude-3-5-sonnet-20241022"},
    {cli: "codex", model: "gpt-4"}
  ],
  mode: "quick"
});

// Conference mode (multi-round)
await use_mcp_tool("deliberate", {
  question: "Should we refactor our authentication system from JWT to session-based auth?",
  participants: [
    {cli: "claude", model: "claude-3-5-sonnet-20241022", stance: "neutral"},
    {cli: "codex", model: "gpt-4", stance: "for"}
  ],
  rounds: 3,
  mode: "conference",
  context: "Current system: JWT tokens with 30min expiration, 50K active users, Redis session store already in use"
});
```

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

### MVP (Current) ✅

- ✅ claude and codex adapters
- ✅ Quick and conference modes
- ✅ Markdown transcripts with full debate history
- ✅ MCP server integration
- ✅ Structured summaries

### Future

- [ ] Convergence detection (auto-stop when opinions stabilize)
- [ ] Semantic similarity for better summary generation
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

**Status:** MVP Complete - Ready for use!
