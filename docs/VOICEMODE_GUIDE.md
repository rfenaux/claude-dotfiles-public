# VoiceMode Guide - Local Voice for Claude Code

> Installed: 2026-01-29 | Version: 8.0.8 | Stack: Fully Local (Privacy Mode)

## Overview

Voice conversations with Claude Code using local speech-to-text (Whisper) and text-to-speech (Kokoro). No cloud APIs, no API costs, full privacy.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VoiceMode Stack                        │
├─────────────────────────────────────────────────────────────┤
│  Voice Input  →  Whisper (local)  →  Text to Claude Code    │
│  Claude Output →  Kokoro (local)  →  Audio Response         │
├─────────────────────────────────────────────────────────────┤
│  MCP Server: uvx voice-mode (user scope)                    │
│  Config: ~/.voicemode/config.yaml                           │
│  Services: ~/.voicemode/services/{whisper,kokoro}           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

**Inside Claude Code session** (recommended):
```
Say: "let's talk" or "voice mode" or invoke /voicemode skill
Claude will use mcp__voicemode__converse tool to speak and listen
```

**Standalone CLI** (outside Claude Code):
```bash
voicemode converse
```

**Controls:**
- Speak naturally - VAD detects speech automatically
- Pause 800ms+ - triggers transcription
- Ctrl+C - end conversation

## Session Identification

VoiceMode announces the current project when starting a voice session to prevent cross-session confusion.

**Auto-announce pattern** (implemented in /voicemode skill):
```
"Voice mode active for [project-name]. Listening."
```

**Multi-session coordination:**
- `wait_for_conch: false` (default) - Returns "busy" if another session is speaking
- `wait_for_conch: true` - Waits for other session to finish, then speaks
- Microphone is a natural lock - only one process can capture at a time

**Visual cue:** Project name extracted from working directory path:
- `~/Documents/Projects - Pro/<COMPANY>/...` → Client/project name
- `/Users/<username>` (home) → "Global session"
- Folder ending with `-claude` → Project name without suffix

## Installation Details

### Components Installed

| Component | Location | Size |
|-----------|----------|------|
| VoiceMode CLI | `~/.local/bin/voicemode` | - |
| Whisper STT | `~/.voicemode/services/whisper` | ~180 MB (base model) |
| Kokoro TTS | `~/.voicemode/services/kokoro` | ~950 MB |
| Config | `~/.voicemode/config.yaml` | - |
| MCP Server | User scope in `~/.claude.json` | - |

### MCP Registration

```json
// In ~/.claude.json
{
  "mcpServers": {
    "voicemode": {
      "command": "uvx",
      "args": ["voice-mode"]
    }
  }
}
```

## Configuration

### Current Config (`~/.voicemode/config.yaml`)

```yaml
stt:
  provider: whisper-local
  model: base
  language: en

tts:
  provider: kokoro
  voice: af_heart
  speed: 1.0

audio:
  vad_aggressiveness: 2
  silence_threshold_ms: 800

conversation:
  auto_speak_responses: true
```

### Whisper Models

| Model | Size | Accuracy | Latency | Use Case |
|-------|------|----------|---------|----------|
| `tiny` | 75 MB | Low | ~0.5s | Quick tests |
| `base` | 141 MB | Good | ~1s | **Default** - general use |
| `small` | 466 MB | Better | ~2s | Technical vocabulary |
| `medium` | 1.5 GB | High | ~3s | Complex discussions |
| `large-v3` | 3.1 GB | Best | ~5s | Maximum accuracy |

**Upgrade command:**
```bash
voicemode service upgrade whisper --model small
```

### Kokoro Voices

| Voice | Style |
|-------|-------|
| `af_heart` | Female, warm (default) |
| `af_sky` | Female, clear |
| `am_adam` | Male, professional |
| `bm_george` | Male, deep |

## Service Management

```bash
# Status
voicemode status                    # All services
voicemode service status whisper    # STT only
voicemode service status kokoro     # TTS only

# Control
voicemode service start whisper
voicemode service stop kokoro
voicemode service restart whisper

# Upgrade
voicemode service upgrade whisper --model medium
```

## Ports Used

| Service | Port | Protocol |
|---------|------|----------|
| Whisper STT | 2022 | HTTP |
| Kokoro TTS | 8880 | HTTP |

## Troubleshooting

### Service won't start

```bash
# Check what's using the port
lsof -i :2022
lsof -i :8880

# Force restart
voicemode service stop whisper && voicemode service start whisper
```

### Poor transcription accuracy

1. Upgrade model: `voicemode service upgrade whisper --model small`
2. Check microphone input level
3. Reduce background noise
4. Speak closer to microphone

### Audio output issues

```bash
# Test TTS directly
curl -X POST http://localhost:8880/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}' \
  --output test.wav && afplay test.wav
```

### Full diagnostics

```bash
voicemode diag
```

## Privacy & Security

| Aspect | Status |
|--------|--------|
| Audio sent to cloud | **Never** (fully local) |
| API keys required | **None** |
| Network dependency | **None** (works offline) |
| Data retention | Local only (in RAM during processing) |

## Cost

| Component | Cost |
|-----------|------|
| VoiceMode | Free (open source) |
| Whisper | Free (local) |
| Kokoro | Free (local) |
| **Total** | **$0** |

## Technical Vocabulary Tips

For better recognition of technical terms (HubSpot, BPMN, ERD, API, webhook):

1. **Upgrade model** - `small` or `medium` handles technical terms better
2. **Speak clearly** - pause slightly between technical acronyms
3. **Spell out** - "H-U-B-S-P-O-T" on first mention helps model learn context

## Alternatives Considered

| Option | Pros | Cons | Why Not Chosen |
|--------|------|------|----------------|
| OpenAI Whisper API | Fast, accurate | $0.006/min, cloud | Privacy concern |
| macOS Dictation | Built-in, free | No Claude integration | Limited control |
| Superwhisper | Great accuracy | $30, no TTS | No Claude integration |
| claude-ptt | Hotkey-based | Less polished | VoiceMode more complete |

## References

- VoiceMode repo: https://github.com/mbailey/voicemode
- VoiceMode docs: https://getvoicemode.com/
- Whisper.cpp: https://github.com/ggerganov/whisper.cpp
- Kokoro TTS: https://github.com/hexgrad/kokoro

## Maintenance

```bash
# Update VoiceMode
voicemode update

# Check for updates
voicemode version
```

---

*Installed via Claude Code session 2026-01-29*
