#!/bin/bash
# Auto-commit new files in ~/.claude repo
# Called by SessionEnd hook - MUST BE FAST (non-blocking)

# Run entire backup in background to prevent exit hanging
(
CLAUDE_DIR="$HOME/.claude"
LOG_FILE="/tmp/claude-config-backup.log"
LOCK_FILE="/tmp/claude-config-backup.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Acquire lock - prevents concurrent backups from multiple sessions
# Uses flock with timeout to avoid deadlocks
exec 200>"$LOCK_FILE"
if ! flock -n -w 5 200; then
    log "Another backup in progress, skipping"
    exit 0
fi

# Check if .claude has its own git repo
if [ ! -d "$CLAUDE_DIR/.git" ]; then
    exit 0
fi

cd "$CLAUDE_DIR" || exit 0

# Quick check - skip if no obvious changes (fast path)
if ! git status --porcelain 2>/dev/null | grep -qE "^\?\?|^ M"; then
    exit 0
fi

log "Changes detected, starting backup..."

# Pull latest with auto-resolve strategy (ours for state files via .gitattributes)
git pull --no-edit --strategy-option=ours origin main 2>/dev/null || {
    log "Pull had conflicts, using local state"
    git checkout --ours ctm/scheduler.json ctm/working-memory.json 2>/dev/null
    git add ctm/ 2>/dev/null
}

# Add new files in key directories
git add agents/ skills/ hooks/ scripts/ templates/ config/ ctm/ prds/ docs/ 2>/dev/null

# Add modified tracked files
git add -u 2>/dev/null

# Commit if there are staged changes
if git diff --cached --quiet 2>/dev/null; then
    exit 0
fi

git commit -m "Auto-backup $(date '+%Y-%m-%d %H:%M')" --no-verify >/dev/null 2>&1 && {
    log "Committed changes"
}

# Push if we have a remote
if git remote get-url origin &>/dev/null; then
    git push origin main --no-verify >/dev/null 2>&1
    log "Push complete"
fi

# Lock is automatically released when subshell exits
) &

# Exit immediately - backup runs in background
exit 0
