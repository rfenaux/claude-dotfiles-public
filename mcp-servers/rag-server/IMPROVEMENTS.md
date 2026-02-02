# RAG System Improvements (December 2025)

This document describes the improvements made to the RAG system for better document management and retrieval, specifically optimized for **project management, specs, and document analysis** workflows (rather than code-focused use cases).

## Table of Contents

1. [Header-Aware Chunking](#1-header-aware-chunking)
2. [Document Summaries](#2-document-summaries)
3. [Dashboard Search UI](#3-dashboard-search-ui)
4. [Document Overview](#4-document-overview)
5. [Manual Project Management](#5-manual-project-management)
6. [Restart All Services](#6-restart-all-services)

---

## 1. Header-Aware Chunking

### What It Does

The new `HeaderChunker` splits documents by their section headers instead of arbitrary character counts. This keeps related content together and preserves document structure.

### Why It Matters for Specs & Docs

- **Requirements stay together**: A requirement section won't be split in the middle
- **Section context is preserved**: Each chunk knows its section path (e.g., "Requirements > Authentication > OAuth")
- **Better retrieval**: When you search for "authentication requirements", you get complete sections, not fragments

### How It Works

The chunker:
1. Detects headers (Markdown `#`, underline-style, or numbered like `1.2.3`)
2. Splits at header boundaries
3. Preserves section hierarchy (H1 > H2 > H3)
4. Uses larger chunks (2000 chars vs 1000) to keep sections complete
5. Falls back to paragraph splitting for very large sections

### File Types Using Header Chunking

- `.md`, `.markdown` (Markdown)
- `.txt` (Plain text)
- `.rst` (reStructuredText)

### Example

**Before (old TextChunker):**
```
Chunk 1: "## Authentication\n\nUsers must authenticate using OAuth 2.0..."
Chunk 2: "...token expires after 24 hours.\n\n## Authorization\n\nOnce authenticated..."
```

**After (HeaderChunker):**
```
Chunk 1: "## Authentication\n\nUsers must authenticate using OAuth 2.0... token expires after 24 hours."
[section_path: "Requirements > Authentication"]

Chunk 2: "## Authorization\n\nOnce authenticated..."
[section_path: "Requirements > Authorization"]
```

### Configuration

Defaults are optimized for specs, but you can customize:

```python
from rag_server.chunking import HeaderChunker

chunker = HeaderChunker(
    chunk_size=2000,      # Max chars per chunk (default: 2000)
    chunk_overlap=200,    # Overlap between chunks (default: 200)
    min_chunk_size=100,   # Skip tiny sections (default: 100)
)
```

---

## 2. Document Summaries

### What It Does

Automatically generates and stores summaries when documents are indexed. This enables "what documents do I have about X?" style queries.

### Why It Matters

Instead of searching through all chunks, you can:
- Quickly find which document covers a topic
- See document types (spec, meeting notes, API doc, etc.)
- Get an overview of topics covered in each doc

### How It Works

On indexing, for each document:
1. **Title extraction**: From first header or filename
2. **Topic extraction**: From all section headers
3. **Description**: From first meaningful paragraph
4. **Document type inference**: Based on keywords (spec, meeting, API, etc.)
5. **Summary embedding**: For semantic search on summaries

### What Gets Stored (Catalog Table)

| Field | Description |
|-------|-------------|
| `title` | Document title |
| `summary` | Combined title + topics + description |
| `topics` | List of main topics from headers |
| `doc_type` | Inferred type (functional_spec, meeting_notes, etc.) |
| `chunk_count` | Number of chunks in the document |

### Document Types Detected

| Type | Keywords/Patterns |
|------|-------------------|
| `functional_spec` | "functional", "requirement" |
| `technical_spec` | "technical", "architecture" |
| `meeting_notes` | "meeting", "attendees", "action items" |
| `documentation` | "guide", "tutorial", "how to" |
| `project_doc` | "project", "roadmap", "milestone" |
| `api_doc` | "api", "endpoint", "request" |

### Using Document Search

**In Claude Code:**
```
# Search document summaries (not chunks)
Use rag_search with search in documents to find which documents are about authentication
```

**Via Dashboard:**
1. Go to Search tab
2. Select "Documents" search type
3. Enter query like "authentication requirements"
4. Results show matching documents with summaries

**Via API:**
```bash
curl "http://localhost:8420/api/search?project=/path/to/project&q=authentication&type=documents"
```

---

## 3. Dashboard Search UI

### What It Does

Adds a full semantic search interface to the dashboard at http://localhost:8420.

### Features

- **Project selector**: Choose which project to search
- **Two search modes**:
  - **Content**: Find specific passages (chunk-level)
  - **Documents**: Find which docs cover a topic (document-level)
- **Configurable results**: 5, 10, or 20 results
- **Rich results display**: Shows source file, score, text preview, dates

### How to Use

1. Open http://localhost:8420
2. Click **Search** tab
3. Select a project
4. Enter your query (natural language works best)
5. Choose **Content** or **Documents** search
6. Click **Search** or press Enter

### Search Modes Explained

| Mode | Best For | Returns |
|------|----------|---------|
| **Content** | "Find the exact text about X" | Chunks with matched text |
| **Documents** | "Which docs talk about X?" | Document summaries |

### Example Queries

- "What are the authentication requirements?" → Content search
- "Which documents cover OAuth?" → Document search
- "Meeting notes about the API redesign" → Content search
- "All specs related to user management" → Document search

---

## 4. Document Overview

### What It Does

Shows all indexed documents for a project with their summaries, topics, and metadata.

### How to Access

1. Open http://localhost:8420
2. Go to **Search** tab
3. Select a project
4. Click **Load Documents**

### What You See

For each document:
- **Title**: Extracted from document
- **Type badge**: Color-coded document type
- **Chunk count**: How many searchable chunks
- **Topics**: Key topics from headers
- **Summary preview**: First ~200 chars of summary

### API Access

```bash
curl "http://localhost:8420/api/documents?project=/path/to/project"
```

Response:
```json
{
  "success": true,
  "documents": [
    {
      "source_file": "specs/auth.md",
      "title": "Authentication Specification",
      "doc_type": "functional_spec",
      "topics": ["OAuth 2.0", "JWT Tokens", "Session Management"],
      "summary": "Authentication Specification\nTopics: OAuth 2.0, JWT Tokens...",
      "chunk_count": 12
    }
  ]
}
```

---

## 5. Manual Project Management

### What It Does

Add any folder to the RAG dashboard, not just auto-detected projects.

### How to Use

**Add a Project:**
1. Open http://localhost:8420
2. Click **+ Add Project** button
3. Enter the full path (e.g., `/Users/you/Documents/my-project`)
4. Click **Add Project**

The system will:
- Validate the path exists
- Initialize RAG if not already set up (creates `.rag/` folder)
- Register in the dashboard

**Remove a Project:**
1. Find the project in the list
2. Click the **✕** button
3. Confirm removal

Note: Removing only hides from dashboard. The `.rag/` folder and index remain intact.

### API Access

```bash
# Add project
curl -X POST "http://localhost:8420/api/project/add" \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/you/Documents/my-project"}'

# Remove project
curl -X POST "http://localhost:8420/api/project/remove" \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/you/Documents/my-project"}'
```

---

## Re-indexing After Upgrade

To take advantage of the new chunking and summaries for existing projects:

```bash
# In Claude Code, navigate to your project then:
rag reindex
```

This will:
1. Clear the existing index
2. Re-index all files with the new HeaderChunker
3. Generate summaries for all documents
4. Update the catalog table

---

## Technical Details

### New Files Added

- `rag_server/summarizer.py`: Document summarization logic
- `rag_server/chunking.py`: Updated with `HeaderChunker` class

### Database Schema Changes

New **catalog** table added to LanceDB:

| Column | Type | Description |
|--------|------|-------------|
| source_file | string | Unique key (file path) |
| title | string | Extracted title |
| summary | string | Searchable summary text |
| vector | float32[] | Summary embedding |
| topics | string | JSON array of topics |
| doc_type | string | Inferred document type |
| chunk_count | int32 | Number of chunks |
| indexed_at | string | Timestamp |
| metadata | string | Additional metadata JSON |

### Dashboard API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | GET | Semantic search |
| `/api/documents` | GET | List indexed documents |
| `/api/project/add` | POST | Add a project |
| `/api/project/remove` | POST | Remove a project |

---

## Troubleshooting

### "No documents indexed yet"

Run `rag reindex` in your project to rebuild with new features.

### Search returns old-style results (no summaries)

The catalog needs to be populated. Run `rag reindex`.

### Dashboard not showing search tab

Restart the dashboard:
```bash
pkill -f "rag-dashboard/server.py"
launchctl load ~/Library/LaunchAgents/com.claude.rag-dashboard.plist
```

### Large documents taking too long

HeaderChunker processes larger chunks. For very large documents (>100 pages), consider splitting into multiple files.

---

## 6. Restart All Services

### What It Does

One-click restart of all RAG-related services from the dashboard.

### Services Restarted

| Service | Action |
|---------|--------|
| **Ollama** | Stops and restarts via `brew services` |
| **MCP Server** | Kills running processes; Claude Code auto-reconnects |
| **Dashboard** | Restarts via LaunchAgent; page auto-reloads |

### How to Use

1. Open http://localhost:8420
2. Click the red **⟳ Restart All** button in the header
3. Confirm the restart
4. Wait ~5 seconds for all services to restart
5. Page auto-reloads when ready

### When to Use

- After updating RAG server code (to reload MCP server)
- If Ollama stops responding
- If search results seem stale
- After system sleep/wake issues

### API Access

```bash
curl "http://localhost:8420/api/restart"
```

Response:
```json
{
  "success": true,
  "services": {
    "ollama": {"success": true, "message": "Restarted via brew services"},
    "mcp_server": {"success": true, "message": "Killed. Claude Code will reconnect."},
    "dashboard": {"success": true, "message": "Will restart via LaunchAgent in ~3 seconds"}
  },
  "message": "Restart initiated. Refresh the page in 5 seconds."
}
```
