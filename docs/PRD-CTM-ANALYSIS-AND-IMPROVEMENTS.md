# PRD: CTM System Analysis & Improvement Recommendations

> **Version**: 1.1 | **Date**: 2026-01-23 | **Author**: Claude (Analysis)
> **Status**: Draft for Review

---

## 1. Executive Summary

Cognitive Task Management (CTM) is a bio-inspired system enabling Claude Code to maintain context across conversations and manage multiple concurrent tasks. After comprehensive analysis of the implementation (~4,500 lines of Python across 8 modules), your actual setup, and external research on cognitive architectures, this PRD documents the current system and proposes targeted improvements.

**Key Finding**: CTM is architecturally sound and ahead of industry patterns. Most improvements are refinements rather than redesigns.

---

## 2. Your Current Setup (Live Analysis)

### 2.1 Active Configuration

| Component | Status | Details |
|-----------|--------|---------|
| **Skill** | ✅ Active | `~/.claude/skills/ctm/SKILL.md` → `/ctm` trigger |
| **Hooks** | ✅ All 4 installed | SessionStart, PreCompact, SessionEnd, UserPrompt |
| **Working Memory** | ✅ Active | 5/5 agents loaded, 1,729/8,000 tokens (22%) |
| **Config** | Default | No customizations to `config.json` |

### 2.2 Current Working Memory State

```
Hot Agents (as of 2026-01-22):
┌─────────────────────────┬─────────┬────────┬──────────┐
│ Agent                   │ Tokens  │ Access │ Status   │
├─────────────────────────┼─────────┼────────┼──────────┤
│ rescue2026              │ 665     │ 6x     │ paused   │
│ fp2026ph1               │ 358     │ 6x     │ paused   │
│ isms2026                │ 246     │ 6x     │ active   │
│ fp-erp-audit-2026-01-22 │ 238     │ 6x     │ paused   │
│ fp-deploy-2026          │ 222     │ 6x     │ active   │
└─────────────────────────┴─────────┴────────┴──────────┘
Total: 1,729 tokens (22% of 8,000 budget)
Evictions: 0 (healthy)
```

### 2.3 Hooks Integration

| Hook | Script | Function |
|------|--------|----------|
| **SessionStart** | `ctm-session-start.sh` | Loads top 5 agents to WM, shows briefing, adds git context |
| **PreCompact** | `ctm-pre-compact.sh` | Creates checkpoint before context compaction |
| **SessionEnd** | `ctm-session-end.sh` | Final checkpoint, updates SESSIONS.md |
| **UserPrompt** | `ctm-user-prompt.sh` | Detects task-switch triggers in user input |

### 2.4 Current Task Distribution

```
By Status:
  Active (3):  fp-deploy-2026, rescue-qb-ph1, isms2026
  Paused (3):  rescue2026, fp2026ph1, fp-erp-audit-2026-01-22
  Completed (1): cfg2026

By Project:
  Rescue (2):  rescue2026, rescue-qb-ph1
  Forsee (3):  fp-deploy-2026, fp2026ph1, fp-erp-audit
  ISMS (1):    isms2026
  Config (1):  cfg2026
```

---

## 3. Full System Architecture

### 3.1 Core Components

```
~/.claude/ctm/
├── lib/                          # Python implementation
│   ├── ctm.py         (1608 loc) # CLI entry point, 20+ commands
│   ├── agents.py       (573 loc) # Agent CRUD, caching, v0→v1 migration
│   ├── briefing.py     (571 loc) # Session briefings with 10 sections
│   ├── consolidation.py(360 loc) # Memory consolidation to DECISIONS.md
│   ├── integration.py  (343 loc) # Hook installation
│   ├── scheduler.py    (312 loc) # Priority queue, bio-inspired scoring
│   ├── extraction.py   (308 loc) # Decision/learning extraction
│   ├── triggers.py     (264 loc) # Context switch detection
│   ├── memory.py       (258 loc) # Working memory with eviction
│   └── config.py       (188 loc) # Configuration with inheritance
├── agents/                       # Per-task JSON files
├── checkpoints/                  # State snapshots
├── context/                      # Shared context
├── index.json                    # Fast lookups
├── scheduler.json                # Queue state
└── working-memory.json           # Hot agent cache
```

### 3.2 Bio-Inspired Design Principles

