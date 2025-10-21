# Adding Adapters: CLI and HTTP

This guide explains how to add new adapters to AI Counsel, enabling integration with additional AI model providers. AI Counsel supports two types of adapters: **CLI adapters** (for command-line tools) and **HTTP adapters** (for HTTP API endpoints).

## Overview

### Adapter Types

AI Counsel uses adapters to invoke AI models in deliberations. There are two types of adapters, each with distinct characteristics:

#### CLI Adapters

CLI adapters invoke command-line tools installed on your system (e.g., `claude`, `codex`, `droid`, `gemini`).

**Pros:**
- Use official CLI tools with full authentication handled automatically
- Leverage existing CLI installations and configurations
- Access to all CLI-specific features and flags
- No need to manage API keys separately (handled by CLI)

**Cons:**
- Subprocess overhead (slower than direct HTTP calls)
- CLI tool must be installed and configured
- Additional dependency on CLI tool stability
- Limited to models supported by each CLI tool

**Best for:** Official provider tools (Claude, Codex, Droid, Gemini) where you already have CLI installed and authenticated.

#### HTTP Adapters

HTTP adapters make direct API calls to HTTP endpoints (e.g., Ollama, LM Studio, OpenRouter, custom APIs).

**Pros:**
- Fast direct API calls without subprocess overhead
- Support for many providers (local and cloud)
- Built-in retry logic with exponential backoff
- No CLI installation required

**Cons:**
- Requires endpoint setup and configuration
- Manual authentication (API keys, tokens)
- Must implement request/response parsing for each provider
- May require running local services (Ollama, LM Studio)

**Best for:** Self-hosted models (Ollama, LM Studio), cloud APIs (OpenRouter), and custom API integrations.

### When to Choose Each Type

| Use Case | Recommended Type | Reason |
|----------|-----------------|--------|
| Official Claude CLI | CLI | Full authentication, project context |
| Official Codex/Droid | CLI | Seamless integration with existing tools |
| Local Ollama models | HTTP | Fast, no CLI needed |
| LM Studio models | HTTP | Direct API access |
| Cloud OpenRouter | HTTP | Standard API integration |
| Custom API | HTTP | Maximum flexibility |
| Multi-provider routing | HTTP | Easier configuration management |

## Adding a CLI Adapter

### Step 1: Create Adapter File

Create a new file `adapters/your_tool.py` that subclasses `BaseCLIAdapter`:

```python
"""Your Tool CLI adapter."""
from adapters.base import BaseCLIAdapter


class YourToolAdapter(BaseCLIAdapter):
    """Adapter for your-tool CLI."""

    def __init__(
        self,
        command: str = "your-tool",
        args: list[str] | None = None,
        timeout: int = 60
    ):
        """
        Initialize YourTool adapter.

        Args:
            command: Command to execute (default: "your-tool")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 60)
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        super().__init__(command=command, args=args, timeout=timeout)

    def parse_output(self, raw_output: str) -> str:
        """
        Parse your-tool CLI output.

        Your CLI might output:
        - Header/initialization text
        - Status messages
        - Actual model response
        - Footer/metadata

        Extract the actual response from the raw output.

        Args:
            raw_output: Raw stdout from your-tool CLI

        Returns:
            Parsed model response
        """
        # Example: Skip header lines and extract response
        lines = raw_output.strip().split("\n")

        # Find where the actual response starts
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not any(
                keyword in line.lower()
                for keyword in ["loading", "version", "initializing"]
            ):
                start_idx = i
                break

        # Join remaining lines
        response = "\n".join(lines[start_idx:]).strip()
        return response
```

**Key points:**
- Inherit from `BaseCLIAdapter`
- Implement `parse_output()` to extract the model's response from CLI output
- Handle CLI-specific formatting (headers, footers, metadata)
- Raise informative exceptions for parsing errors

### Step 2: Update Configuration

Add your adapter to `config.yaml`:

```yaml
adapters:
  your-tool:
    type: cli
    command: "your-tool"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

**Configuration fields:**
- `type`: Must be `"cli"` for CLI adapters
- `command`: Executable name (must be in PATH)
- `args`: Argument template with placeholders:
  - `{model}`: Replaced with model name at runtime
  - `{prompt}`: Replaced with prompt text at runtime
- `timeout`: Maximum execution time in seconds

**Example for reasoning models:**
```yaml
adapters:
  your-reasoning-tool:
    type: cli
    command: "your-tool"
    args: ["--model", "{model}", "--think", "{prompt}"]
    timeout: 180  # Reasoning models need more time
