# CLAUDE.md Inheritance Chain System

> Design Spec for ADR: 2026-01-17-hierarchical-context-architecture

## Overview

This spec defines how CLAUDE.md files at different hierarchy levels merge into a single effective context.

## Inheritance Chain

When Claude is working in a directory, the effective context is computed by merging all ancestor CLAUDE.md files:

```
~/clients/rescue/erp-integration/sap-connector/requirements/

Chain (bottom to top):
  Level 0: ~/.claude/CLAUDE.md                    (global)
  Level 1: ~/clients/rescue/CLAUDE.md             (client)
  Level 2: ~/clients/rescue/erp-integration/CLAUDE.md (project)
  Level 3: .../sap-connector/CLAUDE.md            (sub-project)
  Level 4: .../requirements/CLAUDE.md             (milestone)

Effective = merge(L0, L1, L2, L3, L4)
```

## Front-Matter Schema

Every hierarchical CLAUDE.md file MUST include YAML front-matter:

```yaml
---
# Required
type: client | project | sub_project | milestone
id: rescue/erp-integration/sap-connector          # Unique path-based ID

# Optional - Search/Routing
tags: [erp, sap, integration]
router_summary: "SAP connector for ERP integration"
phase: requirements | discovery | implementation | delivery

# Optional - Templates
template_name: implementation-standard
template_version: 2.1

# Optional - Inheritance control
inherit:
  mode: section                                   # section | full | selective
  exclude_sections: [Internal Notes]              # Don't inherit these
  override_settings: [model, async_mode]          # Override these settings
---
```

## Merge Semantics

### 1. Settings (YAML Front-Matter)

**Rule: Last-wins for specified keys, inherit unmentioned**

```yaml
# Level 1 (client)
---
type: client
async_mode: always
model: opus
tags: [rescue, uk]
---

# Level 2 (project)
---
type: project
async_mode: auto            # Overrides client
# model not mentioned       # Inherits opus
tags: [erp, sap]            # Replaces (not merges)
---

# Effective for Level 2
---
type: project               # Own value
async_mode: auto            # Overridden
model: opus                 # Inherited from client
tags: [erp, sap]            # Own value (arrays replace, not merge)
---
```

### 2. Sections (Markdown Content)

**Rule: Concatenate in ancestor order, unless @override**

```markdown
# Level 1 (client) CLAUDE.md
## Tools
- solution-architect
- hubspot-specialist

## Stakeholders
- John Smith (CTO)

# Level 2 (project) CLAUDE.md
## Tools
- erd-generator
- bpmn-specialist

## Constraints
- Budget: $50k
```

**Effective context:**
```markdown
## Tools
<!-- From: rescue (client) -->
- solution-architect
- hubspot-specialist

<!-- From: erp-integration (project) -->
- erd-generator
- bpmn-specialist

## Stakeholders
<!-- From: rescue (client) -->
- John Smith (CTO)

## Constraints
<!-- From: erp-integration (project) -->
- Budget: $50k
```

### 3. Override Marker

**Rule: `@override` replaces entire section from ancestors**

```markdown
# Level 2 (project) CLAUDE.md
## Tools
@override

- Only these tools for this project
- erd-generator
```

**Effective context:**
```markdown
## Tools
<!-- @override from: erp-integration (project) -->
- Only these tools for this project
- erd-generator

## Stakeholders
<!-- From: rescue (client) -->
- John Smith (CTO)
```

### 4. Additive Marker

**Rule: `@additive` merges arrays/lists explicitly (for settings)**

```yaml
---
tags:
  @additive: [erp, sap]     # Merges with parent tags
---
```

## Chain Resolution Algorithm

```python
def resolve_chain(working_dir: Path) -> EffectiveContext:
    """Resolve full inheritance chain for a working directory."""

    # 1. Find all ancestor CLAUDE.md files
    chain = []
    current = working_dir
    while current != Path.home():
        claude_md = current / "CLAUDE.md"
        if claude_md.exists():
            chain.append(claude_md)
        current = current.parent

    # 2. Add global CLAUDE.md
    global_claude = Path.home() / ".claude" / "CLAUDE.md"
    if global_claude.exists():
        chain.append(global_claude)

    # 3. Reverse to process root-first
    chain = list(reversed(chain))

    # 4. Check cache
    cache_key = compute_cache_key(chain)
    if cached := get_cache(cache_key):
        return cached

    # 5. Merge chain
    effective = EffectiveContext()
    for claude_md in chain:
        parsed = parse_claude_md(claude_md)
        effective = merge(effective, parsed)

    # 6. Cache result
    set_cache(cache_key, effective)

    return effective

def compute_cache_key(chain: list[Path]) -> str:
    """Generate cache key from mtimes and sizes."""
    parts = []
    for path in chain:
        stat = path.stat()
        parts.append(f"{path}:{stat.st_mtime}:{stat.st_size}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]

def merge(base: EffectiveContext, overlay: EffectiveContext) -> EffectiveContext:
    """Merge overlay onto base context."""
    result = base.copy()

    # Merge settings (last-wins)
    for key, value in overlay.settings.items():
        if isinstance(value, dict) and value.get("@additive"):
            # Additive merge for arrays
            result.settings[key] = result.settings.get(key, []) + value["@additive"]
        else:
            result.settings[key] = value

    # Merge sections
    for section_name, section_content in overlay.sections.items():
        if section_content.startswith("@override"):
            # Replace entire section
            result.sections[section_name] = Section(
                content=section_content.replace("@override", "").strip(),
                source=overlay.source,
                is_override=True
            )
        else:
            # Concatenate
            if section_name in result.sections:
                result.sections[section_name].append(
                    content=section_content,
                    source=overlay.source
                )
            else:
                result.sections[section_name] = Section(
                    content=section_content,
                    source=overlay.source
                )

    return result
```

