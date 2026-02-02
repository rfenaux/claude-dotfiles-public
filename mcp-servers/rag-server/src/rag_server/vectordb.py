"""LanceDB vector database operations for per-project RAG storage.

Provides two tables:
1. documents: Chunk-level storage with embeddings for semantic search
2. catalog: Document-level metadata with summaries for discovery

The catalog enables "what documents do I have about X?" queries,
while the documents table enables "find specific content about X" queries.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import lancedb
import pyarrow as pa

from .embeddings import OllamaEmbeddings
from .summarizer import DocumentSummarizer
from .chunk_classifier import apply_relevance_boost
from .temporal_boost import apply_temporal_boost

logger = logging.getLogger(__name__)

class ProjectVectorDB:
    """Per-project vector database using LanceDB.

    Tables:
    - documents: Chunk-level content with embeddings
    - catalog: Document-level summaries and metadata
    """

    TABLE_NAME = "documents"
    CATALOG_TABLE = "catalog"

    def __init__(
        self,
        project_path: str,
        embeddings: Optional[OllamaEmbeddings] = None,
    ):
        """Initialize project vector database.

        Args:
            project_path: Absolute path to project root
            embeddings: Ollama embeddings client (created if not provided)
        """
        self.project_path = Path(project_path)
        self.db_path = self.project_path / ".rag" / "vectordb"
        self.config_path = self.project_path / ".rag" / "config.json"
        self.embeddings = embeddings or OllamaEmbeddings()
        self._db: Optional[lancedb.DBConnection] = None
        self._table = None
        self._catalog = None
        self._summarizer = DocumentSummarizer()

    def _ensure_rag_dir(self):
        """Ensure .rag directory exists with gitignore."""
        rag_dir = self.project_path / ".rag"
        rag_dir.mkdir(parents=True, exist_ok=True)

        # Create gitignore to exclude vectordb but keep config
        gitignore_path = rag_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("vectordb/\nindex-log.json\n")

    @property
    def db(self) -> lancedb.DBConnection:
        """Lazy-initialize database connection."""
        if self._db is None:
            self._ensure_rag_dir()
            self._db = lancedb.connect(str(self.db_path))
        return self._db

    def _get_schema(self) -> pa.Schema:
        """Get PyArrow schema for the documents table."""
        return pa.schema([
            pa.field("id", pa.string()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), self.embeddings.dimension)),
            pa.field("source_file", pa.string()),
            pa.field("chunk_index", pa.int32()),
            pa.field("metadata", pa.string()),
            pa.field("indexed_at", pa.string()),
        ])

    def _get_catalog_schema(self) -> pa.Schema:
        """Get PyArrow schema for the catalog table (document summaries)."""
        return pa.schema([
            pa.field("source_file", pa.string()),       # Unique key
            pa.field("title", pa.string()),              # Document title
            pa.field("summary", pa.string()),            # Searchable summary text
            pa.field("vector", pa.list_(pa.float32(), self.embeddings.dimension)),  # Summary embedding
            pa.field("topics", pa.string()),             # JSON array of topics
            pa.field("doc_type", pa.string()),           # Inferred document type
            pa.field("chunk_count", pa.int32()),         # Number of chunks
            pa.field("indexed_at", pa.string()),         # When indexed
            pa.field("metadata", pa.string()),           # Additional metadata JSON
        ])

    @property
    def table(self):
        """Lazy-initialize or get the documents table."""
        if self._table is None:
            try:
                self._table = self.db.open_table(self.TABLE_NAME)
            except Exception:
                # Table doesn't exist, create it
                logger.info(f"Creating new documents table at {self.db_path}")
                self._table = self.db.create_table(
                    self.TABLE_NAME,
                    schema=self._get_schema(),
                )
        return self._table

    @property
    def catalog(self):
        """Lazy-initialize or get the catalog table (document summaries)."""
        if self._catalog is None:
            try:
                self._catalog = self.db.open_table(self.CATALOG_TABLE)
            except Exception:
                # Table doesn't exist, create it
                logger.info(f"Creating new catalog table at {self.db_path}")
                self._catalog = self.db.create_table(
                    self.CATALOG_TABLE,
                    schema=self._get_catalog_schema(),
                )
        return self._catalog

    def add_documents(self, docs: List[Dict[str, Any]]) -> int:
        """Add documents with embeddings to the database.

        Args:
            docs: List of document dicts with 'id', 'text', 'source_file', etc.

        Returns:
            Number of documents added
        """
        if not docs:
            return 0

        records = []
        indexed_at = datetime.utcnow().isoformat()

        for doc in docs:
            try:
                vector = self.embeddings.embed(doc["text"])
                # Build metadata including classification and dates
                metadata = doc.get("metadata", {})
                if "classification" in doc:
                    metadata["classification"] = doc["classification"]
                if "content_dates" in doc:
                    metadata["content_dates"] = doc["content_dates"]
                if "section_header" in doc:
                    metadata["section_header"] = doc["section_header"]
                if "section_path" in doc:
                    metadata["section_path"] = doc["section_path"]

                records.append({
                    "id": doc["id"],
                    "text": doc["text"],
                    "vector": vector,
                    "source_file": doc["source_file"],
                    "chunk_index": doc.get("chunk_index", 0),
                    "metadata": json.dumps(metadata),
                    "indexed_at": indexed_at,
                })
            except Exception as e:
                logger.error(f"Failed to embed document {doc['id']}: {e}")
                continue

        if records:
            self.table.add(records)
            logger.info(f"Added {len(records)} documents to index")

            # Update catalog with document summary
            self._update_catalog_for_documents(docs, records)

        return len(records)

    def _update_catalog_for_documents(
        self,
        original_docs: List[Dict[str, Any]],
        indexed_records: List[Dict[str, Any]]
    ):
        """Update catalog with summary for newly indexed documents.

        Args:
            original_docs: Original chunk dicts with text and metadata
            indexed_records: Records that were added to documents table
        """
        if not indexed_records:
            return

        # Group by source file
        docs_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for doc in original_docs:
            source = doc.get("source_file", "unknown")
            if source not in docs_by_source:
                docs_by_source[source] = []
            docs_by_source[source].append(doc)

        indexed_at = datetime.utcnow().isoformat()

        for source_file, chunks in docs_by_source.items():
            try:
                # Generate summary from all chunks of this document
                full_text = '\n\n'.join(
                    c.get('text', '') for c in sorted(chunks, key=lambda x: x.get('chunk_index', 0))
                )
                metadata = chunks[0].get('metadata', {}) if chunks else {}
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}

                # Add filename to metadata for summarizer
                metadata['filename'] = source_file

                # Generate summary
                summary = self._summarizer.summarize(full_text, metadata)

                # Generate embedding for summary text
                summary_text = summary.get('summary_text', '')
                if summary_text:
                    try:
                        summary_vector = self.embeddings.embed(summary_text)
                    except Exception as e:
                        logger.warning(f"Failed to embed summary for {source_file}: {e}")
                        summary_vector = [0.0] * self.embeddings.dimension
                else:
                    summary_vector = [0.0] * self.embeddings.dimension

                # Delete existing catalog entry
                try:
                    self.catalog.delete(f"source_file = '{source_file}'")
                except Exception:
                    pass  # May not exist

                # Add to catalog
                catalog_record = {
                    "source_file": source_file,
                    "title": summary.get('title', source_file),
                    "summary": summary_text,
                    "vector": summary_vector,
                    "topics": json.dumps(summary.get('topics', [])),
                    "doc_type": summary.get('doc_type', 'document'),
                    "chunk_count": len(chunks),
                    "indexed_at": indexed_at,
                    "metadata": json.dumps(metadata),
                }
                self.catalog.add([catalog_record])
                logger.info(f"Updated catalog for {source_file}: {summary.get('title')}")

            except Exception as e:
                logger.error(f"Failed to update catalog for {source_file}: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        apply_boost: bool = True,
        apply_temporal: bool = True
    ) -> List[Dict[str, Any]]:
        """Semantic search using query embedding.

        Args:
            query: Search query text
            top_k: Number of results to return
            apply_boost: Whether to apply relevance boosting (default True)
            apply_temporal: Whether to apply temporal boosting - prefers newer
                content and penalizes superseded content (default True)

        Returns:
            List of matching documents with scores, dates, and classification
        """
        try:
            query_vector = self.embeddings.embed(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []

        try:
            # Fetch extra results to account for re-ranking
            fetch_k = top_k * 2 if apply_boost else top_k
            results = (
                self.table
                .search(query_vector)
                .limit(fetch_k)
                .to_list()
            )

            formatted_results = []
            for r in results:
                metadata = json.loads(r.get("metadata", "{}"))

                # Format modification date if available
                modified_date = None
                if "modified" in metadata:
                    try:
                        modified_date = datetime.fromtimestamp(metadata["modified"]).strftime("%Y-%m-%d")
                    except:
                        pass

                # Extract content dates (dates mentioned within the text)
                content_dates = metadata.get("content_dates", {})
                content_date = content_dates.get("most_recent") if content_dates else None

                # Determine the most relevant date for this chunk
                # Prefer content date over file date as it represents what the text discusses
                relevant_date = content_date or modified_date

                # Extract classification info
                classification = metadata.get("classification", {})

                formatted_results.append({
                    "id": r["id"],
                    "text": r["text"],
                    "source_file": r["source_file"],
                    "chunk_index": r["chunk_index"],
                    "score": float(r.get("_distance", 0)),
                    "file_date": modified_date,  # When file was last modified
                    "content_date": content_date,  # Most recent date mentioned in text
                    "relevant_date": relevant_date,  # Best date to use for chronology
                    "date_range": content_dates.get("date_range") if content_dates else None,
                    # Classification fields
                    "relevance": classification.get("relevance", "medium"),
                    "category": classification.get("category", "context"),
                    "custom_tags": classification.get("custom_tags", []),
                    "metadata": metadata,
                })

            # Apply relevance boosting and re-sort
            if apply_boost:
                formatted_results = apply_relevance_boost(formatted_results)

            # Apply temporal boosting (newer content ranks higher, superseded ranks lower)
            if apply_temporal:
                formatted_results = apply_temporal_boost(formatted_results)

            return formatted_results[:top_k]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_by_source(self, source_file: str) -> int:
        """Remove all chunks from a specific source file.

        Args:
            source_file: Path to source file to remove

        Returns:
            Number of documents removed (approximate)
        """
        try:
            # Check if table exists and has data
            if self._table is None:
                # Try to get table, but don't fail if it doesn't exist
                try:
                    _ = self.table
                except Exception:
                    return 0  # No table yet, nothing to delete

            # Count before delete
            try:
                df = self.table.to_pandas()
            except Exception:
                return 0  # Table empty or corrupted, nothing to delete

            if df.empty:
                return 0

            count_before = len(df[df["source_file"] == source_file])

            if count_before > 0:
                self.table.delete(f"source_file = '{source_file}'")
                logger.info(f"Deleted {count_before} chunks from {source_file}")

            return count_before
        except Exception as e:
            # Don't log as error for expected "not found" cases
            if "Not found" not in str(e):
                logger.error(f"Delete failed: {e}")
            return 0

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents with summaries.

        Returns:
            List of documents with chunk counts, summaries, and metadata
        """
        try:
            # Get documents from catalog (includes summaries)
            try:
                catalog_df = self.catalog.to_pandas()
                if not catalog_df.empty:
                    return [
                        {
                            "source_file": row["source_file"],
                            "title": row.get("title", row["source_file"]),
                            "summary": row.get("summary", ""),
                            "topics": json.loads(row.get("topics", "[]")),
                            "doc_type": row.get("doc_type", "document"),
                            "chunk_count": int(row.get("chunk_count", 0)),
                            "indexed_at": row.get("indexed_at", ""),
                        }
                        for _, row in catalog_df.iterrows()
                    ]
            except Exception:
                pass  # Catalog may not exist yet

            # Fallback to documents table if catalog empty/missing
            df = self.table.to_pandas()
            if df.empty:
                return []

            # Group by source file
            grouped = df.groupby("source_file").agg({
                "id": "count",
                "indexed_at": "first",
            }).reset_index()

            return [
                {
                    "source_file": row["source_file"],
                    "title": row["source_file"].rsplit('/', 1)[-1],
                    "chunk_count": int(row["id"]),
                    "indexed_at": row["indexed_at"],
                }
                for _, row in grouped.iterrows()
            ]
        except Exception as e:
            logger.error(f"List failed: {e}")
            return []

    def search_catalog(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search document summaries to find relevant documents.

        Use this for "what documents do I have about X?" queries.
        Returns document-level results, not chunks.

        Args:
            query: Natural language query
            top_k: Number of documents to return

        Returns:
            List of matching documents with summaries
        """
        try:
            query_vector = self.embeddings.embed(query)
        except Exception as e:
            logger.error(f"Failed to embed catalog query: {e}")
            return []

        try:
            results = (
                self.catalog
                .search(query_vector)
                .limit(top_k)
                .to_list()
            )

            return [
                {
                    "source_file": r["source_file"],
                    "title": r.get("title", r["source_file"]),
                    "summary": r.get("summary", ""),
                    "topics": json.loads(r.get("topics", "[]")),
                    "doc_type": r.get("doc_type", "document"),
                    "chunk_count": int(r.get("chunk_count", 0)),
                    "score": float(r.get("_distance", 0)),
                    "indexed_at": r.get("indexed_at", ""),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Catalog search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dict with index statistics
        """
        try:
            df = self.table.to_pandas()
            unique_files = df["source_file"].nunique() if not df.empty else 0

            return {
                "project_path": str(self.project_path),
                "db_path": str(self.db_path),
                "total_chunks": len(df),
                "unique_files": unique_files,
                "embedding_model": self.embeddings.model,
                "embedding_dimension": self.embeddings.dimension,
                "index_exists": True,
            }
        except Exception as e:
            return {
                "project_path": str(self.project_path),
                "db_path": str(self.db_path),
                "total_chunks": 0,
                "unique_files": 0,
                "embedding_model": self.embeddings.model,
                "embedding_dimension": self.embeddings.dimension,
                "index_exists": False,
                "error": str(e),
            }

    def save_config(self, config: Dict[str, Any]):
        """Save RAG configuration."""
        self._ensure_rag_dir()
        self.config_path.write_text(json.dumps(config, indent=2))

    def load_config(self) -> Dict[str, Any]:
        """Load RAG configuration."""
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {}

    def clear(self):
        """Clear all documents and catalog from the index."""
        import shutil
        try:
            # Close connections FIRST to release file locks
            self._table = None
            self._catalog = None
            self._db = None

            # Now remove the directory
            if self.db_path.exists():
                shutil.rmtree(self.db_path)

            logger.info(f"Cleared index and catalog at {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self._db is not None:
            self._db = None
            self._table = None
