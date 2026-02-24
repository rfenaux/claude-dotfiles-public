---
name: init-project
description: Initialize a new project with RAG, memory system, CTM task, and git hooks. One command to set up the full Claude Code infrastructure for a project.
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

One-command setup for new dev projects. Creates RAG index, memory system, CTM task, and git integration.

> **For client engagements**, use `/client-onboard` instead — it adds CLIENT_BRIEF, brand kit, stakeholders, and engagement-specific structure.

## Triggers

Invoke when user says:
- "init project", "/init-project", "initialize project"
- "set up this project", "onboard this project"
- "enable RAG", "enable memory" (partial setup)

## Prerequisites

- Ollama must be running for RAG (`mxbai-embed-large` model)

## Default Project Paths

Projects are created in standardized locations based on type:

| Type | Base Path | When |
|------|-----------|------|
| **Pro (Huble)** | `~/Documents/Projects - Pro/Huble/{project-slug}/` | Client work, Huble engagements |
| **Private** | `~/Documents/Projects - Private/{project-slug}/` | Personal projects |
| **Current directory** | `$(pwd)` | User is already in a project directory |

**Detection logic:**
1. If user specifies `--pro` or `--huble` → Pro path
2. If user specifies `--private` → Private path
3. If user is already in a project directory (has `.git/` or files) → use current directory
4. Otherwise → **ask**: "Is this a Huble/pro project or private?"

**Slug generation:** Lowercase, spaces→hyphens, strip special chars (e.g., "Acme Corp" → `acme-corp`)

## Workflow

### Phase 1: Assessment

First, determine project location and check what exists:

```bash
# Determine path based on type
if [ "$TYPE" = "pro" ]; then
    PROJECT_PATH="$HOME/Documents/Projects - Pro/Huble/$PROJECT_SLUG"
elif [ "$TYPE" = "private" ]; then
    PROJECT_PATH="$HOME/Documents/Projects - Private/$PROJECT_SLUG"
else
    PROJECT_PATH=$(pwd)
fi

mkdir -p "$PROJECT_PATH"
cd "$PROJECT_PATH"

PROJECT_NAME=$(basename "$PROJECT_PATH")

[ -d ".rag" ] && echo "RAG: Already initialized" || echo "RAG: Not set up"
[ -d ".claude/context" ] && echo "Memory: Already initialized" || echo "Memory: Not set up"
[ -d ".claude/git-changelog" ] && echo "Git hooks: Installed" || echo "Git hooks: Not installed"
git rev-parse --git-dir > /dev/null 2>&1 && echo "Git: Yes" || echo "Git: No"
[ -f "$HOME/.claude/projects/$(echo $PROJECT_PATH | tr '/' '-')/memory/MEMORY.md" ] && echo "Per-project MEMORY.md: Exists" || echo "Per-project MEMORY.md: Not set up"
pgrep -x ollama > /dev/null 2>&1 && echo "Ollama: Running" || echo "Ollama: Not running"
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
mcp__rag-server__rag_index(path=".claude/context/", project_path="...")  # if exists
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

2. **Copy templates from `~/.claude/templates/context-structure/`:**

Copy these files (DO NOT overwrite existing ones):
- `DECISIONS.md` — Architecture decisions log (A/T/P/S taxonomy)
- `SESSIONS.md` — Session summaries
- `CHANGELOG.md` — Project evolution tracking
- `STAKEHOLDERS.md` — Key people (optional, ask user)

For each file, check if it already exists before copying:
```bash
for file in DECISIONS.md SESSIONS.md CHANGELOG.md; do
    if [ ! -f ".claude/context/$file" ]; then
        cp ~/.claude/templates/context-structure/$file .claude/context/$file
        echo "Created: .claude/context/$file"
    else
        echo "Skipped (exists): .claude/context/$file"
    fi
done
```

3. **Customize templates:**

Replace `{PROJECT_NAME}` and `{DATE}` placeholders in the copied files with actual values.

4. **Index to RAG if enabled:**
```
# Only if .rag/ directory exists
mcp__rag-server__rag_index(path=".claude/context/", project_path="...")
```

### Phase 4: Per-Project MEMORY.md

Create the per-project memory file that gets auto-injected into system prompt:

1. **Determine the project memory path:**
```bash
# Convert project path to Claude's project memory format
PROJECT_MEMORY_DIR="$HOME/.claude/projects/$(echo $PROJECT_PATH | sed 's|^/||' | tr '/' '-')/memory"
mkdir -p "$PROJECT_MEMORY_DIR"
```

2. **Create MEMORY.md if not exists:**
```markdown
# Project Memory: {PROJECT_NAME}

> Auto-injected into system prompt. Keep under 200 lines.

## Project Overview

- **Path**: {PROJECT_PATH}
- **Initialized**: {DATE}
- **Type**: {dev project / library / service / etc.}

