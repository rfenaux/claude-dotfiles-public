# Cognitive Continuity (CC)

> Created: 2026-01-08 | Version: 1.0

## Overview

**Cognitive Continuity** is a bio-inspired system that enables Claude to maintain context across conversations and manage multiple concurrent tasks. It mimics how the human brain's prefrontal cortex manages working memory, attention, and task switching.

Previously called "CTM" (Cognitive Task Manager), the system is now branded as **Cognitive Continuity** to better reflect its core purpose: enabling Claude to "continue thinking" across sessions.

**Key Concepts:**
- **Agents**: Represent active task contexts (like mental "threads")
- **Priority Queue**: Tasks are ranked by urgency, recency, and value
- **Working Memory**: Limited capacity, with intelligent eviction
- **Checkpoints**: Snapshots for recovery and resumption
- **Consolidation**: Extract decisions/learnings to project memory

---

## For Users

### Quick Start

```bash
# Check CTM status
~/.claude/ctm/scripts/ctm status

# Create a new task
~/.claude/ctm/scripts/ctm spawn "Fix login bug" --priority high --switch

# List all tasks
~/.claude/ctm/scripts/ctm list --all

# Get session briefing
~/.claude/ctm/scripts/ctm brief
```

### Common Commands

| Command | Description |
|---------|-------------|
| `ctm status` | Show current state and active agent |
| `ctm list [--all]` | List agents (active by default) |
| `ctm spawn <title>` | Create new agent |
| `ctm switch <id>` | Switch to an agent |
| `ctm pause [id]` | Pause current/specified agent |
| `ctm complete [id]` | Mark agent complete |
| `ctm brief` | Generate session briefing |
| `ctm queue` | Show priority queue |
| `ctm checkpoint` | Save current state |
| `ctm restore [--list]` | Restore from checkpoint |
| `ctm context show` | View agent decisions/learnings |
| `ctm context add --decision "..."` | Add a decision |
| `ctm repair` | Check and repair CTM data |
| `ctm help` | Show all commands |

### Workflow Example

```bash
# Morning: Get briefing
ctm brief

# Start working on top priority
ctm switch abc123

# Record a decision
ctm context add --decision "Using PostgreSQL for persistence"

# Pause for urgent task
ctm spawn "Urgent: Server down" --priority critical --switch

# After fixing, complete it
ctm complete

# Return to previous task (auto-suggested)
ctm switch abc123
```

---

## For Claude (Auto-Invocation Rules)

### When to Use CTM

| Situation | Action |
|-----------|--------|
| User starts new major task | `ctm spawn "<task>" --switch` |
| User says "let's work on X" | `ctm switch` to matching agent |
| User says "pause this" | `ctm pause` |
| Task is done | `ctm complete` with extraction |
| Significant decision made | `ctm context add --decision "..."` |
| Learning discovered | `ctm context add --learning "..."` |
| Session start | Check `ctm brief` for context |
| Before context compaction | `ctm checkpoint` (auto via hook) |

### Trigger Phrases

CTM should activate when the user says:
- "Let's work on..." / "Switch to..."
- "This is done" / "Mark complete"
- "What was I working on?"
- "Pause this" / "I need to switch"
- "What's the priority?"

### Auto-Invocation via Hooks

CTM hooks are installed in `~/.claude/settings.json`:

| Hook | Trigger | Action |
|------|---------|--------|
| `SessionStart` | Claude Code starts | Show briefing, start session |
| `PreCompact` | Before context compaction | Create checkpoint |
| `SessionEnd` | Claude Code exits | Final save |
| `UserPromptSubmit` | User sends message | Detect task switches |

### Integration with Project Memory

When an agent is completed, CTM:
1. Extracts decisions and learnings
2. Consolidates to `project/.claude/context/DECISIONS.md`
3. Indexes to RAG if `.rag/` exists

---

## Architecture

### File Structure

