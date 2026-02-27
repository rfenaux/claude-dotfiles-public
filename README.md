# Claude Code Power Config

A production-grade configuration layer for Claude Code. Adds persistent memory, 138 specialized agents, semantic search, prompt enhancement, and 55+ automation hooks — all working in the background.

## What's Inside

| System | What it does |
|--------|-------------|
| **Rules** (16) | Behavioral constraints auto-loaded every session — decision guards, verification, scope transparency |
| **CTM** | Cognitive Task Management — tracks work, decisions, and blockers across sessions |
| **RAG** | Local semantic search using Ollama embeddings — ask questions about your project history |
| **Agents** (138) | Specialized sub-agents for HubSpot, Salesforce, diagrams, proposals, reasoning, and more |
| **Skills** (57) | Slash commands — `/ctm`, `/enhance`, `/brand-extract`, `/config-audit`, and 53 others |
| **Hooks** (55) | Event-driven automation — auto-index files, capture decisions, self-heal broken configs |
| **CDP** | Cognitive Delegation Protocol — structured agent spawning with load-aware scheduling |
| **Lessons** | Auto-extracted domain knowledge from past sessions with confidence scoring |
| **Observations** | Auto-captured session memory compressed into searchable summaries |

### How the pieces connect

```
Session Start
    │
    ├── Rules loaded (20 behavioral constraints)
    ├── CTM briefing (what you were working on)
    ├── Memory injected (MEMORY.md → system prompt)
    └── Hooks fire (health checks, device detection)
         │
         ▼
   Working Session
    │
    ├── Agents auto-route (complex tasks → specialists)
    ├── RAG answers questions (semantic search over project)
    ├── Skills available (/ctm, /enhance, /brand-extract...)
    ├── CDP delegates (multi-agent parallel work)
    └── Hooks capture (decisions, observations, lessons)
         │
         ▼
   Session End
    │
    ├── CTM checkpoint (progress + decisions saved)
    ├── Observations compressed (session → summary)
    └── Lessons extracted (patterns → knowledge base)
```

## Install

### Method 1: Full Install

Interactive (recommended — walks you through Ollama setup):

```bash
git clone https://github.com/rfenaux/claude-dotfiles-public.git /tmp/claude-dotfiles
bash /tmp/claude-dotfiles/install.sh
```

Non-interactive:

```bash
git clone https://github.com/rfenaux/claude-dotfiles-public.git /tmp/claude-dotfiles
bash /tmp/claude-dotfiles/install.sh --yes
```

Check prerequisites first (no changes made):

```bash
bash install.sh --check
```

### Method 2: Selective Adoption

Don't want everything? Pick what you need:

| Tier | What you get | Time | Guide |
|------|-------------|------|-------|
| **Essential** | Rules + CLAUDE.md + project memory templates | 5 min | [GETTING_STARTED.md](GETTING_STARTED.md) |
| **Recommended** | + CTM + hooks + key agents | 15 min | [GETTING_STARTED.md](GETTING_STARTED.md) |
| **Power User** | + RAG + full agents + CDP + observability | 30-60 min | [GETTING_STARTED.md](GETTING_STARTED.md) |

### Method 3: Claude-to-Claude

Already have a Claude Code setup? Point your Claude at this repo:

> "Read CLAUDE_ADOPTION_GUIDE.md from this repo and help me integrate the parts that would improve my setup."

The [adoption guide](CLAUDE_ADOPTION_GUIDE.md) is written FOR your Claude instance — it explains each subsystem, maps dependencies, and provides layer-by-layer integration instructions with conflict detection.

## Prerequisites

| Tool | Required? | Install |
|------|-----------|---------|
| **Claude Code CLI** | Yes | `npm install -g @anthropic-ai/claude-code` |
| **Python 3.11+** | Yes | `brew install python@3.12` |
| **git** | Yes | `brew install git` |
| **Ollama** | Recommended | `brew install ollama` — local AI for semantic search |
| **jq** | Recommended | `brew install jq` — JSON processing for hooks |

The installer detects what you have and skips what's already installed.

## First Session

```
/config-audit                  → verify your installation
/ctm spawn "my first task"     → start tracking work across sessions
/enhance                       → see prompt enhancement in action
```

## Key Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main config — auto-loaded every session |
| `AGENTS_INDEX.md` | Master catalog of all 138 agents |
| `SKILLS_INDEX.md` | Master catalog of all 57 skills |
| `CTM_GUIDE.md` | Task management — tracking, decisions, cross-session memory |
| `RAG_GUIDE.md` | Semantic search — indexing, search order, reindexing |
| `CDP_PROTOCOL.md` | Agent delegation protocol |
| `CONFIGURATION_GUIDE.md` | Full architecture reference |
| `GETTING_STARTED.md` | Post-install guide with tier walkthrough |
| `CLAUDE_ADOPTION_GUIDE.md` | For integrating into an existing Claude setup |

## Troubleshooting

**Hooks not running**
```bash
chmod +x ~/.claude/hooks/*.sh ~/.claude/scripts/*.sh
~/.claude/scripts/validate-setup.sh
```

**RAG not returning results**
```bash
ollama serve &
ollama list    # should show mxbai-embed-large
cd /your/project && python3 -m rag_mcp_server.cli index .
```

**`ctm` command not found**
```bash
echo 'export PATH="$HOME/.claude/ctm/scripts:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Settings error on first run**
```bash
cp ~/.claude/settings.example.json ~/.claude/settings.json
```

**Full health check**
```bash
~/.claude/scripts/validate-setup.sh
```
