#!/bin/bash
# Git Auto-Commit Hook for CTM
# Called after CTM checkpoint to commit changes to git
#
# Integration: CTM checkpoint → git auto-commit
# Commits staged and unstaged changes with CTM context

set -e

LOG_FILE="$HOME/.claude/ctm/logs/git-integration.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [git-auto-commit] $1" >> "$LOG_FILE"
}

# Get current directory (project root)
PROJECT_DIR="${1:-$(pwd)}"

# Skip if not a git repo
if [ ! -d "$PROJECT_DIR/.git" ]; then
    log "Not a git repo: $PROJECT_DIR"
    exit 0
fi

cd "$PROJECT_DIR"

# Check if there are changes to commit
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    log "No changes to commit in $PROJECT_DIR"
    exit 0
fi

# Get CTM context for commit message
CTM_CONTEXT=""
if [ -f "$HOME/.claude/ctm/scheduler.json" ]; then
    ACTIVE_AGENT=$(python3 -c "
import json
with open('$HOME/.claude/ctm/scheduler.json') as f:
    data = json.load(f)
print(data.get('active_agent', ''))
" 2>/dev/null || echo "")

    if [ -n "$ACTIVE_AGENT" ]; then
        CTM_CONTEXT="[CTM: $ACTIVE_AGENT]"
    fi
fi

# Stage all changes
git add -A 2>/dev/null || true

# Count changes
CHANGES=$(git diff --cached --stat | tail -1 || echo "changes")

# Create commit with CTM context
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-checkpoint $CTM_CONTEXT

$CHANGES

Triggered by: CTM pre-compact hook
Timestamp: $TIMESTAMP

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

if git commit -m "$COMMIT_MSG" 2>/dev/null; then
    COMMIT_HASH=$(git rev-parse --short HEAD)
    log "Committed $COMMIT_HASH in $PROJECT_DIR"
    echo "[Git] Auto-committed: $COMMIT_HASH"
else
    log "Commit failed or nothing to commit in $PROJECT_DIR"
fi