```

### Step 3: Register in Factory

Update `adapters/__init__.py` to register your adapter:

```python
"""CLI and HTTP adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.base_http import BaseHTTPAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters.droid import DroidAdapter
from adapters.gemini import GeminiAdapter
from adapters.your_tool import YourToolAdapter  # Add import
from models.config import CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig
from typing import Union


def create_adapter(
    name: str, config: Union[CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig]
) -> Union[BaseCLIAdapter, BaseHTTPAdapter]:
    """Factory function to create appropriate adapter."""

    # Registry of CLI adapters
    cli_adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "droid": DroidAdapter,
        "gemini": GeminiAdapter,
        "your-tool": YourToolAdapter,  # Add to registry
    }

    # ... rest of factory logic ...


__all__ = [
    "BaseCLIAdapter",
    "BaseHTTPAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "DroidAdapter",
    "GeminiAdapter",
    "YourToolAdapter",  # Add to exports
    "create_adapter",
]
```

### Step 4: Update Schema

Add your CLI to the schema in `models/schema.py`:

```python
class Participant(BaseModel):
    """Participant in a deliberation."""

    cli: Literal[
        "claude",
        "codex",
        "droid",
        "gemini",
        "your-tool"  # Add your CLI here
    ]
    model: str
```

Update the MCP tool description in `server.py` to document the new CLI:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle MCP tool invocation.

    Supported CLIs:
    - claude: Anthropic Claude CLI (official)
    - codex: GitHub Codex CLI (official)
    - droid: Multi-model CLI (supports Claude, GPT)
    - gemini: Google Gemini CLI (official)
    - your-tool: Your custom CLI tool  # Document it
    """
    # ... rest of tool handler ...
```

### Step 5: Add Recommended Models

Update the `RECOMMENDED_MODELS` dictionary in `server.py`:

```python
RECOMMENDED_MODELS = {
    "claude": ["sonnet-4-5", "opus-4", "haiku-4"],
    "codex": ["gpt-5-codex", "gpt-4o"],
    "droid": ["claude-sonnet-4-5-20250929", "gpt-5-codex"],
    "gemini": ["gemini-2.5-pro-002", "gemini-2.0-flash-001"],
    "your-tool": ["your-model-v1", "your-model-v2"],  # Add recommendations
}
```

### Step 6: Write Tests

Create unit tests in `tests/unit/test_adapters.py`:

```python
import pytest
from adapters.your_tool import YourToolAdapter


class TestYourToolAdapter:
    """Tests for YourToolAdapter."""

    def test_init_requires_args(self):
        """Test that adapter requires args from config."""
        with pytest.raises(ValueError, match="args must be provided"):
            YourToolAdapter(args=None)

    def test_parse_output_basic(self):
        """Test basic output parsing."""
        adapter = YourToolAdapter(args=["{prompt}"])
        raw_output = """Loading model...
Version 1.0
Initializing...

This is the actual model response.
It can span multiple lines.
"""
        result = adapter.parse_output(raw_output)
        assert result == "This is the actual model response.\nIt can span multiple lines."

    def test_parse_output_strips_header(self):
        """Test that header lines are stripped."""
        adapter = YourToolAdapter(args=["{prompt}"])
        raw_output = "Loading...\nModel output here"
        result = adapter.parse_output(raw_output)
        assert "Loading" not in result
        assert "Model output here" in result

    @pytest.mark.asyncio
    async def test_invoke_with_mock(self, mocker):
        """Test invoke with mocked subprocess."""
        adapter = YourToolAdapter(args=["--model", "{model}", "{prompt}"])

        # Mock subprocess
        mock_process = mocker.Mock()
        mock_process.communicate = mocker.AsyncMock(
            return_value=(b"Model response", b"")
        )
        mock_process.returncode = 0
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

        result = await adapter.invoke(prompt="Test prompt", model="test-model")
        assert result == "Model response"
```

Create integration tests in `tests/integration/test_your_tool_integration.py`:

```python
import pytest
from adapters.your_tool import YourToolAdapter


@pytest.mark.integration
@pytest.mark.skipif(
    not shutil.which("your-tool"),
    reason="your-tool CLI not installed"
)
class TestYourToolIntegration:
    """Integration tests for YourToolAdapter (requires CLI installed)."""

    @pytest.mark.asyncio
    async def test_real_invocation(self):
        """Test real CLI invocation."""
        adapter = YourToolAdapter(
            args=["--model", "{model}", "{prompt}"],
            timeout=30
        )

        result = await adapter.invoke(
            prompt="What is 2+2? Answer with just the number.",
            model="your-model-name"
        )

        assert result
        assert "4" in result
