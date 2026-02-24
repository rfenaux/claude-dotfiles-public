# RAG Server for Claude Code

A local, private document search system for Claude Code using Ollama embeddings and LanceDB.

## Dashboard

**Always available at: http://localhost:8420**

The dashboard provides:
- Start/Stop Ollama control
- Process monitor (view/kill processes)
- Project list (all RAG-initialized projects)
- Full documentation

## Quick Start

```bash
# In any project directory with Claude Code:
/rag init           # Initialize RAG
/rag index docs/    # Index files
/rag search "query" # Semantic search
```

## Commands

| Command | Description |
|---------|-------------|
| `/rag init` | Initialize RAG in current project |
| `/rag index <path>` | Index a file or folder |
| `/rag search "query"` | Semantic search across indexed docs |
| `/rag list` | List all indexed documents |
| `/rag remove <file>` | Remove a file from index |
| `/rag status` | Show index status and config |
| `/rag backends` | Show available backends |

## How It Works

1. **Documents** are parsed (PDF, DOCX, MD, code files, etc.)
2. **Chunks** are created with overlap for context
3. **Embeddings** are generated via Ollama (mxbai-embed-large)
4. **Vectors** are stored in LanceDB (per-project `.rag/` folder)
5. **Search** finds most similar chunks to your query

## Auto-Start Configuration

### Dashboard (LaunchAgent)
- Starts automatically on macOS login
- Always available at http://localhost:8420
- Plist: `~/Library/LaunchAgents/com.claude.rag-dashboard.plist`

### MCP Server
- Starts automatically with Claude Code
- Configured in `~/.mcp.json`

### Ollama
- Auto-starts when any RAG tool is used
- Can also be started via dashboard or `brew services start ollama`

## File Locations

| Component | Path |
|-----------|------|
| MCP Server | `~/.claude/mcp-servers/rag-server/` |
| Dashboard | `~/.claude/rag-dashboard/` |
| Dashboard URL | http://localhost:8420 |
| MCP Config | `~/.mcp.json` |
| LaunchAgent | `~/Library/LaunchAgents/com.claude.rag-dashboard.plist` |
| Hook Script | `~/.claude/hooks/rag-startup.sh` |
| Project Index | `<project>/.rag/` |

## Supported File Types

- **Documents**: PDF, DOCX, Markdown, TXT, HTML
- **Code**: Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, etc.
- **Config**: JSON, YAML, TOML, INI

## Troubleshooting

### "Ollama not running"
```bash
brew services start ollama
# Or use the Start button on the dashboard
```

### "No embedding model"
```bash
ollama pull mxbai-embed-large
# Or use the Pull Model button on the dashboard
```

### Dashboard not accessible
```bash
# Check if running
lsof -i :8420

# Start manually
python3 ~/.claude/rag-dashboard/server.py

# Or reload LaunchAgent
launchctl load ~/Library/LaunchAgents/com.claude.rag-dashboard.plist
```

### Claude Code freezes
The MCP server has fast 2-second timeouts. If Ollama isn't running, it will:
1. Fail fast (not hang)
2. Attempt to auto-start Ollama
3. Retry the connection

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Claude Code    │────▶│   MCP Server    │
│                 │     │  (rag-server)   │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Ollama  │ │ LanceDB  │ │ Parsers  │
              │(embeddings)│(vectors) │ │(PDF,DOCX)│
              └──────────┘ └──────────┘ └──────────┘

┌─────────────────┐
│    Dashboard    │──── http://localhost:8420
│   (server.py)   │
└─────────────────┘
```

## Uninstall

```bash
# Remove LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.claude.rag-dashboard.plist
rm ~/Library/LaunchAgents/com.claude.rag-dashboard.plist

# Remove MCP config
# Edit ~/.mcp.json and remove the "rag-server" entry

# Remove files
rm -rf ~/.claude/mcp-servers/rag-server
rm -rf ~/.claude/rag-dashboard
rm -rf ~/.claude/hooks/rag-startup.sh

# Stop Ollama (optional)
brew services stop ollama
```

## Credits

- **Ollama** - Local LLM and embeddings
- **LanceDB** - Vector database
- **FastMCP** - MCP server framework
