"""Offline checks for the opt-in live vote compliance probe."""

from unittest.mock import AsyncMock

import pytest

from scripts.probe_free_model_votes import assess_vote, probe_models


@pytest.mark.parametrize(
    "text,expected",
    [
        ("No vote", (False, False, False, False)),
        ("VOTE: {oops}", (True, False, False, False)),
        (
            'VOTE: {"option":"A","confidence":1.2,"rationale":"reason","continue_debate":false}',
            (True, True, False, True),
        ),
        (
            'VOTE: {"option":"A","confidence":0.8,"rationale":"reason"}',
            (True, True, True, False),
        ),
        (
            'VOTE: {"option":"A","confidence":0.8,"rationale":"reason","continue_debate":"false"}',
            (True, True, True, False),
        ),
        (
            'VOTE: {"option":"A","confidence":0.8,"rationale":"reason","continue_debate":false}',
            (True, True, True, True),
        ),
    ],
)
def test_reports_actual_fields_without_defaulting_continue(text, expected):
    result = assess_vote(text)
    assert (
        tuple(
            result[k]
            for k in ("vote_marker", "json_valid", "confidence_valid", "continue_valid")
        )
        == expected
    )
    assert result["valid"] == all(expected)


@pytest.mark.asyncio
async def test_probe_retains_multi_round_failures_and_prior_context():
    adapter = AsyncMock()
    adapter.invoke.side_effect = [
        'VOTE: {"option":"A","confidence":0.8,"rationale":"reason","continue_debate":true}',
        TimeoutError("secret-bearing provider response"),
        'VOTE: {"option":"B","confidence":0.9,"rationale":"revised","continue_debate":false}',
    ]
    results = await probe_models(adapter, ["test:free"], rounds=3, timeout=1)
    assert [r["status"] for r in results] == ["passed", "error", "passed"]
    assert results[1]["error"] == "TimeoutError"
    assert results[2]["round"] == 3
    assert "reason" in adapter.invoke.call_args_list[2].kwargs["context"]


@pytest.mark.asyncio
async def test_main_skips_without_key_and_writes_report(tmp_path, monkeypatch):
    from scripts.probe_free_model_votes import main

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    output = tmp_path / "report.json"
    assert await main(["--output", str(output)]) == 0
    import json

    report = json.loads(output.read_text())
    assert report["status"] == "skipped_missing_key"
    assert report["results"] == []


@pytest.mark.asyncio
async def test_probe_records_http_status_without_sensitive_error_text():
    import httpx

    response = httpx.Response(
        401, request=httpx.Request("POST", "https://example.test")
    )
    adapter = AsyncMock()
    adapter.invoke.side_effect = httpx.HTTPStatusError(
        "secret", request=response.request, response=response
    )
    rows = await probe_models(adapter, ["test:free"], rounds=2, timeout=1)
    assert rows[0]["http_status"] == 401
    assert "secret" not in str(rows)


@pytest.mark.asyncio
async def test_catalog_blocks_missing_or_paid_models(tmp_path, monkeypatch):
    import httpx
    from unittest.mock import patch
    from scripts.probe_free_model_votes import main

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    response = httpx.Response(
        200,
        json={
            "data": [
                {"id": "paid:free", "pricing": {"prompt": "0.01", "completion": "0"}},
            ]
        },
        request=httpx.Request("GET", "https://example.test"),
    )
    client = AsyncMock()
    client.get.return_value = response
    client.__aenter__.return_value = client
    with patch(
        "scripts.probe_free_model_votes.httpx.AsyncClient", return_value=client
    ), patch("scripts.probe_free_model_votes.OpenRouterAdapter") as adapter:
        assert (
            await main(
                [
                    "--model",
                    "paid:free",
                    "--model",
                    "missing:free",
                    "--output",
                    str(tmp_path / "report.json"),
                ]
            )
            == 1
        )
    adapter.return_value.invoke.assert_not_called()
    import json

    report = json.loads((tmp_path / "report.json").read_text())
    assert [r["status"] for r in report["results"]] == ["not_free", "unavailable"]
