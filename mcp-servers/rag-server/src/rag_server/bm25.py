"""BM25 keyword search index for hybrid retrieval.

Provides keyword-based search to complement vector similarity search.
Uses bm25s for fast, pure-Python BM25 implementation.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import bm25s, fall back gracefully
try:
    import bm25s
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("bm25s not installed. Install with: pip install bm25s")


class BM25Index:
    """BM25 keyword index for a project.

    Stores index alongside LanceDB in .rag/bm25_index/
    """

    def __init__(self, project_path: str):
        """Initialize BM25 index.

        Args:
            project_path: Path to project root
        """
        self.project_path = Path(project_path)
        self.index_path = self.project_path / ".rag" / "bm25_index"
        self._retriever: Optional["bm25s.BM25"] = None
        self._doc_ids: List[str] = []
        self._doc_texts: List[str] = []

    @property
    def is_available(self) -> bool:
        """Check if BM25 is available."""
        return BM25_AVAILABLE

    def _ensure_index_dir(self):
        """Ensure index directory exists."""
        self.index_path.mkdir(parents=True, exist_ok=True)

    def build_index(self, documents: List[Dict[str, Any]]) -> int:
        """Build BM25 index from documents.

        Args:
            documents: List of dicts with 'id' and 'text' fields

        Returns:
            Number of documents indexed
        """
        if not BM25_AVAILABLE:
            logger.warning("BM25 not available, skipping index build")
            return 0

        if not documents:
            return 0

        self._ensure_index_dir()

        # Extract texts and IDs
        self._doc_ids = [doc["id"] for doc in documents]
        self._doc_texts = [doc["text"] for doc in documents]

        # Tokenize documents (simple whitespace + lowercase)
        corpus_tokens = bm25s.tokenize(self._doc_texts, stopwords="en")

        # Build index
        self._retriever = bm25s.BM25()
        self._retriever.index(corpus_tokens)

        # Save index
        self._save_index()

        logger.info(f"Built BM25 index with {len(documents)} documents")
        return len(documents)

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents to existing index (rebuilds for now).

        Args:
            documents: List of dicts with 'id' and 'text' fields

        Returns:
            Number of documents in index after addition
        """
        if not BM25_AVAILABLE:
            return 0

        # Load existing
        self._load_index()

        # Add new documents
        for doc in documents:
            if doc["id"] not in self._doc_ids:
                self._doc_ids.append(doc["id"])
                self._doc_texts.append(doc["text"])

        # Rebuild index with all documents
        if self._doc_texts:
            corpus_tokens = bm25s.tokenize(self._doc_texts, stopwords="en")
            self._retriever = bm25s.BM25()
            self._retriever.index(corpus_tokens)
            self._save_index()

        return len(self._doc_ids)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using BM25.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of dicts with 'id', 'text', 'score'
        """
        if not BM25_AVAILABLE:
            return []

        self._load_index()

        if self._retriever is None or not self._doc_ids:
            return []

        # Tokenize query
        query_tokens = bm25s.tokenize([query], stopwords="en")

        # Search
        results, scores = self._retriever.retrieve(query_tokens, k=min(top_k, len(self._doc_ids)))

        # Format results
        output = []
        for idx, score in zip(results[0], scores[0]):
            if idx < len(self._doc_ids):
                output.append({
                    "id": self._doc_ids[idx],
                    "text": self._doc_texts[idx],
                    "bm25_score": float(score),
                })

        return output

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from index.

        Args:
            doc_id: Document ID to remove

        Returns:
            True if removed
        """
        if not BM25_AVAILABLE:
            return False

        self._load_index()

        if doc_id in self._doc_ids:
            idx = self._doc_ids.index(doc_id)
            self._doc_ids.pop(idx)
            self._doc_texts.pop(idx)

            # Rebuild index
            if self._doc_texts:
                corpus_tokens = bm25s.tokenize(self._doc_texts, stopwords="en")
                self._retriever = bm25s.BM25()
                self._retriever.index(corpus_tokens)
            else:
                self._retriever = None

            self._save_index()
            return True

        return False

    def clear(self):
        """Clear the BM25 index."""
        import shutil
        self._retriever = None
        self._doc_ids = []
        self._doc_texts = []
        if self.index_path.exists():
            shutil.rmtree(self.index_path)

    def _save_index(self):
        """Save index to disk."""
        if not BM25_AVAILABLE or self._retriever is None:
            return

        self._ensure_index_dir()

        # Save retriever
        self._retriever.save(str(self.index_path / "bm25"))

        # Save document mapping
        mapping = {
            "doc_ids": self._doc_ids,
            "doc_texts": self._doc_texts,
        }
        with open(self.index_path / "mapping.json", "w") as f:
            json.dump(mapping, f)

    def _load_index(self):
        """Load index from disk if not already loaded."""
        if not BM25_AVAILABLE:
            return

        if self._retriever is not None:
            return  # Already loaded

        mapping_path = self.index_path / "mapping.json"
        bm25_path = self.index_path / "bm25.index"

        if not mapping_path.exists():
            return

        try:
            # Load mapping
            with open(mapping_path) as f:
                mapping = json.load(f)
            self._doc_ids = mapping.get("doc_ids", [])
            self._doc_texts = mapping.get("doc_texts", [])

            # Load BM25 index
            if (self.index_path / "bm25.index").exists() or (self.index_path / "bm25").exists():
                self._retriever = bm25s.BM25.load(str(self.index_path / "bm25"), load_corpus=False)

        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            self._retriever = None


