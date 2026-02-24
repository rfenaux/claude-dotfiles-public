# PRD: RAG-002 - Metadata Index Enhancement

> **STATUS: SCOPE SIGNIFICANTLY REDUCED** - 2 of 3 indexes already exist (see GAP_ANALYSIS.md)

## Overview

### What Already Exists (from RAG_GUIDE.md)

```
✅ Vector Index: LanceDB (fully implemented)
✅ BM25 Index: Pickle file (fully implemented)
✅ Query Router: Classification exists (where_is, how_to, decision routing)
✅ Hybrid Search: 70% vector + 30% BM25 with RRF fusion
```

### What's Missing (Gap to Fill)

```
❓ SQLite Metadata Index: NEEDS VERIFICATION
   - Does .rag/metadata.db exist?
   - Are category, relevance, date fields indexed?
   - Can we filter by attributes before vector search?
```

### Revised Problem Statement
Query classification and hybrid search exist, but **fast attribute filtering** may be missing:
- Filter by category (decision, requirement, technical) before search
- Filter by date range
- Filter by relevance level (critical, high, medium, low)

### Proposed Solution (Reduced Scope)
1. **VERIFY** if SQLite metadata index exists
2. If NOT: Add SQLite metadata index
3. If YES: Enhance with additional indexed fields

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Metadata filter speed | <5ms | Benchmark filter queries |
| Index sync accuracy | 100% | Verify all indexes contain same docs |
| Storage overhead | <5MB | SQLite is tiny |

---

## Requirements

### Functional Requirements

**FR-1: Vector Index** (✅ ALREADY EXISTS)
- LanceDB vector store - fully implemented
- Semantic similarity search - working
- No changes needed

**FR-2: BM25 Keyword Index** (✅ ALREADY EXISTS)
- Pickle file at `.rag/bm25_index.pkl` - working
- Phrase queries - supported
- No changes needed

**FR-3: Metadata Index** (❓ NEEDS VERIFICATION / IMPLEMENTATION)
- Check if `.rag/metadata.db` exists
- If not: Create SQLite database
- Indexed fields: source_file, content_date, category, relevance, topics
- Support compound filters (category=decision AND relevance>=high)

**FR-4: Query Router** (✅ ALREADY EXISTS - ENHANCE)
- Query classification exists (where_is, how_to, decision)
- ADD: Route filter-heavy queries through metadata first

**FR-5: Index Synchronization** (ENHANCE)
- ✅ Vector + BM25 already sync
- ADD: SQLite metadata sync on `rag_index`

### Non-Functional Requirements

**NFR-1: Storage Efficiency**
- Metadata index: <5MB (SQLite is tiny)

**NFR-2: Query Performance**
- Metadata filter: <5ms
- Combined metadata + vector: <60ms

**NFR-3: Backward Compatibility**
- Existing API unchanged
- Metadata filters via new optional parameters

### Out of Scope

- Changing existing vector/BM25 logic
- Distributed indexes
- Custom metadata schemas

---

## Technical Design

### Architecture (Minimal Addition)

```
┌─────────────────────────────────────────────────────────────┐
│               rag_search(query, category=..., ...)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Query Router (✅ EXISTS - add metadata pre-filter)         │
│  - Analyze query type                                       │
│  - If filters present → metadata first                      │
│  - Select index strategy                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Vector    │  │    BM25     │  │  Metadata   │
│  ✅ EXISTS  │  │  ✅ EXISTS  │  │  ❓ ADD IF  │
│ (LanceDB)   │  │  (.pkl)     │  │   MISSING   │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Data Model

**Storage Structure:**
```
.rag/
├── vectors.lance/       # ✅ EXISTS
├── bm25_index.pkl       # ✅ EXISTS
├── metadata.db          # ❓ ADD IF MISSING
└── config.json          # ✅ EXISTS (add metadata config)
```

**Metadata Schema (SQLite) - ADD IF MISSING:**
```sql
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    content_date DATE,
    category TEXT,
    relevance TEXT,
    topics TEXT,  -- JSON array
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source ON chunks(source_file);
CREATE INDEX idx_category ON chunks(category);
CREATE INDEX idx_relevance ON chunks(relevance);
CREATE INDEX idx_date ON chunks(content_date);
```

### API/Interface Changes

**Enhanced `rag_search()` (existing API - add parameters):**
```python
def rag_search(
    query: str,
    project_path: str,
    top_k: int = 5,
    # These may already exist - verify first:
    category: str = None,
    min_relevance: str = None,
    # Add if missing:
    date_after: str = None,
    date_before: str = None,
    **kwargs
):
    """
    Filter parameters narrow results BEFORE vector search.
    """
    if any([category, min_relevance, date_after, date_before]):
        # Pre-filter via SQLite
        candidate_ids = metadata_filter(...)
        # Then vector search on candidates only
        return vector_search(query, filter_ids=candidate_ids, k=top_k)
    else:
        # Existing hybrid search
        return existing_hybrid_search(query, top_k)
