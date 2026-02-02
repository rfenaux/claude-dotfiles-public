# PRD: Phase 2 - RAG Enhancement

> **Parent PRD:** `PRD-openclaw-inspired-improvements.md`
> **Created:** 2026-01-30 | **Status:** Ready for Implementation
> **Estimated Effort:** 2 days | **Priority:** High
> **Depends On:** Phase 1 completed

---

## Overview

Phase 2 focuses on **improving retrieval quality** and **ensuring RAG reliability**. These improvements make semantic search more accurate and resilient.

### Features in This Phase

| ID | Feature | Impact | Effort |
|----|---------|--------|--------|
| F02 | Hybrid RAG Retrieval (Vector + BM25) | HIGH | 1d |
| F05 | Daily Memory Logs | MEDIUM | 2h |
| F08 | Embedding Provider Fallback Chain | MEDIUM | 2h |
| F10 | Memory Get Tool (Line Ranges) | MEDIUM | 1h |
| F17 | Context Detail Command Extension | MEDIUM | 2h |

---

## F02: Hybrid RAG Retrieval

### Problem
Pure vector search misses exact keyword matches (error codes, IDs, specific terms).

### Solution
Combine vector embeddings (70%) with BM25 full-text search (30%) using Reciprocal Rank Fusion.

### Implementation

#### 2.1 Install dependencies

```bash
pip install rank-bm25
```

#### 2.2 Create hybrid search module

**File:** `~/.claude/mcp-servers/rag-server/hybrid_search.py`

```python
#!/usr/bin/env python3
"""
Hybrid Search Module

Combines vector embeddings with BM25 full-text search
for improved retrieval on exact terms and semantic queries.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
import re

@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector", "bm25", or "hybrid"
    metadata: Dict = None

@dataclass
class HybridConfig:
    """Configuration for hybrid search."""
    vector_weight: float = 0.7
    text_weight: float = 0.3
    rrf_k: int = 60  # RRF constant
    min_score_threshold: float = 0.1

class BM25Index:
    """BM25 index for full-text search."""

    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: List[List[str]] = []
        self.doc_ids: List[str] = []
        self.chunk_ids: List[str] = []
        self.texts: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        text = text.lower()
        # Keep alphanumeric and common code characters
        tokens = re.findall(r'[a-z0-9_\-\.]+', text)
        return [t for t in tokens if len(t) > 1]

    def build(self, documents: List[Dict]):
        """Build BM25 index from documents."""
        self.corpus = []
        self.doc_ids = []
        self.chunk_ids = []
        self.texts = []

        for doc in documents:
            text = doc.get('text', '')
            tokens = self._tokenize(text)

            self.corpus.append(tokens)
            self.doc_ids.append(doc.get('doc_id', ''))
            self.chunk_ids.append(doc.get('chunk_id', ''))
            self.texts.append(text)

        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using BM25."""
        if not self.bm25:
            return []

        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(SearchResult(
                    doc_id=self.doc_ids[idx],
                    chunk_id=self.chunk_ids[idx],
                    text=self.texts[idx],
                    score=float(scores[idx]),
                    source="bm25"
                ))

        return results

class HybridSearcher:
    """Combines vector and BM25 search with RRF fusion."""

    def __init__(self, config: HybridConfig = None):
        self.config = config or HybridConfig()
        self.bm25_index = BM25Index()
        self._vector_search_fn = None

    def set_vector_search(self, search_fn):
        """Set the vector search function."""
        self._vector_search_fn = search_fn

    def index_documents(self, documents: List[Dict]):
        """Build BM25 index (vector index built separately)."""
        self.bm25_index.build(documents)

    def _rrf_score(self, rank: int) -> float:
        """Calculate Reciprocal Rank Fusion score."""
        return 1.0 / (self.config.rrf_k + rank + 1)

    def _fuse_results(
        self,
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Fuse results using weighted RRF."""

        scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}

        # Score vector results
        for rank, result in enumerate(vector_results):
            key = result.chunk_id
            rrf = self._rrf_score(rank) * self.config.vector_weight
            scores[key] = scores.get(key, 0) + rrf
            result_map[key] = result

        # Score BM25 results
        for rank, result in enumerate(bm25_results):
            key = result.chunk_id
            rrf = self._rrf_score(rank) * self.config.text_weight
            scores[key] = scores.get(key, 0) + rrf
            if key not in result_map:
                result_map[key] = result

        # Sort by fused score
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

        fused = []
        for key in sorted_keys:
            result = result_map[key]
            result.score = scores[key]
            result.source = "hybrid"
            fused.append(result)

        return fused

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid"  # "hybrid", "vector", "bm25"
    ) -> List[SearchResult]:
        """
        Perform search using specified mode.

        Args:
            query: Search query
            top_k: Number of results to return
            mode: Search mode - "hybrid", "vector", or "bm25"

        Returns:
            List of SearchResult objects
        """

        if mode == "bm25":
            return self.bm25_index.search(query, top_k)

        if mode == "vector":
            if not self._vector_search_fn:
                raise ValueError("Vector search function not set")
            return self._vector_search_fn(query, top_k)

        # Hybrid mode
        if not self._vector_search_fn:
            # Fallback to BM25 only
            return self.bm25_index.search(query, top_k)

        # Get results from both
        fetch_k = top_k * 2  # Fetch more for fusion
        vector_results = self._vector_search_fn(query, fetch_k)
        bm25_results = self.bm25_index.search(query, fetch_k)

        # Fuse and return top-k
        fused = self._fuse_results(vector_results, bm25_results)
        return fused[:top_k]

# Configuration for the RAG server
def get_hybrid_config(config_path: str = None) -> HybridConfig:
    """Load hybrid search configuration."""
    import json
    from pathlib import Path

    if config_path is None:
        config_path = Path("~/.claude/mcp-servers/rag-server/config.json").expanduser()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return HybridConfig()

    with open(config_path) as f:
        data = json.load(f)

    search_config = data.get("search", {})

    return HybridConfig(
        vector_weight=search_config.get("vector_weight", 0.7),
        text_weight=search_config.get("text_weight", 0.3),
        rrf_k=search_config.get("rrf_k", 60)
    )
```

