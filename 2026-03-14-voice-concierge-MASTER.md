# Voice AI Concierge Platform — Master Document

> Complete design + implementation plan for a multi-tenant luxury real estate voice AI concierge platform with SaaS spin-out.

**Created:** 2026-03-14
**Status:** Design complete, implementation plan ready
**Total scope:** 38 tasks across 4 phases, ~10 weeks

---

## Table of Contents

### Part 1: Design Document
1. System Architecture
2. Repo Structure
3. Database Schema
4. Knowledge Engine
5. Agent Persona & Conversation Flow
6. Learning Loop
7. Outbound & Follow-Up System
8. Multi-Tenant Architecture
9. Security & Data Protection
10. Supporting Services & Infrastructure
11. Pre-Flight Checklist
12. API Key Strategy
13. Verified Technical Specifications
14. Phasing Overview

### Part 2: Implementation Plan
- Phase 1: Platform Core (Tasks 1-15) — Backend, DB, Retell, Dashboard, First Building
- Phase 2: All Projects + Outbound + Learning (Tasks 16-25) — Scale, Compliance, Intelligence
- Phase 3: Spin-Out Completion (Tasks 26-33) — Billing, Onboarding, Marketing, White-Label
- Phase 4: Launch (Tasks 34-38) — QA, Beta, Iterate, Go Live

### Quick Reference
| Phase | Tasks | Focus | Timeline |
|-------|-------|-------|----------|
| Phase 1 | 1-15 | Platform core | Weeks 1-4 |
| Phase 2 | 16-25 | All projects + outbound + learning | Weeks 5-6 |
| Phase 3 | 26-33 | SaaS spin-out | Weeks 7-9 |
| Phase 4 | 34-38 | Beta + launch | Week 10 |

### Monthly Cost Estimate (at scale)
| Service | Cost |
|---------|------|
| Railway (backend + Postgres + Redis) | ~$35-40/mo |
| Retell AI (per-minute, depends on volume) | ~$700/mo at 10K min |
| ElevenLabs TTS (via Retell, +$0.015/min) | Included in Retell |
| Cloudflare R2 (recordings) | ~$5-15/mo |
| Clerk (auth) | ~$25/mo |
| Sentry (errors) | Free tier |
| Resend (email) | Free tier — $20/mo |
| Twilio (SMS) | ~$10-20/mo |
| Stripe (billing) | 2.9% + $0.30 per transaction |
| Vercel (dashboard + marketing) | Free tier — $20/mo |
| **Total baseline** | **~$800-850/mo** |

---
---

# PART 1: DESIGN DOCUMENT

---
# Voice AI Concierge Platform — Design Document

**Goal:** Build a multi-tenant voice AI concierge platform for luxury real estate — inbound phone, website widget, outbound follow-up — with deep per-building knowledge, a self-learning loop, and spin-out readiness as a standalone SaaS product.

**Architecture:** Dedicated Node.js backend on Railway + Next.js admin dashboard on Vercel + own PostgreSQL with pgvector. Retell AI for voice orchestration with ElevenLabs TTS. Two repos: platform (the product) and adapters (glue code for our 4 real estate projects).

**Tech Stack:** Node.js, Express, BullMQ, Redis, PostgreSQL + pgvector, Retell AI SDK, ElevenLabs TTS, Stripe Billing, Next.js 16, Vercel, Railway

---

## Decision Boundaries

### Executor can decide:
- Internal variable/function naming
- Import organization
- Test structure and assertion style
- Git commit message wording
- Database index strategy (within pgvector best practices)

### User must decide (ask if unclear):
- Product name and domain (placeholder: "Voice Concierge")
- Tier pricing amounts ($99/$299/custom)
- Voice selection per building
- Agent persona names per building
- Marketing site copy
- Compliance disclosure exact wording

