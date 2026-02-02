# Project Memory System Guide

> Persistent context across conversations via structured markdown files

## Overview

The Project Memory system maintains context between Claude sessions through structured files in each project's `.claude/context/` directory.

## Context Directory Structure

```
project/.claude/context/
├── DECISIONS.md     # Architecture decisions with supersession tracking
├── SESSIONS.md      # Session summaries
├── CHANGELOG.md     # Project evolution
└── STAKEHOLDERS.md  # Key people
```

## Memory Workflow

1. **Before proposing solutions**: Check `DECISIONS.md` for existing decisions
2. **During conversations**: Offer to record significant decisions
3. **End of sessions**: Summarize key outcomes to `SESSIONS.md` if significant

## Decision Auto-Capture

When Claude detects decision language, it MUST offer to record it.

### Trigger Phrases to Watch For

- "we decided", "let's go with", "decision:", "the decision is"
- "we're going to use", "we'll use", "choosing", "we chose"
- "final answer", "that's the plan", "agreed"
- "instead of X, we'll do Y", "switching to"

### Response Format

When detected, respond with:
> "I notice we made a decision: **[decision summary]**. Want me to record this to DECISIONS.md?"

### Decision Record Format

```markdown
### [Decision Title]
- **Decided**: [DATE]
- **Decision**: [What was decided]
- **Context**: [Why this choice]
- **Alternatives**: [What was considered]
```

### Skip Auto-Capture For

- Trivial decisions (file naming, formatting)
- Already-recorded decisions
- Exploratory discussions without commitment

## Supersession Pattern

When decisions are replaced, use explicit supersession in DECISIONS.md:
- New decision in "Active" section with `**Supersedes**: [old decision]`
- Old decision moved to "Superseded" section with strikethrough

RAG automatically detects and deprioritizes superseded content (strikethrough, "superseded by", "[deprecated]").

## Initialization

To set up for a project:
- Say "Initialize memory system"
- Or copy `~/.claude/templates/context-structure/`

## Integration with CTM

When CTM tasks complete, it extracts decisions and learnings to:
- `project/.claude/context/DECISIONS.md` - Architectural decisions
- `project/.claude/context/SESSIONS.md` - Session summaries
- RAG index (if `.rag/` exists) - Searchable context
