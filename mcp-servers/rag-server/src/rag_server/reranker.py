"""Cross-encoder reranking for improved search relevance.

Uses a cross-encoder model to rerank initial retrieval results
based on query-document relevance scoring.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")


class CrossEncoderReranker:
    """Reranker using cross-encoder models.

    Cross-encoders score query-document pairs jointly, providing
    more accurate relevance than bi-encoder similarity alone.
    """

    # Lightweight cross-encoder models (in order of speed vs quality)
    MODELS = {
        "fast": "cross-encoder/ms-marco-MiniLM-L-6-v2",      # 22M params, fastest
        "balanced": "cross-encoder/ms-marco-MiniLM-L-12-v2",  # 33M params
        "accurate": "cross-encoder/ms-marco-TinyBERT-L-2-v2", # Tiny but accurate
    }

    def __init__(self, model_type: str = "fast"):
        """Initialize reranker.

        Args:
            model_type: One of 'fast', 'balanced', 'accurate'
        """
        self._model: Optional["CrossEncoder"] = None
        self._model_name = self.MODELS.get(model_type, self.MODELS["fast"])

    @property
    def is_available(self) -> bool:
        """Check if reranking is available."""
        return RERANKER_AVAILABLE

    def _ensure_model(self):
        """Lazy-load the model."""
        if not RERANKER_AVAILABLE:
            return

        if self._model is None:
            logger.info(f"Loading cross-encoder model: {self._model_name}")
            self._model = CrossEncoder(self._model_name)

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder.

        Args:
            query: Search query
            results: List of result dicts (must have text_key field)
            top_k: Number of results to return (None = return all, reranked)
            text_key: Key for text field in results

        Returns:
            Reranked results with 'rerank_score' added
        """
        if not RERANKER_AVAILABLE or not results:
            return results

        self._ensure_model()

        if self._model is None:
            return results

        # Create query-document pairs
        pairs = [(query, r[text_key]) for r in results if text_key in r]

        if not pairs:
            return results

        # Score pairs
        try:
            scores = self._model.predict(pairs)
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results

        # Add scores to results
        for i, result in enumerate(results):
            if i < len(scores):
                result["rerank_score"] = float(scores[i])
            else:
                result["rerank_score"] = 0.0

        # Sort by rerank score (descending)
        reranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            return reranked[:top_k]
        return reranked


class SimpleReranker:
    """Fallback reranker using keyword overlap when cross-encoder unavailable.

    Not as good as neural reranking but better than nothing.
    """

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Rerank based on keyword overlap and position.

        Args:
            query: Search query
            results: List of result dicts
            top_k: Number of results to return
            text_key: Key for text field

        Returns:
            Reranked results
        """
        if not results:
            return results

        query_terms = set(query.lower().split())

        for result in results:
            text = result.get(text_key, "").lower()
            text_terms = set(text.split())

            # Calculate overlap
            overlap = len(query_terms & text_terms)
            coverage = overlap / len(query_terms) if query_terms else 0

            # Bonus for exact phrase match
            phrase_bonus = 0.3 if query.lower() in text else 0

            # Bonus for query terms appearing early
            position_bonus = 0
            for term in query_terms:
                pos = text.find(term)
                if pos >= 0 and pos < 500:  # In first 500 chars
                    position_bonus += 0.1

            result["rerank_score"] = coverage + phrase_bonus + position_bonus

        # Sort by score
        reranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            return reranked[:top_k]
        return reranked


def get_reranker(prefer_neural: bool = True) -> Any:
    """Get best available reranker.

    Args:
        prefer_neural: If True, use cross-encoder if available

    Returns:
        Reranker instance
    """
    if prefer_neural and RERANKER_AVAILABLE:
        return CrossEncoderReranker()
    return SimpleReranker()
