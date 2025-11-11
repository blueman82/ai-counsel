# AI Counsel Deliberation Framework for QA Agents

## Purpose
This framework provides comprehensive guidance on using the `mcp__ai-counsel__deliberate` tool for multi-model consensus in quality assurance decisions. QA agents reference this document to understand when, how, and why to invoke deliberative decision-making across multiple AI models.

---

## When to Use Deliberation

### High-Stakes Decision Criteria
Invoke multi-model deliberation when decisions meet these criteria:

1. **Irreversible Consequences**: Deployment, rollback, or production changes
2. **Borderline Metrics**: Values within 5-10% of critical thresholds
3. **Conflicting Signals**: Some indicators pass while others show warnings
4. **Ambiguous Requirements**: Multiple valid interpretations exist
5. **Risk Assessment**: Need to evaluate deployment risk levels
6. **Consensus Validation**: Want to validate a tentative decision with diverse perspectives

### Decision Categories

#### 🚨 Critical Decisions (Use `conference` mode - multi-round)
- Production deployment approval/rejection
- Emergency rollback triggers
- Security incident severity classification
- System-wide architectural changes

#### ⚠️ Important Decisions (Use `quick` mode - single round)
- Borderline quality gate evaluations
- Test coverage sufficiency assessment
- Performance optimization trade-offs
- Bug severity classification

#### ℹ️ Don't Deliberate When
- Clear pass/fail based on explicit thresholds
- Routine operational decisions
- Low-risk changes with easy rollback
- Already established patterns with precedent

---

## How to Construct Effective Questions

### Question Structure Template

```
[Context Setup] + [Decision Point] + [Relevant Data] + [Specific Question]
```

### Example: Quality Gate Decision
```markdown
Context: We're evaluating deployment readiness for Global Graph DI Migration.

Decision Point: Should we proceed to next deployment phase?

Relevant Data:
- Container startup time: 28s (limit 30s, alert 35s)
- Service resolution: 99.1% (limit 99%, alert 98%)
- Memory usage: 11.8GB (limit 12GB, alert 13GB)
- API P99 latency: 320ms (limit 500ms)
- Error rate: 0.02% (limit 0.1%)

Question: Given these borderline metrics, should we proceed with deployment
or wait for performance improvements? Consider risk vs. reward and partial
vs. full rollout options.
```

### Question Quality Checklist
- [ ] Provides sufficient context for models to understand domain
- [ ] Includes specific quantitative data (metrics, thresholds)
- [ ] Clearly states the decision to be made
- [ ] Mentions relevant constraints or considerations
- [ ] Open-ended enough to allow diverse perspectives
- [ ] Focused enough to produce actionable recommendations

---

## Participant Selection Strategies

### Model Diversity for Different Decisions

#### Deployment/Infrastructure Decisions
```json
[
  {"cli": "claude", "model": "sonnet"},
  {"cli": "codex", "model": "gpt-5-codex"},
  {"cli": "gemini", "model": "gemini-2.5-pro"}
]
```
**Rationale**: Diverse architectural perspectives on system reliability

#### Test Strategy Decisions
```json
[
  {"cli": "codex", "model": "gpt-5-codex"},
  {"cli": "claude", "model": "sonnet"}
]
```
**Rationale**: Code-focused models for test architecture decisions

#### Security/Risk Assessment
```json
[
  {"cli": "claude", "model": "opus"},
  {"cli": "codex", "model": "gpt-5-codex"},
  {"cli": "gemini", "model": "gemini-2.5-pro"}
]
```
**Rationale**: Maximum diversity for security-critical decisions

#### Quick Validation (2 models minimum)
```json
[
  {"cli": "claude", "model": "sonnet"},
  {"cli": "codex", "model": "gpt-5-codex"}
]
```
**Rationale**: Fast consensus for time-sensitive decisions

### Stance Configuration

Use `stance` parameter strategically:
- **`neutral`** (default): Let models form opinions independently
- **`for`**: Assign to one model to argue for proceeding
- **`against`**: Assign to another model to argue against proceeding

Example for deployment decision:
```json
[
  {"cli": "claude", "model": "sonnet", "stance": "for"},
  {"cli": "codex", "model": "gpt-5-codex", "stance": "against"},
  {"cli": "gemini", "model": "gemini-2.5-pro", "stance": "neutral"}
]
```

