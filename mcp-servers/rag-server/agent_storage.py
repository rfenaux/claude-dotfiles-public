#!/usr/bin/env python3
"""
Per-Agent Embedding Storage

Provides isolated SQLite databases for agent-specific embeddings.
Prevents cross-contamination between agents.

Part of: OpenClaw-inspired improvements (Phase 4, F15)
Created: 2026-01-30
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentStoreConfig:
    """Configuration for agent embedding store."""
    base_dir: str = "~/.claude/rag/agents"
    global_dir: str = "~/.claude/rag/global"
    vector_dimensions: int = 1024  # Default for mxbai-embed-large


class AgentEmbeddingStore:
    """
    Per-agent embedding storage using SQLite.

    Each agent gets its own isolated database file to prevent
    cross-contamination of embeddings and search results.
    """

    def __init__(
        self,
        agent_id: str,
        config: Optional[AgentStoreConfig] = None
    ):
        """
        Initialize store for an agent.

        Args:
            agent_id: Unique agent identifier
            config: Optional configuration
        """
        self.agent_id = agent_id
        self.config = config or AgentStoreConfig()
        self.base_dir = Path(self.config.base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.base_dir / f"{agent_id}.sqlite"
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        self._conn = sqlite3.connect(str(self.db_path))
        cursor = self._conn.cursor()

        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at REAL DEFAULT (julianday('now')),
                UNIQUE(source_file, chunk_index)
            )
        """)

        # Create embeddings table (store as JSON blob for portability)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                document_id INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        # Create indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_file ON documents(source_file)
        """)

        self._conn.commit()
        logger.debug(f"Initialized agent store: {self.db_path}")

    @property
    def conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
        return self._conn

    def add_document(
        self,
        source_file: str,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a document chunk with its embedding.

        Args:
            source_file: Source file path
            chunk_index: Index of chunk within file
            content: Text content
            embedding: Vector embedding
            metadata: Optional metadata dict

        Returns:
            Document ID
        """
        cursor = self.conn.cursor()

        # Insert or replace document
        cursor.execute("""
            INSERT OR REPLACE INTO documents (source_file, chunk_index, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (source_file, chunk_index, content, json.dumps(metadata or {})))

        doc_id = cursor.lastrowid

        # Insert embedding
        cursor.execute("""
            INSERT OR REPLACE INTO embeddings (document_id, embedding)
            VALUES (?, ?)
        """, (doc_id, json.dumps(embedding)))

        self.conn.commit()
        return doc_id

    def add_documents_batch(
        self,
        documents: List[Tuple[str, int, str, List[float], Optional[Dict]]]
    ) -> List[int]:
        """
        Add multiple documents in a batch.

        Args:
            documents: List of (source_file, chunk_index, content, embedding, metadata)

        Returns:
            List of document IDs
        """
        doc_ids = []
        cursor = self.conn.cursor()

        for source_file, chunk_index, content, embedding, metadata in documents:
            cursor.execute("""
                INSERT OR REPLACE INTO documents (source_file, chunk_index, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (source_file, chunk_index, content, json.dumps(metadata or {})))

            doc_id = cursor.lastrowid
            doc_ids.append(doc_id)

            cursor.execute("""
                INSERT OR REPLACE INTO embeddings (document_id, embedding)
                VALUES (?, ?)
            """, (doc_id, json.dumps(embedding)))

        self.conn.commit()
        logger.info(f"Added {len(doc_ids)} documents to agent {self.agent_id}")
        return doc_ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using cosine similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of results with score, content, source_file, metadata
        """
        cursor = self.conn.cursor()

        # Get all embeddings (for small stores, brute force is fine)
        cursor.execute("""
            SELECT d.id, d.content, d.source_file, d.chunk_index, d.metadata, e.embedding
            FROM documents d
            JOIN embeddings e ON d.id = e.document_id
        """)

        results = []
        for row in cursor.fetchall():
            doc_id, content, source_file, chunk_index, metadata_json, emb_json = row
            doc_embedding = json.loads(emb_json)

            # Calculate cosine similarity
            score = self._cosine_similarity(query_embedding, doc_embedding)

            results.append({
                "id": doc_id,
                "score": score,
                "content": content,
                "source_file": source_file,
                "chunk_index": chunk_index,
                "metadata": json.loads(metadata_json) if metadata_json else {}
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def remove_source(self, source_file: str) -> int:
        """
        Remove all chunks from a source file.

        Args:
            source_file: Source file path

        Returns:
            Number of documents removed
        """
        cursor = self.conn.cursor()

        # Get document IDs
        cursor.execute("""
            SELECT id FROM documents WHERE source_file = ?
        """, (source_file,))
        doc_ids = [row[0] for row in cursor.fetchall()]

        if not doc_ids:
            return 0

        # Delete embeddings
        cursor.execute(f"""
            DELETE FROM embeddings WHERE document_id IN ({','.join('?' * len(doc_ids))})
        """, doc_ids)

        # Delete documents
        cursor.execute("""
            DELETE FROM documents WHERE source_file = ?
        """, (source_file,))

        self.conn.commit()
        logger.info(f"Removed {len(doc_ids)} documents from source {source_file}")
        return len(doc_ids)

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all indexed source files."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT source_file, COUNT(*) as chunk_count
            FROM documents
            GROUP BY source_file
        """)

        return [
            {"source_file": row[0], "chunk_count": row[1]}
            for row in cursor.fetchall()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT source_file) FROM documents")
        source_count = cursor.fetchone()[0]

        file_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            "agent_id": self.agent_id,
            "document_count": doc_count,
            "source_count": source_count,
            "database_size_bytes": file_size,
            "database_path": str(self.db_path)
        }

    def clear(self):
        """Clear all data from the store."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM embeddings")
        cursor.execute("DELETE FROM documents")
        self.conn.commit()
        logger.info(f"Cleared all data from agent {self.agent_id}")

    def delete(self):
        """Delete the entire database file."""
        if self._conn:
            self._conn.close()
            self._conn = None

        if self.db_path.exists():
            self.db_path.unlink()
            logger.info(f"Deleted agent store: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class GlobalEmbeddingStore(AgentEmbeddingStore):
    """
    Global embedding store for shared knowledge.

    Used for lessons learned, documentation, and other
    content that should be accessible to all agents.
    """

    def __init__(self, config: Optional[AgentStoreConfig] = None):
        config = config or AgentStoreConfig()
        global_dir = Path(config.global_dir).expanduser()
        global_dir.mkdir(parents=True, exist_ok=True)

        # Use a special "global" agent ID
        super().__init__("_global_", config)
        # Override the path to use global directory
        self.db_path = global_dir / "embeddings.sqlite"
        self._init_db()


# Store registry
_stores: Dict[str, AgentEmbeddingStore] = {}


def get_agent_store(agent_id: str) -> AgentEmbeddingStore:
    """
    Get or create an agent's embedding store.

    Args:
        agent_id: Unique agent identifier

    Returns:
        AgentEmbeddingStore instance
    """
    if agent_id not in _stores:
        _stores[agent_id] = AgentEmbeddingStore(agent_id)
    return _stores[agent_id]


def get_global_store() -> GlobalEmbeddingStore:
    """Get the global embedding store."""
    if "_global_" not in _stores:
        _stores["_global_"] = GlobalEmbeddingStore()
    return _stores["_global_"]


def list_agent_stores() -> List[str]:
    """List all existing agent stores."""
    config = AgentStoreConfig()
    base_dir = Path(config.base_dir).expanduser()

    if not base_dir.exists():
        return []

    return [
        f.stem for f in base_dir.glob("*.sqlite")
        if not f.stem.startswith("_")
    ]


def cleanup_agent_store(agent_id: str):
    """Clean up an agent's store when the agent is deleted."""
    if agent_id in _stores:
        _stores[agent_id].delete()
        del _stores[agent_id]
    else:
        store = AgentEmbeddingStore(agent_id)
        store.delete()


