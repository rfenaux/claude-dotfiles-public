# Resource Management Guide

> Created: 2026-01-17 | Updated: 2026-01-17 | Version: 1.0

Hardware-aware resource management for Claude Code. Automatically detects device capabilities and configures optimal settings for agent spawning, load thresholds, and embedding generation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESOURCE MANAGEMENT STACK                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │ Device Detection│───▶│ Machine Profile │───▶│ Load Monitoring │        │
│   │ (on new device) │    │ (persistent)    │    │ (real-time)     │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │ Hardware Specs  │    │ Resource Limits │    │ Spawn Decisions │        │
│   │ - CPU cores     │    │ - Max agents    │    │ - OK/CAUTION/   │        │
│   │ - Memory        │    │ - Load thresh.  │    │   HIGH_LOAD     │        │
│   │ - GPU/Metal     │    │ - Ollama config │    │ - Queue vs work │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `~/.claude/machine-profile.json` | Device specs, thresholds, profiles |
| `~/.claude/scripts/check-load.sh` | Real-time load monitoring |
| `~/.claude/scripts/detect-device.sh` | New device detection + profile generation |
| `~/.claude/scripts/switch-profile.sh` | Switch between balanced/aggressive/conservative |
| `~/.claude/devices/` | Archived profiles from previous devices |
| `~/.ollama/ollama.env` | Ollama embedding engine configuration |

---

## Machine Profile

The machine profile (`~/.claude/machine-profile.json`) is the SSOT for hardware-aware settings.

### Structure

```json
{
  "hardware": {
    "model": "MacBook Air",
    "chip": "Apple M4",
    "cores": { "total": 10, "performance": 4, "efficiency": 6 },
    "memory_gb": 16,
    "fingerprint": "8984fd09cc83"
  },
  "thresholds": {
    "load_ok": 8.0,
    "load_caution": 15.0,
    "load_high": 20.0
  },
  "limits": {
    "max_parallel_agents": 4,
    "max_background_shells": 5,
    "agent_spawn_cooldown_ms": 2000
  },
  "profiles": {
    "balanced": { ... },
    "aggressive": { ... },
    "conservative": { ... }
  },
  "active_profile": "balanced"
}
```

### Fingerprint

Each device gets a unique fingerprint (SHA256 hash of serial number, truncated). This allows:
- Detecting when you're on a different machine
- Storing multiple device profiles
- Syncing config across machines while maintaining device-specific tuning

---

## Profiles

Three built-in profiles optimized for different scenarios:

### Balanced (Default)

```
Max Agents: 4
Load OK: 8.0
Use: General work, mixed tasks
```

Recommended for typical usage when Claude Code is your main focus but you have other apps running.

### Aggressive

```
Max Agents: 6
Load OK: 12.0
Use: Higher limits, more agents, higher load tolerance
```

Use when:
- Running intensive agent workflows
- Doing bulk analysis with multiple delegations
- Machine is dedicated to Claude work

### Conservative

```
Max Agents: 3
Load OK: 4.8
Use: Heavy multitasking
```

Use when:
- Running resource-intensive apps (Xcode, Docker, video editing)
- On battery power
- Want minimal system impact

### Switching Profiles

```bash
# Show current
~/.claude/scripts/switch-profile.sh

# Switch
~/.claude/scripts/switch-profile.sh aggressive

# List all
~/.claude/scripts/switch-profile.sh --list
```

---

## Load Monitoring

### Check Current Load

```bash
~/.claude/scripts/check-load.sh
```

Output:
```
┌─────────────────────────────────────────────────────────────┐
│ SYSTEM LOAD CHECK                          [balanced]
├─────────────────────────────────────────────────────────────┤
│ Status:      OK                                             │
│ Load Avg:    3.42 (cores: 10)                               │
│ Memory Free: 67%                                            │
│ Agents:      2 / 4                                          │
├─────────────────────────────────────────────────────────────┤
│ Parallel spawning allowed (2/4 agents)                      │
└─────────────────────────────────────────────────────────────┘
```

### Status Levels

| Status | Load Condition | Policy |
|--------|---------------|--------|
| `OK` | Below `load_ok` | Parallel spawning allowed |
| `CAUTION` | Between `load_ok` and `load_caution` | Sequential only |
| `HIGH_LOAD` | Above `load_caution` | Work inline, no spawning |

### Programmatic Checks

```bash
# Just status string
~/.claude/scripts/check-load.sh --status-only
# Returns: OK, CAUTION, or HIGH_LOAD

# Can spawn check (exit code)
if ~/.claude/scripts/check-load.sh --can-spawn; then
    echo "Safe to spawn"
fi

# JSON output for parsing
~/.claude/scripts/check-load.sh --json
```

---

## Agent Spawning Rules

### NEVER Kill Running Agents

Agents should complete their work. Killing mid-execution can:
- Leave partial results
- Corrupt workspaces
- Lose context

Instead, **respect execution order**:

