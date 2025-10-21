# Convergence Detection

AI Counsel's convergence detection system automatically identifies when AI models reach consensus during deliberation, enabling intelligent early stopping to save time and API costs. The system combines semantic similarity analysis with structured voting to detect when continued debate would yield diminishing returns, while also recognizing stable disagreements that warrant stopping.

## How It Works

Convergence detection operates by comparing responses between consecutive rounds using two complementary mechanisms:

### Semantic Similarity Analysis

After each round (starting from round 2), the system compares the semantic meaning of each participant's response to their previous response. This comparison uses one of three similarity backends (described below) to compute a similarity score between 0.0 (completely different) and 1.0 (identical).

The system then classifies the debate status based on these similarity scores:

- **Converged** (≥ 85% similarity): Models are expressing nearly identical ideas across rounds, indicating consensus has been reached. The deliberation stops early.
- **Refining** (40-85% similarity): Models are still making meaningful adjustments to their positions, showing productive progress. The deliberation continues.
- **Diverging** (< 40% similarity): Models are expressing significantly different ideas, indicating fundamental disagreement or exploration of different angles.
- **Impasse**: When similarity scores remain stable across 2+ consecutive rounds without convergence, indicating a stable disagreement that's unlikely to resolve with more rounds.

### Structured Voting

In addition to semantic similarity, AI Counsel supports structured voting where each model explicitly casts a vote for a specific option. Votes include:

- **Option**: The choice being endorsed (e.g., "Option A", "Vector database")
- **Confidence**: A score from 0.0 to 1.0 indicating how strongly the model supports this option
- **Rationale**: Explanation for why this option was chosen
- **Continue Debate**: Boolean flag indicating whether the model thinks more discussion would be valuable

When votes are present, the system analyzes voting patterns to determine:

- **Unanimous Consensus** (3-0 vote): All models vote for the same option
- **Majority Decision** (2-1 vote): Clear winner with two models agreeing
- **Tie** (1-1-1 vote): No clear winner, each model votes for a different option

### Voting Takes Precedence

**Important**: When models cast structured votes, the convergence status reflects the voting outcome rather than semantic similarity scores. This means:

- A debate with **low semantic similarity** (e.g., 45% - "refining") but a **2-1 vote** will have status `"majority_decision"` instead of `"refining"`
- Voting outcomes provide a more explicit signal of consensus than semantic similarity alone
- The semantic similarity scores are still computed and reported in `per_participant_similarity`, but the overall `status` field reflects the voting result

This precedence rule ensures that when models explicitly agree on an option (even if they articulate their reasoning differently), the system recognizes the consensus.

### Vote Option Grouping

To handle cases where models vote for semantically identical options phrased differently (e.g., "Self-documenting code" vs "Prioritize self-documenting code"), the system automatically groups similar vote options:

- **Threshold**: 0.70 (70% similarity or higher)
- **Backend**: Uses the same similarity backend as convergence detection
- **Transparency**: Vote similarity scores are logged at INFO level in `mcp_server.log`
- **Example**: If Model A votes for "Use vector database" and Model B votes for "Vector database approach", these are merged into a single vote option

This grouping prevents artificial disagreement caused by phrasing variations and ensures accurate vote tallies.

## Similarity Backends

AI Counsel supports three similarity backends with automatic fallback, balancing accuracy with dependency requirements:

### 1. SentenceTransformer (Best)

**Accuracy**: Highest - uses deep learning embeddings for true semantic understanding

**How it works**: Converts text into high-dimensional vector embeddings using pre-trained transformer models, then computes cosine similarity between embeddings.

**Dependencies**:
- `sentence-transformers` package
- Pre-trained model download (~500MB)
- Requires Python 3.8+

**Performance**:
- First run: ~2-3 seconds per comparison (model loading)
- Subsequent runs: ~50-100ms per comparison (cached model)

**Use case**: Production deployments where accuracy is critical, especially for nuanced semantic differences.

**Installation**:
```bash
pip install sentence-transformers
```

### 2. TF-IDF (Good)

**Accuracy**: Good - statistical approach based on term frequency and importance

**How it works**: Converts text into sparse vectors based on term frequency weighted by inverse document frequency (how rare/important each term is), then computes cosine similarity.

**Dependencies**:
- `scikit-learn` package (~50MB)
- No model download required

**Performance**:
- ~10-20ms per comparison
- Low memory footprint

