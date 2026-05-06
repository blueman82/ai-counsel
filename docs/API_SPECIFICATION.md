# API Specification: AI Counsel Graphical Front-End

## Overview

This document defines the API contracts between the frontend and backend for the graphical front-end. It covers:
1. **WebSocket Protocol** - Real-time event streaming during deliberations
2. **REST API Endpoints** - HTTP endpoints for queries and commands
3. **Data Models** - JSON schemas for all messages and responses
4. **Error Handling** - Error response formats and recovery strategies

---

## WebSocket Protocol

### Connection

**URL**: `ws://localhost:8765` (or configured in `.env`)

**Headers**: None required for MVP (can add authentication later)

**Connection lifecycle**:
1. Client initiates WebSocket connection
2. Client waits for `connection_established` event (optional handshake)
3. Client listens for event messages
4. Client auto-reconnects on disconnect with exponential backoff

### Message Format

All WebSocket messages are JSON objects with this structure:

```json
{
  "type": "event_type",
  "timestamp": "2025-10-23T14:30:00.000Z",
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

**Fields**:
- `type` (string, required): Event type identifier
- `timestamp` (string, ISO 8601): Server timestamp when event was sent
- `data` (object): Event-specific payload

### Events

#### 1. `deliberation_started`

**Direction**: Server → Client

**Sent when**: New deliberation is initiated

**Payload**:
```json
{
  "type": "deliberation_started",
  "timestamp": "2025-10-23T14:30:00.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Should we use TypeScript for the new backend?",
    "mode": "conference",
    "participants": [
      {
        "cli": "claude",
        "model": "sonnet"
      },
      {
        "cli": "codex",
        "model": "gpt-5-codex"
      }
    ],
    "rounds": 3,
    "metadata": {
      "started_at": "2025-10-23T14:30:00.000Z"
    }
  }
}
```

**Frontend action**: Store session metadata, show timeline grid, start loading animation

---

#### 2. `round_started`

**Direction**: Server → Client

**Sent when**: New round begins (before any responses)

**Payload**:
```json
{
  "type": "round_started",
  "timestamp": "2025-10-23T14:30:15.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "round": 1,
    "participant_count": 2
  }
}
```

**Frontend action**: Show "Round 1 in progress..." indicator, show loading spinners in grid cells

---

#### 3. `response_received`

**Direction**: Server → Client

**Sent when**: A single model returns a response

**Payload**:
```json
{
  "type": "response_received",
  "timestamp": "2025-10-23T14:30:45.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "round": 1,
    "participant": {
      "cli": "claude",
      "model": "sonnet"
    },
    "response": "TypeScript is strongly recommended for large codebases due to type safety and better IDE support. However, for small scripts, JavaScript may be sufficient.",
    "vote": {
      "option": "Option A (TypeScript)",
      "confidence": 0.88,
      "rationale": "Type safety outweighs learning curve"
    },
    "metadata": {
      "execution_time_ms": 3500,
      "tokens_used": 245
    }
  }
}
```

**Frontend action**: Update grid cell for this participant/round with response, show vote badge, update confidence color

---

#### 4. `round_completed`

**Direction**: Server → Client

**Sent when**: All responses for a round are received

**Payload**:
```json
{
  "type": "round_completed",
  "timestamp": "2025-10-23T14:31:00.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "round": 1,
    "total_responses": 2,
    "duration_seconds": 60,
    "all_responses": [
      {
        "participant": {
          "cli": "claude",
          "model": "sonnet"
        },
        "response": "...",
        "vote": { ... }
      },
      {
        "participant": {
          "cli": "codex",
          "model": "gpt-5-codex"
        },
        "response": "...",
        "vote": { ... }
      }
    ]
  }
}
```

**Frontend action**: All cells for this round should be filled, remove loading spinners, enable scroll

---

#### 5. `convergence_updated`

**Direction**: Server → Client

**Sent when**: Convergence detection completes after each round

**Payload**:
```json
{
  "type": "convergence_updated",
  "timestamp": "2025-10-23T14:31:05.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "round": 1,
    "convergence_info": {
      "detected": true,
      "detection_round": 1,
      "final_similarity": 0.85,
      "status": "refining",
      "scores_by_round": [
        { "round": 1, "similarity": 0.85 }
      ]
    },
    "voting_result": {
      "final_tally": {
        "Option A (TypeScript)": 2,
        "Option B (JavaScript)": 0
      },
      "consensus_reached": false,
      "winning_option": "Option A (TypeScript)"
    }
  }
}
```

**Frontend action**: Update ConvergenceStatus component with new similarity score and voting tally

---

#### 6. `deliberation_completed`

**Direction**: Server → Client

**Sent when**: All rounds complete or early stopping triggered

**Payload**:
```json
{
  "type": "deliberation_completed",
  "timestamp": "2025-10-23T14:32:00.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "complete",
    "rounds_completed": 2,
    "total_duration_seconds": 120,
    "convergence_status": "refining",
    "final_consensus": "Strong majority consensus on using TypeScript. Minor concerns about learning curve from one participant.",
    "voting_summary": {
      "final_tally": {
        "Option A (TypeScript)": 3,
        "Option B (JavaScript)": 0
      },
      "winning_option": "Option A (TypeScript)",
      "confidence": {
        "Option A": 0.88,
        "Option B": null
      }
    },
    "transcript_url": "/api/deliberations/550e8400-e29b-41d4-a716-446655440000/transcript",
    "metadata": {
      "context_injected_from": [
        "50e8400-e29b-41d4-a716-446655440001"
      ],
      "early_stopped": false,
      "early_stop_reason": null
    }
  }
}
```

**Frontend action**: Show completion banner, enable export/share buttons, optionally show "new deliberation" prompt

---

#### 7. `error`

**Direction**: Server → Client

**Sent when**: Error occurs during deliberation

**Payload**:
```json
{
  "type": "error",
  "timestamp": "2025-10-23T14:31:30.000Z",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "round": 1,
    "error_type": "AdapterError",
    "error_message": "Claude adapter timed out after 180s",
    "participant": {
      "cli": "claude",
      "model": "sonnet"
    },
    "severity": "warning",
    "recovery_action": "Skipping this participant for this round and continuing with others"
  }
}
```

**Frontend action**: Show error toast/notification, optionally allow user to retry

---

### Client-to-Server Messages (Optional, Post-MVP)

These can be added later for advanced features like pause/resume:

```json
{
  "type": "client_command",
  "data": {
    "command": "pause" | "resume" | "stop",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## REST API Endpoints

### Base URL

```
http://localhost:8000/api
```

(Configurable via `VITE_API_URL` environment variable)

### 1. Start Deliberation

**Endpoint**: `POST /api/deliberations`

**Request**:
```json
{
  "question": "Should we use microservices or monolithic architecture?",
  "participants": [
    {
      "cli": "claude",
      "model": "sonnet"
    },
    {
      "cli": "codex",
      "model": "gpt-5-codex"
    }
  ],
  "rounds": 3,
  "mode": "conference",
  "context": "We're building a new platform with 50+ engineers. Need to decide on architecture."
}
```

**Response** (201 Created):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "question": "Should we use microservices or monolithic architecture?",
  "ws_url": "ws://localhost:8765",
  "estimated_duration_seconds": 120,
  "created_at": "2025-10-23T14:30:00.000Z"
}
```

**Errors**:
```json
{
  "error": "Invalid participant configuration",
  "status": 400,
  "details": "Minimum 2 participants required"
}
```

---

### 2. Get Deliberation Status

**Endpoint**: `GET /api/deliberations/{session_id}`

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Should we use microservices or monolithic architecture?",
  "status": "in_progress",
  "current_round": 2,
  "total_rounds": 3,
  "elapsed_seconds": 45,
  "responses_received": 3,
  "total_responses_expected": 6,
  "convergence_status": "refining",
  "ws_url": "ws://localhost:8765"
}
```

---

### 3. Get Completed Deliberation

**Endpoint**: `GET /api/deliberations/{session_id}/result`

**Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Should we use microservices or monolithic architecture?",
  "status": "complete",
  "rounds_completed": 3,
  "convergence_info": {
    "status": "majority_decision",
    "similarity": 0.82
  },
  "voting_result": {
    "final_tally": {
      "Microservices": 2,
      "Monolithic": 1
    },
    "consensus_reached": true,
    "winning_option": "Microservices"
  },
  "summary": {
    "consensus": "Majority consensus for microservices architecture",
    "key_agreements": [
      "Scalability is critical",
      "Team size can support complexity"
    ],
    "key_disagreements": [
      "Operational complexity concerns"
    ],
    "final_recommendation": "Implement microservices with strong emphasis on observability and operational tooling"
  },
  "transcript_url": "/api/deliberations/550e8400-e29b-41d4-a716-446655440000/transcript",
  "duration_seconds": 180,
  "completed_at": "2025-10-23T14:33:00.000Z"
}
```

---

### 4. Get Transcript

**Endpoint**: `GET /api/deliberations/{session_id}/transcript`

**Query params**:
- `format` (optional): `markdown`, `json`, `pdf` (default: `markdown`)

**Response** (200 OK):
- Content-Type: `text/markdown` or `application/json` or `application/pdf`
- Returns full debate transcript

---

### 5. List Adapters & Models

**Endpoint**: `GET /api/adapters`

**Response** (200 OK):
```json
{
  "adapters": {
    "claude": {
      "type": "cli",
      "models": [
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001"
      ]
    },
    "codex": {
      "type": "cli",
      "models": [
        "gpt-5-codex",
        "o3"
      ]
    },
    "droid": {
      "type": "cli",
      "models": [
        "claude-opus-4-5-20251101"
      ]
    },
    "gemini": {
      "type": "cli",
      "models": [
        "gemini-2.5-pro",
        "gemini-2.0-flash"
      ]
    },
    "ollama": {
      "type": "http",
      "description": "Local Ollama instance",
      "available": true
    },
    "openrouter": {
      "type": "http",
      "description": "OpenRouter API",
      "available": true
    }
  }
}
```

---

### 6. Search Decision Graph

**Endpoint**: `GET /api/decisions/search`

**Query params**:
- `q` (required): Search query
- `limit` (optional): Max results (default: 5, max: 20)
- `threshold` (optional): Similarity threshold (0.0-1.0, default: 0.7)

**Response** (200 OK):
```json
{
  "count": 3,
  "query": "microservices architecture",
  "results": [
    {
      "id": "50e8400-e29b-41d4-a716-446655440001",
      "question": "Should we adopt microservices?",
      "similarity_score": 0.92,
      "consensus": "Majority decision: Yes, with caveats about operational complexity",
      "participants": 3,
      "rounds": 2,
      "created_at": "2025-10-20T10:00:00.000Z"
    },
    {
      "id": "50e8400-e29b-41d4-a716-446655440002",
      "question": "Monolith vs microservices for new backend?",
      "similarity_score": 0.88,
      "consensus": "Split decision, no consensus",
      "participants": 2,
      "rounds": 1,
      "created_at": "2025-10-18T14:00:00.000Z"
    }
  ]
}
```

---

### 7. Get Decision by ID

**Endpoint**: `GET /api/decisions/{decision_id}`

**Response** (200 OK):
```json
{
  "id": "50e8400-e29b-41d4-a716-446655440001",
  "question": "Should we adopt microservices?",
  "consensus": "Majority decision: Yes, with operational concerns",
  "participants": [
    {
      "cli": "claude",
      "model": "sonnet"
    },
    {
      "cli": "codex",
      "model": "gpt-5-codex"
    }
  ],
  "votes": [
    {
      "round": 1,
      "participant": "sonnet@claude",
      "option": "Yes",
      "confidence": 0.85,
      "rationale": "Scalability benefits outweigh complexity"
    }
  ],
  "created_at": "2025-10-20T10:00:00.000Z"
}
```

---

### 8. Get Decision Graph Stats

**Endpoint**: `GET /api/decisions/stats`

**Response** (200 OK):
```json
{
  "total_decisions": 47,
  "total_participants_unique": 4,
  "avg_convergence": 0.72,
  "convergence_distribution": {
    "converged": 12,
    "refining": 18,
    "diverging": 12,
    "impasse": 5
  },
  "most_common_questions": [
    "Should we use TypeScript?",
    "Microservices vs monolith?",
    "REST vs GraphQL?"
  ],
  "last_updated": "2025-10-23T14:30:00.000Z"
}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "error": "Human-readable error message",
  "error_type": "ErrorClass",
  "status": 400,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-23T14:30:00.000Z",
  "details": {
    "field": "error detail"
  }
}
```

### Common Status Codes

- `200 OK` - Successful GET/POST request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `409 Conflict` - Already exists or state conflict
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily down

---

## Data Models (JSON Schemas)

### Participant

```json
{
  "cli": "claude | codex | droid | gemini | ollama | lmstudio | openrouter | llamacpp",
  "model": "string (model identifier)"
}
```

### Vote

```json
{
  "option": "string (e.g., 'Option A', 'Yes', 'Strongly Agree')",
  "confidence": "number (0.0 - 1.0)",
  "rationale": "string (explanation for vote)",
  "continue_debate": "boolean (whether this participant wants to continue)"
}
```

### RoundResponse

```json
{
  "participant": {
    "cli": "string",
    "model": "string"
  },
  "response": "string (full response text)",
  "vote": {
    "option": "string",
    "confidence": "number",
    "rationale": "string"
  },
  "timestamp": "ISO 8601 timestamp"
}
```

---

## Rate Limiting & Quotas

**MVP Implementation**: No rate limiting

**Post-MVP Recommendations**:
- Limit WebSocket connections per IP: 5
- Limit new deliberations per IP per hour: 10
- Limit deliberation duration: 300 seconds per round

---

## Authentication & Authorization

**MVP Implementation**: No authentication

**Post-MVP Recommendations**:
- JWT token for session authentication
- API key for programmatic access
- Per-user deliberation history

---

## Versioning Strategy

**Current**: No versioning (MVP)

**When to version** (post-MVP):
- New major features added
- Breaking changes to event format
- New required fields

**Versioning approach**:
- API version in URL: `/api/v1/deliberations`
- WebSocket version in handshake message
- Backward compatibility for at least 2 versions

---

## Monitoring & Observability

**Metrics to track**:
- WebSocket connection count
- Average deliberation duration
- Error rate by adapter
- Response latency by percentile (p50, p95, p99)
- Token usage per deliberation

**Logging**:
- All WebSocket events: `info` level
- Errors: `error` level with stack trace
- Slow operations (>5s): `warning` level

---

## Security Considerations

**Current (MVP)**:
- No authentication
- Localhost-only WebSocket
- No rate limiting
- No input validation beyond Pydantic

**Post-MVP**:
- HTTPS for REST API
- WSS (Secure WebSocket)
- CORS headers
- Input sanitization
- OWASP compliance

---

## Example: Complete Deliberation Flow

### 1. Client initiates deliberation
```
POST /api/deliberations
→ Returns session_id and ws_url
```

### 2. Frontend connects to WebSocket
```
ws://localhost:8765
```

### 3. Server sends event sequence
```
→ deliberation_started
→ round_started (round 1)
→ response_received (participant 1)
→ response_received (participant 2)
→ round_completed
→ convergence_updated
→ (if continuing)
→ round_started (round 2)
→ ... (more responses)
→ deliberation_completed
```

### 4. Frontend polls for final result (optional)
```
GET /api/deliberations/{session_id}/result
```

### 5. Frontend exports transcript
```
GET /api/deliberations/{session_id}/transcript?format=markdown
```

---

## Testing the API

### Using curl:
```bash
# Start deliberation
curl -X POST http://localhost:8000/api/deliberations \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test question?",
    "participants": [
      {"cli": "claude", "model": "sonnet"},
      {"cli": "codex", "model": "gpt-5-codex"}
    ],
    "rounds": 2
  }'

# Get status
curl http://localhost:8000/api/deliberations/{session_id}

# List adapters
curl http://localhost:8000/api/adapters
```

### Using WebSocket client (Node.js):
```javascript
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('Connected');
});

ws.on('message', (data) => {
  const event = JSON.parse(data);
  console.log('Event:', event.type, event.data);
});

ws.on('error', (error) => {
  console.error('Error:', error);
});
```

---

## Future Enhancements

1. **Streaming Response Bodies** - Send partial responses as they're generated
2. **Model Interruption** - Allow client to interrupt slow models mid-deliberation
3. **Custom Voting Schemas** - Let users define custom voting options
4. **Debate Playback** - Replay deliberations at faster/slower speeds
5. **Real-time Diff** - Show changes in model positions between rounds
6. **Synthetic Moderator** - AI moderator that asks follow-up questions
7. **Collaboration Mode** - Multiple users observing same deliberation
