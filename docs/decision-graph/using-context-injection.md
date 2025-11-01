# Using Context Injection

Context injection accelerates deliberations by showing AI models similar past decisions before they debate. Instead of reinventing the wheel, models build on previous reasoning.

## How It Works

When you start a deliberation, the system searches for similar past decisions and injects them into Round 1 prompts. Context is tiered by relevance:

- **Strong** (similarity ≥0.75): Full detail with participant positions, votes, and rationale (~500 tokens each)
- **Moderate** (0.60-0.74): Summary format with question and consensus (~200 tokens each)
- **Brief** (<0.60): One-liner reference (~50 tokens each)

The system stops injecting when your token budget is reached, prioritizing the strongest matches.

## Enable It

Add these 3 lines to `config.yaml`:

```yaml
decision_graph:
  enabled: true
  db_path: "decision_graph.db"
  context_token_budget: 1500
```

Default tier boundaries (0.75/0.60) work well for most cases.

## See It In Action

When you run a deliberation like "Should we use Kubernetes?", the Round 1 prompt includes:

```markdown
## Similar Past Deliberations (Tiered by Relevance)

### Strong Match (similarity: 0.82): Should we use Docker for containerization?
**Date**: 2025-10-20T14:30:00
**Convergence Status**: converged
**Consensus**: Yes, Docker should be adopted for consistent deployment
**Winning Option**: Adopt Docker
**Participants**: claude, codex, gemini

**Participant Positions**:
- **claude**: Voted for 'Adopt Docker' (confidence: 85%) - Solves environment consistency issues
- **codex**: Voted for 'Adopt Docker' (confidence: 90%) - Industry standard, strong ecosystem
- **gemini**: Voted for 'Adopt Docker' (confidence: 80%) - Learning curve acceptable given benefits

### Moderate Match (similarity: 0.67): Should we implement microservices architecture?
**Consensus**: Start with modular monolith, migrate high-traffic components to services gradually
**Result**: Phased approach
```

Models see this before Round 1, building on previous reasoning instead of starting from scratch.

## Tune It

Adjust in `config.yaml`:

```yaml
decision_graph:
  context_token_budget: 2000  # Increase for more context (default: 1500)
  tier_boundaries:
    strong: 0.80   # Raise for stricter "strong" threshold (default: 0.75)
    moderate: 0.65 # Raise for stricter "moderate" threshold (default: 0.60)
```

## Best Practices

**When to increase token_budget**:
- Complex domains where more historical context helps
- After 100+ decisions when matches are richer
- Check logs: if you see "Token budget reached" frequently

**When to adjust tier_boundaries**:
- If strong tier dominates (>75% of matches): raise to 0.80
- If convergence happens without strong matches: lower to 0.70
- Start with defaults, adjust after 50+ deliberations based on data

**When NOT to adjust**:
- Don't tune on <20 deliberations (insufficient data)
- Don't raise budget above 3000 (diminishing returns, context overload)
- Don't lower boundaries below 0.50 (noise floor is 0.40, you'll get garbage)

Context injection is automatic once enabled. No manual intervention needed—the system finds, ranks, and formats relevant past decisions for you.
