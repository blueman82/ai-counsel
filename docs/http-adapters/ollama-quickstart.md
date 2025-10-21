# Ollama Quickstart Guide

Get started with zero-cost local AI deliberations using Ollama in under 5 minutes.

## Table of Contents

- [What is Ollama?](#what-is-ollama)
- [Installation](#installation)
- [Running Ollama](#running-ollama)
- [Available Models](#available-models)
- [Complete Example](#complete-example)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

---

## What is Ollama?

**Ollama** is a lightweight, user-friendly runtime for running large language models locally on your machine. Think of it as "Docker for LLMs"—download a model, run it locally, zero API costs.

### Key Features

- **One-line installation** on macOS, Linux, Windows
- **Simple model management** (`ollama pull llama3`, `ollama list`)
- **OpenAI-compatible API** (easy integration with existing tools)
- **GPU acceleration** (automatic CUDA/Metal detection)
- **Zero cost** (no API fees after initial download)
- **Privacy** (data never leaves your machine)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| Disk space | 10GB free | 50GB+ (for multiple models) |
| CPU | Any modern CPU | M1/M2 Mac or AMD/Intel with AVX2 |
| GPU | None (CPU-only works) | NVIDIA RTX 2060+ or M1/M2 |
| OS | macOS 11+, Linux, Windows 10+ | macOS 13+, Ubuntu 22.04+ |

**Note:** 7B parameter models run well on 8GB RAM. 13B models need 16GB. 70B models need 64GB+.

---

## Installation

### macOS (Homebrew)

```bash
# Install Ollama via Homebrew (easiest)
brew install ollama

# Verify installation
ollama --version
```

**Alternative:** Download installer from https://ollama.com/download

### Linux

```bash
# Install via curl script
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

**Manual install:** Download binary from https://ollama.com/download

### Windows

1. Download installer from https://ollama.com/download
2. Run `OllamaSetup.exe`
3. Follow installation wizard
4. Verify in PowerShell: `ollama --version`

---

## Running Ollama

### Start the Ollama Server

Ollama runs as a background service, listening on `http://localhost:11434`.

```bash
# Start Ollama server (runs in background)
ollama serve

# On macOS/Windows, Ollama auto-starts on login (skip this step)
```

**Verify it's running:**
```bash
# Check if Ollama is listening
curl http://localhost:11434/api/tags

# Should return JSON with available models (empty list if none downloaded yet)
```

### Download a Model

Ollama hosts a library of open-source models. Download one to get started:

```bash
# Download Llama 3 (4.7GB, Meta's latest, excellent quality)
ollama pull llama3

# Progress output:
# pulling manifest
# pulling 6a0746a1ec1a... 100% |████████| 4.7 GB
# verifying sha256 digest
# success

# Verify model is available
ollama list

# Output:
# NAME            ID              SIZE    MODIFIED
# llama3:latest   6a0746a1ec1a    4.7 GB  2 minutes ago
```

**Model download time:** ~2-5 minutes on fast broadband (depends on model size).

---

## Available Models

Ollama supports 100+ open-source models. Here are top picks for AI Counsel deliberations:

### Recommended Models

| Model | Size | RAM | Use Case | Download Command |
|-------|------|-----|----------|------------------|
| **llama3** | 4.7GB | 8GB | Best general-purpose, fast | `ollama pull llama3` |
| **mistral** | 4.1GB | 8GB | Excellent reasoning | `ollama pull mistral` |
| **qwen2.5** | 4.4GB | 8GB | Strong coding, multilingual | `ollama pull qwen2.5` |
| **gemma2** | 5.4GB | 8GB | Google's lightweight model | `ollama pull gemma2` |
| **codellama** | 3.8GB | 8GB | Code-specific tasks | `ollama pull codellama` |

### Larger Models (Advanced)

| Model | Size | RAM | Quality | Download Command |
|-------|------|-----|---------|------------------|
| **qwen2.5:14b** | 8.3GB | 16GB | Very good | `ollama pull qwen2.5:14b` |
| **llama3:70b** | 40GB | 64GB | Excellent | `ollama pull llama3:70b` |

### List All Available Models

```bash
# Browse online model library
open https://ollama.com/library

# Or search from CLI
ollama search llama  # Find all Llama variants
```

---

## Complete Example

Here's a complete workflow from installation to first deliberation.

### Step 1: Install and Start Ollama

```bash
# Install (macOS)
brew install ollama

# Start server (auto-starts on macOS, but can run manually)
ollama serve
```

### Step 2: Download Models

```bash
# Download two models for diverse perspectives
ollama pull llama3      # 4.7GB, ~3 min
ollama pull mistral     # 4.1GB, ~3 min

# Verify downloads
ollama list

# Output:
# NAME              SIZE    MODIFIED
# llama3:latest     4.7 GB  5 minutes ago
# mistral:latest    4.1 GB  2 minutes ago
```

### Step 3: Test Model Directly

```bash
# Interactive chat to verify it works
ollama run llama3

# Prompt appears:
# >>> Hello, how are you?
# I'm just a language model, so I don't have feelings, but...

# Exit: type /bye
```

### Step 4: Configure AI Counsel

Your `config.yaml` already includes Ollama support:

```yaml
# config.yaml (already configured!)
adapters:
  ollama:
    type: http
    base_url: "http://localhost:11434"
    timeout: 120
    max_retries: 3
```

### Step 5: Run a Deliberation

```javascript
// In Claude Code, invoke the deliberate tool:
mcp__ai-counsel__deliberate({
  question: "Should we add automated tests to our new API endpoint?",
  participants: [
    {cli: "ollama", model: "llama3"},
    {cli: "ollama", model: "mistral"}
  ],
  mode: "conference",
  rounds: 3
})
```

**Result:**
- Round 1: Both models present initial positions (~10 sec each)
- Round 2: Models refine based on each other's arguments (~10 sec each)
- Round 3: Convergence detected, consensus reached

**Total time:** ~60 seconds
**Total cost:** $0.00
**Output:** Full transcript in `transcripts/` with voting results and AI summary

---

## Configuration

### Basic Configuration

The default config works for most users:

```yaml
# config.yaml
adapters:
  ollama:
    type: http
    base_url: "http://localhost:11434"  # Default Ollama port
    timeout: 120                        # 2 minutes per request
    max_retries: 3                      # Retry on transient failures
```

### Advanced Configuration

#### Custom Port

If Ollama runs on a different port:

```yaml
adapters:
  ollama:
    type: http
    base_url: "http://localhost:8080"  # Custom port
```

```bash
# Start Ollama on custom port
OLLAMA_HOST=0.0.0.0:8080 ollama serve
```

#### Increased Timeout

For large models (70B) or slow hardware:

```yaml
adapters:
  ollama:
    type: http
    timeout: 300  # 5 minutes (for 70B models)
```

#### Remote Ollama Server

Access Ollama running on another machine:

```yaml
adapters:
  ollama:
    type: http
    base_url: "http://192.168.1.100:11434"  # Remote server IP
    timeout: 180
```

### Model-Specific Settings

You can configure different models with different timeouts:

```yaml
# Not directly supported in adapter config, but you can create multiple adapter entries:
adapters:
  ollama_fast:
    type: http
    base_url: "http://localhost:11434"
    timeout: 60  # Fast 7B models

  ollama_slow:
    type: http
    base_url: "http://localhost:11434"
    timeout: 300  # Slow 70B models
```

Then use in deliberations:

```javascript
participants: [
  {cli: "ollama_fast", model: "llama3"},
  {cli: "ollama_slow", model: "llama3:70b"}
]
```

---

## Troubleshooting

### Problem: "Connection refused"

**Symptom:**
```
ERROR: Connection refused to http://localhost:11434
```

**Cause:** Ollama server not running.

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama if not running
ollama serve

# On macOS/Windows, ensure auto-start is enabled
# System Preferences → Users & Groups → Login Items → Ollama
```

### Problem: "Model not found"

**Symptom:**
```
ERROR: HTTP 400 Bad Request - model 'llama3' not found
```

**Cause:** Model not downloaded.

**Solution:**
```bash
# List available models
ollama list

# Download missing model
ollama pull llama3

# Verify download
ollama list
```

### Problem: "Request timeout"

**Symptom:**
```
ERROR: Request timed out after 120 seconds
```

**Cause:** Model loading or slow generation.

**Solution:**

1. **First request is slow (model loading):** Wait 30-60 seconds for model to load into RAM.

2. **Increase timeout:**
   ```yaml
   adapters:
     ollama:
       timeout: 300  # 5 minutes
   ```

3. **Use smaller model:**
   ```bash
   ollama pull llama3  # 7B model instead of 70B
   ```

### Problem: "Out of memory"

**Symptom:**
```
ERROR: Ollama process killed
# or system becomes very slow
```

**Cause:** Model too large for available RAM.

**Solution:**

1. **Check RAM requirements:**
   ```bash
   # See model size
   ollama list

   # Compare to available RAM
   free -h  # Linux
   vm_stat  # macOS
   ```

2. **Use smaller model:**
   - 8GB RAM → Use 7B models (llama3, mistral)
   - 16GB RAM → Use 13B models (qwen2.5:14b)
   - 64GB RAM → Use 70B models (llama3:70b)

3. **Close other applications** to free up RAM.

### Problem: "Slow responses (30+ seconds)"

**Cause:** CPU-only inference (no GPU acceleration).

**Solution:**

1. **Verify GPU acceleration:**
   ```bash
   # Check if Ollama detected GPU
   ollama run llama3  # Look for "Using GPU" message

   # For NVIDIA GPUs, check CUDA:
   nvidia-smi

   # For Apple Silicon, check Metal:
   system_profiler SPDisplaysDataType
   ```

2. **Enable GPU (if available):**
   - **NVIDIA:** Install CUDA toolkit
   - **AMD:** Install ROCm (Linux only)
   - **Apple Silicon:** GPU enabled by default

3. **Use smaller model for faster responses:**
   - llama3:7b → ~30 tokens/sec (CPU)
   - llama3:7b → ~150 tokens/sec (M2 GPU)

### More Troubleshooting

See the comprehensive [HTTP Adapter Troubleshooting Guide](../troubleshooting/http-adapters.md) for advanced issues.

---

## Performance Tips

### 1. Pre-warm Models

Load models into memory before deliberation to avoid first-request delays:

```bash
# Warm up llama3 (keeps it in memory for 10 minutes)
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3",
    "prompt": "warmup",
    "keep_alive": "10m"
  }'
```

### 2. Use Quantized Models

Smaller quantized models run faster with minimal quality loss:

```bash
# Download 4-bit quantized version (smaller, faster)
ollama pull llama3:q4_0  # 2.4GB vs 4.7GB

# Use in deliberation
{cli: "ollama", model: "llama3:q4_0"}
```

**Trade-off:** 2x faster, slight quality reduction (acceptable for most use cases).

### 3. Optimize Context Window

Reduce context size for faster inference:

```yaml
# In deliberation request
mode: "quick"  # Fewer rounds = less context
rounds: 2      # Minimize round count
```

### 4. Run Multiple Models in Parallel

Ollama can serve multiple models concurrently (if RAM permits):

```javascript
participants: [
  {cli: "ollama", model: "llama3"},
  {cli: "ollama", model: "mistral"}
]
// Both models invoked in parallel per round
```

### 5. Monitor Resource Usage

```bash
# Real-time monitoring
htop  # CPU/RAM usage

# GPU monitoring (NVIDIA)
nvidia-smi -l 1

# GPU monitoring (Apple Silicon)
sudo powermetrics --samplers gpu_power -i 1000
```

### 6. Benchmark Your Hardware

Test model performance before production use:

```bash
# Time a simple inference
time ollama run llama3 "What is 2+2?"

# Expected times (M2 MacBook Pro):
# llama3:7b → 3-5 seconds
# mistral:7b → 2-4 seconds
# qwen2.5:14b → 6-10 seconds
```

---

## Next Steps

You're now ready to run local AI deliberations with Ollama!

### Recommended Learning Path

1. **Experiment with models:** Try different models to find the best quality/speed balance
   ```bash
   ollama pull mistral
   ollama pull qwen2.5
   ollama pull gemma2
   ```

2. **Mix local + cloud:** Combine Ollama with Claude for hybrid cost/quality
   ```javascript
   participants: [
     {cli: "ollama", model: "llama3"},
     {cli: "ollama", model: "mistral"},
     {cli: "claude", model: "sonnet"}  // Premium validation
   ]
   ```

3. **Explore advanced features:**
   - [LM Studio Quickstart](lmstudio-quickstart.md) - GUI alternative to Ollama
   - [llama.cpp Quickstart](llamacpp-quickstart.md) - Maximum performance
   - [OpenRouter Guide](openrouter-guide.md) - Cloud model access

4. **Optimize for your use case:**
   - **Speed:** Use smaller models (7B), quantization, GPU acceleration
   - **Quality:** Use larger models (14B, 70B), cloud fallback for critical decisions
   - **Cost:** Pure Ollama (zero cost) vs hybrid (reduced cost)

---

## Summary

**What you learned:**
✅ Install Ollama in one line (`brew install ollama`)
✅ Download models (`ollama pull llama3`)
✅ Configure AI Counsel (already done in `config.yaml`)
✅ Run zero-cost local deliberations
✅ Troubleshoot common issues
✅ Optimize performance

**Result:** Unlimited AI deliberations at $0 cost with complete data privacy.

**Questions?** Check the [Troubleshooting Guide](../troubleshooting/http-adapters.md) or [GitHub Issues](https://github.com/blueman82/ai-counsel/issues).

---

**Related Guides:**
- [Local Model Support Overview](intro.md)
- [LM Studio Quickstart](lmstudio-quickstart.md)
- [OpenRouter Guide](openrouter-guide.md)
- [Troubleshooting](../troubleshooting/http-adapters.md)
