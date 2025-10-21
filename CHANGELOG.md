# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-10-21

### Added - Decision Graph Memory System

**Major Feature: Persistent Learning from Past Deliberations**

The system now learns from every deliberation and automatically injects relevant historical context into new debates, enabling models to converge faster with consistent reasoning.

#### Core Capabilities:
- 🧠 **Decision Graph Storage**: Persistent SQLite database storing all deliberations with questions, consensus, participants, and stances
- 🔍 **Similarity Detection**: Automatic semantic similarity matching to find related past decisions (3+ backends with fallback)
- 💉 **Context Injection**: Related decisions automatically formatted and prepended to Round 1 prompts
- 🔗 **Relationship Tracking**: Edges and similarity scores between related decisions enable knowledge graph traversal
- ⚡ **Non-Blocking**: Async background workers compute similarities without blocking deliberations
- 💾 **Two-Tier Caching**: L1 query results (LRU) + L2 embeddings for 60%+ cache hit rates
- 📊 **Query Engine**: Unified Python API for searching similar decisions, finding contradictions, tracing evolution
- 📤 **Export Formats**: JSON, GraphML, DOT, Markdown exports for analysis and visualization
- 🏥 **Health Monitoring**: Automatic stats collection, growth tracking, threshold warnings

#### Performance Characteristics:
- Store deliberation: <100ms (async background similarity computation)
- Query cache hit: <2μs (instant LRU lookup)
- Query cache miss: <100ms (compute vs 50-100 recent decisions)
- Memory per decision: ~5KB (excludes embeddings)
- Background worker throughput: 10+ jobs/sec

#### Documentation:
- **Quick Start**: `/docs/decision-graph/quickstart.md` - Get started in 5 minutes
- **Configuration**: `/docs/decision-graph/configuration.md` - Tune similarity thresholds and context injection
- **Production Guide**: `/docs/decision-graph/deployment.md` - Best practices and scaling considerations
- **Troubleshooting**: `/docs/decision-graph/troubleshooting.md` - Common issues and solutions
- **API Reference**: See `decision_graph/query_engine.py` for full Python API
- **Integration**: Fully integrated with deliberation engine (enabled by default in config)

#### Configuration:
```yaml
decision_graph:
  enabled: true                    # Opt-in feature toggle
  db_path: "decision_graph.db"     # SQLite database location
  similarity_threshold: 0.7        # Min similarity (0.0-1.0) for context injection
  max_context_decisions: 3         # Max past decisions to inject as context
  compute_similarities: true       # Enable async similarity computation
```

#### Testing:
- 156 unit tests (schema, storage, retrieval, caching)
- 155 integration tests (persistence, workers, health monitoring)
- 100% coverage of core functionality
- Performance benchmarks included

#### Breaking Changes:
- None - Feature is opt-in and backward compatible
- Existing deliberations continue to work unchanged
- No data migration needed for upgrades

#### Migration Notes:
- Existing installations: Feature is enabled by default (set `decision_graph.enabled: false` to disable)
- Database: SQLite file created automatically on first deliberation
- Transcripts: Existing transcripts unaffected
- Config: No changes needed (sensible defaults provided)

### Changed
- Enhanced deliberation engine with optional graph integration
- Improved config schema to support new feature flags

### Fixed
- Minor formatting in HTTP adapter error messages

## [1.2.0] - 2025-09-15

### Added
- Phase 5: Performance optimizations with pruning/archival policies
- Structured voting with confidence levels and continue_debate flags
- Model-controlled early stopping for adaptive round counts
- Vote aggregation and consensus tracking

### Changed
- Refactored convergence detection for voting-aware status
- Improved transcript generation with voting sections

### Fixed
- Edge cases in convergence detection
- Database constraint validation

## [1.1.0] - 2025-08-10

### Added - Local Model Support

**Major Feature: Zero-Cost Inference with Self-Hosted Models**

This release adds HTTP adapter support, enabling AI Counsel to deliberate using locally-hosted open-source models alongside cloud APIs. Run models on your own hardware with **zero API costs**, **no rate limits**, and **complete data privacy**.

#### Local Model Adapters:
- 🏠 **Ollama**: Fast local inference runtime with one-command model downloads
- 💻 **LM Studio**: Desktop GUI for model management with OpenAI-compatible API
- ⚡ **llamacpp**: Ultra-lightweight CLI inference engine for maximum performance

