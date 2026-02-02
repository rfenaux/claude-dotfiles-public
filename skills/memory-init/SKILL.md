---
name: memory-init
description: Sets up persistent memory structure for projects enabling Claude to maintain context across conversations.
async:
  mode: always
  prefer_background:
    - setup automation
    - one-shot initialization
    - directory creation
---

# Memory System Initializer

Sets up the persistent memory structure for a project, enabling Claude to maintain context across conversations.

## Triggers

Invoke when:
- User says "initialize memory", "set up context system", "enable memory tracking"
- Starting a new project that will have multiple sessions
- User experiences context loss and wants to prevent it
- Project has no `.claude/context/` directory

## What Gets Created

```
project/
├── .claude/
│   ├── context/
│   │   ├── DECISIONS.md       # Architecture decisions log
│   │   ├── SESSIONS.md        # Session summaries
│   │   ├── CHANGELOG.md       # Project evolution
│   │   └── STAKEHOLDERS.md    # Key people (optional)
│   └── CLAUDE.md              # Updated with memory instructions
```

## Workflow

### Step 1: Check Current State

```bash
# Check if structure exists
ls -la .claude/context/ 2>/dev/null || echo "No context structure found"
ls -la .claude/CLAUDE.md 2>/dev/null || echo "No CLAUDE.md found"
```

### Step 2: Create Directory Structure

```bash
mkdir -p .claude/context
```

### Step 3: Copy Templates

Copy from `~/.claude/templates/context-structure/`:
- DECISIONS.md
- SESSIONS.md
- CHANGELOG.md
- STAKEHOLDERS.md (optional, ask user)

### Step 4: Update CLAUDE.md

Add memory system instructions to project's CLAUDE.md:

```markdown
## Project Memory

This project uses persistent context files in `.claude/context/`:

### Before Proposing Solutions
1. Check `DECISIONS.md` for existing architecture decisions
2. Search RAG if `.rag/` exists: `rag_search "[topic]" category:decision`

### During Conversations
- When decisions are made, offer to record in DECISIONS.md
- Reference past sessions from SESSIONS.md when relevant

### End of Sessions
- Summarize key outcomes to SESSIONS.md if significant
- Update CHANGELOG.md for major changes

### File Priority for Context
1. `.claude/context/DECISIONS.md` — Current decisions (check first)
2. `.claude/context/SESSIONS.md` — Recent session summaries
3. RAG search — Full document history
4. `conversation-history/` — Raw transcripts (last resort)
```

### Step 5: Initialize RAG (if not exists)

```bash
# If .rag/ doesn't exist, initialize it
rag init
rag index .claude/context/
```

### Step 6: Confirm Setup

Output summary of what was created and how to use it.

## Post-Setup Instructions for User

```markdown
## Your Memory System is Ready

**To record decisions:**
> "Record decision: We chose PostgreSQL for the database"

**To check past decisions:**
> "What decisions have we made about authentication?"

**To summarize a session:**
> "Summarize this session for the memory system"

**Files created:**
- `.claude/context/DECISIONS.md` — Architecture decisions
- `.claude/context/SESSIONS.md` — Session summaries
- `.claude/context/CHANGELOG.md` — Project evolution

**Tip:** These files are auto-indexed to RAG on every save.
```

## Options

| Option | Description |
|--------|-------------|
| `--minimal` | Only DECISIONS.md and SESSIONS.md |
| `--full` | Include STAKEHOLDERS.md |
| `--migrate` | Import existing decisions from conversation history |

## Migration Mode

If user has existing conversations, offer to extract decisions:

1. Read `conversation-history/*.md` files
2. Search for decision-like patterns:
   - "we decided", "let's go with", "agreed on", "chose"
   - Architecture/technical discussions
3. Present found decisions for user to confirm
4. Add confirmed ones to DECISIONS.md with dates

## Integration with Existing Systems

### RAG Auto-Indexing
Context files are auto-indexed via PostToolUse hook when modified.

### Conversation Saving
PreCompact/SessionEnd hooks already save to `conversation-history/`.

### Decision Tracker Skill
Works with `decision-tracker` skill for ongoing management.

## Validation

After setup, verify:
- [ ] `.claude/context/` directory exists
- [ ] Template files are in place
- [ ] CLAUDE.md includes memory instructions
- [ ] Files are indexed to RAG (if RAG enabled)