```
~/.claude/ctm/
├── config.json           # Global configuration
├── index.json            # Agent index for fast lookups
├── scheduler.json        # Priority queue state
├── working-memory.json   # Hot agents cache
├── agents/               # Individual agent files
│   ├── abc123.json
│   └── def456.json
├── checkpoints/          # State snapshots
│   └── 20260108_114934/
├── logs/                 # Error and hook logs
├── lib/                  # Python modules
│   ├── agents.py
│   ├── scheduler.py
│   ├── briefing.py
│   ├── extraction.py
│   ├── consolidation.py
│   ├── errors.py
│   └── style.py
└── scripts/
    └── ctm               # CLI entry point
```

### Agent Structure

Each agent (`.json`) contains:

```json
{
  "id": "abc123",
  "task": {
    "title": "Implement login feature",
    "goal": "Add OAuth2 login to the app",
    "acceptance_criteria": []
  },
  "context": {
    "project": "/path/to/project",
    "key_files": ["src/auth.py"],
    "decisions": [{"text": "Using OAuth2", "timestamp": "..."}],
    "learnings": [{"text": "API rate limited", "timestamp": "..."}]
  },
  "state": {
    "status": "active|paused|blocked|completed|cancelled",
    "progress_pct": 50,
    "current_step": "Implementing token refresh"
  },
  "priority": {
    "level": "high",
    "urgency": 0.8,
    "value": 0.7,
    "computed_score": 0.75
  },
  "timing": {
    "created_at": "2026-01-08T10:00:00Z",
    "last_active": "2026-01-08T11:30:00Z",
    "session_count": 3
  }
}
```

### Priority Calculation

Priority score is computed as:

```
score = Σ(weight × factor)

Factors:
- urgency (0.25): deadline proximity
- recency (0.25): exponential decay from last_active
- value (0.20): task importance
- novelty (0.15): decay from creation
- user_signal (0.10): manual priority boost
- error_boost (0.05): bump for failed tasks
```

---

## Project Integration

### Enable CTM for a Project

CTM is **global** - it works across all projects automatically. Agent context includes the project path, and you can filter by project:

```bash
ctm list --project /path/to/project
```

### Consolidation to Project Memory

When completing an agent, decisions/learnings can be extracted to:

```
project/.claude/context/DECISIONS.md
project/.claude/context/SESSIONS.md
```

To enable auto-consolidation:
1. Ensure `.claude/context/` exists in project
2. Complete agents with `ctm complete` (extraction is automatic)
3. Or manually: `ctm consolidate`

### RAG Integration

If project has `.rag/` folder:
- Completed agents are indexed to RAG
- Agent context becomes searchable via `rag_search`

---

## Hooks Installation

To install CTM hooks (auto-briefing, checkpoints):

```bash
ctm hooks install
ctm hooks status  # Verify installation
```

Hooks are added to `~/.claude/settings.json` under:
- `hooks.SessionStart`
- `hooks.PreCompact`
- `hooks.SessionEnd`

---

## Error Handling & Recovery

### Error Codes

| Code Range | Category |
|------------|----------|
| CTM-0XX | Configuration errors |
| CTM-1XX | Agent errors |
| CTM-2XX | Scheduler errors |
| CTM-3XX | Memory errors |
| CTM-4XX | Integration errors |
| CTM-5XX | Hook errors |
| CTM-6XX | Index errors |

### Repair Command

If CTM data becomes corrupted:

```bash
# Full repair
ctm repair

# Specific repairs
ctm repair --config
ctm repair --agents
ctm repair --scheduler
ctm repair --index
```

Backups are created automatically before repairs.

### Restore from Checkpoint

```bash
# List checkpoints
ctm restore --list

# Restore latest
ctm restore

# Restore specific
ctm restore 20260108_114934
```

---

## Performance Notes

- **Caching**: Scheduler and agents use mtime-based caching
- **Max agents**: 20 in cache, unlimited on disk
- **Checkpoints**: Auto-pruned to keep last 10
- **Index**: Maintained separately for O(1) lookups

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | A task context with state, decisions, and progress |
| **Checkpoint** | A snapshot of agent state for recovery |
| **Consolidation** | Extracting decisions/learnings to project memory |
| **Working Memory** | In-memory cache of hot agents |
| **Priority Queue** | Ordered list of agents by computed score |
| **Briefing** | Summary of pending tasks at session start |

---

## Developer Guide (For Claude)

If asked to update, fix, or extend Cognitive Continuity, here's the architecture:

