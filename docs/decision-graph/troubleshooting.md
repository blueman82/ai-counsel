# Decision Graph Memory: Troubleshooting Guide

Debugging guide for common issues and problems.

## Quick Diagnostic Checklist

```bash
# 1. Check if enabled
grep decision_graph config.yaml

# 2. Check database exists
ls -lh decision_graph.db

# 3. Check stored decisions
sqlite3 decision_graph.db "SELECT COUNT(*) FROM decision_nodes;"

# 4. Check recent decision
sqlite3 decision_graph.db "SELECT question FROM decision_nodes ORDER BY timestamp DESC LIMIT 1;"

# 5. Check logs
tail -50 mcp_server.log | grep error
```

## Common Issues

### Issue 1: No Context Injected

**Symptom**: New deliberations don't show "Decision Graph Context"

**Diagnosis**:

1. **Check enabled**:
   ```bash
   grep "enabled:" config.yaml | grep -A1 decision_graph
   ```
   Expected: `true`

2. **Check similarity threshold**:
   ```bash
   ai-counsel graph similar --query "your question" --limit 5
   ```
   If no results, threshold too high.

3. **Check database has decisions**:
   ```bash
   sqlite3 decision_graph.db "SELECT COUNT(*) FROM decision_nodes;"
   ```
   Expected: >0

**Fix**: Lower threshold temporarily
```yaml
decision_graph:
  similarity_threshold: 0.5
```

---

### Issue 2: Slow Deliberation Start

**Symptom**: Deliberation takes >1 second to start

**Diagnosis**:
```bash
# Enable debug logging
export LOG_LEVEL=debug

# Run deliberation and check timing
grep "Decision graph context retrieved" mcp_server.log
```

**Targets**:
- Cache hit: <2ms ✅
- Cache miss: <450ms ✅

**Fix**:
- Reduce `max_context_decisions` to 1-2
- Increase `similarity_threshold` to 0.8
- Install faster backend: `pip install sentence-transformers`

---

### Issue 3: "Database is locked"

**Symptom**:
```
sqlite3.OperationalError: database is locked
```

**Fix**:
```bash
# Stop other processes
pkill -f "python server.py"

# Enable WAL mode (permanent fix)
sqlite3 decision_graph.db "PRAGMA journal_mode=WAL;"
```

---

### Issue 4: Missing Decisions

**Symptom**: Recent deliberation not in database

**Check logs**:
```bash
grep "Stored decision\|store_deliberation\|Error" mcp_server.log | tail -20
```

**Possible fixes**:
- Check write permissions: `chmod 644 decision_graph.db`
- Verify feature enabled: `decision_graph.enabled: true`
- Check disk space: `df -h .`

---

### Issue 5: Incorrect Similarity Scores

**Symptom**: Obviously similar questions have low scores

**Check backend**:
```bash
python -c "from decision_graph.similarity import QuestionSimilarityDetector; \
           detector = QuestionSimilarityDetector(); \
           print(f'Backend: {detector.backend_name}')"
```

**If `Jaccard`**: Install better backend
```bash
pip install sentence-transformers
```

---

## Performance Debugging

### High Query Latency

**Targets**:
- Cache hit: <2ms
- Cache miss: <450ms

**If slower**:

1. Check cache hit rate:
   ```python
   from decision_graph.retrieval import DecisionRetriever
   from decision_graph.storage import DecisionGraphStorage
   storage = DecisionGraphStorage('decision_graph.db')
   retriever = DecisionRetriever(storage)
   stats = retriever.get_cache_stats()
   print(f'Hit rate: {stats["combined_hit_rate"]:.1%}')
   ```

2. Optimize if needed:
   - Lower threshold: `similarity_threshold: 0.8`
   - Reduce results: `max_context_decisions: 1`
   - Better backend: `pip install sentence-transformers`

---

### Low Cache Hit Rate

**Target**: >60% after warmup

**If <60%**:

Likely cause: Questions too diverse (expected for low-volume)

Only fix if deliberation start latency >450ms.

---

## Database Issues

### Corrupted Database

**Check**:
```bash
sqlite3 decision_graph.db "PRAGMA integrity_check;"
```

**If not `ok`**: Database corrupted

**Recover**:
```bash
# Restore from backup
cp decision_graph.db.backup decision_graph.db

# Verify
sqlite3 decision_graph.db "PRAGMA integrity_check;"
```

---

### Database Too Large

**Check size**:
```bash
ls -lh decision_graph.db
sqlite3 decision_graph.db "SELECT COUNT(*) FROM decision_nodes;"
```

**Fix**:

1. VACUUM to reclaim space:
   ```bash
   sqlite3 decision_graph.db "VACUUM;"
   ```

2. Archive old decisions (>5000):
   ```bash
   # Caution: deletes data
   sqlite3 decision_graph.db "DELETE FROM decision_nodes WHERE timestamp < date('now', '-180 days');"
   ```

---

## Graph Inspection

### Inspect Decisions

```bash
# View all decisions
sqlite3 decision_graph.db "SELECT question, timestamp FROM decision_nodes ORDER BY timestamp DESC LIMIT 10;"

# View specific decision
sqlite3 decision_graph.db "SELECT * FROM decision_nodes WHERE id='<id>';"

# View similarities
sqlite3 decision_graph.db "SELECT target_id, similarity_score FROM decision_similarities WHERE source_id='<id>' ORDER BY similarity_score DESC LIMIT 10;"
```

---

## Logging and Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=debug
ai-counsel deliberate --question "test" --participants "opus@claude" --rounds 1

tail -100 mcp_server.log | grep decision_graph
```

**Key messages**:
- `Initialized DecisionGraphIntegration`: Feature enabled
- `Decision graph context retrieved in XXX ms`: Query timing
- `Stored decision <id>`: Successfully stored
- `Cache hit: true/false`: Cache status
- `Error storing deliberation`: Storage failure

---

## FAQ

### Q: Why isn't my second deliberation showing context?

**A**: Most common causes:
1. Similarity threshold too high (lower to 0.5-0.6)
2. Background worker still processing (<20 seconds)
3. Questions genuinely dissimilar

**Debug**: `ai-counsel graph similar --query "your question"`

---

### Q: Can I disable for specific deliberations?

**A**: Yes:
```bash
AI_COUNSEL_GRAPH_DISABLED=1 ai-counsel deliberate --question "..."
```

---

### Q: How do I delete a decision?

**A**: Direct SQL (use caution):
```bash
sqlite3 decision_graph.db "DELETE FROM decision_nodes WHERE id='<id>';"
```

---

### Q: Can I reset the entire graph?

**A**: Clear all data:
```bash
sqlite3 decision_graph.db "DELETE FROM decision_similarities; DELETE FROM participant_stances; DELETE FROM decision_nodes; VACUUM;"
```

---

## Troubleshooting Checklist

- [ ] Feature enabled in config
- [ ] Database exists and readable
- [ ] Write permissions correct
- [ ] 15+ seconds elapsed since last deliberation
- [ ] Similarity threshold appropriate
- [ ] Better backend installed
- [ ] Logs reviewed for errors
- [ ] Cache hit rate checked
- [ ] Database integrity verified
- [ ] Queries return expected results

---

**Still stuck?** Enable debug logging and review full `mcp_server.log`.
