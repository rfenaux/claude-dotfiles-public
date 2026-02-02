# Implementation Roadmap: Hierarchical Context Architecture

> Created: 2026-01-17 | Status: Planning Complete

## Overview

This roadmap details the phased implementation of the Hierarchical Context Architecture, from foundation work to full production deployment.

## Phase Summary

| Phase | Scope | Status | Dependencies |
|-------|-------|--------|--------------|
| **0. Quick Start** | Create ~/clients/ structure | Ready | None |
| **1. Foundation** | Schemas, parser, cache | Ready | Phase 0 |
| **2. RAG Enhancement** | Hierarchy metadata, scoped search | Ready | Phase 1 |
| **3. Templates** | Milestone templates, apply/update | Ready | Phase 1 |
| **4. CLI Commands** | context add/discover/show | Ready | Phase 1-2 |
| **5. Command Center** | UI updates, hierarchy browser | Ready | Phase 1-4 |
| **6. Migration** | Existing projects → new structure | Ready | Phase 1-4 |

---

## Phase 0: Quick Start (Immediate)

Minimal viable structure to start using the architecture.

### Tasks

- [ ] Create `~/clients/` directory
- [ ] Create first client folder (e.g., `~/clients/rescue/`)
- [ ] Add CLAUDE.md with front-matter to client folder
- [ ] Create `~/.claude/context/` directory structure

### Commands

```bash
# Create base structure
mkdir -p ~/clients/rescue
mkdir -p ~/.claude/context/{cache,templates/milestones}

# Create client CLAUDE.md
cat > ~/clients/rescue/CLAUDE.md << 'EOF'
---
type: client
id: rescue
tags: [rescue, uk, education]
router_summary: "Rescue - UK education client, HubSpot implementation"
---

# Rescue Client Context

## Company Profile
- **Industry**: Education
- **Region**: UK
- **Key Contact**: [TBD]

## Active Projects
- HubSpot Implementation
- ERP Integration
EOF
```

### Validation

```bash
# Verify structure
ls -la ~/clients/rescue/CLAUDE.md
ls -la ~/.claude/context/
```

---

## Phase 1: Foundation

Core infrastructure for hierarchy support.

### Tasks

#### 1.1 Context Index Schema
- [ ] Create `~/.claude/context/index.json` schema
- [ ] Implement JSON validator
- [ ] Create initial index from Phase 0 structure

```json
{
  "version": "1.0",
  "updated_at": "2026-01-17T14:30:00Z",
  "clients_root": "~/clients",
  "nodes": [
    {
      "id": "rescue",
      "path": "~/clients/rescue",
      "type": "client",
      "parent_id": null,
      "tags": ["rescue", "uk"],
      "has_rag": true,
      "children": []
    }
  ]
}
```

#### 1.2 CLAUDE.md Parser
- [ ] Parse YAML front-matter from CLAUDE.md files
- [ ] Handle missing/invalid front-matter gracefully
- [ ] Extract hierarchy metadata

#### 1.3 Inheritance Chain Resolver
- [ ] Walk directory tree to find ancestor CLAUDE.md files
- [ ] Implement merge logic (section concatenation, @override)
- [ ] Cache resolved chains

#### 1.4 Cache Manager
- [ ] Implement cache key computation (mtime + size hash)
- [ ] Lazy invalidation on load
- [ ] Cache read/write to `~/.claude/context/cache/`

### Files Created

| File | Purpose |
|------|---------|
| `~/.claude/context/index.json` | Node registry |
| `~/.claude/context/cache/*.json` | Resolved chains |
| `~/.claude/scripts/context-parser.py` | Parser library |

### Tests

```bash
# Test parser
python ~/.claude/scripts/context-parser.py parse ~/clients/rescue/CLAUDE.md

# Test inheritance
python ~/.claude/scripts/context-parser.py resolve ~/clients/rescue/erp-integration/

# Test cache
python ~/.claude/scripts/context-parser.py cache-stats
```

---

## Phase 2: RAG Enhancement

