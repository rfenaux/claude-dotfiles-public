# Resource Management

Switch profiles: `~/.claude/scripts/switch-profile.sh <profile>`

## Profiles

| Profile | Max Agents | Load OK | Use When |
|---------|-----------|---------|----------|
| `balanced` | 4 | 8.0 | Default - general work |
| `aggressive` | 6 | 12.0 | Higher limits, more agents |
| `conservative` | 3 | 4.8 | Running other apps |

## Load-Aware Spawning

Do not kill running agents — respect execution order.

| Status | Action |
|--------|--------|
| `OK` | Spawn freely (parallel allowed) |
| `CAUTION` | Sequential only — wait for completion |
| `HIGH_LOAD` | Work inline — no new agents |
| Agent limit reached | Queue work — don't spawn |

Before spawning agents, check: `~/.claude/scripts/check-load.sh --can-spawn`

## Model Selection

| Model | Use For |
|-------|---------|
| **Haiku** | Explore agents, file lookups, RAG + light synthesis |
| **Sonnet** | Code implementation, reviews, Plan agents, docs |
| **Opus 4.6** | Solution Architect, complex architecture, multi-system integration |

Announce choice: `[Using {model} for: {reason}]`

## Ollama (RAG Embeddings)

Default model: `mxbai-embed-large` (669MB). Install: `ollama pull mxbai-embed-large`

On new device: run `~/.claude/scripts/detect-device.sh --generate` to create profile.
