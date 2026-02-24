# PRD: RAG-001 - Staged Pre-Filtering Optimization

> **STATUS: SCOPE REDUCED** - Hybrid search already exists (see GAP_ANALYSIS.md)

## Overview

### What Already Exists (from RAG_GUIDE.md)

```
✅ Hybrid Search: 70% Vector + 30% BM25 with RRF fusion
✅ BM25 Index: Already built during indexing
✅ Configurable weights via config
✅ Query classification for routing
```

### Problem Statement (Revised)
The **current hybrid search queries BOTH indexes simultaneously**, then fuses results:

**Current flow:**
```
Query → Vector(ALL chunks) + BM25(ALL chunks) → RRF Fusion → Top-k
```

This is still slower than necessary for large indexes because both searches scan all chunks.

### Proposed Solution (Reduced Scope)
Add **staged pre-filtering**: BM25 narrows candidates FIRST, then vector search runs only on the reduced set.

**Optimized flow:**
```
Query → BM25(ALL) → Top-100 IDs → Vector(100 only) → Hybrid score → Top-k
                    ↑
            The staged approach is 8x faster for large indexes
```

**Target:** 200ms → 25ms (8x improvement on large indexes)

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| P50 query latency | <30ms | Benchmark suite |
| P95 query latency | <100ms | Benchmark suite |
| Recall degradation | <5% | Compare results vs. current hybrid |
| Memory overhead | <50MB | Profile staged index |

---

## Requirements

### Functional Requirements

**FR-1: Staged Pre-Filter Mode** (NEW)
- Add `staged: true` option to rag_search
- When enabled: BM25 first → get top-100 IDs → vector search with ID filter
- Reuses existing BM25 index (no new index needed)

**FR-2: Hybrid Scoring** (ALREADY EXISTS - no change)
- ✅ Final score = 0.7 × vector + 0.3 × BM25 (already implemented)
- ✅ Weights configurable (already implemented)

**FR-3: Fallback Behavior** (ENHANCE)
- If BM25 returns <20 results, fall back to parallel hybrid
- Log fallback occurrences for monitoring

**FR-4: Index Synchronization** (ALREADY EXISTS - no change)
- ✅ BM25 index updates on `rag_index` calls
- ✅ `rag_reindex` rebuilds both indexes

### Non-Functional Requirements

**NFR-1: Performance**
- Staged query time: <50ms P95 (vs current ~200ms)
- BM25 pre-filter: <10ms

**NFR-2: Backward Compatibility**
- Staged mode is OPT-IN (existing behavior unchanged)
- Enable via `staged=True` parameter or config

### Out of Scope

- Changing existing hybrid search logic
- Query expansion (future enhancement)
- Real-time index updates

---

## Technical Design

### Architecture (Modification to Existing)

```
┌─────────────────────────────────────────────────────────────┐
│           rag_search(query, staged=True)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: BM25 Pre-Filter (uses EXISTING BM25 index)        │
│  - Tokenize query (existing code)                           │
│  - Score against BM25 index (existing)                      │
│  - Return top-100 chunk IDs + BM25 scores                   │
│  - Time budget: <10ms                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Filtered Vector Search (NEW logic)                │
│  - Embed query (existing Ollama call)                       │
│  - Search LanceDB WITH chunk ID filter ← KEY CHANGE         │
│  - Compute hybrid score (existing RRF)                      │
│  - Return top-k results                                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Storage (NO NEW FILES - all exist):**
```
.rag/
├── vectors.lance/       # ✅ EXISTING
├── bm25_index.pkl       # ✅ EXISTING (already built)
└── config.json          # Add staged_filtering section
```

**Config Addition (to existing config.json):**
```json
{
  "hybrid_search": {
    "enabled": true,
    "vector_weight": 0.7,
    "bm25_weight": 0.3
  },
  "staged_filtering": {
    "enabled": false,
    "bm25_candidates": 100,
    "fallback_threshold": 20
  }
}
```

### API/Interface Changes

**Modified:** `rag_search()` - add `staged` parameter

```python
def rag_search(
    query: str,
    project_path: str,
    top_k: int = 5,
    staged: bool = False,  # NEW PARAMETER
    **kwargs
):
    config = load_config(project_path)

    if staged or config.staged_filtering.enabled:
        # NEW: Staged mode - BM25 pre-filters candidates
        bm25_results = bm25_search(query, k=config.bm25_candidates)

        if len(bm25_results) < config.fallback_threshold:
            # Fallback to existing parallel hybrid
            return existing_hybrid_search(query, top_k)

        candidate_ids = [r.chunk_id for r in bm25_results]
        bm25_scores = {r.chunk_id: r.score for r in bm25_results}

        # Vector search WITH filter (the key optimization)
        vector_results = vector_search(
            query,
            filter_ids=candidate_ids,  # ← Only search these 100
            k=top_k
        )

        # Apply existing RRF fusion
        return rrf_fusion(vector_results, bm25_scores)
    else:
        # Existing parallel hybrid (unchanged)
        return existing_hybrid_search(query, top_k)