## Cache Structure

**Location:** `~/.claude/context/cache/{node_id}.json`

```json
{
  "cache_key": "a1b2c3d4e5f6g7h8",
  "generated_at": "2026-01-17T14:30:00Z",
  "chain": [
    {"path": "~/.claude/CLAUDE.md", "mtime": 1737123456, "size": 15234},
    {"path": "~/clients/rescue/CLAUDE.md", "mtime": 1737123789, "size": 2341},
    {"path": "~/clients/rescue/erp-integration/CLAUDE.md", "mtime": 1737124012, "size": 1567}
  ],
  "effective_settings": {
    "type": "project",
    "id": "rescue/erp-integration",
    "async_mode": "auto",
    "model": "opus",
    "tags": ["erp", "sap"]
  },
  "effective_sections": {
    "Tools": {
      "content": "- solution-architect\n- erd-generator",
      "sources": ["rescue", "erp-integration"]
    }
  }
}
```

## Context Index

**Location:** `~/.claude/context/index.json`

Central registry of all context nodes:

```json
{
  "version": "1.0",
  "updated_at": "2026-01-17T14:30:00Z",
  "nodes": [
    {
      "id": "rescue",
      "path": "~/clients/rescue",
      "type": "client",
      "parent_id": null,
      "tags": ["rescue", "uk"],
      "has_rag": true,
      "children": ["rescue/hubspot-implementation", "rescue/erp-integration"]
    },
    {
      "id": "rescue/erp-integration",
      "path": "~/clients/rescue/erp-integration",
      "type": "project",
      "parent_id": "rescue",
      "tags": ["erp", "sap"],
      "has_rag": false,
      "children": ["rescue/erp-integration/sap-connector"]
    }
  ]
}
```

## CLI Commands

### `claude context discover`

Scan filesystem and build/update index:

```bash
claude context discover ~/clients/
# Scans for CLAUDE.md files, parses front-matter, builds index

claude context discover --preview
# Shows what would be indexed without writing
```

### `claude context add`

Manually add a context node:

```bash
claude context add ~/clients/acme --type client
# Creates CLAUDE.md with front-matter template

claude context add ~/clients/acme/project-x --type project --template implementation-standard
# Creates from template
```

### `claude context show`

Display effective context for a path:

```bash
claude context show ~/clients/rescue/erp-integration/
# Shows merged context with source annotations

claude context show --chain
# Shows inheritance chain only

claude context show --settings
# Shows effective settings only
```

### `claude context validate`

Validate CLAUDE.md files:

```bash
claude context validate
# Validates all indexed nodes

claude context validate ~/clients/rescue/
# Validates specific path
```

## Integration Points

### Session Start Hook

```bash
# In SessionStart hook
WORKING_DIR=$(pwd)
CONTEXT=$(claude context show "$WORKING_DIR" --json)

# Pass to Claude via hook output
echo "Context loaded from: $(echo $CONTEXT | jq -r '.chain | join(" → ")')"
```

### RAG Search

```python
# When searching, use hierarchy metadata
def rag_search_with_context(query, working_dir):
    # Get effective context
    context = resolve_chain(working_dir)

    # Search with scope
    return rag_search(
        query=query,
        client=context.settings.get("client_id"),
        scope=context.settings.get("id"),
        include_ancestors=True
    )
```

### CTM Tasks

```python
# Link tasks to context nodes
task = {
    "id": "task-123",
    "title": "Implement SAP auth",
    "context_node": "rescue/erp-integration/sap-connector",
    "phase": "requirements"
}
```

## Migration

### From Flat Structure

```bash
# 1. Create client folder
mkdir -p ~/clients/rescue

# 2. Move existing project
mv ~/projects/rescue-claude/* ~/clients/rescue/

# 3. Add front-matter to existing CLAUDE.md
claude context migrate ~/clients/rescue/ --type client

# 4. Re-index RAG with hierarchy
rag reindex ~/clients/rescue/ --with-hierarchy

# 5. Update context index
claude context discover ~/clients/
```

## Error Handling

### Missing CLAUDE.md

If a directory in the chain has no CLAUDE.md, skip it:

```
~/clients/rescue/erp-integration/sap-connector/requirements/
                 ↑ no CLAUDE.md here

Chain: global → rescue → sap-connector → requirements
       (erp-integration skipped - no CLAUDE.md)
```

### Invalid Front-Matter

Log warning, use defaults:

```
Warning: Invalid front-matter in ~/clients/rescue/CLAUDE.md
  Missing required field: type
  Using default: type=unknown
```

### Circular References

Not possible with path-based hierarchy (enforced by filesystem).

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Chain resolution (cold) | <100ms | Parse 5 files |
| Chain resolution (cached) | <5ms | Hash check only |
| Cache hit rate | >95% | For active projects |
| Index rebuild | <1s | For 100 nodes |
