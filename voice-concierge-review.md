# Voice AI Concierge Platform — Design Review

**Reviewed:** 2026-03-14
**Document:** `2026-03-14-voice-concierge-MASTER.md`
**Verdict:** Build it, with corrections below

---

## Dangerous / Must Fix

### 1. Outbound AI calling is legally radioactive

The FCC's 2024 ruling explicitly brought AI-generated voices under TCPA. The 7-step gate is good, but the legal landscape is shifting fast — several states are passing stricter AI calling laws in 2025-2026. One plaintiff's attorney finding a consent gap = $500-$1,500 per call in statutory damages.

**Recommendation:** Launch with inbound-only and widget-only in Phase 1-2. Add outbound as a Phase 3/4 feature after consulting a TCPA attorney. The compliance gate is necessary but not sufficient — you need legal sign-off on the exact consent language, the verbal consent capture method, and state-by-state analysis.

### 2. Verbal consent captured by an AI is weak evidence

The design says the agent asks permission verbally, then sends an SMS consent link. But between those two steps, what's the legal standing? If the caller says "sure" to the AI and then never clicks the SMS link, do you have consent? A court would likely say no.

**Recommendation:** Never consider verbal-to-AI as valid written consent. Only the SMS form / web form / in-app checkbox counts. Verbal = informational consent only (appointment reminders at most).

### 3. Tool call endpoints have no authentication

Code comment says "No auth middleware — verified by Retell's call context." But `/api/tools/search-knowledge` and `/api/tools/check-availability` are public HTTP endpoints. Anyone who discovers the URL can query the knowledge base or probe tenant API endpoints.

**Recommendation:** At minimum, verify requests come from Retell by checking the `x-retell-signature` header (same as webhooks), or allowlist Retell's IP ranges.

### 4. RLS + connection pooling = data leak risk

Using `SET app.current_tenant_id` on pooled connections. If a request errors out before the connection is properly released, the next request on that connection could inherit the wrong tenant ID. This is the #1 multi-tenant security bug.

**Recommendation:** Always `RESET app.current_tenant_id` at the START of every request (not just set it). Use `try/finally` to guarantee release. Consider using `SET LOCAL` within a transaction instead — it auto-resets when the transaction ends.

---

## Significant Gaps

### 5. Single-vendor lock on Retell

The entire product — voice, transcription, widget, phone numbers, call routing — runs through Retell. If Retell raises prices 3x, has an extended outage, or sunsets a feature, there is no fallback.

**Recommendation:** Add an abstraction layer (`VoiceProvider` interface) from the start. No need to build a second integration now, but designing for it costs almost nothing and saves you later.

### 6. Margin math is thin

- Starter at $99/mo with 500 included minutes: ~$42.50 Retell/ElevenLabs COGS + ~$10 infra overhead = ~47% gross margin
- Pro at $299/mo with 2,000 minutes: ~$170 COGS = ~43% gross margin
- SaaS businesses typically need 70-80% gross margins to be viable

**Recommendation:** Either raise prices (luxury real estate can afford it — $199/$499 is more appropriate), reduce included minutes (250/1000), or increase overage rate ($0.18-0.20/min). Run the unit economics before building.

### 7. No human call transfer implementation

The design mentions "warm handoff" in the conversation flow but there's no actual implementation — no Retell `transfer_call` API usage, no forwarding number configuration, no availability checking. When a caller asks for a human, what actually happens?

**Recommendation:** Add a `transfer_call` tool that the agent can invoke, with a configurable forwarding number per property. This is table stakes for v1.

### 8. OpenAI dependency is undocumented

The knowledge service imports `openai` for embeddings (`text-embedding-3-small`), but OpenAI isn't in the API key strategy table, the environment variables section, or the cost estimate. This is a hidden dependency and cost.

**Recommendation:** Either document it properly (add to cost estimate — ~$5-15/mo for embeddings at your scale) or use a local embedding model to keep costs zero and latency low.

### 9. No fallback when embedding service is down

If OpenAI's embedding API is unavailable, every `search_knowledge` tool call fails. Every call gets "I can't look that up right now." This could last hours.

**Recommendation:** Add a keyword/full-text search fallback using PostgreSQL's built-in `tsvector`. Slower and lower quality, but works without external APIs.

---

## Worth Thinking About

### 10. 10 weeks is optimistic for one developer

Phase 1 alone is 15 tasks including a full Express backend, 12+ database tables with RLS, Retell integration, R2 storage, a Next.js dashboard with auth and 4+ pages, and a live building — in 4 weeks. Realistic estimate with testing, debugging, and deployment: 6-8 weeks for Phase 1 alone. Total project: 16-20 weeks.

**Recommendation:** Don't rush. Ship Phase 1 and use it for your own buildings for 2-4 weeks before Phase 2. Real usage reveals issues that no amount of planning catches.

### 11. The interactive demo is expensive

Creating temporary Retell agents for every `/demo` visitor who enters a URL means scraping + Claude API call + Retell agent creation + potential test call minutes. At scale, this could cost $1-5 per demo visitor with no conversion.

**Recommendation:** Use a single demo agent with a pre-loaded sample property. Only create custom agents for visitors who've entered their email (lead capture gate).

### 12. Widget security is theater

`document.referrer` is trivially spoofable and isn't even sent in all browsers.

**Recommendation:** Use Retell's built-in domain verification if available. Otherwise, accept that the widget will be embeddable anywhere and focus on rate limiting instead.

### 13. No graceful updates during live calls

What happens when you update a system prompt or re-embed a knowledge base while calls are active? KB re-embedding deletes all chunks then re-inserts — meaning a mid-call `search_knowledge` could return zero results during the swap window.

**Recommendation:** Don't delete old chunks until new ones are committed. Use the `doc_id` to swap atomically.

### 14. No encryption key rotation strategy

Single `ENCRYPTION_KEY` for all tenant API keys forever. If compromised, all keys are exposed with no way to rotate without re-encrypting everything.

**Recommendation:** Add a key version prefix to encrypted values (`v1:iv:ciphertext`). When you rotate, new encryptions use v2, old values decrypt with v1 until re-encrypted.

---

## What's Done Well

- **Multi-tenant with RLS from day 1** — correct decision, hard to retrofit
- **TCPA compliance depth** — 7-step gate, consent audit trail, DNC checks; more thorough than most startups
- **Learning loop as competitive moat** — this is the actual product, not the voice agent
- **Staleness detection** — time-based + contradiction + site sync is smart
- **Verified tech specs** — Retell docs, pgvector benchmarks, Stripe metering all checked against real documentation
- **Graceful degradation** — fallback prompts when tools fail, agent instructions for handling errors mid-call
- **Cost estimates with real numbers** — most plans skip this

---

## Action Items Before Implementation

1. Fix the 4 dangerous items before writing code
2. Launch inbound-only first (skip outbound until you have legal counsel)
3. Price higher ($199/$499) — luxury real estate customers won't blink
4. Plan for 16-20 weeks, not 10
5. Use your own 4 buildings as the beta for 4+ weeks before selling to external customers

The core idea — an AI concierge that gets smarter from every call, with deep per-building knowledge — is genuinely compelling for luxury real estate. The learning loop is the moat. The rest is plumbing.
