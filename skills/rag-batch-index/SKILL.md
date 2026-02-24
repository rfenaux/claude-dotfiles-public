---
name: rag-batch-index
description: Batch index a project into RAG with smart folder discovery, exclusions, progress tracking, and post-index audit.
trigger: /rag-batch-index
context: fork
agent: general-purpose
model: haiku
tools:
  - Read
  - Bash
  - Glob
user-invocable: true
---

# RAG Batch Index

Systematically index an entire project into RAG with intelligent folder discovery, automatic exclusions, crash-resilient incremental indexing, and comprehensive audit.

## Trigger Phrases

- "batch index this project"
- "index everything into RAG"
- "rag batch index"
- "full RAG indexing"
- "index project to RAG"

## Prerequisites

- RAG must be initialized (`rag init` or check `.rag/` exists)
- Ollama running with `mxbai-embed-large` model
- Sufficient disk space for vector database

## Workflow

### Phase 1: Discovery (Sync)

**Pre-flight check** (run before anything else):
```bash
curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; assert any('mxbai-embed-large' in m for m in models), 'Model not found'" 2>&1 || { echo "FAIL: Ollama not running or mxbai-embed-large not available. Run: ollama pull mxbai-embed-large"; exit 1; }
```
If pre-flight fails, stop and inform user. Do not proceed with indexing.

Scan the project to identify indexable content:

```
1. Verify Ollama + mxbai-embed-large (pre-flight above)
2. List all top-level folders
3. Identify content folders vs infrastructure folders
4. Estimate file counts and sizes per folder
5. Present discovery summary to user
```

**Content folders** (typically index these):
- Client inputs, transcripts, documents
- Knowledge base, decisions, specs
- Solution design, deliverables
- Working drafts

**Infrastructure folders** (skip by default):
- `node_modules/` — Dependencies (thousands of files)
- `.rag/` — RAG database itself
- `.venv/`, `venv/` — Python virtual environments
- `.git/` — Git internals
- `archive/` — Old versions (optional)
- `.agent-workspaces/` — CDP workspaces
- `.claude/` — Claude config (unless specifically needed)

### Phase 2: Exclusion Patterns

Load exclusions from SSOT: `~/.claude/config/rag-exclusions.json`

- Apply `auto_exclude` patterns automatically (directories + file patterns)
- For `ask_user` patterns, present to user for confirmation before excluding
- Check `warnings.slow_patterns` and inform user about expected timing
- Files exceeding `warnings.size_threshold_kb` (100KB) get a speed warning

### Phase 3: Batch Indexing

Index folder-by-folder for visibility and resilience:

```
For each content folder:
    1. Call rag_index(path=folder, project_path=project_root)
    2. Log results: files indexed, files skipped (unchanged), chunks created
    3. Move to next folder
```

**Crash resilience:**
- Indexing is incremental — unchanged files are skipped via content hashing
- Hash index is checkpointed every 10 files during indexing
- Safe to interrupt (Ctrl+C, power loss) — re-run picks up where it stopped
- At most 10 files of work lost on crash (the last uncheckpointed batch)

**Key learnings:**
- PreCompact session files are slow (~2-4 min each) — warn user
- Large conversation history folders take 20-30+ minutes
- Files >100KB are proportionally slower (embedding bottleneck)

### Phase 4: Progress Tracking

Track and report progress throughout:

```markdown
## Indexing Progress

| Folder | Files | Skipped | Chunks | Status |
|--------|-------|---------|--------|--------|
| 01-CLIENT-INPUTS | 61 | 0 | 3,245 | Done |
| 02-KNOWLEDGE-BASE | 24 | 12 | 1,102 | Done |
| 03-SOLUTION-DESIGN | 54 | 0 | 2,891 | Indexing... |
| ... | ... | ... | ... | ... |
```

### Phase 5: Post-Index Audit (Sync)

After all folders indexed, verify completeness:

```
1. Get full RAG list: rag_list(project_path)
2. Get all project files: glob patterns for .md, .txt, .pdf, etc.
3. Compare: identify files NOT in RAG index
4. Categorize gaps:
   - Binary files (expected: PNG, XLSX, DOCX, ZIP)
   - Too small (<1KB creates 0 chunks)
   - JSON schemas (chunk poorly)
   - Excluded folders (expected)
   - True gaps (unexpected — flag for attention)
```