### Hardcoded (do not change):
- Tenant isolation via tenant_id on every table + Postgres RLS
- pgvector in same Postgres instance (not separate vector DB)
- Retell AI as voice platform with ElevenLabs TTS provider
- Railway for backend, Vercel for dashboard
- 7-step pre-call compliance gate for all outbound calls
- AI disclosure at start of every call (FCC requirement)
- Recording disclosure at start of every call (two-party state safe)
- Consent records with full audit trail
- 10-second max response time for tool call webhooks

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    VOICE CONCIERGE PLATFORM              │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Backend (Node.js on Railway — always-on)          │  │
│  │                                                     │  │
│  │  ┌───────────┐  ┌───────────┐  ┌──────────────┐   │  │
│  │  │ Webhook   │  │ Worker    │  │ Outbound     │   │  │
│  │  │ Server    │  │ Queue     │  │ Scheduler    │   │  │
│  │  │ (Express) │  │ (BullMQ)  │  │ (cron jobs)  │   │  │
│  │  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘   │  │
│  │        │               │               │           │  │
│  │  ┌─────┴───────────────┴───────────────┴───────┐   │  │
│  │  │  PostgreSQL + pgvector (Railway managed)    │   │  │
│  │  │                                             │   │  │
│  │  │  Core: tenants, properties, agents, calls   │   │  │
│  │  │  Knowledge: knowledge_docs, chunks (vector) │   │  │
│  │  │  Learning: learning_gaps, call_analyses      │   │  │
│  │  │  Compliance: consent_records, dnc_list       │   │  │
│  │  │  Billing: usage_meters                       │   │  │
│  │  │                                             │   │  │
│  │  │  RLS policies on ALL tenant-scoped tables   │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                                                     │  │
│  │  Redis (Railway managed) — BullMQ job persistence   │  │
│  │  S3/R2 — call recordings (encrypted at rest)        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Admin Dashboard (Next.js on Vercel)               │  │
│  │                                                     │  │
│  │  - Auth (magic link or OAuth)                      │  │
│  │  - Self-serve onboarding wizard                    │  │
│  │  - Agent management (create, test, deploy)         │  │
│  │  - Knowledge base editor (per building)            │  │
│  │  - Call log viewer + transcript playback           │  │
│  │  - Learning queue (review gaps, approve fixes)     │  │
│  │  - Stale knowledge review                          │  │
│  │  - Analytics (calls, conversions, quality)         │  │
│  │  - Billing / account management                    │  │
│  │  - Customer docs / help                            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  External Services                                 │  │
│  │                                                     │  │
│  │  Retell AI ───── agent hosting, call routing,      │  │
│  │                  widget embed, transcription        │  │
│  │  ElevenLabs ──── TTS voice provider (via Retell)   │  │
│  │  Claude API ──── transcript analysis, KB gen,      │  │
│  │                  gap detection, onboarding scrape   │  │
│  │  Stripe ──────── subscriptions + metered billing   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
          │
          │  API calls (webhooks out, REST in)
          │
