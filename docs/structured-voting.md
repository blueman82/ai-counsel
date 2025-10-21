# Structured Voting & Consensus

AI Counsel's structured voting system enables models to make explicit, traceable decisions with confidence levels and evidence-based reasoning. Unlike pure semantic similarity, structured voting provides clear, interpretable outcomes where models formally cast votes and reach consensus through democratic processes.

## Overview

Structured voting embeds formal vote data as JSON markers within model responses, allowing AI Counsel to:

- **Track explicit positions**: Models state their choice, confidence, and reasoning
- **Measure certainty**: Confidence scores (0.0-1.0) reveal how sure each model is
- **Enable early stopping**: Models signal when they're satisfied with the outcome
- **Override semantic similarity**: Explicit votes take precedence over text similarity analysis

**Format**: Models include `VOTE: {json}` markers in their responses during deliberation.

**Purpose**: Provide structured decision-making that complements semantic similarity analysis, enabling clear consensus detection even when models use different wording to express the same position.

**Integration with Convergence Detection**: When models cast votes, the voting outcome (unanimous consensus, majority decision, tie) overrides semantic similarity status. This ensures explicit choices are prioritized over text pattern matching. See [Convergence Detection documentation](convergence-detection.md) for details on the similarity system.

## Vote Structure

Each vote is a JSON object embedded in the model's response with four fields:

```json
{
  "option": "Self-documenting code with comprehensive unit tests",
  "confidence": 0.85,
  "rationale": "Reduces long-term maintenance costs and onboarding time for new developers. Tests ensure refactoring safety.",
  "continue_debate": false
}
```

### Field Descriptions

**`option` (string, required)**
- The model's chosen position or decision
- Should be clear and specific (avoid vague terms like "Option 1")
- Examples:
  - Good: "Event sourcing for audit trail"
  - Good: "Microservices architecture"
  - Poor: "Option A"
  - Poor: "Yes"

**`confidence` (float, required, range: 0.0-1.0)**
- Quantifies the model's certainty in this choice
- Scale interpretation:
  - `0.9-1.0`: Very confident, strong evidence
  - `0.7-0.89`: Confident, good evidence
  - `0.5-0.69`: Moderate confidence, some uncertainty
  - `0.0-0.49`: Low confidence, significant doubt
- Used to weight decisions and identify areas needing more debate

**`rationale` (string, required)**
- Evidence-based explanation for the vote
- Should reference specific considerations, trade-offs, or requirements
- Typically 1-3 sentences
- Example: "TypeScript provides compile-time type safety which catches 40% of production bugs during development. The migration cost is offset by reduced debugging time."

**`continue_debate` (boolean, optional, default: true)**
- Signals whether the model wants more rounds of deliberation
- `true`: "I need more discussion to reach a confident decision"
- `false`: "I'm satisfied with current information and ready to conclude"
- Powers model-controlled early stopping (see Configuration section)

## Consensus Types

AI Counsel recognizes three primary voting outcomes based on vote distribution:

### Unanimous Consensus

**Pattern**: All models vote for the same option (3-0 in a 3-model deliberation)

**Status**: `unanimous_consensus`

**Example**:
```json
{
  "voting_result": {
    "final_tally": {
      "Event sourcing for audit trail": 3
    },
    "consensus_reached": true,
    "winning_option": "Event sourcing for audit trail"
  },
  "convergence_info": {
    "status": "unanimous_consensus"
  }
}
```

**Interpretation**: Strongest form of consensus. All models independently arrived at the same conclusion, often indicating a clearly optimal choice.

### Majority Decision

**Pattern**: One option receives more votes than others (2-1 in a 3-model deliberation)

**Status**: `majority_decision`

**Example**:
```json
{
  "voting_result": {
    "final_tally": {
      "Microservices architecture": 2,
      "Monolith architecture": 1
    },
    "consensus_reached": true,
    "winning_option": "Microservices architecture"
  },
  "convergence_info": {
    "status": "majority_decision"
  }
}
```

**Interpretation**: Clear winner but with dissent. The minority opinion's rationale should be reviewed to understand trade-offs or edge cases.

### Tie

**Pattern**: Multiple options receive equal vote counts (1-1-1 in a 3-model deliberation)

**Status**: `tie`

**Example**:
```json
{
  "voting_result": {
    "final_tally": {
      "Option A": 1,
      "Option B": 1,
      "Option C": 1
    },
    "consensus_reached": false,
    "winning_option": null
  },
  "convergence_info": {
    "status": "tie"
  }
}
```

