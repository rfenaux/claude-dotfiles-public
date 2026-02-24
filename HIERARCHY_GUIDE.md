# Hierarchical Context Architecture Guide

> Created: 2026-01-17 | Version: 1.0

## Overview

Multi-level project organization system enabling:
- **Client → Project → Sub-project → Milestone** hierarchy
- **CLAUDE.md inheritance** with section-level merging
- **Scoped RAG search** with proximity boosting
- **Milestone templates** for consistent project structure

## Architecture

```
~/.claude/clients/                          # Clients root
├── rescue/                         # Client level
│   ├── CLAUDE.md                   # Client context (type: client)
│   ├── hubspot-implementation/     # Project level
│   │   ├── CLAUDE.md               # Project context (type: project)
│   │   ├── discovery/              # Milestone level
│   │   │   └── CLAUDE.md           # Milestone context (type: milestone)
│   │   └── implementation/
│   │       └── CLAUDE.md
│   └── erp-integration/            # Another project
│       ├── CLAUDE.md
│       └── sap-connector/          # Sub-project level
│           ├── CLAUDE.md           # (type: sub_project)
│           ├── requirements/
│           └── development/

~/.claude/context/                  # System files
├── index.json                      # Node registry
├── cache/                          # Inheritance cache
├── lib/context_manager.py          # Core library
└── templates/                      # Milestone templates
    ├── discovery/
    ├── requirements/
    ├── implementation/
    ├── testing/
    ├── delivery/
    └── training/
```

## CLAUDE.md Front-Matter

Every CLAUDE.md should have YAML front-matter:

```yaml
---
type: client | project | sub_project | milestone
id: rescue/erp-integration/sap-connector
tags: [sap, integration, api]
router_summary: "Brief description for routing"
phase: discovery | requirements | implementation | testing | delivery | training
template_name: discovery  # If created from template
---
```

## Inheritance Chain

When working in `~/.claude/clients/rescue/erp-integration/sap-connector/`:

```
~/.claude/CLAUDE.md          (Global)
    ↓
~/.claude/clients/rescue/CLAUDE.md   (Client)
    ↓
~/.claude/clients/rescue/erp-integration/CLAUDE.md   (Project)
    ↓
~/.claude/clients/rescue/erp-integration/sap-connector/CLAUDE.md   (Sub-project)
```

**Merge rules:**
- Settings: Last-wins (deeper overrides parent)
- Sections: Concatenate by default
- `@override`: Replace entire section

## Quick Commands

### Context CLI

```bash
# View hierarchy tree
~/.claude/scripts/context tree

# Show node details
~/.claude/scripts/context show rescue/erp-integration

# Show effective context for a path
~/.claude/scripts/context show ~/.claude/clients/rescue/erp-integration

# Resolve inheritance chain
~/.claude/scripts/context resolve ~/.claude/clients/rescue/erp-integration

# List templates
~/.claude/scripts/context templates

# Add node with template
~/.claude/scripts/context add ~/.claude/clients/acme/project-x --template discovery

# Rebuild index
~/.claude/scripts/context discover
```

### RAG with Hierarchy

```python
# Scoped search (via MCP tool)
rag_search(
    "authentication flow",
    project_path="~/clients/rescue",
    scope="rescue/erp-integration/sap-connector",
    include_ancestors=True,   # Also search parent contexts
    proximity_boost=True,     # Boost results closer to scope
    phase="requirements",     # Filter by phase
    tags=["api", "oauth"]     # Filter by tags
)
```

## What's Automated

| Feature | Trigger | What Happens |
|---------|---------|--------------|
| Context inheritance | Working in client folder | CLAUDE.md chain auto-merged |
| Hierarchy metadata | RAG indexing | Files tagged with client/project/phase |
| Proximity boost | Scoped RAG search | Closer results rank higher |
| Phase inference | Directory names | "discovery/", "dev/", "testing/" auto-detected |
| Index rebuild | `context discover` | Scans ~/.claude/clients/ for nodes |

## What You Need to Do

### Initial Setup (One-Time)

