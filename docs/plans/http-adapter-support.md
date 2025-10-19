# Implementation Plan: HTTP Adapter Support

**Created**: 2025-10-19
**Updated**: 2025-10-19
**Target**: Add HTTP adapter support for Ollama, LM Studio, OpenRouter, and llama.cpp with config schema migration
**Estimated Tasks**: 28 tasks across 4 phases
**Estimated Time**: 12-16 hours

## Implementation Status

| Phase | Tasks | Status | Completion Date |
|-------|-------|--------|----------------|
| **Phase 1: Foundation & Config Migration** | 8/8 | ✅ **COMPLETE** | 2025-10-19 |
| **Phase 2: Ollama Adapter** | 4/4 | ✅ **COMPLETE** | 2025-10-19 |
| **Phase 3: LM Studio & OpenRouter** | 8/8 | ✅ **COMPLETE** | 2025-10-19 |
| **Phase 4: llama.cpp Adapter** | 4/4 | ⏸️ Not Started | - |
| **Phase 5: Integration & Documentation** | 4/4 | ⏸️ Not Started | - |
| **Total Progress** | **20/28** | **71% Complete** | - |

### Completed Work

**Phase 1 Deliverables (Tasks 1-8):**
- ✅ HTTP dependencies added (httpx, tenacity, vcrpy)
- ✅ Type-safe config models with discriminated unions (CLIAdapterConfig, HTTPAdapterConfig)
- ✅ BaseHTTPAdapter abstract class with smart retry logic
- ✅ Extended adapter factory for CLI + HTTP support
- ✅ Config migration script (`scripts/migrate_config.py`)
- ✅ Migration documentation (`docs/migration/cli_tools_to_adapters.md`)
- ✅ CLAUDE.md updated with HTTP adapter architecture
- ✅ Backward compatibility maintained with `cli_tools` section

**Phase 2 Deliverables (Tasks 9-12):**
- ✅ OllamaAdapter implementation (`adapters/ollama.py`)
- ✅ Ollama registered in adapter factory
- ✅ Ollama configuration example in `config.yaml`
- ✅ MCP server schema updated with Ollama support

**Phase 3 Deliverables (Tasks 13-20):**
- ✅ LMStudioAdapter implementation (`adapters/lmstudio.py`)
- ✅ LM Studio registered in adapter factory
- ✅ LM Studio configuration example in `config.yaml`
- ✅ MCP server schema updated with LM Studio support
- ✅ OpenRouterAdapter implementation (`adapters/openrouter.py`)
- ✅ OpenRouter registered in adapter factory
- ✅ OpenRouter configuration example in `config.yaml`
- ✅ MCP server schema updated with OpenRouter support

### Test Results

- **Total Tests**: 167 passing, 1 skipped
- **New Tests Added**: 55 tests across phases 1-3
- **Test Execution Time**: 8.19 seconds
- **Warnings**: 0 (clean test output)
- **Coverage**: High coverage for all new code

### Git Commits

16 commits created following conventional commit format:
- Phase 1: 7 commits (including warning fix)
- Phase 2: 4 commits
- Phase 3: 8 commits (split between LM Studio and OpenRouter)

### Supported HTTP Adapters

1. **Ollama** - Local LLM server (`http://localhost:11434`)
2. **LM Studio** - Local OpenAI-compatible API (`http://localhost:1234`)
3. **OpenRouter** - Cloud multi-provider API (`https://openrouter.ai/api/v1`)

### Next Steps

**Phase 4** (Tasks 21-24): Implement llama.cpp CLI adapter with custom output parsing
**Phase 5** (Tasks 25-28): Integration tests, README updates, troubleshooting documentation

## Context for the Engineer

You are implementing this feature in a codebase that:
- Uses **Python 3.11+** with **Pydantic 2.5+** for validation
- Follows **TDD** (Test-Driven Development) - tests written BEFORE implementation
- Tests with **pytest** (unit/, integration/, e2e/ structure)
- Uses **async/await** for all I/O operations
- Follows **conventional commits** (type: description format)
- Architecture: **Factory pattern** for adapters, **Pydantic models** for config
- Design principles: **DRY**, **YAGNI**, **Simplicity**