```
┌─────────────────────────────────────────────────────────────┐
│                    SPAWNING DECISION TREE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  New task requires agent?                                   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐                                       │
│  │ check-load.sh    │                                       │
│  │ --can-spawn      │                                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│     ┌─────┴─────┐                                           │
│     │           │                                           │
│   exit 0      exit 1                                        │
│     │           │                                           │
│     ▼           ▼                                           │
│  SPAWN       QUEUE/INLINE                                   │
│  agent       Work directly or wait                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cooldown

A 2-second cooldown between agent spawns prevents burst spawning. Configurable in `limits.agent_spawn_cooldown_ms`.

---

## Device Detection

### Automatic Detection

On session start, if the device fingerprint doesn't match the stored profile:

```
┌─────────────────────────────────────────────────────────────┐
│ 🖥️  NEW DEVICE DETECTED                                      │
├─────────────────────────────────────────────────────────────┤
│ MacBook Pro / Apple M3 Max / 64GB                           │
├─────────────────────────────────────────────────────────────┤
│ Would you like to generate optimized resource settings?     │
└─────────────────────────────────────────────────────────────┘

Run: ~/.claude/scripts/detect-device.sh --generate
```

### Manual Commands

```bash
# Show current device info
~/.claude/scripts/detect-device.sh --info

# Check if device matches profile (silent)
~/.claude/scripts/detect-device.sh --check

# Generate new profile for current device
~/.claude/scripts/detect-device.sh --generate
```

### Threshold Calculation

Thresholds are auto-calculated based on hardware:

| Hardware | Formula |
|----------|---------|
| `load_ok` | `cores × 0.8` |
| `load_caution` | `cores × 1.5` |
| `max_agents` | `memory_gb / 4` (clamped 2-6) |

Example for M4 Max (14 cores, 36GB):
- `load_ok` = 11.2
- `load_caution` = 21.0
- `max_agents` = 6

---

## Ollama Configuration

Ollama provides local embedding generation for RAG. The config file `~/.ollama/ollama.env` contains optimized settings.

### Key Settings

```bash
# Concurrent requests (tune for your RAM)
OLLAMA_NUM_PARALLEL=2

# Keep models loaded (faster subsequent requests)
OLLAMA_KEEP_ALIVE="5m"

# Use all GPU layers (Apple Silicon Metal)
OLLAMA_GPU_LAYERS=-1

# Max loaded models (memory constraint)
OLLAMA_MAX_LOADED_MODELS=2
```

### Embedding Models

| Model | Dimensions | Size | Quality | Memory |
|-------|-----------|------|---------|--------|
| `all-minilm` | 384 | 23MB | ⭐⭐ | <8GB RAM |
| `nomic-embed-text` | 768 | 274MB | ⭐⭐⭐ | 16GB (default) |
| `bge-large-en-v1.5` | 1024 | 1.2GB | ⭐⭐⭐⭐ | 16-32GB |
| `mxbai-embed-large` | 1024 | 1.2GB | ⭐⭐⭐⭐⭐ | 16-32GB |
| `snowflake-arctic-embed` | 1024 | 1.1GB | ⭐⭐⭐⭐⭐ | 32GB+ |

### Upgrading Models

```bash
# Pull better model
ollama pull mxbai-embed-large

# Update RAG config (per project)
# In project/.rag/config.json:
{
  "embedding_model": "mxbai-embed-large"
}

# Re-index for new embeddings
rag reindex
```

### Alternatives to Ollama

| Alternative | Pros | Cons |
|-------------|------|------|
| **llama.cpp** | Lighter, no server | Manual setup |
| **FastEmbed** | ONNX, very fast | Fewer models |
| **sentence-transformers** | Most models | Heavy Python deps |

---

## Troubleshooting

### High Load / Slow Performance

```bash
# Check what's running
~/.claude/scripts/check-load.sh

# Switch to conservative
~/.claude/scripts/switch-profile.sh conservative

# Check agent count
ps aux | grep claude | wc -l
```

### Ollama Not Running

```bash
# Check status
ollama ps

# Start if needed
ollama serve &

# Verify embedding model
ollama list | grep embed
```

### Wrong Device Profile

```bash
# Check fingerprint match
~/.claude/scripts/detect-device.sh --check
echo $?  # 0 = match, 1 = mismatch

# Regenerate for current device
~/.claude/scripts/detect-device.sh --generate
```

### Memory Pressure

If memory is low (<20% free):
1. Switch to conservative profile
2. Use smaller embedding model
3. Reduce `OLLAMA_NUM_PARALLEL` to 1
4. Reduce `OLLAMA_MAX_LOADED_MODELS` to 1

---

## Integration with CDP

The Cognitive Delegation Protocol checks load before spawning:

```
Primary Agent
     │
     │ Before Task.spawn():
     ├──▶ check-load.sh --can-spawn
     │           │
     │     ┌─────┴─────┐
     │   exit 0      exit 1
     │     │           │
     │  Spawn        Queue task
     │  agent        or work inline
     │     │
     ▼     ▼
Sub-agent executes
```

The `--can-spawn` check considers BOTH:
- Current system load
- Number of active agents vs max limit

---

## Multi-Device Sync

When using Claude config across multiple machines:

1. **machine-profile.json** — Device-specific, auto-generated per machine
2. **Scripts** — Same across all devices
3. **~/.claude/devices/** — Archive of profiles from other machines

The fingerprint ensures each device gets optimized settings while sharing the same configuration structure.

---

## Future Enhancements

Potential improvements for later:

- [ ] Agent queue system with priority
- [ ] Pause/resume agents (vs kill)
- [ ] Automatic profile switching based on power state
- [ ] Integration with macOS Focus modes
- [ ] Dashboard widget for load monitoring
