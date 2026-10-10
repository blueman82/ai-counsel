| Behavior | Value / limit |
|---|---|
| Output | Result `cost_summary`; transcript Cost Summary table |
| Provider usage | HTTP input/output token counts, `usage.cost` USD; Ollama token counts |
| Ledger scope | Participants, vote retries, fallbacks, AI summaries; isolated concurrent requests |
| Coverage | Reported token subtotals; `calls_with_token_usage / calls` |
| Missing tokens | Paid comparison suppressed |
| Missing costs | Actual cost and savings suppressed |
| CLI / failed calls | Unknown usage/cost; `:free` name insufficient |
| Actual cost | Explicit provider cost required for every recorded invocation |
| Accounting exclusions | Unreported transport retries/interrupted requests; no invoice reconciliation |
| Paid estimate | Baseline rates × same reported token volume |
| Estimate exclusions | Equivalent answer quality; another model's token consumption |
| Savings | Paid estimate − provider cost; negative = cheaper baseline |
| Configuration | Root `cost_comparison` |
| Legacy default | Illustrative $3 input / $15 output per million; no current-price claim |

| Setting | Purpose |
|---------|---------|
| `baseline_name` | Label for the comparison model and price date |
| `input_per_million_usd` | Nonnegative finite USD per million input tokens |
| `output_per_million_usd` | Nonnegative finite USD per million output tokens |

- Exclusions: cumulative tracking; billing reconciliation.