Add hierarchy metadata to RAG indexing and search.

### Tasks

#### 2.1 Schema Update
- [ ] Add columns to LanceDB schema
- [ ] Create migration script for existing indexes

```python
# New columns
"client": str,
"hierarchy_path": str,
"hierarchy_depth": int,
"node_type": str,
"project_name": str,
"milestone_name": str,
"tags": list[str],
"phase": str,
```

#### 2.2 Indexer Update
- [ ] Extract hierarchy from file paths
- [ ] Infer phase from directory names
- [ ] Add tags extraction

#### 2.3 Search Enhancement
- [ ] Add `scope` parameter to `rag_search`
- [ ] Implement ancestor inclusion
- [ ] Add proximity scoring

#### 2.4 MCP Tool Update
- [ ] Extend `rag_search` tool with new parameters
- [ ] Update tool documentation

### Files Modified

| File | Changes |
|------|---------|
| `~/.claude/mcp-servers/rag-server/rag_tools.py` | New parameters |
| `~/.claude/mcp-servers/rag-server/indexer.py` | Hierarchy extraction |
| `~/.claude/mcp-servers/rag-server/schema.py` | New columns |

### Tests

```bash
# Re-index with hierarchy
rag reindex ~/clients/rescue/ --with-hierarchy

# Test scoped search
rag search "auth requirements" --scope erp-integration/sap-connector

# Test phase filter
rag search "decisions" --phase discovery
```

---

## Phase 3: Templates

Milestone templates for quick project setup.

### Tasks

#### 3.1 Template Structure
- [ ] Create `~/.claude/templates/milestones/` directory
- [ ] Create `implementation-standard` template

```
~/.claude/templates/milestones/implementation-standard/
├── template.json           # Metadata
├── CLAUDE.template.md      # Base CLAUDE.md
├── tools.json              # Recommended tools
└── deliverables.md         # Expected outputs
```

#### 3.2 Template Apply
- [ ] Implement `claude template apply <name> <path>`
- [ ] Copy template files
- [ ] Customize front-matter

#### 3.3 Template Update
- [ ] Implement `claude template check` (detect outdated)
- [ ] Implement `claude template update` (three-way merge)

### Templates to Create

| Template | Phases Included |
|----------|-----------------|
| `implementation-standard` | pre-sales, discovery, implementation, delivery, training |
| `integration-project` | requirements, development, testing, go-live |
| `consulting-engagement` | discovery, research, recommendations |

---

## Phase 4: CLI Commands

User-facing commands for context management.

### Tasks

#### 4.1 `claude context discover`
- [ ] Scan filesystem for CLAUDE.md files
- [ ] Parse front-matter
- [ ] Build/update index.json
- [ ] Preview mode (`--preview`)

#### 4.2 `claude context add`
- [ ] Create CLAUDE.md with front-matter template
- [ ] Add to index.json
- [ ] Support `--type` and `--template` options

#### 4.3 `claude context show`
- [ ] Display effective context for path
- [ ] `--chain` shows inheritance only
- [ ] `--settings` shows effective settings

#### 4.4 `claude context validate`
- [ ] Validate all CLAUDE.md files
- [ ] Check front-matter completeness
- [ ] Report broken references

### Implementation

Add to CTM CLI or create new `context` CLI:

```bash
# Option A: Extend CTM
ctm context discover ~/clients/

# Option B: New CLI
~/.claude/scripts/context-cli.py discover ~/clients/
```

---

## Phase 5: Command Center

Web UI updates for hierarchy visualization.

### Tasks

#### 5.1 Hierarchy Browser
- [ ] Tree view of clients/projects/milestones
- [ ] Click to see effective context
- [ ] Visual inheritance chain

#### 5.2 Scoring Updates
- [ ] Add Hierarchical Context category to dashboard
- [ ] Show clients/projects/milestones counts
- [ ] Display hierarchy depth

#### 5.3 RAG Search Enhancements
- [ ] Scope selector in search UI
- [ ] Phase filter dropdown
- [ ] Proximity scoring visualization

