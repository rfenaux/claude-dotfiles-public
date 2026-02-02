#!/bin/bash
# Claude Code Setup Hook
# Triggers: --init, --init-only, --maintenance
# Created: 2026-01-17 | Claude Code 2.1+ feature

set -euo pipefail

MODE="${CLAUDE_SETUP_MODE:-init}"
PROJECT_PATH="${PWD}"

log() { echo "[setup] $1"; }

case "$MODE" in
  init|init-only)
    log "Initializing project at $PROJECT_PATH"

    # Create .claude directory structure
    mkdir -p "$PROJECT_PATH/.claude/context"
    mkdir -p "$PROJECT_PATH/.claude/plans"

    # Initialize memory files if not exist
    if [[ ! -f "$PROJECT_PATH/.claude/context/DECISIONS.md" ]]; then
      cat > "$PROJECT_PATH/.claude/context/DECISIONS.md" << 'EOF'
# Project Decisions

> This file tracks architectural and strategic decisions.
> Format: ### [Title] with Decided date, Decision, Context, Alternatives

---
EOF
      log "Created DECISIONS.md"
    fi

    if [[ ! -f "$PROJECT_PATH/.claude/context/SESSIONS.md" ]]; then
      cat > "$PROJECT_PATH/.claude/context/SESSIONS.md" << 'EOF'
# Session Log

> This file tracks session summaries and continuity.

---
EOF
      log "Created SESSIONS.md"
    fi

    if [[ ! -f "$PROJECT_PATH/.claude/context/CHANGELOG.md" ]]; then
      cat > "$PROJECT_PATH/.claude/context/CHANGELOG.md" << 'EOF'
# Project Changelog

> This file tracks significant changes and milestones.

---
EOF
      log "Created CHANGELOG.md"
    fi

    # Initialize RAG if not already done
    if [[ ! -d "$PROJECT_PATH/.rag" ]]; then
      log "RAG not initialized - will be set up on first index"
    else
      log "RAG database exists"
    fi

    # Initialize CTM workspace if CTM available
    if [[ -f ~/.claude/ctm/scripts/ctm-migrate ]]; then
      log "Setting up CTM workspace..."
      ~/.claude/ctm/scripts/ctm-migrate "$PROJECT_PATH" --setup 2>/dev/null || log "CTM setup skipped"
    fi

    # Git hooks setup if git repo
    if [[ -d "$PROJECT_PATH/.git" ]]; then
      log "Git repository detected"
    fi

    log "Project initialization complete"
    ;;

  maintenance)
    log "Running maintenance checks..."

    # Quick validation
    if [[ -f ~/.claude/scripts/validate-setup.sh ]]; then
      log "Configuration validator:"
      ~/.claude/scripts/validate-setup.sh --quick 2>&1 | grep -E '(PASS|FAIL|Score)' | head -10 || true
    fi

    # CTM repair if needed
    if [[ -f ~/.claude/ctm/scripts/ctm.sh ]]; then
      log "CTM health check..."
      ~/.claude/ctm/scripts/ctm.sh repair 2>/dev/null || log "CTM repair skipped"
    fi

    # RAG status if project has RAG
    if [[ -d "$PROJECT_PATH/.rag" ]]; then
      table_count=$(ls "$PROJECT_PATH/.rag"/*.lance 2>/dev/null | wc -l | tr -d ' ')
      log "RAG status: $table_count tables"
    fi

    # Load check
    if [[ -f ~/.claude/scripts/check-load.sh ]]; then
      load_status=$(~/.claude/scripts/check-load.sh --status-only 2>/dev/null || echo 'unknown')
      log "System load: $load_status"
    fi

    # Dotfiles status
    if [[ -d ~/.dotfiles.git ]]; then
      uncommitted=$(git --git-dir="$HOME/.dotfiles.git" --work-tree="$HOME" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
      log "Dotfiles: $uncommitted uncommitted changes"
    fi

    log "Maintenance complete"
    ;;

  *)
    log "Unknown mode: $MODE"
    exit 1
    ;;
esac