**Interpretation**: No clear consensus. May indicate the question needs refinement, more context, or additional deliberation rounds.

## Vote Option Grouping

Vote option grouping automatically merges semantically similar options using the same similarity backend as convergence detection. This prevents vote fragmentation when models express the same choice with different wording.

### How It Works

**Threshold**: 0.70 (70% similarity or higher merges options)

**Backend**: Uses convergence detection backend (SentenceTransformer → TF-IDF → Jaccard fallback)

**Process**:
1. Collect all unique vote options from all rounds
2. Compute pairwise similarity scores
3. Group options meeting the 0.70 threshold
4. Merge vote counts for grouped options
5. Use first option in group as canonical name

### Example Grouping

**Before grouping** (raw votes):
```json
{
  "Self-documenting code": 1,
  "Prioritize self-documenting code": 1,
  "Focus on comprehensive unit tests": 1
}
```

**Similarity computation**:
```
"Self-documenting code" vs "Prioritize self-documenting code": 0.85 (✓ grouped)
"Self-documenting code" vs "Focus on comprehensive unit tests": 0.42 (✗ not grouped)
```

**After grouping** (merged tally):
```json
{
  "Self-documenting code": 2,
  "Focus on comprehensive unit tests": 1
}
```

**Result**: Changes tie (1-1-1) to majority decision (2-1)

### Transparency

Vote similarity scores are logged at `INFO` level in `mcp_server.log`:

```
INFO: Vote similarity: 'Self-documenting code' vs 'Prioritize self-documenting code': 0.850 (threshold: 0.700)
INFO:   ✓ Grouping 'Prioritize self-documenting code' with 'Self-documenting code'
INFO: Vote option grouping complete: 3 options -> 2 groups. Grouped tally: {'Self-documenting code': 2, 'Focus on comprehensive unit tests': 1}
```

### When Grouping Doesn't Occur

- **Below threshold**: Options with <70% similarity remain separate
- **No similarity backend**: Falls back to exact string matching (no grouping)
- **Single option**: No computation needed if all votes identical
- **Backend failure**: Gracefully falls back to raw tally on errors

### Configuration

Grouping uses the same convergence detection backend configured in `config.yaml`:

```yaml
deliberation:
  convergence_detection:
    enabled: true  # Enables both convergence detection AND vote grouping
```

The 0.70 threshold is fixed and optimized for vote option matching. Convergence detection uses a higher threshold (0.85) for semantic similarity.

## Configuration

Vote-related settings in `config.yaml`:

```yaml
deliberation:
  # Convergence detection (also powers vote grouping)
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85  # Not used for vote grouping (fixed at 0.70)

  # Model-controlled early stopping via continue_debate flag
  early_stopping:
    enabled: true
    threshold: 0.66                    # Stop if >=66% of models set continue_debate: false
    respect_min_rounds: true           # Don't stop before defaults.rounds
```

### Early Stopping Parameters

**`enabled` (boolean, default: true)**
- Allows models to control when deliberation ends
- When disabled, always runs configured number of rounds

**`threshold` (float, default: 0.66)**
- Percentage of models that must want to stop
- 0.66 = 66% = 2 out of 3 models in typical setup
- Higher values (0.8-1.0) require broader agreement to stop

**`respect_min_rounds` (boolean, default: true)**
- Prevents stopping before `defaults.rounds` is reached
- Ensures minimum deliberation depth
- Example: If `rounds: 3` and all models vote `continue_debate: false` in Round 1, deliberation continues through Round 3

### Example Scenarios

**Scenario 1: Unanimous early stop**
- Config: `rounds: 5`, `threshold: 0.66`, `respect_min_rounds: false`
- Round 2: All 3 models vote `continue_debate: false` (100% ≥ 66%)
- Result: Stops after Round 2 (saves 3 rounds of API costs)

**Scenario 2: Respect minimum rounds**
- Config: `rounds: 3`, `threshold: 0.66`, `respect_min_rounds: true`
- Round 1: All 3 models vote `continue_debate: false`
- Result: Continues through Round 3 despite unanimous desire to stop

**Scenario 3: Partial agreement**
- Config: `rounds: 5`, `threshold: 0.66`
- Round 3: 2 of 3 models vote `continue_debate: false` (66% = threshold)
- Result: Stops after Round 3

**Scenario 4: Threshold not met**
- Config: `rounds: 5`, `threshold: 0.66`
- Round 2: 1 of 3 models votes `continue_debate: false` (33% < 66%)
- Result: Continues to next round

