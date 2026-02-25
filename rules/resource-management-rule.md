# Resource Management

## Load-Aware Spawning

**NEVER kill running agents.** Check load before spawning:

```bash
~/.claude/scripts/check-load.sh --can-spawn
```

| Status | Action |
|--------|--------|
| `OK` | Spawn freely (parallel allowed) |
| `CAUTION` | Sequential only — wait for completion |
| `HIGH_LOAD` | Work inline — no new agents |

## Profiles

| Profile | Max Agents | Use When |
|---------|-----------|----------|
| `balanced` | 4 | Default - general work |
| `aggressive` | 6 | Higher limits |
| `conservative` | 3 | Multitasking |

Switch: `~/.claude/scripts/switch-profile.sh <profile>`

## Model Selection

| Model | Use For |
|-------|---------|
| **Haiku** | Explore agents, file lookups, RAG + light synthesis |
| **Sonnet** | Code implementation, reviews, Plan agents, docs |
| **Opus 4.6** | Solution Architect, complex architecture, multi-system integration |

Announce choice: `[Using {model} for: {reason}]`

## Ollama (RAG Embeddings)

Default: `mxbai-embed-large` (669MB). Install: `ollama pull mxbai-embed-large`

**Full guide:** `RESOURCE_MANAGEMENT.md`
