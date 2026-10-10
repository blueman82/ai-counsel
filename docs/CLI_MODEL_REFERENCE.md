- Verified: **2026-10-10** against official OpenAI documentation, Claude Platform documentation, and installed CLI model metadata.
- Availability: provider/account-dependent; exact IDs preferred; mutable aliases.
- Prices below are **standard API USD per million tokens**, not Claude subscriptions or Codex credit charges.

| CLI | Model ID | Input | Cached input | Output | Supported CLI effort |
|---|---|---:|---:|---:|---|
| Claude | `claude-fable-5-1` | $10 | $0.25 | $50 | low, medium, high, xhigh, max |
| Claude | `claude-opus-5-5` (registry default) | $4 | $0.20 | $20 | low, medium, high, xhigh, max |
| Claude | `claude-sonnet-5-5` | $2 | $0.10 | $10 | low, medium, high, xhigh, max |
| Claude | `claude-haiku-5-5`, prompt ≤100K | $0.10 | $0.01 | $0.50 | low, medium, high, xhigh, max |
| Claude | `claude-haiku-5-5`, prompt >100K | $0.50 | $0.05 | $2.50 | low, medium, high, xhigh, max |
| Codex | `gpt-6-astra` | $10 | $1 | $50 | low, medium, high, xhigh, max, ultra |
| Codex | `gpt-6.1-sol` (registry default) | $2 | $0.10 | $10 | low, medium, high, xhigh, max, ultra |
| Codex | `gpt-6-sol` | $2 | $0.20 | $10 | low, medium, high, xhigh, max, ultra |
| Codex | `gpt-6-luna` | $0.10 | $0.01 | $0.50 | low, medium, high, xhigh, max |

- Claude sources: [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview), [Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview), [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [pricing including Haiku tiers](https://platform.claude.com/docs/en/about-claude/pricing), [effort](https://platform.claude.com/docs/en/build-with-claude/effort).
- OpenAI sources: [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [Sol 6.1](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Sol 6](https://developers.openai.com/api/docs/models/gpt-6-sol), [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Codex models](https://learn.chatgpt.com/docs/models).
- Claude API defaults: Fable/Sonnet `high`; Opus/Haiku `medium`; CLI omission: client default.
- Codex default: config `medium`; per-participant override first; table efforts verified in CLI 0.162.1 metadata.
- API-only `none`: GPT-6 Sol/Luna; Codex-only `ultra`: Astra/Sol subagent orchestration; unavailable on Luna.
- GPT-6 API >272K input: full-request input/cache ×2, output ×1.5; cache writes ×1.25 base input; separate Batch/Flex/speed rates.
- Higher effort: higher token consumption; no fixed price multiplier or measured quality guarantee.

| Codex Standard credits per million tokens | Input | Cached input | Output |
|---|---:|---:|---:|
| GPT-6 Astra | 250 | 25 | 1,250 |
| GPT-6.1 Sol | 50 | 2.5 | 250 |
| GPT-6 Sol | 50 | 5 | 250 |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 |

- [Codex credit pricing](https://learn.chatgpt.com/docs/pricing): no cache-write fee; plan/contract-dependent allowances; purchased-credit Fast ×2 / Ultrafast ×6.
- API-key usage: API billing; Droid/OpenRouter/gateway availability: separate catalogs.
