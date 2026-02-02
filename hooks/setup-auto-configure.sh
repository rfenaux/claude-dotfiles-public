#!/bin/bash
# setup-auto-configure.sh - Auto-configure projects on claude --init/--maintenance
# Part of Claude Code 2.1.x Feature Adoption (PRD-claude-code-2.1-feature-adoption)
#
# Triggered by Setup hook event (--init, --init-only, --maintenance flags)
# Auto-initializes RAG, creates .claude/context/ structure, reports setup status

set -e

HOOK_INPUT=$(cat)
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')
PROJECT_DIR="${CWD:-$(pwd)}"

# Don't run in home directory (global config, not project)
if [ "$PROJECT_DIR" = "$HOME" ] || [ "$PROJECT_DIR" = "/Users/<username>" ]; then
    echo "[SETUP] Skipping: Running in home directory (global config)"
    exit 0
fi

# Track what we set up
SETUP_ACTIONS=()

# 1. Check/create .claude/context/ structure
CONTEXT_DIR="$PROJECT_DIR/.claude/context"
if [ ! -d "$CONTEXT_DIR" ]; then
    mkdir -p "$CONTEXT_DIR"

    # Create DECISIONS.md template
    if [ ! -f "$CONTEXT_DIR/DECISIONS.md" ]; then
        cat > "$CONTEXT_DIR/DECISIONS.md" << 'EOF'
# Architecture Decisions

## Active Decisions

<!-- Format: A-XXX for Architecture, T-XXX for Technical, P-XXX for Process, S-XXX for Strategic -->

*No decisions recorded yet.*

## Superseded Decisions

*None.*
EOF
        SETUP_ACTIONS+=("Created DECISIONS.md")
    fi

    # Create SESSIONS.md template
    if [ ! -f "$CONTEXT_DIR/SESSIONS.md" ]; then
        cat > "$CONTEXT_DIR/SESSIONS.md" << 'EOF'
# Session History

## Recent Sessions

*No sessions recorded yet.*
EOF
        SETUP_ACTIONS+=("Created SESSIONS.md")
    fi

    SETUP_ACTIONS+=("Created .claude/context/ directory")
fi

# 2. Check/initialize RAG
RAG_DIR="$PROJECT_DIR/.rag"
if [ ! -d "$RAG_DIR" ]; then
    # Check if Ollama is available for RAG
    if command -v ollama &> /dev/null; then
        # Note: We can't directly initialize RAG from a hook
        # Instead, we'll add a reminder
        SETUP_ACTIONS+=("RAG not initialized - run 'rag init' to enable semantic search")
    fi
else
    SETUP_ACTIONS+=("RAG already initialized")
fi

# 3. Check/create .gitignore entries for Claude artifacts
GITIGNORE="$PROJECT_DIR/.gitignore"
if [ -f "$GITIGNORE" ]; then
    # Check if Claude patterns are already in gitignore
    if ! grep -q "\.rag/" "$GITIGNORE" 2>/dev/null; then
        echo "" >> "$GITIGNORE"
        echo "# Claude Code artifacts" >> "$GITIGNORE"
        echo ".rag/" >> "$GITIGNORE"
        echo ".claude/context/SESSIONS.md" >> "$GITIGNORE"
        SETUP_ACTIONS+=("Added Claude patterns to .gitignore")
    fi
fi

# 4. Report setup status
if [ ${#SETUP_ACTIONS[@]} -eq 0 ]; then
    echo "[SETUP] Project already configured"
else
    echo "[SETUP] Auto-configuration complete:"
    for action in "${SETUP_ACTIONS[@]}"; do
        echo "  - $action"
    done
fi

exit 0
