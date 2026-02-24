# RAG Hierarchical Metadata Schema

> Design Spec for ADR: 2026-01-17-hierarchical-context-architecture

## Overview

This spec defines the enhanced metadata schema for RAG chunks to support hierarchical context and scoped search.

## Current Schema (Baseline)

```python
# Existing chunk schema in rag-server
{
    "content": str,                    # Chunk text
    "embedding": vector(1536),         # mxbai-embed-large embedding
    "source_file": str,                # File path
    "chunk_index": int,                # Position in file
    "content_date": datetime | None,   # Extracted date from content
    "file_date": datetime,             # File modification time
    "category": str | None,            # decision, requirement, technical, etc.
    "relevance": str | None,           # critical, high, medium, low, reference
}
```

## Enhanced Schema (v2.0)

```python
{
    # === Existing fields ===
    "content": str,
    "embedding": vector(1536),
    "source_file": str,
    "chunk_index": int,
    "content_date": datetime | None,
    "file_date": datetime,
    "category": str | None,
    "relevance": str | None,

    # === NEW: Hierarchy metadata ===
    "client": str,                     # "rescue" - extracted from path
    "hierarchy_path": str,             # "rescue/erp-integration/sap-connector/requirements"
    "hierarchy_depth": int,            # 4
    "node_type": str,                  # "client" | "project" | "sub_project" | "milestone"
    "project_name": str | None,        # "erp-integration"
    "sub_project_name": str | None,    # "sap-connector"
    "milestone_name": str | None,      # "requirements"

    # === NEW: Semantic metadata ===
    "tags": list[str],                 # ["erp", "sap", "authentication"]
    "phase": str | None,               # "discovery" | "requirements" | "implementation" | "delivery"

    # === NEW: Search optimization ===
    "path_components": list[str],      # ["rescue", "erp-integration", "sap-connector", "requirements"]
}
```

## Metadata Extraction

### From File Path

```python
def extract_hierarchy_metadata(file_path: Path, clients_root: Path) -> dict:
    """
    Extract hierarchy metadata from file path.

    Example:
        file_path: ~/clients/rescue/erp-integration/sap-connector/requirements/auth.md
        clients_root: ~/clients/

    Returns:
        {
            "client": "rescue",
            "hierarchy_path": "rescue/erp-integration/sap-connector/requirements",
            "hierarchy_depth": 4,
            "node_type": "milestone",
            "project_name": "erp-integration",
            "sub_project_name": "sap-connector",
            "milestone_name": "requirements",
            "path_components": ["rescue", "erp-integration", "sap-connector", "requirements"]
        }
    """
    # Get relative path from clients root
    try:
        rel_path = file_path.relative_to(clients_root)
    except ValueError:
        # Not under clients root - use legacy path
        return extract_legacy_metadata(file_path)

    # Split into components (exclude filename)
    components = list(rel_path.parts[:-1])

    if len(components) == 0:
        return {"client": None, "hierarchy_path": "", "hierarchy_depth": 0, "node_type": "root"}

    # Build metadata
    metadata = {
        "client": components[0] if len(components) >= 1 else None,
        "hierarchy_path": "/".join(components),
        "hierarchy_depth": len(components),
        "path_components": components,
    }

    # Determine node type and names based on depth
    depth = len(components)
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
        # Could be sub_project or milestone - check for CLAUDE.md with sub_project type
        metadata["node_type"] = "sub_project"  # Default, can be overridden
        metadata["project_name"] = components[1]
        metadata["sub_project_name"] = components[2]
        metadata["milestone_name"] = None
    else:  # depth >= 4
        metadata["node_type"] = "milestone"
        metadata["project_name"] = components[1]
        metadata["sub_project_name"] = components[2] if depth > 3 else None
        metadata["milestone_name"] = components[-1]

    return metadata
```

### From CLAUDE.md Front-Matter

If a CLAUDE.md exists in the directory, override extracted metadata:

```python
def enhance_with_frontmatter(metadata: dict, claude_md_path: Path) -> dict:
    """Override metadata with explicit front-matter values."""
    if not claude_md_path.exists():
        return metadata

    frontmatter = parse_frontmatter(claude_md_path)

    # Override type if explicitly set
    if "type" in frontmatter:
        metadata["node_type"] = frontmatter["type"]

    # Add tags
    if "tags" in frontmatter:
        metadata["tags"] = frontmatter["tags"]

    # Add phase
    if "phase" in frontmatter:
        metadata["phase"] = frontmatter["phase"]

    return metadata
```

### Phase Inference

If no explicit phase in front-matter, infer from directory name:

```python
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

def infer_phase(path_components: list[str]) -> str | None:
    """Infer phase from directory names."""
    for component in reversed(path_components):
        normalized = component.lower().replace("-", "").replace("_", "")
        for pattern, phase in PHASE_PATTERNS.items():
            if pattern in normalized:
                return phase
    return None
```

