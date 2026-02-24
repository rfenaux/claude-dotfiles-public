#!/usr/bin/env python3
"""
Result Reranker for RAG Search
Heuristic-based reranking of search results using recency, depth, and cross-references.

Usage:
    python3 result_reranker.py < results.json
    python3 result_reranker.py --test
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def load_config() -> Dict:
    """Load RAG retrieval configuration."""
    config_path = Path.home() / ".claude" / "config" / "rag-retrieval.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {
        "reranking": {
            "enabled": True,
            "weights": {
                "recency": 0.4,
                "depth_relevance": 0.3,
                "cross_refs": 0.3
            },
            "recency_tiers": {
                "fresh_days": 7,
                "recent_days": 30,
                "stale_days": 90
            }
        }
    }


def calculate_recency_score(file_path: str, recency_tiers: Dict) -> float:
    """
    Calculate recency score based on file modification time.

    Args:
        file_path: Path to the source file
        recency_tiers: Configuration dict with fresh_days, recent_days, stale_days

    Returns:
        Score between 0.0 and 1.0
    """
    try:
        # Expand user home directory
        expanded_path = os.path.expanduser(file_path)

        # Get file modification time
        if not os.path.exists(expanded_path):
            return 0.2  # Default for missing files

        mtime = os.path.getmtime(expanded_path)
        file_date = datetime.fromtimestamp(mtime)
        now = datetime.now()
        age_days = (now - file_date).days

        # Apply tier-based scoring
        fresh_days = recency_tiers.get("fresh_days", 7)
        recent_days = recency_tiers.get("recent_days", 30)
        stale_days = recency_tiers.get("stale_days", 90)

        if age_days < fresh_days:
            return 1.0
        elif age_days < recent_days:
            return 0.7
        elif age_days < stale_days:
            return 0.4
        else:
            return 0.2

    except Exception:
        # If we can't determine, use middle score
        return 0.4


def calculate_depth_relevance_score(text: str) -> float:
    """
    Calculate depth relevance score based on text length.
    Shorter, more specific text snippets score higher.

    Args:
        text: The matched text snippet

    Returns:
        Score between 0.0 and 1.0
    """
    text_len = len(text)

    if text_len < 200:
        return 1.0  # Very specific section/snippet
    elif text_len < 500:
        return 0.7  # Medium section
    elif text_len < 1000:
        return 0.4  # Large section
    else:
        return 0.2  # Whole file summary


def calculate_cross_refs_score(source_file: str, all_results: List[Dict]) -> float:
    """
    Calculate cross-reference score by counting how many other results
    reference this result's source file.

    Args:
        source_file: The source file path for this result
        all_results: List of all search results

    Returns:
        Score between 0.0 and 1.0
    """
    ref_count = 0

    # Normalize source file path for comparison
    normalized_source = os.path.normpath(os.path.expanduser(source_file))

    for result in all_results:
        result_source = os.path.normpath(os.path.expanduser(result.get("source_file", "")))

        # Skip self-reference
        if result_source == normalized_source:
            continue

        # Check if this result's text mentions our source file
        text = result.get("text", "")
        if normalized_source in text or source_file in text:
            ref_count += 1

        # Also check metadata fields that might contain references
        metadata = result.get("metadata", {})
        if isinstance(metadata, dict):
            for value in metadata.values():
                if isinstance(value, str) and (normalized_source in value or source_file in value):
                    ref_count += 1
                    break

    # Normalize score
    if ref_count == 0:
        return 0.0
    elif ref_count == 1:
        return 0.5
    else:
        return 1.0


def calculate_composite_score(result: Dict, all_results: List[Dict], weights: Dict, recency_tiers: Dict) -> float:
    """
    Calculate composite score for a result using weighted factors.

    Args:
        result: Individual search result
        all_results: List of all results (for cross-ref calculation)
        weights: Weight configuration dict
        recency_tiers: Recency tier configuration

    Returns:
        Composite score between 0.0 and 1.0
    """
    source_file = result.get("source_file", "")
    text = result.get("text", "")

    # Calculate individual scores
    recency = calculate_recency_score(source_file, recency_tiers)
    depth_rel = calculate_depth_relevance_score(text)
    cross_refs = calculate_cross_refs_score(source_file, all_results)

    # Apply weights
    w_recency = weights.get("recency", 0.4)
    w_depth = weights.get("depth_relevance", 0.3)
    w_cross = weights.get("cross_refs", 0.3)

    composite = (
        recency * w_recency +
        depth_rel * w_depth +
        cross_refs * w_cross
    )

    return composite


def rerank(results: List[Dict], config: Optional[Dict] = None) -> Dict:
    """
    Rerank search results using heuristic scoring.

    Args:
        results: List of search results to rerank
        config: Optional configuration override

    Returns:
        Dict with reranked results, flag, and method
    """
    if config is None:
        config = load_config()

    reranking_config = config.get("reranking", {})

    # Check if reranking is enabled
    if not reranking_config.get("enabled", True):
        return {
            "results": results,
            "reranking_applied": False,
            "method": "disabled"
        }

    # Handle empty results
    if not results:
        return {
            "results": [],
            "reranking_applied": False,
            "method": "empty_input"
        }

    weights = reranking_config.get("weights", {
        "recency": 0.4,
        "depth_relevance": 0.3,
        "cross_refs": 0.3
    })

    recency_tiers = reranking_config.get("recency_tiers", {
        "fresh_days": 7,
        "recent_days": 30,
        "stale_days": 90
    })

    # Calculate scores and add to results
    scored_results = []
    for result in results:
        score = calculate_composite_score(result, results, weights, recency_tiers)
        result_with_score = result.copy()
        result_with_score["rerank_score"] = round(score, 4)
        scored_results.append(result_with_score)

    # Sort by composite score (descending)
    reranked = sorted(scored_results, key=lambda x: x["rerank_score"], reverse=True)

    return {
        "results": reranked,
        "reranking_applied": True,
        "method": "heuristic"
    }


def run_test():
    """Run built-in test with sample data."""
    # Create test data
    test_results = [
        {
            "text": "Short specific section about authentication workflow",
            "source_file": "~/.claude/docs/AUTH.md",
            "relevance": "high",
            "category": "documentation",
            "source_type": "markdown"
        },
        {
            "text": "Very long comprehensive document covering many topics including authentication, authorization, sessions, tokens, OAuth flows, security best practices, and much more detailed information across multiple sections totaling over 1000 characters of content",
            "source_file": "~/.claude/docs/SECURITY_GUIDE.md",
            "relevance": "medium",
            "category": "documentation",
            "source_type": "markdown"
        },
        {
            "text": "Medium length section discussing OAuth implementation. References AUTH.md for details.",
            "source_file": "~/.claude/docs/OAUTH.md",
            "relevance": "high",
            "category": "documentation",
            "source_type": "markdown"
        }
    ]

    # Run reranking
    result = rerank(test_results)

    # Print results
    print(json.dumps(result, indent=2))

    # Print summary
    print("\n--- Test Summary ---")
    print(f"Reranking applied: {result['reranking_applied']}")
    print(f"Method: {result['method']}")
    print("\nRanked order:")
    for i, r in enumerate(result['results'], 1):
        score = r.get('rerank_score', 0)
        source = r.get('source_file', 'unknown')
        print(f"{i}. {source} (score: {score})")


def main():
    """Main CLI entry point."""
    try:
        # Check for test mode
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            run_test()
            sys.exit(0)

        # Read JSON from stdin
        if sys.stdin.isatty():
            print(json.dumps({
                "error": "No input provided. Pipe JSON results to stdin or use --test flag"
            }))
            sys.exit(0)

        input_data = json.load(sys.stdin)

        # Handle both list input and dict with 'results' key
        if isinstance(input_data, list):
            results = input_data
        elif isinstance(input_data, dict) and "results" in input_data:
            results = input_data["results"]
        else:
            print(json.dumps({
                "error": "Invalid input format. Expected list or dict with 'results' key"
            }))
            sys.exit(0)

        # Rerank results
        output = rerank(results)

        # Output JSON
        print(json.dumps(output, indent=2))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "results": [],
            "reranking_applied": False,
            "method": "error"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
