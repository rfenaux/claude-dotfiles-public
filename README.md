# Claude Code — Huble Team Config

A production-grade configuration layer for Claude Code, built for Huble's daily consulting work. Adds persistent memory, 144 specialized agents (HubSpot, Salesforce, diagrams, proposals, and more), semantic search across your project history, and 60+ automation hooks — all working silently in the background.

## What you get

| Capability | What it means |
|---|---|
| **144 specialized agents** | Claude auto-routes to domain experts — HubSpot implementation, API questions, diagrams, ROI analysis, reasoning trios |
| **Persistent task memory (CTM)** | Decisions, blockers, and task context survive between sessions |
| **Semantic search (RAG)** | Ask "what did we decide about auth last week?" and get an answer from your project history |
| **Prompt enhancement** | Every prompt is silently improved before Claude sees it |
| **60+ automation hooks** | Sessions auto-save, files auto-index, decisions auto-capture, failures auto-learn |
| **Self-healing infrastructure** | Broken hooks restart themselves; stale indexes reindex at session start |

## Prerequisites

| Tool | Install |
|---|---|
| **Claude Code CLI** | `npm install -g @anthropic-ai/claude-code` |
| **Python 3.11+** | `brew install python@3.12` |
| **git** | `brew install git` |
| **Ollama** _(recommended)_ | `brew install ollama` — local AI embeddings for semantic search |

macOS is the primary platform. Linux is supported.

## Install

Interactive (recommended for first install — walks you through Ollama setup):

```bash
git clone https://github.com/rfenaux/claude-dotfiles-public.git /tmp/claude-dotfiles
bash /tmp/claude-dotfiles/install.sh
```

Non-interactive (accepts all defaults, skips optional prompts):

```bash
git clone https://github.com/rfenaux/claude-dotfiles-public.git /tmp/claude-dotfiles
bash /tmp/claude-dotfiles/install.sh --yes
```

**Updating an existing install:** The installer detects existing `~/.claude` and offers merge mode — new files are added without overwriting your customizations.

## First session

```
/ctm spawn "my first task"    → start tracking work across sessions
/enhance                       → see prompt enhancement in action
/config-audit                  → verify your installation
```

Claude runs a self-check on startup and reports any issues.

## Key documentation

| File | Purpose |
|---|---|
| `CLAUDE.md` | Main memory file — auto-loaded every session. Start here. |
| `CTM_GUIDE.md` | Cognitive Task Management — task tracking, decisions, cross-session memory |
| `RAG_GUIDE.md` | Semantic search — indexing projects, search order, reindexing |
| `CONFIGURATION_GUIDE.md` | Full architecture reference — hooks, agents, config, troubleshooting |

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
# Add to ~/.zshrc:
export PATH="$HOME/.claude/ctm/scripts:$PATH"
source ~/.zshrc
```

**Full health check**
```bash
~/.claude/scripts/validate-setup.sh
```