## Integration with Convergence Detection

Voting and semantic similarity work together to provide robust consensus detection:

### Precedence Rules

1. **Voting outcome takes priority**: When models cast votes, convergence status reflects voting results
2. **Semantic similarity as fallback**: If no votes found, uses text similarity analysis
3. **Combined reporting**: Both metrics included in results for transparency

### Example: Voting Overrides Similarity

**Scenario**: Semantic similarity shows 60% match (status would be "refining"), but voting shows 2-1 majority.

**Convergence info**:
```json
{
  "convergence_info": {
    "detected": true,
    "detection_round": 2,
    "final_similarity": 0.60,
    "status": "majority_decision",  // Voting outcome, not "refining"
    "per_participant_similarity": {
      "claude@cli": 0.60,
      "codex@cli": 0.70,
      "gemini@cli": 0.55
    }
  },
  "voting_result": {
    "final_tally": {"Option A": 2, "Option B": 1},
    "consensus_reached": true,
    "winning_option": "Option A"
  }
}
```

**Interpretation**: Despite moderate semantic similarity (60%), the explicit votes show clear majority consensus (2-1), so status is `majority_decision` instead of `refining`.

### Why Voting Takes Precedence

**Explicit vs Implicit**: Votes are formal decisions; semantic similarity is pattern matching.

**Reliability**: Models can use different wording to express the same choice (handled by vote grouping), but semantic similarity might not detect this.

**Interpretability**: "2 models voted for A, 1 voted for B" is clearer than "60% similar responses."

**User trust**: Formal votes feel more authoritative than algorithmic similarity scores.

## Example Deliberation

Let's walk through a real 2-round deliberation with 3 models: Claude, Codex, and Gemini.

### Setup

**Question**: "Should we add comprehensive logging to production systems?"

**Participants**:
- Claude (Anthropic Sonnet 4.5)
- Codex (OpenAI GPT-5)
- Gemini (Google Gemini 2.5 Pro)

**Configuration**: `rounds: 2`, `mode: conference`, `early_stopping.threshold: 0.66`

### Round 1: Initial Positions

**Claude's response**:
```
Production logging is essential for debugging and monitoring. I recommend structured
logging with configurable levels (DEBUG, INFO, WARN, ERROR) and a centralized
aggregation system like ELK or Datadog.

VOTE: {"option": "Comprehensive logging with structured format", "confidence": 0.80,
       "rationale": "Enables rapid incident response and root cause analysis",
       "continue_debate": true}
```

**Codex's response**:
```
Logging adds overhead and storage costs. I propose selective logging: only ERROR and
WARN levels in production, with DEBUG/INFO available via feature flags for specific
investigations.

VOTE: {"option": "Selective logging with feature flags", "confidence": 0.75,
       "rationale": "Balances observability with performance and cost",
       "continue_debate": true}
```

**Gemini's response**:
```
Agree with logging importance but concerned about sensitive data exposure. I recommend
comprehensive logging with automatic PII scrubbing and retention policies.

VOTE: {"option": "Comprehensive logging with PII protection", "confidence": 0.70,
       "rationale": "Security and compliance critical for production systems",
       "continue_debate": true}
```

**Round 1 results**:
- Tally: 3 different options (1-1-1 tie)
- Consensus: No (`consensus_reached: false`)
- Continue debate: All 3 models voted `continue_debate: true` (100% want to continue)
- Early stopping: No (threshold not met for stopping)

### Round 2: Refinement and Convergence

Models see each other's Round 1 responses and refine their positions.

**Claude's response**:
```
After reviewing the perspectives, I agree that selective logging balances our needs.
Codex's feature flag approach addresses Gemini's PII concerns: we enable verbose
logging only during investigations, reducing exposure surface.

VOTE: {"option": "Selective logging with feature flags", "confidence": 0.90,
       "rationale": "Combines performance efficiency with on-demand observability",
       "continue_debate": false}
```

**Codex's response**:
```
Maintaining my position but incorporating Gemini's valid PII concern. The feature flag
system should include automatic PII scrubbing when DEBUG logs are enabled.

VOTE: {"option": "Selective logging with feature flags", "confidence": 0.85,
       "rationale": "Optimizes cost and performance while addressing security",
       "continue_debate": false}
```

**Gemini's response**:
```
Convinced by the feature flag approach. It addresses my PII concerns by limiting
verbose logging to controlled investigations where we can enforce scrubbing.

VOTE: {"option": "Selective logging with feature flags", "confidence": 0.88,
       "rationale": "Security-conscious approach with operational flexibility",
       "continue_debate": false}
```

