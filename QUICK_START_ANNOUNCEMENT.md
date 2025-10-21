# Quick Start: Announce Decision Graph Memory Feature

This guide helps you implement the feature announcement strategy in 10 minutes.

---

## TL;DR - What You Need to Do

✅ **3 Required Changes to README.md** (5 minutes)
✅ **CHANGELOG.md Already Created** (done)
✅ **Documentation Already Exists** (done)

**Result**: Decision Graph Memory feature properly announced and tracked!

---

## Step-by-Step Implementation

### Step 1: Update Features List (2 minutes)

**File**: `/README.md`
**Line**: ~40 (Features section)

**Action**: Add this line before the last bullet (🛡️ Fault Tolerant):

```markdown
- 🧠 **Decision Graph Memory:** Learn from past deliberations (optional, opt-in feature)
```

**How to find it**:
```bash
# Search for the Features section
grep -n "## Features" README.md
```

**Full context** (before):
```markdown
- 🎛️ **Model-Controlled Stopping:** Models decide when to stop deliberating (adaptive rounds)
- 🛡️ **Fault Tolerant:** Individual adapter failures don't halt deliberation—remaining models continue
```

**Full context** (after):
```markdown
- 🎛️ **Model-Controlled Stopping:** Models decide when to stop deliberating (adaptive rounds)
- 🧠 **Decision Graph Memory:** Learn from past deliberations (optional, opt-in feature)
- 🛡️ **Fault Tolerant:** Individual adapter failures don't halt deliberation—remaining models continue
```

---

### Step 2: Update Roadmap Section (2 minutes)

**File**: `/README.md`
**Line**: ~660 (Current Features subsection under Roadmap)

**Action**: Add this line at the end of the "Current Features" list:

```markdown
- ✅ Decision Graph Memory (v1.3.0) - Persistent learning from past deliberations
```

**How to find it**:
```bash
# Search for the Roadmap section
grep -n "### Current Features" README.md
```

**Full context** (before):
```markdown
- ✅ HTTP adapter retry logic with exponential backoff
- ✅ Environment variable substitution for secure API key storage
```

**Full context** (after):
```markdown
- ✅ HTTP adapter retry logic with exponential backoff
- ✅ Environment variable substitution for secure API key storage
- ✅ Decision Graph Memory (v1.3.0) - Persistent learning from past deliberations
```

---

### Step 3: Update Version Badge (1 minute)

**File**: `/README.md`
**Line**: ~794 (Status section at bottom)

**Action**: Change version from `1.2.0` to `1.3.0`:

**Before**:
```markdown
![Version](https://img.shields.io/badge/version-1.2.0-blue)
```

**After**:
```markdown
![Version](https://img.shields.io/badge/version-1.3.0-blue)
```

**How to find it**:
```bash
# Search for the version badge
grep -n "version-" README.md
```

---

### Verification (2 minutes)

Run these commands to verify changes:

```bash
# 1. Check word count (should be ~3340 words)
wc -w README.md

# 2. Verify all links work (check Decision Graph section)
grep -n "docs/decision-graph" README.md

# 3. Check markdown syntax (if you have markdownlint)
# npx markdownlint README.md

# 4. Preview changes
git diff README.md
```

---

## Visual Checklist

- [ ] **Step 1**: Features list updated (line ~40)
  - Found "## Features" section
  - Added 🧠 Decision Graph Memory bullet
  - Placed before 🛡️ Fault Tolerant bullet

- [ ] **Step 2**: Roadmap updated (line ~660)
  - Found "### Current Features ✅" section
  - Added line with v1.3.0 version number
  - Placed at end of list

- [ ] **Step 3**: Version badge updated (line ~794)
  - Found "![Version]" badge
  - Changed 1.2.0 to 1.3.0

- [ ] **Verification**: All checks passed
  - Word count reasonable (~3340)
  - Links work in Decision Graph section
  - Git diff shows only 3 changes

---

## Exact Lines to Change

Use your text editor to make these changes:

### Change 1: Features List
**Location**: Line ~40 (search for "Model-Controlled Stopping")

**Insert this line**:
```markdown
- 🧠 **Decision Graph Memory:** Learn from past deliberations (optional, opt-in feature)
```

**After this line**:
```markdown
- 🎛️ **Model-Controlled Stopping:** Models decide when to stop deliberating (adaptive rounds)
```

---

### Change 2: Roadmap Section
**Location**: Line ~666 (search for "Environment variable substitution")

**Insert this line**:
```markdown
- ✅ Decision Graph Memory (v1.3.0) - Persistent learning from past deliberations
```

**After this line**:
```markdown
- ✅ Environment variable substitution for secure API key storage
```

---

### Change 3: Version Badge
**Location**: Line ~794 (search for "version-1.2.0")

**Replace this**:
```markdown
![Version](https://img.shields.io/badge/version-1.2.0-blue)
```

**With this**:
```markdown
![Version](https://img.shields.io/badge/version-1.3.0-blue)
```

---

## What's Already Done

You don't need to do these—they're already complete:

✅ **CHANGELOG.md Created**
- File: `/CHANGELOG.md`
- Includes v1.3.0 entry with full details
- Follows Keep a Changelog format
- Tracks semantic versioning

