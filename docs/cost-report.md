- Deliberation results expose `cost_summary`; transcripts include a Cost Summary table.
- HTTP responses preserve provider-reported input/output token counts and `usage.cost` in USD; Ollama token counts are also supported.
- Accounting includes participant invocations, vote retries, fallback attempts, and AI summaries, with separate ledgers for concurrent requests.
- Token totals are reported subtotals; `calls_with_token_usage / calls` identifies coverage.
- Missing token counts suppress the paid comparison; missing costs suppress actual cost and savings. CLI responses and failed invocations remain unknown, even for a model named `:free`.
- Actual cost requires explicit provider-reported costs for every recorded invocation. It is not invoice reconciliation: charges for transport retries or interrupted requests may be unavailable.
- Estimated paid cost applies the configured baseline rates to the same reported token volume; it does not predict equivalent answer quality or another model's token consumption.
- Estimated savings subtract provider-reported cost from estimated paid cost; negative savings mean the comparison baseline is cheaper.
- Configure the baseline under root `cost_comparison`; older configurations default to an illustrative $3 input / $15 output per million tokens, not a claim about current prices.

| Setting | Purpose |
|---------|---------|
| `baseline_name` | Label for the comparison model and price date |
| `input_per_million_usd` | Nonnegative finite USD per million input tokens |
| `output_per_million_usd` | Nonnegative finite USD per million output tokens |

- Cumulative tracking and billing reconciliation are outside this report.
