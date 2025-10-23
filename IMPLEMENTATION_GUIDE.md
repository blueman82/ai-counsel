# AI Counsel Graphical Front-End: Complete Implementation Guide

**Status**: ✅ Design Complete | Implementation Ready

**Date**: October 23, 2025

**Total Documentation**: ~150KB across 4 comprehensive documents

---

## What Has Been Delivered

### 1. **Complete Design Document** ([`docs/plans/graphical-frontend.md`](./docs/plans/graphical-frontend.md)) - 67KB

**24 Implementation Tasks** broken down into three milestones:

**Milestone 1: MVP (4-6 weeks)**
- ✅ Task 1-15: Core backend (WebSocket server, event streaming, REST API)
- ✅ Task 4-12: Core frontend (React + TypeScript + Vite, components, real-time UI)
- ✅ Task 13-16: Testing and quality assurance

**Milestone 2: Phase 1.5 (2-3 weeks)**
- ✅ Task 16-18: Decision graph search integration

**Milestone 3: Polish (2-3 weeks)**
- ✅ Task 19-24: Export features, dark mode, mobile optimization, accessibility, deployment

**Key Features**:
- Every task includes: description, dependencies, estimated time, TDD test strategy, detailed implementation code structure, integration points, verification steps, commit strategy
- References to existing code patterns in the codebase
- Prerequisites checklist before starting
- Common pitfalls and how to avoid them
- Clear progression from MVP to polished product

---

### 2. **API Specification** ([`docs/API_SPECIFICATION.md`](./docs/API_SPECIFICATION.md)) - 18KB

**Complete API Contract** defining:

**WebSocket Protocol** (Real-time streaming):
- 7 event types: `deliberation_started`, `response_received`, `round_completed`, `convergence_updated`, `deliberation_completed`, `error`
- Detailed message format and payload schemas
- Examples for each event type
- Client message format (extensible for future features)

**REST API Endpoints**:
- `POST /api/deliberations` - Start new deliberation
- `GET /api/deliberations/{session_id}` - Get status
- `GET /api/deliberations/{session_id}/result` - Get completed result
- `GET /api/deliberations/{session_id}/transcript` - Export transcript (Markdown/JSON/PDF)
- `GET /api/adapters` - List available models
- `GET /api/decisions/search` - Search decision graph
- `GET /api/decisions/{id}` - Get past decision
- `GET /api/decisions/stats` - Graph statistics

**Data Models** (JSON Schemas):
- Complete JSON schemas for all request/response types
- Example payloads for each endpoint
- Error response format

**Key Features**:
- Example curl commands for testing
- WebSocket client code (Node.js/JavaScript)
- Rate limiting recommendations (post-MVP)
- Versioning strategy
- Security considerations

---

### 3. **UI Mockups & Design System** ([`docs/UI_MOCKUPS.md`](./docs/UI_MOCKUPS.md)) - 34KB

**5 Complete Screens** with mockups and specifications:

**Screen 1: Home/Initial State**
- Question input form
- Participant selector (grouped by adapter)
- Settings (rounds, voting, context injection)
- Responsive mobile layout

**Screen 2: Active Deliberation - Timeline Grid**
- Timeline grid showing models × rounds
- Color-coded confidence levels
- Expandable cells for full responses
- Convergence status display
- Mobile horizontal scroll

**Screen 3: Completion**
- Summary with verdict
- Voting breakdown with confidence metrics
- Context injection details
- Export/share options

**Screen 4: Decision Graph Search**
- Sidebar showing similar past decisions
- Similarity scores
- Quick access to past decisions

**Screen 5: Export Modal**
- Multiple format options (Markdown, JSON, PDF)
- Options for anonymization and metadata

**Design System**:
- Color palette (light/dark mode)
- Typography scales
- Spacing system
- Button styles
- Grid layout specifications
- Mobile responsive breakpoints

**Accessibility Features**:
- Keyboard navigation guide
- ARIA labels and roles
- Color contrast compliance (WCAG AA)
- Focus indicators
- Reduced motion support

---

### 4. **Proof of Concept Code** ([`docs/PROOF_OF_CONCEPT.md`](./docs/PROOF_OF_CONCEPT.md)) - 33KB

**Production-Ready Starter Code**:

**Backend**:
- ✅ Complete `WebSocketServer` class (Python websockets library)
- ✅ Event emission integration with DeliberationEngine
- ✅ Global instance management
- ✅ Connection handling and cleanup

**Frontend Services**:
- ✅ `apiClient` (axios-based HTTP client with error handling)
- ✅ `WebSocketClient` (with auto-reconnection and exponential backoff)
- ✅ Event subscription system (EventEmitter pattern)
- ✅ Message queueing for offline resilience

**Frontend Components**:
- ✅ `QuestionInput` component (form validation, participant selection)
- ✅ `TimelineGrid` component (responsive grid layout, color-coded cells)
- ✅ Full CSS module example (mobile-responsive)

