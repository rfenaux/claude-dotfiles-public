# PRD: memory-management-expert

## Overview

**Agent Name:** `memory-management-expert`
**Purpose:** Technical expert for Claude Code memory systems (CTM, project memory, sessions)
**Model:** Sonnet (system understanding + guidance)

## Problem Statement

Users need guidance on managing persistent context across Claude Code sessions:
- CTM (Cognitive Task Management) for task contexts
- Project memory (.claude/context/) for decisions and learnings
- Session management and context preservation
- Cross-session continuity strategies

## Key Capabilities

### 1. CTM Management
- Initialize and configure CTM system
- Create, switch, pause, complete task agents
- Manage checkpoints and state
- Extract decisions and learnings from tasks

### 2. Project Memory
- Set up .claude/context/ structure
- Manage DECISIONS.md with A/T/P/S taxonomy
- Maintain SESSIONS.md for session summaries
- Track CHANGELOG.md for project evolution
- Manage STAKEHOLDERS.md

### 3. Memory Initialization
- Bootstrap memory structure for new projects
- Copy templates from ~/.claude/templates/context-structure/
- Configure memory file formats
- Set up supersession patterns

### 4. Context Preservation Advisory
- When to create checkpoints
- Decision recording triggers
- Session summary best practices
- Cross-project memory patterns

## Tools Required

- Read (access memory files)
- Write (create memory structures)
- Edit (update memory files)
- Glob (find memory files)
- Bash (CTM commands)

## Memory Structure

```
project/.claude/context/
├── DECISIONS.md      # Architecture decisions (A/T/P/S)
├── SESSIONS.md       # Session summaries
├── CHANGELOG.md      # Project evolution
└── STAKEHOLDERS.md   # Key people

~/.claude/ctm/
├── agents/           # Task context files
├── index.json        # Agent index
├── scheduler.json    # Priority queue
└── working-memory.json
```

## Decision Taxonomy (A/T/P/S)

- **A (Architecture)**: System design, integration patterns
- **T (Technical)**: Implementation choices, libraries
- **P (Process)**: Workflow, methodology decisions
- **S (Scope)**: Feature boundaries, MVP definitions

## CTM Commands

```bash
ctm status           # Show current state
ctm brief            # Session briefing
ctm spawn "task"     # Create new task
ctm switch           # Switch to task
ctm complete         # Mark task done
ctm checkpoint       # Save state
ctm context add      # Add context
```

## Trigger Patterns

- "help me set up project memory"
- "initialize CTM for this project"
- "record this decision"
- "create a session summary"
- "memory management best practices"

## Integration Points

- Works with `memory-init` skill
- Coordinates with `ctm` skill
- Uses `decision-tracker` skill
- Integrates with RAG for searchable context

## Success Metrics

- Memory structure initialized
- Decisions properly categorized
- Sessions summarized
- CTM tasks tracked