```

## Adding an HTTP Adapter

### Architecture Overview

HTTP adapters inherit from `BaseHTTPAdapter`, which provides:
- HTTP request handling via `httpx`
- Automatic retry logic with exponential backoff (5xx, 429, network errors)
- Fast-fail on client errors (4xx)
- Authentication via environment variable substitution
- Timeout management
- Error isolation (adapter failures don't halt deliberation)

### Step 1: Create Adapter File

Create a new file `adapters/your_adapter.py`:

```python
"""Your API HTTP adapter."""
from typing import Tuple
from adapters.base_http import BaseHTTPAdapter


class YourAdapter(BaseHTTPAdapter):
    """
    Adapter for Your API.

    Your API provides [description of the service].
    API reference: [URL to documentation]

    Default endpoint: [URL]

    Example:
        adapter = YourAdapter(
            base_url="https://api.example.com",
            api_key="your-key",
            timeout=60
        )
        result = await adapter.invoke(
            prompt="What is the capital of France?",
            model="your-model-v1"
        )
    """

    def build_request(
        self, model: str, prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build Your API request.

        Args:
            model: Model identifier (e.g., "your-model-v1", "your-model-v2")
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body):
            - endpoint: API endpoint path (e.g., "/v1/chat/completions")
            - headers: HTTP headers (Content-Type, Authorization, etc.)
            - body: Request body (dict that will be JSON-encoded)
        """
        endpoint = "/v1/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
        }

        body = {
            "model": model,
            "prompt": prompt,
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """
        Parse Your API response.

        Your API response format:
        {
          "id": "cmpl-xxxxx",
          "object": "text_completion",
          "created": 1234567890,
          "model": "your-model-v1",
          "choices": [
            {
              "text": "The model's response text",
              "index": 0,
              "finish_reason": "stop"
            }
          ]
        }

        Args:
            response_json: Parsed JSON response from Your API

        Returns:
            Extracted response text

        Raises:
            KeyError: If response doesn't contain expected fields
            ValueError: If response format is invalid
        """
        if "choices" not in response_json:
            raise KeyError(
                f"Response missing 'choices' field. "
                f"Received keys: {list(response_json.keys())}"
            )

        choices = response_json["choices"]
        if not choices:
            raise ValueError("Response 'choices' array is empty")

        if "text" not in choices[0]:
            raise KeyError(
                f"First choice missing 'text' field. "
                f"Received keys: {list(choices[0].keys())}"
            )

        return choices[0]["text"]
```

**Key implementation points:**
- `build_request()`: Construct endpoint, headers, and body for the API
- `parse_response()`: Extract model response from JSON response
- Include docstrings with API response format examples
- Raise informative exceptions for parsing errors
- Handle authentication (API keys, bearer tokens, etc.)

### Step 2: Update Configuration

Add your adapter to `config.yaml`:

```yaml
adapters:
  your_adapter:
    type: http
    base_url: "https://api.example.com"
    api_key: "${YOUR_API_KEY}"  # Environment variable substitution
    timeout: 60
    max_retries: 3
```

**Configuration fields:**
- `type`: Must be `"http"` for HTTP adapters
- `base_url`: Base URL for the API (protocol + domain + port)
- `api_key`: API key or token (use `${VAR}` for environment variables)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts on transient failures
- `headers` (optional): Additional headers for all requests

**Environment variable substitution:**
```yaml
adapters:
  your_adapter:
    type: http
    base_url: "${API_BASE_URL}"  # From environment
    api_key: "${YOUR_API_KEY}"
    headers:
      X-Custom-Header: "${CUSTOM_VALUE}"
```

Set the environment variables before running:
```bash
export YOUR_API_KEY="sk-xxxxx"
export API_BASE_URL="https://api.example.com"
export CUSTOM_VALUE="custom-value"
```

### Step 3: Register in Factory

Update `adapters/__init__.py`:

```python
"""CLI and HTTP adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.base_http import BaseHTTPAdapter
from adapters.claude import ClaudeAdapter
from adapters.ollama import OllamaAdapter
from adapters.lmstudio import LMStudioAdapter
from adapters.your_adapter import YourAdapter  # Add import
from models.config import CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig
from typing import Union


def create_adapter(
    name: str, config: Union[CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig]
) -> Union[BaseCLIAdapter, BaseHTTPAdapter]:
    """Factory function to create appropriate adapter."""

    # Registry of CLI adapters
    cli_adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
    }

    # Registry of HTTP adapters
    http_adapters = {
        "ollama": OllamaAdapter,
        "lmstudio": LMStudioAdapter,
        "your_adapter": YourAdapter,  # Add to registry
    }

    # ... rest of factory logic ...