if __name__ == "__main__":
    import sys

    print("Per-Agent Embedding Storage")
    print("=" * 40)

    # List existing stores
    stores = list_agent_stores()
    print(f"Existing agent stores: {len(stores)}")
    for agent_id in stores:
        store = get_agent_store(agent_id)
        stats = store.get_stats()
        print(f"  {agent_id}: {stats['document_count']} docs, {stats['database_size_bytes']} bytes")
        store.close()

    # Check global store
    global_store = get_global_store()
    global_stats = global_store.get_stats()
    print(f"\nGlobal store: {global_stats['document_count']} docs")
    global_store.close()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "create" and len(sys.argv) >= 3:
            agent_id = sys.argv[2]
            store = get_agent_store(agent_id)
            print(f"\n✓ Created store for agent: {agent_id}")
            print(f"  Path: {store.db_path}")
            store.close()

        elif cmd == "delete" and len(sys.argv) >= 3:
            agent_id = sys.argv[2]
            cleanup_agent_store(agent_id)
            print(f"\n✓ Deleted store for agent: {agent_id}")

        elif cmd == "stats" and len(sys.argv) >= 3:
            agent_id = sys.argv[2]
            store = get_agent_store(agent_id)
            stats = store.get_stats()
            print(f"\nStats for {agent_id}:")
            for k, v in stats.items():
                print(f"  {k}: {v}")
            store.close()

        else:
            print("\nUsage:")
            print("  agent_storage.py create <agent_id>")
            print("  agent_storage.py delete <agent_id>")
            print("  agent_storage.py stats <agent_id>")