### Code Location

```
~/.claude/ctm/
├── lib/                    # Python modules (the brains)
│   ├── ctm.py              # CLI entry point, all commands
│   ├── agents.py           # Agent CRUD, caching
│   ├── scheduler.py        # Priority queue, switching
│   ├── briefing.py         # Session briefings
│   ├── extraction.py       # Decision/learning extraction
│   ├── consolidation.py    # Write to DECISIONS.md
│   ├── triggers.py         # Detect task switches in prompts
│   ├── resumption.py       # Context restoration cues
│   ├── memory.py           # Working memory management
│   ├── integration.py      # Hook installation
│   ├── errors.py           # Error catalog, recovery
│   ├── config.py           # Configuration loading
│   └── style.py            # CLI colors/formatting
├── scripts/
│   ├── ctm                 # Main CLI (calls lib/ctm.py)
│   └── ctm-migrate         # Project migration helper
├── config.json             # Global settings
├── index.json              # Agent index
├── scheduler.json          # Queue state
└── agents/                 # Individual agent JSON files
```

### Hooks Location

```
~/.claude/hooks/ctm/
├── ctm-session-start.sh    # Shows briefing on session start
├── ctm-pre-compact.sh      # Creates checkpoint before compaction
├── ctm-session-end.sh      # Final save on exit
└── ctm-user-prompt.sh      # Detects task-switch triggers
```

### Adding a New Command

1. Add `cmd_newcommand(args)` function in `lib/ctm.py`
2. Add argument parser in `main()` function
3. Add to `commands` dict in `main()`
4. Update `cmd_help()` docstring

### Adding a New Error Code

Edit `lib/errors.py` → `ERROR_CATALOG`:
```python
"CTM-XXX": ("Error message", ErrorSeverity.MEDIUM, "Recovery hint"),
```

### Testing Changes

```bash
# Test CLI
~/.claude/ctm/scripts/ctm status
~/.claude/ctm/scripts/ctm repair

# Test hooks
~/.claude/hooks/ctm/ctm-session-start.sh
```

### Key Design Decisions

1. **Global, not per-project**: CTM is installed once, tracks project path per agent
2. **File-based state**: JSON files, no database dependency
3. **Caching with mtime**: Reload only when files change
4. **Graceful degradation**: Errors don't crash, return defaults
5. **Hook-based integration**: Uses Claude Code's hook system

### RAG Dashboard Integration

API endpoints in `~/.claude/rag-dashboard/server.py`:
- `GET /api/ctm/status` — Returns agent counts, session info
- `GET /api/ctm/brief` — Returns full briefing text

---

## Lessons Integration

CTM context is used to auto-surface relevant lessons on session start:

```
Session Start
    │
    └─→ lesson-surfacer.sh
        ├─→ Read CTM index.json → extract active task title + tags
        ├─→ Combine with directory context
        ├─→ Search lessons.jsonl
        └─→ Surface top 3 relevant lessons
```

**Example:** If your active CTM task is "HubSpot workflow integration", lessons about HubSpot API quirks, workflow best practices, and deployment patterns are automatically surfaced at session start.

This connects **what you're working on** (CTM) with **what you've learned** (Lessons).

See: `~/.claude/LESSONS_GUIDE.md` → "Automatic Surfacing (CTM Integration)"

---

## Cross-References

CTM integrates with other systems in the Claude Code stack:

| System | Integration Point | Reference |
|--------|-------------------|-----------|
| **Lessons** | Task context used to surface relevant lessons on session start | `~/.claude/LESSONS_GUIDE.md` |
| **CDP** | `ctm delegate` creates CDP workspace + HANDOFF.md | `~/.claude/CDP_PROTOCOL.md` |
| **RAG** | Completed agents indexed to RAG; briefing includes RAG status | `~/.claude/RAG_GUIDE.md` |
| **Project Memory** | Decisions extracted to `DECISIONS.md` on completion | `~/.claude/CLAUDE.md` §Project Memory |
| **Agents** | 80+ specialized agents available for delegation | `ls ~/.claude/agents/` |
| **Skills** | `ctm` skill provides interactive interface | `ls ~/.claude/skills/` |
| **Hooks** | SessionStart/PreCompact/SessionEnd trigger CTM actions | `~/.claude/settings.json` |

