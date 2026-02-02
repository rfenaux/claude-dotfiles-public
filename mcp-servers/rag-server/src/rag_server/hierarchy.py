"""Hierarchy metadata extraction for RAG indexing.

Extracts client/project/milestone hierarchy from file paths for scoped search.
"""
import re
from pathlib import Path
from typing import Any

# Default clients root (can be overridden)
CLIENTS_ROOT = Path.home() / "clients"

# Phase inference patterns
PHASE_PATTERNS = {
    "pre-sales": "pre_sales",
    "presales": "pre_sales",
    "discovery": "discovery",
    "research": "discovery",
    "requirements": "requirements",
    "specs": "requirements",
    "implementation": "implementation",
    "development": "implementation",
    "dev": "implementation",
    "build": "implementation",
    "testing": "testing",
    "qa": "testing",
    "delivery": "delivery",
    "handover": "delivery",
    "training": "training",
    "docs": "training",
}


def infer_phase(path: Path) -> str | None:
    """Infer phase from directory name."""
    for part in reversed(path.parts):
        normalized = part.lower().replace("-", "").replace("_", "")
        for pattern, phase in PHASE_PATTERNS.items():
            if pattern.replace("-", "") in normalized:
                return phase
    return None


def extract_hierarchy_metadata(
    file_path: Path | str,
    project_path: Path | str | None = None,
) -> dict[str, Any]:
    """Extract hierarchy metadata from file path for RAG indexing.

    Args:
        file_path: Path to the file being indexed
        project_path: Path to the project root (used to detect clients root)

    Returns:
        Dictionary with hierarchy metadata:
        - client: Client name (e.g., "rescue")
        - hierarchy_path: Full path (e.g., "rescue/erp-integration/sap-connector")
        - hierarchy_depth: Number of levels
        - node_type: client | project | sub_project | milestone
        - project_name: Project name if applicable
        - sub_project_name: Sub-project name if applicable
        - milestone_name: Milestone name if applicable
        - tags: Path-based tags
        - phase: Inferred phase
        - path_components: List of path components
    """
    file_path = Path(file_path)
    project_path = Path(project_path) if project_path else None

    # Determine clients root from project path or use default
    clients_root = CLIENTS_ROOT
    if project_path:
        # Check if project_path is under ~/clients/
        try:
            project_path.relative_to(CLIENTS_ROOT)
            clients_root = CLIENTS_ROOT
        except ValueError:
            # Project is not under ~/clients/, use project_path as root
            # This means hierarchy metadata will be minimal
            return _extract_legacy_metadata(file_path, project_path)

    # Try to extract hierarchy from clients root
    try:
        rel_path = file_path.relative_to(clients_root)
    except ValueError:
        # File is not under clients root
        return _extract_legacy_metadata(file_path, project_path)

    # Split into components (exclude filename)
    components = list(rel_path.parts[:-1]) if rel_path.parts else []

    if len(components) == 0:
        return {
            "client": None,
            "hierarchy_path": "",
            "hierarchy_depth": 0,
            "node_type": "root",
            "project_name": None,
            "sub_project_name": None,
            "milestone_name": None,
            "tags": [],
            "phase": None,
            "path_components": [],
        }

    depth = len(components)
    metadata = {
        "client": components[0] if depth >= 1 else None,
        "hierarchy_path": "/".join(components),
        "hierarchy_depth": depth,
        "path_components": components,
        "tags": [c.lower() for c in components],
        "phase": infer_phase(file_path.parent),
    }

    # Determine node type and names based on depth
    if depth == 1:
        metadata["node_type"] = "client"
        metadata["project_name"] = None
        metadata["sub_project_name"] = None
        metadata["milestone_name"] = None
    elif depth == 2:
        metadata["node_type"] = "project"
        metadata["project_name"] = components[1]
        metadata["sub_project_name"] = None
        metadata["milestone_name"] = None
    elif depth == 3:
        metadata["node_type"] = "sub_project"
        metadata["project_name"] = components[1]
        metadata["sub_project_name"] = components[2]
        metadata["milestone_name"] = None
    else:  # depth >= 4
        metadata["node_type"] = "milestone"
        metadata["project_name"] = components[1]
        metadata["sub_project_name"] = components[2] if depth > 3 else None
        metadata["milestone_name"] = components[-1]

    return metadata


def _extract_legacy_metadata(
    file_path: Path, project_path: Path | None
) -> dict[str, Any]:
    """Extract minimal metadata for non-hierarchical files."""
    return {
        "client": None,
        "hierarchy_path": "",
        "hierarchy_depth": 0,
        "node_type": "unknown",
        "project_name": project_path.name if project_path else None,
        "sub_project_name": None,
        "milestone_name": None,
        "tags": [],
        "phase": infer_phase(file_path.parent) if file_path.parent else None,
        "path_components": [],
    }


