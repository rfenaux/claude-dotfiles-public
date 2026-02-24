# PRD: RAG-004 - LLM Synthesis Pass (Two-Pass Summarization)

> **STATUS: SCOPE REDUCED** - Citation tracking already exists (see GAP_ANALYSIS.md)

## Overview

### What Already Exists (from RAG_GUIDE.md)

```
✅ Citation Tracking: source_file, start_line, end_line captured
✅ Confidence Scoring: Multi-factor formula implemented
✅ Contradiction Detection: Identifies conflicting information
✅ Cross-Reference Validation: Links related chunks
```

### What's Missing (Gap to Fill)

```
❌ LLM Synthesis Pass: Raw chunks returned, no narrative synthesis
❌ Inline Citation Format: No [1], [2], [3] format
❌ "Not found in sources" handling: No graceful degradation
```

### Revised Problem Statement
Citation infrastructure EXISTS but RAG returns raw chunks. Users must mentally combine fragments to form answers.

### Proposed Solution (Focused on Pass 2 Only)
Add LLM synthesis layer that:
1. Takes retrieved chunks (Pass 1 unchanged)
2. Synthesizes coherent answer with inline citations
3. Uses EXISTING citation tracking for source list

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Answer completeness | >85% satisfaction | User feedback |
| Citation accuracy | 100% verifiable | Leverages existing tracking |
| Response time | <3s for synthesis | Benchmark with LLM call |
| Hallucination rate | <5% uncited claims | Manual audit |

---

## Requirements

### Functional Requirements

**FR-1: Pass 1 - Chunk Retrieval** (✅ ALREADY EXISTS)
- Standard RAG retrieval - working
- Top-k chunks with metadata - working
- Citation tracking (source_file, lines) - working

**FR-2: Pass 2 - LLM Synthesis** (NEW - core of this PRD)
- Take retrieved chunks
- Format as numbered context for LLM
- Prompt: "Answer using ONLY these sources, cite [N]"
- Parse response for citations

**FR-3: Inline Citation Format** (NEW)
- Citations as bracketed numbers: [1], [2], [3]
- Source list uses EXISTING citation tracking
- Include file path and line numbers (already captured!)

**FR-4: Graceful Degradation** (NEW)
- If synthesis fails → return raw chunks
- If sources insufficient → "Not found in sources"
- Timeout handling for LLM call

**FR-5: Confidence Scoring** (✅ ALREADY EXISTS - REUSE)
- Existing confidence scoring → pass through to synthesized response
- Surface low-confidence warnings

### Non-Functional Requirements

**NFR-1: Performance**
- Pass 1: <500ms (existing, unchanged)
- Pass 2: <2500ms (LLM call)
- Total: <3s

**NFR-2: Token Efficiency**
- Synthesis prompt: <2000 tokens
- Response: <1000 tokens
- Use Haiku for synthesis (fast + cheap)

**NFR-3: Backward Compatibility**
- Synthesis is OPT-IN via parameter
- Existing behavior unchanged

### Out of Scope

- Changing Pass 1 retrieval logic
- Multi-turn conversational RAG
- Image/diagram synthesis

---

## Technical Design

### Architecture (Addition to Existing)

```
┌─────────────────────────────────────────────────────────────┐
│          rag_search(query, synthesize=True)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: Chunk Retrieval (✅ EXISTING - NO CHANGE)          │
│  - Standard rag_search logic                                │
│  - Returns chunks with citation tracking (existing)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Pass 2: LLM Synthesis (NEW - THIS PRD)                     │
│  - Format chunks as numbered context                        │
│  - Prompt Haiku: "Answer using ONLY these sources"          │
│  - Parse response for [N] citations                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Citation Enrichment (LEVERAGES EXISTING tracking)          │
│  - Map [N] to EXISTING source_file + line numbers           │
│  - Attach EXISTING confidence scores                        │
│  - Format source list                                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Synthesis Prompt Template:**
```python
SYNTHESIS_PROMPT = """
You are answering a question using ONLY the provided sources.
Every factual claim MUST have a citation in [N] format.

Question: {query}

Sources:
{formatted_sources}

Instructions:
1. Answer the question using ONLY information from the sources
2. Cite every fact with [1], [2], etc.
3. If sources don't contain the answer, say "Not found in sources"
4. Be concise but complete

Answer:
"""
```

**Formatted Sources:**
```
[1] Source: lessons/hubspot-api-patterns.md
Content: OAuth2 is the recommended authentication method for HubSpot APIs.
The refresh token should be stored securely and rotated periodically.

[2] Source: DECISIONS.md
Content: A-023: Chose Redis for session storage due to performance requirements
and built-in TTL support.

