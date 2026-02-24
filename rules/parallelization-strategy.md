# Parallelization Strategy

| Task Type | Workers | Split Strategy |
|-----------|---------|----------------|
| Bulk extraction (>20 files) | 3-4 | By document type |
| Code analysis (>10 modules) | 5-6 | By directory/module |
| Multi-category research | 3-5 | By source category |
| Independent audits | 2-3 | By audit dimension |

**Rules:**
- Split by task TYPE, not time period (avoids context conflicts)
- Read large files in parallel, but CREATE docs sequentially (progress tracking)
- Background agents (`run_in_background: true`) for independent operations
- Fall back to sequential in main session when worker fails or CSB blocks

**Agent delegation model:**
- Agents = explore + analyze (read-only). Main session = all edits
- Spawn agents for finding issues, categorizing files, extracting patterns
- Bring agent findings back to main session for centralized editing
- See `sub-agent-delegation.md` rule for full pattern

**Never parallelize:**
- Sequential file creation with cross-references
- Tasks needing MCP tools (main session only)
- Edits to the same file from multiple agents
- Multi-file coordinated edits (agents get stuck in plan mode — do centrally)