| Brain Concept | CTM Implementation |
|---------------|-------------------|
| **Working Memory (4±1 items)** | `max_hot_agents: 5` in memory.py |
| **DLPFC (executive function)** | Scheduler with priority scoring |
| **Memory Consolidation (sleep)** | `consolidation.py` → DECISIONS.md |
| **Attention Switching** | Trigger detection + preemption |
| **Episodic → Semantic** | Extraction patterns for decisions |
| **Decay/Forgetting** | Exponential recency decay (24h halflife) |

### 3.3 Priority Scoring Algorithm

```python
score = Σ(weight × factor)

Factors (current weights):
- urgency:     0.25  # Deadline proximity
- recency:     0.20  # Exponential decay from last_active
- value:       0.20  # Importance/impact
- novelty:     0.15  # Freshness (7-day halflife)
- user_signal: 0.15  # Explicit priority hints [-1, 1]
- error_boost: 0.05  # Failed tasks get bump (+0.3)
```

### 3.4 Agent Schema (v1)

```json
{
  "id": "8-char-uuid",
  "task": {
    "title": "...",
    "goal": "...",
    "acceptance_criteria": [],
    "dependencies": [],
    "blockers": []
  },
  "context": {
    "project": "/path/to/project",
    "key_files": [],
    "decisions": [{"text": "...", "timestamp": "ISO"}],
    "learnings": [{"text": "...", "timestamp": "ISO"}]
  },
  "state": {
    "status": "active|paused|blocked|completed|cancelled",
    "progress_pct": 0-100,
    "current_step": "...",
    "pending_actions": [],
    "last_error": null
  },
  "priority": {
    "level": "critical|high|normal|low|background",
    "urgency": 0-1,
    "value": 0-1,
    "novelty": 0-1,
    "user_signal": -1 to 1,
    "computed_score": 0-1
  },
  "timing": {
    "created_at": "ISO",
    "last_active": "ISO",
    "total_active_seconds": 0,
    "session_count": 0,
    "estimated_remaining": null,
    "deadline": null
  },
  "triggers": ["custom", "patterns"],
  "outputs": {
    "files_created": [],
    "files_modified": [],
    "commits": [],
    "summary": null
  },
  "metadata": {
    "tags": [],
    "parent_agent": null,
    "child_agents": [],
    "version": "1.0.0",
    "sessions": []
  }
}
```

---

## 4. Observations from Your Usage Patterns

### 4.1 What's Working Well

| Pattern | Evidence |
|---------|----------|
| **Multi-project juggling** | 7 agents across 4 projects (Rescue, Forsee, ISMS, Config) |
| **Token efficiency** | Only 22% of working memory budget used |
| **No evictions** | System hasn't hit capacity limits |
| **Consistent access** | All hot agents have 6x access count (healthy) |

### 4.2 Potential Issues Detected

| Issue | Observation | Impact |
|-------|-------------|--------|
| **ISMS deadline not encoded** | Feb 4 go-live but no `deadline` field | Urgency not reflected in score |
| **Rescue at 85% but paused** | Highest priority score (0.85) but not active | Context switch friction |
| **3 Forsee agents** | Possible fragmentation | Could benefit from milestone grouping |
| **rescue2026 richest context** | 665 tokens vs 222 for fp-deploy | Token estimates working correctly |

### 4.3 Usage-Specific Recommendations

1. **Set deadline on isms2026**: `ctm context add --deadline 2026-02-04` (once implemented)
2. **Consider consolidating Forsee agents**: fp-deploy + fp2026ph1 + fp-erp-audit overlap
3. **Mark cfg2026 for archive**: Completed task still in index

---

## 5. Strengths (Keep)

### 5.1 Architecture
- **File-based state**: JSON files, no database dependency - portable, debuggable
- **Global scope**: Single CTM installation works across all projects
- **Caching with mtime**: Reload only when files change - efficient
- **Graceful degradation**: Errors don't crash, return defaults

### 5.2 Bio-Inspired Features
- **Working memory limits**: Enforces cognitive load management
- **Priority decay**: Stale tasks naturally deprioritize
- **Consolidation**: Converts episodic to semantic memory
- **Trigger detection**: Natural language context switching

### 5.3 Integration
- **Hook-based**: Uses Claude Code's native hook system
- **RAG integration**: Completed agents indexed for retrieval
- **CDP support**: Built-in workspace management for delegation
- **Project memory**: Syncs with DECISIONS.md/SESSIONS.md

---

## 6. Identified Gaps

### 6.1 From External Research

