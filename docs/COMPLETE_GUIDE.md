# R CLI Complete Guide

**Your Local AI Operating System** - 100% Private, 100% Offline, 100% Yours

This comprehensive guide covers everything you can do with R CLI.

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [API Server (Daemon Mode)](#api-server-daemon-mode)
5. [All 27 Skills](#all-27-skills)
6. [Interactive Mode](#interactive-mode)
7. [Direct Commands](#direct-commands)
8. [Plugin System](#plugin-system)
9. [Creating Custom Skills](#creating-custom-skills)
10. [Memory & RAG System](#memory--rag-system)
11. [Themes & UI](#themes--ui)
12. [Troubleshooting](#troubleshooting)
13. [API Reference](#api-reference)

---

## Installation

### From PyPI (Recommended)

```bash
# Basic installation
pip install r-cli-ai

# With semantic search (RAG with ChromaDB)
pip install r-cli-ai[rag]

# With voice mode (Whisper transcription + Piper TTS)
pip install r-cli-ai[audio]

# With image generation (Stable Diffusion)
pip install r-cli-ai[design]

# With OCR (Tesseract)
pip install r-cli-ai[ocr]

# Everything included
pip install r-cli-ai[all]
```

### From Source

```bash
git clone https://github.com/raym33/r.git
cd r
pip install -e .

# With all optional dependencies
pip install -e ".[all]"
```

### Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) or [LM Studio](https://lmstudio.ai/)
- 8GB+ RAM (16GB+ recommended)
- macOS, Linux, or Windows

### Setting Up the LLM Backend

**Option 1: Ollama (Recommended)**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull qwen3:4b      # Fast, 4GB
ollama pull qwen2.5:7b    # Balanced, 8GB
ollama pull qwen2.5:32b   # High quality, 20GB

# Start the server
ollama serve
```

**Option 2: LM Studio**

1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Load a model (e.g., Qwen2.5-7B-Instruct)
3. Start the local server (default port: 1234)

---

## Configuration

### Config File Location

```
~/.r-cli/config.yaml
```

### Complete Configuration Options

```yaml
# LLM Configuration
llm:
  backend: ollama              # ollama, lm-studio, openai-compatible, auto
  model: qwen3:4b              # Model name
  base_url: http://localhost:11434/v1  # API endpoint
  api_key: not-needed          # API key (not needed for local)
  temperature: 0.7             # Creativity (0.0-1.0)
  max_tokens: 4096             # Max response length

  # Timeouts (seconds)
  request_timeout: 60.0        # Timeout for LLM requests
  skill_timeout: 120.0         # Timeout for skill execution
  connection_timeout: 10.0     # Timeout for initial connection

  # Token limits
  max_context_tokens: 8192     # Maximum context window
  token_warning_threshold: 0.8 # Warn at 80% of limit

  # Specialized models (optional)
  coder_model: null            # Model for code tasks
  vision_model: null           # Model for vision tasks

# RAG (Retrieval Augmented Generation)
rag:
  enabled: true
  chunk_size: 1000             # Text chunk size
  chunk_overlap: 200           # Overlap between chunks
  collection_name: r_cli_knowledge
  persist_directory: ~/.r-cli/vectordb

# User Interface
ui:
  theme: ps2                   # ps2, matrix, minimal, retro
  show_thinking: true          # Show agent reasoning
  show_tool_calls: true        # Show tool executions
  animation_speed: 0.05        # Animation speed

# Skills Configuration
skills:
  mode: blacklist              # blacklist or whitelist
  disabled: []                 # Skills to disable
  enabled: []                  # Skills to enable (whitelist mode)
  require_confirmation:        # Skills that need user confirmation
    - ssh
    - docker
    - email

# Directories
home_dir: ~/.r-cli
skills_dir: ~/.r-cli/skills
output_dir: ~/r-cli-output
```

### Quick Setup for Ollama

```bash
mkdir -p ~/.r-cli
cat > ~/.r-cli/config.yaml << 'EOF'
llm:
  backend: ollama
  model: qwen3:4b
  base_url: http://localhost:11434/v1
EOF
```

### Quick Setup for LM Studio

```bash
mkdir -p ~/.r-cli
cat > ~/.r-cli/config.yaml << 'EOF'
llm:
  backend: lm-studio
  model: local-model
  base_url: http://localhost:1234/v1
EOF
```

---

## Basic Usage

### Command Line Alias

The `r` command may conflict with shell built-ins. Set up an alias:

```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'alias r="/path/to/python/bin/r"' >> ~/.zshrc
source ~/.zshrc

# Find your Python bin path
pip show r-cli-ai | grep Location
```

### Interactive Mode

```bash
r                    # Start interactive mode
r --theme matrix     # With Matrix theme
r --no-animation     # Without animations
```

### Direct Chat

```bash
r chat "What is Python?"
r chat "Explain machine learning in simple terms"
r chat --stream "Write a story about a robot"  # With streaming

# Start API server (daemon mode)
r serve --port 8765
```

### Direct Skill Execution

```bash
r pdf "My document content" --title "Report"
r code "fibonacci function" --lang python
r sql data.csv "SELECT * FROM data WHERE value > 100"
```

---

## API Server (Daemon Mode)

R CLI can run as a REST API server for integration with IDEs, scripts, and other applications.

### Starting the Server

```bash
# Default: localhost:8765
r serve

# Custom port
r serve --port 8080

# Listen on all interfaces
r serve --host 0.0.0.0

# Development mode with auto-reload
r serve --reload

# Multiple workers
r serve --workers 4
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Simple health status |
| `/v1/status` | GET | Detailed status (LLM connection, skills, uptime) |
| `/v1/chat` | POST | Chat completions (OpenAI-compatible, supports streaming) |
| `/v1/skills` | GET | List all skills and their tools |
| `/v1/skills/{name}` | GET | Get details about a specific skill |
| `/v1/skills/call` | POST | Direct tool invocation |

### API Documentation

When the server is running, interactive documentation is available at:
- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

### Example: Chat Request

```bash
# Non-streaming
curl -X POST http://localhost:8765/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'

# Streaming
curl -X POST http://localhost:8765/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

### Example: Direct Tool Call

```bash
curl -X POST http://localhost:8765/v1/skills/call \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "pdf",
    "tool": "generate_pdf",
    "arguments": {"content": "Hello World", "output": "test.pdf"}
  }'
```

### Example: List All Skills

```bash
curl http://localhost:8765/v1/skills | jq
```

### Running as a Service

**macOS (launchd):**
```bash
cp services/com.rcli.agent.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.rcli.agent.plist

# Check status
launchctl list | grep rcli

# Stop
launchctl unload ~/Library/LaunchAgents/com.rcli.agent.plist
```

**Linux (systemd):**
```bash
sudo cp services/r-cli.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable r-cli
sudo systemctl start r-cli

# Check status
sudo systemctl status r-cli

# View logs
journalctl -u r-cli -f
```

---

## All 27 Skills

### 1. PDF Skill

Generate PDF documents from text.

```bash
# Basic usage
r pdf "This is my document content"

# With options
r pdf "Report content" --title "Q4 Report" --author "John Doe"
r pdf "Meeting notes" --template business
r pdf "$(cat notes.txt)" --output ~/Documents/notes.pdf
```

**In chat:**
```
▶ Generate a PDF with a summary of Python features
▶ Create a PDF report about climate change
```

### 2. LaTeX Skill

Compile LaTeX documents to professional PDFs.

```bash
# Compile a .tex file
r latex document.tex

# With output path
r latex thesis.tex --output ~/Documents/thesis.pdf
```

**In chat:**
```
▶ Compile my LaTeX document at ~/paper.tex
▶ Create a LaTeX document about quantum physics and compile it
```

### 3. Code Skill

Generate, analyze, and execute code.

```bash
# Generate code
r code "sorting algorithm" --lang python
r code "REST API client" --lang javascript
r code "binary search tree" --lang rust

# Generate and run
r code "hello world" --lang python --run

# Analyze existing code
r code --analyze ~/project/main.py
```

**In chat:**
```
▶ Write a Python function to calculate prime numbers
▶ Create a JavaScript async function to fetch data from an API
▶ Analyze the code in ~/myproject/app.py
```

### 4. SQL Skill

Query CSV files and databases using natural language.

```bash
# Query a CSV file
r sql sales.csv "SELECT * FROM data"
r sql customers.csv "SELECT name, email FROM data WHERE country = 'USA'"
r sql orders.csv "SELECT product, SUM(quantity) FROM data GROUP BY product"

# Query a SQLite database
r sql database.db "SELECT * FROM users WHERE active = 1"

# Natural language queries
r sql data.csv "show me the top 10 products by revenue"
```

**In chat:**
```
▶ Query sales.csv and show total revenue by month
▶ Find all customers from the CSV who made purchases over $1000
```

### 5. Resume Skill

Summarize long documents and texts.

```bash
# Summarize a PDF
r resume document.pdf
r resume report.pdf --style brief
r resume thesis.pdf --style detailed

# Summarize text
r resume "$(cat long_article.txt)"

# Different styles
r resume paper.pdf --style bullets    # Bullet points
r resume paper.pdf --style executive  # Executive summary
```

**In chat:**
```
▶ Summarize the PDF at ~/Downloads/report.pdf
▶ Give me a brief summary of this research paper
```

### 6. File System (FS) Skill

Manage files and directories.

```bash
# List files
r fs --list "*.py"
r fs --list ~/Documents --recursive

# Read files
r fs --read ~/notes.txt

# Search in files
r fs --search "TODO" --path ~/project

# File info
r fs --info ~/Documents/report.pdf
```

**In chat:**
```
▶ List all Python files in my project
▶ Search for "API_KEY" in all files under ~/code
▶ Show me the contents of ~/.bashrc
```

### 7. OCR Skill

Extract text from images and scanned documents.

```bash
# Extract text from image
r ocr image.png
r ocr screenshot.jpg --lang eng

# Multiple languages
r ocr document.png --lang eng+spa

# From PDF (scanned)
r ocr scanned_document.pdf
```

**Supported languages:** eng, spa, fra, deu, ita, por, rus, chi_sim, jpn, kor, ara

**In chat:**
```
▶ Extract text from the image at ~/Downloads/receipt.jpg
▶ OCR this scanned document and translate it to English
```

### 8. Voice Skill

Speech-to-text transcription and text-to-speech synthesis.

```bash
# Transcribe audio (requires Whisper)
r voice --transcribe audio.mp3
r voice --transcribe meeting.wav --model medium

# Text-to-speech (requires Piper)
r voice --speak "Hello, this is R CLI"
r voice --speak "$(cat script.txt)" --output speech.wav

# Transcribe and summarize
r voice --transcribe lecture.mp3 --summarize
```

**In chat:**
```
▶ Transcribe the audio file at ~/recordings/meeting.mp3
▶ Read this text aloud: "Welcome to R CLI"
```

### 9. Design Skill

Generate images using Stable Diffusion.

```bash
# Generate image
r design "a sunset over mountains"
r design "cyberpunk city at night" --style anime
r design "portrait of a scientist" --steps 30

# With specific dimensions
r design "landscape painting" --width 1024 --height 768

# Check GPU status
r design --vram-status

# Unload model to free memory
r design --unload
```

**Styles:** realistic, anime, digital-art, oil-painting, watercolor, sketch

**In chat:**
```
▶ Generate an image of a futuristic spaceship
▶ Create an anime-style portrait of a wizard
```

### 10. Calendar Skill

Manage local calendar and tasks.

```bash
# View today's events
r calendar --today

# Add event
r calendar --add "Team meeting" --date "2024-01-15 10:00"
r calendar --add "Doctor appointment" --date "tomorrow 14:30"

# List events
r calendar --list --from "2024-01-01" --to "2024-01-31"

# Delete event
r calendar --delete <event_id>

# Tasks
r calendar --task "Buy groceries" --due "2024-01-10"
r calendar --tasks  # List all tasks
```

**In chat:**
```
▶ What do I have scheduled for today?
▶ Add a meeting with John tomorrow at 3pm
▶ Show me my tasks for this week
```

### 11. RAG Skill

Semantic search and knowledge base management.

```bash
# Add documents to knowledge base
r rag --add document.pdf
r rag --add ~/notes/*.txt
r rag --add "Important fact: Python was created in 1991"

# Search knowledge base
r rag --query "What is machine learning?"
r rag --search "python best practices"

# List indexed documents
r rag --list

# Clear knowledge base
r rag --clear
```

**In chat:**
```
▶ Add all PDFs from ~/research to my knowledge base
▶ Search my documents for information about neural networks
```

### 12. Multiagent Skill

Orchestrate multiple AI agents for complex tasks.

```bash
# Complex task with multiple steps
r multiagent "Research and write a report about AI trends"
r multiagent "Analyze code, find bugs, and suggest fixes"
```

**In chat:**
```
▶ Use multiple agents to research, summarize, and create a presentation about renewable energy
```

### 13. Plugin Skill

Manage community plugins.

```bash
# Install from GitHub
r plugin install https://github.com/user/r-cli-plugin

# List installed plugins
r plugin list

# Create new plugin
r plugin create my_plugin --author "Your Name" --description "My custom plugin"

# Enable/disable
r plugin enable my_plugin
r plugin disable my_plugin

# Uninstall
r plugin uninstall my_plugin
```

### 14. Web Skill

Web scraping and content extraction.

```bash
# Fetch webpage
r web --fetch https://example.com
r web --fetch https://news.site.com --extract text

# Extract specific elements
r web --fetch https://site.com --selector "article h1"

# Download page
r web --download https://example.com --output page.html
```

**In chat:**
```
▶ Scrape the main content from https://example.com/article
▶ Extract all links from this webpage
```

### 15. Git Skill

Git operations and repository management.

```bash
# Status
r git --status
r git --log --limit 10

# Commit
r git --add .
r git --commit "Fix bug in login"
r git --push

# Branches
r git --branch new-feature
r git --checkout main
r git --merge feature-branch

# Diff
r git --diff
r git --diff HEAD~1
```

**In chat:**
```
▶ Show me the git status of my project
▶ Create a new branch called "feature-auth" and switch to it
▶ Commit all changes with message "Add user authentication"
```

### 16. Docker Skill

Container management.

```bash
# List containers
r docker --ps
r docker --ps --all

# Container operations
r docker --start container_name
r docker --stop container_name
r docker --logs container_name --tail 100

# Images
r docker --images
r docker --pull nginx:latest

# Run container
r docker --run "nginx:latest" --name my-nginx --port 8080:80
```

**In chat:**
```
▶ List all running Docker containers
▶ Show the logs from my postgres container
▶ Start a new Redis container
```

### 17. SSH Skill

Remote server connections.

```bash
# Execute command
r ssh user@host "ls -la"
r ssh server.example.com "df -h"

# Interactive session (if supported)
r ssh --connect user@host

# With key
r ssh user@host "uptime" --key ~/.ssh/id_rsa

# Copy files
r ssh --scp local_file.txt user@host:/remote/path/
```

**In chat:**
```
▶ Connect to my server and check disk space
▶ Run "systemctl status nginx" on production server
```

### 18. HTTP Skill

Make HTTP requests.

```bash
# GET request
r http --get https://api.example.com/data
r http --get https://api.github.com/users/octocat

# POST request
r http --post https://api.example.com/users \
  --data '{"name": "John", "email": "john@example.com"}'

# With headers
r http --get https://api.example.com \
  --header "Authorization: Bearer token123"

# Download file
r http --download https://example.com/file.zip
```

**In chat:**
```
▶ Make a GET request to the GitHub API for user info
▶ POST data to my webhook endpoint
```

### 19. JSON Skill

Parse, query, and transform JSON data.

```bash
# Parse JSON file
r json data.json

# Query with JSONPath
r json data.json --query "$.users[*].name"
r json data.json --query "$.items[?(@.price > 100)]"

# Format/prettify
r json data.json --format

# Convert to other formats
r json data.json --to csv
r json data.json --to yaml
```

**In chat:**
```
▶ Parse the JSON file and extract all email addresses
▶ Convert this JSON to CSV format
```

### 20. Email Skill

Send emails via SMTP.

```bash
# Send email
r email --to recipient@example.com \
  --subject "Hello" \
  --body "This is a test email"

# With attachment
r email --to user@example.com \
  --subject "Report" \
  --body "Please find attached" \
  --attach report.pdf

# Configure SMTP (in config.yaml or environment)
# SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

**In chat:**
```
▶ Send an email to john@example.com with the project status
```

### 21. Translate Skill

Translate text between languages.

```bash
# Translate text
r translate "Hello world" --to spanish
r translate "Bonjour" --to english
r translate "$(cat document.txt)" --to german

# Detect language
r translate --detect "Ciao mondo"
```

**Supported languages:** english, spanish, french, german, italian, portuguese, russian, chinese, japanese, korean, arabic, and more.

**In chat:**
```
▶ Translate "Good morning" to Japanese
▶ Translate this paragraph to French
```

### 22. Clipboard Skill

System clipboard operations.

```bash
# Copy to clipboard
r clipboard --copy "Text to copy"
r clipboard --copy "$(cat file.txt)"

# Paste from clipboard
r clipboard --paste

# Clear clipboard
r clipboard --clear
```

**In chat:**
```
▶ Copy this code to clipboard
▶ What's currently in my clipboard?
```

### 23. Archive Skill

Compress and extract archives.

```bash
# Create archive
r archive --create backup.zip folder/
r archive --create data.tar.gz ~/Documents/data/

# Extract archive
r archive --extract backup.zip
r archive --extract data.tar.gz --output ~/extracted/

# List contents
r archive --list backup.zip

# Supported formats: zip, tar, tar.gz, tar.bz2, 7z
```

**In chat:**
```
▶ Create a zip archive of my project folder
▶ Extract the downloaded archive to ~/Downloads
```

### 24. Screenshot Skill

Capture screen content.

```bash
# Full screen
r screenshot

# Specific region
r screenshot --region 0,0,800,600

# Specific window (if supported)
r screenshot --window "Terminal"

# With delay
r screenshot --delay 5

# Output path
r screenshot --output ~/Pictures/capture.png
```

**In chat:**
```
▶ Take a screenshot of my screen
▶ Capture just the top-left corner (800x600)
```

### 25. Logs Skill (New!)

Log analysis, tailing, and crash diagnosis for developer workflows.

**Tools:**
- `tail_logs` - Tail log files or Docker containers
- `summarize_logs` - AI-powered log summarization
- `explain_crash` - Analyze crash logs and suggest fixes
- `diff_runs` - Compare test run outputs
- `watch_logs` - Watch logs in real-time with filtering

```bash
# In chat:
▶ Tail the last 100 lines of /var/log/nginx/error.log
▶ Explain the crash in my application logs
▶ Summarize errors from the Docker container logs
▶ Compare the pytest output from yesterday vs today
```

### 26. Benchmark Skill (New!)

Python profiling, command benchmarks, and performance comparison.

**Tools:**
- `profile_python` - Profile Python code with cProfile
- `benchmark_command` - Time shell commands
- `benchmark_python` - Benchmark Python functions
- `compare_benchmarks` - Compare two performance runs
- `memory_profile` - Analyze memory usage

```bash
# In chat:
▶ Profile the function in ~/myproject/slow_function.py
▶ Benchmark the command "python process_data.py"
▶ Compare performance before and after my changes
▶ Analyze memory usage of my Python script
```

### 27. OpenAPI Skill (New!)

Load OpenAPI specs, discover services, and call endpoints.

**Tools:**
- `load_openapi_spec` - Load an OpenAPI/Swagger spec
- `list_endpoints` - List all endpoints from a spec
- `describe_endpoint` - Get details about an endpoint
- `call_endpoint` - Make API calls based on spec
- `discover_services` - Find OpenAPI specs on common ports
- `generate_curl` - Generate curl commands for endpoints

```bash
# In chat:
▶ Load the OpenAPI spec from http://localhost:8000/openapi.json
▶ List all endpoints in the API
▶ Call the /users endpoint with GET method
▶ Generate curl commands for the POST /orders endpoint
▶ Discover services running on my localhost
```

---

## Interactive Mode

### Starting Interactive Mode

```bash
r                        # Default
r --theme matrix         # With theme
r --no-animation         # No animations
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/clear` | Clear conversation history |
| `/exit` or `/quit` | Exit R CLI |
| `/skills` | List available skills |
| `/config` | Show configuration |
| `/theme <name>` | Change theme |

### Example Session

```
▶ Hello!
R: ¡Hola! ¿En qué puedo ayudarte?

▶ Generate a Python function to calculate factorial
R: [Generates code using code skill]

▶ Now create a PDF with that code
R: [Creates PDF using pdf skill]

▶ /clear
Conversation cleared.

▶ /exit
¡Hasta luego!
```

---

## Direct Commands

### Available Commands

```bash
r                      # Interactive mode
r chat "message"       # Direct chat
r pdf "content"        # Generate PDF
r code "description"   # Generate code
r sql file "query"     # SQL query
r config              # Show config
r demo                # UI demo
r skills              # List skills
```

### Global Options

```bash
--version, -v         # Show version
--theme, -t NAME      # Set theme (ps2, matrix, minimal, retro)
--no-animation        # Disable animations
--help                # Show help
```

### Chat Options

```bash
r chat "message"
r chat --stream "message"   # Enable streaming
```

---

## Plugin System

### Plugin Structure

```
~/.r-cli/plugins/my_plugin/
├── plugin.yaml         # Metadata
├── __init__.py         # Entry point
├── skill.py            # Skill implementation
└── requirements.txt    # Dependencies (optional)
```

### plugin.yaml Format

```yaml
name: my_plugin
version: 1.0.0
description: My custom plugin
author: Your Name
skills:
  - MyCustomSkill
dependencies:
  - requests>=2.28.0
```

### Skill Implementation

```python
# skill.py
from r_cli.core.agent import Skill
from r_cli.core.llm import Tool

class MyCustomSkill(Skill):
    name = "my_skill"
    description = "Does something custom"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="my_function",
                description="Performs a custom action",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input text"
                        }
                    },
                    "required": ["input"]
                },
                handler=self.my_function,
            )
        ]

    def my_function(self, input: str) -> str:
        # Your logic here
        return f"Processed: {input}"

    def execute(self, **kwargs) -> str:
        """Direct execution without LLM."""
        return self.my_function(kwargs.get("input", ""))
```

---

## Creating Custom Skills

### Basic Skill Template

```python
from r_cli.core.agent import Skill
from r_cli.core.llm import Tool

class MySkill(Skill):
    name = "myskill"
    description = "Description of what this skill does"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="tool_name",
                description="What this tool does",
                parameters={
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"},
                        "param2": {"type": "integer", "description": "Second parameter"}
                    },
                    "required": ["param1"]
                },
                handler=self.tool_handler,
            )
        ]

    def tool_handler(self, param1: str, param2: int = 10) -> str:
        # Implementation
        return f"Result: {param1}, {param2}"
```

### Registering Custom Skills

Place your skill file in `~/.r-cli/skills/` and it will be automatically loaded.

---

## Memory & RAG System

### Memory Layers

R CLI uses a three-tier memory system:

1. **Short-term**: Current conversation context
2. **Medium-term**: Session history (persisted to `~/.r-cli/session.json`)
3. **Long-term**: ChromaDB vector database for semantic search

### Managing Memory

```bash
# Clear session history
rm ~/.r-cli/session.json

# Clear RAG database
rm -rf ~/.r-cli/vectordb

# In interactive mode
/clear   # Clears short-term memory
```

### Adding Documents to RAG

```bash
# Via command
r rag --add document.pdf

# Via chat
▶ Add ~/research/*.pdf to my knowledge base
```

---

## Themes & UI

### Available Themes

| Theme | Description |
|-------|-------------|
| `ps2` | Blue PlayStation 2 style (default) |
| `matrix` | Green Matrix/hacker style |
| `minimal` | Clean, simple interface |
| `retro` | Vintage CRT look |

### Setting Theme

```bash
# Command line
r --theme matrix

# In config.yaml
ui:
  theme: matrix

# In interactive mode
/theme matrix
```

### UI Features

- **Streaming**: Real-time response display
- **Animations**: Loading spinners, transitions
- **Panels**: Formatted response boxes
- **Syntax highlighting**: Code blocks
- **Markdown rendering**: Rich text formatting

---

## Troubleshooting

### LLM Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/v1/models

# Check if LM Studio is running
curl http://localhost:1234/v1/models

# Verify config
cat ~/.r-cli/config.yaml
```

### "r" Command Not Found

```bash
# The 'r' command conflicts with shell built-in
# Solution 1: Use full path
/path/to/python/bin/r

# Solution 2: Create alias
alias r="/path/to/python/bin/r"
```

### Context Too Long Error

```bash
# Clear session history
rm ~/.r-cli/session.json

# Or increase Ollama context
OLLAMA_CONTEXT_LENGTH=8192 ollama serve
```

### ChromaDB Errors

```bash
# Update ChromaDB
pip install --upgrade chromadb

# Clear vector database
rm -rf ~/.r-cli/vectordb
```

### Skill Not Loading

```bash
# Check for missing dependencies
pip install r-cli-ai[all]

# Check skill logs
r --debug
```

---

## API Reference

### LLMClient

```python
from r_cli.core.llm import LLMClient
from r_cli.core.config import Config

config = Config.load()
client = LLMClient(config)

# Simple chat
response = client.chat("Hello!")
print(response.content)

# With streaming
for chunk in client.chat_stream("Tell me a story"):
    print(chunk, end="")
```

### Agent

```python
from r_cli.core.agent import Agent
from r_cli.core.config import Config

config = Config.load()
agent = Agent(config)
agent.load_skills()

# Run a query
response = agent.run("Generate a PDF about Python")
print(response)

# Check available skills
print(agent.get_available_skills())
```

### Memory

```python
from r_cli.core.memory import Memory
from r_cli.core.config import Config

config = Config.load()
memory = Memory(config)

# Add to short-term memory
memory.add_short_term("User said hello", entry_type="user_input")

# Add document to RAG
doc_id = memory.add_document("Content here", metadata={"source": "file.txt"})

# Search RAG
results = memory.search("query", n_results=5)
```

---

## License

MIT License - Use R CLI however you want.

## Author

Created by Ramón Guillamón

- Twitter/X: [@learntouseai](https://x.com/learntouseai)
- Email: [learntouseai@gmail.com](mailto:learntouseai@gmail.com)
- GitHub: [github.com/raym33/r](https://github.com/raym33/r)

---

**R CLI** - Your AI, your machine, your rules.