#### 5.4 Context Editor
- [ ] Edit CLAUDE.md front-matter via UI
- [ ] Add new nodes via UI
- [ ] Template browser and apply

### Files Modified

| File | Changes |
|------|---------|
| `command-center/src/routes/+page.svelte` | Add hierarchy section |
| `command-center/src/lib/api.js` | New endpoints |
| `command-center/src/routes/api/hierarchy/+server.js` | Hierarchy API |

---

## Phase 6: Migration

Migrate existing projects to new structure.

### Tasks

#### 6.1 Migration Script
- [ ] Create `migrate-to-hierarchy.sh`
- [ ] Move `~/.claude/projects/*` to `~/clients/`
- [ ] Add front-matter to existing CLAUDE.md files
- [ ] Re-index RAG with hierarchy

#### 6.2 Backward Compatibility
- [ ] Symlinks from old paths
- [ ] Fallback for non-hierarchical projects

### Migration Script

```bash
#!/bin/bash
# ~/.claude/scripts/migrate-to-hierarchy.sh

CLIENT_NAME="$1"
OLD_PATH="~/.claude/projects/${CLIENT_NAME}-claude"
NEW_PATH="~/clients/${CLIENT_NAME}"

# 1. Create new structure
mkdir -p "$NEW_PATH"

# 2. Move content
mv "$OLD_PATH"/* "$NEW_PATH/"

# 3. Add front-matter if missing
if ! grep -q "^---" "$NEW_PATH/CLAUDE.md"; then
    # Prepend front-matter
    ...
fi

# 4. Create symlink for compatibility
ln -s "$NEW_PATH" "$OLD_PATH"

# 5. Re-index RAG
rag reindex "$NEW_PATH" --with-hierarchy

# 6. Update context index
claude context discover ~/clients/
```

---

## Validation Checklist

### Phase 0 Complete When:
- [ ] `~/clients/` exists with at least one client
- [ ] Client has CLAUDE.md with valid front-matter
- [ ] `~/.claude/context/` directory structure exists

### Phase 1 Complete When:
- [ ] `index.json` lists all nodes
- [ ] Parser handles all CLAUDE.md files
- [ ] Cache hits for repeated resolutions

### Phase 2 Complete When:
- [ ] RAG chunks have `hierarchy_path` field
- [ ] Scoped searches return correct results
- [ ] Proximity scoring affects rankings

### Phase 3 Complete When:
- [ ] At least one template exists
- [ ] `template apply` creates valid structure
- [ ] `template check` detects outdated templates

### Phase 4 Complete When:
- [ ] All CLI commands work
- [ ] Help text is complete
- [ ] Error handling is graceful

### Phase 5 Complete When:
- [ ] Hierarchy browser shows tree
- [ ] Scoring dashboard includes new category
- [ ] Search UI has scope controls

### Phase 6 Complete When:
- [ ] All existing projects migrated
- [ ] Old paths still work (symlinks)
- [ ] No data loss

---

## Timeline Estimate

| Phase | Effort | Calendar |
|-------|--------|----------|
| Phase 0 | 1 hour | Day 1 |
| Phase 1 | 2-3 days | Week 1 |
| Phase 2 | 3-4 days | Week 1-2 |
| Phase 3 | 2 days | Week 2 |
| Phase 4 | 2 days | Week 2 |
| Phase 5 | 3-4 days | Week 2-3 |
| Phase 6 | 1-2 days | Week 3 |

**Total: ~2-3 weeks**

---

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| RAG schema migration breaks existing indexes | Medium | Backup before migration, fallback to legacy schema |
| Inheritance chain performance | Low | Cache hit rate >95% for active projects |
| Command Center build issues | Low | Incremental updates, feature flags |
| Migration data loss | Low | Dry-run mode, manual review before delete |

---

## Next Action

**Start with Phase 0** — create the minimal structure today to validate the architecture before building infrastructure.

```bash
# Run this now:
mkdir -p ~/clients/rescue ~/.claude/context/{cache,templates/milestones}
```
