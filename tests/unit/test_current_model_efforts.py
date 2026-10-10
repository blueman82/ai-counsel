"""Current CLI model effort compatibility and argument forwarding."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model",
    [
        "claude-fable-5-1",
        "claude-opus-5-5",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "fable",
        "opus",
        "sonnet",
        "haiku",
    ],
)
async def test_current_claude_models_forward_effort(model):
    process = Mock(returncode=0, communicate=AsyncMock(return_value=(b"answer", b"")))
    with patch(
        "adapters.base.asyncio.create_subprocess_exec", return_value=process
    ) as spawn:
        adapter = ClaudeAdapter(args=["--model", "{model}", "{prompt}"])
        await adapter.invoke("Question", model, reasoning_effort="max")
    args = spawn.call_args.args
    assert args[args.index("--effort") + 1] == "max"
    assert args[args.index("--model") + 1] == model


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model,effort",
    [
        ("gpt-6-astra", "ultra"),
        ("gpt-6.1-sol", "ultra"),
        ("gpt-6-sol", "max"),
        ("gpt-6-luna", "max"),
    ],
)
async def test_current_codex_models_forward_effort(model, effort):
    process = Mock(returncode=0, communicate=AsyncMock(return_value=(b"answer", b"")))
    with patch(
        "adapters.base.asyncio.create_subprocess_exec", return_value=process
    ) as spawn:
        adapter = CodexAdapter(
            args=[
                "exec",
                "-c",
                'model_reasoning_effort="{reasoning_effort}"',
                "{prompt}",
            ]
        )
        await adapter.invoke("Question", model, reasoning_effort=effort)
    assert f'model_reasoning_effort="{effort}"' in spawn.call_args.args


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime,default", [("ultra", None), (None, "ultra")])
async def test_luna_rejects_ultra_before_launch(runtime, default):
    with patch("adapters.base.asyncio.create_subprocess_exec") as spawn:
        adapter = CodexAdapter(
            args=["exec", "{prompt}"], default_reasoning_effort=default
        )
        with pytest.raises(ValueError, match="ultra"):
            await adapter.invoke("Question", "gpt-6-luna", reasoning_effort=runtime)
    spawn.assert_not_called()


@pytest.mark.asyncio
async def test_mcp_discovery_exposes_current_efforts():
    from server import list_tools

    tool = next(t for t in await list_tools() if t.name == 'deliberate')
    variants = tool.inputSchema['properties']['participants']['items']['oneOf']
    by_cli = {v['properties']['cli']['const']: v['properties'] for v in variants}
    assert 'max' in by_cli['claude']['reasoning_effort']['enum']
    assert 'ultra' in by_cli['codex']['reasoning_effort']['enum']
    assert 'none' not in by_cli['codex']['reasoning_effort']['enum']