1. **Organize clients under `~/.claude/clients/`**
   ```bash
   mkdir -p ~/.claude/clients/{client-name}/{project-name}
   ```

2. **Create CLAUDE.md files with front-matter**
   ```bash
   # Use migration script to add front-matter to existing files
   ~/.claude/scripts/migrate-to-hierarchy.sh --add-frontmatter
   ```

3. **Initialize RAG per client** (optional but recommended)
   ```bash
   rag init ~/.claude/clients/rescue
   rag index ~/.claude/clients/rescue
   ```

### Ongoing Work

1. **Start new projects from templates**
   ```bash
   ~/.claude/scripts/context add ~/.claude/clients/acme/crm-impl --template discovery
   ```

2. **Add `router_summary` to CLAUDE.md** for better routing

3. **Use phases in directory names** for auto-detection:
   - `discovery/`, `research/` → discovery phase
   - `requirements/`, `specs/` → requirements phase
   - `implementation/`, `dev/`, `build/` → implementation phase
   - `testing/`, `qa/` → testing phase
   - `delivery/`, `handover/` → delivery phase
   - `training/`, `docs/` → training phase

## Troubleshooting

### Index Issues

```bash
# Rebuild index from scratch
~/.claude/scripts/context discover

# Check index content
cat ~/.claude/context/index.json | python3 -m json.tool

# Clear inheritance cache
~/.claude/scripts/context cache-clear
```

### RAG Hierarchy Not Working

```bash
# Check if hierarchy columns exist in RAG schema
grep "hierarchy_path" ~/.claude/mcp-servers/rag-server/src/rag_server/vectordb.py

# Reindex to pick up hierarchy metadata
rag reindex ~/.claude/clients/rescue
```

### Front-Matter Not Parsed

```bash
# Validate CLAUDE.md parsing
~/.claude/scripts/context parse ~/.claude/clients/rescue/CLAUDE.md

# Ensure file starts with ---
head -5 ~/.claude/clients/rescue/CLAUDE.md
```

### Command Center Score Low

Check these for Hierarchical Context (9 pts):
- `~/.claude/context/index.json` exists (2 pts)
- At least 1 client in `~/.claude/clients/` with CLAUDE.md (2 pts)
- 80%+ CLAUDE.md files have front-matter (2 pts)
- RAG has hierarchy columns (2 pts)
- Inheritance cache has entries (1 pt)

## API Endpoints (Command Center)

| Endpoint | Description |
|----------|-------------|
| `GET /api/hierarchy` | Full hierarchy index |
| `GET /api/hierarchy/node/{id}` | Node details with ancestors/children |
| `GET /api/hierarchy/templates` | Available templates |

## File Reference

| File | Purpose |
|------|---------|
| `~/.claude/context/index.json` | Node registry (SSOT) |
| `~/.claude/context/lib/context_manager.py` | Core library |
| `~/.claude/context/templates/*/` | Milestone templates |
| `~/.claude/context/cache/*.json` | Inheritance cache |
| `~/.claude/scripts/context` | CLI wrapper |
| `~/.claude/scripts/migrate-to-hierarchy.sh` | Migration tool |
| `~/.claude/mcp-servers/rag-server/src/rag_server/hierarchy.py` | RAG hierarchy module |
| `~/.claude/docs/adr/2026-01-17-hierarchical-context-architecture.md` | Architecture decision |
| `~/.claude/docs/design/2026-01-17-hierarchical-context-architecture/` | Design specs |

## Design Decisions

**Why single RAG per client (not federated)?**
- Simpler architecture
- Cross-project context preserved
- Scoped search via metadata filtering
- Proximity scoring handles relevance

**Why YAML front-matter?**
- Human-readable
- Standard format (Jekyll/Hugo compatible)
- Easy to add to existing CLAUDE.md files
- Supports inheritance metadata

**Why templates?**
- Consistent project structure
- Pre-configured agents/tools per phase
- Faster project kickoff
- Customizable (overlay pattern)

---

*See also: ADR, Design Specs, SCORING.md (Hierarchical Context category)*
