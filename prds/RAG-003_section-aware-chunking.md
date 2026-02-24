# PRD: RAG-003 - Section-Aware Chunking

## Overview

### Problem Statement
Current RAG chunking uses fixed-size windows (e.g., 500 tokens), which breaks document structure:
- Headings separated from their content
- Code blocks split mid-function
- Tables broken across chunks
- Context lost between related paragraphs

This degrades retrieval quality because:
1. Chunks lack semantic coherence
2. Section hierarchy not preserved in metadata
3. Can't retrieve "parent" context for a matched chunk

### Proposed Solution
Parse document structure (headings, sections, code blocks), chunk by semantic boundaries, and preserve hierarchy in metadata.

**Key features:**
- Respect markdown/HTML structure
- Keep code blocks intact
- Store section path (e.g., "Intro > Problem Statement")
- Enable parent-child chunk relationships

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Chunk coherence | >90% readable standalone | Human evaluation sample |
| Retrieval relevance | +15% MRR improvement | Compare to fixed-size baseline |
| Section path accuracy | 100% correct hierarchy | Automated validation |
| Code block integrity | 0% split blocks | Automated check |

---

## Requirements

### Functional Requirements

**FR-1: Structure-Aware Parsing**
- Parse markdown headings (H1-H6)
- Detect code blocks (fenced and indented)
- Identify tables, lists, blockquotes
- Support HTML structure if present

**FR-2: Semantic Boundary Chunking**
- Chunk at heading boundaries (configurable levels)
- Never split code blocks
- Keep tables intact
- Merge small sections into parent

**FR-3: Hierarchy Preservation**
- Store section path in chunk metadata
- Format: `["Document Title", "H1: Overview", "H2: Problem Statement"]`
- Enable "give me the parent section" queries

**FR-4: Parent-Child Relationships**
- Link chunks to their parent section chunk
- Support "expand context" retrieval
- Return sibling chunks when relevant

**FR-5: Size Constraints**
- Max chunk size: 1000 tokens (configurable)
- If section exceeds max, split at paragraph boundaries
- Min chunk size: 100 tokens (merge small sections)

### Non-Functional Requirements

**NFR-1: Performance**
- Parsing overhead: <100ms per document
- No increase in query latency

**NFR-2: Backward Compatibility**
- Works with existing vector index
- Metadata extensions don't break old searches

**NFR-3: Format Support**
- Markdown (primary)
- HTML (secondary)
- Plain text (fallback to fixed-size)

### Out of Scope

- PDF structure extraction (separate enhancement)
- DOCX native parsing (use existing python-docx → markdown)
- Recursive section expansion in queries (future)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Input                           │
│  (Markdown, HTML, or plain text)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Structure Parser                              │
│  - Extract heading hierarchy                                │
│  - Identify semantic blocks (code, tables, lists)           │
│  - Build document tree                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│             Section-Aware Chunker                           │
│  - Walk document tree                                       │
│  - Create chunks at semantic boundaries                     │
│  - Merge small sections                                     │
│  - Split large sections at paragraphs                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Metadata Enrichment                            │
│  - Add section_path to each chunk                           │
│  - Link parent_chunk_id                                     │
│  - Store sibling_chunk_ids                                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

**Chunk Schema Extension:**
```python
@dataclass
class EnrichedChunk:
    chunk_id: str
    content: str
    source_file: str

    # New fields for section awareness
    section_path: List[str]           # ["Doc", "Overview", "Problem"]
    section_level: int                # 0=root, 1=H1, 2=H2, etc.
    parent_chunk_id: Optional[str]    # Link to parent section
    sibling_chunk_ids: List[str]      # Adjacent sections at same level

    # Content type markers
    content_type: str                 # "prose" | "code" | "table" | "list"
    is_complete_section: bool         # True if chunk = entire section

    # Existing fields
    content_date: Optional[date]
    category: Optional[str]
    relevance: Optional[str]
```

