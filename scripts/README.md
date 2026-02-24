# Claude Code Scripts

Utility scripts for the Claude Code configuration at `~/.claude/`.

> 54 scripts | Updated: 2026-02-05

---

## By Category

### Coordination (`coord-*`) - 10 scripts
Multi-session file coordination with locking and merging.

| Script | Purpose |
|--------|---------|
| `coord-acquire.sh` | Acquire lock on shared file |
| `coord-append.sh` | Append to coordinated file |
| `coord-check-hash.sh` | Verify file hash integrity |
| `coord-health.sh` | Check coordination system health |
| `coord-heartbeat.sh` | Session heartbeat for coordination |
| `coord-merge.sh` | Merge coordinated file changes |
| `coord-rebuild.sh` | Rebuild coordination state |
| `coord-release.sh` | Release file lock |
| `coord-rotate.sh` | Rotate coordinated files |
| `coord-status.sh` | Show coordination status |
| `coord-wrapper.sh` | Wrapper for coordinated operations |

### CTM (`ctm-*`) - 2 scripts
Cognitive Task Management integration.

| Script | Purpose |
|--------|---------|
| `ctm-context.sh` | Extract CTM task context |
| `ctm-coordination.sh` | CTM coordination logic |

### Validation (`validate-*`) - 4 scripts
Configuration and setup validation.

| Script | Purpose |
|--------|---------|
| `validate-setup.sh` | Full setup health check |
| `validate-imports.sh` | Verify CLAUDE.md import chains |
| `validate-agent-crossrefs.sh` | Check agent cross-references |
| `validate-routing.sh` | Validate agent routing rules |

### Generation (`generate-*`) - 4 scripts
Inventory and manifest generation.

| Script | Purpose |
|--------|---------|
| `generate-inventory.sh` | Regenerate inventory.json |
| `generate-agent-graph.sh` | Generate agent dependency graph |
| `generate-capability-manifest.sh` | Generate capability manifest |
| `generate-routing-index.sh` | Generate routing index |

### Dotfiles (`dotfiles-*`) - 3 scripts
Dotfiles backup and sync with chezmoi.

| Script | Purpose |
|--------|---------|
| `dotfiles-backup.sh` | Backup config to GitHub |
| `dotfiles-sync.sh` | Sync dotfiles across machines |
| `dotfiles-install-deps.sh` | Install dotfiles dependencies |

### RAG & Fathom - 3 scripts
Semantic search and meeting indexing.

| Script | Purpose |
|--------|---------|
| `rag-smart-index.sh` | Intelligent RAG indexing with dedup |
| `fathom-to-rag.sh` | Index Fathom meeting transcripts |
| `restart-rag-server.sh` | Restart RAG MCP server |

### Migration (`migrate-*`) - 3 scripts
Configuration migration utilities.

| Script | Purpose |
|--------|---------|
| `migrate-all-projects.sh` | Migrate all project configs |
| `migrate-to-hierarchy.sh` | Migrate to hierarchical context |
| `migrate-to-temporal-rag.sh` | Migrate to temporal RAG format |

### Maintenance - 6 scripts
Cleanup, analysis, and upkeep.

| Script | Purpose |
|--------|---------|
| `cleanup-history.sh` | Remove old debug/history files (30/90 day retention) |
| `cleanup-daily-logs.sh` | Clean up daily log files |
| `review-agent-drift.sh` | Detect agent inventory vs docs drift |
| `analyze-lessons.py` | Analyze lesson corpus |
| `lesson-maintenance.py` | Lesson lifecycle management |
| `corrections-to-lessons.py` | Convert corrections to lessons |

### Session & Profile - 5 scripts
Session management and multi-account support.

| Script | Purpose |
|--------|---------|
| `rename-session.sh` | Rename current session |
| `mark-session-renamed.sh` | Mark session as renamed |
| `session-prompt.sh` | Generate session prompt |
| `setup-multi-account.sh` | Configure multi-account support |
| `switch-profile.sh` | Switch between profiles |

### Other Utilities - 10+ scripts

| Script | Purpose |
|--------|---------|
| `check-load.sh` | Check system load for agent spawning |
| `sync-memory.sh` | Sync global memory to project |
| `audit-config-chain.sh` | Audit configuration import chains |
| `inbox-init.sh` | Initialize file inbox |
| `inbox-processor.py` | Process inbox files |
| `detect-device.sh` | Detect current device |
| `trust-session.sh` | Mark session as trusted |
| `create-archive.sh` | Create config archive |
| `update-package-config.sh` | Update package configuration |
| `add-cdp-to-agents.py` | Add CDP compliance to agents |
| `add-self-improvement.sh` | Add self-improvement hooks |
| `claude-wrapper.sh.inactive` | Claude command wrapper (disabled - single CLAUDE.md now) |
| `claude-failover.sh` | Failover handling |

---

## Usage

Most scripts are invoked by hooks automatically. For manual use:

```bash
# Health check
~/.claude/scripts/validate-setup.sh

# Clean old files
~/.claude/scripts/cleanup-history.sh --dry-run

# Check load before spawning agents
~/.claude/scripts/check-load.sh --can-spawn

# Regenerate inventory
~/.claude/scripts/generate-inventory.sh
```