**Round 2 results**:
- Tally: All 3 models voted for same option (3-0)
- Consensus: **Unanimous** (`unanimous_consensus`)
- Winning option: "Selective logging with feature flags"
- Continue debate: All 3 models voted `continue_debate: false` (100% ≥ 66% threshold)
- **Early stopping triggered**: Deliberation ends after Round 2 (saves Round 3+ API costs)

### Final Results

```json
{
  "status": "complete",
  "rounds_completed": 2,
  "convergence_info": {
    "detected": true,
    "detection_round": 2,
    "final_similarity": 0.92,
    "status": "unanimous_consensus",
    "per_participant_similarity": {
      "claude@cli": 0.92,
      "codex@cli": 0.94,
      "gemini@cli": 0.90
    }
  },
  "voting_result": {
    "final_tally": {
      "Selective logging with feature flags": 3
    },
    "votes_by_round": [
      // Round 1 votes (3 different options)
      // Round 2 votes (all same option)
    ],
    "consensus_reached": true,
    "winning_option": "Selective logging with feature flags"
  }
}
```

### Analysis

**Convergence**: Models started with 3 distinct positions (tie) and converged to unanimous agreement in Round 2.

**Confidence progression**:
- Round 1: 0.70-0.80 (moderate confidence, seeking more input)
- Round 2: 0.85-0.90 (high confidence, satisfied with outcome)

**Early stopping**: All models signaled `continue_debate: false`, triggering early stop and saving API costs for rounds 3+.

**Voting override**: Both semantic similarity (92%) and voting (3-0) show consensus, so status is `unanimous_consensus` (voting takes precedence).

**Outcome**: Clear decision with full buy-in from all models, achieved efficiently in 2 rounds.

## Best Practices

### Prompting for Structured Votes

When invoking deliberations, consider adding voting guidance to your question or context:

**Example prompt pattern**:
```javascript
mcp__ai-counsel__deliberate({
  question: "Should we migrate to event sourcing for our audit trail?",
  participants: [...],
  context: `
    Current system: Traditional CRUD with audit_log table
    Requirements: SOC2 compliance, 5-year retention, tamper-proof records

    Please provide your analysis and cast a vote with your recommendation.
  `,
  rounds: 3,
  mode: "conference"
})
```

The system automatically includes voting instructions in prompts, but context helps models make informed decisions.

### Interpreting Confidence Levels

**High confidence (0.8-1.0)**:
- Trust the recommendation
- Likely based on strong evidence or clear requirements
- Safe to proceed with implementation

**Moderate confidence (0.6-0.79)**:
- Review rationales carefully
- May indicate trade-offs or uncertainty
- Consider gathering more context or running additional rounds

**Low confidence (<0.6)**:
- Strong signal that more deliberation needed
- Question may be ambiguous or lack context
- Consider refining the question or adding more participants

### Using Rationales to Understand Disagreements

When votes differ, examine rationales to identify:

**Different priorities**:
```
Model A: "Prioritize performance" (confidence 0.85)
Model B: "Prioritize security" (confidence 0.85)
```
→ Both confident but optimizing for different goals. Clarify priority in context.

**Information gaps**:
```
Model A: "Insufficient information about scale requirements" (confidence 0.50)
```
→ Add context about expected scale, traffic, or constraints.

**Legitimate trade-offs**:
```
Model A: "Option A better for current team size" (confidence 0.75)
Model B: "Option B better for future growth" (confidence 0.70)
```
→ Time horizon matters. Specify short-term vs. long-term focus.

### Trust Higher-Confidence Votes

When consensus is reached, pay attention to confidence levels:

**Unanimous with high confidence** (all >0.8):
- Very strong recommendation
- Models converged on clear optimal choice
- Proceed with confidence

**Majority with mixed confidence**:
- Winning option: 0.85, 0.80 (confident)
- Losing option: 0.90 (also confident)
- Even minority can be very confident
- Review minority rationale for overlooked considerations

**Low confidence consensus** (all <0.7):
- Weak recommendation despite agreement
- May indicate "least bad" choice rather than "clearly good"
- Consider refining question or gathering more information

## Troubleshooting

### Models Not Voting

**Symptom**: No `VOTE:` markers found in responses, `voting_result: null`

**Cause**: Models may not include vote JSON due to:
- Unclear prompt (models unsure what decision to make)
- Informational questions without clear choices
- Models not following voting instructions