---

## Mode Selection Guide

### Quick Mode (`mode: "quick"`)
- **Rounds**: 1 (single round of opinions)
- **Use When**: Time-sensitive decisions, validation needed quickly
- **Duration**: ~30-60 seconds
- **Best For**: Borderline metrics, quick consensus checks, validation of tentative decisions

### Conference Mode (`mode: "conference"`)
- **Rounds**: 2-5 (multi-round deliberation with model interaction)
- **Use When**: Critical decisions, complex trade-offs, high stakes
- **Duration**: ~2-10 minutes depending on rounds
- **Best For**: Production deployment approval, architectural decisions, security assessments

### Rounds Selection
```python
rounds = 1  # Quick validation (quick mode)
rounds = 2  # Standard deliberation with one rebuttal
rounds = 3  # Deep analysis with multiple perspectives
rounds = 4-5  # Complex decisions requiring convergence
```

---

## Interpreting Deliberation Results

### Voting Analysis

#### Strong Consensus (90%+ agreement)
- **Action**: Proceed with the consensus recommendation
- **Documentation**: Note the decision and confidence levels
- **Example**: 3/3 models vote "Proceed" with 0.85+ confidence

#### Moderate Consensus (70-89% agreement)
- **Action**: Proceed with caution, implement monitoring
- **Documentation**: Note dissenting opinion and mitigation strategies
- **Example**: 2/3 models vote "Proceed", 1 votes "Wait with improvements"

#### Split Decision (50-69% agreement)
- **Action**: Investigate further, gather more data, or implement phased approach
- **Documentation**: Summarize both perspectives, identify information gaps
- **Example**: 2/3 vote "Proceed", 1 votes "Rollback" - consider partial rollout

#### No Consensus (<50% or tied)
- **Action**: Do NOT proceed without additional analysis
- **Documentation**: Escalate to human decision-maker with model perspectives
- **Example**: 1 votes "Proceed", 1 votes "Wait", 1 votes "Rollback"

### Confidence Level Interpretation

| Confidence | Interpretation | Action |
|-----------|----------------|--------|
| 0.90-1.0 | Very High | Strong signal, weight heavily in decision |
| 0.75-0.89 | High | Solid reasoning, consider seriously |
| 0.60-0.74 | Moderate | Valid perspective, but verify assumptions |
| 0.40-0.59 | Low | Uncertain, likely needs more information |
| 0.0-0.39 | Very Low | Insufficient confidence, disregard or investigate |

### Rationale Analysis

Look for these elements in model rationales:
- **Risk identification**: What could go wrong?
- **Trade-off analysis**: What are we giving up?
- **Precedent reference**: Similar past decisions
- **Data interpretation**: How metrics are evaluated
- **Mitigation strategies**: How to reduce risk if proceeding

---

## Integration Patterns

### Pre-Decision Deliberation
```markdown
1. Gather relevant metrics and context
2. Formulate deliberation question
3. Select appropriate participants and mode
4. Invoke mcp__ai-counsel__deliberate
5. Analyze voting results and rationales
6. Make final decision based on consensus
7. Document decision and reasoning
```

### Post-Decision Validation
```markdown
1. Make tentative decision based on data
2. Formulate validation question with your reasoning
3. Use quick mode with 2 models
4. If consensus agrees → proceed with confidence
5. If consensus disagrees → reconsider and investigate concerns
```

### Escalation Protocol
```markdown
When to escalate to human decision-maker:
- No consensus reached (<50% agreement)
- High-confidence disagreement (opposing votes >0.80 confidence)
- Security-critical decisions with any uncertainty
- Decisions outside agent authority or scope
```

---

## Example Deliberations

### Example 1: Borderline Quality Gate

**Question:**
```
Context: Pre-deployment validation for container migration phase.

Metrics:
- Startup time: 28s (limit 30s)
- Resolution rate: 99.1% (limit 99%)
- Memory: 11.8GB (limit 12GB)

Should we proceed with deployment or wait for optimization?
```

**Participants:**
```json
[
  {"cli": "claude", "model": "sonnet"},
  {"cli": "codex", "model": "gpt-5-codex"}
]
```

