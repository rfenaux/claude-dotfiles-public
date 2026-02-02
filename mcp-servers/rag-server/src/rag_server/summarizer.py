"""Document summarization for RAG.

Extracts key information from documents to create searchable summaries.
This enables "what is this document about?" style queries without reading all chunks.

Two approaches:
1. Extractive: Pull key sentences/headers from the document (fast, no LLM)
2. Abstractive: Use LLM to generate summary (better quality, slower, optional)

Currently implements extractive summarization for speed and privacy.
"""
import re
from typing import List, Dict, Any, Optional


class DocumentSummarizer:
    """Extract document summaries for improved retrieval."""

    def __init__(self, max_summary_length: int = 500):
        """Initialize summarizer.

        Args:
            max_summary_length: Maximum characters for the summary
        """
        self.max_summary_length = max_summary_length

    def summarize(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a summary of the document.

        Extracts:
        - Title (from first header or filename)
        - Key topics (from headers)
        - Brief description (from first meaningful paragraph)
        - Document type inference

        Args:
            text: Full document text
            metadata: Optional metadata (e.g., filename, file type)

        Returns:
            Summary dict with title, topics, description, doc_type
        """
        if not text or not text.strip():
            return {
                "title": metadata.get("filename", "Untitled") if metadata else "Untitled",
                "topics": [],
                "description": "",
                "doc_type": "unknown",
            }

        # Extract title
        title = self._extract_title(text, metadata)

        # Extract topics from headers
        topics = self._extract_topics(text)

        # Extract description from first paragraph
        description = self._extract_description(text)

        # Infer document type
        doc_type = self._infer_doc_type(text, topics, metadata)

        return {
            "title": title,
            "topics": topics[:10],  # Limit to top 10 topics
            "description": description,
            "doc_type": doc_type,
            "summary_text": self._build_summary_text(title, topics, description),
        }

    def _extract_title(self, text: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Extract document title."""
        lines = text.strip().split('\n')

        # Check for Markdown H1
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line.startswith('# ') and not line.startswith('##'):
                return line[2:].strip()

        # Check for underline-style header
        for i, line in enumerate(lines[:5]):
            if i > 0 and re.match(r'^={3,}$', line.strip()):
                return lines[i-1].strip()

        # Fall back to filename
        if metadata and metadata.get("filename"):
            # Clean up filename
            filename = metadata["filename"]
            # Remove extension and path
            name = filename.rsplit('/', 1)[-1].rsplit('.', 1)[0]
            # Replace underscores/hyphens with spaces
            name = re.sub(r'[-_]+', ' ', name)
            return name.title()

        # Use first non-empty line
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 10 and not line.startswith(('#', '-', '*', '>')):
                return line[:100]

        return "Untitled Document"

    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from document headers."""
        topics = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # Markdown headers (## and ###)
            md_match = re.match(r'^#{2,3}\s+(.+)$', line)
            if md_match:
                topic = md_match.group(1).strip()
                # Clean up common patterns
                topic = re.sub(r'^[\d.]+\s*', '', topic)  # Remove numbering
                if topic and len(topic) > 2:
                    topics.append(topic)

            # Numbered sections (1.2 Topic Name)
            num_match = re.match(r'^\d+(?:\.\d+)*\s+(.+)$', line)
            if num_match:
                topic = num_match.group(1).strip()
                if topic and len(topic) > 2:
                    topics.append(topic)

        # Deduplicate while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique_topics.append(topic)

        return unique_topics

    def _extract_description(self, text: str) -> str:
        """Extract a brief description from the document."""
        lines = text.strip().split('\n')

        # Skip headers and find first meaningful paragraph
        in_paragraph = False
        paragraph = []

        for line in lines:
            line = line.strip()

            # Skip headers
            if line.startswith('#') or re.match(r'^[\d.]+\s+\w', line):
                if paragraph:
                    break  # End of first paragraph
                continue

            # Skip empty lines
            if not line:
                if paragraph:
                    break  # End of paragraph
                continue

            # Skip list items at the start
            if not paragraph and re.match(r'^[-*•]\s', line):
                continue

            # Collect paragraph text
            paragraph.append(line)

            # Stop if we have enough
            if sum(len(l) for l in paragraph) > self.max_summary_length:
                break

        description = ' '.join(paragraph)

        # Truncate to max length at sentence boundary
        if len(description) > self.max_summary_length:
            # Find last sentence boundary
            truncated = description[:self.max_summary_length]
            last_period = truncated.rfind('. ')
            if last_period > self.max_summary_length // 2:
                description = truncated[:last_period + 1]
            else:
                description = truncated.rsplit(' ', 1)[0] + '...'

        return description

    def _infer_doc_type(
        self,
        text: str,
        topics: List[str],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Infer the type of document."""
        text_lower = text.lower()
        topics_lower = ' '.join(topics).lower()

        # Check for spec indicators
        spec_keywords = ['requirement', 'specification', 'functional', 'technical', 'user story']
        if any(kw in text_lower[:2000] or kw in topics_lower for kw in spec_keywords):
            if 'functional' in text_lower[:2000] or 'functional' in topics_lower:
                return 'functional_spec'
            if 'technical' in text_lower[:2000] or 'technical' in topics_lower:
                return 'technical_spec'
            return 'specification'

        # Check for meeting notes
        meeting_keywords = ['meeting', 'attendees', 'agenda', 'action items', 'minutes']
        if any(kw in text_lower[:1000] for kw in meeting_keywords):
            return 'meeting_notes'

        # Check for documentation
        doc_keywords = ['documentation', 'guide', 'tutorial', 'how to', 'getting started']
        if any(kw in text_lower[:1000] or kw in topics_lower for kw in doc_keywords):
            return 'documentation'

        # Check for project/product docs
        project_keywords = ['project', 'product', 'roadmap', 'milestone', 'deliverable']
        if any(kw in text_lower[:1000] or kw in topics_lower for kw in project_keywords):
            return 'project_doc'

        # Check for API docs
        api_keywords = ['api', 'endpoint', 'request', 'response', 'payload']
        if any(kw in text_lower[:1000] or kw in topics_lower for kw in api_keywords):
            return 'api_doc'

        # Default based on file extension
        if metadata and metadata.get("extension"):
            ext = metadata["extension"].lower()
            if ext in ['.md', '.markdown']:
                return 'markdown'
            if ext == '.pdf':
                return 'pdf'
            if ext in ['.doc', '.docx']:
                return 'word_doc'

        return 'document'

    def _build_summary_text(self, title: str, topics: List[str], description: str) -> str:
        """Build a searchable summary text combining all elements."""
        parts = [title]

        if topics:
            parts.append("Topics: " + ", ".join(topics[:5]))

        if description:
            parts.append(description)

        return "\n".join(parts)


def generate_document_summary(
    chunks: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate summary from document chunks.

    Args:
        chunks: List of chunk dictionaries with 'text' field
        metadata: Optional document metadata

    Returns:
        Summary dictionary
    """
    # Reconstruct approximate document from chunks
    # (chunks are in order by chunk_index)
    sorted_chunks = sorted(chunks, key=lambda c: c.get('chunk_index', 0))
    full_text = '\n\n'.join(c.get('text', '') for c in sorted_chunks)

    summarizer = DocumentSummarizer()
    return summarizer.summarize(full_text, metadata)