#### 2.3 Update RAG server configuration

**File:** `~/.claude/mcp-servers/rag-server/config.json` (add/update)

```json
{
  "search": {
    "mode": "hybrid",
    "vector_weight": 0.7,
    "text_weight": 0.3,
    "rrf_k": 60
  },
  "embeddings": {
    "provider": "ollama",
    "model": "mxbai-embed-large"
  }
}
```

#### 2.4 Integrate with existing server

**Modifications to:** `~/.claude/mcp-servers/rag-server/server.py`

```python
# Add to imports
from hybrid_search import HybridSearcher, get_hybrid_config, SearchResult

# In initialization
hybrid_config = get_hybrid_config()
hybrid_searcher = HybridSearcher(hybrid_config)

# In index function - after vector indexing
def on_index_complete(documents):
    hybrid_searcher.index_documents(documents)

# In search function
@mcp_tool
async def rag_search(query: str, project_path: str, top_k: int = 5,
                     mode: str = "hybrid", **kwargs):
    """
    Semantic search with optional hybrid mode.

    Args:
        mode: "hybrid" (default), "vector", or "bm25"
    """
    # ... existing setup ...

    results = hybrid_searcher.search(query, top_k, mode=mode)

    # ... format and return ...
```

### Acceptance Criteria
- [ ] BM25 index builds alongside vector index
- [ ] Hybrid search returns combined results
- [ ] Exact term queries find matches (e.g., "CTM-401")
- [ ] Semantic queries still work well
- [ ] Mode parameter allows fallback to pure vector/bm25
- [ ] Configuration is adjustable

---

## F05: Daily Memory Logs

### Problem
SESSIONS.md grows forever with no temporal organization.

### Solution
Daily append-only log files with automatic creation and injection.

### Implementation

#### 5.1 Create the initialization hook

**File:** `~/.claude/hooks/daily-log-init.sh`

```bash
#!/bin/bash
# Daily Memory Log Initialization
# Creates today's log file and injects recent logs into context

# Get project path from environment or current directory
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"
MEMORY_DIR="$PROJECT_PATH/.claude/memory"
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d 2>/dev/null || echo "")

# Only proceed if this looks like a Claude project
if [ ! -d "$PROJECT_PATH/.claude" ] && [ ! -f "$PROJECT_PATH/.claude/context/DECISIONS.md" ]; then
    exit 0
fi

# Ensure memory directory exists
mkdir -p "$MEMORY_DIR"

# Create today's log if not exists
if [ ! -f "$MEMORY_DIR/$TODAY.md" ]; then
    cat > "$MEMORY_DIR/$TODAY.md" << EOF
# Session Notes: $TODAY

## Decisions

<!-- Decisions will be auto-captured here -->

## Learnings

<!-- Learnings discovered during sessions -->

## Notes

<!-- Manual notes and observations -->

---
*Auto-created by daily-log-init*
EOF
fi

# Output for context injection (keep brief)
echo ""
echo "=== Daily Memory ($TODAY) ==="

# Show today's log (first 30 lines)
if [ -f "$MEMORY_DIR/$TODAY.md" ]; then
    head -30 "$MEMORY_DIR/$TODAY.md" 2>/dev/null
fi

# Show yesterday's summary if exists
if [ -n "$YESTERDAY" ] && [ -f "$MEMORY_DIR/$YESTERDAY.md" ]; then
    echo ""
    echo "--- Yesterday ($YESTERDAY) ---"
    # Just show headers and first item under each
    grep -E "^##|^- " "$MEMORY_DIR/$YESTERDAY.md" 2>/dev/null | head -10
fi
```

