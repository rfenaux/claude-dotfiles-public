# RAG System - Full Guide

Detailed reference for the local RAG (Retrieval-Augmented Generation) system.

**Dashboard:** http://localhost:8420

---

## When to Use RAG

### Always Use `rag_search` First When:
- User asks ANY question about the project (requirements, design, decisions, context)
- User asks "how does X work", "where is X", "what is X", "why did we..."
- User needs context about existing docs, transcripts, or specs
- User references past meetings, decisions, or documentation
- Before reading multiple files to understand something
- When you need project-specific context to answer accurately

### Skip RAG Only For:
- Direct file edits
- Running commands
- Creating new files
- User explicitly says "don't use RAG"

---

## RAG Workflow

1. Check for `.rag/` folder → if exists, RAG is available
2. Use `rag_search` with a relevant natural language query
3. Review the returned chunks - **check the date fields for chronology**
4. **Consider chronology:** newer information supersedes older when conflicts exist
5. Answer based on RAG results + your knowledge
6. Only use Grep/Read if RAG doesn't have enough info or you need exact file content

**Pro tip:** RAG finds semantic matches. Ask questions naturally: "What are the integration requirements?" not keyword searches.

---

## Chronology Awareness

Each search result includes multiple date fields:

| Field | Meaning |
|-------|---------|
| `content_date` | Dates mentioned WITHIN the text (e.g., "as of January 2024") |
| `file_date` | When the file was last modified on disk |
| `relevant_date` | Best date to use (content_date if available, otherwise file_date) |
| `date_range` | If the chunk mentions multiple dates, shows (earliest, latest) |

### Using Dates Intelligently

- **`content_date` is most important** - it tells you when the information *refers to*, not when it was written
- A file modified in 2024 might contain outdated info about 2022; trust the content dates
- When results conflict, prefer the one with the most recent `relevant_date`
- If a chunk has `date_range`, the information may discuss evolution over time

### Temporal Boosting (Automatic)

Search results are automatically boosted by recency:

| Recency | Boost | Effect |
|---------|-------|--------|
| Last 7 days | 0.7x | 30% higher ranking |
| Last 30 days | 0.85x | 15% higher ranking |
| Last 90 days | 1.0x | Neutral |
| Last year | 1.1x | 10% lower ranking |
| Older | 1.2x | 20% lower ranking |

**Supersession Detection**: Content with strikethrough (`~~text~~`), "superseded by", or "[deprecated]" markers is automatically penalized in search ranking.

Results include `temporal_boost` metadata showing applied adjustments.

### How to Respond with Dates

```
"According to the December 2024 update..."
"This changed over time: initially [2022 decision], but as of [2024] it became..."
"I found info from [dates] - which reflects the current state?"
```

---

## Quick Commands

| Command | Action |
|---------|--------|
| `rag init` | Initialize RAG in current project |
| `rag index docs/` | Index files or folders |
| `rag reindex` | Clear and rebuild entire index |
| `rag search "query"` | Semantic search |
| `rag status` | Check status |

---

## Auto-Start Services

| Service | Behavior |
|---------|----------|
| **Ollama** | Auto-starts when RAG tools are used |
| **Dashboard** | Runs on login (LaunchAgent) |
| **MCP Server** | Starts with Claude Code |

---

## Real-Time Auto-Indexing

Files are **automatically indexed immediately** when created or modified during a conversation.

### How It Works

**Real-time (PostToolUse):**
1. After every `Write` or `Edit` tool completes
2. Hook checks if file is in a RAG-enabled project
3. Indexes the file immediately (async, non-blocking)
4. File is searchable within seconds

**Batch (PreCompact/SessionEnd):**
1. Catches any files modified outside Claude (manually added)
2. Finds all files modified since last index
3. Indexes them all at once

### Triggers

| Hook | When | What It Indexes |
|------|------|-----------------|
| `PostToolUse` (Write/Edit) | Immediately after file write | The specific file just written |
| `PreCompact` | Before compaction | All modified files since last index |
| `SessionEnd` | When session ends | All modified files since last index |

### What Gets Indexed

| Extension | Real-time | Batch |
|-----------|-----------|-------|
| `.md`, `.txt`, `.json` | ✅ | ✅ |
| `.pdf`, `.docx`, `.html` | ✅ | ✅ |
| `.py`, `.js`, `.ts`, `.tsx`, `.jsx` | ✅ | ✅ |

### Excluded Paths
`.git/`, `.rag/`, `node_modules/`, `__pycache__/`, `.venv/`, `.claude/`

### Location
Only works for projects in `~/Documents/(Projects|Docs)*/` with a `.rag/` folder.

### Scripts
- Real-time: `~/.claude/hooks/rag-index-on-write.sh`
- Batch: `~/.claude/hooks/save-conversation.sh`

