# Changelog

All notable changes to AI Counsel are documented in this file.

## [Unreleased]

### Phase 1: Budget-Aware Context Injection (In Progress - Oct 22, 2025)

#### Added
- **Budget-Aware Configuration** (`models/config.py`)
  - `context_token_budget`: Maximum tokens for context injection (default: 1500)
  - `tier_boundaries`: Confidence score thresholds for tiering (strong: 0.75, moderate: 0.60)
  - `query_window`: Recent decisions to query (default: 1000)
  - Full backward compatibility with deprecated `similarity_threshold`

- **Tiered Context Formatter** (`decision_graph/retrieval.py`)
  - `format_context_tiered()`: Budget-aware context formatting with tier assignment
  - Confidence-based tiering: STRONG (≥0.75), MODERATE (0.60-0.74), BRIEF (<0.60)
  - Token budget tracking and enforcement
  - Noise floor filtering (0.40) to prevent garbage context

- **Adaptive k Selection** (`decision_graph/retrieval.py`)
  - `_compute_adaptive_k()`: Database size-aware candidate limiting
  - <100 decisions: k=5 (exploration)
  - 100-999 decisions: k=3 (balanced)
  - ≥1000 decisions: k=2 (precision)

- **Confidence Ranking** (`decision_graph/retrieval.py`)
  - Refactored `find_relevant_decisions()` to return scored results
  - Returns `List[Tuple[DecisionNode, float]]` instead of `List[DecisionNode]`
  - **Breaking Change**: Return type includes similarity scores

- **Integrated Context Injection** (`decision_graph/integration.py`)
  - Updated `get_context_for_deliberation()` for budget-aware injection
  - Accepts optional `config` parameter
  - Logs comprehensive metrics for Phase 1.5 calibration

- **Observability Hooks** (`decision_graph/integration.py`)
  - `_log_context_metrics()`: Structured logging of tier distribution, tokens, db size
  - `get_graph_metrics()`: Helper method for Phase 1.5 analysis
  - Parseable log format: `MEASUREMENT: question='...', tier_distribution=(strong:X, moderate:Y, brief:Z), tokens=U/B, db_size=D`

- **Graph Context Summary in MPC Responses** (`deliberation/engine.py`)
  - Enhanced `graph_context_summary` to recognize new tiered formatter headers
  - Shows tier breakdown: "Similar past deliberations found: N decision(s) (X strong, Y moderate, Z brief)"
  - Works with both old and new formatting

#### Changed
- `find_relevant_decisions()` return type changed (BREAKING)
  - Old: `List[DecisionNode]`
  - New: `List[Tuple[DecisionNode, float]]` (includes similarity scores)
- Deprecated `similarity_threshold` parameter (kept for backward compat, ignored)
- Deprecated `max_results` parameter (adaptive k used instead)

#### Fixed
- Graph context summary now properly reports injected decisions in MCP responses
- Fixed header detection in deliberation engine to work with new tiered formatter
- Fixed floating point precision error in similarity score clamping (ensure score ≤ 1.0)
  - Similarity detection backends can return scores slightly > 1.0 due to numerical precision
  - Now clamped to [0.0, 1.0] before storing in database to prevent validation errors

#### Tests
- Added 41 new tests covering all Phase 1 features
- 602 total tests passing (1 skipped)
- No regressions in existing functionality
- Full TDD implementation with RED→GREEN→REFACTOR cycle

### Phase 1 Validation (Oct 22, 2025)
- ✅ Real debate tested: TypeScript backend service
- ✅ STRONG tier (0.84 similarity) correctly identified
- ✅ Tier classification working in practice
- ✅ Models cite past decisions when injected
- ✅ Single-round convergence observed with context injection
- ✅ Next: Collect Phase 1.5 calibration data

## [0.1.0] - 2025-10-22

### Initial Release

#### Core Features
- True deliberative consensus between AI models
- Multi-round debates with convergence detection
- Structured voting with confidence levels
- Semantic vote grouping
- Model-controlled early stopping
- Full markdown transcripts with AI summaries

#### Adapters
- CLI: Claude, GPT-5 Codex, Droid, Gemini
- HTTP: Ollama, LM Studio, OpenRouter

#### Decision Graph Memory
- Persistent SQLite storage
- Semantic similarity matching
- Query interface for finding similar decisions
- Export to JSON, GraphML, DOT, Markdown

#### Infrastructure
- MCP Server implementation
- Comprehensive error handling
- Convergence detection (SentenceTransformer/TF-IDF/Jaccard)
- Background worker for async similarity computation
- Two-tier caching (query results + embeddings)

---

## Planned

### Phase 1.5: Empirical Calibration (Week 2)
- Collect measurement logs from 50+ deliberations
- Analyze tier distribution patterns
- Optimize tier boundaries based on real data
- Refine token budget estimates
- Measure convergence impact of different tiers

### Phase 2: Learning Layer (Future)
- Track which contexts lead to better convergence
- Predict optimal tier for future similar questions
- Hybrid similarity scoring (semantic + keyword)

---

## Notes for Developers

### Breaking Changes in Phase 1
- `find_relevant_decisions()` return type changed to include scores
- Old code relying on `List[DecisionNode]` will need updates
- Use `(decision, score)` tuple unpacking or extract decisions with `[d for d, s in results]`

### Migration Path
1. Update callers of `find_relevant_decisions()` to handle tuples
2. Test with `pytest tests/unit/ -v`
3. Check logs for `MEASUREMENT:` entries
4. Run Phase 1.5 calibration when ready

### Testing Phase 1.5
Run diverse debates and monitor:
```bash
tail -f mcp_server.log | grep "MEASUREMENT:"
```

This will show tier distribution and token usage for calibration analysis.
