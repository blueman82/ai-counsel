"""Opt-in OpenRouter free-model vote format probe; run with python -m scripts.probe_free_model_votes."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import httpx
import yaml
from pydantic import ValidationError

from adapters.openrouter import OpenRouterAdapter
from models.schema import Vote

CATALOG_URL = "https://openrouter.ai/api/v1/models"
QUESTION = (
    "A small offline application needs durable local records. Compare SQLite with "
    "a JSON file, choose one, and reconsider your earlier answer if present. "
    "End with VOTE: followed by one JSON object containing option (string), "
    "confidence (number from 0 to 1), rationale (string), and "
    "continue_debate (JSON boolean; false when satisfied)."
)


def assess_vote(text: str) -> dict:
    """Measure supplied fields without accepting coercion or defaulted flags."""
    result = dict(
        vote_marker="VOTE:" in text,
        json_valid=False,
        confidence_valid=False,
        continue_valid=False,
        valid=False,
    )
    # Match the same final VOTE object that the deliberation parser consumes.
    matches = re.findall(r"VOTE:\s*(\{.+?\})", text, re.DOTALL)
    if not matches:
        return result
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return result
    result["json_valid"] = True
    confidence = data.get("confidence")
    result["confidence_valid"] = (
        (type(confidence) is int or type(confidence) is float) and 0 <= confidence <= 1
    )
    result["continue_valid"] = type(data.get("continue_debate")) is bool
    try:
        Vote.model_validate(data, strict=True)
        result["valid"] = all(
            result[k]
            for k in (
                "vote_marker",
                "json_valid",
                "confidence_valid",
                "continue_valid",
            )
        )
    except ValidationError:
        pass
    return result


async def probe_models(
    adapter: OpenRouterAdapter, models: list[str], rounds: int, timeout: float
) -> list[dict]:
    """Probe sequential rounds, retaining observations and bounded prior context."""
    results = []
    for model in models:
        context = ""
        for round_number in range(1, rounds + 1):
            started = time.monotonic()
            row = {"model": model, "round": round_number}
            try:
                response = await asyncio.wait_for(
                    adapter.invoke(QUESTION, model, context=context),
                    timeout=timeout,
                )
                row.update(assess_vote(response))
                row["status"] = "passed" if row["valid"] else "failed"
                # Keep the final vote, bounded to prevent runaway probe costs.
                context = f"Previous round {round_number}:\n{response[-12000:]}"
            except Exception as exc:
                # Exception text can contain credentials or arbitrary provider output.
                row.update(status="error", error=type(exc).__name__, valid=False)
                if isinstance(exc, httpx.HTTPStatusError):
                    row["http_status"] = exc.response.status_code
            row["elapsed_seconds"] = round(time.monotonic() - started, 3)
            results.append(row)
    return results


async def main(argv: list[str] | None = None) -> int:
    """Write a dated JSON report; fail CI for observed errors or invalid votes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", action="append", help="Exact free model ID; repeatable"
    )
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path, default=Path("free-model-votes.json"))
    args = parser.parse_args(argv)
    if not 2 <= args.rounds <= 10 or not 0 < args.timeout <= 600:
        parser.error(
            "Use 2–10 rounds and a timeout greater than 0 and at most 600 seconds"
        )
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "catalog_url": CATALOG_URL,
        "rounds": args.rounds,
        "results": [],
    }
    key = os.getenv("OPENROUTER_API_KEY")
    exit_code = 0
    if not key:
        report["status"] = "skipped_missing_key"
    else:
        config_path = Path(__file__).resolve().parents[1] / "config.yaml"
        entries = yaml.safe_load(config_path.read_text())["model_registry"][
            "openrouter"
        ]
        models = args.model or [
            e["id"]
            for e in entries
            if e.get("enabled", True) and e["id"].endswith(":free")
        ]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(CATALOG_URL)
                response.raise_for_status()
                catalog = {m["id"]: m for m in response.json()["data"]}
            available = []
            for model in dict.fromkeys(models):
                entry = catalog.get(model)
                if entry is None:
                    report["results"].append(
                        {"model": model, "status": "unavailable", "valid": False}
                    )
                elif not model.endswith(":free") or any(
                    Decimal(str(entry["pricing"][k])) != 0
                    for k in ("prompt", "completion")
                ):
                    report["results"].append(
                        {"model": model, "status": "not_free", "valid": False}
                    )
                else:
                    available.append(model)
            adapter = OpenRouterAdapter(
                base_url="https://openrouter.ai/api/v1",
                api_key=key,
                timeout=args.timeout,
                max_retries=0,
            )
            adapter.default_max_tokens = 2048
            report["results"].extend(
                await probe_models(adapter, available, args.rounds, args.timeout)
            )
            report["status"] = (
                "passed"
                if report["results"]
                and all(r["status"] == "passed" for r in report["results"])
                else "failed"
            )
            exit_code = int(report["status"] != "passed")
        except Exception as exc:
            report.update(status="error", error=type(exc).__name__)
            exit_code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['status']}: {args.output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
