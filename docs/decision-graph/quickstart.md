# Decision Graph Memory: Quickstart

Get decision graph memory running in 5 minutes using Claude Code.

## Prerequisites

- AI Counsel MCP server installed and configured in `~/.claude/config/mcp.json`
- At least one adapter working (Claude, Codex, etc.)
- Claude Code with MCP support enabled
- Write access to AI Counsel project directory

## Step 1: Enable Feature (30 seconds)

Edit `config.yaml` in your AI Counsel directory:

```yaml
decision_graph:
  enabled: true
  db_path: "decision_graph.db"
  similarity_threshold: 0.7
  max_context_decisions: 3
  compute_similarities: true
```

Save and restart Claude Code (or reload the MCP server).

## Step 2: Run First Deliberation (2 minutes)

In Claude Code, use the `deliberate` MCP tool:

```
Use the mcp__ai-counsel__deliberate tool with:
- question: "Should we use REST or GraphQL for our API?"
- participants: [
    {"cli": "claude", "model": "opus"},
    {"cli": "codex", "model": "gpt-5-codex"}
  ]
- rounds: 3
```

**Expected**: Deliberation completes and transcript saved to `transcripts/` directory.

## Step 3: Verify Memory Stored (30 seconds)

Use the `query_decisions` MCP tool:

```
Use the mcp__ai-counsel__query_decisions tool with:
- query_text: "API design"
- threshold: 0.5  # NEW! Adjust sensitivity (0.0-1.0, default 0.6)
- limit: 5
```

**Threshold Guide**:
- **0.3-0.5**: Exploratory (more results, less precision)
- **0.5-0.7**: Balanced (recommended)
- **0.7-0.9**: High precision (fewer but more relevant)

**Expected**: Returns your stored decision with similarity score:

```json
{
  "type": "similar_decisions",
  "count": 1,
  "results": [
    {
      "id": "dec_abc123",
      "question": "Should we use REST or GraphQL for our API?",
      "consensus": "GraphQL recommended for flexible client queries...",
      "score": 0.92,
      "participants": ["claude/opus", "codex/gpt-5-codex"]
    }
  ]
}
```

## Step 4: Test Context Injection (2 minutes)

Run a related deliberation to see context injection in action:

```
Use the mcp__ai-counsel__deliberate tool with:
- question: "What authentication should we use for the API?"
- participants: [
    {"cli": "claude", "model": "opus"},
    {"cli": "codex", "model": "gpt-5-codex"}
  ]
- rounds: 3
```

Check the generated transcript in `transcripts/` - look for the **"Decision Graph Context"** section at the top. It should include:

```markdown
## Decision Graph Context (Retrieved from Memory)

Found 1 similar past decision(s):

### 1. Should we use REST or GraphQL for our API? (similarity: 0.78)
**Consensus**: GraphQL recommended for flexible client queries...
**Participants**: claude/opus, codex/gpt-5-codex
```

This proves the system remembered your first decision and injected it as context!

## Quick Troubleshooting

**No context injected in Step 4?**
- Check `mcp_server.log` for "Decision Graph Context" messages
- Wait 15-30 seconds after Step 2 (background similarity computation)
- Lower threshold in config: `similarity_threshold: 0.5`
- Verify database exists: check for `decision_graph.db` in AI Counsel directory

**query_decisions tool not available?**
- Confirm `decision_graph.enabled: true` in `config.yaml`
- Restart Claude Code to reload MCP server
- Check `mcp_server.log` for initialization errors

**Decision not stored after Step 2?**
- Check `mcp_server.log` for storage errors
- Verify write permissions on project directory
- Run `ls -la decision_graph.db` to confirm file created

**MCP tool not found?**
- Verify MCP server configured in `~/.claude/config/mcp.json`
- Check MCP server is running: look for "ai-counsel" in MCP tools list
- Restart Claude Code

## What's Next?

- **[Configuration Reference](configuration.md)**: Tune performance and thresholds
- **[Troubleshooting](troubleshooting.md)**: Debug common issues
- **[Deployment Guide](deployment.md)**: Production setup with monitoring