__all__ = [
    "BaseCLIAdapter",
    "BaseHTTPAdapter",
    "ClaudeAdapter",
    "OllamaAdapter",
    "YourAdapter",  # Add to exports
    "create_adapter",
]
```

### Step 4: Set Environment Variables

If your adapter uses API keys or environment variables, document them and set them:

```bash
# In your shell profile (~/.bashrc, ~/.zshrc, etc.)
export YOUR_API_KEY="your-api-key-here"
export API_BASE_URL="https://api.example.com"

# Or in a .env file (not committed to git)
# Then load with: export $(cat .env | xargs)
YOUR_API_KEY=your-api-key-here
API_BASE_URL=https://api.example.com
```

### Step 5: Write Tests

Create unit tests in `tests/unit/test_your_adapter.py`:

```python
import pytest
from adapters.your_adapter import YourAdapter


class TestYourAdapter:
    """Tests for YourAdapter."""

    def test_build_request_structure(self):
        """Test request structure."""
        adapter = YourAdapter(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=60
        )

        endpoint, headers, body = adapter.build_request(
            model="your-model-v1",
            prompt="Test prompt"
        )

        assert endpoint == "/v1/completions"
        assert headers["Content-Type"] == "application/json"
        assert "Bearer test-key" in headers.get("Authorization", "")
        assert body["model"] == "your-model-v1"
        assert body["prompt"] == "Test prompt"

    def test_parse_response_success(self):
        """Test successful response parsing."""
        adapter = YourAdapter(base_url="https://api.example.com")

        response_json = {
            "id": "cmpl-123",
            "choices": [
                {
                    "text": "This is the model response.",
                    "index": 0,
                    "finish_reason": "stop"
                }
            ]
        }

        result = adapter.parse_response(response_json)
        assert result == "This is the model response."

    def test_parse_response_missing_choices(self):
        """Test error handling for missing choices."""
        adapter = YourAdapter(base_url="https://api.example.com")

        response_json = {"id": "cmpl-123"}

        with pytest.raises(KeyError, match="missing 'choices'"):
            adapter.parse_response(response_json)

    def test_parse_response_empty_choices(self):
        """Test error handling for empty choices."""
        adapter = YourAdapter(base_url="https://api.example.com")

        response_json = {"choices": []}

        with pytest.raises(ValueError, match="choices.*empty"):
            adapter.parse_response(response_json)

    @pytest.mark.asyncio
    async def test_invoke_with_vcr(self, vcr_cassette):
        """Test invoke with VCR-recorded response."""
        adapter = YourAdapter(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=60
        )

        # VCR will replay recorded HTTP interaction
        result = await adapter.invoke(
            prompt="What is 2+2?",
            model="your-model-v1"
        )

        assert result
        assert isinstance(result, str)
```

**Using VCR for HTTP mocking:**

Create a VCR cassette in `tests/fixtures/vcr_cassettes/your_adapter/`:

```python
# tests/conftest.py
import pytest
import vcr

@pytest.fixture
def vcr_cassette():
    """VCR cassette for HTTP recording/replay."""
    my_vcr = vcr.VCR(
        cassette_library_dir='tests/fixtures/vcr_cassettes',
        record_mode='once',  # Record once, then replay
        match_on=['uri', 'method'],
        filter_headers=['authorization'],  # Hide API keys
    )
    return my_vcr
```

Run tests once with real API to record, then replays are automatic:

```bash
# First run: makes real API call and records
pytest tests/unit/test_your_adapter.py::test_invoke_with_vcr

# Subsequent runs: replays from cassette (no API call)
pytest tests/unit/test_your_adapter.py::test_invoke_with_vcr
```

**Integration tests** (optional, requires running service):

```python
# tests/integration/test_your_adapter_integration.py
import pytest
from adapters.your_adapter import YourAdapter


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("YOUR_API_KEY"),
    reason="YOUR_API_KEY not set"
)
class TestYourAdapterIntegration:
    """Integration tests for YourAdapter (requires API access)."""

    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test real API invocation."""
        adapter = YourAdapter(
            base_url="https://api.example.com",
            api_key=os.getenv("YOUR_API_KEY"),
            timeout=60
        )

        result = await adapter.invoke(
            prompt="What is the capital of France? Answer in one word.",
            model="your-model-v1"
        )

        assert result
        assert "paris" in result.lower()

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test retry behavior on 429 rate limit."""
        adapter = YourAdapter(
            base_url="https://api.example.com",
            api_key=os.getenv("YOUR_API_KEY"),
            timeout=60,
            max_retries=3
        )

        # Make rapid requests to trigger rate limit
        results = []
        for _ in range(5):
            result = await adapter.invoke(
                prompt="Quick test",
                model="your-model-v1"
            )
            results.append(result)

        # Should succeed despite rate limits (via retry)
        assert len(results) == 5
        assert all(results)
