# Decision Graph Memory: Quickstart

Get decision graph memory running in 5 minutes.

## Prerequisites

- AI Counsel installed and configured
- At least one CLI adapter working
- Python 3.11+
- Write access to project directory

## Step 1: Enable Feature (30 seconds)

Edit `config.yaml`:

```yaml
decision_graph:
  enabled: true
  db_path: "decision_graph.db"
  similarity_threshold: 0.7
  max_context_decisions: 3
  compute_similarities: true
```

## Step 2: Run First Deliberation (2 minutes)

```bash
ai-counsel deliberate \
  --question "Should we use REST or GraphQL for our API?" \
  --participants "opus@claude,gpt-4@codex" \
  --rounds 3
```

## Step 3: Verify Memory Stored (30 seconds)

```bash
ai-counsel graph similar --query "API design" --limit 5
```

**Expected**: Returns your stored decision

## Step 4: Test Context Injection (2 minutes)

Run a related deliberation:

```bash
ai-counsel deliberate \
  --question "What authentication should we use for the API?" \
  --participants "opus@claude,gpt-4@codex" \
  --rounds 3
```

Check the transcript for "Decision Graph Context" section.

## Quick Troubleshooting

**No context injected?**
- Check if enabled: `grep decision_graph config.yaml`
- Wait 15 seconds (background processing)
- Lower threshold: `similarity_threshold: 0.5`

**Decision not stored?**
- Verify database: `ls -la decision_graph.db`
- Check write permissions

## What's Next?

- **[Configuration Reference](configuration.md)**: Tune performance
- **[Troubleshooting](troubleshooting.md)**: Debug issues
- **[Deployment Guide](deployment.md)**: Production setup
