---
name: init-project
description: Initialize a new project with RAG, memory system, and git hooks. One command to set up the full Claude Code infrastructure for a project.
trigger: /init-project
context: fork
agent: general-purpose
model: sonnet
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
async:
  mode: never
  require_sync:
    - user confirmation
    - interactive setup
---

# Project Initialization Skill

One-command setup for new projects. Creates RAG index, memory system, and git integration.

## Triggers

Invoke when user says:
- "init project", "/init-project", "initialize project"
- "set up this project", "onboard this project"
- "enable RAG", "enable memory" (partial setup)

## Prerequisites

- Project must be a git repository (recommended)
- Ollama must be running for RAG
- User should be in the project root directory

## Workflow

### Phase 1: Assessment

First, check what already exists:

```bash
# Check current state
[ -d ".rag" ] && echo "RAG: Already initialized" || echo "RAG: Not set up"
[ -d ".claude/context" ] && echo "Memory: Already initialized" || echo "Memory: Not set up"
[ -f ".claude/git-changelog" ] && echo "Git hooks: Installed" || echo "Git hooks: Not installed"
git rev-parse --git-dir > /dev/null 2>&1 && echo "Git: Yes" || echo "Git: No"
```

Present findings to user and ask what to set up.

### Phase 2: RAG Setup

If user wants RAG:

1. **Initialize RAG:**
```
mcp__rag-server__rag_init(project_path="/absolute/path/to/project")
```

2. **Index existing documentation:**
```
# Find and index common doc locations (check existence first)
mcp__rag-server__rag_index(path="docs/", project_path="...")        # if exists
mcp__rag-server__rag_index(path="README.md", project_path="...")    # if exists
mcp__rag-server__rag_index(path="requirements/", project_path="...") # if exists
mcp__rag-server__rag_index(path="specs/", project_path="...")       # if exists
```

3. **Verify:**
```
mcp__rag-server__rag_status(project_path="...")
```

### Phase 3: Memory System Setup

If user wants memory system:

1. **Create directory structure:**
```bash
mkdir -p .claude/context
```

2. **Create DECISIONS.md:**
```markdown
# Architecture Decisions

> Created: {DATE} | Project: {PROJECT_NAME}

## Active Decisions

_No decisions recorded yet._

## Superseded Decisions

_None._

---

## How to Use

Record decisions with:
- **Decision**: What was decided
- **Date**: When
- **Context**: Why this choice
- **Alternatives**: What else was considered
- **Supersedes**: If replacing an old decision

When superseding:
1. Move old decision to "Superseded" section with strikethrough
2. Add new decision to "Active" with `**Supersedes**: [old decision]`
```

3. **Create SESSIONS.md:**
```markdown
# Session Log

> Project: {PROJECT_NAME}

## Recent Sessions

_No sessions recorded yet._

---

## Format

Each session entry:
- **Date**: YYYY-MM-DD
- **Focus**: What was worked on
- **Outcomes**: What was accomplished
- **Next**: What's pending
```

4. **Create STAKEHOLDERS.md:**
```markdown
# Stakeholders

> Project: {PROJECT_NAME}

## Key People

| Name | Role | Contact | Notes |
|------|------|---------|-------|
| _TBD_ | | | |

## Communication Preferences

_Document how stakeholders prefer to communicate._
```

5. **Index to RAG if enabled:**
```
# Only if .rag/ directory exists
mcp__rag-server__rag_index(path=".claude/context/", project_path="...")
```

### Phase 4: Git Integration

If project is a git repo and user wants git integration:

1. **Create changelog directory:**
```bash
mkdir -p .claude/git-changelog
```

2. **Install post-commit hook:**
```bash
# Copy hook if not exists
if [ ! -f ".git/hooks/post-commit" ]; then
    cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-generate changelog and index to RAG
~/.claude/hooks/git-post-commit-rag.sh
EOF
    chmod +x .git/hooks/post-commit
fi
```

3. **Add to .gitignore:**
```bash
# Add Claude artifacts to gitignore if not present
grep -q ".claude/git-changelog" .gitignore 2>/dev/null || echo ".claude/git-changelog/" >> .gitignore
grep -q ".rag/" .gitignore 2>/dev/null || echo ".rag/" >> .gitignore
```

### Phase 5: Discovery (Optional)

Ask user if they want to run discovery:

> "Would you like to run a quick discovery questionnaire to capture project context?"

If yes, invoke `project-discovery` skill with lightweight mode.

### Phase 6: Summary

Output a summary of what was set up:

```
═══ Project Initialized ═══

✓ RAG System
  • Indexed: 15 files
  • Location: .rag/

✓ Memory System
  • DECISIONS.md created
  • SESSIONS.md created
  • STAKEHOLDERS.md created

✓ Git Integration
  • Post-commit hook installed
  • Changelog directory created

Next steps:
1. Run `rag search "test query"` to verify RAG
2. Record your first decision with `decision-tracker`
3. Review STAKEHOLDERS.md and add key people
```

## Quick Mode

If user says "init project --quick" or "quick init":
- Skip discovery
- Skip confirmations
- Use all defaults
- Just set everything up

## Partial Setup

Support partial commands:
- "enable RAG" → Only Phase 2
- "enable memory" → Only Phase 3
- "enable git hooks" → Only Phase 4

## Error Handling

- If Ollama not running: Warn but continue with memory system
- If not a git repo: Skip git integration, inform user
- If files already exist: Skip with message, don't overwrite

## Integration

After setup, remind user:
- CTM will now track tasks for this project
- RAG will index new files automatically (via hooks)
- Decisions should be recorded in DECISIONS.md
- Use `ctm brief` to see project status

## MCP Tools Used

- `mcp__rag-server__rag_init` — Initialize RAG for project (creates `.rag/`)
- `mcp__rag-server__rag_index` — Index files/folders into vector database
- `mcp__rag-server__rag_status` — Verify RAG health and indexed document count

## Related Skills

- `rag-batch-index` — Full batch indexing with discovery and audit
- `memory-init` — Memory system setup only
- `project-discovery` — Requirements gathering questionnaire