```

## Key Differences: CLI vs HTTP

| Feature | CLI Adapter | HTTP Adapter |
|---------|-------------|--------------|
| **Setup** | Install CLI tool + authenticate | Configure endpoint + API key |
| **Speed** | Slower (subprocess overhead ~50-200ms) | Faster (direct HTTP ~10-50ms) |
| **Reliability** | Depends on CLI stability | Built-in retry logic |
| **Authentication** | Handled by CLI (login once) | API key in config/environment |
| **Models** | Limited to CLI-supported models | Provider-specific catalog |
| **Local Models** | Yes (if CLI supports) | Yes (Ollama, LM Studio) |
| **Cloud Models** | Yes (Claude, Codex, Gemini) | Yes (OpenRouter, direct APIs) |
| **Subprocess** | Yes (asyncio.create_subprocess_exec) | No (httpx async client) |
| **Error Handling** | Subprocess errors, timeouts | HTTP status codes, network errors |
| **Retry Logic** | None (single invocation) | Exponential backoff on 5xx/429 |
| **Best For** | Official CLI tools | Self-hosted, cloud APIs |

## Common Patterns

### Error Handling

**CLI Adapter:**
```python
def parse_output(self, raw_output: str) -> str:
    """Parse CLI output with error handling."""
    if not raw_output.strip():
        raise ValueError("CLI returned empty output")

    if "ERROR" in raw_output.upper():
        raise RuntimeError(f"CLI error: {raw_output}")

    # Extract response
    return raw_output.strip()
```

**HTTP Adapter:**
```python
def parse_response(self, response_json: dict) -> str:
    """Parse API response with error handling."""
    # Check for API error format
    if "error" in response_json:
        error_msg = response_json["error"].get("message", "Unknown error")
        raise ValueError(f"API error: {error_msg}")

    # Extract response
    if "choices" not in response_json:
        raise KeyError(f"Missing 'choices' field: {response_json.keys()}")

    return response_json["choices"][0]["text"]
```

### Validation

**CLI Adapter (prompt length validation):**
```python
class YourToolAdapter(BaseCLIAdapter):
    """Adapter with prompt validation."""

    MAX_PROMPT_LENGTH = 100000  # 100k chars

    def validate_prompt_length(self, prompt: str) -> None:
        """Validate prompt length before invocation."""
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt too long: {len(prompt)} chars "
                f"(max: {self.MAX_PROMPT_LENGTH}). "
                f"Try reducing context or splitting request."
            )
```

The base adapter automatically calls `validate_prompt_length()` before invocation if implemented.

**HTTP Adapter (custom validation):**
```python
class YourAdapter(BaseHTTPAdapter):
    """Adapter with custom validation."""

    def build_request(self, model: str, prompt: str) -> Tuple[str, dict, dict]:
        """Build request with validation."""
        # Validate model
        if model not in ["model-v1", "model-v2"]:
            raise ValueError(f"Unsupported model: {model}")

        # Validate prompt
        if len(prompt) > 50000:
            raise ValueError(f"Prompt too long: {len(prompt)} chars (max: 50000)")

        # Build request
        endpoint = "/v1/completions"
        headers = {"Content-Type": "application/json"}
        body = {"model": model, "prompt": prompt}
        return (endpoint, headers, body)
```

### Authentication

**HTTP Adapter with multiple auth methods:**
```python
class YourAdapter(BaseHTTPAdapter):
    """Adapter with flexible authentication."""

    def build_request(self, model: str, prompt: str) -> Tuple[str, dict, dict]:
        """Build request with authentication."""
        endpoint = "/v1/completions"

        headers = {"Content-Type": "application/json"}

        # Bearer token auth
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Or custom header auth
        if self.headers and "X-API-Key" in self.headers:
            headers["X-API-Key"] = self.headers["X-API-Key"]

        body = {"model": model, "prompt": prompt}
        return (endpoint, headers, body)
```

### Timeout Configuration

**Different timeouts for different model types:**
```yaml
adapters:
  your_adapter_fast:
    type: http
    base_url: "https://api.example.com"
    api_key: "${YOUR_API_KEY}"
    timeout: 30  # Fast models

  your_adapter_reasoning:
    type: http
    base_url: "https://api.example.com"
    api_key: "${YOUR_API_KEY}"
    timeout: 180  # Reasoning models need more time
```

## Testing Your Adapter

### Manual Testing

**CLI Adapter:**
```python
# test_cli_adapter.py
import asyncio
from adapters.your_tool import YourToolAdapter