## Key Patterns

_Document project-specific patterns, conventions, and gotchas here._

## Active Decisions

_Summary of current architecture decisions. Full details in `.claude/context/DECISIONS.md`._

---

*Last updated: {DATE}*
```

3. **Trigger memory sync:**
The `enrich-project-memory.sh` hook will auto-append CTM context and lessons on next session start.

### Phase 5: CTM Task

Create an initial CTM task for the project:

```bash
# Create and switch to a task for the project
ctm spawn "{PROJECT_NAME}: Initial Setup" --switch
```

This ensures the project is tracked in the cognitive task management system.

### Phase 6: Git Integration

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
for pattern in ".claude/git-changelog/" ".rag/" ".claude/context/" "conversation-history/"; do
    grep -q "$pattern" .gitignore 2>/dev/null || echo "$pattern" >> .gitignore
done
```

### Phase 7: Project CLAUDE.md

Create or update the project's `.claude/CLAUDE.md` with memory system instructions:

```markdown
## Project Memory

This project uses persistent context files in `.claude/context/`:

### Before Proposing Solutions
1. Check `DECISIONS.md` for existing architecture decisions
2. Search RAG if `.rag/` exists: `rag_search "[topic]"`

### During Conversations
- When decisions are made, offer to record in DECISIONS.md
- Reference past sessions from SESSIONS.md when relevant

### End of Sessions
- Summarize key outcomes to SESSIONS.md if significant
- Update CHANGELOG.md for major changes

### Context Discovery Rule
Before reporting status or blockers:
1. Check conversation files for recent resolutions
2. Compare dates — trust newer sources over DECISIONS.md
3. Use `/decision-sync` when in doubt
```

**Important:** If `.claude/CLAUDE.md` already exists, APPEND the memory section — do not overwrite.

### Phase 8: Discovery (Optional)

Ask user if they want to run discovery:

> "Would you like to run a quick discovery questionnaire to capture project context?"

If yes, invoke `project-discovery` skill with lightweight mode.

### Phase 9: Summary

Output a summary of what was set up:

```
═══ Project Initialized ═══

Project: {PROJECT_NAME}
Path:    {PROJECT_PATH}

✓ RAG System
  • Indexed: {N} files
  • Location: .rag/

✓ Memory System
  • DECISIONS.md created
  • SESSIONS.md created
  • CHANGELOG.md created
  • STAKEHOLDERS.md created (if applicable)

✓ Per-Project Memory
  • MEMORY.md at {MEMORY_PATH}
  • Auto-injected on session start
  • Enriched by CTM + lessons

✓ CTM Task
  • "{PROJECT_NAME}: Initial Setup" (active)

✓ Git Integration
  • Post-commit hook installed
  • Changelog directory created
  • .gitignore updated

Next steps:
1. Run `rag search "test query"` to verify RAG
2. Record your first decision with `/decision-tracker`
3. Review STAKEHOLDERS.md and add key people
4. Run `ctm brief` to see project status
```

## Quick Mode

If user says "init project --quick" or "quick init":
- Skip discovery
- Skip confirmations
- Use all defaults
- Create all components silently
- Still output the summary

## Partial Setup

Support partial commands:
- "enable RAG" → Only Phase 2
- "enable memory" → Only Phases 3-4
- "enable git hooks" → Only Phase 6
- "enable CTM" → Only Phase 5

## Error Handling

| Scenario | Action |
|----------|--------|
| Ollama not running | Warn but continue with memory system |
| Not a git repo | Skip git integration, inform user |
| Files already exist | Skip with message, don't overwrite |
| Templates missing | Create files inline with defaults |
| CTM unavailable | Skip task creation, inform user |
| Memory path unresolvable | Use fallback path, warn user |

## Integration

After setup, remind user:
- **CTM** tracks tasks for this project (`ctm brief`)
- **RAG** indexes new files automatically via hooks
- **Decisions** recorded in DECISIONS.md with auto-capture
- **Memory enrichment** runs on session start (CTM + lessons)
- **Observations** auto-captured during sessions
- Use `/decision-sync` to reconcile documentation drift

## MCP Tools Used

- `mcp__rag-server__rag_init` — Initialize RAG for project (creates `.rag/`)
- `mcp__rag-server__rag_index` — Index files/folders into vector database
- `mcp__rag-server__rag_status` — Verify RAG health and indexed document count

## Related Skills

- `/client-onboard` — Full client engagement setup (superset for consulting projects)
- `/rag-batch-index` — Full batch indexing with discovery and audit
- `/memory-init` — Memory system setup only (subset of this skill)
- `/project-discovery` — Requirements gathering questionnaire
- `/decision-tracker` — Ongoing decision management
- `/decision-sync` — Reconcile decisions between files