**Use case**: Environments with limited disk space or where transformer dependencies are problematic, but statistical similarity is acceptable.

**Installation**:
```bash
pip install scikit-learn
```

### 3. Jaccard (Fallback)

**Accuracy**: Basic - simple word overlap ratio

**How it works**: Treats each response as a set of words, then computes the ratio of shared words to total unique words across both responses.

**Dependencies**:
- None - uses only Python standard library

**Performance**:
- ~1-5ms per comparison
- Minimal memory usage

**Use case**: Zero-dependency environments, testing, or when advanced similarity isn't needed. Works out of the box without any optional packages.

**Installation**:
```bash
# No installation needed - always available
```

### Automatic Fallback

The system attempts to use backends in order of accuracy:

1. Try **SentenceTransformer** (if `sentence-transformers` installed)
2. Fall back to **TF-IDF** (if `scikit-learn` installed)
3. Fall back to **Jaccard** (always available)

This fallback is automatic and logged at startup:

```
INFO: Using SentenceTransformer backend for convergence detection
```

or

```
WARNING: sentence-transformers not found, falling back to TF-IDF
```

You can see which backend is active by checking the logs or the convergence info in results.

## Configuration

Convergence detection is configured in `config.yaml` under the `deliberation` section:

```yaml
deliberation:
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85
    divergence_threshold: 0.40
    min_rounds_before_check: 2
    consecutive_stable_rounds: 2

  # Model-controlled early stopping
  early_stopping:
    enabled: true
    threshold: 0.66  # 66% of models must want to stop
    respect_min_rounds: true  # Wait for min_rounds before stopping
```

### Configuration Parameters

#### `enabled` (boolean, default: `true`)

Enables or disables convergence detection entirely. When disabled, deliberations always run for the configured number of rounds without early stopping.

**Use case**: Disable when you want consistent round counts regardless of consensus (e.g., research, benchmarking).

#### `semantic_similarity_threshold` (float, default: `0.85`)

The minimum similarity score (0.0-1.0) required to classify the debate as "converged". Higher values require stronger agreement before stopping early.

**Examples**:
- `0.85` (default): Models must be 85%+ similar to trigger convergence
- `0.90`: Stricter - requires near-identical responses
- `0.75`: More lenient - accepts moderate consensus

**Trade-off**:
- Higher threshold → fewer false positives (stopping too early), but may miss legitimate consensus
- Lower threshold → more aggressive early stopping, but risk of stopping before thorough discussion

#### `divergence_threshold` (float, default: `0.40`)

The maximum similarity score (0.0-1.0) below which the debate is classified as "diverging". Lower values indicate stronger disagreement.

**Examples**:
- `0.40` (default): Below 40% similarity = diverging
- `0.30`: More tolerant of disagreement before flagging as diverging
- `0.50`: Flags disagreement earlier

**Use case**: Helps identify when models are exploring fundamentally different approaches rather than refining a shared direction.

#### `min_rounds_before_check` (integer, default: `2`)

The minimum number of rounds that must complete before convergence detection begins. Since convergence requires comparing consecutive rounds, this value must be ≥ 1 (you need at least 2 rounds total to compare round 2 to round 1).

**Examples**:
- `2` (default): Start checking after round 2 completes (compares rounds 1→2)
- `3`: Wait until round 3 completes before checking (compares rounds 2→3)
- `1`: Start checking immediately after round 1 completes

**Important**: For 2-round deliberations, use `min_rounds_before_check: 1` to enable convergence checking. If set to `2` or higher, convergence info won't appear because there aren't enough rounds to compare.

#### `consecutive_stable_rounds` (integer, default: `2`)

The number of consecutive rounds with stable (unchanging) similarity scores required to trigger an "impasse" status and stop early.

**Examples**:
- `2` (default): If similarity scores stay the same for 2 rounds → impasse
- `3`: Require 3 consecutive stable rounds before declaring impasse
- `1`: Declare impasse after just 1 round of no change (aggressive)

**Use case**: Prevents endless debate when models have reached stable disagreement and won't change positions.

### Model-Controlled Early Stopping

In addition to convergence detection, models can explicitly signal when they believe the debate should end:

#### `early_stopping.enabled` (boolean, default: `true`)

Enables model-controlled early stopping. When enabled, models can vote to end the debate by setting `continue_debate: false` in their vote.

