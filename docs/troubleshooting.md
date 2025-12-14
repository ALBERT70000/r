# Troubleshooting Guide

This guide covers common issues and their solutions when using R CLI.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Installation Problems](#installation-problems)
- [Performance Issues](#performance-issues)
- [Skill-Specific Issues](#skill-specific-issues)
- [Configuration Problems](#configuration-problems)

---

## Connection Issues

### "LLM not detected" or Connection Refused

**Symptoms:**
- Error: "No se pudo conectar con LLM"
- Error: "Connection refused"
- R CLI hangs when starting

**Solutions:**

1. **Check if your LLM backend is running:**

   For LM Studio:
   ```bash
   curl http://localhost:1234/v1/models
   ```

   For Ollama:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Start your backend:**

   LM Studio: Open the app and load a model

   Ollama:
   ```bash
   ollama serve
   ```

3. **Check backend status:**
   ```bash
   r status
   ```

4. **Verify configuration:**
   ```bash
   r config
   ```

### Timeout Errors

**Symptoms:**
- Error: "Timeout waiting for response"
- Slow or hanging responses

**Solutions:**

1. **Check server load** - The model might be processing a large request

2. **Reduce request size:**
   ```bash
   r config --max-tokens 2000
   ```

3. **Use a smaller/faster model**

4. **Check system resources:**
   ```bash
   # macOS
   top -l 1 | head -20

   # Check memory
   vm_stat
   ```

### Rate Limit Errors

**Symptoms:**
- Error: "Rate limit exceeded"
- 429 status code

**Solutions:**

1. Wait a few seconds before retrying
2. Reduce request frequency
3. For local LLMs, this is rare - check if the server is overloaded

---

## Installation Problems

### Missing Dependencies

**Symptoms:**
- ImportError for specific packages
- "ModuleNotFoundError"

**Solutions:**

1. **Install base package:**
   ```bash
   pip install r-cli-ai
   ```

2. **Install with all features:**
   ```bash
   pip install r-cli-ai[all]
   ```

3. **Install specific features:**
   ```bash
   # RAG support
   pip install r-cli-ai[rag]

   # Voice support
   pip install r-cli-ai[voice]

   # MLX for Apple Silicon
   pip install r-cli-ai[mlx]
   ```

### sentence-transformers Import Error

**Symptoms:**
- Error: "No module named 'sentence_transformers'"
- RAG features not working

**Solution:**
```bash
pip install sentence-transformers chromadb
# or
pip install r-cli-ai[rag]
```

### MLX Not Working

**Symptoms:**
- Error: "MLX solo está disponible en Apple Silicon"
- MLX backend not detected

**Solutions:**

1. **Verify you're on Apple Silicon:**
   ```bash
   uname -m  # Should show arm64
   ```

2. **Install MLX-LM:**
   ```bash
   pip install mlx-lm
   ```

3. **Check installation:**
   ```bash
   python -c "import mlx_lm; print('OK')"
   ```

### PyTorch/CUDA Issues

**Symptoms:**
- CUDA out of memory
- Slow inference on GPU

**Solutions:**

1. **For CPU-only (smaller models):**
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   ```

2. **Check CUDA availability:**
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

---

## Performance Issues

### Slow Responses

**Possible Causes & Solutions:**

1. **Model too large for RAM:**
   - Use a smaller quantized model (4-bit or 8-bit)
   - For Ollama: `ollama run qwen2.5:7b-instruct-q4_K_M`

2. **Disk swapping:**
   - Close other applications
   - Use a smaller model

3. **Network latency (for API-based):**
   - Use a local backend instead

### High Memory Usage

**Solutions:**

1. **Use smaller models:**
   ```bash
   r config --model qwen2.5:3b
   ```

2. **Limit context window:**
   ```bash
   r config --max-tokens 2000
   ```

3. **Clear conversation history:**
   ```bash
   r clear
   ```

### MLX Performance on Mac

**Optimization tips:**

1. **Use 4-bit quantized models:**
   ```bash
   r config --backend mlx --model qwen2.5-7b
   ```

2. **Close GPU-heavy applications** (browsers, video editors)

3. **Check memory pressure:**
   ```bash
   sudo memory_pressure
   ```

---

## Skill-Specific Issues

### PDF Generation Fails

**Symptoms:**
- Error: "fpdf2 not installed"
- PDF not created

**Solutions:**

1. **Install PDF dependencies:**
   ```bash
   pip install fpdf2 markdown
   ```

2. **Check output directory:**
   ```bash
   ls ~/r-cli-output/
   ```

3. **Verify write permissions**

### SQL Skill Not Working

**Symptoms:**
- Error: "Database connection failed"
- "sqlite3 not found"

**Solutions:**

1. **Install database drivers:**
   ```bash
   pip install sqlalchemy
   ```

2. **Check database file exists**

3. **Verify file permissions**

### Voice Skill Issues

**Symptoms:**
- Error: "whisper not installed"
- No audio output

**Solutions:**

1. **Install voice dependencies:**
   ```bash
   pip install openai-whisper piper-tts
   ```

2. **Check microphone permissions** (macOS: System Preferences > Security & Privacy > Microphone)

3. **Verify audio output:**
   ```bash
   # Test speakers
   say "Hello" # macOS
   ```

### RAG/Vector Search Issues

**Symptoms:**
- "ChromaDB not initialized"
- Search returns no results

**Solutions:**

1. **Install RAG dependencies:**
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Initialize the database:**
   ```bash
   r rag init
   ```

3. **Check vector DB directory:**
   ```bash
   ls ~/.r-cli/vectordb/
   ```

---

## Configuration Problems

### Config File Not Found

**Location:** `~/.r-cli/config.yaml`

**Create default config:**
```bash
r config --reset
```

### Invalid Configuration

**Symptoms:**
- YAML parsing errors
- Unknown backend errors

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('~/.r-cli/config.yaml'))"
   ```

2. **Reset to defaults:**
   ```bash
   rm ~/.r-cli/config.yaml
   r config
   ```

3. **Example valid config:**
   ```yaml
   llm:
     backend: ollama
     model: qwen2.5:7b
     temperature: 0.7
     max_tokens: 4096

   rag:
     enabled: true

   ui:
     theme: ps2
     show_thinking: true
   ```

### Backend-Specific Configuration

**Ollama:**
```yaml
llm:
  backend: ollama
  model: qwen2.5:7b
  # Ollama runs on port 11434 by default
```

**LM Studio:**
```yaml
llm:
  backend: lm-studio
  base_url: http://localhost:1234/v1
  model: local-model
```

**MLX (Apple Silicon):**
```yaml
llm:
  backend: mlx
  model: qwen2.5-7b  # Uses mlx-community model
```

---

## Getting Help

### View Logs

```bash
# Log location
cat ~/.r-cli/logs/r_cli.log

# Recent errors
tail -100 ~/.r-cli/logs/r_cli.log | grep ERROR
```

### Debug Mode

```bash
# Set environment variable for verbose output
export R_CLI_DEBUG=1
r chat
```

### Report Issues

1. Check existing issues: https://github.com/raym33/r/issues

2. Include in your report:
   - R CLI version: `r --version`
   - Python version: `python --version`
   - OS and version
   - Backend being used
   - Error message and logs
   - Steps to reproduce

### Community Support

- GitHub Issues: https://github.com/raym33/r/issues
- Discussions: https://github.com/raym33/r/discussions