┌─────────┼─────────────────────────────────────────────────┐
│  REAL ESTATE PROJECTS (existing repos, minimal changes)   │
│                                                           │
│  Each project adds 4 API endpoints:                       │
│                                                           │
│  POST /api/voice/lead ───── create lead from call         │
│  POST /api/voice/tour ───── book tour from call           │
│  GET  /api/voice/listings — live availability lookup      │
│  POST /api/voice/conversation — log call to portal        │
│                                                           │
│  + Widget embed script tag on public pages                │
│                                                           │
│  ┌──────────────┐ ┌────────┐ ┌────────────┐ ┌────────┐  │
│  │LuxuryApts    │ │ Lofts  │ │LuxuryCondos│ │ Agency │  │
│  └──────────────┘ └────────┘ └────────────┘ └────────┘  │
└───────────────────────────────────────────────────────────┘
```

### Graceful Degradation

If the backend goes down (Railway outage), Retell calls still connect but tool calls fail. The agent's system prompt includes fallback behavior:

> "If tools are unavailable or return errors, say: 'I'm having a little trouble looking that up right now — can I take your number and have our team call you back within the hour?' Capture their name and number verbally, then end the call gracefully."

Redis failure: Outbound calls pause (BullMQ jobs stuck) but inbound still works (webhooks are synchronous Express routes). Redis persistence enabled so queued jobs survive restarts.

### Backup Strategy

- Railway automated daily Postgres backups with point-in-time recovery
- Daily pg_dump to S3/R2 as belt-and-suspenders
- Call recordings already in S3/R2 (durable by default)

---

## 2. Repo Structure

### Repo 1: `voice-concierge-platform`

The product. Deployable by anyone.

```
/backend
  /src
    /api
      /webhooks         — Retell webhook handlers
      /tools            — Tool call endpoints (search_knowledge, check_availability)
      /admin            — Dashboard API routes
      /onboarding       — Self-serve signup + setup
      /billing          — Stripe webhook handlers
    /workers
      /transcript-analyzer.ts    — Claude API: analyze calls, detect gaps
      /knowledge-updater.ts      — Re-chunk + re-embed KB docs
      /outbound-caller.ts        — Execute scheduled outbound calls
      /staleness-checker.ts      — Daily: flag stale KB chunks
      /contradiction-detector.ts — Compare KB vs live API data
      /metering-reporter.ts      — Report usage to Stripe
      /metering-reconciler.ts    — Daily: reconcile our logs vs Stripe
    /services
      /retell.ts          — Retell AI SDK: create agents, provision numbers
      /elevenlabs.ts      — ElevenLabs voice config
      /knowledge.ts       — pgvector search, KB CRUD, versioning
      /compliance.ts      — 7-step pre-call gate, consent management
      /billing.ts         — Stripe subscriptions + meters
      /notifications.ts   — Email digest, Slack/SMS alerts
      /scraper.ts         — Auto-scrape sites for KB seeding
    /db
      /migrations         — All Postgres schemas (with RLS policies)
      /seeds              — Default prompts, voice configs, tier definitions
    /middleware
      /tenant-context.ts  — Extract tenant from auth, set for RLS
      /rate-limiter.ts
      /webhook-verify.ts  — Verify Retell x-retell-signature
  /package.json

/dashboard
  /src/app
    /(auth)
      /login
      /signup
    /(onboarding)
      /setup              — Step-by-step wizard
    /(app)
      /properties         — Property management
      /agents             — Agent config + testing
      /knowledge          — KB editor with version history
      /calls              — Call log + transcript viewer + playback
      /learning
        /gaps             — Gap review queue with notifications
        /stale            — Stale knowledge review
        /contradictions   — KB vs live data mismatches
      /analytics          — Usage, conversion, quality dashboards
      /settings
        /account          — Profile, team members
        /billing          — Plan, usage, invoices
        /integrations     — API endpoints, webhook config
    /docs                 — Embedded help / guides
  /public
    /widget.js            — (served from Retell, not us)
  /package.json

/marketing
  /src/app
    /page.tsx             — Hero, features, pricing, CTA
    /pricing              — Tier comparison + ROI calculator
    /demo                 — Interactive: enter URL → instant demo agent
    /signup               — → onboarding wizard
    /docs                 — Public API docs, integration guides
  /package.json
```

### Repo 2: `voice-concierge-adapters` (private)

Our proprietary glue code + knowledge bases.

```
/adapters
  /luxuryapartments
    /api-routes
      /voice/lead.ts
      /voice/tour.ts
      /voice/listings.ts
      /voice/conversation.ts
    /widget-config.json
    /knowledge
      /the-meridian.md
      /the-heights.md
      /...
  /lofts/...
  /luxurycondos/...
  /agency/...

/scripts
  /sync-knowledge.ts      — Scrape our sites → generate KB drafts
  /deploy-adapters.ts     — Copy API routes into target projects

/templates
  /api-route-template.ts  — Generic adapter for any Next.js site
  /knowledge-template.md  — Blank KB format for new buildings
