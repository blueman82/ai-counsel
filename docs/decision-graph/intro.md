# Decision Graph Memory: Introduction

## What is Decision Graph Memory?

Decision Graph Memory transforms AI Counsel from a stateless deliberation tool into a learning system with organizational memory. After each deliberation completes, the decision is stored in a persistent graph database. When you start a new deliberation, AI Counsel automatically searches for similar past decisions and injects relevant context into the models' prompts.

**Think of it as institutional memory for AI deliberations** — your AI team builds on past decisions rather than starting from scratch every time.

## The Core Problem

Without decision graph memory, AI Counsel treats every deliberation as a fresh start:

- **Redundant debates**: Models rehash the same arguments for similar questions
- **No learning curve**: Past insights are lost after the transcript is saved
- **Longer convergence**: Models spend time establishing context that already exists
- **Missed contradictions**: No way to detect when a new decision conflicts with prior choices

## How It Works: A Mental Model

### 1. Storage Phase (After Deliberation)

When a deliberation completes, AI Counsel extracts:

- The question that was asked
- The consensus reached (from the AI summary)
- Each model's final position, vote, confidence, and rationale
- Convergence status (converged, refining, diverging)
- Path to the full transcript

This data is saved as a **DecisionNode** in a SQLite database (`decision_graph.db`).

**Async Background Processing**: Similarity relationships to past decisions are computed in the background without blocking subsequent deliberations. This keeps deliberation start times fast (<450ms p95 latency).

### 2. Retrieval Phase (Before Deliberation)

When you start a new deliberation:

1. **Question Analysis**: AI Counsel computes semantic similarity between your new question and all past questions in the graph
2. **Top-K Selection**: The top 3 most similar past deliberations are retrieved (configurable via `max_context_decisions`)
3. **Context Injection**: These past decisions are formatted as markdown context and prepended to Round 1 prompts
4. **Models See Context**: Each model sees what similar questions were asked, what consensus was reached, and how confident each participant was

## Key Concepts

### DecisionNode

A completed deliberation stored in the graph.

### ParticipantStance  

Each model's position within a deliberation.

### Similarity Score

A float between 0.0 and 1.0 indicating semantic similarity.

## Benefits and Use Cases

### 1. Accelerated Convergence

Reduce rounds needed by 30-40% for related questions.

### 2. Consistency Across Decisions  

Maintain architectural consistency over time.

### 3. Contradiction Detection

Identify when new decisions conflict with past choices.

### 4. Organizational Learning

Enable team understanding of design decisions and reasoning.

## When to Use Decision Graph Memory

### ✅ **Use It When:**

- Architecture decisions and technology choices
- Related questions over time
- Team consistency needed
- Long-term projects with building decisions
- High deliberation volume (>10/month)

### ❌ **Skip It When:**

- One-off exploratory questions
- Brainstorming without binding decisions
- Privacy concerns
- Low volume (<5 deliberations/month)

## What's Next?

- **[Quickstart Guide](quickstart.md)**: Get running in 5 minutes
- **[Configuration Reference](configuration.md)**: Tune performance
- **[Migration Guide](migration.md)**: Import existing transcripts
