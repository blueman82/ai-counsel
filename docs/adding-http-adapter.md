# Adding a New HTTP Adapter

This guide walks through creating a new HTTP adapter for the AI Counsel deliberation system.

## Steps

### 1. Create adapter file in `adapters/your_adapter.py`

Subclass `BaseHTTPAdapter` and implement the required methods:

```python
from adapters.base_http import BaseHTTPAdapter
from typing import Tuple

class YourAdapter(BaseHTTPAdapter):
    def build_request(self, model: str, prompt: str) -> Tuple[str, dict, dict]:
        """Build HTTP request components.

        Returns:
            (endpoint, headers, body) tuple
        """
        endpoint = "/api/generate"
        headers = {"Content-Type": "application/json"}
        body = {"model": model, "prompt": prompt}
        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """Extract text from API response.

        Args:
            response_json: Parsed JSON response from API

        Returns:
            Response text string
        """
        return response_json["response"]
```

### 2. Update config in `config.yaml`

```yaml
adapters:
  your_adapter:
    type: http
    base_url: "https://api.example.com"
    api_key: "${YOUR_API_KEY}"  # Environment variable substitution
    timeout: 60
    max_retries: 3
```

### 3. Register adapter in `adapters/__init__.py`

```python
from adapters.your_adapter import YourAdapter

def create_adapter(name: str, config: AdapterConfig):
    http_adapters = {
        "ollama": OllamaAdapter,
        "lmstudio": LMStudioAdapter,
        "your_adapter": YourAdapter,  # Add here
    }
    # ... rest of factory logic
```

### 4. Set environment variables (if using API keys)

```bash
export YOUR_API_KEY="your-key-here"
```

### 5. Write tests

**Unit tests** in `tests/unit/test_your_adapter.py`:

```python
import pytest
from adapters.your_adapter import YourAdapter

def test_build_request():
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key="test-key",
        timeout=60
    )
    endpoint, headers, body = adapter.build_request(
        model="test-model",
        prompt="Hello"
    )

    assert endpoint == "/api/generate"
    assert headers["Content-Type"] == "application/json"
    assert body["model"] == "test-model"
    assert body["prompt"] == "Hello"

def test_parse_response():
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key="test-key",
        timeout=60
    )
    response_json = {"response": "Hello there!"}
    result = adapter.parse_response(response_json)

    assert result == "Hello there!"
```

**Integration tests** (optional, requires running service):
- Use VCR for HTTP response recording: `tests/fixtures/vcr_cassettes/your_adapter/`
- Record real API interactions once, replay in tests

### 6. Test with deliberation

```python
from adapters.your_adapter import YourAdapter
import asyncio

async def test():
    adapter = YourAdapter(
        base_url="https://api.example.com",
        api_key="your-key",
        timeout=60
    )
    result = await adapter.invoke(prompt="Hello", model="model-name")
    print(result)

asyncio.run(test())
```

## Features Provided by BaseHTTPAdapter

The base class handles:
- **Retry logic**: Exponential backoff on 5xx/429/network errors
- **Fail-fast**: Immediate failure on 4xx client errors
- **Authentication**: Environment variable substitution in config
- **Async HTTP**: Uses `httpx` for non-blocking requests
- **Timeout handling**: Configurable per-request timeouts
- **Error handling**: Structured error responses

## Common Patterns

### Streaming Responses

```python
async def invoke(self, prompt: str, model: str) -> str:
    endpoint, headers, body = self.build_request(model, prompt)
    url = f"{self.base_url}{endpoint}"

    chunks = []
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=body) as response:
            async for chunk in response.aiter_text():
                chunks.append(chunk)

    return "".join(chunks)
```

### Custom Headers

```python
def build_request(self, model: str, prompt: str) -> Tuple[str, dict, dict]:
    endpoint = "/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}",
        "X-Custom-Header": "value"
    }
    body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    return (endpoint, headers, body)
```

### Error Handling

```python
def parse_response(self, response_json: dict) -> str:
    if "error" in response_json:
        raise ValueError(f"API error: {response_json['error']}")

    if "choices" not in response_json:
        raise ValueError("Invalid response format: missing 'choices'")

    return response_json["choices"][0]["message"]["content"]
```

## Testing

```bash
# Unit tests
pytest tests/unit/test_your_adapter.py -v

# With VCR cassettes
pytest tests/unit/test_your_adapter.py --vcr-record=none -v
```

## Retry Configuration

The base adapter uses `tenacity` for retry with exponential backoff:

- **Retryable errors**: 5xx, 429 (rate limit), network errors
- **Non-retryable errors**: 4xx client errors (except 429)
- **Max retries**: Configurable via `max_retries` in config
- **Backoff**: Exponential with jitter

To customize retry behavior, override `invoke()` in your adapter.