**How it works**: After each round, the engine checks what percentage of models want to continue debating. If the percentage wanting to *stop* meets the threshold, the debate ends immediately.

#### `early_stopping.threshold` (float, default: `0.66`)

The minimum fraction (0.0-1.0) of models that must want to stop for early stopping to trigger.

**Examples**:
- `0.66` (default): 66% must want to stop (2 out of 3 models)
- `1.0`: Unanimous agreement required (all 3 models must want to stop)
- `0.5`: Simple majority (2 out of 3 models)

**Use case**: Adjust based on whether you want unanimous agreement or majority rule for stopping.

#### `early_stopping.respect_min_rounds` (boolean, default: `true`)

When `true`, early stopping won't trigger until the minimum number of rounds (from `defaults.rounds`) has completed, even if models want to stop earlier.

**Examples**:
- `true` (default): If `defaults.rounds: 2`, can't stop before round 2 completes
- `false`: Models can stop after round 1 if threshold met

**Use case**: Set to `false` when you want models to have full control, or `true` when you want to ensure minimum discussion happens.

### Example Scenarios

#### Scenario 1: Fast Consensus (2 Models Agree Immediately)

```yaml
deliberation:
  defaults:
    rounds: 2
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85
  early_stopping:
    enabled: true
    threshold: 0.66
```

**Round 1**: All 3 models respond
**Round 2**: 2 models vote for "Option A" with `continue_debate: false`, 1 votes for "Option B"
**Result**: Stops after round 2 with status `"majority_decision"`, saves 3 additional rounds

#### Scenario 2: Thorough Debate (Require All Rounds)

```yaml
deliberation:
  defaults:
    rounds: 5
  convergence_detection:
    enabled: false  # Don't stop early
  early_stopping:
    enabled: false  # Ignore model signals
```

**Result**: Always runs exactly 5 rounds, regardless of consensus or voting

#### Scenario 3: Conservative Early Stopping

```yaml
deliberation:
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.90  # Stricter threshold
    min_rounds_before_check: 3  # Require at least 3 rounds
  early_stopping:
    enabled: true
    threshold: 1.0  # Require unanimous vote to stop
    respect_min_rounds: true
```

**Result**: Only stops early if all models agree unanimously AND semantic similarity is ≥90% AND at least 3 rounds completed

## Example Result

When convergence detection is enabled, the deliberation result includes detailed convergence information:

```json
{
  "question": "Should we use a document database or vector database for similarity search?",
  "rounds": [
    { "round": 1, "responses": [...] },
    { "round": 2, "responses": [...] }
  ],
  "convergence_info": {
    "detected": true,
    "detection_round": 2,
    "final_similarity": 0.73,
    "status": "majority_decision",
    "per_participant_similarity": {
      "claude@cli": 0.73,
      "codex@cli": 0.85,
      "gemini@cli": 0.70
    }
  },
  "voting_result": {
    "final_tally": {
      "Vector database": 2,
      "Document database": 1
    },
    "consensus_reached": true,
    "winning_option": "Vector database",
    "votes_by_round": [
      {
        "round": 1,
        "votes": [
          {
            "participant": "claude@cli",
            "vote": {
              "option": "Vector database",
              "confidence": 0.85,
              "rationale": "Purpose-built for similarity search with HNSW indexing",
              "continue_debate": false
            }
          },
          {
            "participant": "codex@cli",
            "vote": {
              "option": "Vector database",
              "confidence": 0.90,
              "rationale": "Specialized vector operations and embedding storage",
              "continue_debate": false
            }
          },
          {
            "participant": "gemini@cli",
            "vote": {
              "option": "Document database",
              "confidence": 0.60,
              "rationale": "More flexible schema and easier integration",
              "continue_debate": true
            }
          }
        ]
      }
    ]
  },
  "summary": {
    "consensus": "Use a vector database for similarity search tasks",
    "agreements": [
      "Vector databases provide specialized indexing for similarity search",
      "Performance is critical for user-facing search"
    ],
    "disagreements": [
      "Trade-off between specialization (vector DB) vs flexibility (document DB)"
    ],
    "recommendation": "Adopt vector database with proper evaluation of specific use case requirements"
  }
}
```

### Key Fields Explained

#### `convergence_info.detected` (boolean)

Whether convergence (or impasse) was detected during the deliberation. `true` means early stopping occurred, `false` means all rounds completed without convergence.

