"""MCP RAG Server - Semantic document search for Claude Code.

Uses Ollama embeddings + LanceDB for local, private document search.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .embeddings import OllamaEmbeddings
from .vectordb import ProjectVectorDB
from .chunking import get_chunker
from .parsers import parse_file, get_parser

# Configure logging (never use print for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("rag-server")

# Global embeddings client (shared across requests)
_embeddings: Optional[OllamaEmbeddings] = None


def get_embeddings() -> OllamaEmbeddings:
    """Get or create shared embeddings client."""
    global _embeddings
    if _embeddings is None:
        model = os.environ.get("OLLAMA_MODEL", "mxbai-embed-large")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        _embeddings = OllamaEmbeddings(model=model, base_url=base_url)
    return _embeddings


def get_project_config(project_path: str) -> dict:
    """Get project's RAG configuration."""
    config_path = Path(project_path) / ".rag" / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            pass
    return {"backend": "rag", "version": "1.0"}


def save_project_config(project_path: str, config: dict):
    """Save project's RAG configuration."""
    rag_dir = Path(project_path) / ".rag"
    rag_dir.mkdir(parents=True, exist_ok=True)
    config_path = rag_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2))


def get_db(project_path: str) -> ProjectVectorDB:
    """Get vector database for a project."""
    return ProjectVectorDB(project_path, embeddings=get_embeddings())


@mcp.tool()
def rag_backends() -> dict:
    """
    List available RAG backends and their status.

    Returns information about which backends are available on this system:
    - 'rag': Traditional RAG with Ollama embeddings (always available if Ollama running)

    Returns:
        Dictionary with available backends and their status
    """
    embeddings = get_embeddings()
    ollama_available = embeddings.is_available()
    ollama_model = embeddings.ensure_model() if ollama_available else False

    return {
        "success": True,
        "backends": {
            "rag": {
                "available": ollama_available and ollama_model,
                "description": "RAG with Ollama embeddings + LanceDB",
                "ollama_running": ollama_available,
                "embedding_model": embeddings.model if ollama_available else None,
            },
        },
        "recommendation": "rag",
    }


@mcp.tool()
def rag_init(project_path: str, backend: str = "rag") -> dict:
    """
    Initialize RAG for a project.

    Creates the .rag directory and configures the backend.

    Args:
        project_path: Absolute path to the project root directory
        backend: Backend to use (currently only 'rag' is supported)

    Returns:
        Confirmation of initialization
    """
    try:
        project = Path(project_path)
        if not project.exists():
            return {
                "success": False,
                "error": f"Project path does not exist: {project_path}",
            }

        embeddings = get_embeddings()
        rag_available = embeddings.is_available() and embeddings.ensure_model()

        if not rag_available:
            return {
                "success": False,
                "error": "Ollama not running or embedding model not available. Start Ollama first.",
            }

        # Initialize the project
        rag_dir = project / ".rag"
        rag_dir.mkdir(parents=True, exist_ok=True)

        # Create gitignore
        gitignore = rag_dir / ".gitignore"
        gitignore.write_text("vectordb/\nindex-log.json\n")

        # Create config
        config = {
            "version": "1.0",
            "backend": "rag",
            "embedding_model": embeddings.model,
            "chunk_size": 1000,
            "chunk_overlap": 200,
        }

        save_project_config(project_path, config)

        # Register project in dashboard registry (store full info for permission-free access)
        try:
            registry_file = Path.home() / ".claude" / "rag-projects.json"
            if registry_file.exists():
                registry = json.loads(registry_file.read_text())
            else:
                registry = {"projects": []}

            # Check if already registered
            existing_paths = [p.get("path") if isinstance(p, dict) else p for p in registry["projects"]]
            if project_path not in existing_paths:
                registry["projects"].append({
                    "path": project_path,
                    "name": project.name,
                    "backend": "rag"
                })
                registry_file.write_text(json.dumps(registry, indent=2))
        except Exception as reg_error:
            logger.warning(f"Could not register project: {reg_error}")

        return {
            "success": True,
            "message": "RAG initialized",
            "backend": "rag",
            "rag_directory": str(rag_dir),
            "config": config,
        }

    except Exception as e:
        logger.error(f"Init failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def rag_search(
    query: str,
    project_path: str,
    top_k: int = 5,
    category: str = None,
    min_relevance: str = None,
) -> dict:
    """
    Semantic search across indexed documents in a project.

    Uses Ollama embeddings to find the most relevant document chunks.
    Results include classification metadata (relevance, category) and are
    boosted by relevance level (critical/high chunks rank higher).

    Args:
        query: Natural language search query (e.g., "how does authentication work")
        project_path: Absolute path to the project root directory
        top_k: Number of results to return (default: 5, max: 20)
        category: Filter by category (decision, requirement, business_strategy,
                  business_process, technical, constraint, risk, action_item, context)
        min_relevance: Minimum relevance level (critical, high, medium, low, reference)

    Returns:
        Dictionary with search results containing matched text, sources, and classification
    """
    try:
        top_k = min(max(1, top_k), 20)
        db = get_db(project_path)

        # Fetch more results if filtering
        fetch_k = top_k * 3 if (category or min_relevance) else top_k
        results = db.search(query, top_k=fetch_k)

        # Apply category filter
        if category:
            results = [r for r in results if r.get("category") == category]

        # Apply relevance filter
        if min_relevance:
            relevance_order = ["critical", "high", "medium", "low", "reference"]
            if min_relevance in relevance_order:
                min_idx = relevance_order.index(min_relevance)
                results = [
                    r for r in results
                    if relevance_order.index(r.get("relevance", "medium")) <= min_idx
                ]

        # Limit to requested count
        results = results[:top_k]

        return {
            "success": True,
            "backend": "rag",
            "query": query,
            "project_path": project_path,
            "result_count": len(results),
            "filters_applied": {
                "category": category,
                "min_relevance": min_relevance,
            } if (category or min_relevance) else None,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "project_path": project_path,
        }