### Tag Extraction

Extract tags from content and file path:

```python
def extract_tags(content: str, file_path: Path, frontmatter_tags: list[str]) -> list[str]:
    """Extract and merge tags from multiple sources."""
    tags = set(frontmatter_tags or [])

    # Add path-based tags (project/milestone names)
    path_tags = [p.lower() for p in file_path.parts[-4:-1]]  # Last 3 dirs
    tags.update(path_tags)

    # Add content-based tags (look for hashtags or keywords)
    hashtag_pattern = r'#(\w+)'
    for match in re.findall(hashtag_pattern, content):
        tags.add(match.lower())

    return list(tags)
```

## Scoped Search Implementation

### Filter Construction

```python
def build_hierarchy_filter(
    client: str | None,
    scope: str | None,
    include_ancestors: bool,
    phase: str | None,
    tags: list[str] | None,
    node_types: list[str] | None,
) -> str:
    """Build LanceDB filter string for hierarchical search."""
    filters = []

    # Client filter
    if client:
        filters.append(f"client = '{client}'")

    # Scope filter (with optional ancestors)
    if scope:
        if include_ancestors:
            # Match scope and all ancestors
            # scope: "rescue/erp-integration/sap-connector"
            # matches: rescue/*, rescue/erp-integration/*, rescue/erp-integration/sap-connector/*
            parts = scope.split('/')
            scope_filters = []
            for i in range(len(parts)):
                prefix = '/'.join(parts[:i+1])
                scope_filters.append(f"hierarchy_path LIKE '{prefix}/%'")
                scope_filters.append(f"hierarchy_path = '{prefix}'")
            filters.append(f"({' OR '.join(scope_filters)})")
        else:
            # Exact scope only
            filters.append(f"hierarchy_path LIKE '{scope}/%'")

    # Phase filter
    if phase:
        filters.append(f"phase = '{phase}'")

    # Tags filter (any match)
    if tags:
        tag_filters = [f"'{tag}' IN tags" for tag in tags]
        filters.append(f"({' OR '.join(tag_filters)})")

    # Node type filter
    if node_types:
        type_filters = [f"node_type = '{t}'" for t in node_types]
        filters.append(f"({' OR '.join(type_filters)})")

    return " AND ".join(filters) if filters else None
```

### Proximity Scoring

```python
def calculate_proximity_score(
    chunk_path: str,
    current_scope: str,
    base_score: float
) -> float:
    """
    Boost results closer to current scope.

    Example:
        current_scope: "rescue/erp-integration/sap-connector/requirements"

        chunk_path: "rescue/erp-integration/sap-connector/requirements"
        → proximity = 1.0, boosted_score = base_score * 1.0

        chunk_path: "rescue/erp-integration/sap-connector"
        → proximity = 0.85, boosted_score = base_score * 0.925

        chunk_path: "rescue/erp-integration"
        → proximity = 0.7, boosted_score = base_score * 0.85

        chunk_path: "rescue/hubspot-implementation"
        → proximity = 0.5, boosted_score = base_score * 0.75
    """
    if not current_scope:
        return base_score

    current_parts = current_scope.split('/')
    chunk_parts = chunk_path.split('/')

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
```

### Enhanced Search Function

```python
async def rag_search(
    query: str,
    project_path: str,
    # NEW parameters
    client: str | None = None,
    scope: str | None = None,
    include_ancestors: bool = True,
    proximity_boost: bool = True,
    phase: str | None = None,
    tags: list[str] | None = None,
    node_types: list[str] | None = None,
    # Existing parameters
    top_k: int = 20,
    category: str | None = None,
    min_relevance: str | None = None,
) -> dict:
    """
    Enhanced RAG search with hierarchical scope and proximity scoring.

    Args:
        query: Natural language search query
        project_path: Path to project root (for RAG index location)
        client: Filter by client name
        scope: Hierarchy path to scope search (e.g., "rescue/erp-integration")
        include_ancestors: Include parent scopes in search
        proximity_boost: Boost results closer to scope
        phase: Filter by project phase
        tags: Filter by tags (any match)
        node_types: Filter by node type (client, project, milestone)
        top_k: Number of results
        category: Filter by content category
        min_relevance: Minimum relevance level

    Returns:
        {
            "results": [...],
            "scope_used": "rescue/erp-integration",
            "ancestors_included": true,
            "total_chunks_searched": 1234
        }
    """
    # Build hierarchy filter
    hierarchy_filter = build_hierarchy_filter(
        client, scope, include_ancestors, phase, tags, node_types
    )

    # Combine with existing filters
    combined_filter = combine_filters(hierarchy_filter, category, min_relevance)

    # Execute search
    results = await vector_search(
        query=query,
        project_path=project_path,
        filter=combined_filter,
        top_k=top_k * 2 if proximity_boost else top_k  # Get more for re-ranking
    )

    # Apply proximity boost
    if proximity_boost and scope:
        for result in results:
            result["score"] = calculate_proximity_score(
                result["hierarchy_path"],
                scope,
                result["score"]
            )
        # Re-sort by boosted score
        results = sorted(results, key=lambda r: r["score"], reverse=True)

    # Trim to top_k
    results = results[:top_k]

    # Add metadata
    return {
        "results": results,
        "scope_used": scope,
        "ancestors_included": include_ancestors,
        "proximity_boost_applied": proximity_boost,
        "total_chunks_searched": len(results)
    }
```