#### 5.2 Create the append utility

**File:** `~/.claude/hooks/daily-log-append.sh`

```bash
#!/bin/bash
# Append to Daily Memory Log
# Usage: daily-log-append.sh <project_path> <type> <content>
# Types: decision, learning, note

PROJECT_PATH="$1"
TYPE="$2"
CONTENT="$3"

if [ -z "$PROJECT_PATH" ] || [ -z "$TYPE" ] || [ -z "$CONTENT" ]; then
    echo "Usage: daily-log-append.sh <project_path> <type> <content>"
    exit 1
fi

MEMORY_DIR="$PROJECT_PATH/.claude/memory"
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%H:%M)
LOG_FILE="$MEMORY_DIR/$TODAY.md"

# Ensure directory and file exist
mkdir -p "$MEMORY_DIR"
if [ ! -f "$LOG_FILE" ]; then
    ~/.claude/hooks/daily-log-init.sh
fi

# Map type to section
case "$TYPE" in
    decision|decisions)
        SECTION="## Decisions"
        ;;
    learning|learnings)
        SECTION="## Learnings"
        ;;
    note|notes)
        SECTION="## Notes"
        ;;
    *)
        SECTION="## Notes"
        ;;
esac

# Append under the appropriate section
# Find the section and append after it
if grep -q "$SECTION" "$LOG_FILE"; then
    # Use sed to append after section header
    sed -i '' "/$SECTION/a\\
\\
- [$TIMESTAMP] $CONTENT
" "$LOG_FILE" 2>/dev/null || \
    sed -i "/$SECTION/a\\
\\
- [$TIMESTAMP] $CONTENT
" "$LOG_FILE"
else
    # Section doesn't exist, append at end
    echo "" >> "$LOG_FILE"
    echo "$SECTION" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "- [$TIMESTAMP] $CONTENT" >> "$LOG_FILE"
fi

echo "Appended to $LOG_FILE"
```

#### 5.3 Create cleanup script

**File:** `~/.claude/scripts/cleanup-daily-logs.sh`

```bash
#!/bin/bash
# Cleanup old daily logs (older than 30 days)

RETENTION_DAYS=${1:-30}

echo "Cleaning up daily logs older than $RETENTION_DAYS days..."

# Global memory
find ~/.claude/memory -name "????-??-??.md" -mtime +$RETENTION_DAYS -delete 2>/dev/null

# Project memories
find ~/Documents/Projects/*/.claude/memory -name "????-??-??.md" -mtime +$RETENTION_DAYS -delete 2>/dev/null
find ~/Documents/Docs*/*/.claude/memory -name "????-??-??.md" -mtime +$RETENTION_DAYS -delete 2>/dev/null

echo "Done."
```

#### 5.4 Update context template

**File:** `~/.claude/templates/context-structure/memory/.gitkeep`

```
# This directory contains daily memory logs
# Format: YYYY-MM-DD.md
# Auto-created by daily-log-init.sh
```

### Acceptance Criteria
- [ ] Daily log created automatically on session start
- [ ] Append utility works for all types
- [ ] Yesterday's log injected for context
- [ ] Cleanup removes old logs
- [ ] Logs are searchable via RAG (if indexed)

---

## F08: Embedding Provider Fallback Chain

### Problem
RAG fails completely if Ollama is unavailable.

### Solution
Cascading fallback: Local → OpenAI → Gemini → Disabled.

### Implementation

#### 8.1 Create embeddings module

**File:** `~/.claude/mcp-servers/rag-server/embeddings.py`

