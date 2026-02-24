---
name: reindex
description: Quick RAG reindex for current project — pre-flight, background execution, exclusions.
trigger: /reindex
context: fork
agent: general-purpose
model: haiku
tools:
  - Read
  - Bash
  - Glob
  - Write
user-invocable: true
---

# Quick RAG Reindex

Lightweight fire-and-forget reindex for the current project. Unlike `/rag-batch-index` (full discovery + audit), this just reindexes what's already tracked.

## Trigger Phrases

- "reindex this project"
- "refresh the RAG index"
- "reindex"

## Anti-Pattern Warning

DO NOT:
- Try MCP, fail, try CLI, fail, try MCP again (wrong-approach cycling)
- Spawn sub-agents to try MCP (they cannot access MCP tools)
- Debug MCP connectivity (not your job — use CLI fallback)
- Spend more than 1 attempt on any single approach

## Workflow

### Step 0: Route Decision (MANDATORY — do this FIRST)

Determine route ONCE and commit to it:

1. **Am I in a sub-agent?** If yes → CLI only (MCP is main-session only)
2. **Is MCP `mcp__rag-server__rag_reindex` available?** Try it ONCE.
   - If it works → Use MCP for all operations
   - If it fails → Switch to CLI immediately (DO NOT retry MCP)
3. **CLI fallback**: `cd "$PROJECT_PATH" && python3 -m rag_mcp_server.cli reindex . 2>&1`

**NEVER cycle between approaches.** The mcp-fast-fail rule applies here.

### Step 1: Pre-flight

Run this check — if it fails, stop immediately and inform user:

```bash
curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; assert any('mxbai-embed-large' in m for m in models), 'Model not found'" 2>&1 || { echo "FAIL: Ollama not running or mxbai-embed-large not available. Run: ollama pull mxbai-embed-large"; exit 1; }
```

### Step 2: Detect Project

Identify the current project path. Look for `.rag/` directory:

```bash
# Check current directory and parents for .rag/
if [ -d ".rag" ]; then
    PROJECT_PATH="$(pwd)"
elif [ -d "$(git rev-parse --show-toplevel 2>/dev/null)/.rag" ]; then
    PROJECT_PATH="$(git rev-parse --show-toplevel)"
else
    echo "No .rag/ directory found. Run /rag-init first."
    exit 1
fi
```

### Step 3: Reindex

**MCP available (preferred):** Use `mcp__rag-server__rag_reindex` with the project path.

**MCP unavailable (fallback):** Run via CLI in background:

```bash
cd "$PROJECT_PATH" && python3 -m rag_mcp_server.cli reindex . 2>&1
```

**IMPORTANT:** RAG MCP tools only work in the main session. Never delegate to sub-agents.

### Step 4: Exclusions

Load exclusion patterns from SSOT: `~/.claude/config/rag-exclusions.json`

Apply `auto_exclude` patterns automatically. For `ask_user` patterns, confirm with user first. Check `warnings` for slow/large file alerts.

### Step 5: Report

After reindex completes, output a brief summary:

```markdown
## Reindex Complete

- **Project:** <path>
- **Files indexed:** N
- **Files skipped:** N (unchanged)
- **Errors:** N
- **Duration:** Xs
```

## Key Differences from /rag-batch-index

| Aspect | /reindex | /rag-batch-index |
|--------|----------|-----------------|
| Scope | Reindex existing tracked files | Full discovery + new files |
| Speed | Fast (skip unchanged) | Slower (scan + audit) |
| Interaction | Fire-and-forget | Interactive (folder selection) |
| Audit | No post-audit | Full audit report |
| Use when | Regular refresh | First index or deep audit |

## Related Skills

- `rag-batch-index` — Full project indexing with discovery and audit
- `rag-init` — Initialize RAG for a project
- `rag-status` — Check RAG health and stats
