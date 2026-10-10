- OpenRouter uses the HTTP adapter in `config.yaml`; set `OPENROUTER_API_KEY` through your environment or secret manager. Do not print or commit the key.
- Catalog source: [OpenRouter models API](https://openrouter.ai/api/v1/models), checked **2026-10-10**. A catalog listing and zero token price establish neither uptime nor valid voting output.
- Use `list_models` for enabled choices. Disabled compatibility entries remain in the configuration; enable them only after verifying their exact ID and current price.

| Model ID | Catalog observation, 2026-10-10 | Registry | Vote reliability |
|---|---|---|---|
| `google/gemma-4-26b-a4b-it:free` | Listed; input/output price both zero | Enabled | Unmeasured: HTTP 401 in all three attempts |
| `google/gemma-4-31b-it:free` | Listed; input/output price both zero | Enabled | Unmeasured: HTTP 401 in all three attempts |
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

- Corrected mismatches: MiMo VL 7B is not MiMo V2 Flash; Devstral Small is not Devstral 2; the requested KAT ID uses `kwaipilot`, not `arcee-ai`. Corrected requested IDs remain disabled because the catalog does not list them.
- Also disabled absent paid/preview entries: Claude 3.5 Sonnet, Gemini 2.0 Flash, Gemini 3 Pro Preview, Gemini 2.5 Flash Preview 05-20, and the four configured Grok IDs. Existing listed paid models remain available.
- The historical requests in issues #26–#31 cannot establish current availability. The two Gemma 4 choices are explicitly identified alternatives, not renamed replacements for the missing models.

| Tier label | Meaning | Reliability claim |
|---|---|---|
| `free-experimental` | Zero-priced candidate or untested historical free entry | None; inspect `enabled` and dated `note` |
| `free-reasoning` | Reasoning-oriented historical candidate | None |
| `free-coding` | Coding-oriented historical candidate | None |
| `premium`, `balanced`, `speed`, `general`, `reasoning` | Selection hints on paid entries | Not a measured latency or availability rating |

- Avoid `free-reliable` until repeated measurements support a dated, workload-specific claim; company backing, model size, and popularity do not establish service reliability.
- Free requests can time out, be rate-limited, or return invalid votes. AI Counsel bounds requests with configured timeouts; no indefinite-hang claim is made.
- Starting probe budget: 120 seconds per request, three rounds, 2,048 maximum output tokens, no retries. Treat this as a measurement setting, not a measured model latency recommendation.
- For normal deliberations, inspect `adapters.openrouter.timeout`, `max_retries`, and `defaults.timeout_per_round`. Multiple requests/retries need a sufficient round budget.
- Cost-conscious pattern: start with currently listed free candidates, inspect actual vote validity, then explicitly select paid participants when quality needs justify them. A free failure alone is not permission to incur paid-model charges.

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

- The probe uses the same final `VOTE:` object pattern and `Vote` schema as deliberation, plus stricter checks against coerced values and an omitted continue flag. It measures format compliance across prior-response rounds, not factual correctness, full multi-participant consensus, or production uptime.
- Reports contain observed fields only; this checked-in table stays **Untested** until a dated real report is reviewed. Workflow failures flag regressions; missing-secret runs are skips, not reliability passes.
- API prices and Claude/Codex subscription costs are separate; see the [CLI model and cost reference](../CLI_MODEL_REFERENCE.md).

- [Sanitized live report, 2026-10-10](free-model-votes-2026-10-10.json): both current free models returned HTTP 401 in three rounds each. Credential acceptance blocked completion; no vote quality, latency, or reliability pass is claimed. No paid requests were sent.

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
- Fallbacks accept only enabled registry entries ending in `:free` or exactly `openrouter/free`; paid, disabled, missing, and duplicate candidates are skipped. Chains are flat, limited to ten configured fallbacks, and never expanded recursively.
- Timeouts, transient HTTP errors, and malformed responses advance the chain; permanent HTTP errors such as authentication failures stop immediately.
- Responses preserve the requested participant identity and include the actual fallback model in their transcript text. Exhausted chains become participant errors while completed peers remain available.
- Summarizers use only enabled entries when a model registry is supplied, including an empty registry; legacy defaults apply only without a registry.
