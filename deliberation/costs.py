"""Request-scoped accounting for reported provider usage."""

from contextvars import ContextVar

from models.config import CostComparisonConfig
from models.schema import CostSummary, InvocationResult, InvocationUsage

# Child tasks share their request's list; unrelated requests get separate lists.
invocation_usage: ContextVar[list[InvocationUsage] | None] = ContextVar(
    "invocation_usage", default=None
)


async def invoke_with_usage(adapter, **kwargs) -> str:
    """Record each invocation, conservatively retaining unknown failed costs."""
    usage = InvocationUsage(model=kwargs["model"])
    try:
        response = await adapter.invoke(**kwargs)
        if isinstance(response, InvocationResult):
            usage = response.usage
        return response
    finally:
        records = invocation_usage.get()
        if records is not None:
            records.append(usage)


def build_cost_summary(
    records: list[InvocationUsage], pricing: CostComparisonConfig
) -> CostSummary:
    """Compare identical reported token volumes against configured USD rates."""
    input_tokens = sum(r.input_tokens or 0 for r in records)
    output_tokens = sum(r.output_tokens or 0 for r in records)
    complete = sum(
        r.input_tokens is not None and r.output_tokens is not None for r in records
    )
    actual = (
        sum(r.cost_usd for r in records)
        if records and all(r.cost_usd is not None for r in records)
        else None
    )
    estimated = (
        (
            input_tokens * pricing.input_per_million_usd
            + output_tokens * pricing.output_per_million_usd
        )
        / 1_000_000
        if records and complete == len(records)
        else None
    )
    return CostSummary(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        models_used=sorted({r.model for r in records}),
        calls=len(records),
        calls_with_token_usage=complete,
        actual_cost_usd=actual,
        estimated_paid_cost_usd=estimated,
        estimated_savings_usd=(
            estimated - actual if estimated is not None and actual is not None else None
        ),
        baseline_name=pricing.baseline_name,
        input_per_million_usd=pricing.input_per_million_usd,
        output_per_million_usd=pricing.output_per_million_usd,
    )
