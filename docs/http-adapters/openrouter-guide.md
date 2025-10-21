# OpenRouter Guide

Access 200+ AI models through a single unified API with OpenRouter—the cloud alternative to local models.

## Table of Contents

- [What is OpenRouter?](#what-is-openrouter)
- [When to Use OpenRouter](#when-to-use-openrouter)
- [Setup and Authentication](#setup-and-authentication)
- [Available Models](#available-models)
- [Pricing Comparison](#pricing-comparison)
- [Complete Example](#complete-example)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## What is OpenRouter?

**OpenRouter** is a unified API gateway that provides access to 200+ AI models from multiple providers (OpenAI, Anthropic, Meta, Google, Mistral, and more) through a single OpenAI-compatible interface.

### Key Features

- **Unified API** (one integration, 200+ models)
- **Competitive pricing** (often cheaper than direct provider APIs)
- **Model fallbacks** (automatic retry with alternative models)
- **Usage tracking** (detailed analytics and cost monitoring)
- **Pay-per-use** (no subscriptions or minimums)
- **Rate limit pooling** (shared limits across models)

### OpenRouter vs Direct Provider APIs

| Feature | OpenRouter | Direct (Claude/GPT) |
|---------|------------|---------------------|
| API integration | 1 integration | Multiple integrations |
| Model access | 200+ models | 1 provider's models |
| Pricing | Often cheaper | Standard pricing |
| Billing | Single invoice | Multiple invoices |
| Fallbacks | Automatic | Manual implementation |
| Rate limits | Pooled across models | Per-provider limits |

---

## When to Use OpenRouter

### Choose OpenRouter When:

✅ **Access to premium models needed** (GPT-4, Claude Opus, Gemini Pro)
✅ **Multiple providers desired** (compare Claude vs GPT in same deliberation)
✅ **No local hardware** (cloud-native deployment, no GPU required)
✅ **Model diversity** (want to test many models without multiple API keys)
✅ **Cost optimization** (leverage cheaper alternatives like Llama 3.1 70B at $0.30/M tokens)
✅ **Fallback strategy** (automatic retry with alternative models on failure)

### Choose Local Models (Ollama/LM Studio) When:

✅ **Zero cost preferred** (no per-request charges)
✅ **Privacy critical** (data must stay on-premise)
✅ **High volume** (thousands of requests, local is cheaper long-term)
✅ **Offline capability** (no internet dependency)

### Hybrid Approach (Recommended)

**Best of both worlds:**
- Use local models (Ollama) for exploratory rounds (cheap, fast)
- Use OpenRouter for final validation (access to GPT-4, Claude Opus)

**Example cost:**
- 5 rounds, 3 participants
- Rounds 1-4: Local Ollama (Llama 3) → $0
- Round 5: OpenRouter (Claude Sonnet) → $0.50
- **Total:** $0.50 (vs $2.50 for 5 rounds of Claude)

---

## Setup and Authentication

### Step 1: Create OpenRouter Account

1. Visit https://openrouter.ai/
2. Click **Sign In** → Sign up with GitHub, Google, or email
3. Confirm email (check spam folder)

### Step 2: Generate API Key

1. After login, go to https://openrouter.ai/keys
2. Click **Create Key**
3. Name: "AI Counsel" (for tracking)
4. Permissions: Default (full access)
5. Click **Create**
6. **Copy API key** (starts with `sk-or-v1-`)

**Security warning:** Treat API key like a password. Never commit to git or share publicly.

### Step 3: Add Credits (Optional)

OpenRouter uses prepaid credits (no subscription):

1. Go to https://openrouter.ai/credits
2. Click **Add Credits**
3. Options: $5, $10, $20, $50, $100 (no minimum)
4. Pay via credit card or crypto
5. Credits never expire

**Recommendation:** Start with $5-10 to test, add more as needed.

**Free tier:** OpenRouter offers limited free tier for testing (varies by model).

### Step 4: Set Environment Variable

**macOS/Linux:**
```bash
# Set for current session
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENROUTER_API_KEY="sk-or-v1-your-key-here"' >> ~/.zshrc
source ~/.zshrc

# Verify
echo $OPENROUTER_API_KEY
# Should output your key
```

**Windows (PowerShell):**
```powershell
# Set for current session
$env:OPENROUTER_API_KEY = "sk-or-v1-your-key-here"

# Permanent (system-wide)
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-your-key-here", "User")

# Verify
echo $env:OPENROUTER_API_KEY
```

### Step 5: Configure AI Counsel

Your `config.yaml` already includes OpenRouter support:

```yaml
# config.yaml (already configured!)
adapters:
  openrouter:
    type: http
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"  # Environment variable substitution
    timeout: 90
    max_retries: 3
```

**Important:** `${OPENROUTER_API_KEY}` automatically reads from environment variable.

### Step 6: Test API Key

```bash
# Test authentication
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Should return:
# {
#   "data": {
#     "label": "AI Counsel",
#     "limit": null,
#     "usage": 0.0
#   }
# }
```

**If error:** Verify environment variable is set correctly.

---

## Available Models

OpenRouter provides access to 200+ models. Here are top picks for AI Counsel deliberations.

### Premium Models (Best Quality)

| Model | Provider | Cost/M Tokens | Use Case |
|-------|----------|---------------|----------|
| **claude-3.5-sonnet** | Anthropic | $3 input, $15 output | Best overall reasoning |
| **gpt-4-turbo** | OpenAI | $10 input, $30 output | Maximum quality |
| **gemini-pro-1.5** | Google | $1.25 input, $5 output | Long context (1M tokens) |
| **claude-opus-4** | Anthropic | $15 input, $75 output | Highest quality (expensive) |

### Budget Models (Good Quality)

| Model | Provider | Cost/M Tokens | Use Case |
|-------|----------|---------------|----------|
| **llama-3.1-70b-instruct** | Meta | $0.30 input/output | Best budget option |
| **mistral-large** | Mistral | $4 input, $12 output | French/code tasks |
| **qwen-2.5-72b-instruct** | Qwen | $0.35 input/output | Multilingual |
| **gemma-2-27b-it** | Google | $0.27 input/output | Very cheap |

### Free Models (Limited Availability)

| Model | Provider | Cost | Notes |
|-------|----------|------|-------|
| **llama-3.1-8b-instruct:free** | Meta | Free | Rate limited |
| **mistral-7b-instruct:free** | Mistral | Free | Rate limited |

**Note:** Free models have strict rate limits (5-10 req/min). Use for testing only.

### Specialized Models

| Model | Provider | Specialty |
|-------|----------|-----------|
| **codellama-70b-instruct** | Meta | Code generation |
| **gpt-4-vision-preview** | OpenAI | Image understanding |
| **dall-e-3** | OpenAI | Image generation |

### Browse All Models

```bash
# List all available models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | {id: .id, pricing: .pricing}'

# Or visit: https://openrouter.ai/models
```

---

## Pricing Comparison

### Scenario: 30 Deliberations/Month, 3 Participants, 5 Rounds

**Assumptions:**
- 500 tokens prompt/round, 1,000 tokens response/round
- Total: 67,500 tokens/deliberation = 2,025,000 tokens/month

#### Option 1: Premium (Claude Sonnet 3.5)

| Item | Cost |
|------|------|
| Input tokens (1,012,500 @ $3/M) | $3.04 |
| Output tokens (1,012,500 @ $15/M) | $15.19 |
| **Monthly total** | **$18.23** |

#### Option 2: Budget (Llama 3.1 70B)

| Item | Cost |
|------|------|
| Input tokens (1,012,500 @ $0.30/M) | $0.30 |
| Output tokens (1,012,500 @ $0.30/M) | $0.30 |
| **Monthly total** | **$0.60** |
| **Savings vs Claude** | **$17.63 (97%)** |

#### Option 3: Hybrid (2x Llama 70B + 1x Claude)

| Item | Cost |
|------|------|
| Llama 70B (2/3 of load) | $0.40 |
| Claude Sonnet (1/3 of load) | $6.08 |
| **Monthly total** | **$6.48** |
| **Savings vs all-Claude** | **$11.75 (64%)** |

#### Option 4: Local + OpenRouter Fallback

| Item | Cost |
|------|------|
| Ollama local (rounds 1-4) | $0.00 |
| Claude Sonnet (round 5 only) | $3.65 |
| **Monthly total** | **$3.65** |
| **Savings vs all-cloud** | **$14.58 (80%)** |

**Recommendation:** Hybrid approach (local + OpenRouter for validation) offers best cost/quality balance.

---

## Complete Example

### Step 1: Set Up API Key

```bash
# Export environment variable
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Verify
echo $OPENROUTER_API_KEY
```

### Step 2: Verify Configuration

Your `config.yaml` is already set up:

```yaml
adapters:
  openrouter:
    type: http
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"
    timeout: 90
    max_retries: 3
```

### Step 3: Run a Simple Deliberation

```javascript
// Single model test (quick mode)
mcp__ai-counsel__deliberate({
  question: "Should we adopt TypeScript or stick with JavaScript?",
  participants: [
    {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"}
  ],
  mode: "quick"
})
```

**Expected result:**
- Response in ~5-10 seconds
- Cost: ~$0.05-0.15 (depending on response length)
- Full transcript saved to `transcripts/`

### Step 4: Multi-Model Deliberation

```javascript
// Compare premium vs budget models
mcp__ai-counsel__deliberate({
  question: "What database should we use for our microservice?",
  participants: [
    {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"},  // Premium
    {cli: "openrouter", model: "meta-llama/llama-3.1-70b-instruct"},  // Budget
    {cli: "openrouter", model: "google/gemini-pro-1.5"}  // Alternative
  ],
  mode: "conference",
  rounds: 3
})
```

**Expected result:**
- 3 rounds, each model refines based on others
- Cost: ~$0.50-1.00 per deliberation
- Consensus with voting and AI summary

### Step 5: Hybrid Local + Cloud

```javascript
// Optimal cost/quality: Local exploration + Cloud validation
mcp__ai-counsel__deliberate({
  question: "Should we implement feature flags or branching strategy?",
  participants: [
    {cli: "ollama", model: "llama3"},                    // Local, $0
    {cli: "ollama", model: "mistral"},                   // Local, $0
    {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"}  // Cloud validation
  ],
  mode: "conference",
  rounds: 3
})
```

**Cost breakdown:**
- Ollama (2 participants × 3 rounds): $0
- Claude (1 participant × 3 rounds): ~$0.30
- **Total: ~$0.30 vs $0.90 for 3x Claude**

---

## Troubleshooting

### Problem: "Unauthorized (401)"

**Symptom:**
```
ERROR: HTTP 401 Unauthorized
```

**Cause:** Missing or invalid API key.

**Solution:**

1. **Verify environment variable is set:**
   ```bash
   echo $OPENROUTER_API_KEY
   # Should output key starting with "sk-or-v1-"
   ```

2. **Re-export if missing:**
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-your-actual-key"
   ```

3. **Test key directly:**
   ```bash
   curl https://openrouter.ai/api/v1/auth/key \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   # Should return 200 OK with key info
   ```

4. **Generate new key if invalid:**
   - Visit https://openrouter.ai/keys
   - Revoke old key, create new one

### Problem: "Insufficient credits (402)"

**Symptom:**
```
ERROR: HTTP 402 Payment Required - Insufficient credits
```

**Cause:** OpenRouter account balance is zero.

**Solution:**

1. **Check balance:**
   - Visit https://openrouter.ai/credits
   - View current balance

2. **Add credits:**
   - Click **Add Credits**
   - Minimum: $5 (recommended: $10-20 to start)
   - Pay via credit card or crypto

3. **Monitor usage:**
   - Dashboard shows real-time spending
   - Set up alerts for low balance

### Problem: "Rate limit exceeded (429)"

**Symptom:**
```
ERROR: HTTP 429 Too Many Requests
```

**Cause:** Exceeded model's rate limit.

**Solution:**

1. **AI Counsel automatically retries** with exponential backoff:
   - Retry 1: Wait 1 second
   - Retry 2: Wait 2 seconds
   - Retry 3: Wait 4 seconds

2. **Increase retry limit if needed:**
   ```yaml
   adapters:
     openrouter:
       max_retries: 5  # Increased from 3
   ```

3. **Use different model:**
   - Free models: 5-10 req/min
   - Paid models: 60-3600 req/min
   - Premium models: Higher limits

4. **Space out deliberations:**
   - Add delays between consecutive deliberations
   - Or use multiple models to distribute load

### Problem: "Model not found (404)"

**Symptom:**
```
ERROR: HTTP 404 - Model 'claude-sonnet' not found
```

**Cause:** Incorrect model ID format.

**Solution:**

OpenRouter requires **provider/model** format:

```javascript
// Wrong
{cli: "openrouter", model: "claude-sonnet"}

// Correct
{cli: "openrouter", model: "anthropic/claude-3.5-sonnet"}
```

**Find correct model ID:**
```bash
# List all models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | .id'

# Or visit: https://openrouter.ai/models
```

### More Troubleshooting

See the comprehensive [HTTP Adapter Troubleshooting Guide](../troubleshooting/http-adapters.md) for advanced issues.

---

## Best Practices

### 1. Cost Optimization

**Use cheaper models for exploration, premium for validation:**

```javascript
// Rounds 1-3: Budget model explores options
// Round 4: Premium model validates consensus

participants: [
  {cli: "openrouter", model: "meta-llama/llama-3.1-70b-instruct"},  // $0.30/M
  {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"}          // $3/M
]
```

**Result:** 50% cost reduction vs 2x Claude, maintains quality.

### 2. Model Diversity

**Mix different providers for diverse perspectives:**

```javascript
participants: [
  {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"},  // Anthropic reasoning
  {cli: "openrouter", model: "openai/gpt-4-turbo"},           // OpenAI perspective
  {cli: "openrouter", model: "google/gemini-pro-1.5"}         // Google approach
]
```

**Benefit:** Each provider has different training data and biases.

### 3. Monitor Usage

**Track spending to avoid surprises:**

1. **Dashboard:** https://openrouter.ai/activity
   - Real-time request log
   - Cost per request
   - Model usage breakdown

2. **Set alerts:**
   - Email notifications at $5, $10, $20 thresholds
   - Daily spending limits

3. **Analyze patterns:**
   - Which models are cost-effective?
   - Which deliberations are expensive?
   - Optimize accordingly

### 4. Timeout Configuration

Different models have different latencies:

```yaml
adapters:
  openrouter:
    timeout: 90  # Good for most models

  openrouter_slow:
    timeout: 180  # For large context or slow models (Gemini 1.5 Pro with 1M context)
```

### 5. Fallback Strategy

**Use model fallbacks for reliability:**

```javascript
// If primary model fails, try cheaper alternative
participants: [
  {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"},  // Primary
  {cli: "openrouter", model: "meta-llama/llama-3.1-70b-instruct"},  // Fallback
]
```

**AI Counsel's fault tolerance:** If one participant fails, others continue.

### 6. Hybrid Local + Cloud

**Best overall approach:**

```javascript
// Development/exploration: Pure local (Ollama)
participants: [
  {cli: "ollama", model: "llama3"},
  {cli: "ollama", model: "mistral"}
]

// Production/critical: Hybrid (local + cloud validation)
participants: [
  {cli: "ollama", model: "llama3"},
  {cli: "ollama", model: "mistral"},
  {cli: "openrouter", model: "anthropic/claude-3.5-sonnet"}  // Premium check
]
```

**Cost:** 67% reduction vs pure cloud, maintains quality.

---

## Summary

**What you learned:**
✅ Set up OpenRouter account and API key
✅ Access 200+ models through unified API
✅ Configure AI Counsel with environment variables
✅ Run cloud deliberations with premium models
✅ Optimize costs with budget models and hybrid approach
✅ Troubleshoot authentication and rate limit issues
✅ Monitor usage and control spending

**Result:** Access to world's best AI models with flexible pay-per-use pricing.

**OpenRouter vs Local Models:**

| Factor | OpenRouter | Local (Ollama/LM Studio) |
|--------|------------|-------------------------|
| Cost | Pay-per-use (~$0.30-18/month) | $0 after setup |
| Quality | Highest (GPT-4, Claude Opus) | Good (Llama 3, Mistral) |
| Privacy | Data sent to cloud | 100% local |
| Setup | 5 minutes (API key) | 10-30 minutes (install + download) |
| Hardware | None needed | GPU recommended |
| Rate limits | Yes (model-dependent) | None (local unlimited) |
| Offline | No (requires internet) | Yes |

**Recommendation:** Use hybrid approach (local for volume, OpenRouter for quality).

**Next steps:**
- [Local Model Support Overview](intro.md) - Compare local vs cloud
- [Ollama Quickstart](ollama-quickstart.md) - Set up local models
- [Troubleshooting](../troubleshooting/http-adapters.md) - Diagnose issues

**Questions?** Check https://openrouter.ai/docs or [GitHub Issues](https://github.com/blueman82/ai-counsel/issues).
