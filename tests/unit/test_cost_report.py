"""Cost reports must preserve unknowns and isolate concurrent requests."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from adapters.openrouter import OpenRouterAdapter
from deliberation.costs import build_cost_summary, invocation_usage, invoke_with_usage
from models.config import CostComparisonConfig
from models.schema import InvocationResult, InvocationUsage


@pytest.mark.asyncio
async def test_provider_usage_is_per_response():
    adapter = OpenRouterAdapter(base_url="https://example.com", api_key="test")

    async def response(**kwargs):
        model = kwargs["body"]["model"]
        await asyncio.sleep(0)
        return {
            "choices": [{"message": {"content": model}}],
            "usage": {
                "prompt_tokens": 100 if model == "a:free" else 200,
                "completion_tokens": 20,
                "cost": 0,
            },
        }

    adapter._execute_request_with_retry = response
    a, b = await asyncio.gather(
        adapter.invoke("test", "a:free"), adapter.invoke("test", "b:free")
    )
    assert isinstance(a, str) and a == "a:free"
    assert a.usage.input_tokens == 100
    assert b.usage.input_tokens == 200
    assert a.usage.cost_usd == 0


@pytest.mark.asyncio
async def test_ledgers_isolate_requests_and_include_every_call():
    async def run(model):
        records = []
        token = invocation_usage.set(records)
        try:
            adapter = SimpleNamespace(
                invoke=AsyncMock(
                    return_value=InvocationResult(
                        "response",
                        InvocationUsage(
                            model=model, input_tokens=100, output_tokens=20, cost_usd=0
                        ),
                    )
                )
            )
            await asyncio.gather(
                *(invoke_with_usage(adapter, model=model) for _ in range(3))
            )
            adapter.invoke.side_effect = RuntimeError("failed retry")
            with pytest.raises(RuntimeError):
                await invoke_with_usage(adapter, model=model)
            return build_cost_summary(records, CostComparisonConfig())
        finally:
            invocation_usage.reset(token)

    a, b = await asyncio.gather(run("a:free"), run("b:free"))
    assert a.models_used == ["a:free"] and b.models_used == ["b:free"]
    assert a.input_tokens == 300 and a.output_tokens == 60
    assert a.calls == 4 and a.calls_with_token_usage == 3
    assert a.actual_cost_usd is None and a.estimated_savings_usd is None
    assert a.estimated_paid_cost_usd is None
    assert invocation_usage.get() is None


def test_complete_report_uses_configurable_baseline():
    report = build_cost_summary(
        [
            InvocationUsage(
                model="free", input_tokens=1000, output_tokens=2000, cost_usd=0
            ),
            InvocationUsage(
                model="paid", input_tokens=1000, output_tokens=1000, cost_usd=0.01
            ),
        ],
        CostComparisonConfig(
            baseline_name="Example", input_per_million_usd=2, output_per_million_usd=10
        ),
    )
    assert report.estimated_paid_cost_usd == pytest.approx(0.034)
    assert report.actual_cost_usd == pytest.approx(0.01)
    assert report.estimated_savings_usd == pytest.approx(0.024)
    assert report.baseline_name == "Example"


@pytest.mark.parametrize(
    "usage",
    [{}, {"prompt_tokens": -1, "completion_tokens": "bad", "cost": float("nan")}],
)
@pytest.mark.asyncio
async def test_missing_or_invalid_usage_is_unknown(usage):
    adapter = OpenRouterAdapter(base_url="https://example.com", api_key="test")
    adapter._execute_request_with_retry = AsyncMock(
        return_value={"choices": [{"message": {"content": "ok"}}], "usage": usage}
    )
    response = await adapter.invoke("test", "a:free")
    assert response.usage.input_tokens is None
    assert response.usage.output_tokens is None
    assert response.usage.cost_usd is None


@pytest.mark.asyncio
async def test_engine_counts_vote_retries_and_summary_and_renders_unknown(tmp_path):
    from deliberation.engine import DeliberationEngine
    from deliberation.transcript import TranscriptManager
    from models.schema import DeliberateRequest, Participant

    adapter = SimpleNamespace(
        invoke=AsyncMock(
            side_effect=[
                InvocationResult(
                    "analysis without vote",
                    InvocationUsage(
                        model="free", input_tokens=100, output_tokens=10, cost_usd=0
                    ),
                ),
                InvocationResult(
                    'VOTE: {"option": "A", "confidence": 0.9, "rationale": "ok", "continue_debate": false}',
                    InvocationUsage(
                        model="free", input_tokens=20, output_tokens=5, cost_usd=0
                    ),
                ),
                "plain CLI response",
                'VOTE: {"option": "A", "confidence": 0.9, "rationale": "ok", "continue_debate": false}',
            ]
        )
    )
    engine = DeliberationEngine(
        {"openrouter": adapter}, transcript_manager=TranscriptManager(str(tmp_path))
    )
    from models.config import VoteRetryConfig

    engine._get_vote_retry_config = lambda: VoteRetryConfig(min_response_length=0)
    summary_adapter = SimpleNamespace(
        invoke=AsyncMock(
            return_value=InvocationResult(
                "CONSENSUS: A",
                InvocationUsage(
                    model="summary", input_tokens=30, output_tokens=10, cost_usd=0
                ),
            )
        )
    )
    engine.summarizer_chain = [(summary_adapter, "summary", "summary")]

    request = DeliberateRequest(
        question="Should we choose A?",
        working_directory=str(tmp_path),
        rounds=1,
        participants=[
            Participant(cli="openrouter", model="free"),
            Participant(cli="openrouter", model="other"),
        ],
    )
    result = await engine.execute(request)
    assert result.cost_summary.calls == 5
    assert result.cost_summary.input_tokens == 150
    assert result.cost_summary.actual_cost_usd is None
    markdown = engine.transcript_manager.generate_markdown(result)
    assert "## Cost Summary" in markdown
    assert "Unknown" in markdown
    assert "Reported Input Tokens" in markdown
    assert result.model_dump()["cost_summary"]["input_tokens"] == 150
