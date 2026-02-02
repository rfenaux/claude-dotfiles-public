# PRD: rag-integration-expert

## Overview

**Agent Name:** `rag-integration-expert`
**Purpose:** Technical expert for RAG (Retrieval-Augmented Generation) system integration
**Model:** Sonnet (complex configuration + reasoning)

## Problem Statement

Users need guidance on leveraging RAG for semantic search:
- RAG initialization and configuration
- Document indexing strategies
- Effective query patterns
- Hierarchy-aware search
- Ollama embeddings setup

## Key Capabilities

### 1. RAG System Setup
- Initialize .rag/ directory structure
- Configure Ollama embeddings (mxbai-embed-large)
- Set up LanceDB storage
- Configure indexing options

### 2. Document Indexing
- Index files and folders (sync and async)
- Handle different file types (PDF, DOCX, MD, code)
- Manage re-indexing and updates
- Monitor indexing progress

### 3. Search Optimization
- Design effective semantic queries
- Use category filters (decision, requirement, technical)
- Apply relevance levels (critical, high, medium, low)
- Leverage hierarchy-aware search (client/project/milestone)

### 4. RAG Administration
- List indexed documents
- Remove stale documents
- Monitor RAG status
- Troubleshoot indexing issues

## Tools Required

- mcp__rag-server__rag_init
- mcp__rag-server__rag_index
- mcp__rag-server__rag_search
- mcp__rag-server__rag_list
- mcp__rag-server__rag_status
- mcp__rag-server__rag_remove
- mcp__rag-server__rag_reindex
- Bash (Ollama management)

## RAG Directory Structure

```
project/.rag/
├── config.json         # RAG configuration
├── lancedb/            # Vector database
│   └── chunks.lance/   # Chunk storage
└── metadata/           # Document metadata
```

## RAG Search Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| query | Natural language search | "how does auth work" |
| top_k | Number of results | 20 (default) |
| category | Filter by type | "decision", "requirement" |
| min_relevance | Minimum relevance | "high", "critical" |
| client | Client filter | "rescue" |
| scope | Hierarchy scope | "rescue/erp-integration" |
| phase | Project phase | "discovery", "implementation" |

## Category Types

- **decision**: Architecture and design decisions
- **requirement**: Business and technical requirements
- **business_strategy**: Strategic content
- **business_process**: Process documentation
- **technical**: Technical specifications
- **constraint**: Limitations and boundaries
- **risk**: Risk-related content
- **action_item**: Tasks and actions
- **context**: Background information

## Common Commands

```bash
# Initialize RAG
rag init

# Index a folder
rag index ./docs

# Search
rag search "authentication flow"

# Status
rag status

# List indexed files
rag list
```

## Trigger Patterns

- "set up RAG for this project"
- "index these documents"
- "search the knowledge base"
- "RAG configuration help"
- "fix RAG indexing issues"

## Best Practices

1. **Index early**: Set up RAG at project start
2. **Categorize content**: Use metadata for filtering
3. **Prefer recent**: Trust most recent content_date
4. **Hierarchy scoping**: Use client/project/milestone for precision
5. **Hybrid search**: Combine RAG with Grep for verification

## Integration Points

- Works with `rag-init`, `rag-search`, `rag-index` skills
- Coordinates with `file-indexing-expert`
- Uses Ollama for embeddings
- Stores in LanceDB

## Success Metrics

- RAG initialized and healthy
- Documents properly indexed
- Relevant search results
- Fast query responses
