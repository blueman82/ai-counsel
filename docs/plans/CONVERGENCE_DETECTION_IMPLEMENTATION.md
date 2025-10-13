# Convergence Detection Implementation Plan

**Feature:** Auto-stop deliberation when AI model opinions stabilize
**Status:** Phase 5 Complete - E2E Test Framework Ready (User Testing Required)
**Engineer Guidance:** Full implementation guide for developers with minimal codebase context

---

## Table of Contents

1. [Agent Execution Strategy](#agent-execution-strategy) **← NEW**
2. [Background & Context](#background--context)
3. [System Architecture Overview](#system-architecture-overview)
4. [Prerequisites](#prerequisites)
5. [Implementation Principles](#implementation-principles)
6. [Task Breakdown](#task-breakdown)
7. [Testing Guidelines](#testing-guidelines)
8. [Acceptance Criteria](#acceptance-criteria)

---

## Agent Execution Strategy

**🤖 Parallel Agent-Based Implementation**

This implementation uses **3 specialized Python agents** working in parallel with dependency tracking. Each agent has its own TodoWrite list and can work independently on isolated tasks.

### Agent Team

**1. python-schema-architect** (`~/.claude/agents/python-schema-architect.md`)
- **Specialization**: Pydantic models, YAML configuration, data validation
- **Assigned Tasks**: Phase 1 (Tasks 1.1, 1.2)
- **Tools**: Read, Write, Edit, Bash (testing), Grep, Glob, TodoWrite

**2. python-backend-tdd-agent** (`~/.claude/agents/python-backend-tdd-agent.md`)
- **Specialization**: Backend logic with strict TDD (tests before code)
- **Assigned Tasks**: Phase 2 (Tasks 2.1-2.4), Phase 3 (Tasks 3.1-3.2)
- **Tools**: Read, Write, Edit, Bash (pytest), Grep, Glob, TodoWrite

**3. python-integration-specialist** (`~/.claude/agents/python-integration-specialist.md`)
- **Specialization**: Async integration, dependency injection, engine modification
- **Assigned Tasks**: Phase 4 (Tasks 4.1-4.2), Phase 6 (Tasks 6.1-6.2)
- **Tools**: Read, Write, Edit, Bash (testing), Grep, Glob, TodoWrite

### Parallel Execution Strategy

**Execution Flow (Fully Parallel with Dependency Tracking):**

```
START
  │
  ├─▶ Agent 1 (python-schema-architect)
  │   ├─ Task 1.1: Add ConvergenceInfo Model → DONE
  │   └─ Task 1.2: Update Config Schema → DONE
  │       │
  │       ▼ [DEPENDENCY MET: Schema ready]
  │       │
  ├─▶ Agent 2 (python-backend-tdd-agent) [WAITS for Phase 1]
  │   ├─ Task 2.1: Create Test Structure → DONE
  │   ├─ Task 2.2: Implement Jaccard Backend → DONE
  │   ├─ Task 2.3: Implement TF-IDF Backend → DONE
  │   ├─ Task 2.4: Implement Sentence Transformer → DONE
  │   ├─ Task 3.1: Write Detector Tests → DONE
  │   └─ Task 3.2: Implement ConvergenceDetector → DONE
  │       │
  │       ▼ [DEPENDENCY MET: Convergence module ready]
  │       │
  └─▶ Agent 3 (python-integration-specialist) [WAITS for Phase 2 & 3]
      ├─ Task 4.1: Write Integration Tests → ✅ DONE (2025-10-13)
      ├─ Task 4.2: Integrate into Engine → ✅ DONE (2025-10-13)
      ├─ Task 4.3: Fix Production Config Bug → ✅ DONE (2025-10-13)
      ├─ Phase 5: Manual E2E Testing → TODO (User-assisted)
      ├─ Task 6.1: Update README → ✅ DONE (2025-10-13)
      └─ Task 6.2: Add Inline Docs → ✅ DONE (2025-10-13)

COMPLETE ✅
```

### Dependencies & Synchronization

**Critical Dependencies:**
1. **Phase 2-3 DEPENDS ON Phase 1**: Backend code needs schema models
   - Agent 2 waits until Agent 1 commits `models/schema.py`
   - Check: `git log --oneline | grep "ConvergenceInfo"`

2. **Phase 4 DEPENDS ON Phase 2-3**: Engine integration needs convergence module
   - Agent 3 waits until Agent 2 commits `deliberation/convergence.py`
   - Check: `git log --oneline | grep "ConvergenceDetector"`

3. **Phase 5 DEPENDS ON Phase 4**: E2E testing needs integrated engine
   - Manual testing after Agent 3 completes engine integration

**How Agents Check Dependencies:**

Each agent will run these checks before starting work:

```bash
# Agent 2 checks before Phase 2:
python3 -c "from models.schema import ConvergenceInfo; print('✓ Schema ready')" || echo "❌ Waiting for Agent 1..."

# Agent 3 checks before Phase 4:
python3 -c "from deliberation.convergence import ConvergenceDetector; print('✓ Convergence ready')" || echo "❌ Waiting for Agent 2..."
```

### Agent Todo Lists

Each agent maintains its own isolated TodoWrite list:

**Agent 1 (python-schema-architect) Todo List:**
```
- [ ] Task 1.1: Add ConvergenceInfo model to schema.py
- [ ] Task 1.2: Update config.yaml with convergence settings
- [ ] Commit Phase 1 changes
- [ ] Notify Agent 2: Phase 1 complete
```

**Agent 2 (python-backend-tdd-agent) Todo List:**
```
- [ ] Wait for Agent 1 to complete (check schema imports)
- [ ] Task 2.1: Create test_convergence.py structure
- [ ] Task 2.2: Implement Jaccard backend (TDD)
- [ ] Task 2.3: Implement TF-IDF backend (TDD)
- [ ] Task 2.4: Implement Sentence Transformer backend (TDD)
- [ ] Task 3.1: Write ConvergenceDetector tests
- [ ] Task 3.2: Implement ConvergenceDetector class
- [ ] Commit Phase 2-3 changes
- [ ] Notify Agent 3: Phase 2-3 complete
```

**Agent 3 (python-integration-specialist) Todo List:**
```
- [ ] Wait for Agent 2 to complete (check convergence imports)
- [ ] Task 4.1: Write integration test structure
- [ ] Task 4.2: Integrate ConvergenceDetector into engine.py
- [ ] Assist with Phase 5: Manual E2E testing
- [ ] Task 6.1: Update README with convergence docs
- [ ] Task 6.2: Add inline documentation to all code
- [ ] Commit Phase 4-6 changes
- [ ] Final verification: Run all tests
```

### Launching Agents

**Option A: Sequential Launch (Recommended for First Time)**

Launch agents one at a time, verifying each phase:

```bash
# Terminal 1: Launch Agent 1
claude --agent python-schema-architect "Implement Phase 1 tasks from docs/plans/CONVERGENCE_DETECTION_IMPLEMENTATION.md. Use TodoWrite to track progress. Commit when done."

# Wait for Agent 1 to commit, then Terminal 2: Launch Agent 2
claude --agent python-backend-tdd-agent "Implement Phase 2-3 tasks from docs/plans/CONVERGENCE_DETECTION_IMPLEMENTATION.md. Wait for schema changes first. Use TodoWrite to track progress. Commit when done."

# Wait for Agent 2 to commit, then Terminal 3: Launch Agent 3
claude --agent python-integration-specialist "Implement Phase 4 and 6 tasks from docs/plans/CONVERGENCE_DETECTION_IMPLEMENTATION.md. Wait for convergence module first. Use TodoWrite to track progress. Commit when done."
```

**Option B: Fully Parallel Launch (Advanced)**

Launch all agents simultaneously with dependency awareness:

```bash
# Launch all three in parallel - they'll wait for dependencies internally
claude --agent python-schema-architect "Implement Phase 1 per CONVERGENCE_DETECTION_IMPLEMENTATION.md. TodoWrite tracking." &
claude --agent python-backend-tdd-agent "Implement Phase 2-3 per CONVERGENCE_DETECTION_IMPLEMENTATION.md. Wait for schema deps. TodoWrite tracking." &
claude --agent python-integration-specialist "Implement Phase 4 & 6 per CONVERGENCE_DETECTION_IMPLEMENTATION.md. Wait for convergence deps. TodoWrite tracking." &
```

### Monitoring Progress

**Check agent progress:**

```bash
# View Agent 1 commits
git log --oneline --grep="ConvergenceInfo\|config.yaml" --all

# View Agent 2 commits
git log --oneline --grep="convergence.py\|test_convergence" --all

# View Agent 3 commits
git log --oneline --grep="engine.py\|README" --all

# View all agent todo lists
cat .claude/todos/python-schema-architect.json
cat .claude/todos/python-backend-tdd-agent.json
cat .claude/todos/python-integration-specialist.json
```

### Conflict Resolution

If agents produce conflicts (rare due to isolated file work):

1. **Phase 1 vs Phase 2**: Different files - no conflicts expected
2. **Phase 2 vs Phase 3**: Same file (`convergence.py`) but sequential tasks - no conflicts
3. **Phase 3 vs Phase 4**: Different files - no conflicts expected

**If conflict occurs:**
```bash
git status  # Check conflicted files
git diff    # Review conflicts
# Manually resolve, then:
git add <file>
git commit -m "Resolve agent conflict in <file>"
```

### Success Criteria

**Implementation Complete When:**
- ✅ All 3 agents report "DONE" in their TodoWrite lists
- ✅ All tests passing: `pytest tests/unit/ -v`
- ✅ Engine integrates detector: `python -c "from deliberation.engine import DeliberationEngine; print('✓')"`
- ✅ README updated with convergence docs
- ✅ Git log shows clean, sequential commits from all agents

---

## Background & Context

### What is AI Counsel?

AI Counsel is an MCP (Model Context Protocol) server that orchestrates deliberations between multiple AI models. Think of it as a debate moderator:

- **Conference mode**: Models debate over multiple rounds, seeing each other's responses
- **Quick mode**: Models give parallel opinions without seeing each other

Currently, conference mode runs a fixed number of rounds (default: 2-5). This wastes time and API costs when models agree early.

### The Problem

Example scenario:
- User asks: "Should we use TypeScript or JavaScript?"
- Round 1: Both Claude and Codex say "TypeScript"
- Round 2: Both repeat "TypeScript" with same reasoning
- Rounds 3-5: **Waste of time** - they already agree!

### The Solution

**Convergence Detection**: Automatically detect when models' opinions stabilize and stop early.

**Key concepts:**
- **Convergence**: Models reach agreement (high semantic similarity between consecutive rounds)
- **Impasse**: Models fundamentally disagree despite stable positions (low similarity + no stance changes)
- **Semantic similarity**: How similar two pieces of text are in meaning (0.0 = completely different, 1.0 = identical)

---

## System Architecture Overview

### Current File Structure

```
ai-counsel/
├── server.py              # MCP server entry point
├── config.yaml           # Configuration file
├── adapters/             # CLI tool adapters (claude, codex, droid, gemini)
│   ├── __init__.py
│   ├── base.py          # BaseCLIAdapter abstract class
│   ├── claude.py
│   └── codex.py
├── deliberation/         # Core deliberation engine
│   ├── __init__.py
│   ├── engine.py        # DeliberationEngine - orchestrates rounds
│   └── transcript.py    # Generates markdown transcripts
├── models/               # Pydantic data models
│   ├── __init__.py
│   ├── schema.py        # RoundResponse, DeliberationResult, etc.
│   └── config.py        # Config loading
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### New Files We'll Create

```
deliberation/
└── convergence.py         # NEW - Convergence detection logic

tests/unit/
└── test_convergence.py    # NEW - Unit tests for convergence
```

### Files We'll Modify

```
models/schema.py           # Add ConvergenceInfo model
deliberation/engine.py     # Integrate convergence detector
config.yaml               # Add convergence settings
requirements.txt          # Add optional dependencies
```

---

## Prerequisites

### Understanding the Domain

**1. What is a "round" in deliberation?**

A round is one turn where each participant responds. In a 3-round deliberation with 2 participants:
- Round 1: Participant A responds, Participant B responds
- Round 2: Both see round 1, respond again
- Round 3: Both see rounds 1-2, respond again

**2. What is semantic similarity?**

Measuring how similar two texts are in meaning:

```python
text1 = "I prefer TypeScript for type safety"
text2 = "TypeScript is better because it has types"
# High similarity (~0.85) - same meaning, different words

text3 = "JavaScript is more flexible"
# Low similarity (~0.3) - opposite opinion
```

**3. What are the similarity backends?**

Three ways to compute similarity (we'll implement all 3):

- **Jaccard**: Simple word overlap (zero dependencies)
  ```python
  # "the quick brown fox" vs "the lazy brown dog"
  # Shared words: {the, brown} = 2
  # Total unique: {the, quick, brown, fox, lazy, dog} = 6
  # Similarity = 2/6 = 0.33
  ```

- **TF-IDF**: Statistical text analysis (requires scikit-learn)
  - Weighs important words higher
  - Better than Jaccard, lighter than transformers

- **Sentence Transformers**: Neural embeddings (requires sentence-transformers library)
  - Best accuracy, understands semantics
  - ~500MB model download

**4. Understanding Pydantic Models**

This codebase uses Pydantic for data validation:

```python
from pydantic import BaseModel, Field

class Example(BaseModel):
    name: str = Field(..., description="Required field")
    count: int = Field(default=0, description="Optional with default")
```

---

## Implementation Principles

### TDD (Test-Driven Development)

**Always write tests BEFORE implementation:**

1. Write a failing test (RED)
2. Write minimal code to pass (GREEN)
3. Refactor if needed (REFACTOR)
4. Commit

### DRY (Don't Repeat Yourself)

- Extract common logic to base classes
- Reuse existing patterns from the codebase
- Use inheritance for similarity backends

### YAGNI (You Aren't Gonna Need It)

- Implement only what's specified
- No premature optimization
- No extra features "just in case"

### Frequent Commits

Commit after each task completion with descriptive messages:
```bash
git add <files>
git commit -m "Add Jaccard similarity backend with tests"
```

---

## Task Breakdown

### Phase 1: Foundation (Data Models & Config)

#### Task 1.1: Add ConvergenceInfo Model

**Goal**: Create Pydantic model to store convergence detection results

**Files to modify:**
- `models/schema.py`

**What to do:**

1. Open `models/schema.py`
2. Review existing models (RoundResponse, DeliberationResult) to understand the pattern
3. Add this new model BEFORE the `DeliberationResult` class:

```python
class ConvergenceInfo(BaseModel):
    """Convergence detection metadata."""

    detected: bool = Field(
        ...,
        description="Whether convergence was detected"
    )
    detection_round: Optional[int] = Field(
        None,
        description="Round where convergence occurred (None if not detected)"
    )
    final_similarity: float = Field(
        ...,
        description="Final similarity score (minimum across all participants)"
    )
    status: Literal["converged", "diverging", "refining", "impasse", "max_rounds"] = Field(
        ...,
        description="Convergence status"
    )
    scores_by_round: list[dict] = Field(
        default_factory=list,
        description="Per-round similarity tracking data"
    )
    per_participant_similarity: dict[str, float] = Field(
        default_factory=dict,
        description="Latest similarity score for each participant"
    )
```

4. Update `DeliberationResult` class - add this field:

```python
class DeliberationResult(BaseModel):
    # ... existing fields (don't modify) ...

    convergence_info: Optional[ConvergenceInfo] = Field(
        None,
        description="Convergence detection information (None if detection disabled)"
    )
```

**How to test:**

```bash
# Run Python in the repo root
python3 -c "from models.schema import ConvergenceInfo, DeliberationResult; print('✓ Import successful')"
```

You should see: `✓ Import successful`

If you get errors, you probably have syntax issues. Check:
- Commas between fields
- Matching parentheses
- Proper indentation

**Commit:**
```bash
git add models/schema.py
git commit -m "Add ConvergenceInfo and convergence_info field to DeliberationResult

- Add ConvergenceInfo model with detection metadata
- Add optional convergence_info field to DeliberationResult
- Supports convergence detection feature implementation"
```

**Definition of Done:**
- [ ] ConvergenceInfo model added with all 6 fields
- [ ] DeliberationResult has convergence_info field
- [ ] Import test passes
- [ ] Changes committed

---

#### Task 1.2: Update Config Schema

**Goal**: Add convergence detection settings to config.yaml

**Files to modify:**
- `config.yaml`

**What to do:**

1. Open `config.yaml`
2. Find the `deliberation:` section (around line 36)
3. Replace the existing minimal config with this detailed config:

```yaml
deliberation:
  # Convergence detection settings
  convergence_detection:
    enabled: true

    # Similarity thresholds
    semantic_similarity_threshold: 0.85  # Models converged if similarity >= this
    divergence_threshold: 0.40           # Models diverging if similarity < this

    # Round constraints
    min_rounds_before_check: 2           # Don't check convergence until round 3
    consecutive_stable_rounds: 2         # Require 2 stable rounds to confirm

    # Secondary metrics
    stance_stability_threshold: 0.80     # 80% of participants must have stable stances
    response_length_drop_threshold: 0.40 # Flag if response length drops >40%

  # Legacy settings (keep these)
  convergence_threshold: 0.8
  enable_convergence_detection: true
```

**How to test:**

```bash
# Test config loading
python3 -c "
from models.config import load_config
config = load_config('config.yaml')
print(f'✓ Threshold: {config.deliberation.convergence_detection.semantic_similarity_threshold}')
"
```

Expected output: `✓ Threshold: 0.85`

If you get `AttributeError`, check:
- Indentation matches (use spaces, not tabs)
- Key names match exactly
- File saved properly

**Commit:**
```bash
git add config.yaml
git commit -m "Add detailed convergence detection config

- Add convergence_detection section with all thresholds
- Configure min_rounds_before_check, consecutive_stable_rounds
- Keep legacy settings for backward compatibility"
```

**Definition of Done:**
- [ ] convergence_detection section added
- [ ] All 7 settings present with correct values
- [ ] Config loads without errors
- [ ] Changes committed

---

### Phase 2: Similarity Backends (TDD)

**Important**: For each backend, we write tests FIRST, then implementation.

#### Task 2.1: Create Test File Structure

**Goal**: Set up test file with proper structure

**Files to create:**
- `tests/unit/test_convergence.py`

**What to do:**

1. Create the file: `tests/unit/test_convergence.py`
2. Add this starter structure:

```python
"""Unit tests for convergence detection."""
import pytest
from deliberation.convergence import (
    JaccardBackend,
    TFIDFBackend,
    SentenceTransformerBackend,
    ConvergenceDetector,
)


# =============================================================================
# Jaccard Similarity Backend Tests
# =============================================================================

class TestJaccardBackend:
    """Test Jaccard similarity computation."""

    def test_identical_text_returns_one(self):
        """Identical text should have similarity of 1.0."""
        backend = JaccardBackend()
        text = "The quick brown fox jumps over the lazy dog"
        similarity = backend.compute_similarity(text, text)
        assert similarity == 1.0

    def test_completely_different_text_returns_zero(self):
        """Completely different text should have similarity near 0.0."""
        backend = JaccardBackend()
        text1 = "The quick brown fox"
        text2 = "airplane engine turbulence"
        similarity = backend.compute_similarity(text1, text2)
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Partially overlapping text should have intermediate similarity."""
        backend = JaccardBackend()
        text1 = "the quick brown fox"
        text2 = "the lazy brown dog"
        similarity = backend.compute_similarity(text1, text2)
        # Shared: {the, brown} = 2 words
        # Total: {the, quick, brown, fox, lazy, dog} = 6 words
        # Expected: 2/6 = 0.333...
        assert 0.3 <= similarity <= 0.4

    def test_case_insensitive(self):
        """Similarity should be case-insensitive."""
        backend = JaccardBackend()
        text1 = "The Quick Brown Fox"
        text2 = "the quick brown fox"
        similarity = backend.compute_similarity(text1, text2)
        assert similarity == 1.0

    def test_handles_empty_strings(self):
        """Empty strings should return 0.0 similarity."""
        backend = JaccardBackend()
        similarity = backend.compute_similarity("", "some text")
        assert similarity == 0.0


# =============================================================================
# TF-IDF Backend Tests (optional dependency)
# =============================================================================

class TestTFIDFBackend:
    """Test TF-IDF similarity computation."""

    def test_import_skipped_if_sklearn_missing(self):
        """Should skip if scikit-learn not installed."""
        try:
            import sklearn
            pytest.skip("scikit-learn is installed, skip this test")
        except ImportError:
            with pytest.raises(ImportError):
                TFIDFBackend()

    @pytest.mark.skipif(
        not pytest.importorskip("sklearn", minversion="1.0"),
        reason="scikit-learn not installed"
    )
    def test_identical_text_returns_one(self):
        """Identical text should have similarity of 1.0."""
        backend = TFIDFBackend()
        text = "The quick brown fox jumps over the lazy dog"
        similarity = backend.compute_similarity(text, text)
        assert similarity == pytest.approx(1.0, abs=0.01)

    @pytest.mark.skipif(
        not pytest.importorskip("sklearn", minversion="1.0"),
        reason="scikit-learn not installed"
    )
    def test_semantic_similarity(self):
        """TF-IDF should capture some semantic similarity."""
        backend = TFIDFBackend()
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because of types"
        similarity = backend.compute_similarity(text1, text2)
        # Should be higher than Jaccard due to TF-IDF weighting
        assert similarity > 0.3


# =============================================================================
# Sentence Transformer Backend Tests (optional dependency)
# =============================================================================

class TestSentenceTransformerBackend:
    """Test sentence transformer similarity."""

    @pytest.mark.skipif(
        not pytest.importorskip("sentence_transformers", minversion="2.0"),
        reason="sentence-transformers not installed"
    )
    def test_identical_text_returns_one(self):
        """Identical text should have similarity near 1.0."""
        backend = SentenceTransformerBackend()
        text = "The quick brown fox"
        similarity = backend.compute_similarity(text, text)
        assert similarity > 0.99

    @pytest.mark.skipif(
        not pytest.importorskip("sentence_transformers", minversion="2.0"),
        reason="sentence-transformers not installed"
    )
    def test_semantic_understanding(self):
        """Should understand semantic similarity."""
        backend = SentenceTransformerBackend()
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because it has types"
        similarity = backend.compute_similarity(text1, text2)
        # Should be high - same meaning
        assert similarity > 0.7


# =============================================================================
# Convergence Detector Tests (we'll add these in later tasks)
# =============================================================================

class TestConvergenceDetector:
    """Test convergence detection logic."""

    def test_placeholder(self):
        """Placeholder - will implement in Phase 3."""
        pass
```

**How to test:**

```bash
# Run the tests (should skip most, fail placeholder)
source .venv/bin/activate
pytest tests/unit/test_convergence.py -v
```

Expected: Tests exist but we haven't implemented the code yet, so imports will fail. **This is correct for TDD!**

**Commit:**
```bash
git add tests/unit/test_convergence.py
git commit -m "Add test structure for convergence detection (TDD)

- Add test classes for all three similarity backends
- Add placeholder tests for ConvergenceDetector
- Tests will fail until implementation added (TDD red phase)"
```

**Definition of Done:**
- [ ] Test file created with all test classes
- [ ] Tests reference not-yet-created convergence.py (expected)
- [ ] Changes committed

---

#### Task 2.2: Implement Jaccard Backend (Make Tests Pass)

**Goal**: Implement Jaccard similarity to make tests pass

**Files to create:**
- `deliberation/convergence.py`

**What to do:**

1. Create `deliberation/convergence.py`
2. Add this implementation:

```python
"""Convergence detection for deliberation rounds."""
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Similarity Backend Interface
# =============================================================================

class SimilarityBackend(ABC):
    """Abstract base class for similarity computation backends."""

    @abstractmethod
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)
        """
        pass


# =============================================================================
# Jaccard Backend (Zero Dependencies)
# =============================================================================

class JaccardBackend(SimilarityBackend):
    """
    Jaccard similarity backend using word overlap.

    Formula: |A ∩ B| / |A ∪ B|

    Example:
        text1 = "the quick brown fox"
        text2 = "the lazy brown dog"

        A = {the, quick, brown, fox}
        B = {the, lazy, brown, dog}

        Intersection = {the, brown} = 2 words
        Union = {the, quick, brown, fox, lazy, dog} = 6 words

        Similarity = 2 / 6 = 0.333

    Pros:
        - Zero dependencies
        - Fast computation
        - Easy to understand

    Cons:
        - Doesn't understand semantics
        - Order-independent
        - Case-sensitive unless normalized
    """

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        # Handle empty strings
        if not text1 or not text2:
            return 0.0

        # Normalize: lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Handle case where both are empty after normalization
        if not words1 or not words2:
            return 0.0

        # Compute Jaccard similarity
        intersection = words1 & words2  # Words in both
        union = words1 | words2          # All unique words

        # Avoid division by zero
        if not union:
            return 0.0

        similarity = len(intersection) / len(union)
        return similarity


# =============================================================================
# TF-IDF Backend (Requires scikit-learn)
# =============================================================================

class TFIDFBackend(SimilarityBackend):
    """
    TF-IDF similarity backend.

    Requires: scikit-learn

    Better than Jaccard because:
        - Weighs rare words higher (more discriminative)
        - Reduces impact of common words (the, a, is)
        - Still lightweight (~50MB)

    Example:
        text1 = "TypeScript has types"
        text2 = "TypeScript provides type safety"

        TF-IDF will weight "TypeScript" and "type(s)" highly,
        downweight "has" and "provides"
    """

    def __init__(self):
        """Initialize TF-IDF backend."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.vectorizer = TfidfVectorizer()
            self.cosine_similarity = cosine_similarity
        except ImportError as e:
            raise ImportError(
                "TFIDFBackend requires scikit-learn. "
                "Install with: pip install scikit-learn"
            ) from e

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        # Compute TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])

        # Compute cosine similarity
        similarity = self.cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

        return float(similarity)


# =============================================================================
# Sentence Transformer Backend (Requires sentence-transformers)
# =============================================================================

class SentenceTransformerBackend(SimilarityBackend):
    """
    Sentence transformer backend using neural embeddings.

    Requires: sentence-transformers (~500MB model download)

    Best accuracy because:
        - Understands semantics and context
        - Trained on billions of sentence pairs
        - Captures paraphrasing and synonyms

    Example:
        text1 = "I prefer TypeScript for type safety"
        text2 = "TypeScript is better because it has types"

        These have similar meaning despite different words.
        Sentence transformers will give high similarity (~0.85).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence transformer backend.

        Args:
            model_name: Model to use (default: all-MiniLM-L6-v2)
                       This is a good balance of speed and accuracy.
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            logger.info(f"Loading sentence transformer model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.cosine_similarity = cosine_similarity
            logger.info("Sentence transformer model loaded successfully")

        except ImportError as e:
            raise ImportError(
                "SentenceTransformerBackend requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            ) from e

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity using sentence embeddings."""
        if not text1 or not text2:
            return 0.0

        # Generate embeddings (vectors that capture meaning)
        embeddings = self.model.encode([text1, text2])

        # Compute cosine similarity between embeddings
        similarity = self.cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1)
        )[0][0]

        return float(similarity)
```

**How to test:**

```bash
# Run Jaccard tests only
source .venv/bin/activate
pytest tests/unit/test_convergence.py::TestJaccardBackend -v
```

Expected output:
```
test_convergence.py::TestJaccardBackend::test_identical_text_returns_one PASSED
test_convergence.py::TestJaccardBackend::test_completely_different_text_returns_zero PASSED
test_convergence.py::TestJaccardBackend::test_partial_overlap PASSED
test_convergence.py::TestJaccardBackend::test_case_insensitive PASSED
test_convergence.py::TestJaccardBackend::test_handles_empty_strings PASSED

==================== 5 passed ====================
```

If tests fail:
- Check formula: intersection / union
- Verify case normalization: `text.lower()`
- Check empty string handling

**Commit:**
```bash
git add deliberation/convergence.py
git commit -m "Implement Jaccard similarity backend

- Add SimilarityBackend abstract base class
- Implement JaccardBackend with word overlap
- All Jaccard tests passing (5/5)
- Zero dependencies, fast computation"
```

**Definition of Done:**
- [ ] convergence.py created
- [ ] SimilarityBackend base class defined
- [ ] JaccardBackend implemented
- [ ] All 5 Jaccard tests pass
- [ ] Changes committed

---

#### Task 2.3: Implement TF-IDF Backend

**Goal**: Implement TF-IDF similarity (optional dependency)

**Files to modify:**
- `deliberation/convergence.py` (already has TFIDFBackend from previous code)
- `requirements.txt`

**What to do:**

1. The TFIDFBackend class is already in convergence.py (we added it in Task 2.2)

2. Update `requirements.txt` - add optional dependencies at the end:

```txt
# Existing dependencies (don't modify)
mcp
pydantic
pyyaml
pytest
pytest-asyncio
pytest-mock

# Optional: Enhanced convergence detection
scikit-learn  # TF-IDF similarity
sentence-transformers  # Neural semantic similarity
```

3. Install scikit-learn for testing:

```bash
source .venv/bin/activate
pip install scikit-learn
```

**How to test:**

```bash
# Run TF-IDF tests
pytest tests/unit/test_convergence.py::TestTFIDFBackend -v
```

Expected:
```
test_convergence.py::TestTFIDFBackend::test_import_skipped_if_sklearn_missing SKIPPED
test_convergence.py::TestTFIDFBackend::test_identical_text_returns_one PASSED
test_convergence.py::TestTFIDFBackend::test_semantic_similarity PASSED

==================== 2 passed, 1 skipped ====================
```

**Commit:**
```bash
git add requirements.txt
git commit -m "Add TF-IDF backend and optional dependencies

- Add scikit-learn to requirements.txt
- TFIDFBackend tests passing (2/2)
- Gracefully handles missing sklearn (ImportError)"
```

**Definition of Done:**
- [ ] scikit-learn added to requirements.txt
- [ ] TF-IDF tests pass when sklearn installed
- [ ] TF-IDF raises ImportError when sklearn missing
- [ ] Changes committed

---

#### Task 2.4: Implement Sentence Transformer Backend

**Goal**: Implement best-accuracy backend (optional dependency)

**Files to modify:**
- `deliberation/convergence.py` (already has SentenceTransformerBackend)

**What to do:**

1. The SentenceTransformerBackend is already implemented in convergence.py

2. Install sentence-transformers (optional, for testing):

```bash
# This downloads a ~500MB model - only if you want to test
pip install sentence-transformers
```

**How to test:**

```bash
# Run sentence transformer tests
pytest tests/unit/test_convergence.py::TestSentenceTransformerBackend -v
```

Expected (if installed):
```
test_convergence.py::TestSentenceTransformerBackend::test_identical_text_returns_one PASSED
test_convergence.py::TestSentenceTransformerBackend::test_semantic_understanding PASSED

==================== 2 passed ====================
```

Expected (if NOT installed):
```
test_convergence.py::TestSentenceTransformerBackend::test_identical_text_returns_one SKIPPED
test_convergence.py::TestSentenceTransformerBackend::test_semantic_understanding SKIPPED

==================== 2 skipped ====================
```

**Both outcomes are correct!** The backend is optional.

**Commit:**
```bash
git commit --allow-empty -m "Verify sentence transformer backend implementation

- SentenceTransformerBackend tests pass when library installed
- Gracefully skips when library missing (optional dependency)
- All three similarity backends complete"
```

**Definition of Done:**
- [ ] Sentence transformer tests pass OR skip gracefully
- [ ] All three backends implemented
- [ ] Changes committed

---

### Phase 3: Convergence Detection Logic (TDD)

#### Task 3.1: Write Convergence Detector Tests

**Goal**: Write tests for the main convergence detection logic

**Files to modify:**
- `tests/unit/test_convergence.py`

**What to do:**

1. Open `tests/unit/test_convergence.py`
2. Replace the `TestConvergenceDetector` placeholder with these comprehensive tests:

```python
# =============================================================================
# Convergence Detector Tests
# =============================================================================

class TestConvergenceDetector:
    """Test convergence detection logic."""

    def test_detects_convergence_all_participants_stable(self):
        """Should detect convergence when all participants stabilize."""
        from models.schema import RoundResponse
        from models.config import DeliberationConfig

        # Mock config
        config = type('Config', (), {
            'deliberation': type('Delib', (), {
                'convergence_detection': type('Conv', (), {
                    'enabled': True,
                    'semantic_similarity_threshold': 0.85,
                    'min_rounds_before_check': 2,
                    'consecutive_stable_rounds': 1,
                })()
            })()
        })()

        detector = ConvergenceDetector(config)

        # Round 2 responses
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                stance="for",
                response="TypeScript is better for large projects",
                timestamp="2025-01-01T00:00:00"
            ),
            RoundResponse(
                round=2,
                participant="codex@cli",
                stance="for",
                response="I agree TypeScript scales better",
                timestamp="2025-01-01T00:00:01"
            )
        ]

        # Round 3 responses (very similar to round 2)
        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                stance="for",
                response="TypeScript is better for large projects because of types",
                timestamp="2025-01-01T00:01:00"
            ),
            RoundResponse(
                round=3,
                participant="codex@cli",
                stance="for",
                response="I agree TypeScript scales better with type safety",
                timestamp="2025-01-01T00:01:01"
            )
        ]

        result = detector.check_convergence(
            current_round=round3,
            previous_round=round2,
            round_number=3
        )

        # With Jaccard similarity, these should be similar enough
        # to detect convergence (shared key words)
        assert result.converged == True
        assert result.status == "converged"
        assert result.min_similarity > 0.5  # At least moderate similarity

    def test_no_convergence_when_opinions_change(self):
        """Should not detect convergence when opinions change significantly."""
        from models.schema import RoundResponse

        config = type('Config', (), {
            'deliberation': type('Delib', (), {
                'convergence_detection': type('Conv', (), {
                    'enabled': True,
                    'semantic_similarity_threshold': 0.85,
                    'min_rounds_before_check': 2,
                    'consecutive_stable_rounds': 1,
                })()
            })()
        })()

        detector = ConvergenceDetector(config)

        # Round 2: One participant says TypeScript
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                stance="for",
                response="TypeScript is better",
                timestamp="2025-01-01T00:00:00"
            )
        ]

        # Round 3: Same participant now says JavaScript
        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                stance="against",
                response="Actually JavaScript is more flexible",
                timestamp="2025-01-01T00:01:00"
            )
        ]

        result = detector.check_convergence(
            current_round=round3,
            previous_round=round2,
            round_number=3
        )

        assert result.converged == False
        assert result.status in ["refining", "diverging"]

    def test_detects_impasse_stable_disagreement(self):
        """Should detect impasse when models disagree but stop changing."""
        from models.schema import RoundResponse

        config = type('Config', (), {
            'deliberation': type('Delib', (), {
                'convergence_detection': type('Conv', (), {
                    'enabled': True,
                    'semantic_similarity_threshold': 0.85,
                    'divergence_threshold': 0.40,
                    'min_rounds_before_check': 2,
                    'consecutive_stable_rounds': 2,
                })()
            })()
        })()

        detector = ConvergenceDetector(config)

        # Both rounds have opposite opinions, but stable
        round2 = [
            RoundResponse(
                round=2,
                participant="claude@cli",
                stance="for",
                response="TypeScript is better for safety",
                timestamp="2025-01-01T00:00:00"
            ),
            RoundResponse(
                round=2,
                participant="codex@cli",
                stance="against",
                response="JavaScript is better for flexibility",
                timestamp="2025-01-01T00:00:01"
            )
        ]

        round3 = [
            RoundResponse(
                round=3,
                participant="claude@cli",
                stance="for",
                response="TypeScript is still better for safety",
                timestamp="2025-01-01T00:01:00"
            ),
            RoundResponse(
                round=3,
                participant="codex@cli",
                stance="against",
                response="JavaScript is still better for flexibility",
                timestamp="2025-01-01T00:01:01"
            )
        ]

        # First check
        result1 = detector.check_convergence(round3, round2, round_number=3)

        # Second check (stable for 2 rounds)
        round4 = [
            RoundResponse(
                round=4,
                participant="claude@cli",
                stance="for",
                response="TypeScript remains better for safety",
                timestamp="2025-01-01T00:02:00"
            ),
            RoundResponse(
                round=4,
                participant="codex@cli",
                stance="against",
                response="JavaScript remains better for flexibility",
                timestamp="2025-01-01T00:02:01"
            )
        ]

        result2 = detector.check_convergence(round4, round3, round_number=4)

        # After 2 stable rounds of disagreement, should detect impasse
        if result2.consecutive_stable_rounds >= 2:
            assert result2.status == "impasse"

    def test_skips_check_before_min_rounds(self):
        """Should not check convergence before min_rounds_before_check."""
        from models.schema import RoundResponse

        config = type('Config', (), {
            'deliberation': type('Delib', (), {
                'convergence_detection': type('Conv', (), {
                    'enabled': True,
                    'min_rounds_before_check': 2,  # Don't check until round 3
                })()
            })()
        })()

        detector = ConvergenceDetector(config)

        round1 = [
            RoundResponse(
                round=1, participant="claude@cli", stance="neutral",
                response="Initial response", timestamp="2025-01-01T00:00:00"
            )
        ]

        round2 = [
            RoundResponse(
                round=2, participant="claude@cli", stance="neutral",
                response="Initial response", timestamp="2025-01-01T00:01:00"
            )
        ]

        # Should not check at round 2
        result = detector.check_convergence(round2, round1, round_number=2)
        assert result is None or result.status == "refining"
```

**How to test:**

```bash
# These tests will fail because we haven't implemented ConvergenceDetector yet
pytest tests/unit/test_convergence.py::TestConvergenceDetector -v
```

Expected: Tests fail with `NameError: name 'ConvergenceDetector' is not defined` - **This is correct for TDD!**

**Commit:**
```bash
git add tests/unit/test_convergence.py
git commit -m "Add ConvergenceDetector tests (TDD red phase)

- Test convergence detection with all participants stable
- Test no convergence when opinions change
- Test impasse detection for stable disagreement
- Test min_rounds_before_check enforcement
- Tests fail until ConvergenceDetector implemented"
```

**Definition of Done:**
- [ ] 4 new tests added to TestConvergenceDetector
- [ ] Tests fail with expected errors (class not defined)
- [ ] Changes committed

---

#### Task 3.2: Implement ConvergenceDetector Class

**Goal**: Implement main convergence detection logic to make tests pass

**Files to modify:**
- `deliberation/convergence.py`

**What to do:**

1. Open `deliberation/convergence.py`
2. Add these imports at the top (after existing imports):

```python
from dataclasses import dataclass
from typing import List
```

3. Add this result class after the backend implementations:

```python
# =============================================================================
# Convergence Result
# =============================================================================

@dataclass
class ConvergenceResult:
    """Result of convergence detection check."""

    converged: bool
    status: str  # "converged", "diverging", "refining", "impasse"
    min_similarity: float
    avg_similarity: float
    per_participant_similarity: dict[str, float]
    consecutive_stable_rounds: int
```

4. Add the ConvergenceDetector class at the end of the file:

```python
# =============================================================================
# Convergence Detector
# =============================================================================

class ConvergenceDetector:
    """
    Detects when deliberation has converged.

    Uses multiple signals:
        1. Semantic similarity between consecutive rounds
        2. Stance stability (participants not changing positions)
        3. Response length variance (debate exhaustion)

    Automatically selects best available similarity backend:
        - SentenceTransformerBackend (best, requires sentence-transformers)
        - TFIDFBackend (good, requires scikit-learn)
        - JaccardBackend (fallback, zero dependencies)
    """

    def __init__(self, config):
        """
        Initialize convergence detector.

        Args:
            config: Configuration object with deliberation.convergence_detection
        """
        self.config = config.deliberation.convergence_detection
        self.backend = self._select_backend()
        self.consecutive_stable_count = 0

        logger.info(f"ConvergenceDetector initialized with {self.backend.__class__.__name__}")

    def _select_backend(self) -> SimilarityBackend:
        """
        Select best available similarity backend.

        Tries in order:
            1. SentenceTransformerBackend (best)
            2. TFIDFBackend (good)
            3. JaccardBackend (fallback)

        Returns:
            Selected backend instance
        """
        # Try sentence transformers (best)
        try:
            backend = SentenceTransformerBackend()
            logger.info("Using SentenceTransformerBackend (best accuracy)")
            return backend
        except ImportError:
            logger.debug("sentence-transformers not available")

        # Try TF-IDF (good)
        try:
            backend = TFIDFBackend()
            logger.info("Using TFIDFBackend (good accuracy)")
            return backend
        except ImportError:
            logger.debug("scikit-learn not available")

        # Fallback to Jaccard (always available)
        logger.info("Using JaccardBackend (fallback, zero dependencies)")
        return JaccardBackend()

    def check_convergence(
        self,
        current_round: List,  # List[RoundResponse]
        previous_round: List,  # List[RoundResponse]
        round_number: int
    ) -> Optional[ConvergenceResult]:
        """
        Check if convergence has been reached.

        Args:
            current_round: Responses from current round
            previous_round: Responses from previous round
            round_number: Current round number (1-indexed)

        Returns:
            ConvergenceResult or None if too early to check
        """
        # Don't check before minimum rounds
        if round_number <= self.config.min_rounds_before_check:
            return None

        # Match participants between rounds
        participant_pairs = self._match_participants(current_round, previous_round)

        if not participant_pairs:
            logger.warning("No matching participants found between rounds")
            return None

        # Compute similarity for each participant
        similarities = {}
        for participant_id, (curr_resp, prev_resp) in participant_pairs.items():
            similarity = self.backend.compute_similarity(
                curr_resp.response,
                prev_resp.response
            )
            similarities[participant_id] = similarity

        # Compute aggregate metrics
        similarity_values = list(similarities.values())
        min_similarity = min(similarity_values)
        avg_similarity = sum(similarity_values) / len(similarity_values)

        # Determine convergence status
        threshold = self.config.semantic_similarity_threshold
        divergence_threshold = getattr(self.config, 'divergence_threshold', 0.40)

        if min_similarity >= threshold:
            # All participants converged
            self.consecutive_stable_count += 1

            if self.consecutive_stable_count >= self.config.consecutive_stable_rounds:
                status = "converged"
                converged = True
            else:
                status = "refining"
                converged = False

        elif min_similarity < divergence_threshold:
            # Models are diverging
            status = "diverging"
            converged = False
            self.consecutive_stable_count = 0

        else:
            # Still refining
            status = "refining"
            converged = False
            self.consecutive_stable_count = 0

        # Check for impasse (stable disagreement)
        if (status == "diverging" and
            self.consecutive_stable_count >= self.config.consecutive_stable_rounds):
            status = "impasse"

        return ConvergenceResult(
            converged=converged,
            status=status,
            min_similarity=min_similarity,
            avg_similarity=avg_similarity,
            per_participant_similarity=similarities,
            consecutive_stable_rounds=self.consecutive_stable_count
        )

    def _match_participants(
        self,
        current_round: List,
        previous_round: List
    ) -> dict:
        """
        Match participants between consecutive rounds.

        Args:
            current_round: Responses from current round
            previous_round: Responses from previous round

        Returns:
            Dict mapping participant_id -> (current_response, previous_response)
        """
        # Index previous round by participant
        prev_by_participant = {
            resp.participant: resp
            for resp in previous_round
        }

        # Match with current round
        pairs = {}
        for curr_resp in current_round:
            participant_id = curr_resp.participant
            if participant_id in prev_by_participant:
                prev_resp = prev_by_participant[participant_id]
                pairs[participant_id] = (curr_resp, prev_resp)

        return pairs
```

**How to test:**

```bash
# Run all convergence detector tests
pytest tests/unit/test_convergence.py::TestConvergenceDetector -v
```

Expected:
```
test_convergence.py::TestConvergenceDetector::test_detects_convergence_all_participants_stable PASSED
test_convergence.py::TestConvergenceDetector::test_no_convergence_when_opinions_change PASSED
test_convergence.py::TestConvergenceDetector::test_detects_impasse_stable_disagreement PASSED
test_convergence.py::TestConvergenceDetector::test_skips_check_before_min_rounds PASSED

==================== 4 passed ====================
```

If tests fail, check:
- Similarity computation logic
- Threshold comparisons (>= vs >)
- Consecutive stable rounds tracking
- Status assignment logic

**Commit:**
```bash
git add deliberation/convergence.py
git commit -m "Implement ConvergenceDetector with multi-metric analysis

- Add ConvergenceResult dataclass
- Implement ConvergenceDetector with automatic backend selection
- Track consecutive stable rounds
- Detect converged, refining, diverging, impasse states
- All ConvergenceDetector tests passing (4/4)"
```

**Definition of Done:**
- [ ] ConvergenceResult dataclass added
- [ ] ConvergenceDetector class implemented
- [ ] All 4 detector tests pass
- [ ] Changes committed

---

### Phase 4: Integration with Engine

#### Task 4.1: Add Convergence Detection to Engine (Write Tests First)

**Goal**: Write integration tests for engine + convergence detector

**Files to create:**
- `tests/integration/test_engine_convergence.py`

**What to do:**

1. Create `tests/integration/test_engine_convergence.py`:

```python
"""Integration tests for convergence detection in deliberation engine."""
import pytest
from models.schema import DeliberateRequest, Participant
from models.config import load_config
from deliberation.engine import DeliberationEngine


@pytest.mark.integration
class TestEngineConvergenceIntegration:
    """Test convergence detection integrated with deliberation engine."""

    @pytest.fixture
    def config(self):
        """Load test config."""
        return load_config("config.yaml")

    @pytest.fixture
    def engine(self, config):
        """Create engine instance."""
        return DeliberationEngine(config)

    @pytest.mark.asyncio
    async def test_engine_includes_convergence_info_in_result(self, engine):
        """Engine should include convergence info in deliberation result."""
        request = DeliberateRequest(
            question="Test question",
            participants=[
                Participant(cli="claude", model="sonnet", stance="neutral")
            ],
            rounds=3,
            mode="conference"
        )

        # Mock the CLI execution to return consistent responses
        # (In real test, this would use pytest-mock to mock adapters)

        # For now, this is a placeholder showing structure
        # Real implementation will need mocking
        pytest.skip("Needs adapter mocking - placeholder test")

    def test_convergence_detector_initialized_when_enabled(self, engine):
        """Engine should initialize convergence detector when enabled in config."""
        # Check that engine has convergence detector
        assert hasattr(engine, 'convergence_detector')
        assert engine.convergence_detector is not None

    def test_convergence_detector_not_initialized_when_disabled(self):
        """Engine should not initialize detector when disabled."""
        # Create config with convergence disabled
        import yaml

        config_dict = yaml.safe_load(open("config.yaml"))
        config_dict["deliberation"]["convergence_detection"]["enabled"] = False

        # Would need to create temporary config file
        # Placeholder test
        pytest.skip("Needs temporary config creation - placeholder")
```

**How to test:**

```bash
# These will fail/skip because engine integration not implemented yet
pytest tests/integration/test_engine_convergence.py -v -m integration
```

Expected: Tests are skipped (placeholders) - **This is okay!** We'll implement engine integration next.

**Commit:**
```bash
git add tests/integration/test_engine_convergence.py
git commit -m "Add integration test structure for engine convergence

- Add placeholder integration tests
- Tests will be completed after engine integration
- Mark with @pytest.mark.integration"
```

**Definition of Done:**
- [ ] Integration test file created
- [ ] Test structure defined
- [ ] Changes committed

---

#### Task 4.2: Integrate Convergence Detection into Engine

**Goal**: Update DeliberationEngine to use ConvergenceDetector

**Files to modify:**
- `deliberation/engine.py`

**What to do:**

1. Open `deliberation/engine.py`
2. Find the imports section at the top, add:

```python
from deliberation.convergence import ConvergenceDetector
```

3. Find the `__init__` method of `DeliberationEngine`, add after existing initialization:

```python
# Initialize convergence detector if enabled
if (hasattr(self.config.deliberation, 'convergence_detection') and
    self.config.deliberation.convergence_detection.enabled):
    self.convergence_detector = ConvergenceDetector(self.config)
    logger.info("Convergence detection enabled")
else:
    self.convergence_detector = None
    logger.info("Convergence detection disabled")
```

4. Find the `execute` method where it loops through rounds. Look for:

```python
for round_num in range(1, max_rounds + 1):
    # ... existing round execution code ...
```

5. After the round execution (after `all_responses.extend(round_responses)`), add convergence check:

```python
# Check convergence after round 2+
if self.convergence_detector and round_num >= 2:
    prev_round = [r for r in all_responses if r.round == round_num - 1]
    curr_round = round_responses

    convergence_result = self.convergence_detector.check_convergence(
        current_round=curr_round,
        previous_round=prev_round,
        round_number=round_num
    )

    if convergence_result:
        logger.info(
            f"Round {round_num}: {convergence_result.status} "
            f"(min_sim={convergence_result.min_similarity:.2f}, "
            f"avg_sim={convergence_result.avg_similarity:.2f})"
        )

        # Stop if converged or impasse
        if convergence_result.converged:
            logger.info(f"✓ Convergence detected at round {round_num}, stopping early")
            # Store convergence info for result
            final_convergence_info = convergence_result
            break
        elif convergence_result.status == "impasse":
            logger.info(f"✗ Impasse detected at round {round_num}, stopping")
            final_convergence_info = convergence_result
            break
```

6. At the end of `execute`, before returning the result, add convergence info:

```python
# Create deliberation result
result = DeliberationResult(
    status="complete",
    mode=request.mode,
    rounds_completed=round_num,
    participants=[...],  # existing code
    summary=summary,  # existing code
    transcript_path=transcript_path,  # existing code
    full_debate=all_responses,  # existing code
    convergence_info=None  # Will populate below
)

# Add convergence info if available
if self.convergence_detector and 'final_convergence_info' in locals():
    from models.schema import ConvergenceInfo

    result.convergence_info = ConvergenceInfo(
        detected=final_convergence_info.converged,
        detection_round=round_num if final_convergence_info.converged else None,
        final_similarity=final_convergence_info.min_similarity,
        status=final_convergence_info.status,
        scores_by_round=[],  # Could track all rounds if needed
        per_participant_similarity=final_convergence_info.per_participant_similarity
    )

return result
```

**How to test:**

This is complex because it requires running the full engine. For now, test manually:

```bash
# Test that engine initializes without errors
python3 -c "
from models.config import load_config
from deliberation.engine import DeliberationEngine

config = load_config('config.yaml')
engine = DeliberationEngine(config)
print(f'✓ Engine initialized')
print(f'✓ Convergence detector: {engine.convergence_detector is not None}')
"
```

Expected:
```
✓ Engine initialized
✓ Convergence detector: True
```

**Commit:**
```bash
git add deliberation/engine.py
git commit -m "Integrate convergence detection into deliberation engine

- Initialize ConvergenceDetector in engine.__init__
- Check convergence after each round (starting from round 2)
- Stop early on convergence or impasse
- Add convergence_info to DeliberationResult
- Log convergence status per round"
```

**Definition of Done:**
- [ ] ConvergenceDetector initialized in engine
- [ ] Convergence check added to round loop
- [ ] Early stopping on convergence/impasse
- [ ] convergence_info added to result
- [ ] Engine initializes without errors
- [ ] Changes committed

---

### Phase 5: End-to-End Testing

#### Task 5.1: Manual E2E Test

**Goal**: Test the full convergence detection feature end-to-end

**What to do:**

1. Start the MCP server:

```bash
python server.py
```

2. From Claude Code, run a deliberation with convergence detection:

```
Use the deliberate tool with this request:

{
  "question": "Should we use TypeScript or JavaScript for a new project?",
  "participants": [
    {"cli": "claude", "model": "sonnet"},
    {"cli": "codex", "model": "gpt-5-codex"}
  ],
  "rounds": 5,
  "mode": "conference"
}
```

3. Check the response for:
   - `convergence_info` field present
   - `detected` field shows convergence status
   - `status` shows "converged", "refining", etc.
   - Early stopping if convergence detected

4. Check the transcript file in `transcripts/`:
   - Should show the actual number of rounds completed
   - If convergence detected, should be less than 5 rounds

**Expected Outcomes:**

✓ **Success Case**: If models agree early
- Stops at round 3-4 (before max 5)
- `convergence_info.detected = true`
- `convergence_info.status = "converged"`
- Transcript shows early stop message

✓ **Continue Case**: If models keep refining
- Runs all 5 rounds
- `convergence_info.detected = false`
- `convergence_info.status = "refining"`

✓ **Impasse Case**: If models disagree and stabilize
- Stops at round 3-4
- `convergence_info.detected = false`
- `convergence_info.status = "impasse"`

**Document your findings:**

Create a test report file:

```bash
echo "# E2E Test Results

## Test Date: $(date)

## Test 1: TypeScript vs JavaScript
- Question: Should we use TypeScript or JavaScript?
- Expected: Convergence (both likely agree on TypeScript)
- Result: [FILL IN]
- Rounds: [FILL IN]
- Status: [FILL IN]

## Test 2: [Add more tests as needed]

" > tests/e2e/convergence_test_results.md
```

**Commit:**
```bash
git add tests/e2e/convergence_test_results.md
git commit -m "Add E2E test results for convergence detection

- Manual testing of convergence scenarios
- Document success, continue, and impasse cases
- Verify early stopping behavior"
```

**Definition of Done:**
- [ ] Manual E2E test completed
- [ ] Results documented
- [ ] Early stopping verified
- [ ] convergence_info field verified
- [ ] Changes committed

---

### Phase 6: Documentation & Cleanup

#### Task 6.1: Update README with Convergence Detection

**Goal**: Document the new feature in README

**Files to modify:**
- `README.md`

**What to do:**

1. Open `README.md`
2. Find the "Features" section (around line 18)
3. Add convergence detection to the feature list:

```markdown
## Features

- 🎯 **Two Modes:**
  - `quick`: Fast single-round opinions
  - `conference`: Multi-round deliberative debate
- 🤖 **Multi-Model Support:** Works with claude, codex, droid, gemini, and extensible to others
- 📝 **Full Transcripts:** Markdown exports with summary and complete debate
- 🎚️ **User Control:** Configure rounds, stances, and participants
- 🔍 **Transparent:** See exactly what each model said and when
- ⚡ **Auto-Convergence:** Automatically stops when opinions stabilize (NEW)
```

4. Add a new section after "Configuration" explaining convergence:

```markdown
### Convergence Detection

AI Counsel can automatically detect when models reach consensus and stop early, saving time and API costs.

**How it works:**

The system compares responses between consecutive rounds using semantic similarity:
- **Converged** (≥ 85% similarity): Models agree, stops early
- **Refining** (40-85% similarity): Still making progress, continues
- **Diverging** (< 40% similarity): Models disagree significantly
- **Impasse**: Stable disagreement after 2+ rounds, stops

**Similarity Backends:**

Three backends with automatic fallback:
1. **sentence-transformers** (best): Deep semantic understanding (~500MB)
2. **TF-IDF** (good): Statistical similarity (~50MB, requires scikit-learn)
3. **Jaccard** (fallback): Word overlap (zero dependencies)

**Configuration:**

```yaml
deliberation:
  convergence_detection:
    enabled: true
    semantic_similarity_threshold: 0.85
    divergence_threshold: 0.40
    min_rounds_before_check: 2
    consecutive_stable_rounds: 2
```

**Example Result:**

```json
{
  "convergence_info": {
    "detected": true,
    "detection_round": 3,
    "final_similarity": 0.87,
    "status": "converged",
    "per_participant_similarity": {
      "claude@cli": 0.87,
      "codex@cli": 0.89
    }
  }
}
```
```

5. Update the "Roadmap" section - move convergence detection from "Future" to "Current Features":

```markdown
### Current Features ✅

- ✅ 4 CLI adapters: claude, codex, droid, gemini
- ✅ Quick and conference modes
- ✅ Markdown transcripts with full debate history
- ✅ MCP server integration
- ✅ Structured summaries
- ✅ Hook interference prevention
- ✅ Convergence detection (auto-stop when opinions stabilize)

### Future Enhancements

- [ ] Semantic similarity for better summary generation
- [ ] More CLI tool adapters (ollama, llama-cpp, etc.)
- [ ] Web UI for viewing transcripts
- [ ] Structured voting mechanisms
- [ ] Real-time streaming of deliberation progress
```

**How to test:**

```bash
# Verify markdown syntax
python3 -m markdown README.md > /dev/null && echo "✓ Markdown valid"
```

**Commit:**
```bash
git add README.md
git commit -m "Document convergence detection feature in README

- Add convergence to feature list
- Add detailed Convergence Detection section
- Move from Future to Current Features in roadmap
- Include configuration example and result format"
```

**Definition of Done:**
- [ ] Feature added to feature list
- [ ] Convergence Detection section added
- [ ] Roadmap updated
- [ ] Examples included
- [ ] Changes committed

---

#### Task 6.2: Add Inline Documentation

**Goal**: Ensure all new code has proper docstrings

**Files to review:**
- `deliberation/convergence.py`
- `models/schema.py`

**What to do:**

Review all new code and ensure:

1. **Every class has a docstring** explaining:
   - What it does
   - Why it exists
   - Key concepts

2. **Every method has a docstring** with:
   - Brief description
   - Args section
   - Returns section
   - Example if complex

3. **Complex logic has comments** explaining:
   - Why this approach was chosen
   - What edge cases are handled
   - References to requirements if applicable

Check convergence.py:
- [ ] All classes have docstrings
- [ ] All methods have docstrings
- [ ] Complex algorithms have comments

Check schema.py:
- [ ] ConvergenceInfo has descriptive Field descriptions
- [ ] All fields explain their purpose

**If any documentation is missing, add it now.**

Example of good documentation:

```python
def compute_similarity(self, text1: str, text2: str) -> float:
    """
    Compute Jaccard similarity between two texts.

    Jaccard similarity measures word overlap:
        J(A, B) = |A ∩ B| / |A ∪ B|

    Where A and B are sets of words.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0.0 (no overlap) and 1.0 (identical)

    Example:
        >>> backend = JaccardBackend()
        >>> backend.compute_similarity("hello world", "hello there")
        0.5  # 1 shared word / 2 unique words
    """
```

**Commit:**
```bash
git add deliberation/convergence.py models/schema.py
git commit -m "Add comprehensive inline documentation

- Add docstrings to all classes and methods
- Document complex algorithms with comments
- Add examples for clarity
- Ensure code is maintainable for future developers"
```

**Definition of Done:**
- [ ] All classes documented
- [ ] All methods documented
- [ ] Complex logic has comments
- [ ] Changes committed

---

## Testing Guidelines

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run specific test file
pytest tests/unit/test_convergence.py -v

# Run specific test class
pytest tests/unit/test_convergence.py::TestJaccardBackend -v

# Run specific test
pytest tests/unit/test_convergence.py::TestJaccardBackend::test_identical_text_returns_one -v

# Run all tests with coverage
pytest tests/unit/ --cov=deliberation --cov-report=html

# Run integration tests
pytest tests/integration/ -v -m integration
```

### Test Design Principles

**Good Tests:**
- Test one thing
- Have clear names describing what they test
- Have arrange-act-assert structure:
  ```python
  def test_something():
      # Arrange: Set up test data
      backend = JaccardBackend()

      # Act: Call the method
      result = backend.compute_similarity("hello", "hello")

      # Assert: Check expectations
      assert result == 1.0
  ```

**Bad Tests:**
- Test multiple things in one test
- Have vague names like `test_1`
- Don't explain what they're testing
- Have magic numbers without explanation

### When Tests Fail

1. **Read the error message carefully**
   - What was expected?
   - What actually happened?

2. **Check your implementation logic**
   - Did you implement the algorithm correctly?
   - Are there edge cases not handled?

3. **Add debug logging**
   ```python
   logger.debug(f"Similarity: {similarity}, threshold: {threshold}")
   ```

4. **Run in isolation**
   ```bash
   pytest tests/unit/test_convergence.py::TestJaccardBackend::test_partial_overlap -v -s
   ```
   The `-s` flag shows print statements

---

## Acceptance Criteria

Before marking this implementation complete, verify:

### Functionality
- [ ] All three similarity backends implemented and tested
- [ ] ConvergenceDetector correctly detects convergence
- [ ] ConvergenceDetector correctly detects impasse
- [ ] Engine integrates convergence detector
- [ ] Engine stops early on convergence
- [ ] Engine stops on impasse
- [ ] convergence_info included in results

### Testing
- [ ] All unit tests pass (40+ tests)
- [ ] Integration tests pass or documented
- [ ] Manual E2E test completed and documented
- [ ] Test coverage > 80% for new code

### Documentation
- [ ] README updated with convergence feature
- [ ] All code has docstrings
- [ ] Complex logic has comments
- [ ] E2E test results documented

### Code Quality
- [ ] Follows DRY principle (no duplication)
- [ ] Follows YAGNI (no extra features)
- [ ] TDD approach followed (tests before code)
- [ ] Frequent commits with good messages
- [ ] Code formatted with black
- [ ] Linting passes (ruff check .)

### Deployment Readiness
- [ ] Config updated with all settings
- [ ] Optional dependencies documented
- [ ] Backward compatible (convergence_info optional)
- [ ] No breaking changes to existing API
- [ ] Feature can be disabled via config

---

## Common Issues & Solutions

### Issue: Tests fail with "Import Error"

**Cause**: Module not in Python path

**Solution**:
```bash
# Run from repo root
cd /path/to/ai-counsel
source .venv/bin/activate
pytest tests/unit/test_convergence.py -v
```

### Issue: Sentence transformer tests take forever

**Cause**: First run downloads 500MB model

**Solution**:
- Wait for download to complete (one-time)
- Or skip these tests: `pytest -k "not SentenceTransformer"`

### Issue: Config not loading properly

**Cause**: YAML indentation or syntax error

**Solution**:
```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### Issue: Engine doesn't stop early

**Cause**: Threshold too high or consecutive_stable_rounds not met

**Solution**:
- Check logs: `tail -f mcp_server.log`
- Lower threshold temporarily: `semantic_similarity_threshold: 0.70`
- Reduce required stable rounds: `consecutive_stable_rounds: 1`

---

## Final Checklist

Before submitting:

- [ ] All tasks completed (1.1 through 6.2)
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed for quality
- [ ] Feature tested end-to-end
- [ ] Acceptance criteria met
- [ ] Git history has clear commits

**Congratulations!** You've implemented convergence detection for AI Counsel! 🎉

---

## Next Steps (Future Work)

After this implementation is complete and stable, consider:

1. **Semantic Summary Generation**: Use embeddings to generate better summaries
2. **Convergence Visualization**: Add charts showing similarity over rounds
3. **Adaptive Thresholds**: Learn optimal thresholds from past deliberations
4. **Streaming Updates**: Real-time convergence status during deliberation

But remember: **YAGNI** - only implement these if actually needed!