#### Key Benefits:
- **Zero Cost**: Run unlimited deliberations without API charges (vs $0.05-$5/request for cloud models)
- **No Rate Limits**: Local models never hit quota limits or throttling
- **Privacy & Compliance**: Sensitive data never leaves your infrastructure
- **Offline Capability**: Deliberations work without internet connectivity
- **Mixed Deployments**: Combine local models (Llama, Mistral) with cloud APIs (Claude, GPT) in same deliberation

#### Example Configuration:
```yaml
adapters:
  ollama:
    type: http
    base_url: "http://localhost:11434"
    timeout: 120
    max_retries: 3
    # Valid models: llama2, mistral, codellama, qwen
    # Run 'ollama list' to see available models

  lmstudio:
    type: http
    base_url: "http://localhost:1234"
    timeout: 120
    max_retries: 3
    # Valid models: any model loaded in LM Studio
```

#### Example Deliberation (Mixed Local + Cloud):
```javascript
mcp__ai-counsel__deliberate({
  question: "Should we refactor this module?",
  participants: [
    {cli: "ollama", model: "llama2"},           // Local via Ollama
    {cli: "lmstudio", model: "mistral-7b"},     // Local via LM Studio
    {cli: "claude", model: "sonnet"}            // Cloud via Claude
  ],
  mode: "conference"
})
```

#### Additional Features:
- **OpenRouter Adapter**: Access 100+ models through single API (cloud fallback for local infrastructure)
- **Configuration Migration**: Automated script converts legacy `cli_tools` format to new `adapters` schema
- **Environment Variable Substitution**: Secure API key storage via `${VAR_NAME}` pattern in configs
- **Per-Adapter Timeouts**: Independent timeout configuration for each adapter type
- **Retry Logic**: Exponential backoff on network errors, fail-fast on client errors

#### Documentation:
- **HTTP Adapters Guide**: `/docs/troubleshooting/http-adapters.md`
- **Migration Guide**: `/docs/migration/cli_tools_to_adapters.md`
- **Retrospective**: `/docs/HTTP_ADAPTER_RETROSPECTIVE.md` - Design decisions and lessons learned

#### Performance & Reliability:
- Async HTTP client with connection pooling
- Graceful degradation: adapter failures don't halt deliberations
- Tested with 100+ concurrent requests across all adapter types
- Zero breaking changes from v1.0.0 (fully backward compatible)

### Changed
- Adapter factory pattern for extensibility
- Config schema with type discrimination (CLI vs HTTP)
- Enhanced adapter base classes for code reuse

### Fixed
- Subprocess timeout handling edge cases
- Hook interference with Claude CLI in deliberation contexts

## [1.0.0] - 2025-07-01

### Added
- Initial release: True deliberative consensus MCP server
- Multi-round debates between AI models
- CLI adapter support (Claude, Codex, Droid, Gemini)
- Convergence detection with semantic similarity
- Markdown transcript generation
- Full audit trail with timestamps
- Graceful adapter failure handling
- Production-ready error handling and logging

### Features
- Conference mode (multi-round debate)
- Quick mode (single-round opinions)
- Mixed adapter support in single deliberation
- Voting and consensus tracking
- Automatic SSL/TLS support
- Configurable convergence thresholds

---

## Upgrade Guide

### 1.2.0 → 1.3.0
No breaking changes. Decision Graph Memory is **opt-in** and enabled by default.

**Optional**: Disable if you prefer old behavior:
```yaml
decision_graph:
  enabled: false
```

### 1.1.0 → 1.2.0
No breaking changes. New voting features are transparent to existing code.

### 1.0.0 → 1.1.0
**Breaking Change**: Migrate config from `cli_tools` to `adapters`:
```bash
python scripts/migrate_config.py config.yaml
```

---

## Performance Metrics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Store decision | <100ms | Async background similarity |
| Query cache (hit) | <2μs | LRU lookup |
| Query cache (miss) | <100ms | Compute similarity vs 50-100 decisions |
| Context injection | <50ms | Format 3 past decisions |
| Memory per decision | ~5KB | Excludes embeddings |

---

## Known Issues

- Cold start on first deliberation (~500ms) due to similarity computation
- SQLite limitations at 100k+ decisions (consider archival policy)
- Embedding backend selection is automatic (may vary by installed packages)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.