**Master instructions:** `~/.claude/CLAUDE.md`

---

## Version 2.0 Features (2026-01)

CTM v2.0 introduces advanced memory management based on state-of-the-art research from MemGPT, Mem0, and cognitive science.

### 4-Tier Memory Hierarchy

Inspired by MemGPT's virtual context management:

```
┌─────────────────────────────────────────────────┐
│  L1: Active Context (current task + 2 hot)      │  ← In-prompt
│  ↓ compress & evict at 70% pressure             │
├─────────────────────────────────────────────────┤
│  L2: Working Memory (5 agents, 8K tokens)       │  ← Fast retrieval
│  ↓ summarize & archive                          │
├─────────────────────────────────────────────────┤
│  L3: Episodic Store (timestamped sessions)      │  ← Temporal queries
│  ↓ consolidate after 30 days                    │
├─────────────────────────────────────────────────┤
│  L4: Semantic Store (knowledge graph + RAG)     │  ← Semantic search
└─────────────────────────────────────────────────┘
```

**Key Features:**
- Auto-compression when tiers reach 70% capacity
- Intelligent demotion based on access patterns
- Self-directed memory management (like MemGPT)

**Config:** `~/.claude/ctm/config.json` → `memory_tiers` section

### Knowledge Graph

Entity-relationship graph for decisions with semantic search:

```python
# Add decision with conflict detection
kg.add_decision("Use PostgreSQL", "Better for relational data", category="architecture")

# Conflict alert if similar decision exists
# ⚠ Potential conflict detected:
#   New: "Use PostgreSQL for persistence"
#   Existing: "Use SQLite for simplicity" (similarity: 82%)

# Semantic search
kg.search("database decision")  # Returns related entities

# Multi-hop queries
kg.get_related(entity_id, hops=2)  # Get connected entities
```

**Module:** `~/.claude/ctm/lib/knowledge_graph.py`

### Cognitive Load Tracking

Based on research: 23min refocus time, 40% productivity loss from context switching.

```python
# Track task switches
tracker.on_task_switch("project-alpha", "urgent-fix", reason="urgent")

# Get attention residue
residue = tracker.calculate_residue("project-alpha")  # 0.0-1.0

# Focus recommendation
rec = tracker.get_focus_recommendation()
# → "High attention residue (65%). Consider completing interrupted tasks."

# Session stats
stats = tracker.get_session_stats()
# → {switches: 5, total_residue: 0.4, productivity_impact: "25%"}
```

**Module:** `~/.claude/ctm/lib/cognitive_load.py`

### Reflection Pattern

Self-evaluation before marking tasks complete:

```python
# Reflect before completion
result = reflect_before_complete(agent_id)

# Checks:
# - Acceptance criteria achievement
# - Decisions made during task
# - Learnings to extract
# - Reusable patterns identified

if result.ready_to_complete:
    # All criteria met, proceed
else:
    # Show blockers and suggestions
```

**Module:** `~/.claude/ctm/lib/reflection.py`

### Semantic Triggers

Natural language task references using embeddings:

```python
# Old (keyword only)
check_for_switch("continue project-alpha")  # Works

# New (semantic)
check_for_switch_semantic("let's work on the QuickBooks thing")
# → accounting-ph1 (semantic match)

check_for_switch_semantic("back to the ERP integration")
# → erp-integration (semantic match)
```

**Module:** `~/.claude/ctm/lib/triggers.py`

### New Config Options

```json
{
  "memory_tiers": {
    "enabled": true,
    "l1_max_agents": 2,
    "l1_token_budget": 4000,
    "l2_max_agents": 5,
    "l2_token_budget": 8000,
    "l3_retention_days": 30,
    "pressure_threshold": 0.7,
    "compression_model": "haiku",
    "auto_manage": true
  },
  "self_management": {
    "enabled": true,
    "pressure_threshold": 0.7,
    "auto_summarize": true,
    "summarize_model": "haiku"
  }
}
```

### Research Sources