def build_hierarchy_filter(
    client: str | None = None,
    scope: str | None = None,
    include_ancestors: bool = True,
    phase: str | None = None,
    tags: list[str] | None = None,
    node_types: list[str] | None = None,
) -> str | None:
    """Build LanceDB filter string for hierarchical search.

    Args:
        client: Filter by client name
        scope: Hierarchy path (e.g., "rescue/erp-integration/sap-connector")
        include_ancestors: Also search parent scopes
        phase: Filter by project phase
        tags: Filter by tags (any match)
        node_types: Filter by node type

    Returns:
        SQL WHERE clause string or None if no filters
    """
    filters = []

    # Client filter
    if client:
        filters.append(f"client = '{client}'")

    # Scope filter (with optional ancestors)
    if scope:
        if include_ancestors:
            # Match scope and all ancestors
            parts = scope.split("/")
            scope_filters = []
            for i in range(len(parts)):
                prefix = "/".join(parts[: i + 1])
                scope_filters.append(f"hierarchy_path LIKE '{prefix}/%'")
                scope_filters.append(f"hierarchy_path = '{prefix}'")
            filters.append(f"({' OR '.join(scope_filters)})")
        else:
            # Exact scope only
            filters.append(f"hierarchy_path LIKE '{scope}/%'")

    # Phase filter
    if phase:
        filters.append(f"phase = '{phase}'")

    # Tags filter (using JSON contains - simplified for LanceDB)
    # Note: This is approximate; actual implementation may vary
    if tags:
        tag_filters = [f"tags LIKE '%{tag}%'" for tag in tags]
        filters.append(f"({' OR '.join(tag_filters)})")

    # Node type filter
    if node_types:
        type_filters = [f"node_type = '{t}'" for t in node_types]
        filters.append(f"({' OR '.join(type_filters)})")

    return " AND ".join(filters) if filters else None


def calculate_proximity_score(
    chunk_hierarchy_path: str,
    current_scope: str,
    base_score: float,
) -> float:
    """Boost results closer to current scope.

    Args:
        chunk_hierarchy_path: Hierarchy path of the chunk
        current_scope: Current working scope
        base_score: Original similarity score

    Returns:
        Boosted score (base_score * proximity_factor)

    Examples:
        current_scope: "rescue/erp-integration/sap-connector/requirements"

        chunk at "rescue/erp-integration/sap-connector/requirements"
        → proximity = 1.0, boosted = base_score * 1.0

        chunk at "rescue/erp-integration/sap-connector"
        → proximity = 0.75, boosted = base_score * 0.875

        chunk at "rescue/erp-integration"
        → proximity = 0.5, boosted = base_score * 0.75

        chunk at "rescue/hubspot-implementation"
        → proximity = 0.25, boosted = base_score * 0.625
    """
    if not current_scope:
        return base_score

    current_parts = current_scope.split("/") if current_scope else []
    chunk_parts = chunk_hierarchy_path.split("/") if chunk_hierarchy_path else []

    # Calculate common prefix length
    common_length = 0
    for i in range(min(len(current_parts), len(chunk_parts))):
        if current_parts[i] == chunk_parts[i]:
            common_length += 1
        else:
            break

    # Calculate proximity (0.0 to 1.0)
    max_length = max(len(current_parts), len(chunk_parts))
    proximity = common_length / max_length if max_length > 0 else 0.0

    # Apply boost: 50% base + 50% proximity-weighted
    # This ensures even distant results remain visible
    boost_factor = 0.5 + (0.5 * proximity)

    return base_score * boost_factor


def apply_proximity_boost(
    results: list[dict[str, Any]],
    current_scope: str | None,
) -> list[dict[str, Any]]:
    """Apply proximity boosting to search results.

    Args:
        results: List of search results with 'score' and 'hierarchy_path'
        current_scope: Current working scope

    Returns:
        Results sorted by proximity-boosted score
    """
    if not current_scope:
        return results

    for result in results:
        hierarchy_path = result.get("hierarchy_path", "")
        original_score = result.get("score", 0.0)

        result["original_score"] = original_score
        result["score"] = calculate_proximity_score(
            hierarchy_path, current_scope, original_score
        )
        result["proximity_boosted"] = True

    # Re-sort by boosted score
    return sorted(results, key=lambda r: r.get("score", 0), reverse=True)