| Industry Pattern | CTM Status | Gap |
|------------------|------------|-----|
| **Agent Cognitive Compressor (ACC)** | Partial | No bounded internal state compression |
| **Hierarchical Cognitive Buffers** | Missing | Single-level working memory only |
| **Version Control Memory (GCC)** | Partial | Checkpoints exist, no BRANCH/MERGE |
| **Session Handoff Documents** | Partial | Briefings exist, no structured handoff format |
| **Procedural Memory** | Missing | No stored workflows/playbooks per task |

### 6.2 From Implementation Analysis

| Component | Issue | Impact |
|-----------|-------|--------|
| `briefing.py` | 10 sections generated serially | Slow session start |
| `extraction.py` | Regex-only decision detection | Misses implicit decisions |
| `scheduler.py` | No deadline-aware urgency | Equal urgency for all tasks |
| `memory.py` | Token estimation is rough | Inaccurate eviction decisions |
| `triggers.py` | Pattern list is static | Can't learn new patterns |
| `consolidation.py` | One-way to DECISIONS.md | No conflict detection |

### 6.3 Missing Features

1. **Task Dependencies**: `blockedBy` field exists but not enforced in queue
2. **Milestone Tracking**: No rollup of related agents
3. **Time Tracking**: `total_active_seconds` never updated
4. **Estimated Completion**: `estimated_remaining` always null
5. **Agent Templates**: No way to create agents from patterns
6. **Bulk Operations**: No batch status changes
7. **Search**: No way to search across all agents
8. **Archive**: Completed agents stay in agents/ forever

---

## 7. Improvement Recommendations

### 7.1 HIGH Priority (Quick Wins)

#### 7.1.1 Deadline-Aware Urgency
**Current**: `urgency` is static (0.5 default)
**Proposed**: Calculate from deadline proximity

```python
# In scheduler.py calculate_priority()
if agent.timing.get("deadline"):
    deadline = datetime.fromisoformat(agent.timing["deadline"])
    days_until = (deadline - now).days
    if days_until <= 0:
        urgency = 1.0  # Overdue
    elif days_until <= 3:
        urgency = 0.9  # Critical
    elif days_until <= 7:
        urgency = 0.7  # Soon
    else:
        urgency = 0.5 * (14 / max(14, days_until))
```

#### 7.1.2 Task Dependency Enforcement
**Current**: `blockers` field ignored in queue
**Proposed**: Filter blocked tasks from queue

```python
# In scheduler.py rebuild_queue()
for agent_id in active_ids:
    agent = get_agent(agent_id)
    if agent.task.get("blockers"):
        # Check if any blocker is still active
        blocked = False
        for blocker_id in agent.task["blockers"]:
            blocker = get_agent(blocker_id)
            if blocker and blocker.state["status"] != "completed":
                blocked = True
                break
        if blocked:
            agent.set_status(AgentStatus.BLOCKED)
            continue
    # ... rest of queue logic
```

#### 7.1.3 Active Time Tracking
**Current**: `total_active_seconds` never updated
**Proposed**: Track in scheduler switch

```python
# In scheduler.py set_active()
if old_active:
    old_agent = get_agent(old_active)
    if old_agent:
        # Calculate session duration
        if old_agent.timing.get("session_start"):
            duration = (now - old_agent.timing["session_start"]).total_seconds()
            old_agent.timing["total_active_seconds"] += duration
            old_agent.timing["session_start"] = None
            old_agent.save()

if agent_id:
    agent = get_agent(agent_id)
    if agent:
        agent.timing["session_start"] = now.isoformat()
```

### 7.2 MEDIUM Priority (Architecture Enhancements)

#### 7.2.1 Hierarchical Memory Buffers
**Rationale**: From Cognitive Workspace research - progressive abstraction

```
Working Memory (5 agents, full context)
    ↓ eviction
Warm Cache (20 agents, compressed)
    ↓ aging
Cold Storage (unlimited, summary only)
```

**Implementation**: Add `warm-cache.json` with compressed agent summaries

#### 7.2.2 Structured Handoff Documents
**Rationale**: From Session Handoffs research - portable context

```markdown
# CTM Handoff: 2026-01-23

## Active Context
- Task: [rescue2026] Rescue Implementation
- Progress: 85%
- Current: Migration files ready

## Critical Decisions (Last 48h)
1. SKU-based product lookup (not QB Item ID)
2. QB Class on Deal AND Customer record

## Open Questions
- [ ] HUBSPOT_TOKEN for workflows

## Next Actions (Priority Order)
1. Execute Pipedrive import
2. Enable 33 workflows

## Key Files
- MIGRATION_HANDOFF.md
- BACKLOG_PRIORITIZED.md
```