### Manual Index (if needed)
```bash
rag index path/to/file.md
# or for whole folder
rag index 05-WORKING-DRAFTS/
```

### Searching Past Conversations
```bash
rag search "what did we decide about authentication?"
```

---

## Project Memory System

For persistent memory across conversations, use the context structure:

```
project/
├── .claude/
│   ├── context/
│   │   ├── DECISIONS.md     # Architecture decisions with supersession tracking
│   │   ├── SESSIONS.md      # Session summaries
│   │   ├── CHANGELOG.md     # Project evolution
│   │   └── STAKEHOLDERS.md  # Key people
```

### Initialize Memory System
```bash
# Copy templates to your project
cp -r ~/.claude/templates/context-structure/* /path/to/project/.claude/context/
```

Or ask Claude: "Initialize the memory system for this project"

### Decision Tracking Pattern

Use DECISIONS.md for explicit supersession:

```markdown
## Active Decisions

### Database: PostgreSQL
- **Decided**: 2026-01-07
- **Supersedes**: MongoDB consideration (2025-12-15)

## Superseded Decisions

### ~~MongoDB~~ → PostgreSQL (2026-01-07)
- **Original decision**: 2025-12-15
- **Why superseded**: Relational requirements emerged
```

The strikethrough and supersession patterns are automatically detected by RAG and deprioritized in search.

---

## MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `mcp__rag-server__rag_search` | Semantic search across indexed documents |
| `mcp__rag-server__rag_index` | Index a file or folder (auto-extracts document trees) |
| `mcp__rag-server__rag_init` | Initialize RAG for a project |
| `mcp__rag-server__rag_status` | Get index statistics |
| `mcp__rag-server__rag_list` | List all indexed documents |
| `mcp__rag-server__rag_remove` | Remove a document from index |
| `mcp__rag-server__rag_reindex` | Clear and rebuild index |
| `mcp__rag-server__rag_tree_search` | Section-filtered search (vector + tree post-filter) |
| `mcp__rag-server__rag_tree_navigate` | Browse document outline / section hierarchy |
| `mcp__rag-server__rag_tree_list` | List documents with extracted tree structures |
| `mcp__rag-server__rag_clusters` | List topic clusters discovered in indexed documents |

---

## Tree-Enhanced Search (Document Structure)

RAG automatically extracts hierarchical document structure during indexing and uses it for section-scoped search.

### How It Works

During `rag_index`, the system:
1. Extracts document tree (TOC/headings) from PDF, DOCX, or Markdown files
2. Stores tree as JSON sidecar in `.rag/trees/`
3. Enriches chunks with tree metadata (`tree_path`, `tree_level`, `tree_node_id`)

| Source | Extraction Method | Page Mapping |
|--------|-------------------|--------------|
| PDF | PyMuPDF `get_toc()` | Yes (verified) |
| DOCX | Heading paragraph styles | No |
| Markdown | `#` headers, underline headers | No |

### Section-Filtered Search

Use `rag_tree_search` to scope results to specific document sections:

```
rag_tree_search("OAuth flow", section_filter="Authentication")
→ Only returns chunks under sections containing "Authentication" in their tree path

rag_tree_search("pricing", source_file="proposal.pdf", min_level=1, max_level=2)
→ Only top-level and second-level sections from proposal.pdf
```

### Document Navigation

Browse document structure without reading the full file:

```
rag_tree_navigate(source_file="spec.pdf")
→ Returns full document outline with node IDs, page ranges, verification status

rag_tree_navigate(source_file="spec.pdf", node_id="0005", depth=3)
→ Returns node + children + parent chain (breadcrumb)
```

### Tree Listing

```
rag_tree_list(project_path)
→ Lists all documents with extracted trees, node counts, depth, verification %
```

### Storage

Trees are stored as JSON sidecars: `.rag/trees/{md5_hash}.json`
- No schema migration needed
- Auto-deleted when source file is re-indexed or removed
- Files without detectable structure get no tree (graceful degradation)

---

## Knowledge Graph Layer (Optional)

Entity and relationship extraction for graph-enriched search. **Disabled by default.**

### Enable

Set `knowledge_graph.enabled: true` in `.rag/config.json`:

```json
{
  "knowledge_graph": {
    "enabled": true,
    "extraction_model": "llama3.2:3b"
  }
}
```

**Prerequisite:** `ollama pull llama3.2:3b` (~2GB)

### How It Works

When enabled, during indexing:
1. Entity extraction via Ollama (with regex fallback if Ollama unavailable)
2. Entities + relationships stored in `.rag/knowledge_graph.db` (SQLite)
3. Chunk-entity links maintained for search enrichment

During search:
1. Standard vector search runs first
2. Entities for matched chunks are retrieved
3. 1-hop graph expansion finds related entities
4. Graph boost adjusts relevance scores based on entity connectivity

