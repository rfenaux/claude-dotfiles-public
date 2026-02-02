---
name: ctm
description: Bio-inspired task management for multi-task context across sessions. Provides session briefings, task switching, checkpoints, and decision extraction.
async:
  mode: never
  require_sync:
    - task management
    - interactive context
    - session control
---

# CTM - Cognitive Task Manager

A bio-inspired task management system that mimics human working memory and executive function. Automatically invoked at session start/end to provide continuity across conversations.

## Trigger

Invoke this skill when:
- User says "ctm", "/ctm", "task manager", "show tasks", "what am I working on"
- At session start (automatic via hook - shows briefing)
- User mentions switching tasks, pausing work, or resuming something
- User asks about priorities or what to work on next
- User wants to track a complex multi-step task
- User asks "what was I doing?" or "continue where I left off"

## Description

CTM manages multiple task contexts (called "agents") with priority-based scheduling. Like the human brain's DLPFC (dorsolateral prefrontal cortex), it maintains a working memory of active tasks, handles interruptions gracefully, and provides resumption cues when switching back to paused work.

### Key Features
- **Working Memory Pool**: Limited capacity (5 agents, 8000 tokens) like human 4±1 item limit
- **Priority Scheduling**: Weighted scoring based on urgency, recency, value, novelty
- **Auto-Checkpointing**: Saves context at PreCompact and SessionEnd
- **Memory Integration**: Syncs with DECISIONS.md, SESSIONS.md, and RAG
- **Session Briefing**: Shows pending tasks at session start

## Commands

```bash
# Status & Info
/ctm                    Show current status
/ctm status             Show current status
/ctm list               List active agents
/ctm list --all         List all agents (including completed)
/ctm show <id>          Show agent details
/ctm queue              Show priority queue
/ctm brief              Generate session briefing
/ctm memory             Show working memory stats

# Agent Lifecycle
/ctm spawn "title"      Create new agent
/ctm switch <id>        Switch to agent (auto-pauses current)
/ctm pause              Pause current agent
/ctm resume <id>        Resume paused agent
/ctm complete           Mark current agent complete
/ctm cancel <id>        Cancel agent
/ctm priority <id> +/-  Adjust priority

# Integration
/ctm consolidate        Sync to DECISIONS.md, SESSIONS.md, RAG
/ctm hooks install      Install auto-invocation hooks
/ctm hooks status       Check hook installation
```

## Integration with Project Memory

CTM integrates with the project memory system:

### Files Updated by Consolidation
- **DECISIONS.md**: Extracts decisions from agent context
- **SESSIONS.md**: Generates session summaries
- **RAG Index**: Creates agent context documents for semantic search

### Expected Project Structure
```
project/
├── .claude/
│   └── context/
│       ├── DECISIONS.md    # Architecture decisions
│       ├── SESSIONS.md     # Session summaries
│       ├── CHANGELOG.md    # Project evolution
│       └── STAKEHOLDERS.md # Key people
└── .rag/                   # If RAG is initialized
```

## Auto-Invocation

CTM hooks are installed in `~/.claude/settings.json`:

| Hook | Action |
|------|--------|
| SessionStart | Shows briefing with pending tasks |
| PreCompact | Checkpoints active agent before context loss |
| SessionEnd | Final checkpoint + consolidation |

## Priority Algorithm

Agents are scored using weighted factors (0-1 range):

| Factor | Weight | Description |
|--------|--------|-------------|
| Urgency | 25% | Time-sensitivity |
| Recency | 20% | Decays with 24h half-life |
| Value | 20% | Importance/impact |
| Novelty | 15% | Freshness (7-day half-life) |
| User Signal | 15% | Explicit +/- adjustments |
| Error Boost | 5% | Failed tasks get priority |

## Working Memory

Like human working memory, CTM maintains a limited "hot" pool:
- **Capacity**: 5 agents maximum
- **Token Budget**: 8000 tokens
- **Eviction**: Weighted LRU (access frequency × time decay × token cost)
- **Decay**: Fast 1-hour half-life for working memory

## Best Practices

1. **Spawn for non-trivial tasks** that might be interrupted
2. **Use meaningful titles** that remind you of the task
3. **Check `/ctm brief` at session start** for context
4. **Mark tasks complete** to keep queue clean
5. **Run `/ctm consolidate`** to persist important context

## Files

| Path | Purpose |
|------|---------|
| `~/.claude/ctm/config.json` | Configuration |
| `~/.claude/ctm/index.json` | Agent registry |
| `~/.claude/ctm/scheduler.json` | Priority queue |
| `~/.claude/ctm/agents/*.json` | Individual agent state |
| `~/.claude/ctm/working-memory.json` | Hot agent pool |
| `~/.claude/ctm/context/*.md` | Agent context for RAG |
| `~/.claude/ctm/logs/*.log` | Operation logs |
| `~/.claude/hooks/ctm/*.sh` | Hook scripts |

## Example Workflow

```bash
# Start session - see briefing automatically
# Or manually check:
/ctm brief

# Create new task and switch to it
/ctm spawn "Implement user auth" --priority high --switch

# Work on task... add decisions and learnings
# (CTM tracks automatically via hooks)

# Get interrupted - switch to urgent task
/ctm spawn "Fix production bug" --priority critical --switch
# Previous task auto-paused

# Bug fixed
/ctm complete

# Back to original task
/ctm resume <id>  # or: "back to auth"

# End session - auto-consolidates to project memory
```
