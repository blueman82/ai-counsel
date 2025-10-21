# Decision Graph Memory: Migration Guide

Migrate existing transcripts into the decision graph for organizational memory.

## ⚠️ IMPORTANT: Backup First

**MANDATORY STEP**: Backup your transcripts before migration.

```bash
tar -czf transcripts_backup_$(date +%Y%m%d).tar.gz transcripts/
cp ai_counsel.db ai_counsel.db.backup
```

## Migration Overview

### What Gets Migrated

- ✅ Question (from filename and content)
- ✅ Timestamp
- ✅ Consensus
- ✅ Participants
- ✅ Votes and confidence

### What Doesn't Get Migrated

- ❌ Full round-by-round responses
- ❌ Intermediate rounds

## Step-by-Step Migration

### Phase 1: Dry-Run

```bash
python scripts/migrate_transcripts.py --dry-run
```

Review what will be migrated.

### Phase 2: Execute Migration

```bash
python scripts/migrate_transcripts.py
```

Confirm when prompted.

### Phase 3: Verification

```bash
python scripts/verify_migration.py
```

### Phase 4: Test Queries

```bash
ai-counsel graph similar --query "API design" --limit 5
```

## Rollback Instructions

### If Migration Fails

```bash
# Stop AI Counsel
pkill -f ai-counsel

# Restore database
rm decision_graph.db
sqlite3 decision_graph.db < ai_counsel_backup_*.sql
```

## Common Issues

### Issue: "Permission denied" error

```bash
chmod 644 decision_graph.db
```

### Issue: "Database is locked"

```bash
# Stop other processes
pkill -f "python server.py"
sleep 5

# Retry migration
python scripts/migrate_transcripts.py
```

## Migration Checklist

- [ ] Backups created and verified
- [ ] Disk space confirmed
- [ ] `decision_graph.enabled: true`
- [ ] Dry-run reviewed
- [ ] Migration completed
- [ ] Verification passed
- [ ] Test queries work

## What's Next?

- **[Configuration Reference](configuration.md)**: Tune after migration
- **[Deployment Guide](deployment.md)**: Set up backups
- **[Troubleshooting](troubleshooting.md)**: Debug issues
