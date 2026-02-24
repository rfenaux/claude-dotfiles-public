---
status: accepted
date: 2026-01-17
decision-maker: the author
consulted: [reasoning-duo, codex-delegate]
research-method: collaborative-debate
clarification-iterations: 3
perspectives: [InformationRetrieval, SystemArchitecture, UserExperience, Performance]
---

# ADR: Hierarchical Context Architecture for Multi-Level Project Management

## Context and Problem Statement

The current Claude Code configuration treats each folder as a flat "project" (e.g., `rescue-claude`, `isms-claude`). In practice, these are **client folders** containing work that spans multiple projects, sub-projects, and milestones.

**Current state:**
```
~/.claude/projects/
├── rescue-claude/          # Actually a CLIENT
│   ├── sessions-index.json
│   └── (flat structure - everything mixed)
└── isms-claude/
```

**Problems:**
1. All deliverables mixed in one folder
2. RAG searches return noise from unrelated phases
3. No context isolation between discovery and implementation
4. Claude can't determine if information is project-global or phase-specific
5. Tool/skill suggestions are not phase-aware

**Actual project structure:**
```
Client (Rescue)
├── Project: HubSpot Implementation
│   ├── pre-sales/
│   ├── discovery/
│   ├── implementation/
│   └── delivery/
└── Project: ERP Integration
    ├── Sub-project: SAP Connector
    │   ├── requirements/
    │   ├── development/
    │   └── testing/
    └── Sub-project: Data Migration
```

Tree depth is **variable** (2-6+ levels) depending on engagement complexity.

## Decision Drivers

* Context inheritance must work across unlimited tree depth
* Cross-project queries must remain possible ("what did we decide in discovery?")
* Solution must scale to 20+ clients without performance degradation
* Claude must understand if context is global, project-scoped, or milestone-specific
* Hardware constraints: MacBook Air M4 16GB / MacBook Pro M2 Max 64GB

## Considered Options

1. **Federated RAG** - Separate RAG index per project/milestone with router
2. **Single RAG per client** - One index with rich hierarchical metadata
3. **Enhanced flat structure** - Current structure with better tagging

## Decision Outcome

**Chosen option: "Single RAG per client with hierarchical metadata"**

### Rationale

The reasoning-duo debate concluded:

| Aspect | Single RAG + Metadata | Federated RAG |
|--------|:--------------------:|:-------------:|
| Simplicity | ✅ One index | ❌ Many indexes |
| Context inheritance | ✅ Natural (always available) | ❌ Manual cascade |
| Cross-project queries | ✅ Same index, filter | ❌ Query multiple + merge |
| Performance at 100k chunks | ✅ ~80-150ms | ⚠️ Router + fanout = 200ms+ |
| Maintenance | ✅ One reindex | ❌ Sync multiple |

**Key insight:** Federated RAG creates artificial boundaries that break consulting workflow. Context from discovery phase must be accessible during implementation without manual cascade searches.

## Architecture

### Directory Structure

```
~/clients/                              # Client workspaces
├── rescue/                             # CLIENT (Level 1)
│   ├── CLAUDE.md                       # Client context
│   ├── .rag/                           # ONE index for all rescue work
│   ├── .claude/
│   │   ├── context/
│   │   │   ├── DECISIONS.md            # All decisions, tagged by project/phase
│   │   │   ├── SESSIONS.md
│   │   │   └── phases/                 # Phase-specific overrides (optional)
│   │   │       ├── discovery.md
│   │   │       └── implementation.md
│   │   └── sessions-index.json
│   ├── hubspot-implementation/         # PROJECT (Level 2)
│   │   ├── CLAUDE.md                   # Project context
│   │   ├── pre-sales/                  # MILESTONE (Level 3)
│   │   │   └── CLAUDE.md               # Phase context
│   │   ├── discovery/
│   │   ├── implementation/
│   │   └── delivery/
│   └── erp-integration/                # PROJECT (Level 2)
│       ├── CLAUDE.md
│       ├── sap-connector/              # SUB-PROJECT (Level 3)
│       │   ├── CLAUDE.md
│       │   ├── requirements/           # MILESTONE (Level 4)
│       │   ├── development/
│       │   └── testing/
│       └── data-migration/
└── acme/                               # Another CLIENT
    ├── CLAUDE.md
    └── .rag/

~/.claude/
├── CLAUDE.md                           # Global defaults (Level 0)
├── context/
│   ├── index.json                      # Node registry (all clients/projects)
│   └── cache/                          # Resolved inheritance chains
│       └── {node_id}.json
└── templates/
    └── milestones/
        └── implementation-standard/
            ├── CLAUDE.template.md
            ├── tools.json
            └── deliverables.md
```

### CLAUDE.md Front-Matter Schema

Every CLAUDE.md file includes explicit metadata:

```yaml
---
type: project                           # client | project | sub_project | milestone
id: rescue/erp-integration              # Unique path-based identifier
tags: [erp, sap, integration]           # For search filtering
router_summary: "ERP integration connecting SAP to HubSpot"
template_name: implementation-standard  # If using template
template_version: 2.1
inherit:
  mode: section                         # concatenate | override | selective
---
```

### RAG Metadata Schema

Each indexed chunk includes:

