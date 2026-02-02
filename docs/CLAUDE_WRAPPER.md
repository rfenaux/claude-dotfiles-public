# Claude Wrapper: Slim/Full Mode Switching

> Created: 2026-01-19 | Version: 1.0

## Overview

A shell wrapper that switches between **slim** and **full** versions of `~/.claude/CLAUDE.md` to optimize token usage. Main sessions use full config by default; sub-agents automatically use slim.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Main Session (claude)                                          │
│  ├── CLAUDE_MAIN_SESSION=true (env var set)                     │
│  ├── Uses CLAUDE.md.full (~9.5k tokens)                         │
│  │                                                              │
│  └── Sub-Agent (Task tool)                                      │
│      ├── CLAUDE_MAIN_SESSION not set                            │
│      ├── SessionStart hook detects this                         │
│      └── Swaps to CLAUDE.md.slim (~1.5k tokens)                 │
└─────────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `~/.claude/CLAUDE.md` | Active config (swapped by wrapper) |
| `~/.claude/CLAUDE.md.full` | Full config (~835 lines, ~9.5k tokens) |
| `~/.claude/CLAUDE.md.slim` | Slim config (~192 lines, ~1.5k tokens) |
| `~/.claude/scripts/claude-wrapper.sh` | Wrapper script |
| `~/.claude/hooks/subagent-slim.sh` | Sub-agent detection hook |

## Usage

### Basic Commands

```bash
# Start with full config (default)
claude

# Explicitly use full config
claude --full

# Use slim config for this session
claude --slim

# Pass other flags normally
claude --slim --model sonnet
claude --full -p "Hello"
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_MAIN_SESSION` | Set to `true` by wrapper; sub-agents don't have it |
| `CLAUDE_DEFAULT_MODE` | Override default mode (`full` or `slim`) |

### Change Default Mode

```bash
# In ~/.zshrc, add before the alias:
export CLAUDE_DEFAULT_MODE=slim  # Make slim the default

# Or keep full as default (current behavior)
export CLAUDE_DEFAULT_MODE=full
```

## Installation

Already installed. Components:

### 1. Wrapper Script (`~/.claude/scripts/claude-wrapper.sh`)

```bash
#!/bin/bash
# Claude Code wrapper with --slim/--full mode switching

set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_MD_FULL="$CLAUDE_DIR/CLAUDE.md.full"
CLAUDE_MD_SLIM="$CLAUDE_DIR/CLAUDE.md.slim"

DEFAULT_MODE="${CLAUDE_DEFAULT_MODE:-full}"
MODE="$DEFAULT_MODE"

# Parse custom flags
CLAUDE_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --slim) MODE="slim"; shift ;;
        --full) MODE="full"; shift ;;
        *) CLAUDE_ARGS+=("$1"); shift ;;
    esac
done

# Select the right CLAUDE.md
if [[ "$MODE" == "slim" ]]; then
    if [[ -f "$CLAUDE_MD_SLIM" ]]; then
        cp "$CLAUDE_MD_SLIM" "$CLAUDE_MD"
        echo "[claude-wrapper] Using slim CLAUDE.md (~1.5k tokens)"
    fi
elif [[ "$MODE" == "full" ]]; then
    if [[ -f "$CLAUDE_MD_FULL" ]]; then
        cp "$CLAUDE_MD_FULL" "$CLAUDE_MD"
        echo "[claude-wrapper] Using full CLAUDE.md (~9.5k tokens)"
    fi
fi

# Mark this as main session (sub-agents won't have this)
export CLAUDE_MAIN_SESSION=true

# Run the real claude binary
exec /opt/homebrew/bin/claude ${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}
```

### 2. Shell Alias (`~/.zshrc`)

```bash
alias claude='~/.claude/scripts/claude-wrapper.sh'
```

### 3. Sub-Agent Hook (`~/.claude/hooks/subagent-slim.sh`)

```bash
#!/bin/bash
# Detects sub-agents and swaps to slim CLAUDE.md

CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_MD_SLIM="$CLAUDE_DIR/CLAUDE.md.slim"

# If CLAUDE_MAIN_SESSION is set, this is a main session - do nothing
if [[ "${CLAUDE_MAIN_SESSION:-}" == "true" ]]; then
    exit 0
fi

# Otherwise, this is a sub-agent - use slim
if [[ -f "$CLAUDE_MD_SLIM" ]]; then
    cp "$CLAUDE_MD_SLIM" "$CLAUDE_MD"
    echo "Sub-agent detected: using slim CLAUDE.md"
fi
```

### 4. Hook Registration (`~/.claude/settings.json`)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/subagent-slim.sh"
          }
        ]
      }
    ]
  }
}
```

## Slim vs Full: What's Different?

### Full Version (~9.5k tokens)
Contains everything inline:
- Partnership & persona details
- All memory system docs (RAG, CTM, CDP)
- All auto-invoke triggers
- All agent/skill catalogs
- All working patterns
- Full external guide references

### Slim Version (~1.5k tokens)
Contains essentials + pointers:
- Partnership summary (5 lines)
- Critical rules (NEVER list)
- Timestamp format
- Binary file table
- Memory stack overview (pointer to guides)
- Model selection table
- **Pointers to external guides** for everything else

### What Slim Relies On

The slim version points to these external guides:
- `~/.claude/RAG_GUIDE.md` — RAG details
- `~/.claude/CTM_GUIDE.md` — Task management
- `~/.claude/CDP_PROTOCOL.md` — Sub-agent delegation
- `~/.claude/AGENTS_INDEX.md` — Agent catalog
- `~/.claude/SKILLS_INDEX.md` — Skill catalog
- `~/.claude/PROJECT_MEMORY_GUIDE.md` — Decision tracking

**Important:** Keep these guides up-to-date. Slim mode reads them on demand.

## Token Savings

| Scenario | Full | Slim | Savings |
|----------|------|------|---------|
| Main session | 9.5k | - | - |
| Sub-agent | 9.5k | 1.5k | **8k per agent** |
| 3 sub-agents | 28.5k | 4.5k | **24k total** |

## Troubleshooting

### Wrapper Not Working
```bash
# Check alias is set
alias | grep claude

# Reload shell config
source ~/.zshrc

# Check wrapper is executable
chmod +x ~/.claude/scripts/claude-wrapper.sh
```

### Sub-Agents Still Using Full
```bash
# Check hook is registered
cat ~/.claude/settings.json | grep subagent

# Check hook is executable
chmod +x ~/.claude/hooks/subagent-slim.sh
```

### "Unbound variable" Error
Fixed in wrapper with `${CLAUDE_ARGS[@]+"${CLAUDE_ARGS[@]}"}` idiom for empty arrays with `set -u`.

## Backup Location

Original full CLAUDE.md backed up at:
- `~/.claude/CLAUDE.md.backup-2026-01-19`
- `~/.claude/backups/claude-md-cleanup-20260119/`
