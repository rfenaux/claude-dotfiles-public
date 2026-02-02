"""Text chunking strategies for document processing.

Provides multiple chunking strategies optimized for different document types:
- TextChunker: General purpose paragraph-based chunking
- CodeChunker: Respects function/class boundaries in code
- HeaderChunker: Splits by Markdown/document headers (best for specs & docs)

Usage:
    chunker = get_chunker(file_path)  # Auto-selects best strategy
    chunks = chunker.chunk(text, source_file)
"""
from typing import List, Dict, Any, Tuple
import re
import hashlib

from .date_extraction import get_date_context
from .chunk_classifier import classify_chunk

class TextChunker:
    """Chunk text into overlapping segments for embedding."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ):
        """Initialize text chunker.

        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separator: Primary separator for splitting text
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def _generate_chunk_id(self, source_file: str, chunk_index: int, text: str) -> str:
        """Generate a unique ID for a chunk."""
        # Use hash of content for deduplication
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{source_file}::{chunk_index}::{content_hash}"

    def chunk(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks.

        Args:
            text: Text content to chunk
            source_file: Source file path for reference

        Returns:
            List of chunk dictionaries with id, text, source_file, chunk_index
        """
        if not text or not text.strip():
            return []

        chunks = []
        # Split by main separator first
        paragraphs = text.split(self.separator)

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if adding this paragraph exceeds chunk size
            potential_chunk = current_chunk + self.separator + para if current_chunk else para

            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = current_chunk.strip()
                if chunk_text:
                    chunk_data = {
                        "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                        "text": chunk_text,
                        "source_file": source_file,
                        "chunk_index": chunk_index,
                    }
                    # Extract dates mentioned in the chunk content
                    date_context = get_date_context(chunk_text)
                    if date_context["most_recent"]:
                        chunk_data["content_dates"] = date_context
                    # Classify chunk by relevance and category
                    chunk_data["classification"] = classify_chunk(chunk_text)
                    chunks.append(chunk_data)
                    chunk_index += 1

                # Start new chunk with overlap
                # Get last N characters for overlap
                if len(current_chunk) > self.chunk_overlap:
                    # Try to break at sentence boundary for cleaner overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    sentence_break = overlap_text.rfind(". ")
                    if sentence_break > 0:
                        overlap_text = overlap_text[sentence_break + 2:]
                    current_chunk = overlap_text + self.separator + para
                else:
                    current_chunk = para
            else:
                current_chunk = potential_chunk

        # Add final chunk
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunk_data = {
                "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                "text": chunk_text,
                "source_file": source_file,
                "chunk_index": chunk_index,
            }
            # Extract dates mentioned in the chunk content
            date_context = get_date_context(chunk_text)
            if date_context["most_recent"]:
                chunk_data["content_dates"] = date_context
            # Classify chunk by relevance and category
            chunk_data["classification"] = classify_chunk(chunk_text)
            chunks.append(chunk_data)

        return chunks


class CodeChunker(TextChunker):
    """Specialized chunker for code files that respects code structure."""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 100,
    ):
        super().__init__(chunk_size, chunk_overlap, separator="\n\n")

    def chunk(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Chunk code with awareness of function/class boundaries."""
        if not text or not text.strip():
            return []

        # Try to split at function/class definitions
        # Patterns for common languages
        boundary_patterns = [
            r"\n(?=def\s+\w+)",  # Python functions
            r"\n(?=class\s+\w+)",  # Python/JS classes
            r"\n(?=function\s+\w+)",  # JS functions
            r"\n(?=const\s+\w+\s*=\s*(?:async\s*)?\()",  # JS arrow functions
            r"\n(?=func\s+)",  # Go functions
            r"\n(?=fn\s+)",  # Rust functions
            r"\n(?=pub\s+(?:fn|struct|enum))",  # Rust public items
        ]

        # Combine patterns
        combined_pattern = "|".join(boundary_patterns)

        # Split at boundaries
        parts = re.split(combined_pattern, text)

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            potential = current_chunk + "\n\n" + part if current_chunk else part

            if len(potential) > self.chunk_size and current_chunk:
                # Save chunk
                chunk_text = current_chunk.strip()
                if chunk_text:
                    chunk_data = {
                        "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                        "text": chunk_text,
                        "source_file": source_file,
                        "chunk_index": chunk_index,
                    }
                    # Extract dates mentioned in the chunk content
                    date_context = get_date_context(chunk_text)
                    if date_context["most_recent"]:
                        chunk_data["content_dates"] = date_context
                    # Classify chunk by relevance and category
                    chunk_data["classification"] = classify_chunk(chunk_text)
                    chunks.append(chunk_data)
                    chunk_index += 1
                current_chunk = part
            else:
                current_chunk = potential

        # Final chunk
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunk_data = {
                "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                "text": chunk_text,
                "source_file": source_file,
                "chunk_index": chunk_index,
            }
            # Extract dates mentioned in the chunk content
            date_context = get_date_context(chunk_text)
            if date_context["most_recent"]:
                chunk_data["content_dates"] = date_context
            # Classify chunk by relevance and category
            chunk_data["classification"] = classify_chunk(chunk_text)
            chunks.append(chunk_data)

        return chunks


class HeaderChunker(TextChunker):
    """Chunker for structured documents that splits by headers.

    Optimized for:
    - Product/functional/technical specifications
    - Requirements documents
    - Meeting notes with sections
    - Any Markdown or structured document

    Features:
    - Preserves section hierarchy (includes parent headers for context)
    - Larger default chunk size (2000 chars) for complete sections
    - Keeps related content together under its header
    - Adds section path metadata (e.g., "Requirements > Authentication > OAuth")
    """

    # Header patterns for different formats
    HEADER_PATTERNS = [
        (r'^(#{1,6})\s+(.+)$', 'markdown'),           # Markdown: # Header
        (r'^(.+)\n(={3,}|-{3,})$', 'underline'),      # Underline: Header\n====
        (r'^(\d+\.[\d.]*)\s+(.+)$', 'numbered'),      # Numbered: 1.2.3 Header
    ]

    def __init__(
        self,
        chunk_size: int = 2000,  # Larger for specs
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,  # Don't create tiny chunks
    ):
        super().__init__(chunk_size, chunk_overlap, separator="\n\n")
        self.min_chunk_size = min_chunk_size

    def _parse_headers(self, text: str) -> List[Tuple[int, int, str, int]]:
        """Parse all headers in the document.

        Returns:
            List of (start_pos, end_pos, header_text, level) tuples
        """
        headers = []
        lines = text.split('\n')
        pos = 0

        for i, line in enumerate(lines):
            line_start = pos
            line_end = pos + len(line)

            # Check Markdown headers: # Header
            md_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if md_match:
                level = len(md_match.group(1))
                header_text = md_match.group(2).strip()
                headers.append((line_start, line_end, header_text, level))

            # Check underline headers: Header\n====
            elif i > 0 and re.match(r'^(={3,}|-{3,})$', line.strip()):
                prev_line = lines[i-1].strip()
                if prev_line:
                    level = 1 if '=' in line else 2
                    prev_start = pos - len(lines[i-1]) - 1
                    headers.append((prev_start, line_end, prev_line, level))

            # Check numbered headers: 1.2.3 Header
            num_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line.strip())
            if num_match:
                # Level based on number depth (1 = level 1, 1.2 = level 2, etc.)
                level = num_match.group(1).count('.') + 1
                header_text = f"{num_match.group(1)} {num_match.group(2).strip()}"
                headers.append((line_start, line_end, header_text, level))

            pos = line_end + 1  # +1 for newline

        return headers

    def _build_section_path(self, headers: List[Tuple[int, int, str, int]], current_idx: int) -> str:
        """Build hierarchical section path for a header.

        Example: "Requirements > Authentication > OAuth Flow"
        """
        if current_idx < 0 or current_idx >= len(headers):
            return ""

        current_level = headers[current_idx][3]
        path_parts = [headers[current_idx][2]]

        # Walk backwards to find parent headers
        for i in range(current_idx - 1, -1, -1):
            if headers[i][3] < current_level:
                path_parts.insert(0, headers[i][2])
                current_level = headers[i][3]

        return " > ".join(path_parts)

    def chunk(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Chunk document by headers, preserving section structure.

        Each chunk includes:
        - The section header and its content
        - Section path for context (parent headers)
        - Proper metadata for retrieval
        """
        if not text or not text.strip():
            return []

        headers = self._parse_headers(text)

        # If no headers found, fall back to paragraph chunking
        if not headers:
            return super().chunk(text, source_file)

        chunks = []
        chunk_index = 0

        for i, (start, end, header_text, level) in enumerate(headers):
            # Find section end (next header of same or higher level, or EOF)
            section_end = len(text)
            for j in range(i + 1, len(headers)):
                if headers[j][3] <= level:
                    section_end = headers[j][0]
                    break

            # Extract section content
            section_content = text[start:section_end].strip()

            # Skip very small sections
            if len(section_content) < self.min_chunk_size:
                continue

            # Build section path for context
            section_path = self._build_section_path(headers, i)

            # If section is too large, split it further
            if len(section_content) > self.chunk_size:
                # Split large section by paragraphs
                sub_chunks = self._split_large_section(
                    section_content, header_text, section_path, source_file, chunk_index
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
            else:
                # Create single chunk for section
                chunk_data = {
                    "id": self._generate_chunk_id(source_file, chunk_index, section_content),
                    "text": section_content,
                    "source_file": source_file,
                    "chunk_index": chunk_index,
                    "section_header": header_text,
                    "section_path": section_path,
                    "section_level": level,
                }
                # Extract dates
                date_context = get_date_context(section_content)
                if date_context["most_recent"]:
                    chunk_data["content_dates"] = date_context
                # Classify with section metadata for better accuracy
                chunk_data["classification"] = classify_chunk(
                    section_content,
                    {"section_level": level, "section_header": header_text}
                )

                chunks.append(chunk_data)
                chunk_index += 1

        return chunks

    def _split_large_section(
        self,
        content: str,
        header: str,
        section_path: str,
        source_file: str,
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Split a large section into smaller chunks while preserving context."""
        chunks = []
        paragraphs = content.split('\n\n')

        current_chunk = ""
        chunk_index = start_index

        # Always include header in first chunk
        header_prefix = f"[Section: {section_path}]\n\n" if section_path else ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            potential = current_chunk + "\n\n" + para if current_chunk else header_prefix + para

            if len(potential) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = current_chunk.strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunk_data = {
                        "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                        "text": chunk_text,
                        "source_file": source_file,
                        "chunk_index": chunk_index,
                        "section_header": header,
                        "section_path": section_path,
                    }
                    date_context = get_date_context(chunk_text)
                    if date_context["most_recent"]:
                        chunk_data["content_dates"] = date_context
                    # Classify with section metadata
                    chunk_data["classification"] = classify_chunk(
                        chunk_text, {"section_header": header}
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                # Start new chunk with context
                current_chunk = f"[Section: {section_path}]\n\n{para}" if section_path else para
            else:
                current_chunk = potential

        # Add final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk_text = current_chunk.strip()
            chunk_data = {
                "id": self._generate_chunk_id(source_file, chunk_index, chunk_text),
                "text": chunk_text,
                "source_file": source_file,
                "chunk_index": chunk_index,
                "section_header": header,
                "section_path": section_path,
            }
            date_context = get_date_context(chunk_text)
            if date_context["most_recent"]:
                chunk_data["content_dates"] = date_context
            # Classify with section metadata
            chunk_data["classification"] = classify_chunk(
                chunk_text, {"section_header": header}
            )
            chunks.append(chunk_data)

        return chunks


def get_chunker(file_path: str) -> TextChunker:
    """Get appropriate chunker based on file extension.

    Selection logic:
    - Markdown/text docs → HeaderChunker (splits by headers, best for specs)
    - Code files → CodeChunker (respects function/class boundaries)
    - Other files → TextChunker (paragraph-based)

    Args:
        file_path: Path to the file being chunked

    Returns:
        Appropriate chunker instance for the file type
    """
    # Document types that benefit from header-aware chunking
    doc_extensions = {
        ".md", ".markdown",   # Markdown
        ".txt",               # Plain text (often has headers)
        ".rst",               # reStructuredText
    }

    # Code files that need structure-aware chunking
    code_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".rb",
        ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt",
    }

    ext = "." + file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

    if ext in doc_extensions:
        return HeaderChunker()
    elif ext in code_extensions:
        return CodeChunker()
    else:
        # For PDFs, DOCX, HTML - use TextChunker (they're already parsed to text)
        # Could enhance later with format-specific chunkers
        return TextChunker()