#### `convergence_info.detection_round` (integer)

The round number when convergence was first detected. For example, if models converged after round 2, this would be `2`.

#### `convergence_info.final_similarity` (float)

The overall similarity score computed for the round when convergence was detected. This is typically an average of per-participant scores.

#### `convergence_info.status` (string)

The convergence classification at the time of detection:

- `"unanimous_consensus"`: All models voted for the same option (3-0)
- `"majority_decision"`: Clear winning option from voting (2-1)
- `"converged"`: Semantic similarity ≥ threshold (no voting, or voting didn't reach consensus)
- `"refining"`: Making progress but not converged (40-85% similarity)
- `"diverging"`: Significant disagreement (< 40% similarity)
- `"impasse"`: Stable disagreement over multiple rounds
- `"tie"`: No clear winner from voting (1-1-1)

**Note**: When voting is present, `status` reflects the voting outcome rather than semantic similarity.

#### `convergence_info.per_participant_similarity` (object)

Breakdown of similarity scores for each individual participant, showing how much each model's round 2 response resembled their round 1 response.

**Use case**: Identify which models converged quickly vs. which continued exploring different angles.

#### `voting_result.final_tally` (object)

The vote count for each option after all rounds. In the example, "Vector database" received 2 votes and "Document database" received 1 vote.

#### `voting_result.consensus_reached` (boolean)

Whether the voting produced a clear winner. `true` for unanimous or majority decisions, `false` for ties or no votes.

#### `voting_result.winning_option` (string)

The option that received the most votes. Only present when `consensus_reached: true`.

#### `voting_result.votes_by_round` (array)

Complete history of all votes cast in each round, including confidence scores, rationales, and `continue_debate` flags. This provides full transparency into how the consensus evolved.

## Best Practices

### When to Tune Thresholds

#### Increase `semantic_similarity_threshold` (e.g., 0.90+) when:
- Decisions are high-stakes and require very strong consensus
- Models tend to agree superficially but differ in details
- You want to ensure thorough exploration before stopping

#### Decrease `semantic_similarity_threshold` (e.g., 0.75-0.80) when:
- API costs are a concern and early stopping is desired
- Questions are straightforward with clear correct answers
- Models typically converge quickly on your domain

#### Adjust `divergence_threshold` when:
- You want to detect fundamental disagreements earlier (increase threshold)
- You're comfortable with diverse perspectives (decrease threshold)

### Recommended Values for Different Scenarios

#### Rapid Prototyping / Cost Optimization
```yaml
deliberation:
  defaults:
    rounds: 2  # Minimum rounds
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.75  # Lenient
    min_rounds_before_check: 1  # Check immediately
  early_stopping:
    enabled: true
    threshold: 0.66  # Majority rule
```

**Goal**: Stop as early as possible when reasonable consensus emerges

#### Balanced / General Purpose (Default)
```yaml
deliberation:
  defaults:
    rounds: 3
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85  # Moderate
    min_rounds_before_check: 2
  early_stopping:
    enabled: true
    threshold: 0.66
```

**Goal**: Balance between thoroughness and efficiency

#### Thorough Analysis / High-Stakes Decisions
```yaml
deliberation:
  defaults:
    rounds: 5
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.92  # Strict
    min_rounds_before_check: 3  # Require substantial debate
    consecutive_stable_rounds: 3
  early_stopping:
    enabled: true
    threshold: 1.0  # Unanimous agreement required
    respect_min_rounds: true
```

**Goal**: Ensure deep exploration and very high confidence before stopping

#### Research / Benchmarking
```yaml
deliberation:
  defaults:
    rounds: 5
  convergence_detection:
    enabled: false  # Don't stop early
  early_stopping:
    enabled: false  # Ignore model signals
```

**Goal**: Consistent round counts for fair comparison across experiments

### Trade-offs to Consider

#### Early Stopping vs. Thorough Debate

**Early stopping saves costs but may sacrifice depth**:

- **Pro**: Reduces API calls when models agree quickly (2 rounds vs 5 rounds = 60% cost savings)
- **Con**: May stop before exploring edge cases or minority perspectives

**Recommendation**: Enable early stopping for routine decisions, disable for complex or controversial questions.

#### Semantic Similarity vs. Voting

**Semantic similarity is objective but may miss implicit agreement**:

- **Pro**: Continuous metric (0.0-1.0) provides nuanced view of convergence
- **Con**: Models can agree on outcome but phrase reasoning differently, lowering similarity

**Voting is explicit but requires structured responses**:

- **Pro**: Models explicitly declare their position, removing ambiguity
- **Con**: Requires models to follow voting format (may fail if prompt not clear)

**Recommendation**: Use both - voting for explicit decisions, semantic similarity for open-ended discussions.

#### Backend Selection

**SentenceTransformer is most accurate but has dependencies**:

- **Pro**: Captures semantic meaning even when wording differs significantly
- **Con**: 500MB download, requires Python 3.8+, slower first run

**TF-IDF is balanced**:

- **Pro**: Good accuracy for most use cases, smaller footprint
- **Con**: Misses deep semantic relationships (e.g., synonyms, paraphrasing)

**Jaccard is always available but basic**:

- **Pro**: Zero dependencies, instant startup
- **Con**: Only measures word overlap, misses meaning

**Recommendation**: Install `sentence-transformers` for production, use TF-IDF for development, rely on Jaccard only as fallback.

### Integration with Decision Graph Memory

When [decision graph memory](decision-graph/README.md) is enabled, convergence detection becomes even more valuable:

- **Past decisions** are injected as context in round 1, potentially accelerating convergence
- **Similarity thresholds** should be tuned higher (0.88-0.92) when graph memory is active, since models have more context to agree on
- **Early stopping** becomes more reliable because models reference shared historical context

**Example**: A question about "database choice" with graph memory might converge in 2 rounds instead of 4, because models reference a similar past deliberation rather than starting from scratch.

See the [decision graph documentation](decision-graph/README.md) for details on enabling and configuring this optional enhancement.

## Monitoring and Debugging

### Checking Which Backend Is Active

Look for these log lines in `mcp_server.log` at startup:

```
INFO: Using SentenceTransformer backend for convergence detection
```

or

```
WARNING: sentence-transformers not found, falling back to TF-IDF
INFO: Using TF-IDF backend for convergence detection
```

or

```
WARNING: scikit-learn not found, falling back to Jaccard
INFO: Using Jaccard backend for convergence detection
```

### Inspecting Convergence Behavior

Enable detailed logging by checking `mcp_server.log` for convergence-related entries:

```
INFO: Round 2 similarity scores: claude@cli=0.85, codex@cli=0.90, gemini@cli=0.75
INFO: Average similarity: 0.833, threshold: 0.850, status: refining
```

### Troubleshooting Early Stopping Issues

**Problem**: Deliberations always run full rounds despite convergence

**Solutions**:
1. Check `convergence_detection.enabled: true` in config
2. Verify `min_rounds_before_check` is set appropriately (≤ total rounds - 1)
3. Check if similarity scores are below threshold in logs
4. Ensure voting is being parsed correctly (look for "VOTE:" in transcripts)

**Problem**: Deliberations stop too early (premature convergence)

**Solutions**:
1. Increase `semantic_similarity_threshold` (e.g., 0.85 → 0.90)
2. Increase `early_stopping.threshold` (e.g., 0.66 → 1.0 for unanimous agreement)
3. Enable `respect_min_rounds: true` to ensure minimum debate
4. Increase `min_rounds_before_check` to require more rounds before checking

**Problem**: Vote option grouping is too aggressive

**Solutions**:
1. Check vote similarity scores in `mcp_server.log` (logged at INFO level)
2. The grouping threshold is currently hardcoded at 0.70 (70% similarity)
3. If distinct options are being merged incorrectly, consider adjusting prompts to make vote options more semantically distinct

## Summary

AI Counsel's convergence detection provides intelligent deliberation management through:

1. **Dual detection mechanisms**: Semantic similarity + structured voting
2. **Flexible backends**: SentenceTransformer, TF-IDF, or Jaccard with automatic fallback
3. **Model-controlled stopping**: Participants can signal when further debate isn't needed
4. **Rich configuration**: Tune thresholds for your use case
5. **Full transparency**: Detailed convergence info in results and logs

By enabling convergence detection, you can reduce deliberation costs by 40-70% while maintaining high-quality consensus outcomes. The system ensures that debates continue when productive and stop when consensus is reached or stable disagreement emerges.

For questions or issues with convergence detection, check `mcp_server.log` for detailed diagnostic information, or open an issue on the AI Counsel GitHub repository.
