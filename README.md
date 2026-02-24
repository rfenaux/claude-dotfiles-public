# Claude Code Dotfiles

A comprehensive, battle-tested configuration for [Claude Code](https://claude.ai/claude-code) (Anthropic's CLI tool). Built and refined over months of daily use on real enterprise projects.

This repository contains a full setup including:
- **148 Agents** - Specialized AI agents for every use case
- **54 Skills** - Reusable slash command workflows
- **60+ Hooks** - Automation triggers for every session event
- **16 Rules** - Auto-loaded behavioral guidelines
- **RAG MCP Server** - Local semantic search with hybrid retrieval
- **CTM** - Cognitive Task Management for multi-session continuity
- **Self-Healing** - Auto-detect and fix config drift

## Highlights

### Memory & Context Management
- **CTM (Cognitive Task Management)** - Bio-inspired task tracking across sessions with priority scheduling, dependency graphs, and deadlines
- **RAG System** - Local semantic search with hybrid vector + BM25 retrieval, tree navigation, and knowledge graphs
- **Memory Flush** - Pre-compaction extraction of decisions/learnings before context is lost
- **Tool Result Pruning** - TTL-based cleanup of stale tool outputs to keep context lean
- **Observation Memory** - Auto-captured session summaries indexed for future retrieval

### Self-Healing Infrastructure
- **Auto-heal services** - Detects and restarts RAG MCP, Ollama, and Dashboard when down
- **Config integrity checks** - Validates agent count, hook executability, import chains on every session
- **Failure learning** - Automatically extracts lessons from tool failures with SONA confidence scoring
- **Auto-reindex** - Detects stale RAG indexes and triggers background reindexing

### Agents (148 specialized)
- HubSpot implementation (Marketing, Sales, Service, Operations, Content, Commerce Hubs)
- HubSpot API specialists (30+ domain-specific agents)
- Salesforce-HubSpot mapping (Contacts, Companies, Deals, Tickets, Activities)
- Document generation (ERD, BPMN, Lucidchart, presentations, proposals)
- ROI/commercial analysis and investment justification
- Technical specifications and architecture
- Multi-model reasoning (Claude + Codex + Gemini trio)
- Rescue/audit agents for inherited projects
- UAT scenario generators (Sales, Service, Integration, Migration)

### Skills (54 slash commands)
- `/ctm` - Full task management (spawn, switch, checkpoint, brief)
- `/enhance` - Prompt enhancement with approval flow
- `/pm-spec` + `/pm-decompose` + `/pm-gh-sync` - Full PM workflow
- `/brand-extract` - Extract brand identity from websites/docs
- `/uat-generate` - UAT test case generation
- `/validate-hooks` - Hook anti-pattern detection
- `/session-retro` - Automated session retrospective analysis
- `/scope-defense-bundle` - SOW delta matrix for commercial defense
- `/research-loop` - Multi-source research with confidence scoring
- And 45 more...

### Rules (16 behavioral guidelines, auto-loaded)
- ADHD focus support and re-anchoring
- Decision auto-capture and ambiguity marking
- Deviation handling (bugs, scope creep, blockers)
- Large file editing guards
- Hook development quality standards
- Parallelization strategy
- Sub-agent delegation patterns
- MCP fast-fail rules

## Setup

### 1. Clone this repository

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/claude-dotfiles.git ~/.claude
```

### 2. Install dependencies

```bash
~/.claude/scripts/dotfiles-install-deps.sh
```

### 3. Configure hook settings

```bash
cp ~/.claude/settings.example.json ~/.claude/settings.json
# Edit settings.json to enable/disable hooks as needed
```

### 4. Start Ollama for local RAG embeddings

```bash
ollama pull mxbai-embed-large
ollama serve
```

### 5. Initialize RAG for a project

```bash
cd /your/project
claude  # start a session, then:
# /rag-init      (initialize)
# /reindex       (index current project)
```

### 6. (Optional) Configure cloud model fallbacks

```bash
export OPENAI_API_KEY="sk-..."   # for Codex delegation
export GOOGLE_API_KEY="..."      # for Gemini delegation
```

### 7. (Optional) Configure Huble wiki routing

If you use the Huble-style wiki routing agents, set the path to your own indexed wiki:

```bash
export HUBLE_WIKI_PATH=~/projects/your-knowledge-base
```

## Directory Structure

```
~/.claude/
├── agents/           # 148 AI agent definitions
├── skills/           # 54 slash command skills
├── hooks/            # 60+ event-triggered automations
├── rules/            # 16 auto-loaded behavioral guidelines (NEW)
├── scripts/          # 71 utility scripts
├── lib/              # Python libraries (RAG, pruning, intent prediction)
├── config/           # 22 JSON configuration files
├── ctm/              # Cognitive Task Management
│   └── lib/          # 32 CTM core modules
├── mcp-servers/      # MCP server implementations
│   └── rag-server/   # RAG with hybrid search
├── prds/             # Product requirement documents
├── docs/             # Documentation
└── templates/        # Project templates
```

## Key Documentation

| Guide | Purpose |
|-------|---------|
| `CLAUDE.md` | Main memory file (auto-loaded every session) |
| `CTM_GUIDE.md` | Cognitive Task Management system |
| `RAG_GUIDE.md` | RAG system usage and search strategy |
| `CDP_PROTOCOL.md` | Agent delegation protocol |
| `AGENTS_INDEX.md` | Full agent catalog with routing tables |
| `SKILLS_INDEX.md` | Skills catalog with triggers |
| `CONFIGURATION_GUIDE.md` | Complete system architecture |
| `RESOURCE_MANAGEMENT.md` | Load-aware spawning and profiles |
| `LESSONS_GUIDE.md` | SONA confidence scoring and lesson system |

## Requirements

- Claude Code CLI
- Python 3.11+
- Ollama with `mxbai-embed-large` model (for local RAG embeddings)
- Node.js 18+ (for some MCP servers)
- `jq` (for hook JSON processing)
- `ripgrep` / `fd` (for fast file search)

## License

MIT - Feel free to use and adapt for your own setup.

## Acknowledgments

- Built for [Claude Code](https://claude.ai/claude-code) by Anthropic
- RAG server inspired by the OpenClaw architecture patterns