@mcp.tool()
def rag_index(path: str, project_path: str) -> dict:
    """
    Index a file or folder into the project's RAG database.

    Parses files, chunks them, generates embeddings, and stores in LanceDB.
    Supports PDF, DOCX, MD, HTML, TXT, and code files.

    Args:
        path: Absolute path to file or folder to index
        project_path: Absolute path to the project root directory

    Returns:
        Summary of indexed documents
    """
    try:
        target_path = Path(path)

        if not target_path.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {path}",
            }

        # Collect files to index
        files_to_index = []
        if target_path.is_file():
            files_to_index = [target_path]
        else:
            skip_dirs = {
                ".git", ".rag", "node_modules", "__pycache__",
                ".venv", "venv", ".env", "dist", "build",
                ".next", ".nuxt", "coverage", ".pytest_cache",
            }
            for root, dirs, files in os.walk(target_path):
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                for file in files:
                    if file.startswith("."):
                        continue
                    file_path = Path(root) / file
                    if get_parser(file_path) is not None:
                        files_to_index.append(file_path)

        if not files_to_index:
            return {
                "success": True,
                "message": "No supported files found to index",
                "files_indexed": 0,
            }

        db = get_db(project_path)
        indexed_files = []
        errors = []
        total_chunks = 0

        for file_path in files_to_index:
            try:
                content, metadata = parse_file(file_path)
                if not content.strip():
                    continue
                rel_path = str(file_path.relative_to(project_path) if file_path.is_relative_to(project_path) else file_path)
                db.delete_by_source(rel_path)
                chunker = get_chunker(str(file_path))
                chunks = chunker.chunk(content, rel_path)
                for chunk in chunks:
                    # Merge file metadata with chunk-level metadata
                    chunk_content_dates = chunk.get("content_dates")
                    chunk_classification = chunk.get("classification")
                    chunk["metadata"] = {**metadata}
                    if chunk_content_dates:
                        chunk["metadata"]["content_dates"] = chunk_content_dates
                    if chunk_classification:
                        chunk["metadata"]["classification"] = chunk_classification
                added = db.add_documents(chunks)
                total_chunks += added
                indexed_files.append({"file": rel_path, "chunks": added})
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                errors.append({"file": str(file_path), "error": str(e)})

        return {
            "success": True,
            "backend": "rag",
            "files_indexed": len(indexed_files),
            "chunks_created": total_chunks,
            "indexed_files": indexed_files,
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Index operation failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def rag_list(project_path: str) -> dict:
    """
    List all indexed documents in a project.

    Shows all files that have been indexed with chunk counts.

    Args:
        project_path: Absolute path to the project root directory

    Returns:
        List of indexed documents with metadata
    """
    try:
        db = get_db(project_path)
        documents = db.list_documents()

        return {
            "success": True,
            "backend": "rag",
            "project_path": project_path,
            "document_count": len(documents),
            "documents": documents,
        }
    except Exception as e:
        logger.error(f"List failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_path": project_path,
        }


@mcp.tool()
def rag_remove(source_file: str, project_path: str) -> dict:
    """
    Remove a document from the project's RAG index.

    Args:
        source_file: Relative path to the source file to remove
        project_path: Absolute path to the project root directory

    Returns:
        Confirmation of removal
    """
    try:
        db = get_db(project_path)
        removed_count = db.delete_by_source(source_file)
        return {
            "success": True,
            "backend": "rag",
            "source_file": source_file,
            "chunks_removed": removed_count,
        }

    except Exception as e:
        logger.error(f"Remove failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "source_file": source_file,
        }


@mcp.tool()
def rag_reindex(project_path: str) -> dict:
    """
    Clear and re-index entire project.

    Removes existing index and re-indexes all supported files in the project.
    Useful when you want a fresh index or after significant changes.

    Args:
        project_path: Absolute path to the project root directory

    Returns:
        Summary of re-indexing operation
    """
    try:
        project = Path(project_path)
        if not project.exists():
            return {"success": False, "error": f"Project path does not exist: {project_path}"}

        # Clear existing index
        db = get_db(project_path)
        db.clear()
        logger.info(f"Cleared existing index for {project_path}")

        # Re-index the entire project
        result = rag_index(project_path, project_path)

        return {
            "success": result.get("success", False),
            "backend": "rag",
            "action": "reindex",
            "cleared": True,
            "files_indexed": result.get("files_indexed", 0),
            "chunks_created": result.get("chunks_created", 0),
            "errors": result.get("errors"),
        }

    except Exception as e:
        logger.error(f"Re-index failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_path": project_path,
        }


@mcp.tool()
def rag_status(project_path: str) -> dict:
    """
    Get status and statistics of the project's RAG index.

    Shows document count, chunk count, and Ollama status.

    Args:
        project_path: Absolute path to the project root directory

    Returns:
        Index statistics and configuration
    """
    try:
        config = get_project_config(project_path)
        db = get_db(project_path)
        stats = db.get_stats()
        embeddings = get_embeddings()
        stats.update({
            "ollama_available": embeddings.is_available(),
            "model_available": embeddings.ensure_model() if embeddings.is_available() else False,
            "success": True,
            "config": config,
        })

        return stats

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_path": project_path,
        }


def main():
    """Run the MCP server."""
    logger.info("Starting RAG server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