**State Management**:
- ✅ Zustand store (`useDeliberationStore`)
- ✅ Custom hook for WebSocket events (`useWebSocketEvents`)
- ✅ Query hook for adapters (`useAdapters`)

**Configuration**:
- ✅ `.env.example` with all required variables
- ✅ Quick start commands for both backend and frontend

**Key Features**:
- All code is typed (TypeScript strict mode ready)
- TDD-ready (all code structured for testing)
- Production patterns (error handling, logging, cleanup)
- Copy-paste ready: takes ~2-3 hours to adapt to your project

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│            Frontend (React + TypeScript)             │
│  ┌────────────────────────────────────────────────┐  │
│  │ Components:                                    │  │
│  │ - QuestionInput (form)                         │  │
│  │ - TimelineGrid (main visualization)            │  │
│  │ - ConvergenceStatus (voting display)           │  │
│  │ - DecisionGraphSearch (sidebar)                │  │
│  │ - ExportButton, ThemeToggle, etc.             │  │
│  │                                                │  │
│  │ State: Zustand store (centralized)             │  │
│  │ API: React Query + axios (HTTP)                │  │
│  │ Real-time: WebSocket client (ws library)       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│                      ↕ HTTP & WebSocket             │
│                                                      │
│              Backend (Python asyncio)               │
│  ┌────────────────────────────────────────────────┐  │
│  │ MCP Server (server.py):                        │  │
│  │ - MCP tool handler (stdio protocol)            │  │
│  │ - REST API endpoints (FastAPI/aiohttp)        │  │
│  │ - WebSocket server (websockets library)        │  │
│  │                                                │  │
│  │ DeliberationEngine:                            │  │
│  │ - Orchestrates AI model interactions          │  │
│  │ - Emits WebSocket events in real-time         │  │
│  │ - Handles convergence detection               │  │
│  │ - Manages voting and summarization            │  │
│  │                                                │  │
│  │ Decision Graph:                                │  │
│  │ - Stores past deliberations (SQLite)          │  │
│  │ - Provides context injection                  │  │
│  │ - Enables semantic search                     │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│                    ↕ CLI/HTTP                       │
│                                                      │
│        External AI Models (Claude, GPT, etc)        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### ✅ Why Real-Time WebSocket (not polling)?
- **Live "debate room" experience**: Users see responses arrive as they happen
- **Bandwidth efficient**: Push only when events occur
- **Low latency**: Immediate updates (< 500ms target)
- **Scalable**: Can handle multiple concurrent deliberations

### ✅ Why Timeline Grid (not cards or threads)?
- **Natural comparison**: Horizontal scan shows model evolution
- **Compact**: All data visible at once (desktop)
- **Spreadsheet-like**: Familiar mental model for technical users
- **Responsive**: Horizontal scroll on mobile maintains usability

### ✅ Why Technical Decision-Makers as Beachhead?
- **Clear persona**: CTOs, tech leads, architects
- **Proven demand**: 70+ existing deliberations in this domain
- **Fast validation**: Quick adoption, clear ROI
- **Growth path**: Expand to enterprise features after PMF

### ✅ Why React + TypeScript + Vite?
- **Ecosystem**: 10,000+ libraries, largest talent pool
- **Maintainability**: TypeScript catches errors early
- **Performance**: Vite builds in <100ms during development
- **Integration**: Clean SPA model with existing Python backend

---

## Implementation Roadmap

### Week 1-2: Backend Infrastructure
- [ ] WebSocket server setup + event emission
- [ ] REST API endpoints (start deliberation, fetch status)
- [ ] Adapter listing and decision graph search

### Week 2-3: Frontend Scaffolding & Services
- [ ] React + TypeScript + Vite project
- [ ] API client and WebSocket client
- [ ] State management (Zustand store)
- [ ] Custom hooks for event handling

### Week 3-4: Core Components
- [ ] Question input form
- [ ] Timeline grid visualization
- [ ] Convergence status display
- [ ] Real-time integration testing

### Week 4-5: Decision Graph Integration
- [ ] Search API endpoints
- [ ] Search UI component
- [ ] Context injection display

### Week 5-6: Polish & Features
- [ ] Export (Markdown/JSON/PDF)
- [ ] Dark mode toggle
- [ ] Mobile optimization
- [ ] Accessibility audit
- [ ] Error handling & loading states

### Week 6-7: Testing & Deployment
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Docker container
- [ ] Deploy to staging/production

---

## Success Criteria

### MVP (End of Week 4)
- ✅ Users can enter questions and select models
- ✅ Real-time timeline shows responses arriving
- ✅ Convergence status updates live
- ✅ Deliberation completes and shows results
- ✅ Can export transcript as Markdown

### Phase 1.5 (End of Week 5)
- ✅ Decision graph search finds similar past decisions
- ✅ Context from past decisions visible during deliberation
- ✅ Similar decisions sidebar populated