### Search Results Enrichment

When graph is enabled, `rag_search` results include:
- `graph_entities`: entities found in the chunk
- `graph_context`: related entities from graph expansion

### Graceful Degradation

- If Ollama is down: indexing succeeds (entity extraction skipped silently)
- If graph disabled: `rag_search` returns identical results (no new fields)
- All graph code wrapped in try/except -- never blocks core functionality

---

## Hybrid Search (Vector + BM25)

RAG uses **hybrid retrieval** combining vector embeddings with BM25 full-text search for better accuracy on both semantic queries and exact term matches.

### How It Works

| Component | Weight | Best For |
|-----------|--------|----------|
| **Vector** | 70% | Semantic meaning, concepts, paraphrases |
| **BM25** | 30% | Exact terms, error codes, IDs, rare words |

Results are fused using **Reciprocal Rank Fusion (RRF)** for balanced ranking.

### Why Hybrid?

| Query Type | Vector Only | Hybrid |
|------------|-------------|--------|
| "authentication flow" | ✓ Good | ✓ Good |
| "CTM-401 error" | ✗ Poor | ✓ Finds exact match |
| "PostgreSQL vs MySQL" | ✓ Good | ✓ Good |
| "hubspot-api-specialist" | ✗ May miss | ✓ Exact match |

### Configuration

Edit `~/.claude/mcp-servers/rag-server/config.json`:

```json
{
  "search": {
    "mode": "hybrid",
    "vector_weight": 0.7,
    "text_weight": 0.3
  }
}
```

Modes: `"hybrid"` (default), `"vector"`, `"bm25"`

---

## Embedding Provider Fallback

RAG uses a **fallback chain** for embedding generation to ensure availability:

1. **Ollama** (local, free) — Default, uses `mxbai-embed-large`
2. **OpenAI** (cloud, paid) — Falls back if Ollama unavailable
3. **Gemini** (cloud, paid) — Last resort fallback

### Status Check

```bash
python3 ~/.claude/mcp-servers/rag-server/embeddings.py
```

### Configuration

Set API keys for cloud fallbacks:
```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
```

Edit `~/.claude/mcp-servers/rag-server/config.json`:

```json
{
  "embeddings": {
    "provider_order": ["ollama", "openai", "gemini"],
    "ollama": {
      "model": "mxbai-embed-large"
    }
  }
}
```

---

## Daily Memory Logs

Projects can use daily log files for temporal organization:

```
project/.claude/memory/
├── 2026-01-28.md
├── 2026-01-29.md
└── 2026-01-30.md  ← today
```

### Automatic Creation

The `daily-log-init.sh` hook creates today's log at session start.

### Appending Content

```bash
~/.claude/hooks/daily-log-append.sh /path/to/project decision "Use PostgreSQL for persistence"
~/.claude/hooks/daily-log-append.sh /path/to/project learning "API rate limit is 100/min"
```

### Cleanup

Remove logs older than 30 days:
```bash
~/.claude/scripts/cleanup-daily-logs.sh 30
```

---

## Batch Embedding API

For large indexing jobs, embeddings are generated in batches to reduce API calls and improve performance.

### How It Works

| Provider | Batch Size | API Calls for 500 docs |
|----------|------------|------------------------|
| Ollama | 1 (sequential) | 500 calls |
| OpenAI | 100 | 5 calls |
| Gemini | 100 | 5 calls |

### Usage

Batch mode is automatic for large indexing operations:

```python
from embeddings import get_embedding_chain

chain = get_embedding_chain()
# Automatic batching for large lists
result = chain.embed_batch(texts, batch_size=100)
```

### Configuration

Edit `~/.claude/mcp-servers/rag-server/config.json`:

```json
{
  "indexing": {
    "batch_size": 100,
    "progress_reporting": true
  }
}
```

---

## Per-Agent Embedding Storage

Each agent can have its own isolated embedding database to prevent cross-contamination.

### Directory Structure

```
~/.claude/rag/
├── global/           # Shared knowledge (lessons, docs)
│   └── embeddings.sqlite
└── agents/           # Per-agent stores
    ├── worker-abc123.sqlite
    ├── explorer-def456.sqlite
    └── ...
```

### Usage

```python
from agent_storage import get_agent_store, get_global_store

# Per-agent store
store = get_agent_store("my-agent-id")
store.add_document(source_file, chunk_index, content, embedding)
results = store.search(query_embedding, top_k=5)

# Global store for shared knowledge
global_store = get_global_store()
```

### Cleanup

When an agent is deleted, clean up its store:

```bash
python3 ~/.claude/mcp-servers/rag-server/agent_storage.py delete <agent_id>
```

### Status

```bash
python3 ~/.claude/mcp-servers/rag-server/agent_storage.py
```