✅ **Documentation Exists**
- `/docs/decision-graph/intro.md`
- `/docs/decision-graph/quickstart.md`
- `/docs/decision-graph/configuration.md`
- `/docs/decision-graph/deployment.md`
- `/docs/decision-graph/troubleshooting.md`
- `/docs/decision-graph/migration.md`

✅ **Decision Graph README Section**
- Lines 676-761 in README.md
- Includes hook, examples, config, docs links
- Performance stats included
- No changes needed—already perfect!

✅ **Strategy Documents**
- `/docs/FEATURE_ANNOUNCEMENT_STRATEGY.md` (comprehensive guide)
- `/docs/README_UPDATES.md` (detailed snippets)
- `/docs/FEATURE_ANNOUNCEMENT_TEMPLATE.md` (future features)
- `/docs/ANNOUNCEMENT_SUMMARY.md` (executive summary)

---

## Optional: Condense HTTP Troubleshooting

**Goal**: Save 28 lines in README (reduces word count from 3340 to 3312)

**Time**: 15 minutes

### Step 1: Create New File

**File**: `/docs/troubleshooting/http-adapters.md`

**Content**: Move detailed troubleshooting from README lines 541-577

```bash
mkdir -p docs/troubleshooting
cat > docs/troubleshooting/http-adapters.md << 'EOF'
# HTTP Adapter Troubleshooting

## Ollama

**Not responding:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

## LM Studio

**Connection refused:**
1. Open LM Studio → Local Server tab → Start Server
2. Check port matches config (default: 1234)
3. Ensure model is loaded

## OpenRouter

**Authentication failed:**
```bash
# Verify API key is set
echo $OPENROUTER_API_KEY

# Test API key
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Common Issues

**Timeout errors:**
- Increase `timeout` in config (especially for large models)
- Larger models may need 180-300 seconds
- Check network latency

**Rate limiting (429 errors):**
- HTTP adapters automatically retry with exponential backoff
- Check provider rate limits
- Adjust `max_retries` in config

**Model not found:**
- Verify model name matches provider's format
- Check provider documentation for exact model IDs
- Some providers require namespace (e.g., `anthropic/claude-3.5-sonnet`)

**Network errors:**
- Check firewall settings
- Verify proxy configuration
- Test with `curl` to isolate issue
EOF
```

### Step 2: Update README

**Replace** lines 541-577 with this condensed version:

```markdown
#### Troubleshooting HTTP Adapters

Common issues and solutions:
- **Connection refused**: Verify service is running and port matches config
- **Authentication failed**: Check environment variables are set (`echo $OPENROUTER_API_KEY`)
- **Timeouts**: Increase timeout values for large models (180-300s recommended)
- **Rate limiting (429)**: Built-in exponential backoff handles retries automatically

For detailed troubleshooting, see [docs/troubleshooting/http-adapters.md](docs/troubleshooting/http-adapters.md)
```

**Savings**: 36 lines → 8 lines = **28 lines saved**

---

## After You're Done

### Commit Changes

```bash
# Stage changes
git add README.md CHANGELOG.md

# Commit with descriptive message
git commit -m "docs: announce Decision Graph Memory v1.3.0

- Add Decision Graph to Features list
- Update Roadmap with v1.3.0 release
- Update version badge to 1.3.0
- Add comprehensive CHANGELOG entry

Includes:
- Pattern recognition via semantic similarity
- Background async processing (<450ms p95)
- Two-tier caching (70%+ hit rate)
- Export formats: JSON, GraphML, DOT, Markdown
- Complete documentation in /docs/decision-graph/

🤖 Generated with Claude Code"
```

### Create GitHub Release (Optional)

```bash
# Tag the release
git tag v1.3.0 -a -m "Release v1.3.0: Decision Graph Memory"

# Push tag
git push origin v1.3.0

# Create release via GitHub CLI (if installed)
gh release create v1.3.0 \
  --title "v1.3.0 - Decision Graph Memory" \
  --notes "$(cat CHANGELOG.md | sed -n '/## \[1.3.0\]/,/## \[1.2.0\]/p' | head -n -2)"
```

---

## For Future Features

Next time you ship a major feature, use this workflow:

1. **Before coding**: Create `/docs/[feature-name]/` directory structure
2. **During development**: Write docs as you build
3. **Before release**: Use `/docs/FEATURE_ANNOUNCEMENT_TEMPLATE.md`
4. **At release**: Follow this Quick Start guide with your feature name

**Template Location**: `/docs/FEATURE_ANNOUNCEMENT_TEMPLATE.md`

---

## Need Help?

- **Strategy rationale**: Read `/docs/FEATURE_ANNOUNCEMENT_STRATEGY.md`
- **Detailed snippets**: Check `/docs/README_UPDATES.md`
- **Future features**: Use `/docs/FEATURE_ANNOUNCEMENT_TEMPLATE.md`
- **Executive summary**: See `/docs/ANNOUNCEMENT_SUMMARY.md`

---

## Success!

After completing these steps, you'll have:

✅ Decision Graph Memory announced in Features list
✅ Release tracked in Roadmap (v1.3.0)
✅ Version badge updated
✅ CHANGELOG entry for historical tracking
✅ Comprehensive documentation linked
✅ Repeatable process for future features

**Estimated Time**: 5 minutes (required) + 15 minutes (optional condensation) = **20 minutes total**

🎉 **Your feature announcement is complete and production-ready!**