[3] Source: meetings/2026-01-15-architecture-review.txt
Content: Team agreed that user experience should not be compromised for
security theater. Balance is key.
```

**Response Schema:**
```python
@dataclass
class SynthesizedResponse:
    answer: str                       # Synthesized text with citations
    sources: List[CitedSource]        # Source details
    confidence: float                 # Overall confidence score
    uncited_claims: List[str]         # Statements without citations
    raw_chunks: List[Chunk]           # Original chunks (for fallback)

@dataclass
class CitedSource:
    citation_number: int              # [1], [2], etc.
    source_file: str
    line_range: Optional[str]         # "lines 45-52"
    relevance_score: float
    content_preview: str              # First 100 chars
```

### API/Interface Changes

**New function:**
```python
def rag_search_with_synthesis(
    query: str,
    project_path: str,
    top_k: int = 10,
    synthesize: bool = True,
    synthesis_model: str = "claude-sonnet",
    max_synthesis_tokens: int = 1000,
) -> SynthesizedResponse:
    """
    Two-pass RAG with LLM synthesis and citations.

    If synthesize=False, returns raw chunks (backward compatible).
    """
```

**Enhanced existing function (optional):**
```python
def rag_search(
    query: str,
    project_path: str,
    top_k: int = 5,
    synthesize: bool = False,  # New parameter, default off
    **kwargs
) -> Union[List[Chunk], SynthesizedResponse]:
    """
    Optionally enable synthesis via parameter.
    """
```

### Dependencies

- Anthropic API or Ollama for synthesis LLM
- Existing: RAG retrieval infrastructure

---

## Implementation Plan

### Phase 1 (MVP) - 4-5 hours (REDUCED from 8-10h)

**Goal:** Basic synthesis with inline citations

1. **Synthesis Pipeline** (2h)
   - Build prompt from retrieved chunks
   - Call Haiku for synthesis
   - Parse response for [N] citations

2. **Citation Mapping** (1h)
   - Regex extraction of [N] patterns
   - Map to EXISTING source_file + line numbers
   - Format source list (data already available!)

3. **API Integration** (1h)
   - Add `synthesize=True` parameter to rag_search
   - Return SynthesizedResponse dataclass

4. **Testing** (1h)
   - Test citation accuracy
   - Benchmark latency (<3s)

### Phase 2 (Enhancement) - 2-3 hours (REDUCED from 4-6h)

**Goal:** Polish and edge cases

1. **Confidence Pass-Through** (1h)
   - Attach EXISTING confidence scores to response
   - Surface low-confidence warnings

2. **Graceful Degradation** (1h)
   - Handle synthesis failures → return raw chunks
   - Handle insufficient sources → "Not found" message

3. **Caching** (1h)
   - Cache synthesis for repeated queries
   - TTL-based invalidation

### Future Considerations

- Multi-turn RAG (follow-up questions)
- Custom synthesis prompts per project
- Streaming synthesis for long answers

---

## Verification Criteria

### Unit Tests

- `test_citation_extraction()` - Correctly parses [N] patterns
- `test_source_mapping()` - Citations map to correct chunks
- `test_synthesis_prompt_formatting()` - Prompt built correctly
- `test_confidence_calculation()` - Scores computed accurately

### Integration Tests

**Scenario 1: Complete Synthesis**
1. Query: "How does authentication work?"
2. Verify answer has inline citations
3. Verify all citations are valid sources
4. Verify source list is complete

**Scenario 2: Insufficient Sources**
1. Query about topic not in knowledge base
2. Verify response says "Not found in sources"
3. No hallucinated citations

### UAT Scenarios

**UAT-1: Developer Question**
- User asks "What's the logging pattern?"
- Gets synthesized answer with citations
- Can click citations to verify sources

**UAT-2: Decision Lookup**
- User asks "Why did we choose Redis?"
- Gets answer citing specific DECISIONS.md entry
- Citation includes decision ID (A-023)

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM hallucinates citations | High | Medium | Strict prompting; verification step |
| Synthesis latency too high | Medium | Medium | Async option; caching |
| Citation format varies | Low | Medium | Robust regex; normalization |
| Model costs increase | Medium | High | Use efficient model; cache results |

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (MVP) | 4-5 hours | Anthropic API access |
| Phase 2 (Enhancement) | 2-3 hours | Phase 1 complete |
| **Total** | **6-8 hours** | - |

**EFFORT REDUCTION:** 12-16h → 6-8h (savings: ~8 hours)

**Reason:** Citation tracking infrastructure already exists:
- source_file, start_line, end_line already captured
- Confidence scoring already implemented
- Only need to add LLM synthesis layer

**Priority:** High impact, MEDIUM effort (UX game-changer)
**Recommendation:** Implement after RAG-001; transforms RAG from chunk-dumper to answer-provider

---

*PRD Version: 2.0 (Revised after GAP_ANALYSIS.md)*
*Created: 2026-02-03*
*Revised: 2026-02-03*
*Author: Claude (Worker Agent)*
