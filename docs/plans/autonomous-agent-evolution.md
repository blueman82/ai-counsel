# Implementation Plan: Autonomous Agent Evolution with Token Monitoring

**Created**: 2025-10-28
**Target**: Evolve AI Counsel from deliberative consensus system to fully autonomous agent swarm
**Estimated Tasks**: 24 tasks across 3 phases
**Estimated Time**: 6-8 weeks

## Context for the Engineer

You are implementing this feature in a codebase that:
- Uses **Python 3.11+** with **asyncio** for concurrent execution
- Follows **Pydantic** for data validation and type safety
- Tests with **pytest** (unit, integration, e2e markers)
- Uses **TDD** (Test-Driven Development) - write tests BEFORE implementation
- Stores data in **SQLite** via `decision_graph/storage.py`
- Follows existing patterns in `deliberation/engine.py` for orchestration

**You are expected to**:
- Write tests BEFORE implementation (TDD - red, green, refactor)
- Commit frequently (after each completed task)
- Follow existing code patterns (see `deliberation/engine.py`, `adapters/base.py`)
- Keep changes minimal (YAGNI - You Aren't Gonna Need It)
- Avoid duplication (DRY - Don't Repeat Yourself)
- Use type hints consistently
- Log at appropriate levels (debug, info, warning, error)

## Prerequisites Checklist

Before starting, verify:
- [ ] Python 3.11+ installed: `python --version`
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Tests pass: `pytest tests/unit -v`
- [ ] Branch created: `git checkout -b feature/autonomous-agent-evolution`
- [ ] Familiar with existing architecture (read `CLAUDE.md` sections on Engine, Adapters, Decision Graph)

---

# PHASE 1: TOKEN TRACKING & MODEL TIERING FOUNDATION (Weeks 1-2)

## Task 1: Add Token Usage Data Models

**File(s)**: `models/schema.py`
**Depends on**: None
**Estimated time**: 30m

### What you're building
Create Pydantic models for tracking token usage at three granularities (per-agent, per-round, per-deliberation) with accuracy classification to distinguish between exact API measurements and tiktoken estimations.

### Test First (TDD)

**Test file**: `tests/unit/test_token_models.py`

**Test structure**:
```python
class TestTokenUsage:
    - test_token_usage_creation_with_all_fields
    - test_token_usage_accuracy_enum_validation
    - test_token_usage_total_tokens_calculated_correctly
    - test_token_usage_with_reasoning_tokens
    - test_session_token_tracker_initialization
    - test_session_token_tracker_record_exact_tokens
    - test_session_token_tracker_record_estimated_tokens
    - test_session_token_tracker_get_cost_confidence
    - test_session_token_tracker_by_solution_aggregation
    - test_session_token_tracker_by_round_tracking
```

**Test specifics**:
- Mock nothing (these are pure data models)
- Use Pydantic's ValidationError for validation tests
- Assert TokenAccuracy enum values
- Test cost_confidence calculation: exact/(exact+estimated)

**Example test skeleton**:
```python
import pytest
from models.schema import TokenUsage, TokenAccuracy, SessionTokenTracker

class TestTokenUsage:
    def test_token_usage_creation_with_all_fields(self):
        """Test creating TokenUsage with all required fields."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            reasoning_tokens=25,
            total_tokens=175,
            accuracy=TokenAccuracy.EXACT,
            adapter_type="claude",
            model="sonnet",
            timestamp="2025-10-28T12:00:00",
            cost_usd=0.0042
        )
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.reasoning_tokens == 25
        assert usage.total_tokens == 175
        assert usage.accuracy == TokenAccuracy.EXACT

    def test_token_usage_accuracy_enum_validation(self):
        """Test that accuracy field only accepts valid enum values."""
        with pytest.raises(ValidationError):
            TokenUsage(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                accuracy="invalid",  # Should fail
                adapter_type="claude",
                model="sonnet",
                timestamp="2025-10-28T12:00:00"
            )
```

### Implementation

**Approach**:
Add new models to `models/schema.py` following existing patterns for `Participant`, `Vote`, etc.

**Code structure**:
```python
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class TokenAccuracy(str, Enum):
    """Accuracy level of token measurements."""
    EXACT = "exact"        # From API response (HTTP adapters)
    ESTIMATED = "estimated"  # From tiktoken (CLI adapters)
    UNAVAILABLE = "unavailable"  # Adapter failed

class TokenUsage(BaseModel):
    """Token usage for a single adapter invocation."""
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(ge=0)
    accuracy: TokenAccuracy
    adapter_type: str
    model: str
    timestamp: str
    cost_usd: Optional[float] = Field(default=None, ge=0)

class SessionTokenTracker:
    """In-memory tracker for active deliberation session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.by_solution: Dict[str, Dict[str, int]] = {}  # {solution: {exact: X, estimated: Y, total: Z}}
        self.by_round: List[int] = []
        self.start_time: str = datetime.now().isoformat()

    def record(self, solution: str, tokens: TokenUsage, round_num: int) -> None:
        """Record tokens for solution and round."""
        # Implementation details in actual code

    def get_cost_confidence(self) -> float:
        """Return ratio of exact to total tokens."""
        # Implementation details in actual code
```

**Key points**:
- Follow pattern from `Vote` model in `models/schema.py:75`
- Use `Field(ge=0)` for non-negative integer validation
- `SessionTokenTracker` is NOT a Pydantic model (plain Python class for performance)
- Import `datetime` from Python standard library

**Integration points**:
- Imports needed: `from enum import Enum`, `from datetime import datetime`
- Will be used by: `deliberation/engine.py`, `adapters/base.py`

### Verification

**Manual testing**:
```python
# In Python REPL
from models.schema import TokenUsage, TokenAccuracy, SessionTokenTracker
usage = TokenUsage(
    input_tokens=100, output_tokens=50, total_tokens=150,
    accuracy=TokenAccuracy.EXACT, adapter_type="claude",
    model="sonnet", timestamp="2025-10-28T12:00:00"
)
print(usage.model_dump())
```

**Automated tests**:
```bash
pytest tests/unit/test_token_models.py -v
```

**Expected output**:
```
tests/unit/test_token_models.py::TestTokenUsage::test_token_usage_creation_with_all_fields PASSED
tests/unit/test_token_models.py::TestTokenUsage::test_token_usage_accuracy_enum_validation PASSED
[8 tests passed]
```

### Commit

**Commit message**:
```
feat(models): add token usage tracking models

- Add TokenUsage model with accuracy classification
- Add TokenAccuracy enum (exact/estimated/unavailable)
- Add SessionTokenTracker for in-memory aggregation
- Support three granularities: per-agent, per-round, per-deliberation
```

**Files to commit**:
- `models/schema.py`
- `tests/unit/test_token_models.py`

---

## Task 2: Extend Adapter Base Classes with Token Reporting

**File(s)**: `adapters/base.py`, `adapters/base_http.py`
**Depends on**: Task 1
**Estimated time**: 1h

### What you're building
Add `invoke_with_metadata()` method to both `BaseCLIAdapter` and `BaseHTTPAdapter` that returns tuple of (response, TokenUsage). CLI adapters estimate using tiktoken, HTTP adapters parse from API responses.

### Test First (TDD)

**Test file**: `tests/unit/test_adapter_token_tracking.py`

**Test structure**:
```python
class TestBaseCLIAdapterTokens:
    - test_invoke_with_metadata_returns_tuple
    - test_get_token_usage_estimates_with_tiktoken
    - test_get_token_usage_fallback_without_tiktoken
    - test_token_usage_marked_as_estimated

class TestBaseHTTPAdapterTokens:
    - test_invoke_with_metadata_ollama_actual_counts
    - test_invoke_with_metadata_gemini_actual_counts
    - test_token_usage_marked_as_exact
    - test_token_usage_fallback_on_missing_usage_field
```

**Test specifics**:
- Mock `tiktoken.get_encoding()` for CLI tests
- Use VCR cassettes for HTTP API response mocking (see `tests/unit/test_ollama_adapter.py` pattern)
- Assert TokenAccuracy is ESTIMATED for CLI, EXACT for HTTP
- Test fallback path when tiktoken unavailable (4 chars/token heuristic)

**Example test skeleton**:
```python
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from adapters.base import BaseCLIAdapter
from models.schema import TokenUsage, TokenAccuracy

class TestBaseCLIAdapterTokens:
    @pytest.mark.asyncio
    async def test_invoke_with_metadata_returns_tuple(self):
        """Test that invoke_with_metadata returns (response, TokenUsage) tuple."""
        adapter = MockCLIAdapter()
        adapter.invoke_mock.return_value = "Test response"

        response, token_usage = await adapter.invoke_with_metadata(
            prompt="Test prompt",
            model="test-model"
        )

        assert isinstance(response, str)
        assert response == "Test response"
        assert isinstance(token_usage, TokenUsage)
        assert token_usage.adapter_type == "mockcli"
        assert token_usage.accuracy == TokenAccuracy.ESTIMATED

    @patch('tiktoken.get_encoding')
    def test_get_token_usage_estimates_with_tiktoken(self, mock_get_encoding):
        """Test token estimation using tiktoken."""
        mock_encoding = MagicMock()
        mock_encoding.encode.side_effect = [
            [1, 2, 3, 4, 5],  # 5 tokens for prompt
            [6, 7, 8]  # 3 tokens for response
        ]
        mock_get_encoding.return_value = mock_encoding

        adapter = MockCLIAdapter()
        usage = adapter._get_token_usage(
            prompt="Test prompt",
            response="Response",
            model="test-model"
        )

        assert usage.input_tokens == 5
        assert usage.output_tokens == 3
        assert usage.total_tokens == 8
        assert usage.accuracy == TokenAccuracy.ESTIMATED
```

### Implementation

**Approach**:
Add optional `invoke_with_metadata()` alongside existing `invoke()` method. Default implementation in base class, overridden in HTTP adapters where actual counts available.

**Code structure** (`adapters/base.py`):
```python
async def invoke_with_metadata(
    self, prompt: str, model: str, context: Optional[str] = None, is_deliberation: bool = True
) -> Tuple[str, TokenUsage]:
    """
    Invoke adapter and return response with token metadata.

    Returns:
        Tuple of (response, token_usage)
    """
    response = await self.invoke(prompt, model, context, is_deliberation)
    tokens = self._get_token_usage(prompt, response, model)
    return (response, tokens)

def _get_token_usage(self, prompt: str, response: str, model: str) -> TokenUsage:
    """
    Estimate token usage using tiktoken with fallback.

    Override in subclass if adapter provides actual counts.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        input_tokens = len(enc.encode(prompt))
        output_tokens = len(enc.encode(response))
    except (ImportError, Exception):
        # Fallback: conservative 4 chars/token estimate
        input_tokens = len(prompt) // 4
        output_tokens = len(response) // 4

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=0,
        total_tokens=input_tokens + output_tokens,
        adapter_type=self.__class__.__name__.lower().replace("adapter", ""),
        model=model,
        timestamp=datetime.now().isoformat(),
        accuracy=TokenAccuracy.ESTIMATED
    )
```

**Code structure** (`adapters/base_http.py`):
```python
# Override in HTTP adapters to parse actual counts
async def invoke_with_metadata(...) -> Tuple[str, TokenUsage]:
    """HTTP adapters parse actual token counts from API responses."""
    response_json = await self._make_request(...)
    text = self.parse_response(response_json)
    tokens = self._extract_token_usage(response_json, model)
    return (text, tokens)

def _extract_token_usage(self, response_json: dict, model: str) -> TokenUsage:
    """Extract actual token counts from API response."""
    # Implementation varies by adapter (Ollama, Gemini, etc.)
    return TokenUsage(..., accuracy=TokenAccuracy.EXACT)
```

**Key points**:
- Follow async pattern from existing `invoke()` method in `adapters/base.py:50`
- Use `Tuple` type hint: `from typing import Tuple`
- tiktoken import is lazy (try/except block) since it's optional dependency
- HTTP adapters override to provide EXACT counts

**Integration points**:
- Imports needed: `from typing import Tuple`, `from datetime import datetime`, `from models.schema import TokenUsage, TokenAccuracy`
- Modify imports in `adapters/__init__.py` if needed
- Will be called by: `deliberation/engine.py` in execute_round()

### Verification

**Manual testing**:
```bash
# Test tiktoken estimation
python -c "
from adapters.claude import ClaudeAdapter
import asyncio
adapter = ClaudeAdapter(timeout=60)
prompt = 'Test prompt'
response = 'Test response'
usage = adapter._get_token_usage(prompt, response, 'sonnet')
print(f'Tokens: {usage.total_tokens}, Accuracy: {usage.accuracy}')
"
```

**Automated tests**:
```bash
pytest tests/unit/test_adapter_token_tracking.py -v
```

**Expected output**:
```
tests/unit/test_adapter_token_tracking.py::TestBaseCLIAdapterTokens::test_invoke_with_metadata_returns_tuple PASSED
tests/unit/test_adapter_token_tracking.py::TestBaseCLIAdapterTokens::test_get_token_usage_estimates_with_tiktoken PASSED
[8 tests passed]
```

### Commit

**Commit message**:
```
feat(adapters): add token usage reporting to adapters

- Add invoke_with_metadata() to BaseCLIAdapter and BaseHTTPAdapter
- CLI adapters estimate tokens using tiktoken with fallback
- HTTP adapters extract actual counts from API responses
- Mark CLI tokens as ESTIMATED, HTTP as EXACT
```

**Files to commit**:
- `adapters/base.py`
- `adapters/base_http.py`
- `tests/unit/test_adapter_token_tracking.py`

---

## Task 3: Integrate Token Tracking into DeliberationEngine

**File(s)**: `deliberation/engine.py`
**Depends on**: Task 2
**Estimated time**: 1h

### What you're building
Modify `execute_round()` to use `invoke_with_metadata()` instead of `invoke()`, track tokens in SessionTokenTracker, and include token stats in DeliberationResult.

### Test First (TDD)

**Test file**: `tests/unit/test_engine_token_tracking.py`

**Test structure**:
```python
class TestEngineTokenTracking:
    - test_execute_round_tracks_tokens_per_agent
    - test_execute_round_aggregates_tokens_by_solution
    - test_execute_round_tracks_tokens_by_round
    - test_deliberation_result_includes_token_stats
    - test_token_tracking_handles_adapter_failures
```

**Test specifics**:
- Use `mock_adapters` fixture from `tests/conftest.py`
- Mock `invoke_with_metadata()` to return (response, TokenUsage)
- Assert SessionTokenTracker.by_solution has correct aggregation
- Assert DeliberationResult.token_stats exists and has expected structure

**Example test skeleton**:
```python
import pytest
from deliberation.engine import DeliberationEngine
from models.schema import Participant, TokenUsage, TokenAccuracy

class TestEngineTokenTracking:
    @pytest.mark.asyncio
    async def test_execute_round_tracks_tokens_per_agent(self, mock_adapters):
        """Test that tokens are tracked for each participant."""
        engine = DeliberationEngine(mock_adapters)

        # Mock invoke_with_metadata to return token usage
        mock_adapters["claude"].invoke_with_metadata = AsyncMock(
            return_value=("Response", TokenUsage(
                input_tokens=100, output_tokens=50, total_tokens=150,
                accuracy=TokenAccuracy.ESTIMATED, adapter_type="claude",
                model="sonnet", timestamp="2025-10-28T12:00:00"
            ))
        )

        participants = [Participant(cli="claude", model="sonnet", stance="neutral")]

        responses, tracker = await engine.execute_round(
            round_num=1,
            prompt="Test",
            participants=participants,
            previous_responses=[],
            token_tracker=SessionTokenTracker("test-session")
        )

        assert tracker.by_solution["claude"]["total"] == 150
        assert len(tracker.by_round) == 1
        assert tracker.by_round[0] == 150
```

### Implementation

**Approach**:
Modify `execute_round()` to accept optional `token_tracker` parameter, call `invoke_with_metadata()` instead of `invoke()`, and record tokens for each participant.

**Code structure** (`deliberation/engine.py`):
```python
async def execute_round(
    self,
    round_num: int,
    prompt: str,
    participants: List[Participant],
    previous_responses: List[RoundResponse],
    token_tracker: Optional[SessionTokenTracker] = None
) -> Tuple[List[RoundResponse], Optional[SessionTokenTracker]]:
    """Execute single deliberation round with token tracking."""

    # Initialize tracker if not provided
    if token_tracker is None:
        token_tracker = SessionTokenTracker(f"session-{datetime.now().isoformat()}")

    # ... existing context building logic ...

    # Execute adapter invocations
    for participant in participants:
        adapter = self.adapters[participant.cli]

        # Use invoke_with_metadata for token tracking
        if hasattr(adapter, 'invoke_with_metadata'):
            response, token_usage = await adapter.invoke_with_metadata(
                prompt=final_prompt,
                model=participant.model,
                context=context_str,
                is_deliberation=True
            )

            # Record tokens
            token_tracker.record(participant.cli, token_usage, round_num)
        else:
            # Fallback to invoke() if adapter doesn't support metadata
            response = await adapter.invoke(...)

        # ... existing response processing ...

    return responses, token_tracker
```

**Key points**:
- Follow pattern from existing `execute_round()` in `deliberation/engine.py:150`
- Return tuple of (responses, tracker) instead of just responses
- Handle backward compatibility: if adapter doesn't have `invoke_with_metadata`, fall back to `invoke()`
- Use `hasattr()` check for backward compatibility

**Integration points**:
- Imports needed: `from models.schema import SessionTokenTracker, TokenUsage`
- Modify `execute()` method to create and pass tracker between rounds
- Update `DeliberationResult` schema to include `token_stats` field

### Verification

**Manual testing**:
```bash
# Run existing integration tests to ensure backward compatibility
pytest tests/integration/test_engine_convergence.py -v
```

**Automated tests**:
```bash
pytest tests/unit/test_engine_token_tracking.py -v
```

**Expected output**:
```
tests/unit/test_engine_token_tracking.py::TestEngineTokenTracking::test_execute_round_tracks_tokens_per_agent PASSED
tests/unit/test_engine_token_tracking.py::TestEngineTokenTracking::test_execute_round_aggregates_tokens_by_solution PASSED
[5 tests passed]
```

### Commit

**Commit message**:
```
feat(engine): integrate token tracking into deliberation rounds

- Modify execute_round() to use invoke_with_metadata()
- Track tokens per agent, per round, per solution
- Return SessionTokenTracker alongside responses
- Maintain backward compatibility with adapters lacking metadata support
```

**Files to commit**:
- `deliberation/engine.py`
- `tests/unit/test_engine_token_tracking.py`

---

## Task 4: Add Model Tier Selection Logic

**File(s)**: `deliberation/model_selector.py` (new file)
**Depends on**: Task 3
**Estimated time**: 1h 30m

### What you're building
Create `ModelTierSelector` class that analyzes convergence trajectory, vote distribution, and budget to autonomously select between "fast" (haiku, gpt-3.5) and "reasoning" (sonnet, gpt-5-codex) model tiers.

### Test First (TDD)

**Test file**: `tests/unit/test_model_selector.py`

**Test structure**:
```python
class TestModelTierSelector:
    - test_round_1_defaults_to_reasoning
    - test_budget_hard_override_forces_fast_models
    - test_convergence_above_70_triggers_fast_models
    - test_divergence_triggers_reasoning_models
    - test_vote_split_triggers_reasoning_models
    - test_unanimous_vote_triggers_fast_models
    - test_convergence_trajectory_increasing_allows_fast
    - test_convergence_trajectory_decreasing_forces_reasoning
```

**Test specifics**:
- Mock nothing (pure logic tests)
- Test each decision path independently
- Use realistic convergence values (0.0-1.0 range)
- Assert returns Literal["fast"] or Literal["reasoning"]

**Example test skeleton**:
```python
import pytest
from deliberation.model_selector import ModelTierSelector

class TestModelTierSelector:
    def test_round_1_defaults_to_reasoning(self):
        """Test that Round 1 always uses reasoning models for decomposition."""
        selector = ModelTierSelector()

        tier = selector.select_tier(
            round_num=1,
            convergence_history=[],
            vote_distribution={},
            budget_remaining_pct=1.0
        )

        assert tier == "reasoning"

    def test_budget_hard_override_forces_fast_models(self):
        """Test that <10% budget always forces fast models."""
        selector = ModelTierSelector()

        tier = selector.select_tier(
            round_num=2,
            convergence_history=[0.50],
            vote_distribution={"option1": 2, "option2": 1},  # Split
            budget_remaining_pct=0.08  # 8% remaining
        )

        assert tier == "fast"  # Budget override

    def test_convergence_above_70_triggers_fast_models(self):
        """Test that >=70% convergence triggers fast model de-escalation."""
        selector = ModelTierSelector()

        tier = selector.select_tier(
            round_num=2,
            convergence_history=[0.65, 0.72],  # Increasing and above threshold
            vote_distribution={"option1": 2, "option2": 1},
            budget_remaining_pct=0.50
        )

        assert tier == "fast"
```

### Implementation

**Approach**:
Create decision tree that evaluates conditions in priority order: budget override → round 1 default → convergence trajectory → vote distribution.

**Code structure** (`deliberation/model_selector.py`):
```python
"""Model tier selection based on deliberation dynamics."""
from typing import Dict, List, Literal

class ModelTierSelector:
    """
    Selects between fast and reasoning model tiers based on:
    - Budget constraints (hard override)
    - Convergence trajectory (behavioral signal)
    - Vote distribution (consensus indicator)
    - Round number (cold start)
    """

    def __init__(
        self,
        convergence_threshold: float = 0.70,
        budget_hard_limit: float = 0.10,
    ):
        """
        Initialize selector with thresholds.

        Args:
            convergence_threshold: Similarity % to trigger fast models
            budget_hard_limit: Budget % that forces fast models
        """
        self.convergence_threshold = convergence_threshold
        self.budget_hard_limit = budget_hard_limit

    def select_tier(
        self,
        round_num: int,
        convergence_history: List[float],
        vote_distribution: Dict[str, int],
        budget_remaining_pct: float
    ) -> Literal["fast", "reasoning"]:
        """
        Select model tier based on current deliberation state.

        Returns:
            "fast" for haiku/gpt-3.5, "reasoning" for sonnet/gpt-5-codex
        """
        # HARD OVERRIDE: Budget constraint
        if budget_remaining_pct < self.budget_hard_limit:
            return "fast"

        # ROUND 1: Default to reasoning for problem decomposition
        if round_num == 1:
            return "reasoning"

        # ROUND 2+: Use behavioral signals

        # Convergence trajectory analysis
        if len(convergence_history) >= 2:
            current = convergence_history[-1]
            previous = convergence_history[-2]

            # Diverging: need deeper analysis
            if current < previous - 0.15:
                return "reasoning"

            # Converging well: fast models sufficient
            if current >= self.convergence_threshold and current > previous:
                return "fast"

        # Vote distribution analysis
        if len(vote_distribution) == 1:  # Unanimous
            return "fast"
        elif len(vote_distribution) >= 3:  # Split 3 ways
            return "reasoning"

        # Default: conservative (reasoning)
        return "reasoning"
```

**Key points**:
- Use `Literal` type hint for return value (import from `typing`)
- Decision tree evaluates in order: hard constraints first, then behavioral signals
- Convergence threshold of 0.70 (70%) from counsel's recommendation
- Budget hard limit of 0.10 (10%) from counsel's recommendation

**Integration points**:
- Imports needed: `from typing import Dict, List, Literal`
- Will be called by: `deliberation/engine.py` before each round
- Configuration from: `config.yaml` (add model_selection section)

### Verification

**Manual testing**:
```python
# In Python REPL
from deliberation.model_selector import ModelTierSelector
selector = ModelTierSelector()

# Test various scenarios
print(selector.select_tier(1, [], {}, 1.0))  # Should be "reasoning"
print(selector.select_tier(2, [0.75, 0.80], {"A": 3}, 0.50))  # Should be "fast"
print(selector.select_tier(2, [0.60, 0.45], {"A": 1, "B": 1, "C": 1}, 0.50))  # Should be "reasoning"
```

**Automated tests**:
```bash
pytest tests/unit/test_model_selector.py -v
```

**Expected output**:
```
tests/unit/test_model_selector.py::TestModelTierSelector::test_round_1_defaults_to_reasoning PASSED
tests/unit/test_model_selector.py::TestModelTierSelector::test_budget_hard_override_forces_fast_models PASSED
[8 tests passed]
```

### Commit

**Commit message**:
```
feat(deliberation): add behavioral model tier selection

- Create ModelTierSelector with decision tree logic
- Prioritize convergence trajectory over static analysis
- Implement budget hard override at 10% remaining
- Use 70% convergence threshold for fast model de-escalation
```

**Files to commit**:
- `deliberation/model_selector.py`
- `tests/unit/test_model_selector.py`

---

## Task 5: Add SQLite Storage for Token Totals

**File(s)**: `decision_graph/storage.py`
**Depends on**: Task 1
**Estimated time**: 45m

### What you're building
Extend `DecisionGraphStorage` with new `solution_token_totals` table and atomic increment operations for tracking lifetime token usage per solution (claude, codex, gemini, etc.).

### Test First (TDD)

**Test file**: `tests/unit/test_storage_token_totals.py`

**Test structure**:
```python
class TestStorageTokenTotals:
    - test_create_solution_token_totals_table
    - test_increment_solution_totals_new_solution
    - test_increment_solution_totals_existing_solution
    - test_increment_solution_totals_atomic_operation
    - test_get_solution_totals_empty
    - test_get_solution_totals_with_data
    - test_solution_totals_cost_confidence_intervals
```

**Test specifics**:
- Use in-memory SQLite: `":memory:"`
- Test atomic increments with concurrent writes (use asyncio.gather)
- Assert cost_lower_bound and cost_upper_bound calculated correctly
- Mock nothing (test against real SQLite)

**Example test skeleton**:
```python
import pytest
from decision_graph.storage import DecisionGraphStorage

class TestStorageTokenTotals:
    @pytest.mark.asyncio
    async def test_create_solution_token_totals_table(self):
        """Test that solution_token_totals table is created on init."""
        storage = DecisionGraphStorage(":memory:")

        # Query SQLite to verify table exists
        cursor = storage.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='solution_token_totals'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "solution_token_totals"

    @pytest.mark.asyncio
    async def test_increment_solution_totals_new_solution(self):
        """Test incrementing totals for a new solution."""
        storage = DecisionGraphStorage(":memory:")

        await storage.increment_solution_totals({
            "claude": {
                "total": 1000,
                "exact": 800,
                "estimated": 200
            }
        })

        totals = await storage.get_solution_totals("claude")
        assert totals["total_tokens"] == 1000
        assert totals["exact_tokens"] == 800
        assert totals["estimated_tokens"] == 200
        assert totals["deliberation_count"] == 1
```

### Implementation

**Approach**:
Add new table creation in `__init__()`, implement `increment_solution_totals()` with atomic UPDATE, and `get_solution_totals()` for querying.

**Code structure** (`decision_graph/storage.py`):
```python
# Add to __init__ after other table creations
def _create_solution_token_totals_table(self):
    """Create table for tracking lifetime token usage per solution."""
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS solution_token_totals (
            solution TEXT PRIMARY KEY,
            total_tokens INTEGER DEFAULT 0,
            exact_tokens INTEGER DEFAULT 0,
            estimated_tokens INTEGER DEFAULT 0,
            total_cost_usd REAL DEFAULT 0.0,
            cost_lower_bound REAL DEFAULT 0.0,
            cost_upper_bound REAL DEFAULT 0.0,
            deliberation_count INTEGER DEFAULT 0,
            last_updated TEXT
        )
    """)
    self.conn.commit()

async def increment_solution_totals(
    self,
    by_solution: Dict[str, Dict[str, int]]
) -> None:
    """
    Atomically increment token totals for solutions.

    Args:
        by_solution: {solution: {total: X, exact: Y, estimated: Z}}
    """
    for solution, counts in by_solution.items():
        # Atomic increment using UPDATE ... WHERE
        self.conn.execute("""
            INSERT INTO solution_token_totals (
                solution, total_tokens, exact_tokens, estimated_tokens,
                deliberation_count, last_updated
            ) VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(solution) DO UPDATE SET
                total_tokens = total_tokens + excluded.total_tokens,
                exact_tokens = exact_tokens + excluded.exact_tokens,
                estimated_tokens = estimated_tokens + excluded.estimated_tokens,
                deliberation_count = deliberation_count + 1,
                last_updated = excluded.last_updated
        """, (
            solution,
            counts["total"],
            counts.get("exact", 0),
            counts.get("estimated", 0),
            datetime.now().isoformat()
        ))
    self.conn.commit()

async def get_solution_totals(self, solution: str) -> Optional[Dict[str, Any]]:
    """Get lifetime token totals for a solution."""
    cursor = self.conn.cursor()
    cursor.execute(
        "SELECT * FROM solution_token_totals WHERE solution = ?",
        (solution,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    # Convert row to dict
    return {
        "solution": row[0],
        "total_tokens": row[1],
        "exact_tokens": row[2],
        "estimated_tokens": row[3],
        # ... etc
    }
```

**Key points**:
- Follow pattern from existing table creation in `decision_graph/storage.py:50`
- Use `INSERT ... ON CONFLICT DO UPDATE` for atomic increment (SQLite upsert)
- Call `self.conn.commit()` after writes
- Use `cursor.fetchone()` for single-row queries

**Integration points**:
- Call `_create_solution_token_totals_table()` in `__init__()`
- Import `from typing import Dict, Any, Optional`
- Will be called by: `deliberation/engine.py` after deliberation completes

### Verification

**Manual testing**:
```python
# In Python REPL
from decision_graph.storage import DecisionGraphStorage
import asyncio

storage = DecisionGraphStorage(":memory:")

asyncio.run(storage.increment_solution_totals({
    "claude": {"total": 1000, "exact": 800, "estimated": 200}
}))

totals = asyncio.run(storage.get_solution_totals("claude"))
print(totals)  # Should show 1000 total tokens, 1 deliberation
```

**Automated tests**:
```bash
pytest tests/unit/test_storage_token_totals.py -v
```

**Expected output**:
```
tests/unit/test_storage_token_totals.py::TestStorageTokenTotals::test_create_solution_token_totals_table PASSED
tests/unit/test_storage_token_totals.py::TestStorageTokenTotals::test_increment_solution_totals_atomic_operation PASSED
[7 tests passed]
```

### Commit

**Commit message**:
```
feat(storage): add solution token totals table

- Create solution_token_totals table for lifetime tracking
- Implement atomic increment with SQLite upsert
- Track exact vs estimated tokens separately
- Support cost confidence intervals calculation
```

**Files to commit**:
- `decision_graph/storage.py`
- `tests/unit/test_storage_token_totals.py`

---

*[Continue with Tasks 6-10 for checkpoint/resume infrastructure, Tasks 11-17 for autonomous control, and Tasks 18-24 for integration and testing]*

---

# PHASE 2: CHECKPOINT/RESUME INFRASTRUCTURE (Weeks 3-4)

## Task 6: Add Checkpoint Data Models and Schema

*[Similar detailed structure for each remaining task]*

---

# PHASE 3: AUTONOMOUS CONTROL & INTEGRATION (Weeks 5-6)

## Task 18: Implement Three-Tier Autonomous Control Stack

*[Similar detailed structure]*

---

# Testing Strategy

## Unit Tests
- **Location**: `tests/unit/`
- **Naming**: `test_<module>.py`
- **Run command**: `pytest tests/unit -v`
- **Coverage target**: 90%+

## Integration Tests
- **Location**: `tests/integration/`
- **What to test**: Token tracking end-to-end, checkpoint/resume cycles, model tier switching
- **Setup required**: Mock adapters, in-memory SQLite

## E2E Tests
- **Location**: `tests/e2e/`
- **Critical flows**: Full autonomous deliberation with token limit hit, resume from checkpoint

## Test Design Principles for This Feature

**Use these patterns**:
1. **TDD throughout**: Write tests BEFORE implementation (red, green, refactor)
2. **Mock adapters not external services**: Use `MockAdapter` from `tests/conftest.py`
3. **In-memory SQLite for storage tests**: `DecisionGraphStorage(":memory:")`
4. **AsyncMock for async methods**: `from unittest.mock import AsyncMock`

**Avoid these anti-patterns**:
1. **Don't mock Pydantic models**: Test validation by creating real instances
2. **Don't test implementation details**: Test behavior, not internal state
3. **Don't use time.sleep in tests**: Use `await asyncio.sleep(0)` for async yields

**Mocking guidelines**:
- Mock external services: CLI invocations, HTTP APIs (use VCR)
- Don't mock: Data models, pure functions, SQLite (use :memory:)
- Use project's mocking pattern: See `tests/unit/test_engine.py:20` for AsyncMock

---

# Commit Strategy

Break this work into 24 commits following this sequence:

1. **feat(models)**: Add token usage tracking models
2. **feat(adapters)**: Add token usage reporting to adapters
3. **feat(engine)**: Integrate token tracking into deliberation rounds
4. **feat(deliberation)**: Add behavioral model tier selection
5. **feat(storage)**: Add solution token totals table
6. **feat(models)**: Add checkpoint data models and schema
7. **feat(storage)**: Add checkpoint storage operations
8. **feat(engine)**: Add tiered threshold protocol for token limits
9. **feat(engine)**: Implement checkpoint generation at thresholds
10. **feat(server)**: Add resume_deliberation MCP tool
... *(continue for all 24 tasks)*

**Commit message format**:
Follow the pattern seen in recent commits:
```
<type>(<scope>): <description>

- Bullet point 1
- Bullet point 2
- Bullet point 3

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`

---

# Common Pitfalls & How to Avoid Them

1. **Forgetting to call SessionTokenTracker.record() in execute_round()**
   - Why it happens: Token tracking added as optional feature, easy to skip
   - How to avoid: Write test first that asserts tracker.by_solution has values
   - Reference: `tests/unit/test_engine_token_tracking.py:25`

2. **Not handling tiktoken ImportError gracefully**
   - Why it happens: tiktoken is optional dependency, may not be installed
   - How to avoid: Use try/except with fallback to 4 chars/token heuristic
   - Reference: `adapters/base.py:_get_token_usage()` fallback path

3. **Mutable default arguments in SessionTokenTracker**
   - Why it happens: `by_solution: Dict = {}` creates shared reference
   - How to avoid: Initialize in `__init__()` with `self.by_solution = {}`
   - Reference: Python gotcha, see `models/config.py` pattern

4. **SQLite connection not committed after writes**
   - Why it happens: Forgetting `self.conn.commit()` after INSERT/UPDATE
   - How to avoid: Always call commit() after write operations
   - Reference: `decision_graph/storage.py:save_decision()` pattern

5. **Async/await inconsistency**
   - Why it happens: Mixing sync and async code incorrectly
   - How to avoid: If method calls `await`, it must be `async def` and all callers must `await` it
   - Reference: All methods in `deliberation/engine.py` are async

---

# Resources & References

## Existing Code to Reference
- Similar token tracking: `decision_graph/cache.py` (hit rate tracking)
- Adapter patterns: `adapters/base.py`, `adapters/ollama.py`
- Test examples: `tests/unit/test_engine.py`, `tests/unit/test_adapters.py`
- Storage patterns: `decision_graph/storage.py`

## Documentation
- Pydantic validation: https://docs.pydantic.dev/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- SQLite Python: https://docs.python.org/3/library/sqlite3.html
- tiktoken: https://github.com/openai/tiktoken

## Validation Checklist
- [ ] All tests pass: `pytest tests/unit -v`
- [ ] Linter passes: `ruff check .`
- [ ] Formatted correctly: `black .`
- [ ] No print statements left (use logger.debug/info/warning/error)
- [ ] Error handling in place for all external calls
- [ ] Edge cases covered in tests
- [ ] Type hints on all new functions
- [ ] Docstrings for all public methods
- [ ] Commit messages follow pattern
- [ ] CLAUDE.md updated if architecture changes