async def test():
    adapter = YourToolAdapter(
        command="your-tool",
        args=["--model", "{model}", "{prompt}"],
        timeout=60
    )

    result = await adapter.invoke(
        prompt="What is 2+2? Answer with just the number.",
        model="your-model-v1"
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(test())
```

Run: `python test_cli_adapter.py`

**HTTP Adapter:**
```python
# test_http_adapter.py
import asyncio
import os
from adapters.your_adapter import YourAdapter


async def test():
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key=os.getenv("YOUR_API_KEY", "test-key"),
        timeout=60
    )

    result = await adapter.invoke(
        prompt="What is the capital of France? Answer in one word.",
        model="your-model-v1"
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(test())
```

Run: `YOUR_API_KEY=sk-xxxxx python test_http_adapter.py`

### Unit Test Patterns

**Testing parse_output (CLI):**
```python
def test_parse_output_handles_headers():
    """Test that parse_output strips headers."""
    adapter = YourToolAdapter(args=["{prompt}"])

    raw_output = """
    Loading model...
    Initializing...

    This is the actual response.
    It spans multiple lines.
    """

    result = adapter.parse_output(raw_output)

    assert "Loading" not in result
    assert "Initializing" not in result
    assert "This is the actual response" in result
    assert "It spans multiple lines" in result
```

**Testing build_request and parse_response (HTTP):**
```python
def test_build_request_includes_auth():
    """Test that request includes authentication."""
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key="sk-test-key"
    )

    endpoint, headers, body = adapter.build_request(
        model="test-model",
        prompt="Test prompt"
    )

    assert "Bearer sk-test-key" in headers.get("Authorization", "")


def test_parse_response_extracts_text():
    """Test response parsing."""
    adapter = YourAdapter(base_url="https://api.example.com")

    response = {
        "choices": [
            {"text": "Response text", "index": 0}
        ]
    }

    result = adapter.parse_response(response)
    assert result == "Response text"
```

### Integration Testing

**Test with real CLI:**
```python
@pytest.mark.integration
@pytest.mark.skipif(
    not shutil.which("your-tool"),
    reason="your-tool not installed"
)
async def test_real_cli_invocation():
    """Test with real CLI (requires installation)."""
    adapter = YourToolAdapter(
        args=["--model", "{model}", "{prompt}"],
        timeout=30
    )

    result = await adapter.invoke(
        prompt="Echo: Hello World",
        model="your-model"
    )

    assert result
    assert "Hello World" in result
```

**Test with real API:**
```python
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("YOUR_API_KEY"),
    reason="YOUR_API_KEY not set"
)
async def test_real_api_call():
    """Test with real API (requires credentials)."""
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key=os.getenv("YOUR_API_KEY"),
        timeout=60
    )

    result = await adapter.invoke(
        prompt="What is 2+2?",
        model="your-model-v1"
    )

    assert result
    assert "4" in result
```

## Debugging

### Common Issues and Solutions

#### CLI Adapter Issues

**Issue: CLI returns empty output**
```
Solution: Check CLI installation and authentication
```
```bash
# Test CLI directly
your-tool --model test-model "test prompt"

# Check CLI version
your-tool --version

# Verify authentication
your-tool auth status
```

**Issue: Timeout errors**
```
Solution: Increase timeout in config.yaml
```
```yaml
adapters:
  your-tool:
    type: cli
    timeout: 180  # Increased from 60
```

**Issue: Parsing errors**
```
Solution: Add logging to parse_output()
```
```python
def parse_output(self, raw_output: str) -> str:
    """Parse output with debug logging."""
    import logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Raw output:\n{raw_output}")

    # Your parsing logic
    result = raw_output.strip()

    logger.debug(f"Parsed result:\n{result}")
    return result
```

#### HTTP Adapter Issues

**Issue: Authentication failures (401, 403)**
```
Solution: Verify API key and environment variables
```
```bash
# Check environment variable is set
echo $YOUR_API_KEY

# Test API key with curl
curl -H "Authorization: Bearer $YOUR_API_KEY" \
     https://api.example.com/v1/models
```

**Issue: Connection errors**
```
Solution: Check base_url and network connectivity
```
```bash
# Test connectivity
curl https://api.example.com/health

# Check if service is running (for local APIs)
curl http://localhost:11434/api/tags  # Ollama example
```

**Issue: Request/response parsing errors**
```
Solution: Add logging to see actual JSON
```
```python
def parse_response(self, response_json: dict) -> str:
    """Parse response with debug logging."""
    import logging
    import json
    logger = logging.getLogger(__name__)

    logger.debug(f"Response JSON:\n{json.dumps(response_json, indent=2)}")

    # Your parsing logic
    if "choices" not in response_json:
        logger.error(f"Missing 'choices'. Keys: {list(response_json.keys())}")
        raise KeyError("Missing 'choices' field")

    result = response_json["choices"][0]["text"]
    logger.debug(f"Extracted text: {result[:100]}...")
    return result
