#!/usr/bin/env python3
"""
Hybrid Search Module

Combines vector embeddings with BM25 full-text search
for improved retrieval on exact terms and semantic queries.

Part of: OpenClaw-inspired improvements (Phase 2, F02)
Created: 2026-01-30
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)

# Try to import rank_bm25, gracefully degrade if not available
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not installed. Install with: pip install rank-bm25")


@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector", "bm25", or "hybrid"
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class HybridConfig:
    """Configuration for hybrid search."""
    vector_weight: float = 0.7
    text_weight: float = 0.3
    rrf_k: int = 60  # RRF constant (higher = more equal weighting)
    min_score_threshold: float = 0.01

    @classmethod
    def from_dict(cls, data: dict) -> "HybridConfig":
        return cls(
            vector_weight=data.get("vector_weight", 0.7),
            text_weight=data.get("text_weight", 0.3),
            rrf_k=data.get("rrf_k", 60),
            min_score_threshold=data.get("min_score_threshold", 0.01)
        )


class BM25Index:
    """BM25 index for full-text search."""

    def __init__(self):
        self.bm25: Optional["BM25Okapi"] = None
        self.corpus: List[List[str]] = []
        self.doc_ids: List[str] = []
        self.chunk_ids: List[str] = []
        self.texts: List[str] = []
        self.metadata: List[Dict] = []

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase, split on non-alphanumeric.
        Keeps code-relevant characters like underscores and hyphens.
        """
        text = text.lower()
        # Keep alphanumeric and common code characters
        tokens = re.findall(r'[a-z0-9_\-\.]+', text)
        # Filter very short tokens but keep error codes like "CTM-401"
        return [t for t in tokens if len(t) > 1 or t.isdigit()]

    def build(self, documents: List[Dict]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of dicts with 'text', 'doc_id', 'chunk_id', and optional 'metadata'
        """
        if not BM25_AVAILABLE:
            logger.warning("BM25 not available, skipping index build")
            return

        self.corpus = []
        self.doc_ids = []
        self.chunk_ids = []
        self.texts = []
        self.metadata = []

        for doc in documents:
            text = doc.get('text', '')
            tokens = self._tokenize(text)

            self.corpus.append(tokens)
            self.doc_ids.append(doc.get('doc_id', ''))
            self.chunk_ids.append(doc.get('chunk_id', str(len(self.chunk_ids))))
            self.texts.append(text)
            self.metadata.append(doc.get('metadata', {}))

        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            logger.info(f"Built BM25 index with {len(self.corpus)} documents")

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using BM25."""
        if not BM25_AVAILABLE or not self.bm25:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

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
                    source="bm25",
                    metadata=self.metadata[idx]
                ))

        return results

    def is_available(self) -> bool:
        """Check if BM25 index is ready."""
        return BM25_AVAILABLE and self.bm25 is not None


class HybridSearcher:
    """Combines vector and BM25 search with RRF fusion."""

    def __init__(self, config: Optional[HybridConfig] = None):
        self.config = config or HybridConfig()
        self.bm25_index = BM25Index()
        self._vector_search_fn = None
        self._documents = []

    def set_vector_search(self, search_fn):
        """
        Set the vector search function.

        Args:
            search_fn: Function that takes (query: str, top_k: int) and returns List[SearchResult]
        """
        self._vector_search_fn = search_fn

    def index_documents(self, documents: List[Dict]):
        """
        Build BM25 index (vector index built separately).

        Args:
            documents: List of dicts with 'text', 'doc_id', 'chunk_id', and optional 'metadata'
        """
        self._documents = documents
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
            if key not in result_map:
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
            if scores[key] < self.config.min_score_threshold:
                continue
            result = result_map[key]
            # Create new result with fused score
            fused.append(SearchResult(
                doc_id=result.doc_id,
                chunk_id=result.chunk_id,
                text=result.text,
                score=scores[key],
                source="hybrid",
                metadata=result.metadata
            ))

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
        vector_results = []
        bm25_results = []

        # Get vector results if available
        if self._vector_search_fn:
            try:
                vector_results = self._vector_search_fn(query, top_k * 2)
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")

        # Get BM25 results if available
        if self.bm25_index.is_available():
            bm25_results = self.bm25_index.search(query, top_k * 2)

        # If only one source available, use it
        if not vector_results and bm25_results:
            return bm25_results[:top_k]
        if vector_results and not bm25_results:
            return vector_results[:top_k]
        if not vector_results and not bm25_results:
            return []

        # Fuse and return top-k
        fused = self._fuse_results(vector_results, bm25_results)
        return fused[:top_k]

    def get_status(self) -> dict:
        """Get status of the hybrid searcher."""
        return {
            "bm25_available": self.bm25_index.is_available(),
            "bm25_doc_count": len(self.bm25_index.corpus) if self.bm25_index.corpus else 0,
            "vector_available": self._vector_search_fn is not None,
            "config": {
                "vector_weight": self.config.vector_weight,
                "text_weight": self.config.text_weight,
                "rrf_k": self.config.rrf_k
            }
        }


def get_hybrid_config(config_path: str = None) -> HybridConfig:
    """Load hybrid search configuration from file."""
    import json
    from pathlib import Path

    if config_path is None:
        config_path = Path("~/.claude/mcp-servers/rag-server/config.json").expanduser()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return HybridConfig()

    try:
        with open(config_path) as f:
            data = json.load(f)
        search_config = data.get("search", {})
        return HybridConfig.from_dict(search_config)
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
        return HybridConfig()


# Convenience function for testing
def demo_search():
    """Demo the hybrid search functionality."""
    # Sample documents
    docs = [
        {"doc_id": "1", "chunk_id": "1-1", "text": "Error CTM-401: Authentication failed for user"},
        {"doc_id": "1", "chunk_id": "1-2", "text": "The authentication system uses OAuth2 tokens"},
        {"doc_id": "2", "chunk_id": "2-1", "text": "Memory management in Python uses garbage collection"},
        {"doc_id": "2", "chunk_id": "2-2", "text": "The CTM system manages cognitive task memory"},
    ]

    # Create searcher
    searcher = HybridSearcher()
    searcher.index_documents(docs)

    # Test queries
    queries = [
        ("CTM-401", "Exact error code"),
        ("authentication", "Semantic concept"),
        ("memory management", "Multi-word semantic"),
    ]

    print("=" * 60)
    print("Hybrid Search Demo")
    print("=" * 60)

    for query, desc in queries:
        print(f"\nQuery: '{query}' ({desc})")
        print("-" * 40)

        # BM25 only
        bm25_results = searcher.search(query, top_k=2, mode="bm25")
        print("BM25 results:")
        for r in bm25_results:
            print(f"  [{r.score:.3f}] {r.text[:60]}...")

        print()


if __name__ == "__main__":
    demo_search()
