# LM Studio Quickstart Guide

Get started with GUI-based local AI deliberations using LM Studio in under 10 minutes.

## Table of Contents

- [What is LM Studio?](#what-is-lm-studio)
- [Installation](#installation)
- [Loading a Model](#loading-a-model)
- [Starting the Server](#starting-the-server)
- [Complete Example](#complete-example)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

---

## What is LM Studio?

**LM Studio** is a desktop application for running large language models locally with a beautiful graphical interface. Think of it as "iTunes for AI models"—browse, download, and run models without touching the command line.

### Key Features

- **Graphical interface** (no terminal required)
- **Model browser** (search and download from Hugging Face)
- **OpenAI-compatible API** (works with existing tools)
- **GPU acceleration** (automatic CUDA/Metal detection)
- **Chat interface** (test models before using in deliberations)
- **Cross-platform** (macOS, Windows, Linux)

### Why Choose LM Studio?

**Best for:**
- Non-technical users who prefer GUI over CLI
- Windows users (better Windows support than Ollama)
- Users who want to test models interactively before deliberations
- Visual exploration of model library

**Choose Ollama instead if:**
- You prefer command-line tools
- You want faster model switching (Ollama is more lightweight)
- You're on macOS/Linux and comfortable with terminal

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| Disk space | 20GB free | 100GB+ (for model library) |
| CPU | Any modern CPU | M1/M2 Mac or Intel/AMD with AVX2 |
| GPU | None (CPU works) | NVIDIA RTX 3060+ or M1/M2 |
| OS | macOS 11+, Windows 10+, Linux | macOS 13+, Windows 11 |

---

## Installation

### macOS

1. **Download LM Studio:**
   - Visit https://lmstudio.ai/
   - Click "Download for macOS"
   - Download size: ~150MB

2. **Install:**
   ```bash
   # Open downloaded DMG
   # Drag "LM Studio" to Applications folder
   # Launch from Applications
   ```

3. **First launch:**
   - macOS may show "unidentified developer" warning
   - Right-click → Open → Confirm
   - Grant necessary permissions (file access)

### Windows

1. **Download LM Studio:**
   - Visit https://lmstudio.ai/
   - Click "Download for Windows"
   - Download size: ~200MB

2. **Install:**
   - Run `LMStudioSetup.exe`
   - Follow installation wizard
   - Choose installation directory (ensure enough space for models)

3. **First launch:**
   - Windows may show SmartScreen warning
   - Click "More info" → "Run anyway"

### Linux

1. **Download LM Studio:**
   - Visit https://lmstudio.ai/
   - Click "Download for Linux"
   - Download `.AppImage` file

2. **Install:**
   ```bash
   # Make executable
   chmod +x LM-Studio-*.AppImage

   # Run
   ./LM-Studio-*.AppImage
   ```

3. **Optional: Create desktop entry:**
   ```bash
   # Copy to /usr/local/bin
   sudo cp LM-Studio-*.AppImage /usr/local/bin/lmstudio

   # Now run with: lmstudio
   ```

---

## Loading a Model

### Step 1: Open LM Studio

Launch the application. You'll see the main interface with tabs:
- **Discover** (search models)
- **Local Models** (downloaded models)
- **Chat** (test models)
- **Local Server** (API server)

### Step 2: Search for Models

1. Click **Discover** tab
2. Search bar: type "llama" or "mistral"
3. Browse results (sorted by popularity/downloads)

**Recommended models for beginners:**
- `meta-llama/Llama-3.2-1B-Instruct` (1.3GB, very fast)
- `mistralai/Mistral-7B-Instruct-v0.3` (4.1GB, excellent quality)
- `Qwen/Qwen2.5-7B-Instruct` (4.4GB, strong reasoning)

### Step 3: Download a Model

1. **Click on a model** (e.g., "Llama-3.2-1B-Instruct")
2. **Select quantization level:**
   - Q4_K_M (4-bit, recommended, best speed/quality balance)
   - Q5_K_M (5-bit, higher quality, slower)
   - Q8_0 (8-bit, highest quality, slowest)

   **Recommendation:** Start with Q4_K_M (2-3x smaller, minimal quality loss)

3. **Click "Download"**
   - Progress bar shows download status
   - Models saved to default location:
     - macOS: `~/.cache/lm-studio/models`
     - Windows: `C:\Users\YourName\.cache\lm-studio\models`
     - Linux: `~/.cache/lm-studio/models`

**Download times:**
- 1B model (1.3GB): 1-3 minutes
- 7B model (4GB): 3-10 minutes
- 14B model (8GB): 10-20 minutes

### Step 4: Verify Download

1. Click **Local Models** tab
2. You should see your downloaded model listed
3. Green checkmark = ready to use

### Model Selection for Deliberations

For reliable AI Counsel deliberations, choose models based on parameter count:

| Model Size | Deliberation Quality | Examples | Recommendation |
|------------|---------------------|----------|----------------|
| **7B-8B+** | ✅ Excellent | Llama-3-8B, Mistral-7B, Qwen-2.5-7B | **Recommended** |
| **3B-7B** | ⚠️ Variable | Phi-3-mini, Llama-3.2-3B | Use with caution |
| **<3B** | ❌ Poor | Llama-3.2-1B, TinyLlama | Testing only |

**Why size matters:**
- Deliberations require structured JSON output (votes with confidence and rationale)
- Small models (<3B) often echo prompts, produce invalid JSON, or skip vote formatting
- 7B-8B models reliably follow complex instructions and produce valid votes

---

## Starting the Server

LM Studio provides an OpenAI-compatible API server for AI Counsel integration.

### Step 1: Load a Model

1. Go to **Local Server** tab
2. Click **Select a model to load**
3. Choose your downloaded model (e.g., "Llama-3.2-1B-Instruct Q4_K_M")
4. Click **Load Model**

**Wait for model to load (~10-30 seconds):**
- Loading indicator shows progress
- "Model loaded" message appears when ready

### Step 2: Configure Server Settings

**Default settings work for most users:**

| Setting | Default | Description |
|---------|---------|-------------|
| Port | 1234 | HTTP server port |
| CORS | Enabled | Allow browser requests |
| API Keys | Disabled | No authentication required (local use) |

**Advanced settings (optional):**
- **GPU Offload:** Auto (uses GPU if available)
- **Context Length:** 2048 (max tokens for conversation)
- **Temperature:** 0.7 (creativity level)

### Step 3: Start Server

1. Click **Start Server** button
2. Server status changes to "Running"
3. Endpoint URL shown: `http://localhost:1234/v1`

**Verify server is running:**
```bash
# Test connection
curl http://localhost:1234/v1/models

# Should return JSON with loaded model info
```

### Step 4: Keep Running

**Important:** LM Studio server must remain running during deliberations.

- Minimize LM Studio window (don't close)
- Server runs until you click "Stop Server" or quit LM Studio

---

## Complete Example

Here's a complete workflow from installation to first deliberation.

### Step 1: Install LM Studio

Download from https://lmstudio.ai/ and install (see [Installation](#installation)).

### Step 2: Download Models

1. Open LM Studio
2. **Discover** tab → Search "llama"
3. Download "Llama-3.2-1B-Instruct" (Q4_K_M variant, ~1.3GB)
4. **Discover** tab → Search "mistral"
5. Download "Mistral-7B-Instruct-v0.3" (Q4_K_M variant, ~4GB)

**Total download time:** ~5-10 minutes (depending on internet speed)

### Step 3: Test Models in Chat

Before using in deliberations, test model quality:

1. Click **Chat** tab
2. **Select model** dropdown → "Llama-3.2-1B-Instruct"
3. Type a test message: "Explain test-driven development in one sentence."
4. Review response quality

**Repeat for Mistral model** to compare.

### Step 4: Start API Server

1. **Local Server** tab
2. **Select a model to load** → "Llama-3.2-1B-Instruct Q4_K_M"
3. Click **Load Model** (wait 10-30 seconds)
4. Click **Start Server**
5. Verify: "Server running on http://localhost:1234"

### Step 5: Configure AI Counsel

Your `config.yaml` already includes LM Studio support:

```yaml
# config.yaml (already configured!)
adapters:
  lmstudio:
    type: http
    base_url: "http://localhost:1234"
    timeout: 120
    max_retries: 3
```

### Step 6: Run a Deliberation

```javascript
// In Claude Code, invoke the deliberate tool:
mcp__ai-counsel__deliberate({
  question: "Should we prioritize code quality or shipping speed?",
  participants: [
    {cli: "lmstudio", model: "llama-3.2-1b-instruct"}
  ],
  mode: "quick"
})
```

**Result:**
- Model generates response (~5-10 seconds)
- Full transcript saved to `transcripts/`
- Zero API cost

### Step 7: Multi-Model Deliberation

To use multiple models, you need to manually switch models in LM Studio between rounds (LM Studio limitation: one model at a time).

**Workaround:** Combine LM Studio with other adapters:

```javascript
participants: [
  {cli: "lmstudio", model: "llama-3.2-1b-instruct"},
  {cli: "ollama", model: "mistral"},  // Run Ollama in parallel
  {cli: "claude", model: "sonnet"}    // Cloud model for validation
]
```

**Better approach for multi-model local:** Use Ollama (can run multiple models concurrently).

---

## Configuration

### Basic Configuration

The default config works for most users:

```yaml
# config.yaml
adapters:
  lmstudio:
    type: http
    base_url: "http://localhost:1234"  # Default LM Studio port
    timeout: 120                       # 2 minutes per request
    max_retries: 3                     # Retry on transient failures
```

### Advanced Configuration

#### Custom Port

If you changed LM Studio's server port:

1. **LM Studio:** Local Server tab → Settings → Port: 8080
2. **config.yaml:**
   ```yaml
   adapters:
     lmstudio:
       type: http
       base_url: "http://localhost:8080"
   ```

#### Increased Timeout

For large models or slow hardware:

```yaml
adapters:
  lmstudio:
    type: http
    timeout: 300  # 5 minutes (for slow generation)
```

#### Remote LM Studio Server

Access LM Studio running on another machine:

1. **LM Studio:** Local Server tab → Settings → Enable "Allow network connections"
2. **config.yaml:**
   ```yaml
   adapters:
     lmstudio:
       type: http
       base_url: "http://192.168.1.100:1234"  # Remote server IP
   ```

**Security note:** Only enable network access on trusted networks (no authentication by default).

---

## Troubleshooting

### Problem: "Connection refused"

**Symptom:**
```
ERROR: Connection refused to http://localhost:1234
```

**Cause:** LM Studio server not running.

**Solution:**
1. Open LM Studio
2. Go to **Local Server** tab
3. Verify model is loaded (if not, load one)
4. Click **Start Server**
5. Wait for "Server running" status
6. Retry deliberation

### Problem: "Model not loaded"

**Symptom:**
LM Studio shows "No model loaded" in Local Server tab.

**Cause:** Model not selected or failed to load.

**Solution:**
1. Click **Select a model to load**
2. Choose a downloaded model from dropdown
3. Click **Load Model**
4. Wait for "Model loaded" message (~10-30 seconds)
5. If loading fails:
   - Check available RAM (model may be too large)
   - Try smaller model (1B instead of 7B)
   - Restart LM Studio

### Problem: "Request timeout"

**Symptom:**
```
ERROR: Request timed out after 120 seconds
```

**Cause:** Model generating response too slowly.

**Solution:**

1. **First request is slow (model warming up):** Wait up to 60 seconds.

2. **Increase timeout:**
   ```yaml
   adapters:
     lmstudio:
       timeout: 300  # 5 minutes
   ```

3. **Use smaller/faster model:**
   - 1B models: ~5-10 seconds per response
   - 7B models: ~10-30 seconds per response
   - 14B models: ~30-90 seconds per response

4. **Enable GPU acceleration:**
   - LM Studio → Local Server → Settings → GPU Offload: Max

### Problem: "Model response is gibberish"

**Symptom:**
Model returns nonsensical or repetitive text.

**Cause:** Wrong model format or corruption.

**Solution:**
1. Re-download model:
   - Local Models tab → Right-click model → Delete
   - Discover tab → Re-download
2. Verify model is "Instruct" variant (required for chat)
   - ✅ "Llama-3.2-1B-**Instruct**"
   - ❌ "Llama-3.2-1B" (base model, not for chat)

### Problem: "Out of memory"

**Symptom:**
LM Studio shows "Failed to load model: Out of memory"

**Cause:** Model too large for available RAM.

**Solution:**

1. **Check model size vs RAM:**
   - 1B model (Q4): ~1.5GB RAM required
   - 7B model (Q4): ~6GB RAM required
   - 14B model (Q4): ~12GB RAM required
   - Add 2GB for LM Studio overhead

2. **Use smaller quantization:**
   - Instead of Q8_0 (8-bit), use Q4_K_M (4-bit)
   - Reduces RAM usage by 50%

3. **Use smaller model:**
   - 1B models work on 8GB RAM
   - 7B models need 16GB RAM
   - 14B+ models need 32GB+ RAM

4. **Close other applications** to free RAM.

### More Troubleshooting

See the comprehensive [HTTP Adapter Troubleshooting Guide](../troubleshooting/http-adapters.md) for advanced issues.

---

## Performance Tips

### 1. Choose Right Quantization

**Trade-offs:**

| Quantization | Size | Speed | Quality | RAM |
|--------------|------|-------|---------|-----|
| Q4_K_M | 1.0× | Fastest | Good | 1.0× |
| Q5_K_M | 1.3× | Fast | Very Good | 1.3× |
| Q8_0 | 2.0× | Medium | Excellent | 2.0× |
| FP16 | 4.0× | Slow | Best | 4.0× |

**Recommendation:** Q4_K_M for most use cases (best speed/quality balance).

### 2. Enable GPU Acceleration

**LM Studio → Local Server → Settings:**
- **GPU Offload:** Set to "Max" (uses all available GPU layers)
- **GPU Type:** Auto-detected (CUDA for NVIDIA, Metal for Apple Silicon)

**Performance impact:**
- CPU-only: ~10 tokens/sec (7B model)
- GPU (M2): ~40 tokens/sec (7B model)
- GPU (RTX 4090): ~100+ tokens/sec (7B model)

### 3. Optimize Context Length

Smaller context = faster inference:

**LM Studio → Local Server → Settings:**
- **Context Length:** 2048 (default, good for deliberations)
- Reduce to 1024 for faster responses (if prompts are short)
- Increase to 4096 only if needed (slower)

### 4. Pre-warm Model

First request is slow (model loading into GPU). Pre-warm before deliberations:

1. **Chat** tab → Send a test message
2. Model stays loaded in memory
3. Subsequent deliberation requests are faster

### 5. Batch Operations

If running multiple deliberations, keep LM Studio server running between them:
- Avoid stopping/restarting server (slow model reload)
- Model stays in GPU memory for instant responses

### 6. Monitor Resource Usage

**Task Manager (Windows) / Activity Monitor (macOS):**
- Check "LM Studio" process
- GPU usage should be high (80-100% during inference)
- If GPU usage low, check GPU offload settings

### 7. Benchmark Your Hardware

Test model performance before production use:

**LM Studio Chat tab:**
- Type: "Count from 1 to 100"
- Note tokens/second in bottom status bar
- Target: 20+ tokens/sec for 7B models (good UX)

---

## Next Steps

You're now ready to run local AI deliberations with LM Studio!

### Recommended Learning Path

1. **Experiment with models:**
   - Download and test different model sizes (1B, 7B, 14B)
   - Compare quantization levels (Q4 vs Q5 vs Q8)
   - Find your optimal speed/quality balance

2. **Mix with other adapters:**
   ```javascript
   participants: [
     {cli: "lmstudio", model: "mistral-7b-instruct"},
     {cli: "ollama", model: "llama3"},     // Multiple local models
     {cli: "claude", model: "sonnet"}      // Premium cloud validation
   ]
   ```

3. **Explore advanced features:**
   - [Ollama Quickstart](ollama-quickstart.md) - CLI alternative (better for multiple models)
   - [llama.cpp Quickstart](llamacpp-quickstart.md) - Maximum performance
   - [OpenRouter Guide](openrouter-guide.md) - Cloud model access

4. **Optimize for your use case:**
   - **Speed:** Use 1B models, Q4 quantization, GPU acceleration
   - **Quality:** Use 7B+ models, Q5/Q8 quantization, cloud fallback
   - **Cost:** Pure LM Studio (zero cost) vs hybrid (reduced cost)

---

## Summary

**What you learned:**
✅ Install LM Studio with graphical interface
✅ Download and manage models visually
✅ Start OpenAI-compatible API server
✅ Configure AI Counsel (already done in `config.yaml`)
✅ Run zero-cost local deliberations
✅ Troubleshoot common issues
✅ Optimize performance with quantization and GPU

**Result:** GUI-based unlimited AI deliberations at $0 cost with complete data privacy.

**LM Studio vs Ollama:**
- **LM Studio:** Best for GUI users, Windows, visual model exploration
- **Ollama:** Best for CLI users, running multiple models concurrently, macOS/Linux

**Questions?** Check the [Troubleshooting Guide](../troubleshooting/http-adapters.md) or [GitHub Issues](https://github.com/blueman82/ai-counsel/issues).

---

**Related Guides:**
- [Local Model Support Overview](intro.md)
- [Ollama Quickstart](ollama-quickstart.md)
- [OpenRouter Guide](openrouter-guide.md)
- [Troubleshooting](../troubleshooting/http-adapters.md)
