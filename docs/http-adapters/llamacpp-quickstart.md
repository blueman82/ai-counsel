# llama.cpp Quickstart Guide

Get maximum performance from local AI models using llama.cpp, the high-performance C++ inference engine.

## Table of Contents

- [What is llama.cpp?](#what-is-llamacpp)
- [Installation](#installation)
- [Downloading Models](#downloading-models)
- [Configuration](#configuration)
- [Complete Example](#complete-example)
- [Performance Benchmarks](#performance-benchmarks)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## What is llama.cpp?

**llama.cpp** is a high-performance C++ library for running large language models with extreme efficiency. It's the engine behind Ollama and many other LLM tools.

### Key Features

- **Maximum performance** (fastest local inference engine)
- **Low memory footprint** (optimized quantization)
- **Cross-platform** (macOS, Linux, Windows, even mobile)
- **GPU acceleration** (CUDA, Metal, OpenCL, Vulkan)
- **Bare-metal control** (fine-tune every inference parameter)
- **Zero dependencies** (pure C++, no Python runtime)

### Why Choose llama.cpp?

**Best for:**
- Advanced users comfortable with command-line compilation
- Performance-critical applications (low latency, high throughput)
- Resource-constrained environments (embedded, edge devices)
- Custom inference pipelines (fine-grained control)

**Choose Ollama/LM Studio instead if:**
- You want GUI or simplified management
- You prioritize ease of use over maximum performance
- You're a beginner to local LLMs

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| Disk space | 10GB free | 50GB+ |
| CPU | x86_64 with AVX2 | Apple Silicon or AMD/Intel with AVX512 |
| GPU | None (CPU works) | NVIDIA RTX 2060+, M1/M2, or AMD ROCm |
| OS | macOS, Linux, Windows | macOS 13+, Ubuntu 22.04+, Windows 11 |
| Build tools | GCC/Clang or MSVC | CMake 3.14+ |

---

## Installation

### macOS (Homebrew - Easiest)

```bash
# Install llama.cpp via Homebrew
brew install llama.cpp

# Verify installation
llama-cli --version

# Output: llama.cpp version <version> (with Metal GPU support)
```

**Advantage:** Pre-built with Metal GPU support for Apple Silicon.

### macOS/Linux (Build from Source - Maximum Performance)

```bash
# Clone repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build (CPU-only, fastest compile)
make

# Or build with GPU acceleration
make LLAMA_METAL=1      # Apple Silicon (Metal)
make LLAMA_CUDA=1       # NVIDIA (CUDA)
make LLAMA_HIPBLAS=1    # AMD (ROCm)
make LLAMA_VULKAN=1     # Cross-platform Vulkan

# Verify build
./llama-cli --version
```

### macOS/Linux (CMake Build - Advanced)

```bash
# Clone repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DLLAMA_METAL=ON       # Apple Silicon
# OR
cmake .. -DLLAMA_CUDA=ON        # NVIDIA GPU
# OR
cmake .. -DLLAMA_HIPBLAS=ON     # AMD GPU

# Build
cmake --build . --config Release

# Binaries in: build/bin/
./bin/llama-cli --version
```

### Windows (Pre-built Binary - Easiest)

1. **Download pre-built binary:**
   - Visit: https://github.com/ggerganov/llama.cpp/releases
   - Download: `llama-<version>-bin-win-cuda-x64.zip` (NVIDIA GPU)
   - Or: `llama-<version>-bin-win-x64.zip` (CPU-only)

2. **Extract:**
   ```powershell
   # Extract to C:\llama.cpp
   Expand-Archive llama-*-win-*.zip -DestinationPath C:\llama.cpp
   ```

3. **Add to PATH:**
   ```powershell
   # Add to PATH for easy access
   $env:Path += ";C:\llama.cpp"
   ```

4. **Verify:**
   ```powershell
   llama-cli --version
   ```

### Windows (Build from Source - Advanced)

**Prerequisites:** Visual Studio 2019+ with C++ tools, CMake

```powershell
# Clone repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with CMake (CUDA example)
mkdir build
cd build
cmake .. -DLLAMA_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release

# Binary in: build\bin\Release\llama-cli.exe
.\bin\Release\llama-cli.exe --version
```

---

## Downloading Models

llama.cpp uses GGUF format (optimized quantized models).

### Where to Find Models

**Hugging Face** is the primary source:
- Search: https://huggingface.co/models?library=gguf
- Example: https://huggingface.co/TheBloke (high-quality quantizations)

### Recommended Models for Beginners

| Model | Size | Quality | Download Link |
|-------|------|---------|---------------|
| **Llama 3.2 1B Q4** | 800MB | Good | [Link](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF) |
| **Llama 3 8B Q4** | 4.3GB | Excellent | [Link](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF) |
| **Mistral 7B Q4** | 4.1GB | Excellent | [Link](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF) |
| **Qwen 2.5 7B Q4** | 4.4GB | Excellent | [Link](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF) |

### Download Example (Command Line)

```bash
# Create models directory
mkdir -p ~/llama-models
cd ~/llama-models

# Download Llama 3.2 1B (Q4_K_M quantization)
wget https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Or use curl
curl -L -o llama-3.2-1b-q4.gguf \
  "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"

# Verify download (should be ~800MB)
ls -lh
```

### Download Example (Browser)

1. Visit model page (e.g., https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF)
2. Click **Files and versions** tab
3. Download `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (click filename)
4. Save to `~/llama-models/` directory

### Understanding Quantization Levels

| Quantization | Size | Speed | Quality | Use Case |
|--------------|------|-------|---------|----------|
| Q4_K_M | 1.0× | Fastest | Good | **Recommended for beginners** |
| Q5_K_M | 1.3× | Fast | Very Good | Balanced performance |
| Q6_K | 1.6× | Medium | Excellent | High quality needed |
| Q8_0 | 2.0× | Slow | Near-perfect | Maximum quality |

**Recommendation:** Start with Q4_K_M (best speed/quality/size balance).

---

## Configuration

### AI Counsel Setup

Your `config.yaml` includes llamacpp support:

```yaml
# config.yaml
cli_tools:
  llamacpp:
    command: "llama-cli"
    args: ["-m", "{model}", "-p", "{prompt}", "-n", "512", "-c", "2048"]
    timeout: 180
```

### Understanding Arguments

| Argument | Description | Default | Recommendation |
|----------|-------------|---------|----------------|
| `-m` | Model path | N/A | **Required:** `/path/to/model.gguf` |
| `-p` | Prompt text | N/A | **Required:** Use `{prompt}` placeholder |
| `-n` | Tokens to predict | 128 | **512+** (for complete responses) |
| `-c` | Context size | 512 | **2048-4096** (for deliberations) |
| `-t` | CPU threads | Auto | **8-16** (match CPU cores) |
| `--temp` | Temperature | 0.8 | **0.7** (balanced creativity) |
| `--top-p` | Nucleus sampling | 0.9 | **0.9** (default is good) |
| `--repeat-penalty` | Repetition penalty | 1.1 | **1.1** (prevent loops) |

### Recommended Configuration

```yaml
# config.yaml (optimized)
cli_tools:
  llamacpp:
    command: "llama-cli"
    args:
      - "-m"
      - "{model}"  # Use full path: /Users/you/llama-models/llama-3.2-1b-q4.gguf
      - "-p"
      - "{prompt}"
      - "-n"
      - "1024"     # Increased from 512 (longer responses)
      - "-c"
      - "4096"     # Increased from 2048 (larger context)
      - "-t"
      - "8"        # Use 8 CPU threads (adjust for your hardware)
      - "--temp"
      - "0.7"      # Balanced temperature
      - "--gpu-layers"
      - "99"       # Offload all layers to GPU (if available)
    timeout: 180
```

### GPU Acceleration

**Apple Silicon (Metal):**
```yaml
args:
  - "-m"
  - "{model}"
  - "-p"
  - "{prompt}"
  - "-ngl"
  - "99"         # Offload 99 layers to GPU (Metal)
  - "-n"
  - "512"
```

**NVIDIA (CUDA):**
```yaml
args:
  - "-m"
  - "{model}"
  - "-p"
  - "{prompt}"
  - "-ngl"
  - "99"         # Offload 99 layers to GPU (CUDA)
  - "-n"
  - "512"
```

**Explanation:** `-ngl` (GPU layers) offloads computation to GPU. Set to 99 to use GPU fully. Adjust down if GPU runs out of memory.

---

## Complete Example

Here's a complete workflow from installation to first deliberation.

### Step 1: Install llama.cpp

```bash
# macOS (Homebrew)
brew install llama.cpp

# Verify
llama-cli --version
```

### Step 2: Download Model

```bash
# Create models directory
mkdir -p ~/llama-models
cd ~/llama-models

# Download Llama 3.2 1B (Q4_K_M, ~800MB)
curl -L -o llama-3.2-1b-instruct-q4.gguf \
  "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"

# Verify download
ls -lh llama-3.2-1b-instruct-q4.gguf
# Should show ~800MB file
```

### Step 3: Test Model

```bash
# Test inference directly
llama-cli \
  -m ~/llama-models/llama-3.2-1b-instruct-q4.gguf \
  -p "What is test-driven development?" \
  -n 100 \
  -c 2048

# Should output a response about TDD
```

### Step 4: Configure AI Counsel

```yaml
# config.yaml
cli_tools:
  llamacpp:
    command: "llama-cli"
    args:
      - "-m"
      - "{model}"
      - "-p"
      - "{prompt}"
      - "-n"
      - "512"
      - "-c"
      - "2048"
    timeout: 180
```

### Step 5: Run a Deliberation

```javascript
// In Claude Code, invoke the deliberate tool:
mcp__ai-counsel__deliberate({
  question: "Should we adopt microservices or monolith architecture?",
  participants: [
    {
      cli: "llamacpp",
      model: "/Users/yourname/llama-models/llama-3.2-1b-instruct-q4.gguf"
    }
  ],
  mode: "quick"
})
```

**Important:** Use **full absolute path** to model file, not relative path.

**Result:**
- Model generates response (~5-10 seconds)
- Full transcript saved to `transcripts/`
- Zero API cost

---

## Performance Benchmarks

### Hardware Comparison (Llama 3 8B Q4_K_M)

| Hardware | CPU | GPU | Tokens/sec | Response Time (512 tokens) |
|----------|-----|-----|------------|---------------------------|
| M2 MacBook Pro | ✓ | ✗ | 12 tok/s | ~42 sec |
| M2 MacBook Pro | ✗ | ✓ (Metal) | 45 tok/s | ~11 sec |
| Intel i7-12700K | ✓ | ✗ | 18 tok/s | ~28 sec |
| RTX 4090 | ✗ | ✓ (CUDA) | 180 tok/s | ~3 sec |
| RTX 3060 | ✗ | ✓ (CUDA) | 60 tok/s | ~8 sec |

**Key takeaway:** GPU acceleration provides 3-10x speedup.

### Model Size vs Speed (M2 MacBook Pro, Metal GPU)

| Model | Size | RAM | Tokens/sec | Quality |
|-------|------|-----|------------|---------|
| Llama 3.2 1B Q4 | 800MB | 2GB | 120 tok/s | Good |
| Llama 3 8B Q4 | 4.3GB | 8GB | 45 tok/s | Excellent |
| Llama 3 8B Q8 | 8.5GB | 12GB | 30 tok/s | Near-perfect |
| Llama 2 13B Q4 | 7.2GB | 12GB | 22 tok/s | Excellent |
| Llama 2 70B Q4 | 38GB | 48GB | 4 tok/s | Best |

**Recommendation:** 8B Q4 models offer best quality/speed balance for most users.

### Quantization Impact (Llama 3 8B on M2 Metal)

| Quantization | Size | Speed | Perplexity | Quality Loss |
|--------------|------|-------|------------|--------------|
| Q4_K_M | 4.3GB | 45 tok/s | 5.98 | ~3% |
| Q5_K_M | 5.6GB | 38 tok/s | 5.82 | ~1.5% |
| Q6_K | 6.6GB | 34 tok/s | 5.75 | ~0.8% |
| Q8_0 | 8.5GB | 30 tok/s | 5.70 | ~0.3% |

**Key takeaway:** Q4_K_M is 50% faster than Q8_0 with only 3% quality degradation (imperceptible in practice).

---

## Troubleshooting

### Problem: "Command not found: llama-cli"

**Cause:** llama.cpp not in PATH.

**Solution:**

```bash
# If installed via Homebrew
brew link llama.cpp

# If built from source
export PATH="/path/to/llama.cpp:$PATH"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export PATH="/path/to/llama.cpp:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Problem: "Failed to load model"

**Cause:** Invalid model path or corrupted model file.

**Solution:**

1. **Verify path is absolute:**
   ```bash
   # Wrong (relative path)
   model: "models/llama.gguf"

   # Correct (absolute path)
   model: "/Users/yourname/llama-models/llama.gguf"
   ```

2. **Verify file exists:**
   ```bash
   ls -lh /path/to/model.gguf
   # Should show file size (~800MB for 1B, ~4GB for 8B)
   ```

3. **Test model directly:**
   ```bash
   llama-cli -m /path/to/model.gguf -p "test" -n 10
   # Should output text, not error
   ```

4. **Re-download if corrupted:**
   ```bash
   # Check file size matches expected (e.g., 4.3GB for Llama 3 8B Q4)
   # If not, re-download
   ```

### Problem: "Out of memory"

**Symptom:**
```
error: failed to allocate memory for model
```

**Cause:** Model too large for available RAM.

**Solution:**

1. **Check RAM requirements:**
   - 1B Q4: ~2GB RAM
   - 8B Q4: ~8GB RAM
   - 13B Q4: ~12GB RAM
   - 70B Q4: ~48GB RAM

2. **Use smaller model or quantization:**
   ```bash
   # Instead of Q8_0 (8.5GB), use Q4_K_M (4.3GB)
   ```

3. **Reduce context size:**
   ```yaml
   args:
     - "-c"
     - "1024"  # Reduced from 2048
   ```

4. **Use GPU offloading** (if available):
   ```yaml
   args:
     - "-ngl"
     - "32"    # Offload 32 layers to GPU (frees RAM)
   ```

### Problem: "Slow inference (5+ tokens/sec)"

**Cause:** CPU-only inference without GPU acceleration.

**Solution:**

1. **Verify GPU support:**
   ```bash
   # Check if llama.cpp was built with GPU support
   llama-cli --version

   # Should show: "Metal support" (macOS) or "CUDA support" (NVIDIA)
   ```

2. **Rebuild with GPU support:**
   ```bash
   # macOS
   make clean && make LLAMA_METAL=1

   # NVIDIA
   make clean && make LLAMA_CUDA=1
   ```

3. **Enable GPU layers:**
   ```yaml
   args:
     - "-ngl"
     - "99"    # Offload all layers to GPU
   ```

4. **Verify GPU is being used:**
   ```bash
   # During inference, check GPU utilization
   # macOS: sudo powermetrics --samplers gpu_power -i 1000
   # NVIDIA: nvidia-smi -l 1
   # Should show high GPU usage (80-100%)
   ```

### More Troubleshooting

See the comprehensive [HTTP Adapter Troubleshooting Guide](../troubleshooting/http-adapters.md) for additional issues.

---

## Advanced Usage

### Custom Inference Parameters

Fine-tune generation quality and speed:

```yaml
cli_tools:
  llamacpp:
    command: "llama-cli"
    args:
      - "-m"
      - "{model}"
      - "-p"
      - "{prompt}"
      - "-n"
      - "1024"           # Max tokens to generate
      - "-c"
      - "4096"           # Context window size
      - "-t"
      - "16"             # CPU threads (match your cores)
      - "--temp"
      - "0.7"            # Temperature (0.0-2.0, lower = more deterministic)
      - "--top-p"
      - "0.95"           # Nucleus sampling (0.0-1.0)
      - "--top-k"
      - "40"             # Top-K sampling (0 = disabled)
      - "--repeat-penalty"
      - "1.1"            # Prevent repetition (1.0 = disabled)
      - "--repeat-last-n"
      - "64"             # Look back N tokens for repetition
      - "-ngl"
      - "99"             # GPU layers (Metal/CUDA)
      - "--mlock"        # Lock model in RAM (prevent swapping)
```

### Running HTTP Server

llama.cpp includes `llama-server` for OpenAI-compatible API:

```bash
# Start HTTP server
llama-server \
  -m ~/llama-models/llama-3.2-1b-instruct-q4.gguf \
  -c 2048 \
  --port 8080 \
  -ngl 99

# Server runs on http://localhost:8080
```

**Then configure AI Counsel to use HTTP adapter:**

```yaml
adapters:
  llamacpp_http:
    type: http
    base_url: "http://localhost:8080"
    timeout: 120
```

**Advantage:** OpenAI-compatible API, better for concurrent requests.

### Batch Processing

Process multiple deliberations in parallel:

```bash
# Run 4 llama-server instances on different ports
llama-server -m model.gguf --port 8081 -ngl 24 &  # GPU layers split
llama-server -m model.gguf --port 8082 -ngl 24 &
llama-server -m model.gguf --port 8083 -ngl 24 &
llama-server -m model.gguf --port 8084 -ngl 24 &

# Configure 4 adapters in config.yaml
# Run 4 deliberations concurrently
```

**Use case:** High-throughput batch deliberations.

---

## Next Steps

You've mastered llama.cpp—the most powerful local inference engine!

### Recommended Learning Path

1. **Experiment with models:**
   - Download multiple quantization levels (Q4, Q5, Q8)
   - Benchmark on your hardware (tokens/sec)
   - Find optimal quality/speed balance

2. **Optimize inference:**
   - Tune `-t` threads to match CPU cores
   - Adjust `-ngl` layers for optimal GPU/RAM split
   - Experiment with temperature/top-p for desired creativity

3. **Mix with other adapters:**
   ```javascript
   participants: [
     {cli: "llamacpp", model: "/path/to/llama-8b-q4.gguf"},
     {cli: "ollama", model: "mistral"},        // Simpler management
     {cli: "claude", model: "sonnet"}          // Cloud validation
   ]
   ```

4. **Production deployment:**
   - Use `llama-server` for concurrent requests
   - Monitor performance with `nvidia-smi` / `powermetrics`
   - Implement request queueing for load balancing

---

## Summary

**What you learned:**
✅ Install llama.cpp (fastest local inference engine)
✅ Download GGUF models from Hugging Face
✅ Configure AI Counsel with optimal parameters
✅ Run zero-cost deliberations at maximum performance
✅ Troubleshoot common issues
✅ Benchmark and optimize for your hardware
✅ Enable GPU acceleration (Metal/CUDA)

**Result:** Maximum-performance unlimited AI deliberations at $0 cost.

**llama.cpp vs Ollama/LM Studio:**
- **llama.cpp:** Best for maximum performance, advanced users, custom pipelines
- **Ollama:** Best for simplicity, ease of use, model management
- **LM Studio:** Best for GUI users, visual exploration

**Performance:** llama.cpp with GPU can be 2-3x faster than Ollama (same model/quantization) due to fine-tuned parameters.

**Questions?** Check the [Troubleshooting Guide](../troubleshooting/http-adapters.md) or [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp/discussions).

---

**Related Guides:**
- [Local Model Support Overview](intro.md)
- [Ollama Quickstart](ollama-quickstart.md)
- [LM Studio Quickstart](lmstudio-quickstart.md)
- [OpenRouter Guide](openrouter-guide.md)
- [Troubleshooting](../troubleshooting/http-adapters.md)
