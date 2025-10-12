# AI Counsel - Comprehensive Implementation Plan

**Version:** 1.0
**Last Updated:** 2025-10-12
**Estimated Duration:** 3-4 weeks

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Overview](#project-overview)
3. [Development Principles](#development-principles)
4. [Phase 0: Project Setup](#phase-0-project-setup)
5. [Phase 1: Foundation & Models](#phase-1-foundation--models)
6. [Phase 2: CLI Adapters](#phase-2-cli-adapters)
7. [Phase 3: Deliberation Engine](#phase-3-deliberation-engine)
8. [Phase 4: MCP Server Integration](#phase-4-mcp-server-integration)
9. [Phase 5: Transcript Management](#phase-5-transcript-management)
10. [Phase 6: Testing & Documentation](#phase-6-testing--documentation)
11. [Testing Guidelines](#testing-guidelines)
12. [Commit Strategy](#commit-strategy)
13. [Resources](#resources)

---

## Prerequisites

### Required Knowledge
- Python 3.9+ (async/await, type hints, subprocess)
- Basic understanding of MCP (Model Context Protocol)
- Git and command line basics
- pytest for testing

### Required Tools
```bash
# Install these before starting
python3 --version  # Should be 3.9 or higher
pip install mcp pydantic pyyaml pytest pytest-asyncio pytest-cov
```

### Reference Documentation
- [MCP Python SDK Docs](https://modelcontextprotocol.io/introduction)
- [Pydantic V2 Docs](https://docs.pydantic.dev/latest/)
- [pytest Documentation](https://docs.pytest.org/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

---

## Project Overview

**What We're Building:**
An MCP server that enables TRUE deliberative consensus between AI models via CLI tools. Unlike existing tools (like Zen's consensus feature), our models will see each other's responses and refine their positions across multiple rounds.

**Key Differentiator:**
- **Zen**: Parallel opinions (models never see each other's responses)
- **AI Counsel**: True debate (models respond to each other's arguments)

**MVP Scope:**
- Support 2 CLI tools: `claude-code` and `codex`
- Both "quick" (1 round) and "conference" (multi-round) modes
- Full transcript logging with markdown export
- Structured summaries showing consensus/disagreement

---

## Development Principles

### DRY (Don't Repeat Yourself)
- Extract common logic to base classes
- Use config files for repeated settings
- Share test fixtures across test files

### YAGNI (You Aren't Gonna Need It)
- Build ONLY what's in the spec
- No premature optimization
- No "nice to have" features until MVP is done

### TDD (Test-Driven Development)
- Write test BEFORE implementation
- Run test (it should fail - RED)
- Write minimal code to pass (GREEN)
- Refactor (REFACTOR)
- Commit

### Commit Strategy
- Commit after every GREEN state
- Small, focused commits (1 feature/fix per commit)
- Use conventional commit messages (see [Commit Strategy](#commit-strategy))

---

## Phase 0: Project Setup ✅ COMPLETE

**Status:** All tasks completed
**Last Updated:** 2025-10-12

### Task 0.1: Initialize Project Structure ✅

**Objective:** Create the complete directory structure.

**Files to Create:**
```
ai-counsel/
├── README.md
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── config.yaml
├── server.py
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── claude_code.py
│   └── codex.py
├── deliberation/
│   ├── __init__.py
│   ├── engine.py
│   ├── convergence.py
│   └── transcript.py
├── models/
│   ├── __init__.py
│   └── schema.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_adapters.py
│   │   ├── test_engine.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_real_clis.py
│   └── e2e/
│       ├── __init__.py
│       └── test_full_deliberation.py
└── transcripts/
    └── .gitkeep
```

**Step-by-Step:**

1. **Create directory structure**
```bash
cd /path/to/your/projects
mkdir ai-counsel && cd ai-counsel
mkdir -p adapters deliberation models tests/unit tests/integration tests/e2e transcripts
touch adapters/__init__.py deliberation/__init__.py models/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/e2e/__init__.py
touch transcripts/.gitkeep
```

2. **Create `.gitignore`**
```bash
# ai-counsel/.gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.venv/
venv/
transcripts/*.md
transcripts/*.json
!transcripts/.gitkeep
.env
config.local.yaml
```

3. **Create `requirements.txt`**
```python
# ai-counsel/requirements.txt
mcp==0.9.0
pydantic==2.5.0
pyyaml==6.0.1
```

4. **Create `requirements-dev.txt`**
```python
# ai-counsel/requirements-dev.txt
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.12.1
ruff==0.1.9
```

5. **Create `pytest.ini`**
```ini
# ai-counsel/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require CLI tools installed)
    e2e: End-to-end tests (full workflow, expensive)
```

6. **Create initial `README.md`**
```markdown
# AI Counsel

True deliberative consensus MCP server where AI models debate and refine positions.

## Status

🚧 **Under Development** - MVP in progress

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/unit -v

# Run server (when implemented)
python server.py
```

## Documentation

See `docs/plans/IMPLEMENTATION_PLAN.md` for full implementation details.
```

**Testing:**
```bash
# Verify structure
ls -R
# Should see all directories and files

# Initialize git
git init
git add .
git commit -m "chore: initialize project structure"
```

**Commit Message:**
```
chore: initialize project structure

- Create complete directory layout
- Add .gitignore for Python project
- Add requirements.txt and requirements-dev.txt
- Configure pytest.ini with markers
- Add initial README
```

---

### Task 0.2: Install and Verify Dependencies ✅

**Objective:** Set up Python virtual environment and install all dependencies.

**Step-by-Step:**

1. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

3. **Verify installations**
```bash
python -c "import mcp; print(f'MCP version: {mcp.__version__}')"
python -c "import pydantic; print(f'Pydantic version: {pydantic.__version__}')"
pytest --version
```

**Testing:**
```bash
# Run pytest (should show 0 tests collected)
pytest
```

**Commit Message:**
```
chore: add python virtual environment and install dependencies

- Create .venv
- Install all required and dev dependencies
- Verify all imports work correctly
```

---

## Phase 1: Foundation & Models

### Task 1.1: Define Pydantic Models

**Objective:** Create all data models for requests, responses, and internal state.

**File:** `models/schema.py`

**Why This First:** Models define our data structure. Everything else will use these models.

**Step-by-Step:**

1. **Write the test FIRST** (TDD)

**File:** `tests/unit/test_models.py`

```python
"""Unit tests for Pydantic models."""
import pytest
from pydantic import ValidationError
from models.schema import (
    Participant,
    DeliberateRequest,
    RoundResponse,
    DeliberationResult,
)


class TestParticipant:
    """Tests for Participant model."""

    def test_valid_participant(self):
        """Test creating a valid participant."""
        p = Participant(
            cli="claude-code",
            model="claude-3-5-sonnet-20241022",
            stance="neutral"
        )
        assert p.cli == "claude-code"
        assert p.model == "claude-3-5-sonnet-20241022"
        assert p.stance == "neutral"

    def test_participant_defaults_to_neutral_stance(self):
        """Test that stance defaults to neutral."""
        p = Participant(cli="codex", model="gpt-4")
        assert p.stance == "neutral"

    def test_invalid_cli_raises_error(self):
        """Test that invalid CLI tool raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Participant(cli="invalid-cli", model="gpt-4")
        assert "cli" in str(exc_info.value)

    def test_invalid_stance_raises_error(self):
        """Test that invalid stance raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Participant(cli="codex", model="gpt-4", stance="maybe")
        assert "stance" in str(exc_info.value)


class TestDeliberateRequest:
    """Tests for DeliberateRequest model."""

    def test_valid_request_minimal(self):
        """Test valid request with minimal fields."""
        req = DeliberateRequest(
            question="Should we use TypeScript?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
                Participant(cli="codex", model="gpt-4"),
            ]
        )
        assert req.question == "Should we use TypeScript?"
        assert len(req.participants) == 2
        assert req.rounds == 2  # Default
        assert req.mode == "quick"  # Default

    def test_valid_request_full(self):
        """Test valid request with all fields."""
        req = DeliberateRequest(
            question="Should we refactor?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet-20241022", stance="for"),
                Participant(cli="codex", model="gpt-4", stance="against"),
            ],
            rounds=3,
            mode="conference",
            context="Legacy codebase, 50K LOC"
        )
        assert req.rounds == 3
        assert req.mode == "conference"
        assert req.context == "Legacy codebase, 50K LOC"

    def test_requires_at_least_two_participants(self):
        """Test that at least 2 participants are required."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[Participant(cli="codex", model="gpt-4")]
            )
        assert "participants" in str(exc_info.value)

    def test_rounds_must_be_positive(self):
        """Test that rounds must be >= 1."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[
                    Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
                    Participant(cli="codex", model="gpt-4"),
                ],
                rounds=0
            )
        assert "rounds" in str(exc_info.value)

    def test_rounds_capped_at_five(self):
        """Test that rounds cannot exceed 5."""
        with pytest.raises(ValidationError) as exc_info:
            DeliberateRequest(
                question="Test?",
                participants=[
                    Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
                    Participant(cli="codex", model="gpt-4"),
                ],
                rounds=10
            )
        assert "rounds" in str(exc_info.value)


class TestRoundResponse:
    """Tests for RoundResponse model."""

    def test_valid_round_response(self):
        """Test creating a valid round response."""
        resp = RoundResponse(
            round=1,
            participant="claude-3-5-sonnet@claude-code",
            stance="neutral",
            response="I think we should consider...",
            timestamp="2025-10-12T15:30:00Z"
        )
        assert resp.round == 1
        assert "claude-3-5-sonnet" in resp.participant


class TestDeliberationResult:
    """Tests for DeliberationResult model."""

    def test_valid_result(self):
        """Test creating a valid deliberation result."""
        result = DeliberationResult(
            status="complete",
            mode="conference",
            rounds_completed=2,
            participants=["claude-3-5-sonnet@claude-code", "gpt-4@codex"],
            summary={
                "consensus": "Strong agreement",
                "key_agreements": ["Point 1", "Point 2"],
                "key_disagreements": ["Detail A"],
                "final_recommendation": "Proceed with approach X"
            },
            transcript_path="/path/to/transcript.md",
            full_debate=[]
        )
        assert result.status == "complete"
        assert result.rounds_completed == 2
```

**Run the test (it should fail - RED):**
```bash
pytest tests/unit/test_models.py -v
# Expected: ModuleNotFoundError: No module named 'models.schema'
```

2. **Now write the implementation**

**File:** `models/schema.py`

```python
"""Pydantic models for AI Counsel."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Participant(BaseModel):
    """Model representing a deliberation participant."""

    cli: Literal["claude-code", "codex"] = Field(
        ...,
        description="CLI tool to use for this participant"
    )
    model: str = Field(
        ...,
        description="Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'gpt-4')"
    )
    stance: Literal["neutral", "for", "against"] = Field(
        default="neutral",
        description="Stance for this participant"
    )


class DeliberateRequest(BaseModel):
    """Model for deliberation request."""

    question: str = Field(
        ...,
        min_length=10,
        description="The question or proposal to deliberate on"
    )
    participants: list[Participant] = Field(
        ...,
        min_length=2,
        description="List of participants (minimum 2)"
    )
    rounds: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of deliberation rounds (1-5)"
    )
    mode: Literal["quick", "conference"] = Field(
        default="quick",
        description="Deliberation mode"
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional additional context"
    )


class RoundResponse(BaseModel):
    """Model for a single round response from a participant."""

    round: int = Field(..., description="Round number")
    participant: str = Field(..., description="Participant identifier")
    stance: str = Field(..., description="Participant's stance")
    response: str = Field(..., description="The response text")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class Summary(BaseModel):
    """Model for deliberation summary."""

    consensus: str = Field(..., description="Overall consensus description")
    key_agreements: list[str] = Field(..., description="Points of agreement")
    key_disagreements: list[str] = Field(..., description="Points of disagreement")
    final_recommendation: str = Field(..., description="Final recommendation")


class DeliberationResult(BaseModel):
    """Model for complete deliberation result."""

    status: Literal["complete", "partial", "failed"] = Field(..., description="Status")
    mode: str = Field(..., description="Mode used")
    rounds_completed: int = Field(..., description="Rounds completed")
    participants: list[str] = Field(..., description="Participant identifiers")
    summary: Summary = Field(..., description="Deliberation summary")
    transcript_path: str = Field(..., description="Path to full transcript")
    full_debate: list[RoundResponse] = Field(..., description="Full debate history")
```

**Run the test again (it should pass - GREEN):**
```bash
pytest tests/unit/test_models.py -v
# Expected: All tests pass
```

3. **Refactor if needed** (REFACTOR)

In this case, the code is clean. No refactoring needed.

**Commit:**
```bash
git add models/schema.py tests/unit/test_models.py
git commit -m "feat: add pydantic models for deliberation

- Add Participant model with CLI and stance validation
- Add DeliberateRequest model with validation (2+ participants, 1-5 rounds)
- Add RoundResponse and DeliberationResult models
- Add comprehensive unit tests with 100% coverage
- Tests validate all constraints and error cases"
```

---

### Task 1.2: Create Base Configuration Module

**Objective:** Load and validate configuration from `config.yaml`.

**Files:**
- `config.yaml` (create)
- `models/config.py` (create)
- `tests/unit/test_config.py` (create)

**Step-by-Step:**

1. **Create `config.yaml`**

```yaml
# ai-counsel/config.yaml
version: "1.0"

cli_tools:
  claude-code:
    command: "claude-code"
    args: ["--model", "{model}", "--prompt", "{prompt}"]
    timeout: 60

  codex:
    command: "codex"
    args: ["--model", "{model}", "{prompt}"]
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

2. **Write test FIRST**

**File:** `tests/unit/test_config.py`

```python
"""Unit tests for configuration loading."""
import pytest
from pathlib import Path
from models.config import load_config, Config


class TestConfigLoading:
    """Tests for config loading."""

    def test_load_default_config(self):
        """Test loading default config.yaml."""
        config = load_config()
        assert config is not None
        assert config.version == "1.0"
        assert "claude-code" in config.cli_tools
        assert "codex" in config.cli_tools

    def test_cli_tool_config_structure(self):
        """Test CLI tool config has required fields."""
        config = load_config()
        claude = config.cli_tools["claude-code"]
        assert claude.command == "claude-code"
        assert isinstance(claude.args, list)
        assert claude.timeout == 60

    def test_defaults_loaded(self):
        """Test default settings are loaded."""
        config = load_config()
        assert config.defaults.mode == "quick"
        assert config.defaults.rounds == 2
        assert config.defaults.max_rounds == 5

    def test_storage_config_loaded(self):
        """Test storage configuration is loaded."""
        config = load_config()
        assert config.storage.transcripts_dir == "transcripts"
        assert config.storage.format == "markdown"
        assert config.storage.auto_export is True

    def test_invalid_config_path_raises_error(self):
        """Test that invalid config path raises error."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
```

**Run test (RED):**
```bash
pytest tests/unit/test_config.py -v
# Expected: ModuleNotFoundError
```

3. **Implement config module**

**File:** `models/config.py`

```python
"""Configuration loading and validation."""
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class CLIToolConfig(BaseModel):
    """Configuration for a single CLI tool."""
    command: str
    args: list[str]
    timeout: int


class DefaultsConfig(BaseModel):
    """Default settings."""
    mode: str
    rounds: int
    max_rounds: int
    timeout_per_round: int


class StorageConfig(BaseModel):
    """Storage configuration."""
    transcripts_dir: str
    format: str
    auto_export: bool


class DeliberationConfig(BaseModel):
    """Deliberation engine configuration."""
    convergence_threshold: float
    enable_convergence_detection: bool


class Config(BaseModel):
    """Root configuration model."""
    version: str
    cli_tools: dict[str, CLIToolConfig]
    defaults: DefaultsConfig
    storage: StorageConfig
    deliberation: DeliberationConfig


def load_config(path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config file (default: config.yaml)

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return Config(**data)
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_config.py -v
# Expected: All tests pass
```

**Commit:**
```bash
git add config.yaml models/config.py tests/unit/test_config.py
git commit -m "feat: add configuration loading with validation

- Create config.yaml with CLI tool, storage, and deliberation settings
- Add Config pydantic models with nested structures
- Add load_config() function with error handling
- Add comprehensive tests for config loading and validation"
```

---

## Phase 2: CLI Adapters

### Task 2.1: Implement Base CLI Adapter

**Objective:** Create abstract base class for CLI adapters with subprocess management.

**Files:**
- `adapters/base.py`
- `tests/unit/test_adapters.py`

**Step-by-Step:**

1. **Write test FIRST**

**File:** `tests/unit/test_adapters.py`

```python
"""Unit tests for CLI adapters."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from adapters.base import BaseCLIAdapter
from adapters.claude_code import ClaudeCodeAdapter


class TestBaseCLIAdapter:
    """Tests for BaseCLIAdapter."""

    def test_cannot_instantiate_base_adapter(self):
        """Test that base adapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCLIAdapter(command="test", args=[], timeout=60)

    def test_subclass_must_implement_parse_output(self):
        """Test that subclasses must implement parse_output."""
        class IncompleteAdapter(BaseCLIAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter(command="test", args=[], timeout=60)


@pytest.mark.asyncio
class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = ClaudeCodeAdapter(timeout=90)
        assert adapter.command == "claude-code"
        assert adapter.timeout == 90

    @patch('adapters.claude_code.asyncio.create_subprocess_exec')
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"Claude Code output\n\nActual model response here",
            b""
        ))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCodeAdapter()
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="claude-3-5-sonnet-20241022"
        )

        assert result == "Actual model response here"
        mock_subprocess.assert_called_once()

    @patch('adapters.claude_code.asyncio.create_subprocess_exec')
    async def test_invoke_timeout(self, mock_subprocess):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCodeAdapter(timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test", "model")

        assert "timed out" in str(exc_info.value).lower()

    @patch('adapters.claude_code.asyncio.create_subprocess_exec')
    async def test_invoke_process_error(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"",
            b"Error: Model not found"
        ))
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCodeAdapter()

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test", "model")

        assert "failed" in str(exc_info.value).lower()

    def test_parse_output_extracts_response(self):
        """Test output parsing extracts model response."""
        adapter = ClaudeCodeAdapter()

        raw_output = """
        Claude Code v1.0
        Loading model...

        Here is the actual response from the model.
        This is what we want to extract.
        """

        result = adapter.parse_output(raw_output)
        assert "actual response" in result
        assert "Claude Code v1.0" not in result
        assert "Loading model" not in result
```

**Run test (RED):**
```bash
pytest tests/unit/test_adapters.py -v
# Expected: Import errors
```

2. **Implement base adapter**

**File:** `adapters/base.py`

```python
"""Base CLI adapter with subprocess management."""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional


class BaseCLIAdapter(ABC):
    """
    Abstract base class for CLI tool adapters.

    Handles subprocess execution, timeout management, and error handling.
    Subclasses must implement parse_output() for tool-specific parsing.
    """

    def __init__(self, command: str, args: list[str], timeout: int = 60):
        """
        Initialize CLI adapter.

        Args:
            command: CLI command to execute
            args: List of argument templates (may contain {model}, {prompt} placeholders)
            timeout: Timeout in seconds (default: 60)
        """
        self.command = command
        self.args = args
        self.timeout = timeout

    async def invoke(self, prompt: str, model: str, context: Optional[str] = None) -> str:
        """
        Invoke the CLI tool with the given prompt and model.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context

        Returns:
            Parsed response from the model

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If CLI process fails
        """
        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"

        # Format arguments
        formatted_args = [
            arg.format(model=model, prompt=full_prompt)
            for arg in self.args
        ]

        # Execute subprocess
        try:
            process = await asyncio.create_subprocess_exec(
                self.command,
                *formatted_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise RuntimeError(f"CLI process failed: {error_msg}")

            raw_output = stdout.decode('utf-8', errors='replace')
            return self.parse_output(raw_output)

        except asyncio.TimeoutError:
            raise TimeoutError(f"CLI invocation timed out after {self.timeout}s")

    @abstractmethod
    def parse_output(self, raw_output: str) -> str:
        """
        Parse raw CLI output to extract model response.

        Must be implemented by subclasses based on their output format.

        Args:
            raw_output: Raw stdout from CLI tool

        Returns:
            Parsed model response text
        """
        pass
```

**Run test (should still be RED - ClaudeCodeAdapter not implemented):**
```bash
pytest tests/unit/test_adapters.py::TestBaseCLIAdapter -v
# Expected: Should pass
pytest tests/unit/test_adapters.py::TestClaudeCodeAdapter -v
# Expected: Import error
```

3. **Implement ClaudeCodeAdapter**

**File:** `adapters/claude_code.py`

```python
"""Claude Code CLI adapter."""
from adapters.base import BaseCLIAdapter


class ClaudeCodeAdapter(BaseCLIAdapter):
    """Adapter for claude-code CLI tool."""

    def __init__(self, timeout: int = 60):
        """
        Initialize Claude Code adapter.

        Args:
            timeout: Timeout in seconds (default: 60)
        """
        super().__init__(
            command="claude-code",
            args=["--model", "{model}", "--prompt", "{prompt}"],
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        """
        Parse claude-code output.

        Claude code typically outputs:
        - Header/initialization text
        - Blank lines
        - Actual model response

        We extract everything after the first substantial block of text.

        Args:
            raw_output: Raw stdout from claude-code

        Returns:
            Parsed model response
        """
        lines = raw_output.strip().split('\n')

        # Skip header lines (typically start with "Claude Code", "Loading", etc.)
        # Find first line that looks like model output (substantial content)
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not any(
                keyword in line.lower()
                for keyword in ['claude code', 'loading', 'version', 'initializing']
            ):
                start_idx = i
                break

        # Join remaining lines
        response = '\n'.join(lines[start_idx:]).strip()
        return response
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_adapters.py -v
# Expected: All tests pass
```

**Commit:**
```bash
git add adapters/base.py adapters/claude_code.py tests/unit/test_adapters.py
git commit -m "feat: implement base CLI adapter and claude-code adapter

- Add BaseCLIAdapter with subprocess management and timeout handling
- Add ClaudeCodeAdapter with output parsing
- Handle timeouts, process errors, and edge cases
- Add comprehensive unit tests with mocked subprocesses
- Tests cover success, timeout, and error scenarios"
```

---

### Task 2.2: Implement Codex Adapter

**Objective:** Add Codex CLI adapter.

**Files:**
- `adapters/codex.py`
- Update `tests/unit/test_adapters.py`

**Step-by-Step:**

1. **Add tests FIRST**

**File:** `tests/unit/test_adapters.py` (add to existing file)

```python
# Add these imports at top
from adapters.codex import CodexAdapter

# Add this class after TestClaudeCodeAdapter
@pytest.mark.asyncio
class TestCodexAdapter:
    """Tests for CodexAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes with correct values."""
        adapter = CodexAdapter(timeout=90)
        assert adapter.command == "codex"
        assert adapter.timeout == 90

    @patch('adapters.codex.asyncio.create_subprocess_exec')
    async def test_invoke_success(self, mock_subprocess):
        """Test successful CLI invocation."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(
            b"Codex Output\nModel: gpt-4\n\nThis is the response",
            b""
        ))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = CodexAdapter()
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="gpt-4"
        )

        assert result == "This is the response"
        mock_subprocess.assert_called_once()

    def test_parse_output_extracts_response(self):
        """Test output parsing extracts model response."""
        adapter = CodexAdapter()

        raw_output = """
        Codex v2.0
        Model: gpt-4

        This is the actual response.
        Multiple lines here.
        """

        result = adapter.parse_output(raw_output)
        assert "actual response" in result
        assert "Codex v2.0" not in result
```

**Run test (RED):**
```bash
pytest tests/unit/test_adapters.py::TestCodexAdapter -v
# Expected: Import error
```

2. **Implement CodexAdapter**

**File:** `adapters/codex.py`

```python
"""Codex CLI adapter."""
from adapters.base import BaseCLIAdapter


class CodexAdapter(BaseCLIAdapter):
    """Adapter for codex CLI tool."""

    def __init__(self, timeout: int = 60):
        """
        Initialize Codex adapter.

        Args:
            timeout: Timeout in seconds (default: 60)
        """
        super().__init__(
            command="codex",
            args=["--model", "{model}", "{prompt}"],
            timeout=timeout
        )

    def parse_output(self, raw_output: str) -> str:
        """
        Parse codex output.

        Codex typically outputs:
        - Header with version/model info
        - Blank line
        - Model response

        Args:
            raw_output: Raw stdout from codex

        Returns:
            Parsed model response
        """
        lines = raw_output.strip().split('\n')

        # Skip header lines
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not any(
                keyword in line.lower()
                for keyword in ['codex', 'model:', 'version']
            ):
                start_idx = i
                break

        response = '\n'.join(lines[start_idx:]).strip()
        return response
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_adapters.py::TestCodexAdapter -v
# Expected: All tests pass
```

3. **Create adapter factory**

**File:** `adapters/__init__.py`

```python
"""CLI adapters for AI Counsel."""
from adapters.claude_code import ClaudeCodeAdapter
from adapters.codex import CodexAdapter
from models.config import CLIToolConfig


def create_adapter(cli_name: str, config: CLIToolConfig):
    """
    Factory function to create appropriate adapter.

    Args:
        cli_name: Name of CLI tool ('claude-code' or 'codex')
        config: CLI tool configuration

    Returns:
        Instantiated adapter

    Raises:
        ValueError: If cli_name is not supported
    """
    adapters = {
        "claude-code": ClaudeCodeAdapter,
        "codex": CodexAdapter,
    }

    if cli_name not in adapters:
        raise ValueError(f"Unsupported CLI tool: {cli_name}")

    return adapters[cli_name](timeout=config.timeout)


__all__ = [
    "BaseCLIAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "create_adapter",
]
```

**Commit:**
```bash
git add adapters/codex.py adapters/__init__.py tests/unit/test_adapters.py
git commit -m "feat: add codex adapter and adapter factory

- Implement CodexAdapter with output parsing
- Add create_adapter() factory function
- Add tests for CodexAdapter
- Update __init__.py with all exports"
```

---

## Phase 3: Deliberation Engine

### Task 3.1: Implement Single-Round Execution

**Objective:** Execute one round of deliberation where each participant responds to the question.

**Files:**
- `deliberation/engine.py`
- `tests/unit/test_engine.py`

**Why Single Round First:** Build incrementally. Get one round working, then add multi-round logic.

**Step-by-Step:**

1. **Write test FIRST**

**File:** `tests/unit/test_engine.py`

```python
"""Unit tests for deliberation engine."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from deliberation.engine import DeliberationEngine
from models.schema import Participant, DeliberateRequest


@pytest.fixture
def mock_adapters():
    """Fixture providing mocked adapters."""
    claude_mock = Mock()
    claude_mock.invoke = AsyncMock(return_value="Claude response")

    codex_mock = Mock()
    codex_mock.invoke = AsyncMock(return_value="Codex response")

    return {
        "claude-code": claude_mock,
        "codex": codex_mock,
    }


@pytest.mark.asyncio
class TestDeliberationEngine:
    """Tests for DeliberationEngine."""

    async def test_single_round_execution(self, mock_adapters):
        """Test executing a single round of deliberation."""
        request = DeliberateRequest(
            question="Should we use TypeScript?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
                Participant(cli="codex", model="gpt-4"),
            ],
            rounds=1,
            mode="quick"
        )

        engine = DeliberationEngine(adapters=mock_adapters)
        result = await engine.execute_round(request, round_num=1, previous_responses=[])

        assert len(result) == 2
        assert result[0].round == 1
        assert result[0].response == "Claude response"
        assert result[1].response == "Codex response"

        # Verify both adapters were called
        mock_adapters["claude-code"].invoke.assert_called_once()
        mock_adapters["codex"].invoke.assert_called_once()

    async def test_single_round_with_context(self, mock_adapters):
        """Test round execution includes context if provided."""
        request = DeliberateRequest(
            question="Should we refactor?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
            ],
            rounds=1,
            context="Legacy codebase, 50K LOC"
        )

        engine = DeliberationEngine(adapters=mock_adapters)
        await engine.execute_round(request, round_num=1, previous_responses=[])

        # Verify context was passed
        call_args = mock_adapters["claude-code"].invoke.call_args
        assert call_args.kwargs.get("context") == "Legacy codebase, 50K LOC"

    async def test_round_handles_adapter_failure(self, mock_adapters):
        """Test that engine handles individual adapter failures gracefully."""
        # Make one adapter fail
        mock_adapters["codex"].invoke = AsyncMock(side_effect=RuntimeError("Model error"))

        request = DeliberateRequest(
            question="Test?",
            participants=[
                Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
                Participant(cli="codex", model="gpt-4"),
            ],
            rounds=1
        )

        engine = DeliberationEngine(adapters=mock_adapters)
        result = await engine.execute_round(request, round_num=1, previous_responses=[])

        # Should have 1 successful response, 1 error
        assert len(result) == 2
        assert result[0].response == "Claude response"
        assert "error" in result[1].response.lower()
```

**Run test (RED):**
```bash
pytest tests/unit/test_engine.py -v
# Expected: Import error
```

2. **Implement engine (single round only)**

**File:** `deliberation/engine.py`

```python
"""Deliberation engine for orchestrating multi-round debates."""
import asyncio
from datetime import datetime
from typing import Optional
from models.schema import DeliberateRequest, RoundResponse


class DeliberationEngine:
    """
    Engine for executing deliberation rounds.

    Orchestrates calling multiple AI models through their CLI adapters,
    manages response threading, and handles errors gracefully.
    """

    def __init__(self, adapters: dict):
        """
        Initialize engine with CLI adapters.

        Args:
            adapters: Dict mapping cli_name -> adapter instance
        """
        self.adapters = adapters

    async def execute_round(
        self,
        request: DeliberateRequest,
        round_num: int,
        previous_responses: list[RoundResponse]
    ) -> list[RoundResponse]:
        """
        Execute a single round of deliberation.

        In round 1, participants see only the question.
        In subsequent rounds, participants see previous round responses.

        Args:
            request: Deliberation request
            round_num: Current round number (1-indexed)
            previous_responses: Responses from previous rounds

        Returns:
            List of responses from this round
        """
        # Build prompt
        prompt = self._build_prompt(request.question, previous_responses, round_num)

        # Execute all participants in parallel
        tasks = []
        for participant in request.participants:
            task = self._invoke_participant(
                participant=participant,
                prompt=prompt,
                context=request.context,
                round_num=round_num
            )
            tasks.append(task)

        # Wait for all to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        round_responses = []
        for i, (participant, response) in enumerate(zip(request.participants, responses)):
            if isinstance(response, Exception):
                # Handle error gracefully
                round_responses.append(
                    RoundResponse(
                        round=round_num,
                        participant=f"{participant.model}@{participant.cli}",
                        stance=participant.stance,
                        response=f"[ERROR: {str(response)}]",
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    )
                )
            else:
                round_responses.append(response)

        return round_responses

    async def _invoke_participant(
        self,
        participant,
        prompt: str,
        context: Optional[str],
        round_num: int
    ) -> RoundResponse:
        """
        Invoke a single participant.

        Args:
            participant: Participant model
            prompt: Prompt to send
            context: Optional context
            round_num: Current round number

        Returns:
            RoundResponse
        """
        adapter = self.adapters[participant.cli]

        # Call adapter
        response_text = await adapter.invoke(
            prompt=prompt,
            model=participant.model,
            context=context
        )

        return RoundResponse(
            round=round_num,
            participant=f"{participant.model}@{participant.cli}",
            stance=participant.stance,
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    def _build_prompt(
        self,
        question: str,
        previous_responses: list[RoundResponse],
        round_num: int
    ) -> str:
        """
        Build prompt for this round.

        Round 1: Just the question
        Round 2+: Question + previous responses

        Args:
            question: Original question
            previous_responses: Responses from previous rounds
            round_num: Current round number

        Returns:
            Formatted prompt
        """
        if round_num == 1 or not previous_responses:
            return question

        # Build prompt with previous responses
        prompt_parts = [
            "QUESTION:",
            question,
            "",
            "PREVIOUS RESPONSES:",
        ]

        for resp in previous_responses:
            prompt_parts.append(f"\n**{resp.participant}** ({resp.stance}):")
            prompt_parts.append(resp.response)
            prompt_parts.append("")

        prompt_parts.append("YOUR RESPONSE:")
        prompt_parts.append("Please provide your perspective, addressing points raised above.")

        return "\n".join(prompt_parts)
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_engine.py -v
# Expected: All tests pass
```

**Commit:**
```bash
git add deliberation/engine.py tests/unit/test_engine.py
git commit -m "feat: implement single-round deliberation engine

- Add DeliberationEngine with execute_round() method
- Implement parallel participant invocation
- Add prompt building with previous response threading
- Handle adapter failures gracefully
- Add comprehensive unit tests with mocked adapters"
```

---

### Task 3.2: Implement Multi-Round Orchestration

**Objective:** Add ability to execute multiple rounds sequentially.

**Files:**
- Update `deliberation/engine.py`
- Update `tests/unit/test_engine.py`

**Step-by-Step:**

1. **Add test FIRST**

**File:** `tests/unit/test_engine.py` (add to existing)

```python
# Add to TestDeliberationEngine class
@pytest.mark.asyncio
async def test_multi_round_execution(self, mock_adapters):
    """Test executing multiple rounds."""
    # Make adapters return different responses per call
    claude_responses = ["Claude round 1", "Claude round 2"]
    codex_responses = ["Codex round 1", "Codex round 2"]

    mock_adapters["claude-code"].invoke = AsyncMock(side_effect=claude_responses)
    mock_adapters["codex"].invoke = AsyncMock(side_effect=codex_responses)

    request = DeliberateRequest(
        question="Should we use TypeScript?",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
            Participant(cli="codex", model="gpt-4"),
        ],
        rounds=2,
        mode="conference"
    )

    engine = DeliberationEngine(adapters=mock_adapters)
    result = await engine.execute(request)

    assert result.rounds_completed == 2
    assert len(result.full_debate) == 4  # 2 rounds x 2 participants

    # Verify round 2 participants saw round 1 responses
    round_2_call = mock_adapters["claude-code"].invoke.call_args_list[1]
    prompt_arg = round_2_call.kwargs["prompt"]
    assert "PREVIOUS RESPONSES" in prompt_arg
    assert "Claude round 1" in prompt_arg or "Codex round 1" in prompt_arg

@pytest.mark.asyncio
async def test_quick_mode_single_round(self, mock_adapters):
    """Test quick mode executes only 1 round regardless of config."""
    request = DeliberateRequest(
        question="Test?",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
        ],
        rounds=3,  # Request 3 but mode is quick
        mode="quick"
    )

    engine = DeliberationEngine(adapters=mock_adapters)
    result = await engine.execute(request)

    # Quick mode should override rounds config
    assert result.rounds_completed == 1
```

**Run test (RED):**
```bash
pytest tests/unit/test_engine.py::TestDeliberationEngine::test_multi_round_execution -v
# Expected: AttributeError (execute method doesn't exist)
```

2. **Implement multi-round execution**

**File:** `deliberation/engine.py` (add to class)

```python
# Add this method to DeliberationEngine class

async def execute(self, request: DeliberateRequest) -> "DeliberationResult":
    """
    Execute full deliberation with multiple rounds.

    Args:
        request: Deliberation request

    Returns:
        Complete deliberation result
    """
    from models.schema import DeliberationResult, Summary

    # Determine actual rounds to execute
    if request.mode == "quick":
        rounds_to_execute = 1
    else:
        rounds_to_execute = request.rounds

    # Execute rounds sequentially
    all_responses = []
    for round_num in range(1, rounds_to_execute + 1):
        round_responses = await self.execute_round(
            request=request,
            round_num=round_num,
            previous_responses=all_responses
        )
        all_responses.extend(round_responses)

    # Generate summary (placeholder for now)
    summary = Summary(
        consensus="Generated summary placeholder",
        key_agreements=["Agreement 1", "Agreement 2"],
        key_disagreements=["Disagreement 1"],
        final_recommendation="Recommendation placeholder"
    )

    # Build participant list
    participant_ids = [
        f"{p.model}@{p.cli}"
        for p in request.participants
    ]

    return DeliberationResult(
        status="complete",
        mode=request.mode,
        rounds_completed=rounds_to_execute,
        participants=participant_ids,
        summary=summary,
        transcript_path="",  # Will be set by transcript manager
        full_debate=all_responses
    )
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_engine.py -v
# Expected: All tests pass
```

**Commit:**
```bash
git add deliberation/engine.py tests/unit/test_engine.py
git commit -m "feat: add multi-round deliberation execution

- Implement execute() method for full deliberation workflow
- Add sequential round execution with response threading
- Handle quick mode (1 round) vs conference mode (N rounds)
- Add tests for multi-round execution and mode handling"
```

---

## Phase 4: MCP Server Integration

### Task 4.1: Create MCP Server with `deliberate()` Tool

**Objective:** Wire up MCP server that exposes the `deliberate()` tool.

**Files:**
- `server.py`
- `tests/integration/test_mcp_server.py`

**Step-by-Step:**

1. **Create basic server structure**

**File:** `server.py`

```python
"""AI Counsel MCP Server."""
import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

from models.config import load_config
from models.schema import DeliberateRequest, DeliberationResult
from adapters import create_adapter
from deliberation.engine import DeliberationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize server
app = Server("ai-counsel")


# Load configuration
try:
    config = load_config()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load config: {e}")
    raise


# Create adapters
adapters = {}
for cli_name, cli_config in config.cli_tools.items():
    try:
        adapters[cli_name] = create_adapter(cli_name, cli_config)
        logger.info(f"Initialized adapter: {cli_name}")
    except Exception as e:
        logger.error(f"Failed to create adapter for {cli_name}: {e}")


# Create engine
engine = DeliberationEngine(adapters=adapters)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="deliberate",
            description=(
                "Initiate true deliberative consensus where AI models debate and "
                "refine positions across multiple rounds. Models see each other's "
                "responses and can adjust their reasoning. Use for critical decisions, "
                "architecture choices, or complex technical debates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or proposal for the models to deliberate on",
                        "minLength": 10
                    },
                    "participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cli": {
                                    "type": "string",
                                    "enum": ["claude-code", "codex"],
                                    "description": "CLI tool to use"
                                },
                                "model": {
                                    "type": "string",
                                    "description": "Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'gpt-4')"
                                },
                                "stance": {
                                    "type": "string",
                                    "enum": ["neutral", "for", "against"],
                                    "default": "neutral",
                                    "description": "Stance for this participant"
                                }
                            },
                            "required": ["cli", "model"]
                        },
                        "minItems": 2,
                        "description": "List of AI participants (minimum 2)"
                    },
                    "rounds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 2,
                        "description": "Number of deliberation rounds (1-5)"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "conference"],
                        "default": "quick",
                        "description": "quick = single round opinions, conference = multi-round deliberation"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional additional context (code snippets, requirements, etc.)"
                    }
                },
                "required": ["question", "participants"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "deliberate":
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Validate and parse request
        request = DeliberateRequest(**arguments)
        logger.info(f"Starting deliberation: {request.question[:50]}...")

        # Execute deliberation
        result = await engine.execute(request)
        logger.info(f"Deliberation complete: {result.rounds_completed} rounds")

        # Return result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2)
        )]

    except Exception as e:
        logger.error(f"Error in deliberation: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "status": "failed"
            })
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting AI Counsel MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

2. **Test the server manually**

```bash
# In terminal 1: Start the server
python server.py

# In terminal 2: Use MCP inspector or test client
# (For now, just verify it starts without errors)
```

3. **Add integration test**

**File:** `tests/integration/test_mcp_server.py`

```python
"""Integration tests for MCP server."""
import pytest
import json
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_server_lists_tools():
    """Test that server lists deliberate tool."""
    # This requires server to be running
    # For MVP, we'll test this manually
    # Full implementation would use mcp test utilities
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deliberate_tool_execution():
    """Test executing deliberate tool."""
    # Manual test for now
    # Would require real CLI tools installed
    pass
```

**Commit:**
```bash
git add server.py tests/integration/test_mcp_server.py
git commit -m "feat: implement MCP server with deliberate tool

- Create server.py with MCP server initialization
- Add deliberate tool registration with full schema
- Wire up DeliberationEngine to tool handler
- Add error handling and logging
- Add integration test placeholders"
```

---

## Phase 5: Transcript Management

### Task 5.1: Implement Transcript Manager

**Objective:** Save full deliberation transcripts as markdown files.

**Files:**
- `deliberation/transcript.py`
- `tests/unit/test_transcript.py`

**Step-by-Step:**

1. **Write test FIRST**

**File:** `tests/unit/test_transcript.py`

```python
"""Unit tests for transcript management."""
import pytest
from pathlib import Path
from deliberation.transcript import TranscriptManager
from models.schema import RoundResponse, DeliberationResult, Summary


@pytest.fixture
def sample_result():
    """Fixture providing a sample deliberation result."""
    return DeliberationResult(
        status="complete",
        mode="conference",
        rounds_completed=2,
        participants=["claude-3-5-sonnet@claude-code", "gpt-4@codex"],
        summary=Summary(
            consensus="Strong agreement on TypeScript adoption",
            key_agreements=["Better type safety", "Improved IDE support"],
            key_disagreements=["Learning curve concerns"],
            final_recommendation="Adopt TypeScript for new modules"
        ),
        transcript_path="",
        full_debate=[
            RoundResponse(
                round=1,
                participant="claude-3-5-sonnet@claude-code",
                stance="neutral",
                response="I think TypeScript offers...",
                timestamp="2025-10-12T15:30:00Z"
            ),
            RoundResponse(
                round=1,
                participant="gpt-4@codex",
                stance="for",
                response="TypeScript is excellent because...",
                timestamp="2025-10-12T15:30:05Z"
            ),
        ]
    )


class TestTranscriptManager:
    """Tests for TranscriptManager."""

    def test_generate_markdown(self, sample_result, tmp_path):
        """Test generating markdown transcript."""
        manager = TranscriptManager(output_dir=str(tmp_path))

        markdown = manager.generate_markdown(sample_result)

        assert "# AI Counsel Deliberation Transcript" in markdown
        assert "## Summary" in markdown
        assert "Strong agreement on TypeScript" in markdown
        assert "## Round 1" in markdown
        assert "claude-3-5-sonnet@claude-code" in markdown
        assert "I think TypeScript offers" in markdown

    def test_save_transcript(self, sample_result, tmp_path):
        """Test saving transcript to file."""
        manager = TranscriptManager(output_dir=str(tmp_path))

        filepath = manager.save(sample_result, question="Should we use TypeScript?")

        assert Path(filepath).exists()
        assert Path(filepath).suffix == ".md"

        # Verify content
        content = Path(filepath).read_text()
        assert "Should we use TypeScript?" in content
        assert "Strong agreement on TypeScript" in content

    def test_generates_unique_filenames(self, sample_result, tmp_path):
        """Test that multiple saves generate unique filenames."""
        manager = TranscriptManager(output_dir=str(tmp_path))

        file1 = manager.save(sample_result, "Question 1")
        file2 = manager.save(sample_result, "Question 2")

        assert file1 != file2
        assert Path(file1).exists()
        assert Path(file2).exists()
```

**Run test (RED):**
```bash
pytest tests/unit/test_transcript.py -v
# Expected: Import error
```

2. **Implement TranscriptManager**

**File:** `deliberation/transcript.py`

```python
"""Transcript management for deliberations."""
from datetime import datetime
from pathlib import Path
from typing import Optional
from models.schema import DeliberationResult


class TranscriptManager:
    """
    Manages saving deliberation transcripts.

    Generates markdown files with full debate history and summary.
    """

    def __init__(self, output_dir: str = "transcripts"):
        """
        Initialize transcript manager.

        Args:
            output_dir: Directory to save transcripts (default: transcripts/)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, result: DeliberationResult) -> str:
        """
        Generate markdown transcript from result.

        Args:
            result: Deliberation result

        Returns:
            Markdown formatted transcript
        """
        lines = [
            "# AI Counsel Deliberation Transcript",
            "",
            f"**Status:** {result.status}",
            f"**Mode:** {result.mode}",
            f"**Rounds Completed:** {result.rounds_completed}",
            f"**Participants:** {', '.join(result.participants)}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"**Consensus:** {result.summary.consensus}",
            "",
            "### Key Agreements",
            "",
        ]

        for agreement in result.summary.key_agreements:
            lines.append(f"- {agreement}")

        lines.extend([
            "",
            "### Key Disagreements",
            "",
        ])

        for disagreement in result.summary.key_disagreements:
            lines.append(f"- {disagreement}")

        lines.extend([
            "",
            f"**Final Recommendation:** {result.summary.final_recommendation}",
            "",
            "---",
            "",
            "## Full Debate",
            "",
        ])

        # Group by round
        current_round = None
        for response in result.full_debate:
            if response.round != current_round:
                current_round = response.round
                lines.extend([
                    f"### Round {current_round}",
                    "",
                ])

            lines.extend([
                f"**{response.participant}** ({response.stance})",
                "",
                response.response,
                "",
                f"*{response.timestamp}*",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)

    def save(
        self,
        result: DeliberationResult,
        question: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save deliberation transcript to file.

        Args:
            result: Deliberation result
            question: Original question
            filename: Optional custom filename (default: auto-generated)

        Returns:
            Path to saved file
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            # Create safe filename from question
            safe_question = "".join(c for c in question[:50] if c.isalnum() or c in (' ', '-', '_'))
            safe_question = safe_question.strip().replace(' ', '_')
            filename = f"{timestamp}_{safe_question}.md"

        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'

        filepath = self.output_dir / filename

        # Generate markdown with question at top
        markdown = f"# {question}\n\n" + self.generate_markdown(result)

        # Save
        filepath.write_text(markdown, encoding='utf-8')

        return str(filepath)
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_transcript.py -v
# Expected: All tests pass
```

**Commit:**
```bash
git add deliberation/transcript.py tests/unit/test_transcript.py
git commit -m "feat: implement transcript manager with markdown export

- Add TranscriptManager for saving deliberations
- Implement markdown generation with summary and full debate
- Generate unique filenames with timestamps
- Add comprehensive unit tests with tmp_path fixture"
```

---

### Task 5.2: Integrate Transcript Manager with Engine

**Objective:** Wire transcript manager into deliberation flow.

**Files:**
- Update `deliberation/engine.py`
- Update `tests/unit/test_engine.py`

**Step-by-Step:**

1. **Update engine**

**File:** `deliberation/engine.py` (modify execute method)

```python
# Add import at top
from deliberation.transcript import TranscriptManager

# Modify __init__
def __init__(self, adapters: dict, transcript_manager: Optional[TranscriptManager] = None):
    """
    Initialize engine with CLI adapters.

    Args:
        adapters: Dict mapping cli_name -> adapter instance
        transcript_manager: Optional transcript manager (creates default if None)
    """
    self.adapters = adapters
    self.transcript_manager = transcript_manager or TranscriptManager()

# Modify execute method to save transcript
async def execute(self, request: DeliberateRequest) -> "DeliberationResult":
    """
    Execute full deliberation with multiple rounds.

    Args:
        request: Deliberation request

    Returns:
        Complete deliberation result with saved transcript
    """
    from models.schema import DeliberationResult, Summary

    # ... existing code ...

    # Build participant list
    participant_ids = [
        f"{p.model}@{p.cli}"
        for p in request.participants
    ]

    # Create result
    result = DeliberationResult(
        status="complete",
        mode=request.mode,
        rounds_completed=rounds_to_execute,
        participants=participant_ids,
        summary=summary,
        transcript_path="",  # Will be set below
        full_debate=all_responses
    )

    # Save transcript
    transcript_path = self.transcript_manager.save(result, request.question)
    result.transcript_path = transcript_path

    return result
```

2. **Update test**

**File:** `tests/unit/test_engine.py` (add test)

```python
@pytest.mark.asyncio
async def test_engine_saves_transcript(self, mock_adapters, tmp_path):
    """Test that engine saves transcript after execution."""
    from deliberation.transcript import TranscriptManager

    manager = TranscriptManager(output_dir=str(tmp_path))

    request = DeliberateRequest(
        question="Should we use TypeScript?",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
        ],
        rounds=1
    )

    engine = DeliberationEngine(adapters=mock_adapters, transcript_manager=manager)
    result = await engine.execute(request)

    # Verify transcript was saved
    assert result.transcript_path
    assert Path(result.transcript_path).exists()

    # Verify content
    content = Path(result.transcript_path).read_text()
    assert "Should we use TypeScript?" in content
```

**Run test (GREEN):**
```bash
pytest tests/unit/test_engine.py::TestDeliberationEngine::test_engine_saves_transcript -v
# Expected: Pass
```

**Commit:**
```bash
git add deliberation/engine.py tests/unit/test_engine.py
git commit -m "feat: integrate transcript manager with deliberation engine

- Add transcript_manager to engine initialization
- Save transcript after deliberation completes
- Update result with transcript_path
- Add test verifying transcript save"
```

---

## Phase 6: Testing & Documentation

### Task 6.1: Write End-to-End Test

**Objective:** Create E2E test that exercises full workflow (requires real CLI tools).

**File:** `tests/e2e/test_full_deliberation.py`

```python
"""End-to-end tests for full deliberation workflow."""
import pytest
from pathlib import Path
from models.schema import DeliberateRequest, Participant
from models.config import load_config
from adapters import create_adapter
from deliberation.engine import DeliberationEngine
from deliberation.transcript import TranscriptManager


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_deliberation_workflow(tmp_path):
    """
    Full E2E test of deliberation.

    PREREQUISITES:
    - claude-code CLI must be installed
    - codex CLI must be installed
    - Both must be configured with valid API keys

    This test will make real API calls and incur costs.
    """
    # Load config
    config = load_config()

    # Create adapters
    adapters = {
        "claude-code": create_adapter("claude-code", config.cli_tools["claude-code"]),
        "codex": create_adapter("codex", config.cli_tools["codex"]),
    }

    # Create transcript manager
    transcript_manager = TranscriptManager(output_dir=str(tmp_path))

    # Create engine
    engine = DeliberationEngine(
        adapters=adapters,
        transcript_manager=transcript_manager
    )

    # Create request
    request = DeliberateRequest(
        question="What is 2+2? Please answer briefly.",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
            Participant(cli="codex", model="gpt-4"),
        ],
        rounds=2,
        mode="conference"
    )

    # Execute
    result = await engine.execute(request)

    # Verify result
    assert result.status == "complete"
    assert result.rounds_completed == 2
    assert len(result.full_debate) == 4  # 2 rounds x 2 participants

    # Verify all responses contain something about "4"
    for response in result.full_debate:
        assert "4" in response.response or "four" in response.response.lower()

    # Verify transcript exists
    assert Path(result.transcript_path).exists()
    content = Path(result.transcript_path).read_text()
    assert "What is 2+2?" in content
    assert "claude-3-5-sonnet@claude-code" in content
    assert "gpt-4@codex" in content


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_quick_mode_single_round(tmp_path):
    """Test quick mode with real CLIs."""
    config = load_config()

    adapters = {
        "claude-code": create_adapter("claude-code", config.cli_tools["claude-code"]),
    }

    engine = DeliberationEngine(
        adapters=adapters,
        transcript_manager=TranscriptManager(output_dir=str(tmp_path))
    )

    request = DeliberateRequest(
        question="What is the capital of France? Answer in one word.",
        participants=[
            Participant(cli="claude-code", model="claude-3-5-sonnet-20241022"),
        ],
        rounds=3,  # Will be overridden by quick mode
        mode="quick"
    )

    result = await engine.execute(request)

    assert result.rounds_completed == 1
    assert "paris" in result.full_debate[0].response.lower()
```

**Note:** These tests require real CLI tools. Mark them appropriately:

```bash
# Run only unit tests (fast)
pytest tests/unit -v

# Run E2E tests (slow, requires tools)
pytest tests/e2e -v -m e2e
```

**Commit:**
```bash
git add tests/e2e/test_full_deliberation.py
git commit -m "test: add end-to-end tests for full workflow

- Add E2E test exercising complete deliberation
- Test with real claude-code and codex CLIs
- Verify transcript generation
- Mark tests as e2e for selective execution"
```

---

### Task 6.2: Write README Documentation

**Objective:** Complete user-facing documentation.

**File:** `README.md` (update existing)

```markdown
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
- 🤖 **CLI-Based:** Works with claude-code, codex, and extensible to others
- 📝 **Full Transcripts:** Markdown exports with summary and complete debate
- 🎚️ **User Control:** Configure rounds, stances, and participants
- 🔍 **Transparent:** See exactly what each model said and when

## Installation

### Prerequisites

```bash
# Python 3.9+
python3 --version

# Install CLI tools you want to use
# For claude-code: https://docs.claude.com/en/docs/claude-code
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
pytest tests/unit -v
```

## Configuration

Edit `config.yaml` to configure CLI tools, timeouts, and settings:

```yaml
cli_tools:
  claude-code:
    command: "claude-code"
    args: ["--model", "{model}", "--prompt", "{prompt}"]
    timeout: 60

  codex:
    command: "codex"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60

defaults:
  mode: "quick"
  rounds: 2
  max_rounds: 5

storage:
  transcripts_dir: "transcripts"
  format: "markdown"
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
      "args": ["/path/to/ai-counsel/server.py"]
    }
  }
}
```

3. **Use the `deliberate` tool:**

```javascript
// Quick mode (1 round)
await use_mcp_tool("deliberate", {
  question: "Should we use TypeScript?",
  participants: [
    {cli: "claude-code", model: "claude-3-5-sonnet-20241022"},
    {cli: "codex", model: "gpt-4"}
  ],
  mode: "quick"
});

// Conference mode (multi-round)
await use_mcp_tool("deliberate", {
  question: "Should we refactor our authentication system?",
  participants: [
    {cli: "claude-code", model: "claude-3-5-sonnet-20241022", stance: "neutral"},
    {cli: "codex", model: "gpt-4", stance: "for"}
  ],
  rounds: 3,
  mode: "conference",
  context: "Current system: JWT tokens, 50K users"
});
```

### Transcripts

All deliberations are automatically saved to `transcripts/` as markdown:

```
transcripts/
├── 20251012_153045_Should_we_use_TypeScript.md
└── 20251012_154230_Should_we_refactor_auth.md
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
```

## Architecture

```
ai-counsel/
├── server.py              # MCP server entry point
├── config.yaml           # Configuration
├── adapters/             # CLI tool adapters
│   ├── base.py          # Abstract base
│   ├── claude_code.py   # Claude Code adapter
│   └── codex.py         # Codex adapter
├── deliberation/         # Core engine
│   ├── engine.py        # Orchestration
│   ├── transcript.py    # Markdown generation
│   └── convergence.py   # Future: convergence detection
├── models/               # Data models
│   ├── schema.py        # Pydantic models
│   └── config.py        # Config loading
└── tests/               # Test suite
```

## Principles

- **DRY**: No code duplication
- **YAGNI**: Build only what's needed
- **TDD**: Tests first, implementation second
- **Simple**: Prefer simple solutions over clever ones

## Roadmap

### MVP (Current)
- ✅ claude-code and codex adapters
- ✅ Quick and conference modes
- ✅ Markdown transcripts
- ✅ MCP server integration

### Future
- [ ] Convergence detection (auto-stop when opinions stabilize)
- [ ] Semantic similarity for better summary generation
- [ ] More CLI tool adapters
- [ ] Web UI for viewing transcripts
- [ ] Structured voting mechanisms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD)
4. Implement feature
5. Ensure all tests pass
6. Submit PR with clear description

## License

MIT License - see LICENSE file

## Credits

Built with:
- [MCP SDK](https://modelcontextprotocol.io/) - Model Context Protocol
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [pytest](https://pytest.org/) - Testing

Inspired by the need for true deliberative AI consensus beyond parallel opinion gathering.
```

**Commit:**
```bash
git add README.md
git commit -m "docs: complete README with usage and architecture

- Add comprehensive installation instructions
- Document usage as MCP server
- Add examples for quick and conference modes
- Document development workflow
- Add architecture diagram and principles
- Document extensibility for new CLI tools"
```

---

## Testing Guidelines

### Test Structure

**Good Test Structure (AAA Pattern):**

```python
def test_something():
    # Arrange - Set up test data
    adapter = ClaudeCodeAdapter(timeout=30)

    # Act - Execute the code under test
    result = adapter.parse_output("raw output")

    # Assert - Verify the result
    assert result == "expected"
```

**Test Naming:**
- Use descriptive names: `test_adapter_handles_timeout_gracefully`
- Not: `test_1`, `test_adapter`

### Mocking Guidelines

**When to Mock:**
- External dependencies (API calls, subprocess, file I/O)
- Slow operations
- Non-deterministic behavior

**What NOT to Mock:**
- The code you're testing
- Simple data structures

**Good Mock Example:**

```python
@patch('adapters.claude_code.asyncio.create_subprocess_exec')
async def test_invoke_success(self, mock_subprocess):
    # Mock the subprocess
    mock_process = Mock()
    mock_process.communicate = AsyncMock(return_value=(b"output", b""))
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    # Test your code
    adapter = ClaudeCodeAdapter()
    result = await adapter.invoke("prompt", "model")

    # Verify
    assert result == "parsed output"
    mock_subprocess.assert_called_once()
```

### Test Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Cover happy path
- **E2E Tests**: 1-2 critical workflows

**Check Coverage:**

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Commit Strategy

### Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding tests
- `refactor`: Code restructuring
- `docs`: Documentation
- `chore`: Maintenance (dependencies, config)
- `style`: Formatting (no code change)

**Examples:**

```bash
# Good commits
git commit -m "feat: add claude-code adapter with timeout handling"
git commit -m "test: add unit tests for deliberation engine"
git commit -m "fix: handle empty responses in transcript generation"
git commit -m "docs: add installation instructions to README"

# Bad commits
git commit -m "updates"
git commit -m "fixed stuff"
git commit -m "WIP"
```

### Commit Frequency

**Commit after every GREEN test:**

1. Write test (RED)
2. Implement minimum code (GREEN)
3. **COMMIT** ✅
4. Refactor (still GREEN)
5. **COMMIT** ✅

**Small, focused commits** are better than large ones.

---

## Resources

### Official Documentation
- [MCP Documentation](https://modelcontextprotocol.io/introduction)
- [MCP Python SDK](https://github.com/anthropics/mcp-python)
- [Pydantic V2 Docs](https://docs.pydantic.dev/latest/)
- [pytest Documentation](https://docs.pytest.org/)
- [asyncio Guide](https://docs.python.org/3/library/asyncio.html)

### Code Examples
- [MCP Python Examples](https://github.com/anthropics/mcp-python/tree/main/examples)
- [Zen MCP Server](https://github.com/BeehiveInnovations/zen-mcp-server) - Reference (but remember: they do parallel, we do deliberative)

### Testing Resources
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### Python Best Practices
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [Async/Await Tutorial](https://realpython.com/async-io-python/)

---

## Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError`**
```bash
# Solution: Activate virtual environment
source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Issue: Tests failing with `asyncio` errors**
```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Verify pytest.ini has:
# asyncio_mode = auto
```

**Issue: Adapter timeout errors**
```bash
# Solution: Increase timeout in config.yaml
cli_tools:
  claude-code:
    timeout: 120  # Increase from 60
```

**Issue: Transcript files not being created**
```bash
# Solution: Check directory permissions
mkdir -p transcripts
chmod 755 transcripts
```

---

## Development Workflow

### Daily Workflow

1. **Start each day:**
```bash
source .venv/bin/activate
git pull origin main
pytest tests/unit -v  # Sanity check
```

2. **Before starting new task:**
```bash
git checkout -b feature/your-feature-name
```

3. **While working:**
   - Write test (RED)
   - Write code (GREEN)
   - Commit
   - Refactor
   - Commit

4. **Before pushing:**
```bash
pytest tests/unit -v  # All must pass
black .               # Format
ruff check .         # Lint
```

5. **Push and PR:**
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

### Review Checklist

Before submitting code:
- [ ] All tests pass
- [ ] Added tests for new code
- [ ] Code is formatted (black)
- [ ] No linting errors (ruff)
- [ ] Docstrings added
- [ ] README updated (if needed)
- [ ] Commit messages follow convention
- [ ] No TODO or FIXME comments (use issues instead)

---

## Success Metrics

### MVP Complete When:

- [ ] All Phase 1-6 tasks completed
- [ ] Unit test coverage > 90%
- [ ] Integration tests pass with real CLIs
- [ ] E2E test demonstrates full workflow
- [ ] README has complete usage instructions
- [ ] Can deliberate with 2+ models
- [ ] Both quick and conference modes work
- [ ] Transcripts save correctly
- [ ] MCP server starts without errors
- [ ] Tool appears in MCP inspector

### Quality Gates:

```bash
# Must pass before considering MVP done
pytest tests/unit -v                    # 100% pass
pytest tests/integration -v -m integration  # All pass
pytest --cov=. --cov-report=term-missing    # >90% coverage
black --check .                         # No formatting needed
ruff check .                           # No lint errors
```

---

## Next Steps After MVP

Once MVP is complete and working:

1. **User Testing**
   - Use it yourself for real decisions
   - Gather feedback on transcript readability
   - Identify pain points

2. **Performance Optimization**
   - Profile slow operations
   - Add caching if needed
   - Optimize prompt building

3. **Advanced Features**
   - Convergence detection algorithm
   - Better summary generation (embeddings)
   - More CLI adapters

4. **Production Readiness**
   - Error handling edge cases
   - Rate limiting
   - Logging improvements
   - Metrics/observability

---

**END OF IMPLEMENTATION PLAN**

This plan should be treated as a living document. Update it as you learn and discover better approaches. The key is to:

1. Follow TDD religiously
2. Make small, frequent commits
3. Keep scope minimal (YAGNI)
4. Test everything
5. Document as you go

Good luck! You got this. 🚀
