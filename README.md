# R CLI

<div align="center">

```
██████╗        ██████╗██╗     ██╗
██╔══██╗      ██╔════╝██║     ██║
██████╔╝█████╗██║     ██║     ██║
██╔══██╗╚════╝██║     ██║     ██║
██║  ██║      ╚██████╗███████╗██║
╚═╝  ╚═╝       ╚═════╝╚══════╝╚═╝
```

**Your Local AI Operating System**

[![PyPI version](https://badge.fury.io/py/r-cli-ai.svg)](https://pypi.org/project/r-cli-ai/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**74 Skills** · **REST API** · **Android Simulator** · **100% Offline**

[Installation](#installation) · [Quick Start](#quick-start) · [R OS Simulator](#r-os---android-simulator) · [All Skills](#all-74-skills) · [Documentation](docs/COMPLETE_GUIDE.md)

</div>

---

## What is R CLI?

R CLI connects local LLMs (Ollama, LM Studio) to real system tools. Chat in the terminal or integrate via REST API. **Your data never leaves your machine.**

```bash
$ r chat "Create a PDF report about Python"
📄 Generated: python_report.pdf (12 pages)

$ r chat "Scan my WiFi networks"
📶 Found 5 networks: Home_5G (90%), Guest (65%)...

$ r-os  # Launch Android-like simulator
```

## Features

| Feature | Description |
|---------|-------------|
| 🔒 **100% Local** | Your data never leaves your machine |
| 🛠️ **74 Skills** | PDF, SQL, code, voice, GPIO, HubLab, and more |
| 📱 **R OS Simulator** | Android-like TUI for Raspberry Pi |
| 🌐 **REST API** | OpenAI-compatible daemon for IDE integration |
| 🎙️ **Voice Interface** | Wake word + Whisper STT + Piper TTS |
| 🔌 **Hardware Control** | GPIO, Bluetooth, WiFi, Power management |
| 🎨 **Themes** | PS2, Matrix, AMOLED, Retro |
| 🧩 **Extensible** | Create skills or install plugins |

---

## Installation

```bash
# Basic
pip install r-cli-ai

# With all features
pip install r-cli-ai[all]

# R OS Simulator (Textual TUI)
pip install r-cli-ai[simulator]

# Raspberry Pi (with GPIO)
pip install r-cli-ai[all-rpi]
```

### Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) or [LM Studio](https://lmstudio.ai/)
- 8GB+ RAM (16GB+ recommended)

---

## Quick Start

### 1. Start your LLM

```bash
# Ollama
ollama pull qwen3:4b && ollama serve

# Or use LM Studio GUI
```

### 2. Run R CLI

```bash
# Interactive chat
r

# Direct command
r chat "Explain quantum computing in simple terms"

# Start API server
r serve --port 8765
```

---

## R OS - Android Simulator

Transform your terminal into an Android-like interface. Perfect for Raspberry Pi and edge devices.

```
┌─────────────────────────────────────────────────────────┐
│ ▁▂▄█ 📶 R OS          12:45          🔋 85%             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   💬 Messages   📞 Phone     📧 Email     🌐 Browser   │
│                                                         │
│   📷 Camera     🖼️ Gallery   🎵 Music     🎬 Video     │
│                                                         │
│   📁 Files      📅 Calendar  ⏰ Clock     🔢 Calculator │
│                                                         │
│   🤖 R Chat     🎤 Voice     🌍 Translate 📝 Notes     │
│                                                         │
│   ⚙️ Settings   📶 WiFi      🔵 Bluetooth 🔋 Battery   │
│                                                         │
│   💡 GPIO       💻 Terminal  🔌 Network   📊 System    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│           ◀ Back      ● Home      ▢ Recent             │
└─────────────────────────────────────────────────────────┘
```

### Launch

```bash
r-os                    # Material theme
r-os --theme amoled     # AMOLED black
r-os --theme light      # Light theme
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `t` | Cycle themes |
| `n` | Notifications panel |
| `h` | Home |
| `Esc` | Back |
| `q` | Quit |

### Raspberry Pi Setup

```bash
# One-command installer
curl -sSL https://raw.githubusercontent.com/raym33/r/main/r_os/rpi/install.sh | bash
```

📖 **[Full R OS Documentation](r_os/README.md)**

---

## All 74 Skills

### 📄 Documents
`pdf` · `latex` · `markdown` · `pdftools` · `template` · `resume` · `changelog`

### 💻 Code & Data
`code` · `sql` · `json` · `yaml` · `csv` · `regex` · `schema` · `diff`

### 🤖 AI & Knowledge
`rag` · `multiagent` · `translate` · `faker`

### 🎨 Media
`ocr` · `voice` · `design` · `image` · `video` · `audio` · `screenshot` · `qr` · `barcode`

### 📁 Files
`fs` · `archive` · `clipboard` · `env`

### 📅 Productivity
`calendar` · `email` · `ical` · `vcard`

### 🔧 DevOps
`git` · `docker` · `ssh` · `http` · `web` · `network` · `system` · `metrics`

### 🔍 Dev Tools
`logs` · `benchmark` · `openapi` · `cron` · `jwt`

### 📝 Text
`text` · `html` · `xml` · `url` · `ip` · `encoding`

### 🔢 Data
`datetime` · `color` · `math` · `currency` · `crypto` · `semver` · `mime`

### 🌐 Web
`rss` · `sitemap` · `manifest` · `hublab` · `weather`

### 🔌 Hardware (R OS)
`gpio` · `bluetooth` · `wifi` · `power` · `android`

### 🧩 Extensions
`plugin`

---

## REST API

```bash
# Start server
r serve --port 8765

# Chat (OpenAI-compatible)
curl -X POST http://localhost:8765/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'

# Call skill directly
curl -X POST http://localhost:8765/v1/skills/call \
  -d '{"skill": "pdf", "tool": "generate_pdf", "arguments": {"content": "Hello"}}'
```

**Swagger UI:** http://localhost:8765/docs

---

## Configuration

```yaml
# ~/.r-cli/config.yaml
llm:
  backend: ollama
  model: qwen3:4b
  base_url: http://localhost:11434/v1

ui:
  theme: ps2  # ps2, matrix, minimal, retro

skills:
  disabled: []  # Skills to disable
```

---

## Create Custom Skills

```python
# ~/.r-cli/skills/my_skill.py
from r_cli.core.agent import Skill
from r_cli.core.llm import Tool

class MySkill(Skill):
    name = "my_skill"
    description = "My custom skill"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="my_function",
                description="Does something useful",
                parameters={"type": "object", "properties": {"input": {"type": "string"}}},
                handler=self.my_function,
            )
        ]

    def my_function(self, input: str) -> str:
        return f"Processed: {input}"
```

---

## Development

```bash
git clone https://github.com/raym33/r.git
cd r
pip install -e ".[dev]"
pytest tests/ -v
ruff check . && ruff format .
```

---

## Links

- 📖 [Complete Documentation](docs/COMPLETE_GUIDE.md)
- 📱 [R OS Documentation](r_os/README.md)
- 🐛 [Report Issues](https://github.com/raym33/r/issues)
- 📦 [PyPI Package](https://pypi.org/project/r-cli-ai/)

---

## License

MIT License - Use R CLI however you want.

---

<div align="center">

**R CLI** - Your AI, your machine, your rules.

Created by [Ramón Guillamón](https://x.com/learntouseai)

</div>
