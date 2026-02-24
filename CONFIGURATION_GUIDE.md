# Claude Code Configuration Guide

> **Version:** 1.8 | **Updated:** 2026-02-07

Complete documentation for the custom Claude Code setup at `~/.claude/`.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Systems](#core-systems)
   - [CTM (Cognitive Task Manager)](#ctm-cognitive-task-manager)
   - [CDP (Cognitive Delegation Protocol)](#cdp-cognitive-delegation-protocol)
   - [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
   - [Project Memory](#project-memory)
   - [Hierarchical Context Architecture](#hierarchical-context-architecture-new) (NEW)
4. [Skills](#skills)
5. [Agents](#agents)
6. [Plugins](#plugins)
7. [Hooks](#hooks)
8. [Configuration Files](#configuration-files)
9. [Commands Reference](#commands-reference)
10. [Workflows](#workflows)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance](#maintenance)

---

## Overview

This Claude Code configuration transforms Claude from a simple assistant into a **persistent, context-aware consulting partner** optimized for CRM implementations and solution architecture work.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Persistent Memory** | Remembers decisions, tasks, and context across sessions |
| **Task Management** | Tracks multiple concurrent tasks with priority scheduling |
| **Semantic Search** | Searches project documents using AI embeddings |
| **Agent Delegation** | Spawns specialized sub-agents for complex tasks |
| **Auto-Indexing** | Automatically indexes new files and conversations |
| **Health Monitoring** | Self-validates configuration at session start |

### Design Principles

1. **Partnership over tool** — Claude acts as a collaborative partner
2. **Soft enforcement** — Rules via prompts, not hard blocks
3. **Graceful degradation** — Errors don't crash the system
4. **Self-contained** — No external databases or cloud services
5. **Maintainable** — Scripts and docs over magic

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ~/.claude/ (Global Config)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │      CTM        │   │      CDP        │   │         RAG             │   │
│  │  Task Manager   │◀──│  Delegation     │──▶│   Semantic Search       │   │
│  │                 │   │  Protocol       │   │                         │   │
│  │  ~/.claude/ctm/ │   │  HANDOFF/OUTPUT │   │   project/.rag/         │   │
│  └────────┬────────┘   └────────┬────────┘   └────────────┬────────────┘   │
│           │                     │                         │                 │
│           ▼                     ▼                         ▼                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        PROJECT MEMORY                               │   │
│  │              .claude/context/DECISIONS.md, SESSIONS.md              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────────┐   │
│  │  133 Agents  │   │   45 Skills      │   │     6 Plugins            │   │
│  │  specialized │   │  workflows       │   │  marketplace             │   │
│  └──────────────┘   └──────────────────┘   └──────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                             HOOKS (Automation Layer)                        │
│  SessionStart → CTM briefing + health check + config audit                  │
│  PreCompact → CTM checkpoint + conversation save + RAG index                │
│  SessionEnd → CTM save + conversation save + dotfiles backup                │
│  PostToolUse (Write/Edit) → RAG auto-index + config audit (if .claude/)     │
│  UserPromptSubmit → Timestamp injection                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
~/.claude/
├── CLAUDE.md                 # Master instructions (loaded every session)
├── CONFIGURATION_GUIDE.md    # This file
├── AGENTS_INDEX.md           # Agent catalog (optional — routing is in CLAUDE.md)
├── SKILLS_INDEX.md           # Skills catalog (optional — use /config-audit to list)
├── AGENT_STANDARDS.md        # Agent compliance rules
├── CTM_GUIDE.md              # CTM documentation
├── CDP_PROTOCOL.md           # CDP specification
├── RAG_GUIDE.md              # RAG documentation
├── settings.json             # Claude Code settings + hooks
├── statusline.sh             # Custom status bar script
│
├── ctm/                      # Cognitive Task Manager
│   ├── config.json
│   ├── index.json
│   ├── scheduler.json
│   ├── agents/               # Task agent files
│   ├── checkpoints/          # State snapshots
│   ├── lib/                  # Python modules
│   └── scripts/ctm           # CLI entry point
│
├── agents/                   # 81 specialized agents
│   ├── erd-generator.md
│   ├── bpmn-specialist.md
│   └── ...
│
├── skills/                   # 11 interactive skills
│   ├── solution-architect/
│   ├── init-project/
│   └── ...
│
├── hooks/                    # Hook scripts
│   ├── ctm/
│   │   ├── ctm-session-start.sh
│   │   ├── ctm-pre-compact.sh
│   │   └── ctm-session-end.sh
│   ├── save-conversation.sh
│   ├── rag-index-on-write.sh    # Debounced RAG indexing
│   ├── context-preflight.sh     # Auto RAG search for questions
│   └── git-*.sh/py
│
├── scripts/                  # Utility scripts
│   ├── validate-setup.sh        # Configuration validator
│   ├── generate-inventory.sh    # Inventory manifest generator
│   └── check-load.sh            # Performance monitor for delegation
│
├── inventory.json            # Single source of truth manifest
│
├── plugins/                  # Marketplace plugins
│   └── marketplaces/
│
├── mcp-servers/              # MCP server configurations
│   └── rag-server/
│
└── projects/                 # Project-specific context (per-project memory)
```

---

## Core Systems

### CTM (Cognitive Task Manager)

Bio-inspired task management that mimics human working memory.

#### Purpose
- Track multiple concurrent tasks across sessions
- Prioritize work automatically
- Provide session briefings
- Extract decisions when tasks complete

#### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | A task context with state, decisions, and progress |
| **Priority Queue** | Tasks ranked by urgency, recency, and value |
| **Checkpoint** | Snapshot of state for recovery |
| **Briefing** | Summary of pending work at session start |
| **Consolidation** | Extract decisions to project memory |

#### Commands

```bash
ctm status           # Show current state
ctm brief            # Session briefing
ctm spawn "title"    # Create new task
ctm switch <id>      # Switch to task
ctm pause [id]       # Pause task
ctm complete [id]    # Mark complete
ctm context add -d   # Add decision
ctm checkpoint       # Save state
ctm restore          # Restore from checkpoint
ctm repair           # Fix corrupted data
ctm delegate "..."   # Delegate via CDP
```

#### Files

| File | Purpose |
|------|---------|
| `config.json` | Global settings |
| `index.json` | Agent index for fast lookups |
| `scheduler.json` | Priority queue state |
| `agents/*.json` | Individual task agents |
| `checkpoints/` | State snapshots |

**Documentation:** `~/.claude/CTM_GUIDE.md`

---

### CDP (Cognitive Delegation Protocol)

Function-call semantics for sub-agent delegation with orchestration controls.

#### Purpose
- Keep primary conversation lightweight
- Isolate agent work in separate context
- Standardize handoffs and returns
- **Control delegation depth** (max 3 levels)
- **Load-aware spawning** (adapt to system performance)

#### Protocol Flow

```
PRIMARY                              SUB-AGENT
   │                                     │
   │ 1. Check load (check-load.sh)       │
   │ 2. Create workspace                 │
   │ 3. Write HANDOFF.md (with depth)    │
   │ 4. Spawn agent ─────────────────────▶
   │                                     │ 5. Read HANDOFF.md
   │                                     │ 6. Check depth (can I spawn?)
   │                                     │ 7. Execute task
   │                                     │ 8. Write OUTPUT.md
   │ ◀───────────────────────────────────│ 9. Signal complete
   │ 10. Read OUTPUT.md                  │
```

#### Delegation Depth (NEW in v1.2)

Sub-agents can spawn their own sub-agents, up to 3 levels:

```
Human
└── Primary (depth=0)     ← can spawn
    └── L1 (depth=1)      ← can spawn
        └── L2 (depth=2)  ← can spawn
            └── L3 (depth=3) ← CANNOT spawn
```

Depth is tracked in the delegation preamble:
```
[CLAUDE-TO-CLAUDE DELEGATION]
From: Claude (depth=1) | To: Claude (depth=2)
Max-Depth: 3 | Can-Spawn: YES
```

#### Load-Aware Spawning (NEW in v1.2)

Check system load before spawning:

```bash
~/.claude/scripts/check-load.sh --status-only
```

| Status | Load Avg | Policy |
|--------|----------|--------|
| `OK` | < 5.0 | Parallel spawning allowed |
| `CAUTION` | 5.0-10.0 | Sequential (cascade) only |
| `HIGH_LOAD` | > 10.0 | Avoid spawning, work inline |

#### Workspace Structure

```
.agent-workspaces/{task-id}/
├── HANDOFF.md      # Input: What agent needs (includes depth)
├── WORK.md         # Scratchpad (optional)
├── OUTPUT.md       # Return value
├── PROGRESS.md     # ACP: Subtask tracking
└── SOURCES.md      # ACP: File excerpts
```

#### ACP Extension

ACP (Agent Context Protocol) extends CDP for parallel/long-running agents:
- Adds `PROGRESS.md` for incremental updates
- Adds `SOURCES.md` to cache file excerpts
- Used when `async: always` or task involves >10 files

**Documentation:** `~/.claude/CDP_PROTOCOL.md`

---

### RAG (Retrieval-Augmented Generation)

Semantic search over project documents using Ollama embeddings.

#### Purpose
- Answer questions about project context
- Find relevant past decisions
- Search meeting notes, specs, requirements

#### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| MCP Server | `~/.claude/mcp-servers/rag-server/` | Provides search tools |
| Database | `project/.rag/` | LanceDB vector store |
| Dashboard | `http://localhost:8420` | Web UI |
| Ollama | System service | Embeddings generation |

#### Commands

```bash
rag init             # Initialize for project
rag index docs/      # Index files/folders
rag reindex          # Rebuild entire index
rag search "query"   # Semantic search
rag status           # Check status
rag list             # List indexed docs
```

#### Auto-Indexing

Files are automatically indexed when:
- Created/modified via Write/Edit tools (PostToolUse hook)
- Session ends (SessionEnd hook)
- Before compaction (PreCompact hook)

#### Chronology Awareness

Search results include date metadata:
- `content_date` — Dates mentioned in text
- `file_date` — File modification time
- `relevant_date` — Best date to use

Newer content is boosted; superseded content is penalized.

**Documentation:** `~/.claude/RAG_GUIDE.md`

---

### Project Memory

Persistent context structure for individual projects.

#### Auto Memory (MEMORY.md)

Global MEMORY.md (`~/.claude/memory/MEMORY.md`) is synced to per-project directories at SessionStart via `sync-memory.sh`. After sync, `enrich-project-memory.sh` appends a `## Project Context (Auto-Generated)` section with CTM decisions/blockers and high-confidence lessons matching the project. First 200 lines auto-injected into system prompt by Claude Code.

**Scripts:** `~/.claude/scripts/sync-memory.sh` | `~/.claude/scripts/enrich-project-memory.sh`
**Guide:** `~/.claude/memory/README.md`

#### Structure

```
project/.claude/context/
├── DECISIONS.md     # Architecture decisions
├── SESSIONS.md      # Session summaries
├── CHANGELOG.md     # Project evolution
└── STAKEHOLDERS.md  # Key people
```

#### DECISIONS.md Format

```markdown
## Active Decisions

### Database: PostgreSQL
- **Decided**: 2026-01-07
- **Decision**: Use PostgreSQL for persistence
- **Context**: Relational requirements emerged
- **Alternatives**: MongoDB, SQLite
- **Supersedes**: MongoDB consideration (2025-12-15)

## Superseded Decisions

### ~~MongoDB~~ → PostgreSQL (2026-01-07)
- **Original decision**: 2025-12-15
- **Why superseded**: Relational requirements emerged
```

#### Decision Auto-Capture

Claude watches for decision language and offers to record:
- "we decided", "let's go with", "decision:"
- "we're going to use", "choosing", "agreed"

**Initialize:** Run `init project` or copy templates from `~/.claude/templates/`

---

### Hierarchical Context Architecture (NEW)

Multi-level project organization for client engagements with context inheritance.

#### Purpose
- Organize work by Client → Project → Sub-project → Milestone
- Scope RAG searches to relevant context
- Inherit configuration across hierarchy levels
- Enable phase-aware tool suggestions

#### Structure

```
~/.claude/clients/                              # Client workspaces
├── rescue/                             # CLIENT (Level 1)
│   ├── CLAUDE.md                       # Client context
│   ├── .rag/                           # Single RAG for all client work
│   ├── hubspot-implementation/         # PROJECT (Level 2)
│   │   ├── CLAUDE.md                   # Project overrides
│   │   ├── discovery/                  # MILESTONE (Level 3)
│   │   └── implementation/
│   └── erp-integration/                # PROJECT (Level 2)
│       ├── sap-connector/              # SUB-PROJECT (Level 3)
│       │   └── requirements/           # MILESTONE (Level 4)
│       └── data-migration/
└── acme/                               # Another CLIENT
    └── .rag/
```

#### CLAUDE.md Front-Matter

Every CLAUDE.md in the hierarchy requires metadata:

```yaml
---
type: client | project | sub_project | milestone
id: rescue/erp-integration
tags: [erp, sap]
router_summary: "ERP integration connecting SAP to HubSpot"
phase: requirements                     # For milestones
template_name: implementation-standard  # If using template
inherit:
  mode: section                         # How to merge with parent
---
```

#### Context Inheritance

When working in a directory, effective context merges all ancestors:

```
~/.claude/clients/rescue/erp-integration/sap-connector/requirements/

Effective = merge(
  ~/.claude/CLAUDE.md,                    # Global
  ~/.claude/clients/rescue/CLAUDE.md,             # Client
  ~/.claude/clients/rescue/erp-integration/CLAUDE.md,  # Project
  .../sap-connector/CLAUDE.md,            # Sub-project
  .../requirements/CLAUDE.md              # Milestone
)
```

**Merge rules:**
- Settings (YAML): Last-wins for specified keys, inherit unmentioned
- Sections: Concatenate in ancestor order
- `@override`: Replace entire section from ancestors

#### Scoped RAG Search

```bash
# Narrow: milestone-scoped with parent context
rag search "auth approach" --scope erp-integration/sap-connector

# Broad: all discovery across client
rag search "stakeholder preferences" --phase discovery

# Cross-project patterns
rag search "API rate limiting" --tags api,integration
```

#### Proximity Scoring

Results are boosted based on distance from current scope:
- Same path: 1.0x
- Parent: 0.85x
- Grandparent: 0.70x
- Sibling project: 0.55x
- Client root: 0.50x

#### Commands

```bash
claude context discover ~/.claude/clients/      # Build index from filesystem
claude context add ~/.claude/clients/acme --type client  # Add manually
claude context show ~/.claude/clients/rescue/   # Show effective context
claude template apply implementation-standard ./project/
```

#### Files

| File | Purpose |
|------|---------|
| `~/.claude/context/index.json` | Registry of all context nodes |
| `~/.claude/context/cache/*.json` | Resolved inheritance chains |
| `~/.claude/templates/milestones/` | Milestone templates |

**Documentation:** `~/.claude/docs/adr/2026-01-17-hierarchical-context-architecture.md`

---

## Skills

Interactive workflows invoked by trigger phrases. Located at `~/.claude/skills/`.

### Catalog (9 Skills)

| Skill | Triggers | Purpose |
|-------|----------|---------|
| `solution-architect` | "architect mode", "SA mode" | CRM architecture, ERD, BPMN |
| `project-discovery` | "assess project", "discovery" | Requirements gathering |
| `hubspot-specialist` | "HubSpot API", "tier pricing" | HubSpot platform expertise |
| `pptx` | "create presentation" | PowerPoint creation/editing |
| `doc-coauthoring` | "write a doc", "draft spec" | Collaborative documentation |
| `decision-tracker` | "record decision" | Decision management |
| `memory-init` | "initialize memory" | Project memory setup |
| `ctm` | "show tasks", "ctm" | Task management |
| `init-project` | "init project" | Full project onboarding |

### Async Modes

| Mode | Skills |
|------|--------|
| `never` (interactive) | solution-architect, project-discovery, pptx, doc-coauthoring, decision-tracker, ctm, init-project |
| `auto` | hubspot-specialist |
| `always` | memory-init |

**Full list:** Run `/config-audit` in a session, or `ls ~/.claude/skills/`

---

## Agents

Specialized sub-agents for specific deliverables. Located at `~/.claude/agents/`.

### Quick Reference (94 Agents)

| Category | Agents |
|----------|--------|
| **Diagrams** | erd-generator, bpmn-specialist, lucidchart-generator, system-architecture-visualizer |
| **Documents** | solution-spec-writer, functional-spec-generator, technical-brief-compiler, executive-summary-creator |
| **Presentations** | slide-deck-creator, board-presentation-designer, pitch-deck-optimizer |
| **Analysis** | technology-auditor, discovery-audit-analyzer, options-analyzer, 80-20-recommender |
| **HubSpot** | hubspot-implementation-runbook (orchestrator) + 17 sub-agents |
| **Risk/Commercial** | risk-analyst-[PROJECT], commercial-analyst-[PROJECT], roi-calculator |
| **Knowledge** | knowledge-base-synthesizer, knowledge-base-query, rag-search-agent, document-merger |
| **Reasoning** | reasoning-duo (C+X), reasoning-duo-cg (C+G), reasoning-duo-xg (X+G), reasoning-trio |
| **Token Optimization** | codex-delegate (primary), gemini-delegate (fallback) |
| **Utility** | worker, demo-data-generator |

### Model Distribution

| Model | Count | Use Case |
|-------|-------|----------|
| Haiku | 7 | Simple tasks, status reports, delegation |
| Sonnet | 70 | Standard work, implementation |
| Opus | 7 | Complex architecture, decisions |

### Async Distribution

| Mode | Count | When |
|------|-------|------|
| `always` | 14 | No user interaction needed |
| `auto` | 56 | Claude decides |
| `never` | 14 | Requires user feedback |

### v2.1+ Frontmatter Fields

| Field | Agents Using | Values |
|-------|-------------|--------|
| `memory` | 5 | `user` (ctm-expert, debugger-agent, memory-management-expert), `project` (rag-integration-expert, context-audit-expert) |
| `permissionMode` | 7 | `bypassPermissions` (codex-delegate, gemini-delegate), `plan` (comparable-project-finder, 80-20-recommender, playbook-advisor), `acceptEdits` (decision-memo-generator, executive-summary-creator) |
| `disallowedTools` | 3 | `[Write, Edit, Bash]` on comparable-project-finder, 80-20-recommender, playbook-advisor |
| `context: fork` | 2+ | codex-delegate, notebooklm-verifier + several skills |

### Rules Directory (NEW in v2.0)

Auto-loaded behavioral rules extracted from CLAUDE.md:

```
~/.claude/rules/
├── critical-rules.md          # 8 NEVER rules
├── context-discovery-rule.md  # Drift prevention (4 steps)
├── decision-auto-capture.md   # Trigger phrases + behavior
├── deviation-handling.md      # Type/trigger/action table
└── adhd-focus-support.md      # Focus support + guide ref
```

All `.md` files in `~/.claude/rules/` are auto-loaded as user-level memory.

### Auto-Invoke Distribution

| Status | Count | Behavior |
|--------|-------|----------|
| `auto_invoke: true` | 12 | Triggered automatically by context |
| `auto_invoke: false` | 72 | Manual invocation only |

**Auto-invoke agents:** erd-generator, bpmn-specialist, lucidchart-generator, rag-search-agent, brand-kit-extractor, hubspot-implementation-runbook, proposal-orchestrator, reasoning-duo, reasoning-duo-cg, reasoning-trio, codex-delegate, gemini-delegate

**Full list:** Run `/config-audit` in a session, or `ls ~/.claude/agents/`
**Auto-invoke PRD:** `~/.claude/PRD-auto-invoke-rollout.md`

---

## Plugins

Marketplace plugins for extended capabilities. Located at `~/.claude/plugins/`.

### Installed Plugins (4)

| Plugin | Features |
|--------|----------|
| `visual-documentation-skills` | HTML diagrams, flowcharts, timelines, dashboards |
| `doc-tools` | PDF generation, LaTeX, ASCII diagram validation |
| `itp` | graph-easy, semantic-release, ADR workflows |
| `feature-dev` | 7-phase feature development workflow |

### Usage

```bash
# Install plugin
npx claude-plugins install @marketplace/plugin-name

# List installed
npx claude-plugins list

# Invoke
/feature-dev "Add user authentication"
```

---

## Hooks

Automated actions triggered by Claude Code events.

### Configured Hooks (13 Events)

| Event | Script | Purpose | Flags |
|-------|--------|---------|-------|
| **SessionStart** | `device-check.sh` | Device profile detection | `once: true` |
| | `ctm/ctm-session-start.sh` | Briefing + health check | `once: true` |
| | `proactive-rag-surfacer.sh` | Surface relevant RAG docs | `once: true` |
| | `sync-memory.sh` | Sync global MEMORY.md | `once: true` |
| | `enrich-project-memory.sh` | CTM+lessons enrichment | `once: true` |
| **UserPromptSubmit** | `global-privacy-guard.sh` | Privacy data scanning | |
| | (inline) | Timestamp injection | |
| | (inline) | Enhance mode injection | `once: true` |
| | `csb-approve-handler.py` | CSB approval handler | |
| **PreToolUse** | `csb-write-guard.py` | Write security guard | matcher: Write |
| | `csb-edit-guard.py` | Edit security guard | matcher: Edit |
| | `outgoing-data-guard.py` | Outgoing data guard | matcher: Bash |
| | `csb-bash-guard.py` | Bash security guard | matcher: Bash |
| | `search-routing-reminder.sh` | Search routing hints | matcher: Grep/Glob |
| | `csb-pretool-defense.sh` | Pre-tool defense | matcher: Read/WebFetch |
| **PostToolUse** | `observation-logger.sh` | Session observation capture | |
| | `rag-index-on-write.sh` | Auto-index files (debounced) | matcher: Write/Edit |
| | `csb-posttool-scanner.py` | Post-tool scanning | matcher: Read/WebFetch |
| | `csb-webfetch-cache.py` | WebFetch caching | matcher: WebFetch |
| | `pattern-tracker.sh` | Pattern tracking | |
| **PostToolUseFailure** | `observation-logger.sh` | Capture tool failures | |
| **PreCompact** | `memory-flush-precompact.sh` | Extract decisions/learnings | |
| | `save-conversation.sh` | Save conversation | |
| | `ctm/ctm-pre-compact.sh` | CTM checkpoint | |
| **Stop** | `session-compressor.sh` | Compress observations | |
| **SessionEnd** | `save-conversation.sh` | Save conversation | |
| | `ctm/ctm-session-end.sh` | CTM final save | |
| | `claude-config-backup.sh` | Config backup | |
| | `session-compressor.sh` | Compress observations | |
| **PermissionRequest** | `permission-auto-handler.sh` | Auto-approve/deny patterns | |
| **SubagentStart** | `subagent-logger.sh` | Log agent spawning | |
| **Notification** | `notification-sound.sh` | Play sound on notification | |
| **TeammateIdle** | `subagent-logger.sh` | Log teammate idle events | |
| **TaskCompleted** | `subagent-logger.sh` | Log task completion events | |

### Hook Locations

```
~/.claude/hooks/
├── ctm/
│   ├── ctm-session-start.sh    # Briefing + git context + health
│   ├── ctm-pre-compact.sh      # Checkpoint
│   ├── ctm-session-end.sh      # Final save
│   └── ctm-user-prompt.sh      # Context injection on prompt
├── save-conversation.sh        # Export conversation to file
├── rag-index-on-write.sh       # Auto-index on Write/Edit (debounced + locked)
├── proactive-rag-surfacer.sh   # Surface relevant RAG docs at session start
├── device-check.sh             # Device profile detection
├── global-privacy-guard.sh     # Privacy data scanning
├── csb-write-guard.py          # Write security guard
├── csb-edit-guard.py           # Edit security guard
├── csb-bash-guard.py           # Bash security guard
├── csb-pretool-defense.sh      # Pre-tool defense
├── csb-posttool-scanner.py     # Post-tool scanning
├── csb-webfetch-cache.py       # WebFetch caching
├── csb-approve-handler.py      # CSB approval handler
├── outgoing-data-guard.py      # Outgoing data guard
├── observation-logger.sh       # Session observation capture
├── pattern-tracker.sh          # Pattern tracking
├── search-routing-reminder.sh  # Search routing hints
├── memory-flush-precompact.sh  # Pre-compact memory extraction
├── session-compressor.sh       # Observation compression
├── claude-config-backup.sh     # Config backup on session end
├── permission-auto-handler.sh  # PermissionRequest auto-handler (NEW)
├── subagent-logger.sh          # SubagentStart/Idle/Complete logger (NEW)
├── notification-sound.sh       # Notification sound (NEW)
└── git-post-commit-rag.sh      # Index commits to RAG
```

### Context Preflight Hook

Automatically runs RAG search when user asks a question about the project:

**Triggers on:**
- Questions starting with what/where/how/why/when/which/who
- Questions about "the project", "this codebase", "we discussed"
- Messages containing `?`

**Skips:**
- Commands (fix, create, write, add, run, test, build...)
- Messages shorter than 20 characters
- Projects without `.rag/` folder

**Output:** Injects `<context-preflight>` block with top 3 relevant RAG results.

### RAG Indexing (Debounced)

The `rag-index-on-write.sh` hook includes:
- **Debounce:** 5-second window per file prevents thrashing
- **Lock file:** Prevents concurrent indexing for same project
- **Error logging:** Failures logged to `.rag/.index_errors.log`
- **Activity log:** Successful indexes logged to `.rag/.index_activity.log`

---

## Configuration Files

### settings.json

Main Claude Code configuration:

```json
{
  "permissions": {
    "allow": ["Bash(...)", "mcp__rag-server__*", "mcp__fathom__*", "..."],
    "deny": [],
    "defaultMode": "default"
  },
  "hooks": {
    "SessionStart": ["... (5 hooks, all once: true)"],
    "UserPromptSubmit": ["... (5 hooks, enhance once: true)"],
    "PreToolUse": ["... (8 hooks with matchers)"],
    "PostToolUse": ["... (6 hooks with matchers)"],
    "PostToolUseFailure": ["observation-logger.sh"],
    "PreCompact": ["... (3 hooks)"],
    "Stop": ["session-compressor.sh"],
    "SessionEnd": ["... (4 hooks)"],
    "PermissionRequest": ["permission-auto-handler.sh"],
    "SubagentStart": ["subagent-logger.sh"],
    "Notification": ["notification-sound.sh"],
    "TeammateIdle": ["subagent-logger.sh"],
    "TaskCompleted": ["subagent-logger.sh"]
  },
  "statusLine": { "type": "command", "command": "~/.claude/scripts/status-line.sh" },
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "enabledPlugins": {
    "visual-documentation-skills@...": true,
    "doc-tools@...": true,
    "itp@...": true,
    "dotfiles-tools@...": true,
    "statusline-tools@...": true,
    "iterm2-layout-config@...": true
  },
  "attribution": { "commit": "Co-Authored-By: ...", "pr": "" },
  "plansDirectory": "~/.claude/plans",
  "spinnerTipsEnabled": false,
  "spinnerVerbs": { "mode": "append", "verbs": ["Architecting", "Brewing", "Orchestrating", "Consulting"] }
}
```
```

### statusline.sh

Custom status bar showing:
- Working directory
- Current model
- Context usage %
- Cache %
- 5-hour billing block remaining
- Session duration
- Session ID
- Time

### CLAUDE.md

Master instructions loaded every session:
- Partnership principles
- Memory stack overview
- Auto-invoke rules
- Decision auto-capture
- Model selection guidance
- Working patterns

---

## Commands Reference

### CTM Commands

| Command | Description |
|---------|-------------|
| `ctm status` | Show current state |
| `ctm brief` | Session briefing |
| `ctm list [--all]` | List tasks |
| `ctm spawn "title" [--priority high]` | Create task |
| `ctm switch <id>` | Switch to task |
| `ctm pause [id]` | Pause task |
| `ctm complete [id]` | Complete task |
| `ctm context add --decision "..."` | Add decision |
| `ctm checkpoint` | Save state |
| `ctm restore [--list]` | Restore from checkpoint |
| `ctm repair` | Fix corrupted data |
| `ctm delegate "task" --agent worker` | Delegate via CDP |

### RAG Commands

| Command | Description |
|---------|-------------|
| `rag init` | Initialize RAG |
| `rag index <path>` | Index files/folders |
| `rag reindex` | Rebuild index |
| `rag search "query"` | Semantic search |
| `rag status` | Check status |
| `rag list` | List indexed docs |

### Validation Commands

| Command | Description |
|---------|-------------|
| `~/.claude/scripts/validate-setup.sh` | Full validation |
| `~/.claude/scripts/validate-setup.sh --quick` | Quick check |

### Performance Monitoring

| Command | Description |
|---------|-------------|
| `~/.claude/scripts/check-load.sh` | Full load report with recommendation |
| `~/.claude/scripts/check-load.sh --status-only` | Just OK/CAUTION/HIGH_LOAD |
| `~/.claude/scripts/check-load.sh --json` | JSON output for parsing |

### Usage Tracking

| Command | Description |
|---------|-------------|
| `ccusage` | Daily usage |
| `ccusage weekly` | Weekly breakdown |
| `ccusage monthly` | Monthly summary |
| `ccusage session` | Per-session |
| `ccusage blocks` | Billing blocks |

---

## Workflows

### Starting a New Project

```bash
# 1. Navigate to project
cd /path/to/project

# 2. Initialize everything
# Say: "init project"

# This creates:
# - .rag/ (semantic search)
# - .claude/context/ (decisions, sessions)
# - Git hooks (changelog)
```

### Daily Workflow

1. **Session Start** → CTM briefing shows pending tasks + health check
2. **Work** → Use skills/agents as needed
3. **Decisions** → Auto-captured when detected
4. **Session End** → Conversation saved, state checkpointed

### Making Decisions

```
User: "Let's go with PostgreSQL for the database"
Claude: "I notice we made a decision: **Use PostgreSQL for database**.
         Want me to record this to DECISIONS.md?"
User: "yes"
Claude: [Records to DECISIONS.md]
```

### Delegating Work

```
# Via CTM
ctm delegate "Analyze customer data" --agent worker

# Claude creates:
# - .agent-workspaces/{task-id}/HANDOFF.md
# - Spawns worker agent in background
# - Agent writes OUTPUT.md when done
```

---

## Troubleshooting

### Common Issues

#### "Ollama not running"

```bash
# Start Ollama
ollama serve

# Verify
pgrep -x ollama
```

#### "CTM not initialized"

```bash
# Repair CTM
~/.claude/ctm/scripts/ctm repair

# Or reinitialize
rm -rf ~/.claude/ctm/*.json
~/.claude/ctm/scripts/ctm status
```

#### "Agent count mismatch"

```bash
# Check actual count
ls ~/.claude/agents/*.md | wc -l

# Update docs
# Edit AGENTS_INDEX.md, CLAUDE.md, AGENT_STANDARDS.md
```

#### "RAG not working"

```bash
# Check status
rag status

# Verify Ollama
curl http://localhost:11434/api/tags

# Reindex
rag reindex
```

### Validation

Run the validation script to check everything:

```bash
~/.claude/scripts/validate-setup.sh        # Full validation (36 checks)
~/.claude/scripts/validate-setup.sh --quick # Quick health check
```

This checks:
- Agent counts across all docs
- Async frontmatter in agents
- Hook configuration + executability
- CTM files
- RAG/Ollama status
- Documentation completeness
- **Inventory drift** (inventory.json vs actual counts)
- **Permissions sprawl** (warns if >100, fails if >200)
- Dangerous permission patterns

---

## Maintenance

### Inventory System

The `inventory.json` file is the **single source of truth** for configuration state:

```bash
# Generate/refresh inventory
~/.claude/scripts/generate-inventory.sh
```

**Contents:**
- Agent count, skill count, hook count
- Model distribution (haiku/sonnet/opus)
- Async mode distribution (always/auto/never)
- Enabled plugins
- MCP servers

**Freshness:** Regenerate if stale (>24h) — validator warns automatically.

**Usage:** Detect configuration drift before it causes issues.

### Regular Tasks

| Frequency | Task | Command |
|-----------|------|---------|
| Daily | Check briefing | `ctm brief` |
| Weekly | Review decisions | Check `DECISIONS.md` |
| Weekly | Clean workspaces | `ctm workspace clean` |
| Weekly | Regenerate inventory | `generate-inventory.sh` |
| Weekly | Clean conversations | `cleanup-conversations.sh` (30 days) |
| Weekly | Clean debug files | `cleanup-debug.sh` (7 days) |
| Monthly | Full validation | `validate-setup.sh` |
| Monthly | Prune RAG index | `rag reindex` |

### Retention Policies

Automated cleanup scripts in `~/.claude/scripts/` manage storage growth:

| Directory | Retention | Script | Default Size |
|-----------|-----------|--------|--------------|
| `conversation-history/` | 30 days | `cleanup-conversations.sh` | ~3.6 GB |
| `debug/` | 7 days | `cleanup-debug.sh` | ~957 MB |
| `observations/` | 30 days | Auto (observation-config.json) | ~572 KB |
| `ctm/checkpoints/` | 90 days | Manual (`gzip` old files) | ~84 MB |
| `file-history/` | 90 days | Manual | ~154 MB |

**Usage:**

```bash
# Run with default retention
~/.claude/scripts/cleanup-conversations.sh      # 30 days
~/.claude/scripts/cleanup-debug.sh               # 7 days

# Custom retention (days)
~/.claude/scripts/cleanup-conversations.sh 14    # Keep 14 days
~/.claude/scripts/cleanup-debug.sh 3             # Keep 3 days
```

**Output:** Reports files deleted and size before/after.

### Adding New Agents

1. Create `~/.claude/agents/new-agent.md`
2. Include required frontmatter:
```yaml
---
name: new-agent
description: ...
model: sonnet
async:
  mode: auto
  prefer_background: [...]
  require_sync: [...]
---
```
3. Update `AGENTS_INDEX.md`
4. Regenerate inventory: `~/.claude/scripts/generate-inventory.sh`
5. Run `validate-setup.sh`

### Adding New Skills

1. Create `~/.claude/skills/new-skill/SKILL.md`
2. Include frontmatter with async settings
3. Update `SKILLS_INDEX.md`
4. Update `CLAUDE.md` Core Skills table

### Backup

```bash
# Backup entire config
cp -r ~/.claude ~/.claude-backup-$(date +%Y%m%d)

# Backup just CTM state
cp -r ~/.claude/ctm ~/.claude/ctm-backup-$(date +%Y%m%d)
```

### Updates

```bash
# Update ccusage
npm update -g ccusage

# Update plugins
npx claude-plugins update

# Update Ollama
brew upgrade ollama
```

---

## Troubleshooting

### MCP Server Not Loading

**Symptom:** MCP tools don't appear in session. `ListMcpResources` returns empty despite server being in `enabledMcpjsonServers`.

**Diagnosis:**
```bash
# Check configured path
cat ~/.mcp.json | jq '.mcpServers.SERVER_NAME'

# Verify path exists
ls -la /path/from/config
```

**Common causes:**
1. **Path mismatch** — Config points to non-existent file (e.g., `dist/index.js` when actual server is `server.py`)
2. **Wrong interpreter** — Config uses `node` but server is Python, or vice versa
3. **Missing venv** — Python server needs `.venv/bin/python`, not system python

**Fix:** Update `~/.mcp.json` with correct command and args:
```json
"server-name": {
  "command": "/path/to/.venv/bin/python",  // or "node" for JS
  "args": ["/path/to/server.py"],
  "env": { ... }
}
```

Then restart Claude Code or run `/mcp` to reload.

### RAG Search Returns Empty

**Diagnosis:**
```bash
rag status           # Check if initialized
rag list             # See what's indexed
ollama list          # Ensure embedding model exists
```

**Common causes:**
1. RAG not initialized — run `rag init`
2. Files not indexed — run `rag index /path`
3. Ollama not running — `ollama serve`
4. Missing embedding model — `ollama pull mxbai-embed-large`

### Hooks Not Firing

**Diagnosis:**
```bash
# Test hook manually
~/.claude/hooks/HOOK_NAME.sh

# Check permissions
ls -la ~/.claude/hooks/
```

**Common causes:**
1. Missing execute permission — `chmod +x hook.sh`
2. Missing shebang — add `#!/bin/bash` at top
3. Wrong path in settings.json

---

## Quick Reference Card

### Essential Commands

```bash
# Task Management
ctm brief                    # What should I work on?
ctm spawn "task" --switch    # Start new task
ctm complete                 # Finish current task

# Search
rag search "query"           # Find in docs

# Validation
validate-setup.sh            # Check everything (36 checks)
validate-setup.sh --quick    # Quick health check
generate-inventory.sh        # Regenerate inventory.json

# Usage
ccusage                      # Today's cost
```

### Trigger Phrases

| Say This | Gets This |
|----------|-----------|
| "architect mode" | Solution Architect skill |
| "init project" | Project onboarding |
| "create presentation" | PPTX skill |
| "we decided X" | Decision auto-capture |
| "/feature-dev" | Feature development workflow |

### Status Bar

```
~/.claude | Opus | Ctx:45% | Cache:82% | ⏱2h34m | 1m23s | #a1b2c3d4 | 15:47
    │        │       │          │          │         │        │         │
    │        │       │          │          │         │        │         └─ Time
    │        │       │          │          │         │        └─ Session ID
    │        │       │          │          │         └─ Duration
    │        │       │          │          └─ 5hr block remaining
    │        │       │          └─ Cache hit %
    │        │       └─ Context usage
    │        └─ Model
    └─ Directory
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-02-08 | **Insights-driven optimization:** Added 2-attempt pivot rule to Execution Directness (CLAUDE.md). Created `/reindex` skill (quick fire-and-forget RAG reindex). Added headless aliases to .zshrc (`claude-reindex`, `claude-audit`). postEdit validation hook already existed (`validate-syntax.sh`). Skills: 45→46. |
| 2.0 | 2026-02-07 | **v2.1.37 feature parity upgrade:** Added `once: true` to 6 hooks (all SessionStart + enhance-mode). Created `~/.claude/rules/` directory with 5 extracted rules from CLAUDE.md (-49 lines). Added 6 new hook events (PermissionRequest, SubagentStart, Notification, PostToolUseFailure, TeammateIdle, TaskCompleted) with 3 new scripts. Added MCP wildcard permissions (5 servers). Added v2.1+ agent frontmatter: `memory:` on 5 agents, `permissionMode:` on 7 agents, `disallowedTools:` on 3 agents. Added keybindings (ctrl+shift+p model picker). Added settings: attribution, plansDirectory, spinnerTipsEnabled, spinnerVerbs. Registered device-check.sh. Hook events: 7->13. Total: 23 files changed (14 edited, 9 created). |
| 1.9 | 2026-02-07 | Performance & functionality upgrade: Fixed Python PATH (scancode venv pollution in .zshrc). Indexed 89 observation summaries to RAG (142 chunks, was empty). Fixed session-compressor.sh to auto-index summaries after compression. Expanded Google Workspace MCP (added calendar, sheets, tasks — 3→6 tools). Created 3 agents: `hubspot-impl-reporting-analytics`, `salesforce-mapping-activities`, `proposal-generator` (130→133). Updated routing tables in routers and CLAUDE.md. |
| 1.8 | 2026-02-07 | Round 2 cleanup: Deleted 17 duplicate `-ignore-and-do-not-rag-index` agent files (147->130 agents). Created `.ragignore`. Deleted 14 more orphan hooks (cascading reference check). Cleaned CTM queue (421->2 phantom entries). Extracted statusLine to `scripts/status-line.sh`. Ran storage cleanup (720MB debug freed). Synced counts: 130 agents, 45 skills, 25 hooks, 6 plugins. |
| 1.7 | 2026-02-07 | Comprehensive cleanup: Deleted nested `.claude/.claude/` mirror (~1.6GB). Fixed 3 broken CLAUDE.md references. Consolidated settings.json hooks (351->291 lines). Added Salesforce-HubSpot Mapping + HubSpot API routing tables. Deleted 14 dead scripts (coord-*, migrate-*), 12 orphan hooks, 2 inactive files, deprecated docs. Created retention policy scripts (`cleanup-conversations.sh`, `cleanup-debug.sh`). Updated counts: 147 agents, 44 skills, 6 plugins. |
| 1.6 | 2026-02-07 | Consolidated: Single authoritative `~/.claude/CLAUDE.md` (749 lines). Merged full + hybrid versions, deleted `.slim`/`.full` variants and backups, disabled swap scripts (`subagent-slim.sh`, `claude-wrapper.sh`). Added: ADHD Focus Support, Search Tool Selection, Context Management (flush/pruning/inspection), Deviation Handling, Slack Integration, Observation Memory, RAG Search Order sections. |
| 1.5 | 2026-02-07 | Added: Per-project memory auto-enrichment (`enrich-project-memory.sh`) - SessionStart hook appends CTM decisions/blockers + high-confidence lessons to project MEMORY.md. 24h cooldown, 200-line limit, domain keyword inference (Huble→HubSpot). |
| 1.4 | 2026-02-05 | Added: Multi-account support, auto memory system (global + per-project MEMORY.md), Opus 4.6 upgrade (adaptive thinking, 128K output), GitHub MCP server, CSB whitelist expansion for own config files, agent frontmatter standardization (147 agents), permission consolidation (343 → 56), dotfiles history cleanup. Inventory: 147 agents, 41 skills, 46 hooks, 4 MCP servers, 21 plugins. |
| 1.3 | 2026-01-22 | Added: Hierarchical context architecture, agent cross-reference system |
| 1.2 | 2026-01-16 | Added: Troubleshooting section (MCP path mismatch, RAG empty, hooks not firing) |
| 1.1 | 2026-01-15 | Added: inventory.json manifest, context-preflight hook, RAG debounce/lock, codex-delegate + reasoning-duo agents, enhanced validation (36 checks) |
| 1.0 | 2026-01-09 | Initial comprehensive documentation |

---

*This configuration represents ~7 weeks of iteration on Claude Code workflows for CRM consulting and solution architecture work.*
