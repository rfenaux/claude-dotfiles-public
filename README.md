# Claude Code Dotfiles

> A production-grade configuration for Claude Code — 144 AI agents, persistent memory across sessions, self-healing automation, and local semantic search. Built and refined over months of daily professional use.

## What is this?

[Claude Code](https://claude.ai/claude-code) is Anthropic's AI coding assistant for the command line. This repository is a configuration layer for it: a collection of agents, automations, and memory systems that make Claude Code dramatically more capable for daily professional use.

Think of it as the difference between a stock IDE and one configured by an expert — same underlying tool, completely different experience.

## Who is this for?

- Developers and consultants who use Claude Code daily and want it to work harder
- Teams who want consistent AI behavior and shared agent libraries
- Anyone who's thought "I wish Claude would remember X between sessions"
- Power users who want to extend Claude with custom workflows and domain expertise

You don't need to understand all 144 agents to get value. Install it, start a session, and discover what it does as you work.

## What you get

| Capability | What it means for you |
|---|---|
| **144 specialized agents** | Claude routes complex requests to domain experts automatically — HubSpot, APIs, diagrams, ROI analysis, reasoning trios |
| **Persistent task memory (CTM)** | Your decisions, blockers, and task context survive between chat sessions |
| **Semantic search (RAG)** | Ask "what did we decide about auth last week?" and get an answer from your project history |
| **Self-healing config** | Broken hooks restart themselves; stale indexes reindex at session start; failures are logged and learned from |
| **Prompt enhancement** | Every prompt gets silently improved before Claude sees it |
| **60+ automation hooks** | Sessions auto-save, files auto-index, decisions auto-capture, failures auto-learn |

## Prerequisites

| Tool | Why | Install |
|---|---|---|
| **Claude Code CLI** | The AI assistant this configures | [claude.ai/claude-code](https://claude.ai/claude-code) |
| **Python 3.11+** | Powers RAG, hooks, and the task manager | [python.org](https://python.org) or `brew install python@3.12` |
| **git** | Required by the installer | `brew install git` or `apt install git` |
| **Ollama** _(optional)_ | Local AI embeddings for semantic search | [ollama.ai](https://ollama.ai) — the installer will offer to set up |

macOS is the primary platform. Linux is supported. Windows is not.

## Quick Install

### Option 1: Clone and run the interactive installer

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/claude-dotfiles.git /tmp/claude-dotfiles
bash /tmp/claude-dotfiles/install.sh
```

The installer will:
- Check your prerequisites and guide you through any that are missing
- Ask where to install (default: `~/.claude`)
- Safely handle existing `.claude` directories (backup or merge)
- Optionally set up Ollama for local AI search
- Validate the installation when done

### Option 2: Non-interactive (accepts all defaults)

```bash
bash install.sh --yes
```

### Option 3: Custom install path

```bash
bash install.sh --prefix ~/my-claude-config
```

### Option 4: Manual install

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/claude-dotfiles.git ~/.claude
chmod +x ~/.claude/hooks/*.sh ~/.claude/scripts/*.sh
cp ~/.claude/settings.example.json ~/.claude/settings.json
~/.claude/scripts/dotfiles-install-deps.sh
```

## After Install: First Session

1. **Restart your terminal** — new environment variables need to load
2. **Navigate to any project**: `cd /your/project`
3. **Start Claude Code**: `claude`
4. **Try these first**:

```
/ctm spawn "my first task"    → start tracking your work across sessions
/enhance                       → see prompt enhancement in action
/config-audit                  → health check your installation
```

Claude will run a self-check on startup and report any issues.

## Key Features

### Memory: CTM + RAG

**CTM (Cognitive Task Management)** tracks your tasks, decisions, and blockers in a local JSON store. When you start a new session, it tells Claude exactly what you were working on.

```bash
ctm spawn "implement auth"     # start a task
ctm brief                      # what was I working on?
ctm checkpoint                 # save progress before a break
ctm complete                   # mark done, extract learnings
```

**RAG (Retrieval Augmented Generation)** builds a semantic index of your project files and past sessions. Ask natural language questions about your project history.

```bash
rag search "how did we handle rate limiting?"
rag search "what was the decision about auth provider?"
```

Initialize RAG in a project:
```bash
cd /your/project
/rag-init      # in a Claude session
/reindex       # index project files
```

### Agents (144 specialized)

Agents activate automatically when Claude detects matching context. Examples:

| What you're doing | What activates |
|---|---|
| HubSpot implementation | `hubspot-api-crm` + 30 domain-specific agents |
| Creating a diagram | `bpmn-specialist` or `erd-generator` |
| Weighing two approaches | `decision-memo-generator` |
| Bulk file analysis (>20 files) | `codex-delegate` for token efficiency |
| High-stakes architecture | `reasoning-trio` (Claude + Codex + Gemini) |
| Inherited/broken project | `rescue-project-assessor` |

Full catalog: `AGENTS_INDEX.md`

### Skills (56 slash commands)

```
/ctm           → full task management (spawn, switch, checkpoint, brief)
/enhance       → prompt enhancement with approval flow
/pm-spec       → generate a PM specification
/pm-decompose  → break spec into implementable tasks
/brand-extract → extract brand identity from website or docs
/uat-generate  → generate UAT test cases
/session-retro → automated session retrospective
/mem-search    → search observation memory
```

Full catalog: `SKILLS_INDEX.md`

### Hooks (60+ automations)

Hooks run on session events and tool use. They work silently in the background:

- **SessionStart**: self-check, CTM brief, RAG staleness check, pre-warm context
- **PostToolUse**: auto-index files you write, extract lessons from failures, track patterns
- **PreCompact**: save conversation transcript before context compression
- **SessionEnd**: save session summary, compress observations, sync decisions

### Self-Healing Infrastructure

- **Service restart** — if RAG MCP server crashes, next session start restarts it
- **Index freshness** — stale indexes trigger background reindexing
- **Failure learning** — tool failures auto-extract lessons with confidence scoring
- **Config integrity** — every session validates agent count, hook executability, import chains
- **Circuit breakers** — hooks that fail repeatedly get disabled and logged

## Directory Structure

```
~/.claude/
├── agents/           # 144 AI agent definitions
├── skills/           # 56 slash command skills
├── hooks/            # 60+ event-triggered automations
├── rules/            # 16 auto-loaded behavioral guidelines
├── scripts/          # 71 utility scripts
├── lib/              # Python libraries (RAG, pruning, intent prediction)
├── config/           # 22 JSON configuration files
├── ctm/              # Cognitive Task Management
│   └── lib/          # 32 CTM core modules
├── mcp-servers/      # MCP server implementations
│   └── rag-server/   # RAG with hybrid vector + BM25 search
├── docs/             # Extended documentation
├── prds/             # Product requirement documents
└── templates/        # Project templates
```

## Customizing

### Add an agent

Create `~/.claude/agents/my-agent.md`:

```yaml
---
name: my-agent
description: One-line description of what this agent does and when to invoke it.
model: claude-sonnet-4-5
---

Your agent instructions here. Describe its role, expertise, and how it should respond.
```

### Disable a hook

Edit `~/.claude/settings.json` and remove or comment out the hook entry under the relevant event.

### Add a Bash permission

Edit the `permissions.allow` list in `~/.claude/settings.json`:

```json
"permissions": {
  "allow": [
    "Bash(npm *)",
    "Bash(pytest *)"
  ]
}
```

### Adjust settings

`~/.claude/settings.json` controls everything: hooks, permissions, MCP servers, status line, and more. `settings.example.json` is the documented reference.

## Troubleshooting

### Hooks not running

```bash
# Check hooks are executable
ls -la ~/.claude/hooks/*.sh

# Fix permissions
chmod +x ~/.claude/hooks/*.sh ~/.claude/scripts/*.sh

# Full validation
~/.claude/scripts/validate-setup.sh
```

### RAG not returning results

```bash
# Is Ollama running?
ollama ps

# Start it
ollama serve &

# Is the embedding model available?
ollama list    # should show mxbai-embed-large

# Re-index your project
cd /your/project && python3 -m rag_mcp_server.cli index .
```

### `ctm` command not found

CTM CLI lives at `~/.claude/ctm/scripts/ctm`. Add it to your PATH:

```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$HOME/.claude/ctm/scripts:$PATH"

# Then reload:
source ~/.zshrc
```

### Settings not applying

Claude Code reads `~/.claude/settings.json`. If it doesn't exist:

```bash
cp ~/.claude/settings.example.json ~/.claude/settings.json
```

Then restart Claude Code.

### Full health check

```bash
~/.claude/scripts/validate-setup.sh
```

Checks all components and reports errors vs warnings with fix instructions.

## Key Documentation

| Guide | Purpose |
|---|---|
| `CLAUDE.md` | Main memory file — auto-loaded every session |
| `AGENTS_INDEX.md` | Full agent catalog with routing tables |
| `SKILLS_INDEX.md` | All slash commands with triggers |
| `CTM_GUIDE.md` | Cognitive Task Management system |
| `RAG_GUIDE.md` | Semantic search usage and strategy |
| `CONFIGURATION_GUIDE.md` | Full architecture reference |
| `CDP_PROTOCOL.md` | Agent delegation protocol |
| `RESOURCE_MANAGEMENT.md` | Load-aware spawning and profiles |

## Requirements

- Claude Code CLI
- Python 3.11+
- Ollama with `mxbai-embed-large` model (for local RAG embeddings)
- Node.js 18+ (for some MCP servers)
- `jq` (for hook JSON processing)
- `ripgrep` / `fd` (for fast file search)

## License

MIT — use, fork, and adapt freely. Attribution appreciated but not required.

## Acknowledgments

- Built for [Claude Code](https://claude.ai/claude-code) by Anthropic
- RAG server inspired by the OpenClaw architecture patterns