**You are expected to**:
- Write tests BEFORE implementation (strict TDD)
- Commit frequently (after each completed task)
- Follow existing code patterns in `adapters/` directory
- Keep changes minimal (YAGNI - You Aren't Gonna Need It)
- Avoid duplication (DRY - Don't Repeat Yourself)
- Run tests after each change: `pytest tests/unit -v`

## Design Decisions (From Deliberation)

Based on multi-model deliberation, these architectural decisions are final:

1. **Config Structure**: Rename `cli_tools` → `adapters` with explicit `type` field
2. **Priority**: Implement Ollama → LM Studio → OpenRouter → llama.cpp (easiest-first)
3. **Migration**: Support both `cli_tools` (deprecated) and `adapters`, provide migration script
4. **BaseHTTPAdapter Interface**: `build_request(model, prompt) → (endpoint, headers, body)`
5. **Error Handling**: Smart retries with exponential backoff for 5xx/network errors
6. **Testing**: VCR hybrid - recorded HTTP responses for realistic validation
7. **Authentication**: Environment variable substitution `api_key: ${OPENROUTER_API_KEY}`

## Prerequisites Checklist

Before starting, verify:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Virtual environment activated (`.venv/bin/activate`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tests passing (`pytest tests/unit -v` shows 113+ passing)
- [ ] Branch created: `git checkout -b feature/http-adapter-support`
- [ ] For local testing: Ollama installed (optional, for manual verification)

## Phase 1: Foundation & Config Migration (Tasks 1-8)

### Task 1: Add HTTP Dependencies

**File(s)**: `requirements.txt`
**Depends on**: None
**Estimated time**: 5m

#### What you're building
Adding `httpx` (async HTTP client) and `tenacity` (retry logic) dependencies for HTTP adapter support, plus `vcrpy` for test response recording.

#### Test First (TDD)

**Test file**: `tests/unit/test_requirements.py` (new file)

**Test structure**:
```python
def test_httpx_importable():
    """Verify httpx can be imported."""

def test_tenacity_importable():
    """Verify tenacity can be imported."""
```

**Example test skeleton**:
```python
"""Test that required dependencies are available."""

def test_httpx_importable():
    """Verify httpx can be imported."""
    import httpx
    assert hasattr(httpx, 'AsyncClient')

def test_tenacity_importable():
    """Verify tenacity can be imported."""
    import tenacity
    assert hasattr(tenacity, 'retry')

def test_vcrpy_importable():
    """Verify vcrpy can be imported for testing."""
    import vcr
    assert hasattr(vcr, 'VCR')
```

#### Implementation

Add to `requirements.txt`:
```python
# HTTP client and retry logic for HTTP adapters
httpx>=0.27.0
tenacity>=8.2.0

# Test dependencies
vcrpy>=4.4.0  # HTTP response recording for tests
```

#### Verification

**Automated tests**:
```bash
pip install -r requirements.txt
pytest tests/unit/test_requirements.py -v
```

**Expected output**:
```
tests/unit/test_requirements.py::test_httpx_importable PASSED
tests/unit/test_requirements.py::test_tenacity_importable PASSED
tests/unit/test_requirements.py::test_vcrpy_importable PASSED
```

#### Commit

**Commit message**:
```
feat: add HTTP adapter dependencies (httpx, tenacity, vcrpy)

Add httpx for async HTTP client, tenacity for retry logic,
and vcrpy for test response recording to support HTTP adapters.
```

**Files to commit**:
- `requirements.txt`
- `tests/unit/test_requirements.py`

---

### Task 2: Create New Config Models (AdapterConfig, HTTPAdapterConfig)

**File(s)**: `models/config.py`
**Depends on**: Task 1
**Estimated time**: 30m

#### What you're building
New Pydantic models to support both CLI and HTTP adapters with explicit type discrimination. This enables the config schema migration while maintaining backward compatibility.

#### Test First (TDD)

**Test file**: `tests/unit/test_config.py` (append to existing)

**Test structure**:
```python
class TestAdapterConfig:
    def test_cli_adapter_config_validation():
        """CLI adapter requires command, args, timeout."""

    def test_http_adapter_config_validation():
        """HTTP adapter requires base_url, timeout."""

    def test_http_adapter_with_env_var_substitution():
        """HTTP adapter supports ${ENV_VAR} in api_key."""

    def test_adapter_config_discriminates_by_type():
        """Type field determines CLI vs HTTP parsing."""

    def test_invalid_adapter_type_rejected():
        """Unknown adapter type raises ValidationError."""
```

**Test specifics**:
- Mock environment variables for env var substitution tests
- Use `pytest.raises(ValidationError)` for error cases
- Test both valid and invalid configurations

**Example test skeleton**:
```python
import os
import pytest
from pydantic import ValidationError
from models.config import CLIAdapterConfig, HTTPAdapterConfig, AdapterConfig

class TestCLIAdapterConfig:
    def test_valid_cli_adapter_config(self):
        """Test valid CLI adapter configuration."""
        config = CLIAdapterConfig(
            type="cli",
            command="claude",
            args=["--model", "{model}", "{prompt}"],
            timeout=60
        )
        assert config.type == "cli"
        assert config.command == "claude"
        assert config.timeout == 60

    def test_cli_adapter_requires_command(self):
        """Test that command field is required."""
        with pytest.raises(ValidationError):
            CLIAdapterConfig(
                type="cli",
                args=["--model", "{model}"],
                timeout=60
            )

class TestHTTPAdapterConfig:
    def test_valid_http_adapter_config(self):
        """Test valid HTTP adapter configuration."""
        config = HTTPAdapterConfig(
            type="http",
            base_url="http://localhost:11434",
            timeout=60
        )
        assert config.type == "http"
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 60

    def test_http_adapter_with_api_key_env_var(self):
        """Test HTTP adapter with environment variable substitution."""
        os.environ["TEST_API_KEY"] = "sk-test-123"
        config = HTTPAdapterConfig(
            type="http",
            base_url="https://api.example.com",
            api_key="${TEST_API_KEY}",
            timeout=60
        )
        # After loading, ${TEST_API_KEY} should be resolved
        assert config.api_key == "sk-test-123"
        del os.environ["TEST_API_KEY"]

    def test_http_adapter_requires_base_url(self):
        """Test that base_url field is required."""
        with pytest.raises(ValidationError):
            HTTPAdapterConfig(
                type="http",
                timeout=60
            )

class TestAdapterConfig:
    def test_adapter_config_discriminates_cli_type(self):
        """Test AdapterConfig discriminates to CLIAdapterConfig."""
        data = {
            "type": "cli",
            "command": "claude",
            "args": ["--model", "{model}"],
            "timeout": 60
        }
        config = AdapterConfig(**data)
        assert isinstance(config, CLIAdapterConfig)

    def test_adapter_config_discriminates_http_type(self):
        """Test AdapterConfig discriminates to HTTPAdapterConfig."""
        data = {
            "type": "http",
            "base_url": "http://localhost:11434",
            "timeout": 60
        }
        config = AdapterConfig(**data)
        assert isinstance(config, HTTPAdapterConfig)

    def test_invalid_adapter_type_raises_error(self):
        """Test that invalid type raises ValidationError."""
        with pytest.raises(ValidationError):
            AdapterConfig(
                type="invalid",
                command="test",
                timeout=60
            )
```

#### Implementation

**Approach**:
Use Pydantic's discriminated unions to create a type-safe adapter configuration that can handle both CLI and HTTP adapters.

**Code structure**:
```python
# In models/config.py

from typing import Literal, Union, Optional
from pydantic import BaseModel, Field, field_validator
import os
import re

class CLIAdapterConfig(BaseModel):
    """Configuration for CLI-based adapter."""
    type: Literal["cli"] = "cli"
    command: str
    args: list[str]
    timeout: int = 60

class HTTPAdapterConfig(BaseModel):
    """Configuration for HTTP-based adapter."""
    type: Literal["http"] = "http"
    base_url: str
    api_key: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    timeout: int = 60
    max_retries: int = 3

    @field_validator('api_key', 'base_url')
    @classmethod
    def resolve_env_vars(cls, v: Optional[str]) -> Optional[str]:
        """Resolve ${ENV_VAR} references in string fields."""
        if v is None:
            return v

        # Pattern: ${VAR_NAME}
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(
                    f"Environment variable '{env_var}' is not set. "
                    f"Required for configuration."
                )
            return value

        return re.sub(pattern, replacer, v)

# Discriminated union - Pydantic uses 'type' field to determine which model to use
AdapterConfig = Union[CLIAdapterConfig, HTTPAdapterConfig]

# Keep CLIToolConfig for backward compatibility
class CLIToolConfig(BaseModel):
    """Legacy CLI tool configuration (deprecated, use CLIAdapterConfig)."""
    command: str
    args: list[str]
    timeout: int

# Update Config model to support both old and new schemas
class Config(BaseModel):
    """Root configuration model."""
    version: str

    # New adapters section (preferred)
    adapters: Optional[dict[str, AdapterConfig]] = None

    # Legacy cli_tools section (deprecated)
    cli_tools: Optional[dict[str, CLIToolConfig]] = None

    defaults: DefaultsConfig
    storage: StorageConfig
    deliberation: DeliberationConfig

    @field_validator('adapters', 'cli_tools')
    @classmethod
    def ensure_one_adapter_section(cls, v, info):
        """Ensure at least one of adapters or cli_tools is provided."""
        # This validator is called for each field, we check in model_post_init
        return v

    def model_post_init(self, __context):
        """Post-initialization validation."""
        if self.adapters is None and self.cli_tools is None:
            raise ValueError("Configuration must include either 'adapters' or 'cli_tools' section")

        # If cli_tools is used, emit deprecation warning
        if self.cli_tools is not None and self.adapters is None:
            import warnings
            warnings.warn(
                "The 'cli_tools' configuration section is deprecated. "
                "Please migrate to 'adapters' section with explicit 'type' field. "
                "See migration guide: docs/migration/cli_tools_to_adapters.md",
                DeprecationWarning,
                stacklevel=2
            )
```

**Key points**:
- Use `Literal["cli"]` and `Literal["http"]` for type discrimination
- Pydantic automatically validates discriminated unions based on `type` field
- Environment variable substitution uses regex pattern `${VAR_NAME}`
- Validation raises clear errors if env vars are missing
- Backward compatibility: support both `cli_tools` and `adapters` sections

#### Verification

**Manual testing**:
1. Create test config with env var: `echo 'TEST_KEY=sk-123' > .env`
2. Test config loading in Python REPL:
```python
from models.config import HTTPAdapterConfig
import os
os.environ["TEST_KEY"] = "sk-123"
config = HTTPAdapterConfig(
    type="http",
    base_url="http://localhost",
    api_key="${TEST_KEY}",
    timeout=60
)
print(config.api_key)  # Should print: sk-123
```

**Automated tests**:
```bash
pytest tests/unit/test_config.py::TestCLIAdapterConfig -v
pytest tests/unit/test_config.py::TestHTTPAdapterConfig -v
pytest tests/unit/test_config.py::TestAdapterConfig -v
```

**Expected output**:
All new tests passing with clear success messages.

#### Commit

**Commit message**:
```
feat: add adapter config models with type discrimination

Add CLIAdapterConfig and HTTPAdapterConfig with Pydantic
discriminated unions. Support environment variable substitution
in api_key fields. Maintain backward compatibility with
cli_tools section.
```

**Files to commit**:
- `models/config.py`
- `tests/unit/test_config.py`

---

### Task 3: Create BaseHTTPAdapter Abstract Class

**File(s)**: `adapters/base_http.py` (new file)
**Depends on**: Tasks 1-2
**Estimated time**: 45m

#### What you're building
Abstract base class for HTTP-based adapters that handles HTTP mechanics (requests, retries, timeouts, error handling) while delegating API-specific logic to subclasses.

#### Test First (TDD)

**Test file**: `tests/unit/test_base_http_adapter.py` (new file)

**Test structure**:
```python
class TestBaseHTTPAdapter:
    def test_cannot_instantiate_base_http_adapter():
        """Base adapter is abstract, cannot instantiate."""

    def test_subclass_must_implement_build_request():
        """Subclass must implement build_request method."""

    def test_subclass_must_implement_parse_response():
        """Subclass must implement parse_response method."""

class TestHTTPAdapterInvoke:
    @pytest.mark.asyncio
    async def test_invoke_success():
        """Successful HTTP request returns parsed response."""

    @pytest.mark.asyncio
    async def test_invoke_with_context():
        """Context is prepended to prompt."""

    @pytest.mark.asyncio
    async def test_invoke_timeout():
        """Timeout raises TimeoutError."""

    @pytest.mark.asyncio
    async def test_invoke_retries_on_5xx():
        """Retries on 5xx errors with exponential backoff."""

    @pytest.mark.asyncio
    async def test_invoke_no_retry_on_4xx():
        """Does not retry on 4xx client errors."""

    @pytest.mark.asyncio
    async def test_invoke_network_error_retries():
        """Retries on network errors."""
```

**Mocking guidelines**:
- Mock `httpx.AsyncClient` for HTTP requests
- Use `AsyncMock` for async methods
- Test retry logic with `side_effect` to simulate failures then success

**Example test skeleton**:
```python
"""Unit tests for BaseHTTPAdapter."""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from abc import ABC
import httpx

# We'll create a concrete test implementation
class ConcreteHTTPAdapter:
    """Concrete implementation for testing."""

    def __init__(self, base_url: str, timeout: int = 60, max_retries: int = 3):
        # Will use actual BaseHTTPAdapter after implementation
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def build_request(self, model: str, prompt: str):
        """Test implementation."""
        return (
            f"{self.base_url}/test",
            {"Authorization": "Bearer test"},
            {"model": model, "prompt": prompt}
        )

    def parse_response(self, response_json: dict) -> str:
        """Test implementation."""
        return response_json.get("response", "")

class TestBaseHTTPAdapter:
    def test_cannot_instantiate_base_adapter(self):
        """Test that BaseHTTPAdapter cannot be instantiated."""
        # Will test with actual BaseHTTPAdapter after implementation
        # from adapters.base_http import BaseHTTPAdapter
        # with pytest.raises(TypeError):
        #     BaseHTTPAdapter(base_url="http://test", timeout=60)
        pass  # Placeholder

    def test_subclass_must_implement_build_request(self):
        """Test that subclass must implement build_request."""
        # from adapters.base_http import BaseHTTPAdapter
        # class IncompleteAdapter(BaseHTTPAdapter):
        #     def parse_response(self, response_json):
        #         return str(response_json)
        #
        # with pytest.raises(TypeError):
        #     IncompleteAdapter(base_url="http://test", timeout=60)
        pass  # Placeholder

class TestHTTPAdapterInvoke:
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_invoke_success(self, mock_client_class):
        """Test successful HTTP request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test response"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        adapter = ConcreteHTTPAdapter(base_url="http://test", timeout=60)
        # Will use actual invoke method after implementation
        # result = await adapter.invoke(prompt="test prompt", model="test-model")
        # assert result == "Test response"
        # mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_invoke_retries_on_503(self, mock_client_class):
        """Test retry logic on 503 Service Unavailable."""
        # Setup mock to fail twice with 503, then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "503", request=Mock(), response=mock_response_fail
            )
        )

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"response": "Success after retry"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_response_fail, mock_response_fail, mock_response_success]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        adapter = ConcreteHTTPAdapter(base_url="http://test", timeout=60, max_retries=3)
        # Will test with actual implementation
        # result = await adapter.invoke(prompt="test", model="test-model")
        # assert result == "Success after retry"
        # assert mock_client.post.call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_invoke_no_retry_on_400(self, mock_client_class):
        """Test that 4xx errors are not retried."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_response
            )
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        adapter = ConcreteHTTPAdapter(base_url="http://test", timeout=60, max_retries=3)
        # Will test with actual implementation
        # with pytest.raises(httpx.HTTPStatusError):
        #     await adapter.invoke(prompt="test", model="test-model")
        # mock_client.post.assert_called_once()  # No retries for 4xx
```

#### Implementation

**Approach**:
Create abstract base class that mirrors `BaseCLIAdapter` pattern but for HTTP. Use `httpx.AsyncClient` for async HTTP requests and `tenacity` for retry logic with exponential backoff.

**Code structure**:
```python
"""Base HTTP adapter with request/retry management."""
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception
)


def is_retryable_http_error(exception):
    """Determine if an HTTP error should be retried."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on 5xx server errors and 429 rate limit
        return exception.response.status_code >= 500 or exception.response.status_code == 429
    # Retry on network errors
    return isinstance(exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError))


class BaseHTTPAdapter(ABC):
    """
    Abstract base class for HTTP API adapters.

    Handles HTTP requests, timeout management, retry logic with exponential backoff,
    and error handling. Subclasses must implement build_request() and parse_response()
    for API-specific logic.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None
    ):
        """
        Initialize HTTP adapter.

        Args:
            base_url: Base URL for API (e.g., "http://localhost:11434")
            timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts for transient failures (default: 3)
            api_key: Optional API key for authentication
            headers: Optional default headers to include in all requests
        """
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key
        self.default_headers = headers or {}

    @abstractmethod
    def build_request(
        self,
        model: str,
        prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build API-specific request components.

        Args:
            model: Model identifier
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body):
            - endpoint: Full URL path (e.g., "/api/generate")
            - headers: Request headers dict
            - body: Request body dict (will be JSON-encoded)
        """
        pass

    @abstractmethod
    def parse_response(self, response_json: dict) -> str:
        """
        Parse API-specific response to extract model output.

        Args:
            response_json: Parsed JSON response from API

        Returns:
            Extracted model response text
        """
        pass

    async def invoke(
        self,
        prompt: str,
        model: str,
        context: Optional[str] = None,
        is_deliberation: bool = True
    ) -> str:
        """
        Invoke the HTTP API with the given prompt and model.

        Args:
            prompt: The prompt to send to the model
            model: Model identifier
            context: Optional additional context to prepend to prompt
            is_deliberation: Whether this is part of a deliberation (unused for HTTP,
                           kept for API compatibility with BaseCLIAdapter)

        Returns:
            Parsed response from the model

        Raises:
            TimeoutError: If request exceeds timeout
            httpx.HTTPStatusError: If API returns error status
            RuntimeError: If retries exhausted
        """
        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n{prompt}"

        # Get request components from subclass
        endpoint, headers, body = self.build_request(model, full_prompt)

        # Build full URL
        full_url = f"{self.base_url}{endpoint}"

        # Execute request with retry logic
        try:
            response_json = await self._execute_request_with_retry(
                url=full_url,
                headers=headers,
                body=body
            )
            return self.parse_response(response_json)

        except asyncio.TimeoutError:
            raise TimeoutError(f"HTTP request timed out after {self.timeout}s")

    async def _execute_request_with_retry(
        self,
        url: str,
        headers: dict[str, str],
        body: dict
    ) -> dict:
        """
        Execute HTTP POST request with retry logic.

        Uses tenacity for exponential backoff retry on:
        - 5xx server errors
        - 429 rate limit errors
        - Network errors (connection, timeout)

        Does NOT retry on:
        - 4xx client errors (bad request, auth, etc.)

        Args:
            url: Full request URL
            headers: Request headers
            body: Request body (will be JSON-encoded)

        Returns:
            Parsed JSON response

        Raises:
            httpx.HTTPStatusError: On HTTP error (after retries exhausted for 5xx)
            httpx.NetworkError: On network error (after retries exhausted)
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception(is_retryable_http_error),
            reraise=True
        )
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=body
                )
                response.raise_for_status()  # Raise for 4xx/5xx
                return response.json()

        return await _make_request()
```

**Key points**:
- Follow pattern from `BaseCLIAdapter`: minimal interface, maximum delegation
- Use `httpx.AsyncClient` for async HTTP (aligns with async adapter pattern)
- `tenacity` library handles retry logic declaratively
- Retry only on transient failures (5xx, 429, network errors)
- Fail fast on client errors (4xx)
- Return type is `Tuple[str, dict, dict]` for `build_request()` - gives full control
- `is_deliberation` parameter kept for API compatibility but unused

**Integration points**:
- Imports: `httpx`, `tenacity`, `asyncio`, `abc`
- Used by: Concrete HTTP adapters (OllamaAdapter, LMStudioAdapter, etc.)
- Pattern matches: `BaseCLIAdapter` from `adapters/base.py`

#### Verification

**Manual testing**:
```python
# Test in Python REPL
from adapters.base_http import BaseHTTPAdapter

# Try to instantiate (should fail - abstract class)
try:
    adapter = BaseHTTPAdapter(base_url="http://test", timeout=60)
except TypeError as e:
    print(f"Expected error: {e}")

# Create concrete implementation
class TestAdapter(BaseHTTPAdapter):
    def build_request(self, model, prompt):
        return ("/test", {"Content-Type": "application/json"}, {"prompt": prompt})

    def parse_response(self, response_json):
        return response_json.get("text", "")

# Should work
adapter = TestAdapter(base_url="http://localhost", timeout=60)
print(f"Adapter created: {adapter.base_url}")
```

**Automated tests**:
```bash
pytest tests/unit/test_base_http_adapter.py -v
```

**Expected output**:
All tests passing, including retry logic and error handling tests.

#### Commit

**Commit message**:
```
feat: add BaseHTTPAdapter abstract class

Implement abstract base class for HTTP adapters with:
- Async HTTP client (httpx)
- Smart retry logic with exponential backoff (tenacity)
- Retries on 5xx/network errors only, fails fast on 4xx
- Abstract build_request() and parse_response() methods
```

**Files to commit**:
- `adapters/base_http.py`
- `tests/unit/test_base_http_adapter.py`

---

### Task 4: Update Adapter Factory for HTTP Support

**File(s)**: `adapters/__init__.py`
**Depends on**: Tasks 2-3
**Estimated time**: 20m

#### What you're building
Extend the `create_adapter()` factory function to support both CLI and HTTP adapters based on the `type` field in configuration.

#### Test First (TDD)

**Test file**: `tests/unit/test_adapters.py` (append to existing TestAdapterFactory)

**Test structure**:
```python
class TestAdapterFactory:
    # ... existing CLI tests ...

    def test_create_http_adapter_with_http_config():
        """Test creating HTTP adapter from HTTPAdapterConfig."""

    def test_factory_discriminates_by_type_field():
        """Test factory uses type field to choose adapter class."""

    def test_create_adapter_with_new_config_format():
        """Test factory works with new AdapterConfig union type."""
```

**Example test skeleton**:
```python
# Add to tests/unit/test_adapters.py, in TestAdapterFactory class

def test_create_http_adapter_placeholder(self):
    """Test creating HTTP adapter (placeholder until Ollama implemented)."""
    # This will be updated in Task 9 when we implement OllamaAdapter
    # For now, just test that the factory can handle HTTP config type
    from models.config import HTTPAdapterConfig

    config = HTTPAdapterConfig(
        type="http",
        base_url="http://localhost:11434",
        timeout=60
    )

    # Factory should recognize HTTP type
    # Will implement in Task 9 when we add OllamaAdapter
    # adapter = create_adapter("ollama", config)
    # assert isinstance(adapter, OllamaAdapter)
    pass  # Placeholder

def test_factory_rejects_http_adapter_with_cli_config(self):
    """Test that HTTP adapter name requires HTTP config."""
    from models.config import CLIAdapterConfig
    import pytest

    config = CLIAdapterConfig(
        type="cli",
        command="claude",
        args=["--model", "{model}"],
        timeout=60
    )

    # Trying to create "ollama" (HTTP adapter) with CLI config should fail
    # Will implement proper error in Task 9
    pass  # Placeholder
```

#### Implementation

**Approach**:
Extend the factory pattern to handle both CLI and HTTP adapter types. Use type checking to route to appropriate adapter class.

**Code structure**:
```python
# In adapters/__init__.py

"""CLI and HTTP adapter factory and exports."""
from adapters.base import BaseCLIAdapter
from adapters.base_http import BaseHTTPAdapter
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters.droid import DroidAdapter
from adapters.gemini import GeminiAdapter
from models.config import CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig, AdapterConfig
from typing import Union

def create_adapter(
    name: str,
    config: Union[CLIToolConfig, CLIAdapterConfig, HTTPAdapterConfig]
) -> Union[BaseCLIAdapter, BaseHTTPAdapter]:
    """
    Factory function to create appropriate adapter (CLI or HTTP).

    Args:
        name: Adapter name (e.g., 'claude', 'ollama')
        config: Adapter configuration (CLI or HTTP)

    Returns:
        Appropriate adapter instance (CLI or HTTP)

    Raises:
        ValueError: If adapter is not supported
        TypeError: If config type doesn't match adapter type
    """
    # Registry of CLI adapters
    cli_adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "droid": DroidAdapter,
        "gemini": GeminiAdapter,
    }

    # Registry of HTTP adapters (will be populated in Phase 2)
    http_adapters = {
        # "ollama": OllamaAdapter,  # Added in Task 9
        # "lmstudio": LMStudioAdapter,  # Added in Task 13
        # "openrouter": OpenRouterAdapter,  # Added in Task 17
    }

    # Handle legacy CLIToolConfig (backward compatibility)
    if isinstance(config, CLIToolConfig):
        if name in cli_adapters:
            return cli_adapters[name](
                command=config.command,
                args=config.args,
                timeout=config.timeout
            )
        else:
            raise ValueError(
                f"Unsupported CLI tool: '{name}'. "
                f"Supported: {', '.join(cli_adapters.keys())}"
            )

    # Handle new typed configs
    if isinstance(config, CLIAdapterConfig):
        if name not in cli_adapters:
            raise ValueError(
                f"Unknown CLI adapter: '{name}'. "
                f"Supported CLI adapters: {', '.join(cli_adapters.keys())}"
            )

        return cli_adapters[name](
            command=config.command,
            args=config.args,
            timeout=config.timeout
        )

    elif isinstance(config, HTTPAdapterConfig):
        if name not in http_adapters:
            raise ValueError(
                f"Unknown HTTP adapter: '{name}'. "
                f"Supported HTTP adapters: {', '.join(http_adapters.keys())} "
                f"(Note: HTTP adapters are being added in phases)"
            )

        return http_adapters[name](
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            api_key=config.api_key,
            headers=config.headers
        )

    else:
        raise TypeError(
            f"Invalid config type: {type(config)}. "
            f"Expected CLIToolConfig, CLIAdapterConfig, or HTTPAdapterConfig"
        )


__all__ = [
    "BaseCLIAdapter",
    "BaseHTTPAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "DroidAdapter",
    "GeminiAdapter",
    "create_adapter"
]
```

**Key points**:
- Maintain backward compatibility with `CLIToolConfig`
- Use `isinstance()` checks to route to correct adapter type
- Clear error messages for unsupported adapters
- HTTP adapter registry starts empty, populated as we add adapters
- Type hints show factory can return either CLI or HTTP adapter

#### Verification

**Manual testing**:
```python
from adapters import create_adapter
from models.config import CLIAdapterConfig

# Test CLI adapter creation (existing)
config = CLIAdapterConfig(
    type="cli",
    command="claude",
    args=["--model", "{model}"],
    timeout=60
)
adapter = create_adapter("claude", config)
print(f"Created adapter: {type(adapter)}")
```

**Automated tests**:
```bash
pytest tests/unit/test_adapters.py::TestAdapterFactory -v
```

**Expected output**:
All existing factory tests pass, new placeholder tests pass.

#### Commit

**Commit message**:
```
feat: extend adapter factory for HTTP adapter support

Update create_adapter() to handle both CLI and HTTP adapters
using config type discrimination. Maintain backward compatibility
with CLIToolConfig.
```

**Files to commit**:
- `adapters/__init__.py`
- `tests/unit/test_adapters.py`

---

### Task 5: Update Config Loader for Adapter Migration

**File(s)**: `models/config.py`
**Depends on**: Task 2
**Estimated time**: 20m

#### What you're building
Enhance `load_config()` to support both `cli_tools` (deprecated) and `adapters` sections, with deprecation warnings for `cli_tools`.

#### Test First (TDD)

**Test file**: `tests/unit/test_config.py`

**Test structure**:
```python
class TestConfigLoader:
    def test_load_config_with_adapters_section():
        """Test loading config with new adapters section."""

    def test_load_config_with_cli_tools_section():
        """Test loading config with legacy cli_tools section (deprecated)."""

    def test_load_config_emits_deprecation_warning():
        """Test that cli_tools usage emits DeprecationWarning."""

    def test_load_config_fails_without_adapter_section():
        """Test that config without adapters or cli_tools fails."""
```

**Example test skeleton**:
```python
import pytest
import warnings
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError
from models.config import load_config

class TestConfigLoader:
    def test_load_config_with_adapters_section(self, tmp_path):
        """Test loading config with new adapters section."""
        config_data = {
            "version": "1.0",
            "adapters": {
                "claude": {
                    "type": "cli",
                    "command": "claude",
                    "args": ["--model", "{model}"],
                    "timeout": 60
                }
            },
            "defaults": {
                "mode": "quick",
                "rounds": 2,
                "max_rounds": 5,
                "timeout_per_round": 120
            },
            "storage": {
                "transcripts_dir": "transcripts",
                "format": "markdown",
                "auto_export": True
            },
            "deliberation": {
                "convergence_detection": {
                    "enabled": True,
                    "semantic_similarity_threshold": 0.85,
                    "divergence_threshold": 0.40,
                    "min_rounds_before_check": 1,
                    "consecutive_stable_rounds": 2,
                    "stance_stability_threshold": 0.80,
                    "response_length_drop_threshold": 0.40
                },
                "early_stopping": {
                    "enabled": True,
                    "threshold": 0.66,
                    "respect_min_rounds": True
                },
                "convergence_threshold": 0.8,
                "enable_convergence_detection": True
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config.adapters is not None
        assert "claude" in config.adapters
        assert config.cli_tools is None

    def test_load_config_with_cli_tools_emits_warning(self, tmp_path):
        """Test that cli_tools section triggers deprecation warning."""
        config_data = {
            "version": "1.0",
            "cli_tools": {
                "claude": {
                    "command": "claude",
                    "args": ["--model", "{model}"],
                    "timeout": 60
                }
            },
            # ... rest of config ...
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = load_config(str(config_file))

            # Check warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "cli_tools" in str(w[0].message).lower()
            assert "deprecated" in str(w[0].message).lower()

    def test_load_config_fails_without_adapter_section(self, tmp_path):
        """Test config without adapters or cli_tools raises error."""
        config_data = {
            "version": "1.0",
            # Missing both adapters and cli_tools
            "defaults": {"mode": "quick", "rounds": 2},
            # ... minimal config ...
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))

        assert "adapters" in str(exc_info.value).lower()
        assert "cli_tools" in str(exc_info.value).lower()
```

#### Implementation

The `Config` model already handles this in Task 2's `model_post_init()`. The test just validates it works correctly.

#### Verification

**Automated tests**:
```bash
pytest tests/unit/test_config.py::TestConfigLoader -v
```

**Expected output**:
All config loader tests pass, deprecation warning correctly triggered.

#### Commit

**Commit message**:
```
test: add config loader tests for adapter migration

Test loading config with both new adapters and legacy
cli_tools sections. Verify deprecation warnings are emitted.
```

**Files to commit**:
- `tests/unit/test_config.py`

---

### Task 6: Create Migration Script (cli_tools → adapters)

**File(s)**: `scripts/migrate_config.py` (new file)
**Depends on**: Tasks 2, 5
**Estimated time**: 30m

#### What you're building
A migration script that converts `config.yaml` from `cli_tools` format to `adapters` format, adding explicit `type: cli` fields.

#### Test First (TDD)

**Test file**: `tests/unit/test_migrate_config.py` (new file)

**Test structure**:
```python
class TestMigrateConfig:
    def test_migrate_cli_tools_to_adapters():
        """Test migration converts cli_tools to adapters with type: cli."""

    def test_migrate_preserves_other_config():
        """Test migration preserves defaults, storage, deliberation."""

    def test_migrate_already_migrated_config():
        """Test migrating already-migrated config is idempotent."""

    def test_migrate_creates_backup():
        """Test migration creates .bak backup file."""
```

**Example test skeleton**:
```python
"""Tests for config migration script."""
import pytest
import yaml
from pathlib import Path
from scripts.migrate_config import migrate_config_file

class TestMigrateConfig:
    def test_migrate_cli_tools_to_adapters(self, tmp_path):
        """Test migration adds type: cli to existing tools."""
        old_config = {
            "version": "1.0",
            "cli_tools": {
                "claude": {
                    "command": "claude",
                    "args": ["--model", "{model}"],
                    "timeout": 60
                },
                "codex": {
                    "command": "codex",
                    "args": ["exec", "{prompt}"],
                    "timeout": 120
                }
            },
            "defaults": {"mode": "quick", "rounds": 2},
            "storage": {"transcripts_dir": "transcripts"},
            "deliberation": {"convergence_threshold": 0.8}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(old_config, f)

        # Run migration
        migrate_config_file(str(config_file))

        # Load migrated config
        with open(config_file, "r") as f:
            new_config = yaml.safe_load(f)

        # Verify structure
        assert "adapters" in new_config
        assert "cli_tools" not in new_config
        assert new_config["adapters"]["claude"]["type"] == "cli"
        assert new_config["adapters"]["codex"]["type"] == "cli"
        assert new_config["adapters"]["claude"]["command"] == "claude"

    def test_migrate_creates_backup(self, tmp_path):
        """Test that migration creates .bak file."""
        old_config = {
            "version": "1.0",
            "cli_tools": {"claude": {"command": "claude", "args": [], "timeout": 60}},
            "defaults": {},
            "storage": {},
            "deliberation": {}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(old_config, f)

        migrate_config_file(str(config_file))

        backup_file = tmp_path / "config.yaml.bak"
        assert backup_file.exists()

        # Verify backup contains original
        with open(backup_file, "r") as f:
            backup_config = yaml.safe_load(f)
        assert "cli_tools" in backup_config

    def test_migrate_already_migrated_is_idempotent(self, tmp_path):
        """Test migrating already-migrated config doesn't break."""
        already_migrated = {
            "version": "1.0",
            "adapters": {
                "claude": {
                    "type": "cli",
                    "command": "claude",
                    "args": [],
                    "timeout": 60
                }
            },
            "defaults": {},
            "storage": {},
            "deliberation": {}
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(already_migrated, f)

        # Should not raise error
        migrate_config_file(str(config_file))

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Should be unchanged
        assert config == already_migrated
```

#### Implementation

**Approach**:
Simple script that reads YAML, transforms structure, creates backup, writes new config.

**Code structure**:
```python
#!/usr/bin/env python3
"""
Migration script: cli_tools → adapters

Migrates config.yaml from legacy cli_tools format to new adapters format
with explicit type fields.

Usage:
    python scripts/migrate_config.py [path/to/config.yaml]

If no path provided, defaults to ./config.yaml
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any
import shutil


def migrate_config_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate config dictionary from cli_tools to adapters format.

    Args:
        config: Config dictionary with cli_tools section

    Returns:
        Migrated config with adapters section
    """
    # If already migrated (has adapters, no cli_tools), return as-is
    if "adapters" in config and "cli_tools" not in config:
        print("ℹ️  Config already migrated (has 'adapters' section)")
        return config

    # If no cli_tools, nothing to migrate
    if "cli_tools" not in config:
        print("⚠️  No 'cli_tools' section found, nothing to migrate")
        return config

    # Create new config with adapters
    migrated = config.copy()

    # Transform cli_tools → adapters
    adapters = {}
    for name, cli_config in config["cli_tools"].items():
        adapters[name] = {
            "type": "cli",  # Add explicit type
            "command": cli_config["command"],
            "args": cli_config["args"],
            "timeout": cli_config["timeout"]
        }

    migrated["adapters"] = adapters
    del migrated["cli_tools"]

    print(f"✓ Migrated {len(adapters)} CLI tools to adapters format")

    return migrated


def migrate_config_file(path: str) -> None:
    """
    Migrate config file from cli_tools to adapters format.

    Creates a backup at {path}.bak before modifying.

    Args:
        path: Path to config.yaml file

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    # Create backup
    backup_path = Path(f"{path}.bak")
    shutil.copy2(config_path, backup_path)
    print(f"✓ Created backup: {backup_path}")

    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Migrate
    migrated = migrate_config_dict(config)

    # Write migrated config
    with open(config_path, "w") as f:
        yaml.dump(migrated, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Migrated config written to: {config_path}")
    print(f"\nℹ️  Review the changes and delete {backup_path} when satisfied.")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yaml"

    print(f"Migrating config: {config_path}")
    print("-" * 50)

    try:
        migrate_config_file(config_path)
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("1. Review the migrated config.yaml")
        print("2. Test loading: python -c 'from models.config import load_config; load_config()'")
        print("3. Delete backup if satisfied: rm config.yaml.bak")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Key points**:
- Idempotent: safe to run multiple times
- Creates backup before modifying
- Clear user feedback with emoji indicators
- Preserves all other config sections unchanged
- Can be imported and used programmatically

#### Verification

**Manual testing**:
```bash
# Create test config with cli_tools
cat > test_config.yaml <<EOF
version: "1.0"
cli_tools:
  claude:
    command: claude
    args: ["--model", "{model}"]
    timeout: 60
defaults:
  mode: quick
  rounds: 2
storage:
  transcripts_dir: transcripts
deliberation:
  convergence_threshold: 0.8
EOF

# Run migration
python scripts/migrate_config.py test_config.yaml

# Verify output
cat test_config.yaml
# Should have "adapters" with "type: cli" added

# Check backup exists
ls test_config.yaml.bak
```

**Automated tests**:
```bash
pytest tests/unit/test_migrate_config.py -v
```

**Expected output**:
All migration tests pass, script produces correct output.

#### Commit

**Commit message**:
```
feat: add config migration script for cli_tools → adapters

Create migrate_config.py script to convert legacy cli_tools
configs to new adapters format with explicit type fields.
Includes backup creation and idempotent execution.
```

**Files to commit**:
- `scripts/migrate_config.py`
- `tests/unit/test_migrate_config.py`

---

### Task 7: Add Migration Documentation

**File(s)**: `docs/migration/cli_tools_to_adapters.md` (new file)
**Depends on**: Task 6
**Estimated time**: 15m

#### What you're building
User-facing documentation explaining the config migration process and why it's needed.

#### Implementation

Create clear, concise documentation:

```markdown
# Migration Guide: cli_tools → adapters

## Why This Change?

The `cli_tools` configuration section has been renamed to `adapters` to better reflect the system's architecture. AI Counsel now supports both CLI-based adapters (claude, codex, etc.) and HTTP-based adapters (Ollama, LM Studio, OpenRouter).

The new `adapters` section uses an explicit `type` field to distinguish between adapter types, making the configuration more maintainable and future-proof.

## What Changed?

### Before (Deprecated)
```yaml
cli_tools:
  claude:
    command: "claude"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

### After (Current)
```yaml
adapters:
  claude:
    type: cli  # ← Explicit type field
    command: "claude"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

## Migration Options

### Option 1: Automatic Migration (Recommended)

Use the provided migration script:

```bash
python scripts/migrate_config.py config.yaml
```

This will:
1. Create a backup at `config.yaml.bak`
2. Convert `cli_tools` to `adapters` with `type: cli` added
3. Preserve all other configuration unchanged

### Option 2: Manual Migration

1. Rename `cli_tools:` to `adapters:`
2. Add `type: cli` to each adapter entry
3. Verify with: `python -c "from models.config import load_config; load_config()"`

## Backward Compatibility

**The `cli_tools` section still works** but will emit a deprecation warning:

```
DeprecationWarning: The 'cli_tools' configuration section is deprecated.
Please migrate to 'adapters' section with explicit 'type' field.
```

Support for `cli_tools` will be removed in **version 2.0**.

## New HTTP Adapter Format

The new structure also supports HTTP-based adapters:

```yaml
adapters:
  ollama:
    type: http  # ← HTTP adapter type
    base_url: "http://localhost:11434"
    timeout: 60

  openrouter:
    type: http
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"  # ← Environment variable
    timeout: 90
    max_retries: 3
```

## Troubleshooting

### Error: "Configuration must include either 'adapters' or 'cli_tools' section"

Your config is missing the adapter section. Add either `adapters:` or `cli_tools:` (deprecated).

### Error: "Environment variable 'XXX' is not set"

An HTTP adapter references an undefined environment variable. Set it:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

Or add to `.env` file if using python-dotenv.

## Questions?

See the main README or open an issue on GitHub.
```

#### Verification

**Manual testing**:
- Read through documentation for clarity
- Follow migration steps with test config
- Verify all examples are accurate

#### Commit

**Commit message**:
```
docs: add cli_tools to adapters migration guide

Document the config schema migration with examples,
migration script usage, and backward compatibility info.
```

**Files to commit**:
- `docs/migration/cli_tools_to_adapters.md`

---

### Task 8: Update CLAUDE.md with New Architecture

**File(s)**: `CLAUDE.md`
**Depends on**: Tasks 3, 6, 7
**Estimated time**: 20m

#### What you're building
Update project documentation to reflect the new dual-adapter architecture (CLI + HTTP) and configuration schema.

#### Implementation

Add new sections to CLAUDE.md after "Core Components":

```markdown
## Core Components

[... existing sections ...]

**HTTP Adapter Layer** (`adapters/base_http.py`, `adapters/ollama.py`, etc.)
- Abstract base: `BaseHTTPAdapter` handles HTTP mechanics, retry logic, error handling
- Concrete adapters: `OllamaAdapter`, `LMStudioAdapter`, `OpenRouterAdapter`
- Each adapter implements `build_request()` for request construction and `parse_response()` for response parsing
- Retry logic: exponential backoff on 5xx/network errors, fail-fast on 4xx client errors
- Authentication: environment variable substitution pattern `${VAR_NAME}` in config

**Config Schema Migration** (`models/config.py`, `scripts/migrate_config.py`)
- New `adapters` section with explicit `type` field replaces `cli_tools`
- Backward compatibility: both sections supported, deprecation warning on `cli_tools`
- Migration script: `python scripts/migrate_config.py config.yaml`
- Environment variable substitution in HTTP adapter configs for secure API key storage

[... continue with updated Data Flow ...]

## Adding a New HTTP Adapter

1. **Create adapter file** in `adapters/your_adapter.py`:
   - Subclass `BaseHTTPAdapter`
   - Implement `build_request(model, prompt) -> (endpoint, headers, body)`
   - Implement `parse_response(response_json) -> str`

2. **Update config models** in `models/config.py`:
   - No changes needed - HTTPAdapterConfig handles all HTTP adapters

3. **Register adapter** in `adapters/__init__.py`:
   - Import adapter class
   - Add to `http_adapters` dict in `create_adapter()`

4. **Update schema** in `models/schema.py`:
   - Add CLI name to `Participant.cli` Literal type if needed

5. **Add to config.yaml** example:
   ```yaml
   adapters:
     your_adapter:
       type: http
       base_url: "https://api.example.com"
       api_key: "${YOUR_API_KEY}"
       timeout: 60
   ```

6. **Write tests**:
   - Unit tests in `tests/unit/test_adapters.py`
   - VCR fixtures in `tests/fixtures/vcr_cassettes/your_adapter/`
   - Integration tests optional (requires running service)

[... rest of document ...]
```

#### Verification

**Manual testing**:
- Read through changes for accuracy
- Ensure existing sections still accurate
- Check that new patterns match implementation

#### Commit

**Commit message**:
```
docs: update CLAUDE.md with HTTP adapter architecture

Document BaseHTTPAdapter pattern, config migration,
and instructions for adding new HTTP adapters.
```

**Files to commit**:
- `CLAUDE.md`

---

## Phase 2: Ollama Adapter (Tasks 9-12)

### Task 9: Implement OllamaAdapter

**File(s)**: `adapters/ollama.py` (new file)
**Depends on**: Task 3
**Estimated time**: 45m

#### What you're building
First HTTP adapter implementation for Ollama's local API. This establishes the pattern for all subsequent HTTP adapters.

#### Test First (TDD)

**Test file**: `tests/unit/test_ollama_adapter.py` (new file)

**Test structure**:
```python
class TestOllamaAdapter:
    def test_adapter_initialization():
        """Adapter initializes with correct base_url and defaults."""

    def test_build_request_structure():
        """build_request returns correct endpoint, headers, body."""

    def test_build_request_with_context():
        """Context is properly included in request."""

    def test_parse_response_extracts_content():
        """parse_response extracts 'response' field from JSON."""

    @pytest.mark.asyncio
    async def test_invoke_success_with_vcr():
        """Successful invocation with recorded response."""

    @pytest.mark.asyncio
    async def test_invoke_handles_streaming_response():
        """Handle Ollama's streaming response format."""
```

**VCR fixtures**:
- Create `tests/fixtures/vcr_cassettes/ollama/` directory
- Record a real Ollama API response
- Use for realistic validation without running Ollama

**Example test skeleton**:
```python
"""Tests for Ollama adapter."""
import pytest
import vcr
from adapters.ollama import OllamaAdapter

class TestOllamaAdapter:
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = OllamaAdapter(
            base_url="http://localhost:11434",
            timeout=60
        )
        assert adapter.base_url == "http://localhost:11434"
        assert adapter.timeout == 60

    def test_build_request_structure(self):
        """Test build_request returns correct structure."""
        adapter = OllamaAdapter(base_url="http://localhost:11434")

        endpoint, headers, body = adapter.build_request(
            model="llama2",
            prompt="What is 2+2?"
        )

        assert endpoint == "/api/generate"
        assert headers["Content-Type"] == "application/json"
        assert body["model"] == "llama2"
        assert body["prompt"] == "What is 2+2?"
        assert body["stream"] == False

    def test_parse_response_extracts_content(self):
        """Test parse_response extracts response field."""
        adapter = OllamaAdapter(base_url="http://localhost:11434")

        response_json = {
            "model": "llama2",
            "created_at": "2023-08-01T00:00:00Z",
            "response": "The answer is 4.",
            "done": True
        }

        result = adapter.parse_response(response_json)
        assert result == "The answer is 4."

    @pytest.mark.asyncio
    @vcr.use_cassette('tests/fixtures/vcr_cassettes/ollama/generate_success.yaml')
    async def test_invoke_with_vcr(self):
        """Test invoke with recorded Ollama response."""
        adapter = OllamaAdapter(base_url="http://localhost:11434")

        result = await adapter.invoke(
            prompt="Say hello",
            model="llama2"
        )

        assert isinstance(result, str)
        assert len(result) > 0
```

#### Implementation

**Approach**:
Implement concrete HTTP adapter for Ollama's `/api/generate` endpoint. Reference: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion

**Code structure**:
```python
"""Ollama HTTP adapter."""
from typing import Tuple
from adapters.base_http import BaseHTTPAdapter


class OllamaAdapter(BaseHTTPAdapter):
    """
    Adapter for Ollama local API.

    Ollama API reference: https://github.com/ollama/ollama/blob/main/docs/api.md

    Default endpoint: http://localhost:11434
    """

    def build_request(
        self,
        model: str,
        prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build Ollama API request.

        Args:
            model: Ollama model name (e.g., "llama2", "mistral")
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body)
        """
        endpoint = "/api/generate"

        headers = {
            "Content-Type": "application/json"
        }

        body = {
            "model": model,
            "prompt": prompt,
            "stream": False  # Use non-streaming for simplicity
        }

        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """
        Parse Ollama API response.

        Ollama response format:
        {
          "model": "llama2",
          "created_at": "2023-08-01T00:00:00Z",
          "response": "The model's response text",
          "done": true
        }

        Args:
            response_json: Parsed JSON response from Ollama

        Returns:
            Extracted response text

        Raises:
            KeyError: If response doesn't contain 'response' field
        """
        if "response" not in response_json:
            raise KeyError(
                f"Ollama response missing 'response' field. "
                f"Received: {response_json.keys()}"
            )

        return response_json["response"]
```

**Key points**:
- Inherits all HTTP mechanics from `BaseHTTPAdapter`
- `build_request()` returns Ollama-specific structure
- `stream: False` for simplicity (non-streaming responses)
- `parse_response()` extracts `response` field
- Clear error if response structure unexpected

**Integration points**:
- Imports: `BaseHTTPAdapter` from `adapters.base_http`
- Used by: `create_adapter()` factory

#### Verification

**Manual testing** (requires Ollama running):
```bash
# Start Ollama (if not running)
ollama serve

# Pull a model
ollama pull llama2

# Test in Python
python3 << 'EOF'
import asyncio
from adapters.ollama import OllamaAdapter

async def test():
    adapter = OllamaAdapter(base_url="http://localhost:11434", timeout=60)
    result = await adapter.invoke(prompt="Say hello in one sentence", model="llama2")
    print(f"Response: {result}")

asyncio.run(test())
EOF
```

**Automated tests**:
```bash
pytest tests/unit/test_ollama_adapter.py -v
```

**Expected output**:
All tests pass, VCR cassette recorded/replayed successfully.

#### Commit

**Commit message**:
```
feat: add Ollama HTTP adapter

Implement OllamaAdapter for local Ollama API with
non-streaming generation endpoint. First HTTP adapter
establishing the pattern.
```

**Files to commit**:
- `adapters/ollama.py`
- `tests/unit/test_ollama_adapter.py`
- `tests/fixtures/vcr_cassettes/ollama/` (VCR recordings)

---

### Task 10: Register Ollama in Adapter Factory

**File(s)**: `adapters/__init__.py`
**Depends on**: Task 9
**Estimated time**: 10m

#### What you're building
Register OllamaAdapter in the factory so it can be instantiated via `create_adapter("ollama", config)`.

#### Test First (TDD)

**Test file**: `tests/unit/test_adapters.py` (update TestAdapterFactory)

**Test structure**:
```python
class TestAdapterFactory:
    # ... existing tests ...

    def test_create_ollama_adapter():
        """Test creating OllamaAdapter via factory."""

    def test_factory_validates_http_config_for_ollama():
        """Test Ollama requires HTTP config, not CLI."""
```

**Example test**:
```python
def test_create_ollama_adapter(self):
    """Test creating OllamaAdapter via factory."""
    from models.config import HTTPAdapterConfig
    from adapters.ollama import OllamaAdapter

    config = HTTPAdapterConfig(
        type="http",
        base_url="http://localhost:11434",
        timeout=60
    )

    adapter = create_adapter("ollama", config)
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.base_url == "http://localhost:11434"
    assert adapter.timeout == 60

def test_factory_rejects_cli_config_for_ollama(self):
    """Test Ollama with CLI config raises error."""
    from models.config import CLIAdapterConfig

    config = CLIAdapterConfig(
        type="cli",
        command="ollama",
        args=[],
        timeout=60
    )

    with pytest.raises(ValueError) as exc_info:
        create_adapter("ollama", config)

    assert "http" in str(exc_info.value).lower()
```

#### Implementation

Update `adapters/__init__.py`:

```python
# Add to imports
from adapters.ollama import OllamaAdapter

# Update http_adapters dict in create_adapter()
http_adapters = {
    "ollama": OllamaAdapter,
}
```

#### Verification

```bash
pytest tests/unit/test_adapters.py::TestAdapterFactory::test_create_ollama_adapter -v
```

#### Commit

**Commit message**:
```
feat: register Ollama adapter in factory

Add OllamaAdapter to http_adapters registry in
create_adapter() factory function.
```

**Files to commit**:
- `adapters/__init__.py`
- `tests/unit/test_adapters.py`

---

### Task 11: Add Ollama to Example Config

**File(s)**: `config.yaml`
**Depends on**: Tasks 9-10
**Estimated time**: 10m

#### What you're building
Add Ollama adapter example to config.yaml demonstrating HTTP adapter configuration.

#### Implementation

Add to config.yaml after existing adapters:

```yaml
# New adapters section (replaces cli_tools)
adapters:
  # CLI adapters (existing tools with type: cli added)
  claude:
    type: cli
    command: "claude"
    args: ["-p", "--model", "{model}", "--settings", "{{\"disableAllHooks\": true}}", "{prompt}"]
    timeout: 300

  codex:
    type: cli
    command: "codex"
    args: ["exec", "--model", "{model}", "{prompt}"]
    timeout: 180

  droid:
    type: cli
    command: "droid"
    args: ["exec", "-m", "{model}", "{prompt}"]
    timeout: 180

  gemini:
    type: cli
    command: "gemini"
    args: ["-m", "{model}", "-p", "{prompt}"]
    timeout: 180

  # HTTP adapters (new)
  ollama:
    type: http
    base_url: "http://localhost:11434"
    timeout: 120
    max_retries: 3
    # No api_key needed for local Ollama
    # Valid models: "llama2", "mistral", "codellama", etc.
    # Run 'ollama list' to see available models
```

Also rename `cli_tools:` section to comment it out with deprecation note:

```yaml
# DEPRECATED: cli_tools section is deprecated, use adapters section above
# This section will be removed in v2.0
# To migrate: python scripts/migrate_config.py config.yaml
#
# cli_tools:
#   claude:
#     command: "claude"
#     ...
```

#### Verification

```bash
# Validate config loads correctly
python -c "from models.config import load_config; config = load_config(); print(f'Loaded {len(config.adapters)} adapters')"

# Should show: Loaded 5 adapters (claude, codex, droid, gemini, ollama)
```

#### Commit

**Commit message**:
```
feat: add Ollama to example config and migrate to adapters

Update config.yaml to use new adapters section with HTTP
adapter example (Ollama). Comment out deprecated cli_tools.
```

**Files to commit**:
- `config.yaml`

---

### Task 12: Update MCP Server Schema for Ollama

**File(s)**: `server.py`
**Depends on**: Task 10
**Estimated time**: 15m

#### What you're building
Update MCP tool schema to include Ollama in supported CLIs and recommended models.

#### Test First (TDD)

**Test file**: `tests/integration/test_mcp_server.py` (append)

**Test structure**:
```python
@pytest.mark.asyncio
async def test_deliberate_tool_includes_ollama():
    """Test that deliberate tool schema includes ollama."""

def test_ollama_in_recommended_models():
    """Test Ollama models in RECOMMENDED_MODELS."""
```

#### Implementation

Update `server.py`:

```python
# Add to RECOMMENDED_MODELS constant (around line 20)
RECOMMENDED_MODELS = {
    "claude": ["sonnet", "opus", "haiku"],
    "codex": ["gpt-5-codex", "o3"],
    "droid": ["claude-sonnet-4-5-20250929", "gpt-5-codex"],
    "gemini": ["gemini-2.5-pro"],
    "ollama": ["llama2", "mistral", "codellama", "qwen"],  # New
}

# Update deliberate tool description (around line 100)
# In list_tools() method:
{
    "name": "deliberate",
    "description": (
        "True deliberative consensus where AI models debate and refine "
        "positions across multiple rounds. Supports CLI tools (claude, codex, "
        "droid, gemini) and HTTP services (ollama). Models see each other's "
        "responses and can adjust their reasoning. Use for critical decisions, "
        "architecture choices, or complex technical debates."
    ),
    # ... rest of schema
}
```

#### Verification

```bash
# Start server
python server.py

# In another terminal, check tool schema
# (This would be done via MCP client, but we can test module directly)
python -c "from server import RECOMMENDED_MODELS; print('ollama' in RECOMMENDED_MODELS)"
```

#### Commit

**Commit message**:
```
feat: add Ollama to MCP server schema

Include Ollama in supported CLIs and recommended models
in MCP deliberate tool schema.
```

**Files to commit**:
- `server.py`
- `tests/integration/test_mcp_server.py`

---

## Phase 3: LM Studio & OpenRouter Adapters (Tasks 13-20)

[Similar structure for LM Studio (tasks 13-16) and OpenRouter (tasks 17-20)]

### Task 13: Implement LMStudioAdapter

[Similar to Task 9, adapted for LM Studio's OpenAI-compatible API]

---

### Task 17: Implement OpenRouterAdapter

[Similar to Task 9, adapted for OpenRouter's API with authentication]

---

## Phase 4: llama.cpp Adapter (Tasks 21-24)

### Task 21: Implement LlamaCppAdapter

**Note**: llama.cpp uses CLI, not HTTP, but has different output parsing than existing CLI adapters.

[Implementation details for llama.cpp CLI adapter]

---

## Phase 5: Integration & Documentation (Tasks 25-28)

### Task 25: Integration Test for Multi-Adapter Deliberation

**File(s)**: `tests/integration/test_multi_adapter_deliberation.py`
**Estimated time**: 30m

#### What you're building
End-to-end integration test that runs a deliberation with mix of CLI and HTTP adapters.

[Test details]

---

### Task 26: Update README with HTTP Adapter Examples

**File(s)**: `README.md`
**Estimated time**: 20m

#### What you're building
User-facing documentation showing how to configure and use HTTP adapters.

[Documentation updates]

---

### Task 27: Create HTTP Adapter Troubleshooting Guide

**File(s)**: `docs/troubleshooting/http-adapters.md`
**Estimated time**: 25m

#### What you're building
Troubleshooting guide for common HTTP adapter issues.

[Guide content]

---

### Task 28: Final Verification & Cleanup

**Estimated time**: 30m

#### Verification Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] No deprecation warnings in tests
- [ ] Config migration script works on example config
- [ ] Can create adapters via factory for all types
- [ ] Documentation complete and accurate
- [ ] CLAUDE.md reflects current architecture
- [ ] No leftover TODO comments
- [ ] Code formatted: `black .`
- [ ] No type errors: `mypy .` (if using mypy)

---

## Testing Strategy

### Unit Tests
- **Location**: `tests/unit/`
- **Naming**: `test_<module>.py`, class `Test<ClassName>`, method `test_<behavior>`
- **Run command**: `pytest tests/unit -v`
- **Coverage target**: >85% for new code
- **Mocking**: Use `unittest.mock.AsyncMock` for async methods, `@patch` for external dependencies

### Integration Tests
- **Location**: `tests/integration/`
- **What to test**: Factory integration, config loading, adapter creation
- **Setup required**: VCR cassettes recorded
- **Run command**: `pytest tests/integration -v`

### VCR Testing (HTTP Adapters)
- **Location**: `tests/fixtures/vcr_cassettes/<adapter>/`
- **Recording**: Run tests with real services once to record
- **Replaying**: Subsequent runs use recordings (fast, deterministic)
- **Updating**: Delete cassette files to re-record

### Test Design Principles

**Use these patterns**:
1. **Arrange-Act-Assert**: Clear test structure
2. **One assertion per test**: Test one behavior
3. **Descriptive names**: `test_retry_on_503_server_error` not `test_retry1`
4. **Mock external services**: Never hit real APIs in unit tests
5. **Use fixtures**: Share setup via conftest.py

**Avoid these anti-patterns**:
1. **Testing implementation**: Test behavior, not internal state
2. **Brittle assertions**: Don't assert exact string matches for error messages
3. **Test interdependence**: Tests must run independently
4. **Magic values**: Use descriptive constants

**Mocking guidelines**:
- Mock external services: `httpx.AsyncClient`, subprocess execution
- Don't mock: Pydantic validation, our own business logic
- Use project's pattern: See `tests/conftest.py::MockAdapter` for adapter mocking

---

## Commit Strategy

Break this work into 28 commits following this sequence:

**Phase 1: Foundation (Commits 1-8)**
1. feat: add HTTP adapter dependencies
2. feat: add adapter config models with type discrimination
3. feat: add BaseHTTPAdapter abstract class
4. feat: extend adapter factory for HTTP support
5. test: add config loader tests for adapter migration
6. feat: add config migration script
7. docs: add migration guide
8. docs: update CLAUDE.md

**Phase 2: Ollama (Commits 9-12)**
9. feat: add Ollama HTTP adapter
10. feat: register Ollama in factory
11. feat: add Ollama to config
12. feat: add Ollama to MCP schema

**Phase 3: LM Studio & OpenRouter (Commits 13-20)**
[Similar pattern]

**Phase 4: llama.cpp (Commits 21-24)**
[Implementation commits]

**Phase 5: Integration (Commits 25-28)**
25. test: add multi-adapter integration test
26. docs: update README with HTTP examples
27. docs: add HTTP adapter troubleshooting
28. chore: final cleanup and verification

**Commit message format**:
Follow existing pattern:
```
<type>: <subject>

[optional body]
```

Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`

---

## Common Pitfalls & How to Avoid Them

### 1. **Forgetting to add `type` field in config**
- **Why**: New adapters section requires explicit `type: cli` or `type: http`
- **How to avoid**: Always validate config after changes with `load_config()`
- **Reference**: `models/config.py:7-11` (CLIAdapterConfig)

### 2. **Not handling environment variable expansion**
- **Why**: API keys use `${VAR_NAME}` pattern
- **How to avoid**: Use `HTTPAdapterConfig.resolve_env_vars` validator
- **Reference**: `models/config.py:65-85` (field_validator)

### 3. **Retrying on 4xx errors**
- **Why**: Client errors (400, 401, 404) are not transient
- **How to avoid**: Only retry on 5xx, 429, network errors
- **Reference**: `adapters/base_http.py:is_retryable_http_error()`

### 4. **Not creating VCR cassettes**
- **Why**: Tests without recordings will fail in CI
- **How to avoid**: Run tests with real service once to record
- **Reference**: `tests/unit/test_ollama_adapter.py` (VCR usage)

### 5. **Breaking backward compatibility**
- **Why**: Existing `cli_tools` configs must still work
- **How to avoid**: Test with both old and new config formats
- **Reference**: `models/config.py:78-96` (Config validation)

### 6. **Forgetting async/await**
- **Why**: All adapters use async invoke
- **How to avoid**: Mark tests with `@pytest.mark.asyncio`, use `AsyncMock`
- **Reference**: `adapters/base.py:28` (invoke signature)

---

## Resources & References

### Existing Code to Reference
- **CLI adapter pattern**: `adapters/base.py`, `adapters/claude.py`
- **Factory pattern**: `adapters/__init__.py::create_adapter()`
- **Config validation**: `models/config.py`
- **Test fixtures**: `tests/conftest.py`
- **Async testing**: `tests/unit/test_adapters.py::TestClaudeAdapter::test_invoke_success`

### External Documentation
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md
- **httpx docs**: https://www.python-httpx.org/
- **tenacity docs**: https://tenacity.readthedocs.io/
- **VCR.py docs**: https://vcrpy.readthedocs.io/
- **Pydantic validators**: https://docs.pydantic.dev/latest/concepts/validators/

### Testing Resources
- **pytest async**: https://pytest-asyncio.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **VCR patterns**: See `tests/unit/test_ollama_adapter.py` after Task 9

### Validation Checklist
- [ ] All tests pass: `pytest tests/unit -v`
- [ ] Config validates: `python -c "from models.config import load_config; load_config()"`
- [ ] Migration works: `python scripts/migrate_config.py config.yaml`
- [ ] No linter errors: `ruff check .` (if using ruff)
- [ ] Formatted correctly: `black . --check`
- [ ] No debug prints: `grep -r "print(" adapters/ models/` returns nothing
- [ ] Error handling: All adapters raise clear errors
- [ ] Edge cases: Empty responses, timeouts, network errors tested

---

## Summary

This implementation plan adds HTTP adapter support to AI Counsel through 28 discrete tasks organized into 5 phases:

**Phase 1 (Tasks 1-8)**: Foundation - config models, BaseHTTPAdapter, migration tooling
**Phase 2 (Tasks 9-12)**: Ollama adapter - first HTTP adapter, establishes pattern
**Phase 3 (Tasks 13-20)**: LM Studio & OpenRouter - additional HTTP adapters
**Phase 4 (Tasks 21-24)**: llama.cpp adapter - CLI with complex parsing
**Phase 5 (Tasks 25-28)**: Integration tests, documentation, final verification

**Start with**: Task 1 (Add HTTP dependencies)

**Estimated completion**: 12-16 hours over ~3-4 days

**Key principles**:
- TDD: Write tests before implementation
- Frequent commits: After each task
- Backward compatibility: Support both old and new configs
- Clear errors: Helpful messages for misconfigurations
- Simple: Follow YAGNI, avoid over-engineering
