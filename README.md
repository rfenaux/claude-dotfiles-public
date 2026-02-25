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

| Tool | Required? | Install |
|---|---|---|
| **Claude Code CLI** | Yes | `npm install -g @anthropic-ai/claude-code` |
| **Python 3.11+** | Yes | `brew install python@3.12` |
| **git** | Yes | `brew install git` |
| **Ollama** | Recommended | `brew install ollama` — local AI embeddings for semantic search |
| **jq** | Recommended | `brew install jq` — JSON processing for hooks |

macOS is the primary platform. Linux is supported.

> **The installer is smart about existing tools.** It detects what you already have and skips anything that's already installed — you won't get duplicate installs or version conflicts. The table above is just so you know what's involved.

**Want to see what you have before running anything?**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/rfenaux/claude-dotfiles-public/main/install.sh) --check
```

Or if you've already cloned the repo:

```bash
bash install.sh --check
```

This prints a quick report of what's installed, what's missing, and what versions you have — without changing anything.

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

**Settings error on first run** (e.g. `prompt: Expected string, but received undefined`)
```bash
# This usually means a pre-existing hook in settings.json has an old format.
# Reset to the known-good config:
cp ~/.claude/settings.example.json ~/.claude/settings.json
```

**Full health check**
```bash
~/.claude/scripts/validate-setup.sh
```
