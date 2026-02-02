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
async:
  mode: auto
  prefer_async:
    - batch indexing
    - large folders
  require_sync:
    - discovery phase
    - audit phase
user-invocable: true
---

# RAG Batch Index

Systematically index an entire project into RAG with intelligent folder discovery, automatic exclusions, async batch processing, and comprehensive audit.

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

Scan the project to identify indexable content:

```
1. List all top-level folders
2. Identify content folders vs infrastructure folders
3. Estimate file counts and sizes per folder
4. Present discovery summary to user
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

Default exclusions (applied automatically):

```
EXCLUDE_PATTERNS = [
    "node_modules/",
    ".rag/",
    ".venv/",
    "venv/",
    ".git/",
    "__pycache__/",
    "*.pyc",
    ".DS_Store",
    "*.lock",
    "package-lock.json",
    "yarn.lock"
]
```

Optional exclusions (ask user):
- `archive/` — Historical versions
- `conversation-history/` — Past Claude sessions
- `.agent-workspaces/` — CDP delegation workspaces

### Phase 3: Batch Indexing (Async)

Index folder-by-folder for visibility and resilience:

```
For each content folder:
    1. Start async index job: rag_index(path, async_mode=True)
    2. Record job_id
    3. Monitor progress with rag_job_status(job_id)
    4. Wait for completion before next folder
    5. Log results: files indexed, chunks created, duration
```

**Key learnings:**
- Use `async_mode=True` for folders with >10 files
- PreCompact session files are slow (~2-4 min each) — warn user
- Large conversation history folders take 20-30+ minutes
- Monitor job status every 30-60 seconds

### Phase 4: Progress Tracking

Track and report progress throughout:

```markdown
## Indexing Progress

| Folder | Files | Chunks | Duration | Status |
|--------|-------|--------|----------|--------|
| 01-CLIENT-INPUTS | 61 | 3,245 | 8m 23s | ✅ |
| 02-KNOWLEDGE-BASE | 24 | 1,102 | 2m 15s | ✅ |
| 03-SOLUTION-DESIGN | 54 | 2,891 | 5m 47s | ⏳ |
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

**Total indexed:** 481 files → 30,457 chunks

### By Folder
| Folder | Total | Indexed | Missing | Notes |
|--------|-------|---------|---------|-------|
| 01-CLIENT-INPUTS | 61 | 57 | 4 | 3 PDFs, 1 transcript |

### Missing Files (Unexpected)
- path/to/file.md — Reason unknown, try manual index

### Missing Files (Expected)
- Binary files: 23 (PNG, XLSX, DOCX)
- Too small: 15 (< 1KB)
- Excluded: 4,467 (.rag/, node_modules/)
```

## Important Technical Notes

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
2. Check `rag_lock_status` for stale locks
3. Resume from failed folder (already-indexed files are idempotent)

## Example Session

```
User: batch index this project

Claude: Let me discover indexable folders in your project.

## Discovery Results

| Folder | Files | Est. Size | Recommend |
|--------|-------|-----------|-----------|
| 01-CLIENT-INPUTS | 61 | 12MB | ✅ Index |
| 02-KNOWLEDGE-BASE | 24 | 2MB | ✅ Index |
| 03-SOLUTION-DESIGN | 54 | 8MB | ✅ Index |
| node_modules | 236 dirs | 180MB | ❌ Skip |
| .rag | 4,467 | 2GB | ❌ Skip |

Should I proceed with indexing the recommended folders?

User: yes

Claude: Starting batch indexing...

[Phase 3-4: Index each folder, track progress]

## Indexing Complete

**Total:** 139 files → 7,238 chunks in 16m 25s

Running post-index audit...

## Audit Results

✅ All important files indexed
⚠️ 4 files skipped (3 PDFs, 1 binary)
```

## MCP Tools Used

- `mcp__rag-server__rag_status` — Check RAG is initialized
- `mcp__rag-server__rag_index` — Index files/folders (with async_mode)
- `mcp__rag-server__rag_job_status` — Monitor async jobs
- `mcp__rag-server__rag_list` — List all indexed documents
- `mcp__rag-server__rag_lock_status` — Check for stale locks

## Related Skills

- `rag-init` — Initialize RAG for a project
- `rag-search` — Search the RAG database
- `rag-status` — Check RAG health and stats