- [MemGPT](https://research.memgpt.ai/) - Virtual context management
- [Mem0](https://mem0.ai/research) - Hybrid vector + knowledge graph
- [Zep](https://blog.getzep.com/) - Temporal knowledge graphs
- [Cognitive Workspace](https://arxiv.org/html/2508.13171v1) - Active memory
- Princeton PFC Research - Cognitive block reuse

---

---

## Version 2.1: Multi-Agent Shared Memory (2026-01)

Enables related agents to share context through memory pools.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Memory Pool                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Fragment   │  │  Fragment   │  │  Fragment   │         │
│  │ (decision)  │  │ (learning)  │  │ (context)   │         │
│  │ owner: A    │  │ owner: B    │  │ owner: A    │         │
│  │ shared: yes │  │ shared: yes │  │ shared: no  │ ← private│
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
         ↑ publish              ↓ subscribe
    ┌────┴────┐            ┌────┴────┐
    │ Agent A │            │ Agent B │
    │ (active)│            │ (paused)│
    └─────────┘            └─────────┘
```

### Access Levels

| Level | Description |
|-------|-------------|
| `PRIVATE` | Only owner can read |
| `PROJECT` | All agents in same project |
| `TAGGED` | Agents with matching tags |
| `PUBLIC` | All agents |

### Usage

```python
# Share a decision from an agent
from agents import share_agent_decision
share_agent_decision("agent123", "Using PostgreSQL for persistence")

# Get shared context from other agents
from agents import get_agent_shared_context
context = get_agent_shared_context("agent123")
# → {"decisions": [...], "learnings": [...], "contributors": [...]}

# Direct pool access
from shared_memory import get_project_pool, FragmentType
pool = get_project_pool("/path/to/project")
pool.publish("agent123", FragmentType.DECISION, "Using OAuth2", tags=["auth"])

# Query shared fragments
decisions = pool.query("agent123", ftypes=[FragmentType.DECISION])

# Subscribe to updates
pool.subscribe("agent456", filter_types=[FragmentType.BLOCKER],
               callback=lambda f: print(f"New blocker: {f.content}"))
```

### Provenance Tracking

Every fragment tracks:
- `created_by`: Original author agent
- `created_at`: Timestamp
- `modified_by`: List of agents who updated
- `accessed_by`: List of agents who read
- `source_files`: Referenced files

### Research Sources

- [ICML Collaborative Memory](https://arxiv.org/html/2505.18279v1) - Multi-user memory sharing with access control
- [Google ADK Context Engineering](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/) - Context patterns for production
- [MongoDB Memory Engineering](https://medium.com/mongodb/why-multi-agent-systems-need-memory-engineering-153a81f8d5be) - Why multi-agent needs memory

**Module:** `~/.claude/ctm/lib/shared_memory.py`

---

## Version 2.2: Project-Context Awareness (2026-01)

CTM now automatically detects which project you're working in and prioritizes tasks accordingly.

### How It Works

1. **Auto-Detection**: When a Claude session starts, CTM detects the project from `$PWD`
2. **Priority Boost**: Tasks belonging to the current project get +20% priority boost
3. **Grouped Briefings**: Session briefings show current-project tasks first
4. **Manual Override**: Use `ctm project set <path>` to manually switch context

### Session Start Behavior

When you start Claude from a project directory:

```
$ cd /Users/me/Projects/client-a
$ claude

[CTM] Loaded 5 agent(s) into working memory
[CTM] 2/8 tasks in client-a | Top: Implement auth flow
  → Top: [auth2026] Implement auth flow (45%)
    Step: JWT validation middleware
```

The format `2/8 tasks in client-a` means:
- 2 tasks belong to the current project (client-a)
- 8 total active tasks across all projects

### Commands

```bash
# Show current project context
ctm project
ctm project show

# Set project context manually
ctm project set /path/to/project

# Clear project context (show all tasks equally)
ctm project clear

# Re-detect from current directory
ctm project detect
```

### Briefing Output

With project context set, briefings group tasks:

```
**Priority Queue**
📁 client-a:
  1. ○ [auth2026] Implement auth flow (45%)
  2. ○ [api2026] API rate limiting (20%)

📂 Other Projects:
  1. ○ [internal2026] Update docs.. (internal-tools)
  2. ○ [review2026] Code review.. (client-b)
     ... and 3 more in other projects
```

### Integration with Scheduler

The scheduler's `calculate_priority()` adds a project boost:

```python
# If task matches current project context
if self.is_project_match(agent):
    score += PROJECT_CONTEXT_BOOST  # +0.20 (20%)
```

This ensures local tasks surface first while still allowing high-priority tasks from other projects to preempt if needed.

**Module:** `~/.claude/ctm/lib/scheduler.py` (project context methods)
**Module:** `~/.claude/ctm/lib/briefing.py` (project-aware formatting)

---

## Version 3.0: Task Intelligence (2026-01)

CTM v3.0 adds time awareness and task dependencies for smarter task management.

### Deadline Management

Set and track deadlines with automatic urgency indicators:

```bash
# Set deadlines
ctm deadline auth2026 2026-02-15      # Absolute date
ctm deadline auth2026 +3d             # Relative: 3 days from now
ctm deadline auth2026 +2w             # 2 weeks
ctm deadline auth2026 +1m             # 1 month

# View/clear deadlines
ctm deadline auth2026                 # Show current deadline
ctm deadline auth2026 clear           # Remove deadline
ctm deadlines                         # List all deadlines
```

**Briefing Output:**
```
**⏰ Deadlines**
🔴 OVERDUE: [api2026] API Integration — 2d overdue
🟠 TODAY: [auth2026] Auth flow — due in 4h
🟡 SOON: [docs2026] Documentation — due in 2d
🟢 [test2026] Testing — due in 5d
```

Urgency levels:
- 🔴 **OVERDUE** - Past deadline
- 🟠 **TODAY** - Due within 24 hours
- 🟡 **SOON** - Due within 3 days
- 🟢 **WEEK** - Due within 7 days

### Task Dependencies

Create tasks with blockers that auto-unblock on completion:

```bash
# Create blocked task
ctm spawn "Login page" --blocked-by auth2026

# Add/remove blockers manually
ctm block login2026 --by auth2026
ctm unblock login2026 --from auth2026
ctm unblock login2026                 # Remove all blockers

# View dependencies
ctm deps auth2026                     # Show task's dependencies
ctm deps --all                        # Show full dependency graph
```

**Auto-Unblocking:**

When a blocker completes, dependent tasks automatically unblock:

```
$ ctm complete auth2026
✓ Completed [auth2026]: Auth setup
  ✓ Unblocked: [login2026] Login page
  ✓ Unblocked: [api2026] API integration
  Next: [login2026] Login page (score: 0.750)
```

**Dependency Visualization:**

Briefings show high-impact blockers and blocked tasks:

```
**🔗 Dependencies**
High-impact (complete to unblock multiple tasks):
  ⚡ [auth2026] Auth setup → unblocks 3 tasks

Blocked tasks:
  ⛔ [login2026] Login page ← auth2026
  ⛔ [api2026] API integration ← auth2026
```

The `ctm deps --all` command shows an ASCII dependency tree:

```
═══ Task Dependencies ═══

High-impact tasks (complete to unblock others):
  ⚡ [auth2026] Auth setup → unblocks 3

Blocked tasks:
  ⛔ [login2026] Login page
     ← waiting on: auth2026

────────────────────────────────────────
Dependency Tree:
  ○ [auth2026] Auth setup
    └─ ⛔ [login2026] Login page
    └─ ⛔ [api2026] API integration
```

### Circular Dependency Prevention

CTM validates dependencies to prevent cycles:

```
$ ctm block auth2026 --by login2026
✗ Would create circular dependency: login2026 -> auth2026 -> login2026
```

### Progress Auto-Tracking

CTM infers task progress from multiple signals beyond manual percentage:

```bash
# View progress breakdown for a task
ctm progress auth2026

# Set key files to track for file-based progress
ctm progress auth2026 --files src/auth.ts src/login.ts tests/auth.test.ts
```

**Progress Signals:**

| Signal | Weight | Description |
|--------|--------|-------------|
| Manual | 3.0 | Explicit `progress_pct` you set |
| Files | 2.0 | Key files touched in last 7 days |
| Commits | 1.0 | Git commits mentioning task (capped 50%) |

**Example Output:**
```
═══ Progress: [auth2026] Auth setup ═══

📊 Manual Progress: 45%

📁 File Activity: 75% (3/4 files touched)

📝 Git Commits: 30% (3 commits mentioning task)

────────────────────────────────────────
🎯 Inferred Progress: 51% (vs 45% manual)
```

**Briefing Integration:**

Briefings show both manual and inferred progress:

```
**Priority Queue**
1. ○ [auth2026] Auth setup (45%→51%)
      └─ Implementing login flow
```

The arrow notation `45%→51%` indicates manual vs inferred progress when they differ.

### Cross-Session Continuity

CTM captures session snapshots to provide rich context when resuming work:

```bash
# Manual snapshot commands
ctm snapshot show auth2026          # View latest snapshot
ctm snapshot capture auth2026       # Capture current state
ctm snapshot list                   # List recent snapshots

# Capture with context
ctm snapshot capture auth2026 \
  --summary "Implementing JWT refresh" \
  --next "Add Redis token storage" \
  -q "Use Redis or Postgres?"
```

**Automatic Capture:**

Session snapshots are automatically captured by the `ctm-session-end.sh` hook:
- Last modified file (from git)
- Current action type (editing, testing, debugging, etc.)
- Recent decisions from agent context
- Uncommitted files count
- Git last commit message

**Enhanced Resume Point:**

Briefings show snapshot data in the Resume Point section:

```
**Resume Point**
Last session (2h ago): Auth Implementation
├─ Progress: 65% (manual) / 49% (inferred)
├─ Current: Implementing JWT refresh
├─ Last: editing src/auth/jwt.ts
├─ Open questions:
│   ? Use Redis or Postgres for tokens?
├─ Uncommitted: 3 file(s)
└─ Next: Add Redis token storage
```

**Snapshot Storage:**

Snapshots are stored in `~/.claude/ctm/snapshots/` with:
- Max 5 snapshots per agent (rolling)
- JSON format for easy inspection
- Automatic cleanup of old snapshots

### Task Templates

Spawn pre-configured tasks with phases, steps, and dependencies:

```bash
# List available templates
ctm templates

# Show template details
ctm templates show hubspot-impl

# Spawn from template
ctm spawn "Client X Implementation" --template hubspot-impl

# Create template from existing agent
ctm templates create my-template --from agent123
```

**Default Templates:**

| Template | Phases | Description |
|----------|--------|-------------|
| `hubspot-impl` | 6 | HubSpot implementation (discovery → go-live) |
| `integration` | 4 | System integration project |
| `feature` | 4 | Standard feature development |
| `migration` | 5 | Data migration project |

**Template Structure (YAML):**

```yaml
name: My Project Template
description: Description of this template

defaults:
  priority:
    value: 0.7
    urgency: 0.6

tags:
  - category
  - type

phases:
  - id: design
    title: Design Phase
    steps:
      - Requirements
      - Architecture
    progress_weight: 25

  - id: build
    title: Build Phase
    steps:
      - Implementation
      - Testing
    progress_weight: 50
    blocked_by: [design]

  - id: deploy
    title: Deployment
    progress_weight: 25
    blocked_by: [build]
```

**Template Effects on Agent:**
- Sets priority/urgency from defaults
- Stores phase structure in `context.phases`
- Sets first phase step as `current_step`
- Applies tags to agent context

**Module:** `~/.claude/ctm/lib/templates.py` (template loading and application)
**Module:** `~/.claude/ctm/lib/session_snapshot.py` (snapshot capture/restore)
**Module:** `~/.claude/ctm/lib/progress.py` (progress inference engine)
**Module:** `~/.claude/ctm/lib/dependencies.py` (dependency graph operations)
**Module:** `~/.claude/ctm/lib/briefing.py` (deadline + dependency + progress + snapshot sections)
**Module:** `~/.claude/ctm/lib/ctm.py` (all commands including templates)

---

## Version 3.1: Agent Messaging & State Versioning (2026-01)

### Agent-to-Agent Messaging

Enables real-time communication between agents via filesystem-based message queue.

```bash
# Send a message
ctm send <agent-id> "What's the API status?"

# Send and wait for reply
ctm send <agent-id> "Check this file" --wait --timeout 30

# Receive messages
ctm receive
ctm receive --from <agent-id>

# Reply to a message
ctm reply <message-id> "Here's the answer"
```

**Message Lifecycle:**
- Messages have TTL (default 5 minutes)
- Status: pending → delivered → read → replied
- Expired messages archived automatically

**Module:** `~/.claude/ctm/lib/messaging.py`

### State Versioning

Optimistic concurrency control prevents race conditions:

```python
from versioning import VersionedStore

store = VersionedStore("~/.claude/ctm/index.json")
state = store.read()  # Gets version + data

# Update with version check
store.write(new_data, expected_version=state.version)

# Atomic update with retry
store.update(lambda data: {**data, "count": data["count"] + 1})
```

**Migration:**
```bash
python3 ~/.claude/ctm/lib/versioning.py migrate ~/.claude/ctm/index.json
python3 ~/.claude/ctm/lib/versioning.py migrate-dir ~/.claude/ctm/agents/
```

**Module:** `~/.claude/ctm/lib/versioning.py`

### Workspace Bootstrap Files

Standard files injected at session start:

| File | Purpose | Max Size |
|------|---------|----------|
| IDENTITY.md | Project identity | 5K chars |
| CONTEXT.md | Current state | 10K chars |
| DECISIONS.md | Architecture decisions | 15K chars |
| CONVENTIONS.md | Coding standards | 5K chars |
| HEARTBEAT.md | Status/priorities | 3K chars |

**Config:** `~/.claude/config/bootstrap.json`

---

## Version 3.2: Reliability & Multi-Session (2026-01)

### Hook Idempotency

Prevents duplicate hook execution using time-based keys with TTL-based cache.

**Problem:** Hooks may execute multiple times on retry, causing duplicate operations.

**Solution:** Track hook executions with idempotency keys and skip duplicates.

```bash
# In hook scripts
source ~/.claude/hooks/lib/idempotency.sh

if ! check_idempotency "my-hook" "$CONTEXT"; then
    exit 0  # Skip - already executed
fi

# ... hook logic here ...
```

**CLI:**
```bash
python3 ~/.claude/lib/idempotency.py stats    # Show cache stats
python3 ~/.claude/lib/idempotency.py clear    # Clear cache
```

**Config:**
- TTL: 300 seconds (5 minutes)
- Max entries: 1000 keys

**Module:** `~/.claude/lib/idempotency.py`

### Session Presence Tracking

Tracks active Claude sessions on the same machine for conflict detection and multi-session awareness.

**Problem:** Multiple Claude sessions may conflict without awareness of each other.

**Solution:** Register sessions on start, heartbeat periodically, unregister on end.

**CLI:**
```bash
python3 ~/.claude/lib/presence.py list        # List active sessions
python3 ~/.claude/lib/presence.py check /path # Check sessions in project
```

**API:**
```python
from presence import get_tracker

tracker = get_tracker()
tracker.register("session-id", "/project/path", "opus")
tracker.heartbeat()

# Check for conflicts
other_sessions = tracker.get_sessions_in_project("/project/path")
if other_sessions:
    print(f"Warning: {len(other_sessions)} other session(s) in this project")

tracker.unregister()
```

**Config:**
- Heartbeat interval: 30 seconds
- Stale threshold: 90 seconds

**Module:** `~/.claude/lib/presence.py`

---

## Feature Maturity

| Status | Features |
|--------|----------|
| **Production** | Priority scoring, session hooks, briefing generation, checkpoints, deadlines, dependencies, task templates, working memory (L1/L2), progress inference, compression, complexity scoring |
| **Beta** | Agent messaging v3.1, session snapshots v3.0, state versioning |
| **Alpha** | Semantic triggers (embedding integration incomplete), shared memory v2.1 (multi-agent pools unused) |
| **Not Implemented** | Knowledge graph (directory exists, empty), session presence tracking (referenced in code, not built) |

> **For productization:** Focus on Production + Beta features. Alpha/unimplemented features are documented for completeness but should not be relied upon.

---

*Updated: 2026-02-14 | Version: 3.3.0*
