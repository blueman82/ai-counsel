# Decision Graph Memory: Deployment Guide

Production deployment strategies and backup procedures.

## Production Configuration

### Recommended Settings

```yaml
decision_graph:
  enabled: true
  db_path: "/var/lib/ai-counsel/decision_graph.db"
  similarity_threshold: 0.7
  max_context_decisions: 3
  compute_similarities: true
```

### File Permissions

```bash
sudo mkdir -p /var/lib/ai-counsel
sudo chown ai-counsel:ai-counsel /var/lib/ai-counsel
sudo chmod 755 /var/lib/ai-counsel
```

## Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  ai-counsel:
    build: .
    image: ai-counsel:latest
    restart: unless-stopped
    
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml:ro
    
    environment:
      - DECISION_GRAPH_DB_PATH=/app/data/decision_graph.db
      - LOG_LEVEL=info
    
    healthcheck:
      test: ["CMD", "sqlite3", "/app/data/decision_graph.db", "SELECT 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Deployment

```bash
docker-compose build
docker-compose up -d
```

## Backup Strategies

### Daily Automated Backup

```bash
#!/bin/bash
BACKUP_DIR=/var/backups/ai-counsel
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH=/var/lib/ai-counsel/decision_graph.db

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/decision_graph_$DATE.db'"

# Keep only last 30 days
find "$BACKUP_DIR" -mtime +30 -delete
```

**Cron schedule**:
```cron
0 2 * * * /usr/local/bin/backup-ai-counsel.sh
```

## Database Maintenance

### Monthly VACUUM

```bash
sqlite3 /var/lib/ai-counsel/decision_graph.db "VACUUM;"
```

Reclaim unused space, defragment database.

### Integrity Checks

```bash
sqlite3 decision_graph.db "PRAGMA integrity_check;"
```

Expected: `ok`

## Performance Monitoring

### Key Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Deliberation start latency (p95) | <450ms | Warn if >600ms |
| Cache hit rate | >60% | Warn if <50% |
| Database size | <100MB (1000 decisions) | Warn at 500MB |

### Monitor Script

```bash
#!/bin/bash
DB_PATH=/var/lib/ai-counsel/decision_graph.db
db_size=$(du -h "$DB_PATH" | cut -f1)
decision_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM decision_nodes;")

echo "$(date +%Y%m%d_%H%M%S),size=$db_size,decisions=$decision_count" >> /var/log/ai-counsel-metrics.log
```

## Disaster Recovery

### Corrupted Database

```bash
# Restore from backup
cp /var/backups/ai-counsel/decision_graph_latest.db \
   /var/lib/ai-counsel/decision_graph.db

# Verify
sqlite3 /var/lib/ai-counsel/decision_graph.db "PRAGMA integrity_check;"
```

## What's Next?

- **[Configuration Reference](configuration.md)**: Tune settings
- **[Troubleshooting](troubleshooting.md)**: Debug issues
- **[Introduction](intro.md)**: Understand architecture