### Polished Product (End of Week 7)
- ✅ Export to PDF and JSON
- ✅ Dark mode support
- ✅ Mobile responsive (works on tablet/phone)
- ✅ WCAG 2.1 AA accessibility compliance
- ✅ Handles network errors gracefully
- ✅ ~80% unit test coverage
- ✅ Deployed and accessible

---

## Files to Review

**Before Starting**:
1. Read [`docs/plans/graphical-frontend.md`](./docs/plans/graphical-frontend.md) - Full implementation plan
2. Skim [`docs/API_SPECIFICATION.md`](./docs/API_SPECIFICATION.md) - Understand the contract
3. Check [`docs/UI_MOCKUPS.md`](./docs/UI_MOCKUPS.md) - Know what you're building
4. Reference [`docs/PROOF_OF_CONCEPT.md`](./docs/PROOF_OF_CONCEPT.md) - Starter code

**Existing Codebase**:
- `models/schema.py` - Data models (Pydantic patterns)
- `deliberation/engine.py` - Engine architecture (async patterns)
- `tests/conftest.py` - Testing patterns
- `server.py` - MCP integration example

---

## Getting Started

### For Backend Engineers
1. Start with Task 1-3 in implementation plan (WebSocket + REST API)
2. Reference backend patterns in `deliberation/engine.py`
3. Use `tests/conftest.py` as mock adapter example
4. Run: `pip install websockets fastapi uvicorn`

### For Frontend Engineers
1. Start with Task 4-5 in implementation plan (React setup + services)
2. Copy starter code from `PROOF_OF_CONCEPT.md`
3. Reference TypeScript patterns in existing codebase
4. Run: `npm create vite@latest frontend -- --template react-ts`

### For Full-Stack Teams
1. Parallelize: Backend tasks 1-3 + Frontend tasks 4-5 simultaneously
2. Integrate WebSocket (Task 2) + Frontend hook (Task 9) together
3. Test end-to-end after both are complete
4. Iterate on features from Task 6 onward

---

## Key Metrics to Track

### Development
- Velocity: tasks/week
- Test coverage: target >80%
- Build time: < 2 minutes
- Lighthouse score: >90 (performance, accessibility, best practices)

### Runtime
- WebSocket connection success rate: >99%
- Response latency (p95): <500ms
- Deliberation completion time: tracked
- Error rate: <1%

### User Experience
- Time-to-first-response: <2 seconds
- Timeline grid load time: <1 second
- Mobile responsiveness: works on 320px+ screens

---

## Risk Mitigation

### Potential Risks
1. **WebSocket connection drops** → Implement auto-reconnect with exponential backoff
2. **Slow model responses** → Show loading states, allow timeout configuration
3. **Large timeline grids** → Virtualization for 5+ models × 5 rounds
4. **Mobile responsiveness** → Test early and often on real devices
5. **API contract changes** → Version endpoint URLs, maintain backward compatibility

---

## Future Enhancements (Post-MVP)

1. **Streaming Responses**: Show partial responses as they're generated
2. **Model Interruption**: User can interrupt slow models
3. **Debate Playback**: Replay deliberations at different speeds
4. **Synthetic Moderator**: AI asks follow-up questions
5. **Collaboration Mode**: Multiple users observing same deliberation
6. **Authentication**: User accounts, deliberation history
7. **Advanced Analytics**: Charts showing model agreement trends
8. **Custom Voting Schemas**: User-defined voting options

---

## Support & Questions

### Documentation
- Implementation plan: `docs/plans/graphical-frontend.md`
- API spec: `docs/API_SPECIFICATION.md`
- UI mockups: `docs/UI_MOCKUPS.md`
- Starter code: `docs/PROOF_OF_CONCEPT.md`

### Code References
- WebSocket patterns: See `server_websocket.py` in PROOF_OF_CONCEPT.md
- Component patterns: See React examples in PROOF_OF_CONCEPT.md
- Testing patterns: `tests/conftest.py` (existing mocks)

### Getting Help
1. Check the relevant documentation file
2. Search existing code for similar patterns
3. Refer to external library docs (React, Pydantic, websockets)
4. Ask in code review for architectural feedback

---

## Summary

You now have:

✅ **Complete design** - 24 tasks broken down with clear dependencies
✅ **API specification** - Full contract for frontend-backend communication
✅ **UI mockups** - Every screen designed with accessibility & responsiveness
✅ **Starter code** - Production-ready templates for immediate use
✅ **Architecture diagram** - Clear data flow and component relationships
✅ **Roadmap** - 7-week realistic timeline with milestones
✅ **Success criteria** - Clear definition of done for MVP and beyond

**Ready to implement?** Start with Task 1 in `docs/plans/graphical-frontend.md` and follow the TDD approach. The design is comprehensive, but not prescriptive - adapt as needed for your team's constraints and preferences.

**Estimated effort**: 10-14 weeks solo, 4-6 weeks with team of 2-3 engineers.

Good luck! 🚀