```python
#!/usr/bin/env python3
"""
Embedding Provider Chain

Provides fallback chain for embedding generation:
1. Ollama (local, free)
2. OpenAI (cloud, paid)
3. Gemini (cloud, paid)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embeddings: List[List[float]]
    provider: str
    model: str
    dimension: int

class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass

class OllamaProvider(EmbeddingProvider):
    """Local Ollama embeddings."""

    name = "ollama"

    def __init__(self, model: str = "mxbai-embed-large", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._dimension = 1024  # mxbai-embed-large default

    def is_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if r.status_code != 200:
                return False
            # Check if model is available
            models = r.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in models)
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def embed(self, texts: List[str]) -> List[List[float]]:
        import requests
        embeddings = []
        for text in texts:
            r = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            r.raise_for_status()
            embeddings.append(r.json()["embedding"])
        return embeddings

    def get_dimension(self) -> int:
        return self._dimension

class OpenAIProvider(EmbeddingProvider):
    """OpenAI embeddings."""

    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

    def is_available(self) -> bool:
        return bool(self.api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [e.embedding for e in response.data]

    def get_dimension(self) -> int:
        return self._dimensions.get(self.model, 1536)

class GeminiProvider(EmbeddingProvider):
    """Google Gemini embeddings."""

    name = "gemini"

    def __init__(self, model: str = "models/embedding-001"):
        self.model = model
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._dimension = 768

    def is_available(self) -> bool:
        return bool(self.api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        return embeddings

    def get_dimension(self) -> int:
        return self._dimension

class EmbeddingChain:
    """Fallback chain of embedding providers."""

    def __init__(self, providers: List[str] = None):
        """
        Initialize with ordered list of provider names.

        Args:
            providers: List like ["ollama", "openai", "gemini"]
        """
        self.provider_classes = {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider
        }

        provider_names = providers or ["ollama", "openai", "gemini"]
        self.providers: List[EmbeddingProvider] = []

        for name in provider_names:
            if name in self.provider_classes:
                try:
                    provider = self.provider_classes[name]()
                    self.providers.append(provider)
                    logger.info(f"Initialized provider: {name}")
                except Exception as e:
                    logger.warning(f"Failed to init {name}: {e}")

    def get_available_provider(self) -> Optional[EmbeddingProvider]:
        """Get first available provider."""
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    def embed(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed texts using first available provider.

        Raises:
            RuntimeError: If no providers are available
        """
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, trying next")
                continue

            try:
                logger.info(f"Using embedding provider: {provider.name}")
                embeddings = provider.embed(texts)
                return EmbeddingResult(
                    embeddings=embeddings,
                    provider=provider.name,
                    model=getattr(provider, 'model', 'unknown'),
                    dimension=provider.get_dimension()
                )
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}, trying next")
                continue

        raise RuntimeError(
            "No embedding providers available. "
            "Ensure Ollama is running or set OPENAI_API_KEY/GOOGLE_API_KEY."
        )

    def get_status(self) -> dict:
        """Get status of all providers."""
        status = {
            "available": [],
            "unavailable": [],
            "active": None
        }

        for provider in self.providers:
            info = {
                "name": provider.name,
                "model": getattr(provider, 'model', 'unknown'),
                "dimension": provider.get_dimension()
            }

            if provider.is_available():
                status["available"].append(info)
                if status["active"] is None:
                    status["active"] = provider.name
            else:
                status["unavailable"].append(info)

        return status

# Default chain instance
_default_chain: Optional[EmbeddingChain] = None

def get_embedding_chain() -> EmbeddingChain:
    """Get or create the default embedding chain."""
    global _default_chain
    if _default_chain is None:
        _default_chain = EmbeddingChain()
    return _default_chain

def embed_texts(texts: List[str]) -> EmbeddingResult:
    """Convenience function to embed texts."""
    return get_embedding_chain().embed(texts)
```

### Acceptance Criteria
- [ ] Ollama is tried first
- [ ] Falls back to OpenAI if Ollama unavailable
- [ ] Falls back to Gemini if OpenAI unavailable
- [ ] Clear error if all unavailable
- [ ] Status endpoint shows provider state

---

## F10: Memory Get Tool

### Problem
Need to read full files when only a section is needed.

### Solution
Add `rag_get` tool for line-range retrieval.

### Implementation

**Add to:** `~/.claude/mcp-servers/rag-server/server.py`

