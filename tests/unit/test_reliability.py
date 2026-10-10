"""Regression checks for registry isolation, free fallback, and rate limiting."""

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from tenacity import RetryCallState

from adapters.openrouter import OpenRouterAdapter
from deliberation.engine import DeliberationEngine
from models.config import ModelDefinition
from models.schema import Participant


def engine_for(entries, adapter=None, **fallback):
    config = SimpleNamespace(
        model_registry={"openrouter": [ModelDefinition(**e) for e in entries]},
        free_model_fallback=SimpleNamespace(
            enabled=True,
            max_retries_per_model=1,
            timeout_before_fallback=0.02,
            log_fallback_events=True,
            **fallback
        ),
    )
    return DeliberationEngine(
        {"openrouter": adapter or SimpleNamespace(invoke=AsyncMock())}, config=config
    )


def test_summarizer_uses_only_enabled_registry_models():
    config = SimpleNamespace(
        model_registry={
            "claude": [
                ModelDefinition(id="approved"),
                ModelDefinition(id="disabled", enabled=False),
            ]
        }
    )
    engine = DeliberationEngine({"claude": object(), "gemini": object()}, config=config)
    assert [(model, name) for _, model, name in engine.summarizer_chain] == [
        ("approved", "approved")
    ]
    config.model_registry = {}
    assert (
        DeliberationEngine({"claude": object()}, config=config).summarizer_chain == []
    )


@pytest.mark.asyncio
async def test_fallback_uses_only_enabled_registered_free_models():
    adapter = SimpleNamespace(invoke=AsyncMock(side_effect=[TimeoutError(), "answer"]))
    engine = engine_for(
        [
            {
                "id": "primary:free",
                "fallback_chain": [
                    "paid",
                    "missing:free",
                    "disabled:free",
                    "good:free",
                    "good:free",
                ],
            },
            {"id": "paid"},
            {"id": "disabled:free", "enabled": False},
            {"id": "good:free"},
        ],
        adapter,
    )
    actual, response = await engine._invoke_with_fallback(
        Participant(cli="openrouter", model="primary:free"), prompt="hi"
    )
    assert (actual, response) == ("good:free", "answer")
    assert [call.kwargs["model"] for call in adapter.invoke.call_args_list] == [
        "primary:free",
        "good:free",
    ]


@pytest.mark.asyncio
async def test_fallback_cancels_hung_primary_and_handles_malformed_response():
    async def invoke(**kwargs):
        if kwargs["model"] == "primary:free":
            await asyncio.sleep(100)
        if kwargs["model"] == "bad:free":
            return None
        return "answer"

    engine = engine_for(
        [
            {"id": "primary:free", "fallback_chain": ["bad:free", "good:free"]},
            {"id": "bad:free"},
            {"id": "good:free"},
        ],
        SimpleNamespace(invoke=invoke),
    )
    assert await engine._invoke_with_fallback(
        Participant(cli="openrouter", model="primary:free"), prompt="hi"
    ) == ("good:free", "answer")


@pytest.mark.asyncio
async def test_permanent_http_error_does_not_fallback():
    error = httpx.HTTPStatusError(
        "unauthorized",
        request=httpx.Request("POST", "https://test"),
        response=httpx.Response(401),
    )
    adapter = SimpleNamespace(invoke=AsyncMock(side_effect=error))
    engine = engine_for(
        [{"id": "primary:free", "fallback_chain": ["good:free"]}, {"id": "good:free"}],
        adapter,
    )
    with pytest.raises(httpx.HTTPStatusError):
        await engine._invoke_with_fallback(
            Participant(cli="openrouter", model="primary:free"), prompt="hi"
        )
    assert adapter.invoke.call_count == 1


@pytest.mark.parametrize(
    "header,expected", [("7", 7), ("9999", 120), ("-1", 1), ("bad", 1), ("NaN", 1)]
)
def test_retry_after_seconds_and_invalid_values(header, expected):
    adapter = OpenRouterAdapter(base_url="https://test")
    state = RetryCallState(None, None, (), {})
    error = httpx.HTTPStatusError(
        "limited",
        request=httpx.Request("POST", "https://test"),
        response=httpx.Response(429, headers={"Retry-After": header}),
    )
    state.set_exception((type(error), error, None))
    assert adapter._retry_wait(state) == expected


def test_retry_after_http_date():
    adapter = OpenRouterAdapter(base_url="https://test")
    state = RetryCallState(None, None, (), {})
    date = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=20))
    error = httpx.HTTPStatusError(
        "limited",
        request=httpx.Request("POST", "https://test"),
        response=httpx.Response(429, headers={"Retry-After": date}),
    )
    state.set_exception((type(error), error, None))
    assert 18 <= adapter._retry_wait(state) <= 20


@pytest.mark.asyncio
async def test_pacing_shared_across_free_models():
    from models.config import RateLimitingConfig

    adapter = OpenRouterAdapter(
        base_url="https://test",
        rate_limiting=RateLimitingConfig(free_model_delay_ms=20),
    )
    times = []

    async def start(model):
        await adapter._before_request({"model": model})
        times.append(asyncio.get_running_loop().time())

    await asyncio.gather(start("a:free"), start("b:free"), start("a:free"))
    assert all(b - a >= 0.018 for a, b in zip(times, times[1:]))