## LanceDB Index Configuration

### Table Schema

```python
import lancedb
import pyarrow as pa

# Define schema with new columns
schema = pa.schema([
    # Existing
    pa.field("content", pa.string()),
    pa.field("embedding", pa.list_(pa.float32(), 1536)),
    pa.field("source_file", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("content_date", pa.timestamp("ms")),
    pa.field("file_date", pa.timestamp("ms")),
    pa.field("category", pa.string()),
    pa.field("relevance", pa.string()),

    # NEW: Hierarchy
    pa.field("client", pa.string()),
    pa.field("hierarchy_path", pa.string()),
    pa.field("hierarchy_depth", pa.int32()),
    pa.field("node_type", pa.string()),
    pa.field("project_name", pa.string()),
    pa.field("sub_project_name", pa.string()),
    pa.field("milestone_name", pa.string()),

    # NEW: Semantic
    pa.field("tags", pa.list_(pa.string())),
    pa.field("phase", pa.string()),

    # NEW: Search optimization
    pa.field("path_components", pa.list_(pa.string())),
])
```

### Index Configuration

```python
# Create indexes for common filter patterns
table.create_index(
    ["client"],
    index_type="BTREE"
)

table.create_index(
    ["hierarchy_path"],
    index_type="BTREE"
)

table.create_index(
    ["phase"],
    index_type="BTREE"
)

# Vector index (existing)
table.create_index(
    ["embedding"],
    index_type="IVF_PQ",
    num_partitions=256,
    num_sub_vectors=96
)
```

## Migration

### Re-Index Existing Data

```bash
# Re-index with hierarchy metadata extraction
rag reindex ~/clients/rescue/ --with-hierarchy

# Verify metadata
rag list ~/clients/rescue/ --show-hierarchy
```

### Schema Migration Script

```python
def migrate_schema_v1_to_v2(db_path: Path) -> None:
    """Add hierarchy columns to existing LanceDB table."""
    db = lancedb.connect(db_path)
    table = db.open_table("chunks")

    # Add new columns with defaults
    new_columns = [
        ("client", pa.string(), None),
        ("hierarchy_path", pa.string(), ""),
        ("hierarchy_depth", pa.int32(), 0),
        ("node_type", pa.string(), "unknown"),
        ("project_name", pa.string(), None),
        ("sub_project_name", pa.string(), None),
        ("milestone_name", pa.string(), None),
        ("tags", pa.list_(pa.string()), []),
        ("phase", pa.string(), None),
        ("path_components", pa.list_(pa.string()), []),
    ]

    for name, dtype, default in new_columns:
        table.add_column(name, dtype, default)

    # Backfill from source_file paths
    backfill_hierarchy_metadata(table)
```

## MCP Tool Updates

### Updated `rag_search` Tool

```python
@mcp_tool
def rag_search(
    query: str,
    project_path: str,
    # NEW
    client: str | None = None,
    scope: str | None = None,
    include_ancestors: bool = True,
    proximity_boost: bool = True,
    phase: str | None = None,
    tags: list[str] | None = None,
    # Existing
    top_k: int = 20,
    category: str | None = None,
    min_relevance: str | None = None,
) -> dict:
    """
    Semantic search across indexed documents in a project.

    NEW parameters for hierarchical search:
    - client: Filter by client name
    - scope: Hierarchy path (e.g., "rescue/erp-integration/sap-connector")
    - include_ancestors: Also search parent scopes (default: true)
    - proximity_boost: Rank closer results higher (default: true)
    - phase: Filter by project phase (discovery, requirements, implementation, delivery)
    - tags: Filter by content tags (any match)
    """
    ...
```

## Performance Considerations

| Operation | Without Hierarchy | With Hierarchy | Notes |
|-----------|-------------------|----------------|-------|
| Index 1k files | ~30s | ~35s | +17% for metadata extraction |
| Search (no filter) | ~80ms | ~80ms | No change |
| Search (scoped) | N/A | ~50ms | Filter pre-applied, fewer vectors |
| Search (ancestors) | N/A | ~100ms | Multiple prefix matches |
| Proximity re-rank | N/A | +10ms | In-memory sort |

**Conclusion:** Minimal overhead for significant functionality gain.