```

---

## 3. Database Schema

All tenant-scoped tables have RLS policies enforcing `tenant_id = current_setting('app.current_tenant_id')`.

```sql
-- Multi-tenancy
CREATE TABLE tenants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR NOT NULL,
  slug          VARCHAR UNIQUE NOT NULL,
  api_endpoint  VARCHAR,
  api_key_enc   VARCHAR,
  tier          VARCHAR DEFAULT 'starter',
  stripe_customer_id VARCHAR,
  stripe_subscription_id VARCHAR,
  settings      JSONB DEFAULT '{}',
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE properties (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID REFERENCES tenants(id) NOT NULL,
  name          VARCHAR NOT NULL,
  slug          VARCHAR NOT NULL,
  metro_area    VARCHAR,
  address       TEXT,
  timezone      VARCHAR DEFAULT 'America/New_York',
  settings      JSONB DEFAULT '{}',
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agents (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID REFERENCES tenants(id) NOT NULL,
  property_id   UUID REFERENCES properties(id) NOT NULL,
  name          VARCHAR NOT NULL,
  type          VARCHAR NOT NULL,
  retell_agent_id VARCHAR,
  phone_number  VARCHAR,
  system_prompt TEXT NOT NULL,
  voice_id      VARCHAR NOT NULL,
  voice_model   VARCHAR DEFAULT 'eleven_turbo_v2_5',
  status        VARCHAR DEFAULT 'draft',
  max_call_duration_ms INTEGER DEFAULT 900000,
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE calls (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  agent_id        UUID REFERENCES agents(id) NOT NULL,
  property_id     UUID REFERENCES properties(id) NOT NULL,
  retell_call_id  VARCHAR,
  direction       VARCHAR NOT NULL,
  caller_phone    VARCHAR,
  caller_name     VARCHAR,
  status          VARCHAR NOT NULL,
  duration_ms     INTEGER,
  recording_url   VARCHAR,
  transcript      JSONB,
  analysis        JSONB,
  outcome         VARCHAR,
  sentiment_score FLOAT,
  recording_consent BOOLEAN DEFAULT true,
  created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_docs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID REFERENCES tenants(id) NOT NULL,
  property_id   UUID REFERENCES properties(id) NOT NULL,
  content       TEXT NOT NULL,
  version       INTEGER DEFAULT 1,
  is_current    BOOLEAN DEFAULT true,
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id        UUID REFERENCES knowledge_docs(id) NOT NULL,
  tenant_id     UUID REFERENCES tenants(id) NOT NULL,
  property_id   UUID REFERENCES properties(id) NOT NULL,
  metro_area    VARCHAR,
  section       VARCHAR,
  content       TEXT NOT NULL,
  embedding     vector(1536),
  staleness_category VARCHAR,
  stale_after_days INTEGER,
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_embedding ON knowledge_chunks
  USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_tenant_property ON knowledge_chunks(tenant_id, property_id);
CREATE INDEX idx_chunks_tenant_metro ON knowledge_chunks(tenant_id, metro_area);

CREATE TABLE learning_gaps (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  property_id     UUID REFERENCES properties(id) NOT NULL,
  question        TEXT NOT NULL,
  context         TEXT,
  frequency       INTEGER DEFAULT 1,
  status          VARCHAR DEFAULT 'pending_review',
  suggested_answer TEXT,
  approved_answer TEXT,
  approved_by     UUID,
  call_ids        UUID[],
  created_at      TIMESTAMP DEFAULT NOW(),
  resolved_at     TIMESTAMP
);

CREATE TABLE stale_flags (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  property_id     UUID REFERENCES properties(id) NOT NULL,
  chunk_id        UUID REFERENCES knowledge_chunks(id),
  flag_type       VARCHAR NOT NULL,
  details         TEXT,
  current_value   TEXT,
  detected_value  TEXT,
  status          VARCHAR DEFAULT 'pending',
  created_at      TIMESTAMP DEFAULT NOW(),
  resolved_at     TIMESTAMP
);

CREATE TABLE consent_records (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  property_id     UUID,
  contact_phone   VARCHAR NOT NULL,
  contact_name    VARCHAR NOT NULL,
  consent_type    VARCHAR NOT NULL,
  consent_method  VARCHAR NOT NULL,
  consent_text    TEXT NOT NULL,
  ip_address      VARCHAR,
  user_agent      VARCHAR,
  call_id         UUID,
  signed_at       TIMESTAMP NOT NULL,
  revoked_at      TIMESTAMP,
  revocation_method VARCHAR,
  created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_consent_phone ON consent_records(contact_phone, consent_type)
  WHERE revoked_at IS NULL;

CREATE TABLE dnc_list (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  phone_number    VARCHAR NOT NULL,
  source          VARCHAR NOT NULL,
  added_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE usage_records (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  call_id         UUID REFERENCES calls(id),
  minutes         FLOAT NOT NULL,
  reported_to_stripe BOOLEAN DEFAULT false,
  stripe_event_id VARCHAR,
  created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pii_deletion_requests (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenants(id) NOT NULL,
  contact_phone   VARCHAR NOT NULL,
  request_source  VARCHAR NOT NULL,
  status          VARCHAR DEFAULT 'pending',
  items_deleted   JSONB,
  requested_at    TIMESTAMP DEFAULT NOW(),
  completed_at    TIMESTAMP
);

CREATE TABLE team_members (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID REFERENCES tenants(id) NOT NULL,
  clerk_user_id VARCHAR NOT NULL,
  email       VARCHAR NOT NULL,
  name        VARCHAR NOT NULL,
  role        VARCHAR NOT NULL DEFAULT 'member',
  created_at  TIMESTAMP DEFAULT NOW(),
  updated_at  TIMESTAMP DEFAULT NOW()
);
```

### Row-Level Security

```sql
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON properties
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
-- Repeat for all tenant-scoped tables
```

Backend middleware sets tenant context:
```typescript
app.use(async (req, res, next) => {
  const tenantId = extractTenantFromAuth(req);
  await db.query("SET app.current_tenant_id = $1", [tenantId]);
  next();
});
```

---

## 4. Knowledge Engine

### Three-Layer Architecture

**Layer 1: Live Data** — Real-time from each project's Supabase via `/api/voice/listings`. Current pricing, availability, move-in dates. Never cached.

**Layer 2: Curated Knowledge Base** — Per-building markdown documents, chunked and embedded in pgvector. Amenities, neighborhood, policies, building history. Searched via cosine similarity.

**Layer 3: Learned Knowledge** — Answers from real calls via learning loop, human-approved, merged into KB. Grows over time. Compound competitive advantage.

### Mid-Conversation Tool Calls

**Tool: `search_knowledge`** — Embed query, pgvector cosine search, return top 3 chunks. Must respond within 10 seconds.

**Tool: `check_availability`** — Look up tenant's API endpoint, GET live listings, return formatted results.

### Knowledge Versioning & Rollback

Every KB edit creates new version. All versions retained. Dashboard shows diff view and one-click rollback.

### Contradiction Detection

When human approves a learning gap answer: embed new answer, search existing chunks for similarity > 0.85, warn if conflict found.

---

## 5. Agent Persona & Conversation Flow

### Persona
- Warm, confident, unhurried — like the best leasing consultant
- ElevenLabs voice with calm emotion, slightly slower speed (0.9)
- Backchannel enabled for natural responses

### Conversation Flow
1. **Warm Greeting** (~15s) — AI + recording disclosure
2. **Discovery** (~2-3 min) — What brings them, timeline, who's moving
3. **Property Showcase** (~3-5 min) — KB search + live availability
4. **Handle Questions** (~2-5 min) — KB search for every factual question
5. **Soft Close** (~1 min) — Tour offer, info send, or human handoff
6. **Post-Call Automation** — Lead creation, tour booking, follow-up email, transcript for learning

### Hallucination Detection
Post-call analysis flags responses where agent stated facts without preceding search_knowledge tool call.

---

## 6. Learning Loop

Call ends → BullMQ job queued → Claude API analyzes transcript → Extracts gaps, objections, corrections, hallucinations → Gaps written to learning_gaps table (deduplicated) → Notification system triggered by frequency → Human reviews in dashboard → Approved answer appended to KB → Re-chunked and re-embedded → Available on next call.

### Staleness Detection
- Time-based: pricing 7 days, amenities 90 days, policies 180 days, overview 365 days
- Contradiction: live API data vs KB
- Caller-triggered: transcript detects caller corrections
- Site sync: weekly re-scrape and diff

---

## 7. Outbound & Follow-Up System

### Call Types
- Tour reminders (informational, express consent)
- Lead follow-up (marketing, written consent required)
- No-show re-engagement (marketing, written consent required)
- Post-tour follow-up (marketing, written consent required)

### 7-Step Pre-Call Compliance Gate
1. 10am-7pm in caller's timezone?
2. Valid unrevoked consent?
3. Consent type matches call purpose?
4. Federal DNC list check?
5. Internal opt-out list check?
6. Max attempt limit reached?
7. 72hr minimum interval elapsed?

### Consent Capture Points
1. During inbound call — verbal + SMS consent form link
2. Website widget — inline checkbox
3. Tour booking form — checkbox
4. Concierge request form — checkbox

---

## 8. Multi-Tenant Architecture

### Tenant Hierarchy
Tenant → Properties → Agents → Calls, Knowledge, Gaps, Consent

### Isolation
- Data: RLS + application-level tenant_id filtering
- Knowledge: vector search always filtered by tenant_id
- Cross-sell: only within same tenant
- Phone numbers: each maps to one agent, one property, one tenant
- Recordings: stored at recordings/{tenant_id}/{call_id}.wav
- API keys: encrypted at rest, masked in UI
- Widget: domain allowlist per property

### Tier System
- Starter ($99/mo): 1 property, inbound only, 500 min, basic KB
- Pro ($299/mo): 10 properties, inbound + outbound, 2000 min, full features
- Enterprise (custom): unlimited, white-label, custom voice, API access

---

## 9. Security & Data Protection

### PII Handling
- Recordings encrypted at rest in R2
- Configurable retention (default 90 days)
- Auto-delete past retention
- CCPA/GDPR deletion requests tracked and executed
- Retell PII scrubbing on agent creation

### API Key Strategy
One key per service for entire platform (not per-tenant). Per-tenant keys only for tenant's own backend API.

### Widget Security
- Domain allowlist per property
- document.referrer check
- reCAPTCHA v3 for bot protection

---

## 10-14. Supporting Services, Pre-Flight, Specs, Phasing

- Auth: Clerk ($25/mo)
- Email: Resend (free tier)
- SMS: Twilio ($0.0079/SMS)
- Monitoring: Sentry (free) + UptimeRobot (free)
- Storage: Cloudflare R2 ($0.015/GB/mo)
- Analytics: computed from calls table
- Testing: unit, integration, E2E, mock mode

---
---

# PART 2: IMPLEMENTATION PLAN

---

## Phase 1: Platform Core (Tasks 1-15, Weeks 1-4)

### Task 1: Initialize Backend Repo
Express + TypeScript setup, package.json, tsconfig, .env.example, health endpoint.

### Task 2: Database Schema + Migrations
Connection pool, migration runner, 001_initial_schema.sql (all tables), 002_rls_policies.sql.

### Task 3: Tenant Context Middleware + Encryption Service
AES-256 encryption for API keys, tenant context middleware (SET app.current_tenant_id), webhook signature verification.

### Task 4: Knowledge Service (pgvector search)
Document chunking by markdown headings, staleness category assignment, pgvector cosine search with property/portfolio/metro scoping, OpenAI text-embedding-3-small for embeddings, doc ingestion with versioning.

### Task 5: Retell Tool Call Endpoints
search-knowledge endpoint (embed query, pgvector search, return top 3), check-availability endpoint (proxy to tenant's API). Both must respond <10s.

### Task 6: Retell Webhook Handlers
call_started, call_ended, call_analyzed handlers. Usage record creation. Transcript analysis queue.

### Task 7: Retell Agent Management Service
Create/update/delete agents via Retell SDK. Phone number provisioning.

### Task 8: Admin API Routes (CRUD)
Properties, agents, knowledge, calls CRUD with tenant context middleware.

### Task 9: R2 Recording Storage Service
Upload, signed URL generation, deletion via S3-compatible API.

### Task 10: Initialize Dashboard (Next.js + Clerk)
Next.js app with Clerk auth, nav shell, placeholder pages.

### Tasks 11-13: Dashboard Pages
Properties management, agent management + KB editor, call log + transcript viewer.

### Task 14: Deploy Backend to Railway + Dashboard to Vercel
Railway deployment with Postgres + Redis plugins. Vercel dashboard deployment. End-to-end verification.

### Task 15: First Building Knowledge Base
Scrape LuxuryApartments site, write KB doc, ingest via dashboard, create inbound agent, test end-to-end call.

---

## Phase 2: All Projects + Outbound + Learning (Tasks 16-25, Weeks 5-6)

### Tasks 16-17: Adapter API Routes
4 API routes per project (lead, tour, listings, conversation) for all 4 real estate projects.

### Task 18: Knowledge Bases for All Buildings
Scrape, generate, enrich, ingest KBs. Create agents. Provision numbers. Embed widgets.

### Task 19: Transcript Analysis Worker
Claude API analysis: gaps, objections, corrections, hallucinations. BullMQ worker.

### Task 20: Learning Queue Dashboard
Gap review queue, color-coded by frequency, contradiction checking, stale knowledge page.

### Task 21: Notification Service
Dashboard badges, email via Resend, SMS via Twilio. Daily digest cron.

### Task 22: Staleness Detection Workers
Time-based, contradiction (live API vs KB), site sync (weekly re-scrape).

### Task 23: Compliance Service + Consent API
7-step pre-call gate with tests. Public consent form endpoint. Consent management admin API.

### Task 24: Outbound Calling System
Scheduler (tour reminders, follow-ups, no-shows, post-tour). Caller worker with compliance gate. Dashboard management.

### Task 25: Dashboard Analytics Page
Call metrics, conversion rates, sentiment, gap trends, usage vs included minutes.

---

## Phase 3: Spin-Out Completion (Tasks 26-33, Weeks 7-9)

### Task 26: Stripe Billing Integration
Products/prices/meter setup. Billing service. Stripe webhooks. Metering reporter + reconciler. Soft limit warnings.

### Task 27: Self-Serve Onboarding Wizard
Site scraper with questionnaire fallback. 6-step wizard: account, tier, property, KB, agent, go live.

### Task 28: Dashboard Settings Pages
Billing, account, team management, integrations.

### Task 29: White-Label Theming
Tenant branding in dashboard + widget. Enterprise: hide platform branding.

### Task 30: PII Management & Data Deletion
Deletion endpoint, recording retention cleanup, privacy settings page.

### Task 31: Marketing Site
Home, pricing with ROI calculator, interactive demo (enter URL, instant agent), docs.

### Task 32: Customer Documentation
Getting started, KB writing guide, integration guides, compliance guide, API reference.

### Task 33: Free Trial
7-day trial, 50 minutes, Pro features, credit card required, auto-convert or pause.

---

## Phase 4: Launch (Tasks 34-38, Week 10)

### Task 34: Internal QA Pass
Full system test, compliance audit, security review, performance check.

### Task 35: Beta Invite Program
3-5 testers, extended trial, walk-through, feedback collection.

### Task 36: Iterate on Beta Feedback
Persona tuning, KB improvements, conversation flow, dashboard UX, notification thresholds.

### Task 37: Public Launch Preparation
Testimonials, metrics, SEO, launch channels, support readiness.

### Task 38: Go Live
Remove restrictions, enable public signup, monitor 48 hours, quick fixes.

---

## Sources

- Retell AI Create Agent API, Webhook Overview, Chat Widget, Function Calling, Pricing
- ElevenLabs vs Retell Comparison
- Railway Pricing, Node.js + pgvector Starter
- Stripe Usage-Based Billing
- pgvector Benchmarks
- FCC TCPA + AI Voices ruling
- 2026 AI Compliance Guide
- TCPA Appointment Reminders best practices
- State Recording Laws
