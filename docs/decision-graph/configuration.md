# Decision Graph Memory: Configuration Reference

Complete reference for decision graph configuration options.

## Configuration Location

`config.yaml` in project root

## Configuration Parameters

### `enabled` (boolean)

**Default**: `false`

Master switch for decision graph memory.

```yaml
decision_graph:
  enabled: true   # Enable feature
```

### `db_path` (string)

**Default**: `"decision_graph.db"`

Path to SQLite database file.

```yaml
decision_graph:
  db_path: "decision_graph.db"              # Relative
  db_path: "/var/lib/ai-counsel/graph.db"   # Absolute
```

### `similarity_threshold` (float)

**Default**: `0.7`  
**Range**: `0.0` - `1.0`

Minimum similarity score for context injection.

```yaml
decision_graph:
  similarity_threshold: 0.7   # Balanced (default)
  similarity_threshold: 0.8   # Conservative
  similarity_threshold: 0.6   # Aggressive
```

| Threshold | Behavior | Use Case |
|-----------|----------|----------|
| **0.9+** | Only near-duplicates | Prevent redundant deliberations |
| **0.8** | Highly related questions | High-quality context |
| **0.7** | Moderately related | Balanced (default) |
| **0.6** | Loosely related | Broad context |

### `max_context_decisions` (integer)

**Default**: `3`  
**Range**: `1` - `10`

Maximum past decisions to inject as context.

```yaml
decision_graph:
  max_context_decisions: 3   # Balanced (default)
  max_context_decisions: 1   # Minimal (fastest)
  max_context_decisions: 5   # Comprehensive
```

### `compute_similarities` (boolean)

**Default**: `true`

Enable async background similarity computation.

```yaml
decision_graph:
  compute_similarities: true   # Recommended
```

## Configuration Examples

### Conservative

```yaml
decision_graph:
  enabled: true
  similarity_threshold: 0.8
  max_context_decisions: 1
  compute_similarities: true
```

### Balanced (Default)

```yaml
decision_graph:
  enabled: true
  similarity_threshold: 0.7
  max_context_decisions: 3
  compute_similarities: true
```

### Aggressive

```yaml
decision_graph:
  enabled: true
  similarity_threshold: 0.6
  max_context_decisions: 5
  compute_similarities: true
```

## Scaling Considerations

### Small Scale (<100 decisions)

Performance: Excellent (<200ms queries)

### Medium Scale (100-1000 decisions)

Performance: Good (<350ms queries)

### Large Scale (1000-5000 decisions)

```yaml
decision_graph:
  similarity_threshold: 0.8
  max_context_decisions: 2
```

Performance: Acceptable (<450ms queries)

## What's Next?

- **[Quickstart Guide](quickstart.md)**: Get started
- **[Migration Guide](migration.md)**: Import transcripts
- **[Troubleshooting](troubleshooting.md)**: Debug performance