**Document Tree (Intermediate):**
```python
@dataclass
class DocumentNode:
    heading: Optional[str]
    level: int                        # 0=root, 1-6=H1-H6
    content: str                      # Text content of this section
    children: List['DocumentNode']    # Subsections
    content_type: str                 # prose | code | table | list
```

### API/Interface Changes

**Enhanced `rag_index()`:**
```python
def rag_index(
    path: str,
    project_path: str,
    # New parameter
    chunking_strategy: str = "auto"  # auto | section | fixed
):
    """
    Chunking strategies:
    - auto: Section-aware for markdown/HTML, fixed for plain text
    - section: Force section-aware chunking
    - fixed: Legacy fixed-size chunking
    """
```

**Enhanced `rag_search()` (future):**
```python
def rag_search(
    query: str,
    project_path: str,
    # New parameters
    expand_context: bool = False,    # Include parent/sibling chunks
    section_filter: str = None,      # Filter by section path pattern
):
    """
    Context expansion returns parent and sibling chunks
    for better understanding of matched content.
    """
```

### Dependencies

- `markdown-it-py` - Markdown parsing with AST
- `beautifulsoup4` - HTML structure extraction
- Existing: LanceDB, Ollama

---

## Implementation Plan

### Phase 1 (MVP) - 6-8 hours

**Goal:** Section-aware chunking for markdown

1. **Markdown Parser** (2h)
   - Extract heading hierarchy
   - Build document tree
   - Identify code blocks and tables

2. **Section Chunker** (3h)
   - Walk tree and create chunks
   - Respect size constraints
   - Handle edge cases (empty sections, deep nesting)

3. **Metadata Storage** (2h)
   - Extend chunk schema
   - Store section_path and relationships

4. **Testing** (2h)
   - Test with real CLAUDE.md files
   - Verify code blocks stay intact

### Phase 2 (Enhancement) - 4-6 hours

**Goal:** Context expansion and HTML support

1. **Parent-Child Linking** (2h)
   - Store relationship IDs
   - Query for context expansion

2. **HTML Parser** (2h)
   - Extract structure from HTML
   - Map to same document tree format

3. **Context Expansion Search** (2h)
   - `expand_context` parameter
   - Return parent + siblings with result

### Future Considerations

- PDF structure extraction (requires specialized parser)
- Learning optimal section boundaries from user feedback
- Cross-document section linking (related sections across files)

---

## Verification Criteria

### Unit Tests

- `test_markdown_heading_extraction()` - Correct hierarchy
- `test_code_block_integrity()` - Never split code
- `test_table_integrity()` - Tables stay whole
- `test_section_path_accuracy()` - Correct paths
- `test_large_section_splitting()` - Splits at paragraphs
- `test_small_section_merging()` - Merges correctly

### Integration Tests

**Scenario 1: CLAUDE.md Indexing**
1. Index `~/.claude/CLAUDE.md`
2. Verify chunks align with sections
3. Check section_path metadata

**Scenario 2: Code-Heavy Document**
1. Index file with many code blocks
2. Verify 0 code blocks split
3. Each code chunk has correct section_path

### UAT Scenarios

**UAT-1: Section Search**
- User searches "Critical Rules"
- Gets chunk with full Critical Rules section
- section_path shows ["CLAUDE.md", "Critical Rules"]

**UAT-2: Context Expansion**
- User searches for specific function
- Finds code block
- Expands to see surrounding documentation

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Parser errors on malformed markdown | Medium | Medium | Fallback to fixed-size; log warnings |
| Very large sections exceed limits | Low | Medium | Intelligent paragraph splitting |
| Performance regression | Medium | Low | Benchmark during development |

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 (MVP) | 6-8 hours | markdown-it-py package |
| Phase 2 (Enhancement) | 4-6 hours | Phase 1 complete |
| **Total** | **10-14 hours** | - |

**Priority:** Medium impact, Medium effort
**Recommendation:** Implement after RAG-001 and RAG-002; enhances retrieval quality

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
