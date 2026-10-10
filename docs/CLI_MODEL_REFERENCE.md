- Verified: **2026-10-10** against official OpenAI documentation, Claude Platform documentation, and installed CLI model metadata.
- Registry availability does not grant provider/account access. Use exact IDs for reproducible configuration; aliases can change.
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
- Claude API default effort: Fable/Sonnet `high`; Opus/Haiku `medium`. Without an explicit effort, AI Counsel leaves Claude Code's client default intact.
- Codex config explicitly defaults to `medium`; per-participant `reasoning_effort` overrides it. Local Codex 0.162.1 metadata advertises the CLI efforts in the table. Client defaults can differ from API defaults.
- API `none` is supported by GPT-6 Sol/Luna, but is not an advertised effort in the installed Codex CLI. `ultra` is Codex subagent orchestration, not an API `reasoning.effort` value; Luna rejects it.
- GPT-6 API prompts above 272K input tokens use 2× input/cache rates and 1.5× output for the full request; cache writes cost 1.25× base input. Batch/Flex and speed tiers have separate rates.
- Higher effort spends more tokens; no fixed per-effort price or measured quality guarantee is implied. Compare on your own tasks.

| Codex Standard credits per million tokens | Input | Cached input | Output |
|---|---:|---:|---:|
| GPT-6 Astra | 250 | 25 | 1,250 |
| GPT-6.1 Sol | 50 | 2.5 | 250 |
| GPT-6 Sol | 50 | 5 | 250 |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 |

- [Codex credit pricing](https://learn.chatgpt.com/docs/pricing): no separate cache-write fee; API-key usage follows API pricing. Credit purchase prices and included subscription allowances depend on plan/contract. Fast/Ultrafast purchased-credit rates are 2×/6× Standard where available.
- This update does not claim Droid, OpenRouter, or third-party gateways support the same IDs as native Claude/Codex; their catalogs are separate.