```

### Checking Logs

AI Counsel logs all adapter invocations to `mcp_server.log`:

```bash
# Watch logs in real-time
tail -f mcp_server.log

# Search for adapter-specific logs
grep "YourAdapter" mcp_server.log

# Check for errors
grep "ERROR" mcp_server.log | grep "your_adapter"
```

### Testing in Isolation

**Test adapter without deliberation:**
```python
# quick_test.py
import asyncio
from adapters.your_adapter import YourAdapter

async def main():
    adapter = YourAdapter(
        base_url="http://localhost:11434",  # Example: local Ollama
        timeout=60
    )

    try:
        result = await adapter.invoke(
            prompt="Say hello",
            model="llama2"
        )
        print(f"SUCCESS: {result}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
```

Run: `python quick_test.py`

## Real-World Example: Adding Replicate HTTP Adapter

Let's walk through a complete example of adding support for Replicate's API.

### Step 1: Research the API

From [Replicate's API docs](https://replicate.com/docs/reference/http):

**Request format:**
```bash
curl -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "model-version-id",
    "input": {
      "prompt": "a vision of paradise"
    }
  }'
```

**Response format:**
```json
{
  "id": "abc123",
  "status": "succeeded",
  "output": ["Generated text response"]
}
```

### Step 2: Create the Adapter

```python
# adapters/replicate.py
"""Replicate HTTP adapter."""
from typing import Tuple
from adapters.base_http import BaseHTTPAdapter
import time


