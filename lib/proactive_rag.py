#!/usr/bin/env python3
"""
Proactive RAG Surfacing - Python Helper

Extracts CTM context, builds weighted queries, and cascades through RAG indexes
to surface relevant documents at session start.

Usage:
    python proactive_rag.py [--project /path/to/project] [--verbose]
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add CTM lib to path for shared context extractor
_ctm_lib_path = Path.home() / ".claude" / "ctm" / "lib"
if str(_ctm_lib_path) not in sys.path:
    sys.path.insert(0, str(_ctm_lib_path))

# Add scripts to path for query expansion + reranking (F8)
_scripts_path = Path.home() / ".claude" / "scripts"
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

# Use shared CTM context extractor (DRY consolidation)
from context_extractor import extract_ctm_context as extract_ctm_context_shared, CTMContext as SharedCTMContext

# Configure logging
LOG_FILE = Path.home() / ".claude" / "logs" / "proactive-memory.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)
logger = logging.getLogger(__name__)


# Alias for backwards compatibility
CTMContext = SharedCTMContext


@dataclass
class SearchResult:
    """A single RAG search result."""
    text: str
    source_file: str
    relevance: str
    category: str
    source_type: str  # "lessons", "config", "project"


@dataclass
class Config:
    """Configuration for proactive RAG."""
    enabled: bool
    max_results: int
    max_tokens: int
    cascade_order: List[str]
    min_relevance: str
    early_stop_threshold: int
    weights: Dict[str, float]


def load_config() -> Config:
    """Load configuration from proactive-rag.json."""
    config_path = Path.home() / ".claude" / "config" / "proactive-rag.json"

    defaults = Config(
        enabled=True,
        max_results=5,
        max_tokens=400,
        cascade_order=["lessons", "config", "project", "observations"],
        min_relevance="medium",
        early_stop_threshold=3,
        weights={"task_title": 3, "task_tags": 2, "decisions": 1.5, "project": 1}
    )

    if not config_path.exists():
        return defaults

    try:
        with open(config_path) as f:
            data = json.load(f)
        return Config(
            enabled=data.get("enabled", defaults.enabled),
            max_results=data.get("max_results", defaults.max_results),
            max_tokens=data.get("max_tokens", defaults.max_tokens),
            cascade_order=data.get("cascade_order", defaults.cascade_order),
            min_relevance=data.get("min_relevance", defaults.min_relevance),
            early_stop_threshold=data.get("early_stop_threshold", defaults.early_stop_threshold),
            weights=data.get("weights", defaults.weights),
        )
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        return defaults


def extract_ctm_context(project_path: Optional[str] = None) -> Optional[CTMContext]:
    """Extract context from CTM index and active agents.

    Delegates to shared context_extractor.extract_ctm_context().
    """
    context = extract_ctm_context_shared(project_path)
    if context.is_empty():
        return None
    return context


def build_weighted_query(context: CTMContext, config: Config) -> str:
    """Build a composite query with weighted terms.

    Uses CTMContext.to_query_terms() for weight-aware term extraction.
    """
    # Use shared method for weighted query terms
    terms = context.to_query_terms()

    if not terms:
        return ""

    query = " ".join(terms)
    # Limit query length
    return query[:500]


def rag_search_cascade(
    query: str,
    project_path: str,
    config: Config
) -> List[SearchResult]:
    """Search RAG indexes in cascade order."""
    results: List[SearchResult] = []
    seen_files: set = set()

    # Import RAG search function
    try:
        sys.path.insert(0, str(Path.home() / ".claude" / "mcp-servers" / "rag-server" / "src"))
        from rag_server.server import rag_search
    except ImportError as e:
        logger.error(f"Failed to import rag_search: {e}")
        return []

    # Map source types to paths
    source_paths = {
        "lessons": str(Path.home() / ".claude" / "lessons"),
        "config": str(Path.home() / ".claude"),
        "huble-wiki": str(Path.home() / "projects" / "huble-wiki"),
        "project": project_path,
        "observations": str(Path.home() / ".claude" / "observations"),
    }

    for source_type in config.cascade_order:
        if len(results) >= config.early_stop_threshold:
            logger.debug(f"Early stopping: {len(results)} results found")
            break

        source_path = source_paths.get(source_type)
        if not source_path:
            continue

        # Check if RAG is initialized for this path
        rag_dir = Path(source_path) / ".rag"
        if not rag_dir.exists():
            logger.debug(f"No RAG index at {source_path}")
            continue

        try:
            search_results = rag_search(
                query=query,
                project_path=source_path,
                top_k=2,
                min_relevance=config.min_relevance,
            )

            for r in search_results.get("results", []):
                source_file = r.get("source_file", "")

                # Deduplicate by file
                if source_file in seen_files:
                    continue
                seen_files.add(source_file)

                results.append(SearchResult(
                    text=r.get("text", "")[:200],
                    source_file=source_file,
                    relevance=r.get("relevance", "medium"),
                    category=r.get("category", "context"),
                    source_type=source_type,
                ))

        except Exception as e:
            logger.warning(f"RAG search failed for {source_type}: {e}")
            continue

    return results[:config.max_results]


def format_output(
    context: CTMContext,
    results: List[SearchResult],
    config: Config
) -> str:
    """Format results as markdown for session context."""
    if not results:
        return ""

    lines = [
        "",
        "### Proactive Context",
        "",
    ]

    if context.task_title:
        lines.append(f"**Relevant to:** {context.task_title}")
        lines.append("")

    # Group by source type
    by_source: Dict[str, List[SearchResult]] = {}
    for r in results:
        by_source.setdefault(r.source_type, []).append(r)

    source_labels = {
        "lessons": "From Lessons",
        "config": "From Config",
        "org-wiki": "From Organization Wiki",
        "project": "From Project",
        "observations": "From Observations",
    }

    for source_type in config.cascade_order:
        source_results = by_source.get(source_type, [])
        if not source_results:
            continue

        label = source_labels.get(source_type, source_type.title())
        lines.append(f"**{label}:**")

        for r in source_results:
            # Extract title from filename
            title = Path(r.source_file).stem.replace("-", " ").replace("_", " ").title()
            # Truncate summary
            summary = r.text.replace("\n", " ")[:100]
            if len(r.text) > 100:
                summary += "..."

            lines.append(f"- **{title}**: {summary}")

        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Proactive RAG Surfacing")
    parser.add_argument("--project", type=str, help="Project path", default=None)
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        # Also log to stderr for debugging
        logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))

    config = load_config()

    if not config.enabled:
        logger.info("Proactive RAG is disabled")
        return

    # Extract CTM context
    context = extract_ctm_context(args.project)
    if not context:
        logger.info("No CTM context available")
        return

    logger.info(f"CTM context: {context.task_title}, tags: {context.task_tags}")

    # Build query
    query = build_weighted_query(context, config)
    if not query.strip():
        logger.info("Empty query, skipping search")
        return

    logger.debug(f"Query: {query[:100]}...")

    # Determine project path for search
    project_path = args.project or context.project_path or os.getcwd()

    # Search with primary query
    results = rag_search_cascade(query, project_path, config)
    logger.info(f"Found {len(results)} results from primary query")

    # F8: Query expansion — if results are sparse, try expanded variants
    if len(results) < 3:
        try:
            from query_expander import expand
            expanded = expand(query)
            variants = expanded.get("variants", [])
            if variants:
                best_variant = variants[0]
                logger.info(f"Expanding query: '{best_variant}'")
                extra = rag_search_cascade(best_variant, project_path, config)
                # Deduplicate by source_file
                seen = {r.get("source_file", r.get("file", "")) for r in results}
                for r in extra:
                    key = r.get("source_file", r.get("file", ""))
                    if key and key not in seen:
                        results.append(r)
                        seen.add(key)
                logger.info(f"After expansion: {len(results)} total results")
        except ImportError:
            logger.debug("query_expander not available, skipping expansion")
        except Exception as e:
            logger.debug(f"Query expansion failed (non-fatal): {e}")

    # F8: Result reranking — improve ordering by recency + depth + cross-refs
    if len(results) > 1:
        try:
            from result_reranker import rerank
            reranked = rerank(results)
            if reranked.get("reranking_applied"):
                results = reranked["results"]
                logger.info("Results reranked successfully")
        except ImportError:
            logger.debug("result_reranker not available, skipping reranking")
        except Exception as e:
            logger.debug(f"Reranking failed (non-fatal): {e}")

    # Format and output
    output = format_output(context, results, config)
    if output:
        print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Silent exit for graceful degradation
        sys.exit(0)