**Solution**:
- Silent fallback to semantic similarity (no error)
- Check transcript for model responses
- Ensure question has clear decision points
- Consider adding explicit options to context

**Example fix**:
```javascript
// Before (vague)
question: "What do you think about microservices?"

// After (clear decision)
question: "Should we migrate from monolith to microservices?"
context: "Options: (A) Migrate now, (B) Migrate incrementally, (C) Stay with monolith"
```

### Low Confidence Across All Votes

**Symptom**: All models vote with confidence <0.5

**Cause**:
- Question lacks context
- Ambiguous requirements
- Conflicting priorities
- Insufficient information to make informed decision

**Solution**:
- Review `continue_debate` flags (likely all `true`)
- Add more context about requirements, constraints, priorities
- Increase number of rounds to allow more refinement
- Consider breaking complex question into smaller decisions

**Example**:
```javascript
// Low confidence trigger
question: "What's the best architecture?"
// Result: Models can't decide without context

// High confidence trigger
question: "What's the best architecture?"
context: "E-commerce site, 10K users, $5K/month budget, 3-person team"
// Result: Models have specific constraints to optimize for
```

### Inconsistent Vote Options

**Symptom**: Many unique vote options (5+ options in 3-model deliberation), semantic grouping shows minimal merging

**Cause**:
- Models interpreting question differently
- Too many variables to optimize simultaneously
- Unclear decision boundaries

**Effect**: Vote semantic grouping automatically handles similar wording (>70% similarity), but truly different options remain separate.

**Example**:
```json
// Semantic grouping successfully merges these:
"Event sourcing for audit trail" (similarity: 0.89)
"Use event sourcing to implement audit trail" (merged)

// But these remain separate (too different):
"Event sourcing for audit trail" (similarity: 0.45)
"Traditional CRUD with audit table"
```

**Solution**:
- Refine question to be more specific
- Provide explicit options in context
- Use `stance` parameter to guide perspectives
- Review grouping logs in `mcp_server.log` to see similarity scores

### Vote Grouping Not Merging Expected Options

**Symptom**: Options that seem similar aren't grouped together

**Cause**:
- Similarity score below 0.70 threshold
- Different semantic meaning despite surface similarity
- Fallback to exact matching (similarity backend unavailable)

**Diagnosis**:
Check `mcp_server.log` for similarity scores:
```
INFO: Vote similarity: 'Option A' vs 'Option B': 0.650 (threshold: 0.700)
```

**Solutions**:

1. **Enable similarity backend**: Install optional dependencies for better matching
   ```bash
   pip install -r requirements.txt
   ```

2. **Review semantic difference**: If scores are 0.60-0.69, options may be genuinely different despite similar wording

3. **Use consistent wording**: Encourage models to use exact phrases by providing example options in context

### Early Stopping Not Triggering

**Symptom**: All models vote `continue_debate: false` but deliberation continues

**Causes**:

1. **`early_stopping.enabled: false`** in config
   - Solution: Set to `true` in `config.yaml`

2. **Threshold not met**: Less than 66% of models want to stop
   - Example: 2 of 4 models (50% < 66%)
   - Solution: Lower threshold to 0.50 or ensure more models agree

3. **`respect_min_rounds: true`** and min rounds not reached
   - Example: Round 2 but `defaults.rounds: 3`
   - Solution: Set `respect_min_rounds: false` or let deliberation reach min rounds

**Verification**:
Check `mcp_server.log`:
```
INFO: Early stopping check: 2/3 models want to stop (66.7% >= 66.0% threshold)
INFO: Early stopping triggered after round 2
```

## Summary

Structured voting transforms AI deliberation from opinion gathering to formal decision-making:

- **Explicit choices**: Models formally vote instead of just discussing
- **Quantified confidence**: 0.0-1.0 scale reveals certainty and doubt
- **Semantic grouping**: Similar options automatically merged (>70% similarity)
- **Model-controlled pacing**: Participants signal when ready to conclude
- **Clear outcomes**: Unanimous consensus, majority decision, or tie
- **Audit trail**: Full voting history with timestamps and rationales

Combined with [semantic similarity analysis](convergence-detection.md), structured voting provides robust consensus detection that works reliably across diverse model architectures and response styles.

For configuration details, see `config.yaml` sections:
- `deliberation.convergence_detection` (enables vote grouping)
- `deliberation.early_stopping` (model-controlled stopping)
- `defaults.rounds` (minimum rounds before early stop)