```

### Dependencies

- `sqlite3` - Python stdlib (no install needed)
- ✅ All other dependencies already installed

---

## Implementation Plan

### Phase 0 (Investigation) - 1 hour

**Goal:** Verify current state before building

1. **Check existing metadata storage** (30min)
   - Does `.rag/metadata.db` exist?
   - Is metadata stored in LanceDB columns?
   - What fields are currently captured?

2. **Review rag_search parameters** (30min)
   - Are category, min_relevance already supported?
   - How are they currently used?

### Phase 1 (MVP) - 3-4 hours (REDUCED from 8-10h)

**Goal:** Add SQLite metadata IF missing

1. **Metadata Index** (2h) - IF NEEDED
   - SQLite schema creation
   - Populate from existing chunks
   - Sync during `rag_index`

2. **Filter Parameters** (1h)
   - Add/verify filter parameters to rag_search
   - Wire up metadata pre-filtering

3. **Testing** (1h)
   - Verify filter queries work
   - Benchmark filter speed (<5ms)

### Phase 2 (Enhancement) - 2 hours (REDUCED from 4-6h)

**Goal:** Enhanced filtering

1. **Compound Filters** (1h)
   - Multiple filter combination
   - Date range queries

2. **Index Statistics** (1h)
   - Add metadata to rag_status output
   - Track category distribution

### Future Considerations

- Custom metadata schemas per project
- Full-text search within SQLite for specific fields

---

## Verification Criteria

### Unit Tests

- `test_metadata_index_creation()` - SQLite schema correct
- `test_triple_index_sync()` - All indexes have same docs
- `test_query_router_classification()` - Correct mode selection
- `test_result_merger_scoring()` - Combined scores accurate

### Integration Tests

**Scenario 1: Filter + Vector**
1. Index 1000 docs with categories
2. Search with category filter
3. Verify filter applies before vector search

**Scenario 2: BM25 Exact Match**
1. Index docs with unique phrases
2. Search with quoted phrase
3. Verify exact match returned first

### UAT Scenarios

**UAT-1: Category Filtering**
- User: `rag_search("auth", category="decision")`
- Returns only decision documents about auth

**UAT-2: Date Range Query**
- User: `rag_search("budget", date_range=("2026-01-01", "2026-01-31"))`
- Returns only January 2026 documents

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Index desync | High | Medium | Atomic updates; manifest tracking; sync validation |
| Storage bloat | Medium | Medium | Monitor sizes; optional index compression |
| Query routing errors | Medium | Low | Conservative defaults; logging for debugging |

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0 (Investigation) | 1 hour | None |
| Phase 1 (MVP) | 3-4 hours | Phase 0 findings |
| Phase 2 (Enhancement) | 2 hours | Phase 1 complete |
| **Total** | **6-7 hours** | - |

**EFFORT REDUCTION:** 12-16h → 6-7h (savings: ~8 hours)

**Reason:** Vector + BM25 indexes already exist. Only need:
1. Verify/add SQLite metadata index
2. Wire up filter parameters

**Priority:** Medium impact, LOW effort
**Recommendation:** Quick investigation first to confirm scope

---

*PRD Version: 2.0 (Revised after GAP_ANALYSIS.md)*
*Created: 2026-02-03*
*Revised: 2026-02-03*
*Author: Claude (Worker Agent)*