```python
@mcp_tool
async def rag_get(
    source_file: str,
    project_path: str,
    start_line: int = None,
    end_line: int = None,
    around_match: str = None,
    context_lines: int = 5
) -> dict:
    """
    Get specific content from a file with line ranges.

    Args:
        source_file: Relative path to source file
        project_path: Absolute path to project root
        start_line: Starting line (1-indexed)
        end_line: Ending line (inclusive)
        around_match: Text to find and return context around
        context_lines: Lines of context around match

    Returns:
        Dict with content, line numbers, and metadata
    """
    from pathlib import Path

    full_path = Path(project_path).expanduser() / source_file

    if not full_path.exists():
        return {"error": f"File not found: {source_file}"}

    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    total_lines = len(lines)

    # Handle around_match
    if around_match:
        for i, line in enumerate(lines):
            if around_match in line:
                start_line = max(1, i + 1 - context_lines)
                end_line = min(total_lines, i + 1 + context_lines)
                break
        else:
            return {
                "error": f"Match not found: {around_match}",
                "file": source_file,
                "total_lines": total_lines
            }

    # Default to full file
    start_line = start_line or 1
    end_line = end_line or total_lines

    # Clamp to valid range
    start_line = max(1, min(start_line, total_lines))
    end_line = max(start_line, min(end_line, total_lines))

    # Extract lines (convert to 0-indexed)
    selected = lines[start_line - 1:end_line]

    # Format with line numbers
    content = ""
    for i, line in enumerate(selected, start=start_line):
        content += f"{i:5d} │ {line}"

    return {
        "source_file": source_file,
        "project_path": project_path,
        "start_line": start_line,
        "end_line": end_line,
        "total_lines": total_lines,
        "lines_returned": len(selected),
        "content": content
    }
```

### Acceptance Criteria
- [ ] Can retrieve specific line ranges
- [ ] Can find text and return surrounding context
- [ ] Returns line numbers with content
- [ ] Handles missing files gracefully
- [ ] Works with large files

---

## F17: Context Detail Command Extension

Extends F06 (from Phase 1) with additional detail.

### Implementation

**Update:** `~/.claude/skills/context-inspector/SKILL.md`

Add to the detail section:

```markdown
## Extended Detail (`/context detail --full`)

Full analysis including:
- Token estimates per message
- Tool result age histogram
- Largest individual items
- Injection file sizes
- Recommendation prioritization
```

### Acceptance Criteria
- [ ] Extended detail shows all metrics
- [ ] Recommendations are prioritized
- [ ] Works with Phase 1 `/context` skill

---

## Task Checklist

### F02: Hybrid RAG Retrieval
- [ ] T2.1: Install rank-bm25 (`pip install rank-bm25`)
- [ ] T2.2: Create `hybrid_search.py` module
- [ ] T2.3: Update RAG server config with search settings
- [ ] T2.4: Integrate hybrid searcher with server
- [ ] T2.5: Test exact term queries (error codes, IDs)
- [ ] T2.6: Test semantic queries still work
- [ ] T2.7: Verify mode switching (hybrid/vector/bm25)

### F05: Daily Memory Logs
- [ ] T5.1: Create `daily-log-init.sh`
- [ ] T5.2: Create `daily-log-append.sh`
- [ ] T5.3: Create `cleanup-daily-logs.sh`
- [ ] T5.4: Make scripts executable
- [ ] T5.5: Test log creation on session start
- [ ] T5.6: Test append functionality
- [ ] T5.7: Add to context template

### F08: Embedding Provider Fallback
- [ ] T8.1: Create `embeddings.py` module
- [ ] T8.2: Implement OllamaProvider
- [ ] T8.3: Implement OpenAIProvider
- [ ] T8.4: Implement GeminiProvider
- [ ] T8.5: Implement EmbeddingChain
- [ ] T8.6: Test fallback with Ollama stopped
- [ ] T8.7: Add status endpoint

### F10: Memory Get Tool
- [ ] T10.1: Add `rag_get` tool to server.py
- [ ] T10.2: Implement line range retrieval
- [ ] T10.3: Implement around_match feature
- [ ] T10.4: Test with various files
- [ ] T10.5: Document in RAG_GUIDE.md

### F17: Context Detail Extension
- [ ] T17.1: Update context-inspector skill
- [ ] T17.2: Add extended detail view
- [ ] T17.3: Test with Phase 1 integration

### Integration Testing
- [ ] T-INT.1: Test hybrid search end-to-end
- [ ] T-INT.2: Test embedding fallback
- [ ] T-INT.3: Verify daily logs work with RAG
- [ ] T-INT.4: Benchmark search improvements

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Exact term recall | 70%+ | Test queries for IDs, codes |
| Semantic recall maintained | No regression | Compare to baseline |
| RAG availability | 99.9% | Monitor over 1 week |
| Daily log creation | 100% | Check project sessions |

---

## Rollback Plan

1. Set `search.mode: "vector"` in config
2. Remove `hybrid_search.py`
3. Remove `embeddings.py` (revert to direct Ollama)
4. Remove daily log hooks

All changes isolated and reversible.