@pytest.mark.asyncio
async def test_exhausted_chain_preserves_other_participant_results():
    async def invoke(**kwargs):
        if kwargs["model"] != "healthy:free":
            raise TimeoutError("unavailable")
        return 'Analysis. VOTE: {"option": "yes", "confidence": 0.9, "rationale": "ok"}'

    engine = engine_for(
        [
            {"id": "primary:free", "fallback_chain": ["bad:free"]},
            {"id": "bad:free"},
            {"id": "healthy:free"},
        ],
        SimpleNamespace(invoke=invoke),
    )
    results = await engine.execute_round(
        1,
        "question",
        [
            Participant(cli="openrouter", model=model)
            for model in ("primary:free", "healthy:free")
        ],
        [],
    )
    assert "Free model chain exhausted (primary:free, bad:free)" in results[0].response
    assert "Analysis." in results[1].response


@pytest.mark.asyncio
async def test_round_transcript_text_reports_actual_fallback():
    adapter = SimpleNamespace(
        invoke=AsyncMock(
            side_effect=[
                TimeoutError(),
                'Answer. VOTE: {"option": "yes", "confidence": 0.9, "rationale": "ok"}',
            ]
        )
    )
    engine = engine_for(
        [{"id": "primary:free", "fallback_chain": ["good:free"]}, {"id": "good:free"}],
        adapter,
    )
    results = await engine.execute_round(
        1, "question", [Participant(cli="openrouter", model="primary:free")], []
    )
    assert "requested primary:free; responded with good:free" in results[0].response
    assert results[0].participant == "primary:free@openrouter"


@pytest.mark.asyncio
async def test_rate_limited_request_retries_and_permanent_error_fails_fast(monkeypatch):
    from models.config import RateLimitingConfig

    seen = []

    def serve(request):
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(
                429, headers={"Retry-After": "0"}, json={"error": "limited"}
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "done"}}]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original_client(transport=httpx.MockTransport(serve), **kw),
    )
    adapter = OpenRouterAdapter(
        base_url="https://test",
        max_retries=2,
        rate_limiting=RateLimitingConfig(free_model_delay_ms=0),
    )
    assert await adapter.invoke("hi", "primary:free") == "done"
    assert len(seen) == 2


@pytest.mark.asyncio
async def test_disabled_fallback_and_paid_primary_do_not_try_chain():
    adapter = SimpleNamespace(invoke=AsyncMock(side_effect=TimeoutError()))
    engine = engine_for(
        [{"id": "paid", "fallback_chain": ["good:free"]}, {"id": "good:free"}], adapter
    )
    with pytest.raises(TimeoutError):
        await engine._invoke_with_fallback(
            Participant(cli="openrouter", model="paid"), prompt="hi"
        )
    assert adapter.invoke.call_count == 1


def test_rate_settings_factory_wiring():
    from adapters import create_adapter
    from models.config import HTTPAdapterConfig

    adapter = create_adapter(
        "openrouter",
        HTTPAdapterConfig(
            base_url="https://test",
            rate_limiting={"free_model_delay_ms": 42, "respect_retry_after": False},
        ),
    )
    assert adapter.rate_limiting.free_model_delay_ms == 42
    assert not adapter.rate_limiting.respect_retry_after


@pytest.mark.asyncio
async def test_cancelled_pacing_waiter_does_not_block_next_request():
    from models.config import RateLimitingConfig

    adapter = OpenRouterAdapter(
        base_url="https://test",
        rate_limiting=RateLimitingConfig(free_model_delay_ms=20),
    )
    await adapter._before_request({"model": "a:free"})
    waiter = asyncio.create_task(adapter._before_request({"model": "b:free"}))
    await asyncio.sleep(0)
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    await asyncio.wait_for(adapter._before_request({"model": "c:free"}), 0.1)


@pytest.mark.asyncio
async def test_disabled_fallback_does_not_call_replacement():
    adapter = SimpleNamespace(invoke=AsyncMock(side_effect=TimeoutError()))
    engine = engine_for(
        [
            {"id": "primary:free", "fallback_chain": ["good:free"]},
            {"id": "good:free"},
        ],
        adapter,
    )
    engine.config.free_model_fallback.enabled = False
    with pytest.raises(TimeoutError):
        await engine._invoke_with_fallback(
            Participant(cli="openrouter", model="primary:free"), prompt="hi"
        )
    assert adapter.invoke.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("entries", [[], [{"id": "primary:free", "enabled": False}]])
async def test_disallowed_primary_is_not_invoked(entries):
    adapter = SimpleNamespace(invoke=AsyncMock())
    engine = engine_for(entries, adapter)
    with pytest.raises(ValueError, match="not enabled"):
        await engine._invoke_with_fallback(
            Participant(cli="openrouter", model="primary:free"), prompt="hi"
        )
    adapter.invoke.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed",
    [
        {"choices": [None]},
        {"choices": "bad"},
        {"choices": [{"message": []}]},
        [],
    ],
)
async def test_malformed_http_response_advances_to_healthy_fallback(
    monkeypatch, malformed
):
    import json
    from models.config import RateLimitingConfig

    models = []

    def serve(request):
        models.append(json.loads(request.content)["model"])
        body = (
            malformed
            if len(models) == 1
            else {"choices": [{"message": {"content": "healthy"}}]}
        )
        return httpx.Response(200, json=body)

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original_client(transport=httpx.MockTransport(serve), **kw),
    )
    adapter = OpenRouterAdapter(
        base_url="https://test", rate_limiting=RateLimitingConfig(free_model_delay_ms=0)
    )
    engine = engine_for(
        [{"id": "primary:free", "fallback_chain": ["good:free"]}, {"id": "good:free"}],
        adapter,
    )
    assert await engine._invoke_with_fallback(
        Participant(cli="openrouter", model="primary:free"), prompt="hi"
    ) == ("good:free", "healthy")
    assert models == ["primary:free", "good:free"]
