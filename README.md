# Claude Code Dotfiles

A comprehensive configuration for [Claude Code](https://claude.ai/claude-code) (Anthropic's CLI tool).

This repository contains my personal setup for Claude Code, including:
- **Agents** - Specialized AI agents for various tasks
- **Skills** - Reusable command templates (slash commands)
- **Hooks** - Automation triggers for session events
- **Scripts** - Utility scripts for maintenance
- **MCP Servers** - Custom Model Context Protocol servers (RAG)
- **CTM** - Cognitive Task Management system for multi-session continuity

## Features

### Memory & Context Management
- **CTM (Cognitive Task Management)** - Bio-inspired task tracking across sessions
- **RAG System** - Local semantic search with hybrid retrieval (vector + BM25)
- **Memory Flush** - Pre-compaction extraction of decisions/learnings
- **Tool Result Pruning** - TTL-based cleanup of stale tool outputs

### Agents (125+)
Specialized agents for:
- HubSpot implementation (Marketing, Sales, Service, Operations, Content, Commerce Hubs)
- Salesforce-HubSpot mapping
- Document generation (ERD, BPMN, Lucidchart, presentations)
- ROI/commercial analysis
- Technical specifications
- Multi-model reasoning (Claude + Codex + Gemini)

### Skills (40+)
Slash commands for common workflows:
- `/ctm` - Task management
- `/enhance` - Prompt enhancement
- `/brand-extract` - Extract brand identity from websites
- `/pptx` - PowerPoint generation
- `/uat-generate` - UAT test case generation
- And many more...

## Setup

1. Clone this repository:
```bash
git clone https://github.com/<your-username>/claude-dotfiles.git ~/.claude
```

2. Install dependencies:
```bash
~/.claude/scripts/dotfiles-install-deps.sh
```

3. Configure API keys (optional, for cloud fallbacks):
```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
```

4. Start Ollama for local embeddings:
```bash
ollama pull mxbai-embed-large
ollama serve
```

## Directory Structure

```
~/.claude/
├── agents/           # AI agent definitions
├── skills/           # Slash command skills
├── hooks/            # Event-triggered automations
├── scripts/          # Utility scripts
├── lib/              # Python libraries
├── ctm/              # Cognitive Task Management
│   └── lib/          # CTM core libraries
├── mcp-servers/      # MCP server implementations
│   └── rag-server/   # RAG with hybrid search
├── config/           # Configuration files
├── prds/             # Product requirement documents
├── docs/             # Documentation
└── templates/        # Project templates
```

## Key Documentation

- `CLAUDE.md` - Main configuration (loaded every session)
- `RAG_GUIDE.md` - RAG system usage
- `CTM_GUIDE.md` - Cognitive Task Management
- `CDP_PROTOCOL.md` - Agent delegation protocol
- `AGENTS_INDEX.md` - Agent catalog
- `SKILLS_INDEX.md` - Skills catalog

## Requirements

- Claude Code CLI (obviously)
- Python 3.11+
- Ollama (for local embeddings)
- Node.js 18+ (for some MCP servers)

## License

MIT - Feel free to use and adapt for your own setup.

## Acknowledgments

- Inspired by [OpenClaw](https://github.com/openclaw/openclaw) architecture
- Built for Claude Code by Anthropic