class ReplicateAdapter(BaseHTTPAdapter):
    """
    Adapter for Replicate API.

    Replicate provides cloud-hosted AI models via REST API.
    API reference: https://replicate.com/docs/reference/http

    Note: Replicate uses async prediction model - you create a prediction,
    then poll until it completes. This adapter handles polling automatically.

    Example:
        adapter = ReplicateAdapter(
            base_url="https://api.replicate.com",
            api_key="r8_xxxxx",
            timeout=120
        )
        result = await adapter.invoke(
            prompt="Explain quantum computing",
            model="meta/llama-2-70b-chat:version-id"
        )
    """

    def build_request(
        self, model: str, prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build Replicate API request.

        Args:
            model: Model version ID (e.g., "meta/llama-2-70b-chat:02e509c...")
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body)
        """
        endpoint = "/v1/predictions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Extract owner/name:version from model string
        if ":" in model:
            model_path, version = model.split(":", 1)
        else:
            raise ValueError(
                f"Model must be in format 'owner/name:version'. Got: {model}"
            )

        body = {
            "version": version,
            "input": {
                "prompt": prompt,
                "max_length": 4096,
            }
        }

        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """
        Parse Replicate API response.

        Replicate uses async predictions - response includes prediction ID,
        which we need to poll until status is "succeeded".

        Response format:
        {
          "id": "abc123",
          "status": "starting|processing|succeeded|failed|canceled",
          "output": ["result text"] or null,
          "error": "error message" or null
        }

        Args:
            response_json: Parsed JSON response from Replicate

        Returns:
            Extracted output text

        Raises:
            ValueError: If prediction failed or output is missing
        """
        if "status" not in response_json:
            raise KeyError(
                f"Response missing 'status' field. "
                f"Received keys: {list(response_json.keys())}"
            )

        status = response_json["status"]

        # Check for errors
        if status == "failed":
            error_msg = response_json.get("error", "Unknown error")
            raise ValueError(f"Replicate prediction failed: {error_msg}")

        if status == "canceled":
            raise ValueError("Replicate prediction was canceled")

        # For succeeded status, extract output
        if status == "succeeded":
            output = response_json.get("output")
            if not output:
                raise ValueError("Response has no output")

            # Output can be list or string
            if isinstance(output, list):
                return "".join(output)
            else:
                return str(output)

        # For starting/processing status, we need to poll
        # (BaseHTTPAdapter doesn't handle polling, so we raise an error)
        raise ValueError(
            f"Prediction still processing (status: {status}). "
            f"Replicate requires polling - not yet implemented."
        )
```

### Step 3: Add Configuration

```yaml
# config.yaml
adapters:
  replicate:
    type: http
    base_url: "https://api.replicate.com"
    api_key: "${REPLICATE_API_TOKEN}"
    timeout: 120  # Replicate can be slow
    max_retries: 3
```

### Step 4: Register Adapter

```python
# adapters/__init__.py
from adapters.replicate import ReplicateAdapter

http_adapters = {
    "ollama": OllamaAdapter,
    "lmstudio": LMStudioAdapter,
    "replicate": ReplicateAdapter,  # Add here
}
```

### Step 5: Set Environment Variable

```bash
# ~/.bashrc or ~/.zshrc
export REPLICATE_API_TOKEN="r8_xxxxx"
```

### Step 6: Write Tests

```python
# tests/unit/test_replicate.py
import pytest
from adapters.replicate import ReplicateAdapter


class TestReplicateAdapter:
    """Tests for ReplicateAdapter."""

    def test_build_request_parses_model_format(self):
        """Test that model format is parsed correctly."""
        adapter = ReplicateAdapter(
            base_url="https://api.replicate.com",
            api_key="r8_test"
        )

        endpoint, headers, body = adapter.build_request(
            model="meta/llama-2-70b:02e509c789",
            prompt="Test"
        )

        assert endpoint == "/v1/predictions"
        assert "Bearer r8_test" in headers["Authorization"]
        assert body["version"] == "02e509c789"
        assert body["input"]["prompt"] == "Test"

    def test_build_request_rejects_invalid_format(self):
        """Test that invalid model format is rejected."""
        adapter = ReplicateAdapter(
            base_url="https://api.replicate.com",
            api_key="r8_test"
        )

        with pytest.raises(ValueError, match="owner/name:version"):
            adapter.build_request(model="invalid-format", prompt="Test")

    def test_parse_response_succeeded(self):
        """Test parsing successful response."""
        adapter = ReplicateAdapter(base_url="https://api.replicate.com")

        response = {
            "id": "abc123",
            "status": "succeeded",
            "output": ["Generated text here"]
        }

        result = adapter.parse_response(response)
        assert result == "Generated text here"

    def test_parse_response_failed(self):
        """Test error handling for failed prediction."""
        adapter = ReplicateAdapter(base_url="https://api.replicate.com")

        response = {
            "id": "abc123",
            "status": "failed",
            "error": "Model timed out"
        }

        with pytest.raises(ValueError, match="failed.*timed out"):
            adapter.parse_response(response)

    def test_parse_response_processing(self):
        """Test error handling for still-processing prediction."""
        adapter = ReplicateAdapter(base_url="https://api.replicate.com")

        response = {
            "id": "abc123",
            "status": "processing"
        }

        with pytest.raises(ValueError, match="still processing"):
            adapter.parse_response(response)
```

### Step 7: Manual Testing

```python
# test_replicate_manual.py
import asyncio
import os
from adapters.replicate import ReplicateAdapter


async def main():
    adapter = ReplicateAdapter(
        base_url="https://api.replicate.com",
        api_key=os.getenv("REPLICATE_API_TOKEN"),
        timeout=120
    )

    try:
        result = await adapter.invoke(
            prompt="Explain quantum entanglement in one sentence.",
            model="meta/llama-2-70b-chat:02e509c789..."
        )
        print(f"SUCCESS: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
```

Run:
```bash
export REPLICATE_API_TOKEN="r8_xxxxx"
python test_replicate_manual.py
```

### Step 8: Use in Deliberation

```yaml
# Example deliberation request
{
  "question": "Should we use Replicate for model hosting?",
  "participants": [
    {"cli": "claude", "model": "sonnet-4-5"},
    {"cli": "replicate", "model": "meta/llama-2-70b-chat:02e509..."}
  ],
  "rounds": 2
}
```

This example demonstrates a complete adapter implementation with:
- API research and understanding
- Request/response handling
- Error handling for API-specific scenarios
- Configuration with environment variables
- Comprehensive tests
- Manual testing script
- Integration with deliberations

## Next Steps

After adding your adapter:

1. **Test thoroughly**: Unit tests, integration tests, manual testing
2. **Document models**: Add recommended models to `server.py::RECOMMENDED_MODELS`
3. **Update README**: Add your adapter to the supported adapters list
4. **Write usage examples**: Create example deliberation requests
5. **Monitor logs**: Check `mcp_server.log` for issues during deliberations
6. **Optimize timeouts**: Adjust timeout values based on model performance
7. **Consider contributing**: Submit PR to share your adapter with the community

## Additional Resources

- **Base Adapters**: `/Users/harrison/Github/ai-counsel/adapters/base.py` and `/Users/harrison/Github/ai-counsel/adapters/base_http.py`
- **Example CLI Adapter**: `/Users/harrison/Github/ai-counsel/adapters/claude.py`
- **Example HTTP Adapter**: `/Users/harrison/Github/ai-counsel/adapters/ollama.py`
- **Test Examples**: `/Users/harrison/Github/ai-counsel/tests/unit/test_adapters.py`
- **Configuration Schema**: `/Users/harrison/Github/ai-counsel/models/config.py`
- **Project Documentation**: `/Users/harrison/Github/ai-counsel/README.md` and `/Users/harrison/Github/ai-counsel/CLAUDE.md`
