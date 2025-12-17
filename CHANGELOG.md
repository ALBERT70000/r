# Changelog

All notable changes to R CLI are documented here.

## [0.3.1] - 2024-12-17

### Changed
- Renamed from "AI Operating System" to "Local AI Agent Runtime" for accuracy
- R OS now clearly labeled as "Terminal UI (Experimental)"
- Added architecture diagram to README
- Added "Why Structured Tools Instead of Terminal Access?" section
- Added "Honest Limitations" section

## [0.3.0] - 2024-12-16

### Added
- **R OS Terminal UI**: Android-like interface built with Textual
- **5 Hardware Skills**: `gpio`, `bluetooth`, `wifi`, `power`, `android`
- **Voice Interface**: Wake word detection + Whisper STT + Piper TTS
- Raspberry Pi one-command installer
- 3 themes: Material, AMOLED, Light

### Changed
- Total skills increased from 69 to 74

## [0.2.0] - 2024-12-14

### Added
- **REST API Server**: `r serve --port 8765`
- OpenAI-compatible `/v1/chat` endpoint with streaming
- Direct skill invocation via `/v1/skills/call`
- Swagger UI at `/docs`
- JWT authentication support
- Python and TypeScript SDKs
- **HubLab Skill**: UI component search and code generation
- 40+ new utility skills (encoding, crypto, semver, mime, etc.)
- Comprehensive test suite (200+ tests)

### Changed
- Total skills increased from 27 to 69

## [0.1.0] - 2024-12-10

### Added
- Initial release
- 27 core skills:
  - Documents: `pdf`, `latex`, `markdown`, `template`, `resume`
  - Code: `code`, `sql`, `json`, `yaml`, `csv`
  - AI: `rag`, `multiagent`, `translate`
  - Media: `ocr`, `voice`, `design`, `image`, `screenshot`
  - DevOps: `git`, `docker`, `ssh`, `http`, `web`
  - Productivity: `calendar`, `email`, `fs`, `archive`
- Interactive chat mode
- Direct command execution
- Plugin system for custom skills
- Multiple themes: PS2, Matrix, Minimal, Retro
- Ollama and LM Studio support

---

[0.3.1]: https://github.com/raym33/r/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/raym33/r/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/raym33/r/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/raym33/r/releases/tag/v0.1.0
