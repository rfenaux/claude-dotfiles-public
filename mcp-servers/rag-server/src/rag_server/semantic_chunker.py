"""Semantic chunking using embeddings to detect topic boundaries.

Splits text at natural topic transitions rather than arbitrary character limits.
Uses cosine similarity between sentence embeddings to find breakpoints.
"""
import logging
import re
import hashlib
from typing import List, Dict, Any, Optional, Callable

from .date_extraction import get_date_context
from .chunk_classifier import classify_chunk

logger = logging.getLogger(__name__)

# Try to import numpy for cosine similarity
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available, semantic chunking disabled")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not NUMPY_AVAILABLE:
        # Fallback without numpy
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class SemanticChunker:
    """Chunk text based on semantic boundaries using embeddings.

    How it works:
    1. Split text into sentences
    2. Group sentences into sliding windows
    3. Generate embeddings for each window
    4. Compare consecutive windows - low similarity = topic change
    5. Split at topic boundaries

    Advantages over fixed-size chunking:
    - Preserves topic coherence within chunks
    - Natural breakpoints instead of mid-sentence cuts
    - Better retrieval relevance

    Trade-offs:
    - Requires embedding calls (slower indexing)
    - Best for important documents where quality matters
    """

    def __init__(
        self,
        embed_func: Callable[[str], List[float]],
        min_chunk_size: int = 200,
        max_chunk_size: int = 2000,
        similarity_threshold: float = 0.5,
        window_size: int = 3,
    ):
        """Initialize semantic chunker.

        Args:
            embed_func: Function that takes text and returns embedding vector
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size (will split at threshold)
            similarity_threshold: Below this similarity, consider it a topic break
            window_size: Number of sentences to combine for embedding
        """
        self.embed_func = embed_func
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.similarity_threshold = similarity_threshold
        self.window_size = window_size

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'(Mr|Mrs|Ms|Dr|Prof|Inc|Ltd|Jr|Sr|vs)\.\s+', r'\1<DOT> ', text)
        text = re.sub(r'(\d+)\.\s+', r'\1<DOT> ', text)  # numbered lists

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Restore dots
        sentences = [s.replace('<DOT>', '.') for s in sentences]

        # Filter empty
        return [s.strip() for s in sentences if s.strip()]

    def _combine_sentences(self, sentences: List[str], start: int, count: int) -> str:
        """Combine a window of sentences."""
        end = min(start + count, len(sentences))
        return ' '.join(sentences[start:end])

    def _find_breakpoints(self, sentences: List[str]) -> List[int]:
        """Find semantic breakpoints using embedding similarity.

        Returns indices where topic changes occur.
        """
        if len(sentences) < self.window_size * 2:
            return []  # Too short for meaningful analysis

        breakpoints = []

        # Create windows and get embeddings
        windows = []
        for i in range(len(sentences) - self.window_size + 1):
            window_text = self._combine_sentences(sentences, i, self.window_size)
            windows.append(window_text)

        # Batch embed if possible (more efficient)
        try:
            embeddings = [self.embed_func(w) for w in windows]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

        # Compare consecutive windows
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # Find drops in similarity (topic changes)
        for i, sim in enumerate(similarities):
            if sim < self.similarity_threshold:
                # Breakpoint is after the center of the first window
                breakpoint_idx = i + self.window_size // 2 + 1
                if breakpoint_idx < len(sentences):
                    breakpoints.append(breakpoint_idx)

        return breakpoints

    def _generate_chunk_id(self, source_file: str, chunk_index: int, text: str) -> str:
        """Generate a unique ID for a chunk."""
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{source_file}::{chunk_index}::{content_hash}"

    def chunk(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Split text into semantically coherent chunks.

        Args:
            text: Text content to chunk
            source_file: Source file path for reference

        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []

        sentences = self._split_sentences(text)

        if not sentences:
            return []

        # Find semantic breakpoints
        breakpoints = self._find_breakpoints(sentences)

        # Create chunks based on breakpoints
        chunks = []
        chunk_index = 0

        # Add start and end boundaries
        boundaries = [0] + breakpoints + [len(sentences)]
        boundaries = sorted(set(boundaries))  # Dedupe and sort

        current_text = ""
        current_start = 0

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            segment = ' '.join(sentences[start:end])

            # Check if adding segment would exceed max size
            potential = current_text + ' ' + segment if current_text else segment

            if len(potential) > self.max_chunk_size and current_text:
                # Save current chunk
                if len(current_text) >= self.min_chunk_size:
                    chunk_data = self._create_chunk(
                        current_text.strip(), source_file, chunk_index
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1
                current_text = segment
            elif len(segment) > self.max_chunk_size:
                # Segment itself is too large, split it
                if current_text and len(current_text) >= self.min_chunk_size:
                    chunk_data = self._create_chunk(
                        current_text.strip(), source_file, chunk_index
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                # Split large segment by sentences
                sub_chunks = self._split_large_segment(segment, source_file, chunk_index)
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                current_text = ""
            else:
                # Add to current chunk
                if len(current_text) < self.min_chunk_size:
                    current_text = potential
                else:
                    current_text = potential

        # Add final chunk
        if current_text.strip() and len(current_text.strip()) >= self.min_chunk_size:
            chunk_data = self._create_chunk(
                current_text.strip(), source_file, chunk_index
            )
            chunks.append(chunk_data)

        # If no chunks created, fall back to simple chunking
        if not chunks and text.strip():
            chunk_data = self._create_chunk(text.strip(), source_file, 0)
            chunks.append(chunk_data)

        return chunks

    def _create_chunk(self, text: str, source_file: str, chunk_index: int) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata."""
        chunk_data = {
            "id": self._generate_chunk_id(source_file, chunk_index, text),
            "text": text,
            "source_file": source_file,
            "chunk_index": chunk_index,
            "chunking_method": "semantic",
        }

        # Extract dates
        date_context = get_date_context(text)
        if date_context["most_recent"]:
            chunk_data["content_dates"] = date_context

        # Classify chunk
        chunk_data["classification"] = classify_chunk(text)

        return chunk_data

    def _split_large_segment(
        self, text: str, source_file: str, start_index: int
    ) -> List[Dict[str, Any]]:
        """Split an oversized segment into smaller chunks."""
        sentences = self._split_sentences(text)
        chunks = []
        current = ""
        idx = start_index

        for sentence in sentences:
            potential = current + ' ' + sentence if current else sentence

            if len(potential) > self.max_chunk_size and current:
                if len(current) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(current.strip(), source_file, idx))
                    idx += 1
                current = sentence
            else:
                current = potential

        if current and len(current) >= self.min_chunk_size:
            chunks.append(self._create_chunk(current.strip(), source_file, idx))

        return chunks


class AdaptiveChunker:
    """Wrapper that chooses best chunking strategy based on content.

    Uses semantic chunking for high-value documents, falls back to
    simpler methods for code or structured content.
    """

    def __init__(
        self,
        embed_func: Optional[Callable[[str], List[float]]] = None,
        use_semantic: bool = True,
    ):
        """Initialize adaptive chunker.

        Args:
            embed_func: Embedding function (required for semantic mode)
            use_semantic: Whether to enable semantic chunking
        """
        self.embed_func = embed_func
        self.use_semantic = use_semantic and embed_func is not None
        self._semantic_chunker: Optional[SemanticChunker] = None

    def _get_semantic_chunker(self) -> Optional[SemanticChunker]:
        """Lazy-load semantic chunker."""
        if self._semantic_chunker is None and self.embed_func:
            self._semantic_chunker = SemanticChunker(self.embed_func)
        return self._semantic_chunker

    def chunk(self, text: str, source_file: str, force_semantic: bool = False) -> List[Dict[str, Any]]:
        """Chunk text using appropriate strategy.

        Args:
            text: Text to chunk
            source_file: Source file path
            force_semantic: Force semantic chunking even for code

        Returns:
            List of chunks
        """
        from .chunking import get_chunker, HeaderChunker, CodeChunker

        # Determine file type
        ext = "." + source_file.rsplit(".", 1)[-1].lower() if "." in source_file else ""
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".rb", ".java"}

        # Use code chunker for code (unless forced)
        if ext in code_extensions and not force_semantic:
            return get_chunker(source_file).chunk(text, source_file)

        # Use semantic chunking for rich text documents if available
        if self.use_semantic and self._should_use_semantic(text, ext):
            semantic = self._get_semantic_chunker()
            if semantic:
                try:
                    return semantic.chunk(text, source_file)
                except Exception as e:
                    logger.warning(f"Semantic chunking failed, falling back: {e}")

        # Fall back to standard chunker
        return get_chunker(source_file).chunk(text, source_file)

    def _should_use_semantic(self, text: str, ext: str) -> bool:
        """Decide if semantic chunking is appropriate for this content."""
        # Use semantic for prose-heavy documents
        prose_extensions = {".md", ".txt", ".pdf", ".docx", ".html"}

        if ext in prose_extensions:
            # Check if it's actually prose (not just bullet lists)
            lines = text.split('\n')
            prose_lines = sum(1 for l in lines if len(l) > 80 and not l.strip().startswith(('-', '*', '#', '|')))
            return prose_lines > len(lines) * 0.3  # At least 30% prose

        return False
