- Setup: `adapters.openrouter` in `config.yaml`; `OPENROUTER_API_KEY` via environment or secret manager; no key logging.
- Catalog: [OpenRouter models API](https://openrouter.ai/api/v1/models); checked **2026-10-10**; availability/pricing evidence only.
- Selection: `list_models`; disabled compatibility entries retained; exact-ID and price recheck before activation.

| Model ID | Catalog observation, 2026-10-10 | Registry | Vote reliability |
|---|---|---|---|
| `google/gemma-4-26b-a4b-it:free` | Listed; input/output price both zero | Enabled | Unmeasured: HTTP 429 in all three attempts |
| `google/gemma-4-31b-it:free` | Listed; input/output price both zero | Enabled | Unmeasured: HTTP 429 in all three attempts |
| `nvidia/nemotron-3.5-lightning:free` | Listed; input/output price both zero | Enabled | Vote-format probe: 3/3 rounds passed; small sample |
| `xiaomi/mimo-v2-flash:free` | Not listed | Disabled | Untested |
| `deepseek/deepseek-r1:free` | Not listed | Disabled | Untested |
| `deepseek/deepseek-r1-0528:free` | Not listed; distinct ID from R1 | Disabled | Untested |
| `mistralai/devstral-2:free` | Not listed | Disabled | Untested |
| `meta-llama/llama-3.3-70b-instruct:free` | Not listed | Disabled | Untested |
| `kwaipilot/kat-coder-pro-v1:free` | Not listed | Disabled | Untested |
| `google/gemma-3-27b-it:free` | Not listed | Disabled | Untested |
| `mistralai/mistral-small-3.1-24b-instruct:free` | Not listed | Disabled | Untested |
| `meta-llama/llama-4-scout:free` | Not listed | Disabled | Untested |
| `qwen/qwen3-32b:free` | Not listed | Disabled | Untested |

- Corrected IDs: MiMo V2 Flash instead of VL 7B; Devstral 2 instead of Small; KAT namespace `kwaipilot` instead of `arcee-ai`; all unavailable.
- Other absent entries disabled: Claude 3.5 Sonnet; Gemini 2.0 Flash, 3 Pro Preview, 2.5 Flash Preview 05-20; four configured Grok IDs.
- Issues #26–#31: historical endpoints unavailable; Gemma 4 entries: explicitly identified current alternatives.

| Tier label | Meaning | Reliability claim |
|---|---|---|
| `free-experimental` | Zero-priced candidate or untested historical free entry | None; inspect `enabled` and dated `note` |
| `free-reasoning` | Reasoning-oriented historical candidate | None |
| `free-coding` | Coding-oriented historical candidate | None |
| `premium`, `balanced`, `speed`, `general`, `reasoning` | Selection hints on paid entries | Not a measured latency or availability rating |

- `free-reliable`: reserved for repeated, dated workload measurements; no inference from backing, size, or popularity.
- Failure modes: timeouts, rate limits, invalid votes; bounded requests; no indefinite-hang claim.
- Probe budget: 120 seconds/request; three rounds; 2,048 output tokens; zero retries; no model latency claim.
- Deliberation budgets: `adapters.openrouter.timeout`, `max_retries`, `defaults.timeout_per_round`; room for requests/retries.
- Cost control: free candidates → vote measurements → explicitly selected paid participants; no automatic paid substitution.

| Check | Command / behavior |
|---|---|
| Offline harness checks | `python -m pytest tests/unit/test_free_model_probe.py -q` |
| Opt-in live report | `python -m scripts.probe_free_model_votes --output artifacts/free-model-votes.json` |
| Select candidates | Repeat `--model exact/provider-id:free`; `--rounds 3`; `--timeout 120` |
| Missing key | Writes `skipped_missing_key`; makes no requests; exit 0 |
| Missing/nonzero-price catalog ID | Records `unavailable`/`not_free`; sends no completion; exit 1 |
| Observations | Per model/round: marker, JSON validity, numeric confidence range, explicit boolean `continue_debate`, strict vote schema validity, status, elapsed seconds |
| Request failure | Records exception type without provider error text or credentials; continues remaining rounds; exit 1 |
| Weekly CI | Monday schedule/manual dispatch; `OPENROUTER_API_KEY` repository secret; JSON artifact retained even on failure |

- Probe scope: final `VOTE:` pattern; `Vote` schema; strict field types; explicit continue flag; prior-response rounds.
- Exclusions: factual correctness, multi-participant consensus, production uptime; missing secret ≠ pass.
- Cost reference: [CLI API prices and separate subscription/credit costs](../CLI_MODEL_REFERENCE.md).

- [Live report, 2026-10-10](free-model-votes-2026-10-10.json): refreshed key; 2 free models × 3 rounds; six HTTP 429s; rate-limit rejection; zero votes; zero paid requests.
- [Nemotron report, 2026-10-10](nemotron-free-votes-2026-10-10.json): 3/3 vote-format rounds passed; 39.949s / 8.924s / 31.120s; 90-second budget; no retries; zero-priced endpoint; no broad reliability claim.

- Free-model reliability settings (all optional):
  - `adapters.openrouter.rate_limiting.enabled`: `true`; spaces free request starts across participants and retries sharing the adapter.
  - `adapters.openrouter.rate_limiting.free_model_delay_ms`: `1000`; paid requests bypass pacing.
  - `adapters.openrouter.rate_limiting.respect_retry_after`: `true`; accepts HTTP seconds or dates, falling back to exponential backoff for malformed values.
  - `adapters.openrouter.rate_limiting.max_wait_seconds`: `120`; caps each retry wait (not the whole invocation).
  - `free_model_fallback.enabled`: `false`; opt in at the configuration root.
  - `free_model_fallback.timeout_before_fallback`: `30`; wall-clock seconds per model invocation, including adapter retries and pacing.
  - `free_model_fallback.max_retries_per_model`: `1`; maximum invocations per candidate, each bounded by the timeout above; adapter `max_retries` still limits HTTP attempts within that budget.
  - `free_model_fallback.log_fallback_events`: `true`; logs failed attempts and the actual replacement model.
- Add `fallback_chain: ["other-provider/model:free"]` to a primary entry in `model_registry.openrouter`; also register and enable each fallback separately.
- Fallback eligibility: enabled `:free` / `openrouter/free`; no paid, disabled, absent, duplicate candidates; flat chain; ten-fallback limit.
- Fallback triggers: timeout, transient HTTP error, malformed response; permanent/authentication error: immediate stop.
- Identity: requested participant retained; actual replacement in transcript; exhausted chain: participant error; completed peers retained.
- Summarizers: enabled registry entries only; empty registry respected; legacy defaults only without registry.
