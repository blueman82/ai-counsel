# Adding a New CLI Adapter

This guide walks through creating a new CLI adapter for the AI Counsel deliberation system.

## Steps

### 1. Create adapter file in `adapters/your_cli.py`
- Subclass `BaseCLIAdapter`
- Implement `parse_output(raw_output: str) -> str`
- Handle any tool-specific output formatting

Example:
```python
from adapters.base import BaseCLIAdapter

class YourCLIAdapter(BaseCLIAdapter):
    def parse_output(self, raw_output: str) -> str:
        # Remove tool-specific wrappers, headers, etc.
        # Return clean response text
        return raw_output.strip()
```

### 2. Update config in `config.yaml`
```yaml
adapters:
  your_cli:
    type: cli
    command: "your-cli"
    args: ["--model", "{model}", "{prompt}"]
    timeout: 60
```

### 3. Register adapter in `adapters/__init__.py`
- Import adapter class
- Add to `cli_adapters` dict in `create_adapter()`

Example:
```python
from adapters.your_cli import YourCLIAdapter

def create_adapter(name: str, config: AdapterConfig):
    cli_adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "your_cli": YourCLIAdapter,  # Add here
    }
    # ... rest of factory logic
```

### 4. Update schema in `models/schema.py`
- Add CLI name to `Participant.cli` Literal type
- Update MCP tool description in `server.py`

Example:
```python
class Participant(BaseModel):
    cli: Literal["claude", "codex", "droid", "gemini", "your_cli"]  # Add here
    model: str
```

### 5. Add recommended models in `server.py::RECOMMENDED_MODELS`

Example:
```python
RECOMMENDED_MODELS = {
    "claude": ["claude-sonnet-4-5-20250929", ...],
    "your_cli": ["model-name-1", "model-name-2"],
}
```

### 6. Write tests in `tests/unit/test_adapters.py` and `tests/integration/`

Unit test example:
```python
def test_your_cli_adapter_parse_output():
    adapter = YourCLIAdapter(command="your-cli", args=[], timeout=60)
    raw = "WRAPPER_START\nActual response\nWRAPPER_END"
    parsed = adapter.parse_output(raw)
    assert parsed == "Actual response"
```

Integration test example:
```python
@pytest.mark.integration
async def test_your_cli_adapter_invoke():
    adapter = YourCLIAdapter(command="your-cli", args=["--model", "{model}", "{prompt}"], timeout=60)
    result = await adapter.invoke(prompt="Hello", model="model-name")
    assert isinstance(result, str)
    assert len(result) > 0
```

## Testing

```bash
# Unit tests
pytest tests/unit/test_adapters.py::test_your_cli_adapter_parse_output -v

# Integration tests (requires CLI tool installed)
pytest tests/integration -k your_cli -v
```

## Common Patterns

**Removing wrappers**:
```python
def parse_output(self, raw_output: str) -> str:
    # Remove markdown code fences
    if raw_output.startswith("```") and raw_output.endswith("```"):
        lines = raw_output.split("\n")
        return "\n".join(lines[1:-1])
    return raw_output
```

**Extracting JSON responses**:
```python
import json

def parse_output(self, raw_output: str) -> str:
    data = json.loads(raw_output)
    return data["response"]
```

**Handling errors**:
```python
def parse_output(self, raw_output: str) -> str:
    if "ERROR:" in raw_output:
        raise ValueError(f"CLI returned error: {raw_output}")
    return raw_output.strip()
```
