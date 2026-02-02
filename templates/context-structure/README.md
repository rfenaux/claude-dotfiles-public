# Claude's Memory Stack - Project Template

This template enables all three memory systems for a project:
- **Cognitive Continuity** — Task management across sessions
- **RAG** — Semantic search over documents
- **Project Memory** — Decisions, sessions, stakeholders

## Quick Setup

### Option 1: Auto-setup (Recommended)
```bash
~/.claude/ctm/scripts/ctm-migrate /path/to/project --setup
```

### Option 2: Manual Setup
```bash
# Create project memory structure
mkdir -p /path/to/project/.claude/context
cp ~/.claude/templates/context-structure/*.md /path/to/project/.claude/context/

# Initialize RAG (in Claude)
# Say: "rag init"
```

## Directory Structure

```
project/
├── .claude/
│   ├── CLAUDE.md              # Project-specific instructions
│   └── context/
│       ├── DECISIONS.md       # Architecture decisions
│       ├── SESSIONS.md        # Session summaries
│       ├── CHANGELOG.md       # Project evolution
│       └── STAKEHOLDERS.md    # Key people
├── .rag/                      # RAG index (auto-created)
│   └── lancedb/               # Vector database
└── ...
```

## The Three Systems

### 1. Cognitive Continuity (Global)

Bio-inspired task management. Works automatically across all projects.

```bash
ctm status           # Current state
ctm spawn "task"     # New task
ctm complete         # Mark done → extracts to DECISIONS.md
ctm brief            # Session briefing
```

**Auto-triggers:** "Let's work on...", "This is done", "What's the priority?"

### 2. RAG System (Per-Project)

Semantic search over project documents.

```bash
rag init             # Initialize for project
rag index docs/      # Index a folder
rag search "query"   # Search semantically
```

**Auto-use:** If `.rag/` exists, Claude searches before answering questions.

### 3. Project Memory (Per-Project)

Structured context files:

| File | Purpose | Updated When |
|------|---------|--------------|
| `DECISIONS.md` | Architecture choices | Decisions made |
| `SESSIONS.md` | Session summaries | End of significant sessions |
| `CHANGELOG.md` | Project evolution | Milestones reached |
| `STAKEHOLDERS.md` | Key people | Team changes |

## How They Work Together

```
┌────────────────┐     ┌─────────────────┐     ┌──────────────┐
│    Cognitive   │────▶│  DECISIONS.md   │◀────│     RAG      │
│   Continuity   │     │  SESSIONS.md    │     │   Indexing   │
│  (ctm complete)│     └─────────────────┘     └──────────────┘
└────────────────┘              │                      │
                                ▼                      ▼
                    User can query via         Claude searches
                    "check decisions"          before answering
```

**Flow:**
1. Start task → `ctm spawn`
2. Work on it → decisions recorded via `ctm context add -d`
3. Complete → `ctm complete` extracts to DECISIONS.md
4. DECISIONS.md auto-indexed to RAG
5. Future questions → RAG finds relevant decisions

## Enabling for Existing Projects

Run the migration check:
```bash
~/.claude/ctm/scripts/ctm-migrate /path/to/project
```

With auto-setup:
```bash
~/.claude/ctm/scripts/ctm-migrate /path/to/project --setup
```

This will:
- Verify Cognitive Continuity is working
- Create `.claude/context/` if needed
- Show RAG status

## Best Practices

1. **Use Cognitive Continuity** for multi-step tasks spanning sessions
2. **Record decisions** when architectural choices are made
3. **Summarize sessions** after significant work
4. **Keep RAG indexed** — reindex after major document changes

## CLAUDE.md Integration

Add to your project's `.claude/CLAUDE.md`:

```markdown
## Project Memory

This project uses Claude's Memory Stack:
- **Cognitive Continuity**: Task context via `ctm` commands
- **RAG**: Semantic search (`.rag/` exists)
- **Project Memory**: Check `.claude/context/` for decisions

Before proposing architecture, check DECISIONS.md.
When significant decisions are made, offer to record them.
```
