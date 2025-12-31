# LESSONS LEARNED — AI-COUNSEL

## Format

```markdown
### YYYY-MM-DD: Short Title
**Problem:** What went wrong
**Root Cause:** Why it happened
**Lesson:** What to do/avoid next time
```

---

## Entries

### 2025-12-31: Activity-Based Timeout vs Fixed Timeout
**Problem:** CLI adapters killed processes that were still generating output, just slowly (reasoning models think for long periods)
**Root Cause:** `communicate()` timeout waits for process completion, not for activity. A model generating tokens every few seconds would be killed after fixed timeout.
**Lesson:** Use activity-based timeout — reset timer on each output chunk. Only kill process if no activity for N seconds (default 120s).

### 2025-12-31: Responses API Detection
**Problem:** OpenAI o1/o3/o4 models require Responses API, not Chat Completions API
**Root Cause:** Different API endpoints for reasoning vs chat models
**Lesson:** Use `responses_api_prefixes` config to detect which models need Responses API. Check model name prefix before choosing API method.