def merge_hybrid_results(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    alpha: float = 0.4,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Merge vector and BM25 results using reciprocal rank fusion.

    Args:
        vector_results: Results from vector search (must have 'id' and 'score')
        bm25_results: Results from BM25 search (must have 'id' and 'bm25_score')
        alpha: Weight for BM25 (0.4 = 40% keyword, 60% semantic)
        top_k: Number of results to return

    Returns:
        Merged results with combined scores
    """
    # Normalize scores to 0-1 range
    def normalize_scores(results: List[Dict], score_key: str) -> Dict[str, float]:
        if not results:
            return {}
        scores = [r[score_key] for r in results]
        min_s, max_s = min(scores), max(scores)
        range_s = max_s - min_s if max_s > min_s else 1.0
        return {
            r["id"]: 1 - ((r[score_key] - min_s) / range_s)  # Invert: lower distance = higher score
            for r in results
        }

    # For BM25, higher is better (no inversion needed)
    def normalize_bm25(results: List[Dict]) -> Dict[str, float]:
        if not results:
            return {}
        scores = [r["bm25_score"] for r in results]
        min_s, max_s = min(scores), max(scores)
        range_s = max_s - min_s if max_s > min_s else 1.0
        return {
            r["id"]: (r["bm25_score"] - min_s) / range_s if range_s > 0 else 0.5
            for r in results
        }

    vector_scores = normalize_scores(vector_results, "score")
    bm25_scores = normalize_bm25(bm25_results)

    # Combine scores
    all_ids = set(vector_scores.keys()) | set(bm25_scores.keys())
    combined = {}

    for doc_id in all_ids:
        v_score = vector_scores.get(doc_id, 0.0)
        b_score = bm25_scores.get(doc_id, 0.0)
        combined[doc_id] = (1 - alpha) * v_score + alpha * b_score

    # Sort by combined score (descending)
    sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

    # Build result list with full document info
    doc_lookup = {r["id"]: r for r in vector_results}
    doc_lookup.update({r["id"]: r for r in bm25_results})

    output = []
    for doc_id in sorted_ids[:top_k]:
        if doc_id in doc_lookup:
            result = doc_lookup[doc_id].copy()
            result["hybrid_score"] = combined[doc_id]
            result["vector_contrib"] = vector_scores.get(doc_id, 0.0)
            result["bm25_contrib"] = bm25_scores.get(doc_id, 0.0)
            output.append(result)

    return output