**Audit report format:**

```markdown
## RAG Index Audit

**Total indexed:** 481 files -> 30,457 chunks

### By Folder
| Folder | Total | Indexed | Skipped | Missing | Notes |
|--------|-------|---------|---------|---------|-------|
| 01-CLIENT-INPUTS | 61 | 57 | 0 | 4 | 3 PDFs, 1 binary |

### Missing Files (Unexpected)
- path/to/file.md — Reason unknown, try manual index

### Missing Files (Expected)
- Binary files: 23 (PNG, XLSX, DOCX)
- Too small: 15 (< 1KB)
- Excluded: 4,467 (.rag/, node_modules/)
```

## Important Technical Notes

### Crash Resilience
- `rag_index` saves file hashes every 10 files (atomic writes)
- Interrupted indexing resumes automatically — unchanged files skipped via hash
- `rag_reindex` is safe to interrupt — no destructive clear, per-file delete+insert
- Orphaned entries (deleted files) cleaned up automatically after reindex

### Incremental vs Full Reindex
- **`rag_index(path, project_path)`** — Incremental: skips unchanged files (use for updates)
- **`rag_index(path, project_path, force=True)`** — Force: re-processes all files (keeps existing DB)
- **`rag_reindex(project_path)`** — Full: clears hashes, re-indexes everything, cleans orphans

### MCP Tool Availability

**MCP RAG tools (`rag_index`, `rag_reindex`, etc.) are ONLY available in the main session** — never delegate RAG indexing to Task sub-agents. Sub-agents cannot access MCP tools.

If MCP tools are unavailable (connection failure, session issue), fall back to direct CLI:
```bash
cd <project> && python3 -m rag_mcp_server.cli index <path>
```

### Chunk Threshold
- RAG uses 1000-char chunks with 200-char overlap
- Files under ~1KB often create 0 chunks (below threshold)
- This is normal behavior, not an error

### File Types That Don't Index Well
- JSON schema files — Create few/no meaningful chunks
- Minified JS/CSS — No semantic value
- Binary files — Not supported (PDF requires special handling)

### Slow File Warning
Files matching these patterns are slow to embed:
- `*PreCompact*.md` — 2-4 minutes each
- Large session JSONL — 3-5 minutes each
- Files >100KB — Proportionally slower

Warn user before indexing folders containing these.

### Ollama Timeout Recovery
If Ollama times out during batch indexing:
1. Note which folder was in progress
2. Re-run the same `rag_index` call — it resumes from last checkpoint
3. Already-indexed files are skipped (hash match)

## Example Session

```
User: batch index this project

Claude: Let me discover indexable folders in your project.

## Discovery Results

| Folder | Files | Est. Size | Recommend |
|--------|-------|-----------|-----------|
| 01-CLIENT-INPUTS | 61 | 12MB | Index |
| 02-KNOWLEDGE-BASE | 24 | 2MB | Index |
| 03-SOLUTION-DESIGN | 54 | 8MB | Index |
| node_modules | 236 dirs | 180MB | Skip |
| .rag | 4,467 | 2GB | Skip |

Should I proceed with indexing the recommended folders?

User: yes

Claude: Starting batch indexing...

[Phase 3-4: Index each folder, track progress]

## Indexing Complete

**Total:** 139 files -> 7,238 chunks in 16m 25s
**Skipped:** 0 files (first run)

Running post-index audit...

## Audit Results

All important files indexed
4 files skipped (3 PDFs, 1 binary)
```

## MCP Tools Used

- `mcp__rag-server__rag_status` — Check RAG is initialized
- `mcp__rag-server__rag_index` — Index files/folders (incremental, crash-resilient)
- `mcp__rag-server__rag_reindex` — Full safe reindex (no destructive clear)
- `mcp__rag-server__rag_list` — List all indexed documents
- `mcp__rag-server__rag_remove` — Remove specific files from index

## Related Skills

- `rag-init` — Initialize RAG for a project
- `rag-search` — Search the RAG database
- `rag-status` — Check RAG health and stats
