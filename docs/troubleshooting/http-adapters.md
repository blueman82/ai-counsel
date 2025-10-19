# HTTP Adapter Troubleshooting Guide

This guide helps diagnose and fix common issues with HTTP adapters (Ollama, LM Studio, OpenRouter).

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Authentication Issues](#authentication-issues)
3. [Request Issues](#request-issues)
4. [Response Issues](#response-issues)
5. [Performance Issues](#performance-issues)
6. [Debugging Tips](#debugging-tips)

---

## Connection Issues

### Problem: "Connection refused" or "Failed to connect"

**Error message:**
```
ERROR: Connection refused to http://localhost:11434
```

**Root cause:** The HTTP server (Ollama, LM Studio) is not running or listening on the wrong port.

**Solution:**

1. **Verify the service is running:**

   **For Ollama:**
   ```bash
   # Check if Ollama is running
   ps aux | grep ollama

   # Start Ollama if not running
   ollama serve

   # Test connection
   curl http://localhost:11434/api/tags
   ```

   **For LM Studio:**
   - Open LM Studio application
   - Go to "Local Server" tab
   - Click "Start Server"
   - Verify port number (default: 1234)

2. **Verify the port in config.yaml matches:**
   ```yaml
   adapters:
     ollama:
       base_url: "http://localhost:11434"  # Check port number
   ```

3. **Check for port conflicts:**
   ```bash
   # See what's using the port
   lsof -i :11434  # For Ollama
   lsof -i :1234   # For LM Studio
   ```

**Prevention:**
- Add Ollama to startup services: `systemctl enable ollama` (Linux)
- Keep LM Studio server running during deliberations

---

### Problem: "Network timeout" or "Connection timeout"

**Error message:**
```
ERROR: Request timed out after 60 seconds
```

**Root cause:** Request exceeded configured timeout, often due to slow model loading or generation.

**Solution:**

1. **Increase timeout in config.yaml:**
   ```yaml
   adapters:
     ollama:
       timeout: 180  # 3 minutes (was 60)
   ```

2. **For first request with cold model:**
   - Models need time to load into memory (5-30 seconds)
   - Subsequent requests are faster
   - Consider pre-warming: `curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"hi"}'`

3. **For slow generation:**
   - Larger models need more time (70B models may need 120-300s)
   - Check model is appropriate for your hardware
   - Monitor system resources (RAM, CPU)

**Prevention:**
- Use timeout values appropriate for model size:
  - Small models (7B): 60-90 seconds
  - Medium models (13B-30B): 90-180 seconds
  - Large models (70B+): 180-300 seconds

---

### Problem: "Connection reset by peer" or "Broken pipe"

**Error message:**
```
ERROR: Connection reset by peer
```

**Root cause:** Server crashed or restarted during request.

**Solution:**

1. **Check server logs:**

   **Ollama:**
   ```bash
   # Check Ollama logs
   journalctl -u ollama -n 100
   # Or if running in terminal:
   # Check the terminal where `ollama serve` is running
   ```

   **LM Studio:**
   - Check LM Studio console output
   - Look for error messages or crashes

2. **Verify server resources:**
   ```bash
   # Check available RAM
   free -h

   # Check if process was killed
   dmesg | grep -i kill
   ```

3. **HTTP adapter will automatically retry:**
   - Built-in exponential backoff
   - Default: 3 retries
   - Increase if needed: `max_retries: 5`

**Prevention:**
- Ensure sufficient RAM for model (check model requirements)
- Monitor system resources during deliberations
- Use appropriately sized models for your hardware

---

## Authentication Issues

### Problem: "Unauthorized" (401) or "Forbidden" (403)

**Error message:**
```
ERROR: HTTP 401 Unauthorized
ERROR: HTTP 403 Forbidden
```

**Root cause:** Missing, invalid, or expired API key.

**Solution:**

1. **Verify environment variable is set:**
   ```bash
   # Check if variable exists
   echo $OPENROUTER_API_KEY

   # Should output your key, not blank
   ```

2. **Set environment variable:**
   ```bash
   # For current session
   export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

   # For permanent (add to ~/.bashrc or ~/.zshrc)
   echo 'export OPENROUTER_API_KEY="sk-or-v1-your-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Verify config uses correct variable name:**
   ```yaml
   adapters:
     openrouter:
       api_key: "${OPENROUTER_API_KEY}"  # Must match env var name
   ```

4. **Test API key directly:**
   ```bash
   # For OpenRouter
   curl https://openrouter.ai/api/v1/auth/key \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"

   # Should return key info, not error
   ```

**Prevention:**
- Add API key to shell profile for persistence
- Use `.env` file and load with direnv
- Never commit API keys to git (use environment variables)

---

### Problem: "Invalid API key format"

**Error message:**
```
ERROR: API key format invalid
```

**Root cause:** API key has incorrect format or contains extra characters.

**Solution:**

1. **Check for whitespace or quotes:**
   ```bash
   # Wrong (has quotes)
   export OPENROUTER_API_KEY="'sk-or-v1-key'"

   # Correct
   export OPENROUTER_API_KEY="sk-or-v1-key"
   ```

2. **Verify key prefix:**
   - OpenRouter: Should start with `sk-or-v1-`
   - Check provider documentation for correct format

3. **Generate new key if corrupted:**
   - Visit provider dashboard
   - Revoke old key
   - Generate new key

**Prevention:**
- Copy API keys carefully (no extra spaces)
- Store in password manager for backup
- Test immediately after setting

---

## Request Issues

### Problem: "Invalid request" (400) or "Bad request"

**Error message:**
```
ERROR: HTTP 400 Bad Request - Invalid model name
```

**Root cause:** Request body format incorrect or invalid parameters.

**Solution:**

1. **Verify model name is correct:**
   ```yaml
   participants:
     - cli: "ollama"
       model: "llama3"  # Check spelling
   ```

2. **List available models:**
   ```bash
   # For Ollama
   ollama list

   # For OpenRouter
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

3. **Check provider-specific model naming:**
   - OpenRouter: Use full format like `anthropic/claude-3.5-sonnet`
   - Ollama: Use short names like `llama3` or `mistral`
   - LM Studio: Use model name from loaded models list

**Prevention:**
- Verify model names before running deliberation
- Use tab completion when available
- Check provider documentation for model IDs

---

### Problem: "Rate limit exceeded" (429)

**Error message:**
```
ERROR: HTTP 429 Too Many Requests
```

**Root cause:** Exceeded provider's rate limits.

**Solution:**

1. **HTTP adapters automatically retry with backoff:**
   - Initial retry: 1 second
   - Second retry: 2 seconds
   - Third retry: 4 seconds
   - Up to `max_retries` (default: 3)

2. **Increase retry attempts:**
   ```yaml
   adapters:
     openrouter:
       max_retries: 5  # More retries for rate limits
   ```

3. **Add delay between deliberations:**
   - Space out deliberations if running many
   - Check provider's rate limit documentation

4. **Check rate limit headers:**
   ```bash
   # See rate limit info
   curl -I https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"

   # Look for:
   # X-RateLimit-Limit: 100
   # X-RateLimit-Remaining: 99
   # X-RateLimit-Reset: 1234567890
   ```

**Prevention:**
- Use local adapters (Ollama, LM Studio) for unlimited requests
- Upgrade to higher tier plan if frequently hitting limits
- Implement request batching or queueing

---

### Problem: "Payload too large" (413)

**Error message:**
```
ERROR: HTTP 413 Payload Too Large
```

**Root cause:** Prompt or context exceeds provider's limits.

**Solution:**

1. **Check prompt length:**
   - Most providers: 32K-100K tokens
   - Calculate: ~4 characters per token
   - Use shorter prompts or context

2. **For context-heavy deliberations:**
   - Reduce number of rounds (less context accumulation)
   - Summarize earlier rounds instead of including full text
   - Use models with larger context windows

3. **Check model-specific limits:**
   ```bash
   # For OpenRouter
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     | jq '.data[] | {name: .id, context_length: .context_length}'
   ```

**Prevention:**
- Monitor prompt size in deliberations
- Use quick mode for simple questions
- Choose models with appropriate context windows

---

## Response Issues

### Problem: "Unexpected response format" or parsing errors

**Error message:**
```
ERROR: Failed to parse response: 'response' key not found
```

**Root cause:** HTTP adapter received unexpected JSON structure from provider.

**Solution:**

1. **Check server logs:**
   ```bash
   # AI Counsel logs
   tail -f mcp_server.log

   # Look for raw response JSON
   ```

2. **Test provider API directly:**
   ```bash
   # For Ollama
   curl http://localhost:11434/api/generate \
     -d '{"model":"llama3","prompt":"test"}' | jq .

   # For OpenRouter
   curl https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"anthropic/claude-3.5-sonnet","messages":[{"role":"user","content":"test"}]}' | jq .
   ```

3. **Verify adapter implementation:**
   - Check `adapters/ollama.py`, `adapters/lmstudio.py`, etc.
   - Ensure `parse_response()` matches current API format

**Prevention:**
- Keep adapters updated with provider API changes
- Monitor provider API documentation for breaking changes
- Report parsing issues to ai-counsel GitHub

---

### Problem: "Empty response" or blank output

**Error message:**
```
ERROR: Received empty response from adapter
```

**Root cause:** Model returned empty string or provider failed silently.

**Solution:**

1. **Test model directly:**
   ```bash
   # For Ollama
   ollama run llama3 "Hello"

   # Should get response, not blank
   ```

2. **Check model status:**
   ```bash
   # For Ollama
   ollama list

   # Verify model is fully downloaded
   # Check SIZE column is not "0 B"
   ```

3. **Try different model:**
   - Model may be corrupted
   - Try another model: `ollama pull mistral`

**Prevention:**
- Verify models work before using in deliberations
- Keep models updated: `ollama pull llama3`
- Monitor provider status pages for outages

---

## Performance Issues

### Problem: "Slow responses" or "Deliberation taking too long"

**Symptoms:**
- Each round takes 60+ seconds
- Deliberations timeout frequently

**Root cause:** Model loading, slow generation, or resource constraints.

**Solution:**

1. **Optimize model choice:**
   - Use smaller models for faster responses:
     - 7B models: 5-15 seconds
     - 13B models: 15-30 seconds
     - 70B models: 30-120+ seconds

2. **Pre-warm models:**
   ```bash
   # For Ollama - load model into memory first
   curl http://localhost:11434/api/generate \
     -d '{"model":"llama3","prompt":"warmup","keep_alive":"10m"}'
   ```

3. **Optimize hardware:**
   - Use GPU if available: `ollama run llama3` (auto-detects)
   - Close other applications (free up RAM)
   - Check CPU/GPU usage: `nvidia-smi` or `top`

4. **Adjust timeout for expected performance:**
   ```yaml
   adapters:
     ollama:
       timeout: 120  # Allow more time for slower hardware
   ```

**Prevention:**
- Choose models appropriate for hardware
- Monitor system resources during deliberations
- Use quick mode for simple questions

---

### Problem: "Retry exhaustion" or "Max retries exceeded"

**Error message:**
```
ERROR: Max retries (3) exceeded for request
```

**Root cause:** Persistent failures (network, server errors) exceeded retry limit.

**Solution:**

1. **Check underlying issue:**
   - Connection problems? See [Connection Issues](#connection-issues)
   - Rate limits? See [Rate Limit](#problem-rate-limit-exceeded-429)
   - Server errors? Check provider status

2. **Increase retry limit:**
   ```yaml
   adapters:
     openrouter:
       max_retries: 5  # More attempts
   ```

3. **Check provider status:**
   - OpenRouter: https://status.openrouter.ai/
   - Anthropic: https://status.anthropic.com/
   - OpenAI: https://status.openai.com/

**Prevention:**
- Use reliable providers
- Monitor provider status before large deliberations
- Have backup adapters configured (fallback to local)

---

### Problem: "High memory usage" or "Out of memory"

**Symptoms:**
- System becomes slow during deliberations
- Process killed with "Killed" message
- `dmesg` shows OOM killer

**Root cause:** Model too large for available RAM.

**Solution:**

1. **Check model RAM requirements:**
   - 7B model: ~8GB RAM
   - 13B model: ~16GB RAM
   - 30B model: ~32GB RAM
   - 70B model: ~64GB RAM

2. **Use smaller model:**
   ```bash
   # Instead of llama3:70b
   ollama pull llama3:7b
   ```

3. **Close other applications:**
   ```bash
   # Free up memory
   # Close browsers, IDEs, etc.
   ```

4. **Use cloud adapter instead:**
   - OpenRouter doesn't use local RAM
   - Offload to cloud for large models

**Prevention:**
- Choose models within RAM limits
- Monitor memory: `free -h` or Activity Monitor
- Use cloud adapters for large models

---

## Debugging Tips

### Enable Debug Logging

1. **Check server logs:**
   ```bash
   tail -f mcp_server.log
   ```

2. **Increase logging verbosity:**
   ```python
   # In server.py or adapter files
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Test Adapters Independently

**Test Ollama adapter:**
```python
import asyncio
from adapters.ollama import OllamaAdapter

async def test():
    adapter = OllamaAdapter(
        base_url="http://localhost:11434",
        timeout=60
    )
    result = await adapter.invoke(prompt="Hello", model="llama3")
    print(result)

asyncio.run(test())
```

**Test OpenRouter adapter:**
```python
import asyncio
from adapters.openrouter import OpenRouterAdapter
import os

async def test():
    adapter = OpenRouterAdapter(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        timeout=60
    )
    result = await adapter.invoke(
        prompt="Hello",
        model="anthropic/claude-3.5-sonnet"
    )
    print(result)

asyncio.run(test())
```

### Verify Configuration

1. **Check config loading:**
   ```bash
   python3 -c "from models.config import load_config; c = load_config('config.yaml'); print(c)"
   ```

2. **Verify environment variables:**
   ```bash
   env | grep API_KEY
   ```

3. **Test adapter creation:**
   ```bash
   python3 -c "from adapters import create_adapter; from models.config import load_config; c = load_config('config.yaml'); a = create_adapter('ollama', c.adapters['ollama']); print(a)"
   ```

### Common Debugging Commands

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test OpenRouter authentication
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Check running processes
ps aux | grep -E "(ollama|lmstudio)"

# Check port usage
lsof -i :11434
lsof -i :1234

# Monitor system resources
htop
nvidia-smi  # For GPU

# Check logs
tail -f mcp_server.log
journalctl -u ollama -f
```

### Getting Help

1. **Check logs first:**
   - `mcp_server.log` - AI Counsel server logs
   - Provider logs (Ollama, LM Studio console)

2. **Search existing issues:**
   - GitHub: https://github.com/blueman82/ai-counsel/issues
   - Search for error message

3. **Create detailed bug report:**
   - Include error message
   - Include relevant config
   - Include adapter type and model
   - Include steps to reproduce

4. **Community support:**
   - GitHub Discussions
   - Provider Discord/forums (for provider-specific issues)

---

## Quick Reference

### Checklist for New HTTP Adapter Setup

- [ ] Service is running (Ollama, LM Studio)
- [ ] Port in config matches service port
- [ ] Environment variables set (if using API keys)
- [ ] Model is downloaded/available
- [ ] Test connection with curl
- [ ] Timeout is appropriate for model size
- [ ] Test with single deliberation first

### Common Error Codes

| Code | Meaning | Common Cause | Solution |
|------|---------|--------------|----------|
| 400 | Bad Request | Invalid model name | Check model list |
| 401 | Unauthorized | Missing/invalid API key | Set environment variable |
| 403 | Forbidden | API key lacks permissions | Check key permissions |
| 404 | Not Found | Endpoint or model not found | Verify base_url and model |
| 413 | Payload Too Large | Prompt too long | Reduce prompt size |
| 429 | Rate Limited | Too many requests | Wait or increase retries |
| 500 | Server Error | Provider issue | Check provider status |
| 502 | Bad Gateway | Proxy/network issue | Check network |
| 503 | Service Unavailable | Server overloaded | Retry later |
| 504 | Gateway Timeout | Request too slow | Increase timeout |

### Recommended Timeouts by Model Size

| Model Size | Timeout (seconds) |
|------------|-------------------|
| 7B | 60-90 |
| 13B | 90-120 |
| 30B | 120-180 |
| 70B+ | 180-300 |

### Recommended max_retries by Adapter Type

| Adapter | max_retries | Reason |
|---------|-------------|--------|
| Ollama (local) | 2-3 | Fast, reliable locally |
| LM Studio (local) | 2-3 | Fast, reliable locally |
| OpenRouter (cloud) | 3-5 | May have rate limits/network issues |

---

**Last updated:** 2025-01-19
**Version:** 1.0.0