```

### Dependencies

- ✅ `rank_bm25` - Already installed (used by existing BM25)
- ✅ LanceDB - Already installed
- ✅ Ollama - Already installed
- **NO NEW DEPENDENCIES**

---

## Implementation Plan

### Phase 1 (MVP) - 2-3 hours (REDUCED from 4-6h)

**Goal:** Add staged mode to existing hybrid search

1. **Add Filter to Vector Search** (1.5h)
   - Modify LanceDB query to accept chunk ID filter
   - Pass BM25 candidate IDs as filter
   - This is the KEY change

2. **Add `staged` Parameter** (0.5h)
   - Add parameter to rag_search
   - Add config option
   - Wire up to existing BM25 search

3. **Testing** (1h)
   - Benchmark latency improvement
   - Verify recall quality matches existing hybrid

### Phase 2 (Enhancement) - 1-2 hours (REDUCED from 2-3h)

**Goal:** Tuning and observability

1. **Fallback Logic** (0.5h)
   - Detect sparse BM25 results
   - Fall back to parallel hybrid

2. **Monitoring** (0.5h)
   - Log staged vs parallel mode
   - Track fallback rate

3. **Auto-Enable Heuristic** (0.5h)
   - Auto-enable staged mode for indexes >5000 chunks
   - Below threshold, parallel is fine

### Future Considerations

- Query expansion (synonyms, related terms)
- Dynamic candidate count based on query complexity
- Per-project optimal thresholds

---

## Verification Criteria

### Unit Tests

- `test_bm25_index_creation()` - Index builds correctly
- `test_staged_search_returns_results()` - Two-stage flow works
- `test_hybrid_scoring()` - Scores calculated correctly
- `test_fallback_on_sparse_results()` - Fallback triggers appropriately

### Integration Tests

**Scenario 1: Large Corpus**
1. Index 10,000 documents
2. Run 100 queries
3. Verify P95 latency <100ms

**Scenario 2: Recall Quality**
1. Run queries with staged filtering
2. Run same queries with vector-only
3. Compare result overlap (should be >95%)

### UAT Scenarios

**UAT-1: Developer Search**
- User searches "authentication pattern"
- Results return in <50ms
- Relevant docs about auth appear in top 5

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| BM25 misses relevant docs | High | Medium | Generous candidate count (100); tunable threshold |
| Index sync issues | Medium | Low | Rebuild BM25 on every `rag_index` call |
| Memory overhead | Low | Medium | Profile and optimize; lazy loading |

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (MVP) | 2-3 hours | None (uses existing indexes) |
| Phase 2 (Enhancement) | 1-2 hours | Phase 1 complete |
| **Total** | **3-5 hours** | - |

**EFFORT REDUCTION:** 6-9h → 3-5h (savings: ~4 hours)

**Reason:** BM25 index and hybrid scoring already exist. Only need to add:
1. Filter parameter to vector search
2. Staged mode logic
3. Config option

**Priority:** High impact, LOW effort (now a quick win!)
**Recommendation:** Implement immediately - low-hanging fruit for performance gain

---

*PRD Version: 2.0 (Revised after GAP_ANALYSIS.md)*
*Created: 2026-02-03*
*Revised: 2026-02-03*
*Author: Claude (Worker Agent)*