**Implementation**: `ctm handoff` command generating structured markdown

#### 7.2.3 Agent Templates
**Rationale**: Reduce boilerplate for common task types

```yaml
# ~/.claude/ctm/templates/hubspot-implementation.yaml
title_pattern: "{client} HubSpot {hub} Implementation"
tags: ["hubspot", "implementation"]
priority:
  level: high
  value: 0.8
context:
  key_files:
    - ".claude/context/DECISIONS.md"
    - "04-CLIENT-DELIVERABLES/"
acceptance_criteria:
  - "All objects configured"
  - "Data migration complete"
  - "UAT passed"
```

**Command**: `ctm spawn --template hubspot-implementation --client Rescue --hub Sales`

### 7.3 LOW Priority (Future Enhancements)

#### 7.3.1 LLM-Enhanced Extraction
Replace regex patterns with Claude Haiku for decision detection:
- Better implicit decision capture
- Context-aware categorization
- Confidence scoring

#### 7.3.2 Agent Search
```bash
ctm search "quickbooks"  # Full-text across all agents
ctm search --tag hubspot --status active
```

#### 7.3.3 Archive Management
```bash
ctm archive --older-than 30d  # Move to ~/.claude/ctm/archive/
ctm restore <agent-id>         # Bring back from archive
```

#### 7.3.4 Milestone Rollup
Group related agents under a milestone for aggregate progress:
```bash
ctm milestone create "Q1 Rescue Delivery" --agents rescue2026,rescue-qb-ph1
ctm milestone status "Q1 Rescue Delivery"  # Shows rollup progress
```

---

## 8. CTM Expert Agent Specification

Based on this analysis, the CTM Expert Agent should have:

### 8.1 Core Knowledge
- Complete understanding of all 8 modules
- Bio-inspired design rationale
- Priority algorithm internals
- Schema evolution (v0 → v1)
- Integration points (hooks, RAG, CDP, project memory)

### 8.2 Capabilities
1. **Diagnose** CTM issues (corruption, drift, stale data)
2. **Repair** broken state files
3. **Optimize** priority weights for user patterns
4. **Extend** with new commands/features
5. **Troubleshoot** hook failures
6. **Advise** on best practices

### 8.3 Trigger Patterns
- "CTM not working"
- "task stuck", "agent won't switch"
- "briefing wrong", "priority incorrect"
- "how does CTM...", "explain CTM..."
- "add feature to CTM"

---

## 9. Implementation Roadmap

| Phase | Items | Effort |
|-------|-------|--------|
| **Phase 1** | Deadline urgency, dependency enforcement, time tracking | 2-3 hours |
| **Phase 2** | Handoff documents, agent templates | 4-6 hours |
| **Phase 3** | Hierarchical buffers, search, archive | 8-12 hours |
| **Phase 4** | LLM extraction, milestone rollup | Research needed |

---

## 10. References

### External Research
- [Agent Cognitive Compressor (ACC)](https://arxiv.org/html/2601.11653) - Bio-inspired memory controller
- [Cognitive Workspace](https://arxiv.org/html/2508.13171v1) - Active memory management for LLMs
- [Git Context Controller (GCC)](https://arxiv.org/html/2508.00031v1) - Version control for agent memory
- [Session Handoffs](https://dev.to/dorothyjb/session-handoffs-giving-your-ai-assistant-memory-that-actually-persists-je9) - Structured handoff documents
- [LangChain Context Engineering](https://docs.langchain.com/oss/python/langchain/context-engineering) - Compression patterns

### Internal Documentation
- `~/.claude/CTM_GUIDE.md` - User/developer guide
- `~/.claude/ctm/config.json` - Configuration reference
- `~/.claude/ctm/lib/*.py` - Source code

---

## 11. Appendix: Module Summary

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `ctm.py` | CLI commands | `cmd_*` functions, `main()` |
| `agents.py` | Agent CRUD | `Agent`, `AgentIndex`, `get_agent()` |
| `scheduler.py` | Priority queue | `Scheduler`, `calculate_priority()` |
| `memory.py` | Working memory | `WorkingMemory`, `MemorySlot` |
| `briefing.py` | Session briefings | `BriefingGenerator`, `BriefingSection` |
| `extraction.py` | Decision mining | `DecisionExtractor`, pattern matching |
| `triggers.py` | Context switch | `TriggerDetector`, `TriggerMatch` |
| `consolidation.py` | Memory sync | `Consolidator`, DECISIONS.md writer |
| `config.py` | Configuration | `CTMConfig`, `load_config()` |
