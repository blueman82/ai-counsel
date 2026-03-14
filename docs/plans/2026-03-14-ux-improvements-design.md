# AI Counsel UX Improvements — Design Document

**Status:** Approved
**Date:** 2026-03-14

---

## Goal

Four quality-of-life improvements to make ai-counsel easier to use day-to-day: preset panels, file context injection, auto-open HTML reports, and shorter filenames.

---

## Feature 1: Preset Panels

### Problem
Every deliberation requires specifying participants, mode, and rounds inline. For repeated use cases (architecture review, security audit, quick check), this is tedious.

### Design
A `panels.yaml` file at the project root defines named participant configurations. The `deliberate` MCP tool gets a new optional `panel` parameter.

**panels.yaml format:**
```yaml
panels:
  architecture-review:
    description: "Architecture and design review"
    participants:
      - cli: claude
        model: sonnet
      - cli: openrouter
        model: google/gemini-2.5-flash
      - cli: openrouter
        model: google/gemma-3-27b-it:free
    mode: conference
    rounds: 2

  security-audit:
    description: "Security-focused review"
    participants:
      - cli: claude
        model: opus
        reasoning_effort: high
      - cli: openrouter
        model: x-ai/grok-4
      - cli: openrouter
        model: deepseek/deepseek-r1
    mode: conference
    rounds: 3

  quick-check:
    description: "Fast 2-model sanity check"
    participants:
      - cli: claude
        model: sonnet
      - cli: openrouter
        model: google/gemini-2.5-flash
    mode: quick
    rounds: 1
```

**Usage:** `deliberate(question="...", panel="architecture-review", working_directory="...")`

**Behavior:**
- If `panel` is provided, participants/mode/rounds are loaded from the panel definition
- Inline participants override panel participants if both are specified
- Panel not found = clear error with list of available panels
- `list_models` tool extended to also list available panels

### Files Changed
- New: `panels.yaml`
- Modified: `server.py` (load panels, add `panel` parameter to schema)
- Modified: `models/schema.py` (add optional `panel` field to `DeliberateRequest`)

---

## Feature 2: Context Injection from Files

### Problem
Long prompts must include file contents inline (like pasting 4 docs into the prompt today). This is error-prone and wastes tokens on formatting.

### Design
The `deliberate` tool gets a new optional `files` parameter — an array of file paths or glob patterns. The engine resolves paths, reads contents, and prepends them to the prompt.

**Usage:**
```
deliberate(
  question="Review these architecture docs",
  files=["docs/plans/2026-03-12-monorepo-*.md", "TRACKING.md"],
  panel="architecture-review",
  working_directory="c:/Dev/AutoSweep"
)
```

**Injected format:**
```
--- File: docs/plans/2026-03-12-monorepo-design-v2.md ---
<contents>

--- File: TRACKING.md ---
<contents>

---

Review these architecture docs
```

**Safeguards:**
- Paths resolved relative to `working_directory`
- Max total injected content: 500KB (configurable via `config.yaml` `deliberation.max_file_injection_bytes`)
- Binary files skipped with warning
- Non-existent paths logged as warnings, not failures
- Globs use `pathlib.glob()`, respecting existing `tool_security.exclude_patterns`

### Files Changed
- Modified: `server.py` (resolve files before building request)
- Modified: `deliberation/engine.py` (prepend file contents to prompt)
- Modified: `models/schema.py` (add optional `files` field)
- Modified: `config.yaml` (add `max_file_injection_bytes` setting)

---

## Feature 3: Auto-Open HTML Reports

### Problem
After deliberation, the HTML report is saved but you have to manually navigate to it.

### Design
After saving the HTML to `results/`, open it in the default browser via `webbrowser.open()`.

**Configurable in config.yaml:**
```yaml
results:
  auto_open_html: true
```

Default: `true`.

### Files Changed
- Modified: `server.py` (add `webbrowser.open()` after HTML save)
- Modified: `config.yaml` (add `results.auto_open_html` setting)

---

## Feature 4: Shorter Filenames

### Problem
Current filenames are the first 50 chars of the question verbatim, producing unwieldy names like `20260314_085305_You_are_reviewing_four_architecture_documents_for.html`.

### Design
Auto-generate a 3-5 word slug from the question:

1. Strip common filler words (stop words: "review", "these", "the", "for", "and", "documents", "please", "can", "you", "should", "we", "is", "are", "what", "how", etc.)
2. Take the first 4-5 meaningful words
3. Slugify (lowercase, hyphens, no special chars)
4. Prepend timestamp: `{YYYYMMDD}_{HHMMSS}_{slug}`

**Examples:**
| Question | New filename |
|---|---|
| "Review these architecture docs for risks" | `20260314_085305_architecture-docs-risks` |
| "Should we use Redis or Memcached for caching?" | `20260314_085305_redis-memcached-caching` |

**Applied to:** `results/` (JSON + HTML) and `transcripts/` (markdown).

Implemented as a shared utility function `generate_slug(question)` used by both `TranscriptManager.save()` and the auto-save block in `server.py`.

### Files Changed
- New: utility function in `deliberation/transcript.py` or `scripts/render_result.py`
- Modified: `deliberation/transcript.py` (use new slug function)
- Modified: `server.py` (use new slug function for results/)