**Expected Outcome:** Quick consensus on proceed/wait with risk mitigation

---

### Example 2: Production Deployment Approval

**Question:**
```
Context: Final production deployment approval for Phase 2 auto-commit feature.

Test Results:
- 1625/1625 tests passing (100%)
- Latency: 45ms (target <50ms)
- CPU usage: 0.8% (target <1%)
- Security scan: 2 medium findings (0 high/critical)

Should we approve production deployment or address medium security findings first?
```

**Participants:**
```json
[
  {"cli": "claude", "model": "opus"},
  {"cli": "codex", "model": "gpt-5-codex"},
  {"cli": "gemini", "model": "gemini-2.5-pro"}
]
```

**Mode:** `conference` with 2 rounds

**Expected Outcome:** Deep analysis of security findings with deployment recommendation

---

### Example 3: Test Coverage Sufficiency

**Question:**
```
Context: Evaluating test coverage for new integration feature.

Coverage:
- Unit tests: 247 tests, 94% line coverage
- Integration tests: 18 scenarios
- Edge cases: 12 identified, 9 tested
- Performance tests: 3 load scenarios

Is this test coverage sufficient for production deployment?
```

**Participants:**
```json
[
  {"cli": "codex", "model": "gpt-5-codex"},
  {"cli": "claude", "model": "sonnet"}
]
```

**Expected Outcome:** Assessment of coverage gaps and recommendations

---

## Best Practices

### DO
✅ **Provide Quantitative Data**: Include metrics, thresholds, and specific numbers
✅ **Frame Clear Questions**: State the decision explicitly
✅ **Use Appropriate Mode**: Quick for validation, conference for critical decisions
✅ **Consider Diverse Models**: Different models bring different perspectives
✅ **Document Outcomes**: Record decisions and rationales for future reference
✅ **Trust Strong Consensus**: When 3 models agree with >0.80 confidence, proceed
✅ **Investigate Split Decisions**: Understand why models disagree

### DON'T
❌ **Don't Deliberate Obvious Decisions**: Clear pass/fail doesn't need consensus
❌ **Don't Omit Context**: Models need domain understanding to provide value
❌ **Don't Ignore Dissent**: Minority opinions may identify critical risks
❌ **Don't Over-Deliberate**: Use quick mode when appropriate
❌ **Don't Skip Documentation**: Record why deliberation was invoked and outcome
❌ **Don't Defer All Decisions**: Use deliberation strategically, not as default

---

## Performance and Cost Considerations

### Latency
- **Quick mode (1 round, 2 models)**: ~30-60 seconds
- **Quick mode (1 round, 3 models)**: ~45-90 seconds
- **Conference mode (2 rounds, 3 models)**: ~2-4 minutes
- **Conference mode (5 rounds, 3 models)**: ~8-12 minutes

### Cost per Deliberation
- Varies by model selection and rounds
- Use Sonnet for cost-efficiency
- Use Opus/GPT-5 for critical decisions
- Monitor cumulative costs in high-frequency scenarios

### When to Optimize
- If deliberating >10 times per day, review necessity
- Consider caching similar deliberations
- Use quick mode as default, conference only when needed

---

## Agent-Specific Usage

Each QA agent has specific trigger conditions for deliberation based on their decision domains. See individual agent configurations for:

- **qa-deployment-validator**: Quality gate thresholds and rollback triggers
- **guardian**: Production readiness and performance boundary cases
- **quality-control**: Task completion ambiguity and process violations
- **test-automator**: Testing strategy debates and coverage decisions
- **integration-validator**: Integration status and deployment phase progression

---

## Continuous Improvement

### Learning from Deliberations

Track these patterns over time:
1. **Accuracy**: Did consensus recommendations prove correct?
2. **Utility**: Did deliberation change decisions meaningfully?
3. **Efficiency**: Could some deliberations have been avoided?
4. **Coverage**: Are we deliberating on the right decisions?

### Framework Evolution

This framework will evolve based on:
- Real-world deliberation outcomes
- New decision patterns that emerge
- Model capability improvements
- Team feedback and usage patterns

**Last Updated**: 2025-10-14
**Version**: 1.0.0
**Maintained By**: QA Agent Team