```python
{
    # Core fields
    "content": str,
    "embedding": vector,
    "source_file": str,

    # Hierarchy metadata (extracted from path)
    "client": "rescue",
    "hierarchy_path": "rescue/erp-integration/sap-connector/requirements",
    "hierarchy_depth": 4,
    "node_type": "milestone",            # client | project | sub_project | milestone
    "project_name": "erp-integration",
    "milestone_name": "sap-connector",

    # Semantic metadata
    "tags": ["erp", "sap", "authentication"],
    "phase": "requirements",

    # Classification (existing)
    "category": str,
    "relevance": str,
    "content_date": datetime
}
```

### Inheritance Chain Resolution

When working in `~/clients/rescue/erp-integration/sap-connector/requirements/`:

```
Effective context = merge(
    ~/.claude/CLAUDE.md,                              # Global (Level 0)
    ~/clients/rescue/CLAUDE.md,                       # Client (Level 1)
    ~/clients/rescue/erp-integration/CLAUDE.md,       # Project (Level 2)
    ~/clients/rescue/.../sap-connector/CLAUDE.md,     # Sub-project (Level 3)
    ~/clients/rescue/.../requirements/CLAUDE.md       # Milestone (Level 4)
)
```

**Merge semantics:**
- Settings (YAML front-matter): Last-wins for specified keys, inherit unmentioned
- Sections: Concatenate in ancestor order
- `@override` marker: Replace ancestor section entirely

**Caching:**
- Location: `~/.claude/context/cache/{node_id}.json`
- Key: hash(mtimes + sizes of all ancestor files)
- Invalidation: Lazy check on load

### Scoped Search API

```python
def rag_search(
    query: str,
    client: str,
    scope: str | None = None,           # "erp-integration/sap-connector"
    include_ancestors: bool = True,     # Search parent contexts too
    proximity_boost: bool = True,       # Boost results near scope
    phase: str | None = None,           # Filter by phase
    tags: list[str] | None = None,      # Filter by tags
    top_k: int = 20
) -> list[SearchResult]
```

**Examples:**

```python
# Narrow: milestone-scoped with parent context
rag_search("auth approach",
           client="rescue",
           scope="erp-integration/sap-connector",
           include_ancestors=True)

# Broad: all discovery across client
rag_search("stakeholder preferences",
           client="rescue",
           phase="discovery")

# Cross-project patterns
rag_search("API rate limiting",
           client="rescue",
           tags=["api"])
```

### Proximity Scoring

Results ranked by `vector_similarity × proximity_score`:

| Chunk Location | Proximity Score |
|----------------|-----------------|
| Same path (current milestone) | 1.0x |
| Parent (sub-project) | 0.85x |
| Grandparent (project) | 0.70x |
| Sibling project | 0.55x |
| Client root | 0.50x |

This gives "context levels" in a single query.

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Add hierarchy metadata to RAG schema
- [ ] Implement CLAUDE.md front-matter parser
- [ ] Build inheritance chain resolver with caching
- [ ] Create `~/.claude/context/` structure

### Phase 2: RAG Enhancement (Week 1-2)
- [ ] Extend `rag_index` to extract hierarchy from paths
- [ ] Extend `rag_search` with scope/proximity parameters
- [ ] Implement proximity scoring algorithm
- [ ] Test with existing client (~100k chunks)

### Phase 3: Templates (Week 2)
- [ ] Create milestone template structure
- [ ] Implement `claude template apply` command
- [ ] Build three-way merge for template updates

### Phase 4: CLI Commands (Week 2-3)
- [ ] `claude context add <path> --type <type>`
- [ ] `claude context discover [<root>]`
- [ ] `claude context show [<path>]`
- [ ] `claude template apply/update/check`

### Phase 5: Migration (Week 3)
- [ ] Create migration script for existing clients
- [ ] Re-index with hierarchy metadata
- [ ] Update CLAUDE.md files with front-matter
- [ ] Validate with real workflows

## Performance Considerations

| Metric | Target | Rationale |
|--------|--------|-----------|
| Inheritance chain load | <50ms | 6-level chain with cache hit |
| Scoped RAG search | <200ms | 100k chunks with metadata filter |
| Cache hit rate | >90% | Active projects stay warm |
| Memory footprint | <500MB | LanceDB memory-mapped for 100k chunks |

**Hardware compatibility:**
- MacBook Air M4 16GB: Comfortable for typical workloads
- MacBook Pro M2 Max 64GB: Can handle 1M+ chunks

## Consequences

### Positive
- Context inheritance is natural (always available without manual cascade)
- Cross-project queries trivial (same index, different filters)
- Phase-aware tool suggestions become possible
- Deliverables self-organize by folder
- Single index per client = simple operations

### Negative
- Requires CLAUDE.md files at multiple levels (mitigated by templates)
- Initial migration effort for existing projects
- Learning curve for new hierarchy concepts

### Neutral
- Changes mental model from "project = folder" to "client > project > milestone"

## Related Decisions

- CTM Task Management: Tasks will link to hierarchy nodes via `node_id`
- Session Routing: Sessions stored at client level with phase tagging
- CDP Agent Workspaces: Workspaces prefixed with phase identifier

## References

- Reasoning-duo analysis session: 2026-01-17
- LanceDB performance benchmarks: https://lancedb.github.io/lancedb/
- MADR 4.0 template: https://adr.github.io/madr/
