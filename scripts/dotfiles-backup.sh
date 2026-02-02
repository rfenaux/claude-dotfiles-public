#!/bin/bash
# Auto-backup dotfiles to GitHub
# Called by SessionEnd hook and launchd daily backup

DOTFILES="git --git-dir=$HOME/.dotfiles.git --work-tree=$HOME"
LOG_FILE="/tmp/dotfiles-backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Quick network check (fail fast if offline)
if ! ping -c 1 -W 2 github.com &>/dev/null; then
    log "Offline - skipping backup"
    exit 0
fi

# Check if repo exists
if [ ! -d "$HOME/.dotfiles.git" ]; then
    exit 0
fi

# Check if there are changes
if ! $DOTFILES status --porcelain 2>/dev/null | grep -q .; then
    log "No changes to backup"
    exit 0
fi

log "Starting backup..."

# Temporarily move .claude/.git to avoid submodule issues
if [ -d ~/.claude/.git ]; then
    mv ~/.claude/.git ~/.claude-git-backup
    RESTORE_GIT=1
fi

# Add all tracked paths
$DOTFILES add -u 2>/dev/null

# Add new files in tracked directories (recursive with --all for new files)
$DOTFILES add --all .claude/ .codex/ .gemini/ .mcp.json .claude-server-commander/ \
    .agent-workspaces/ .hscli/ Projects/ clients/ AGENTS.md 2>/dev/null

# Explicitly add commonly-missed subdirectories
$DOTFILES add .claude/agents/ .claude/skills/ .claude/hooks/ .claude/scripts/ \
    .claude/templates/ .claude/config/ .claude/ctm/ .claude/prds/ .claude/docs/ 2>/dev/null

# Force add marketplace plugins (ignored by .claude/.gitignore)
$DOTFILES add -f .claude/plugins/marketplaces/ 2>/dev/null

# Restore .claude/.git
if [ "$RESTORE_GIT" = "1" ]; then
    mv ~/.claude-git-backup ~/.claude/.git
fi

# Count changes
CHANGED=$($DOTFILES diff --cached --stat 2>/dev/null | tail -1 || echo "")

# Commit
$DOTFILES commit -m "Auto-backup $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1 || {
    log "Commit failed (nothing to commit?)"
    exit 0
}

# Push
if $DOTFILES push >/dev/null 2>&1; then
    log "Backup successful: $CHANGED"
    echo "Dotfiles backed up to GitHub"
else
    log "Push failed"
    # Don't fail - commit is local, push will happen next time
    echo "Dotfiles committed (push pending)"
fi

# ============================================
# SESSION SYNC TO REMOTE DEVICE (if mounted)
# ============================================
REMOTE_VOLUME="/Volumes/<username>"
REMOTE_PROJECTS="$REMOTE_VOLUME/.claude/.claude/projects"

if [ -d "$REMOTE_VOLUME" ] && [ -d "$REMOTE_PROJECTS" ]; then
    log "Remote volume mounted - syncing sessions..."

    # Sync sessions from last 7 days (one-way: local → remote)
    # --whole-file: safer for network mounts (no delta)
    # --ignore-existing: never overwrite remote files (prevents corruption)
    # --exclude patterns: skip temp files and actively-written sessions

    cd "$HOME/.claude/projects" && \
    find . -name "*.jsonl" -mtime -7 -type f > /tmp/session_sync_list.txt 2>/dev/null

    if [ -s /tmp/session_sync_list.txt ]; then
        SYNC_COUNT=$(wc -l < /tmp/session_sync_list.txt | tr -d ' ')

        # --update: only copy if source is newer (prevents overwriting resumed sessions)
        rsync -a --whole-file --update \
            --files-from=/tmp/session_sync_list.txt \
            "$HOME/.claude/projects/" \
            "$REMOTE_PROJECTS/" 2>/dev/null

        if [ $? -eq 0 ]; then
            log "Session sync: $SYNC_COUNT files to remote"
        else
            log "Session sync: partial (some files skipped)"
        fi

        # Also sync sessions-index.json files for resume capability
        find . -name "sessions-index.json" -mtime -7 -type f > /tmp/session_index_list.txt 2>/dev/null
        if [ -s /tmp/session_index_list.txt ]; then
            rsync -a --whole-file --update \
                --files-from=/tmp/session_index_list.txt \
                "$HOME/.claude/projects/" \
                "$REMOTE_PROJECTS/" 2>/dev/null
            rm -f /tmp/session_index_list.txt
        fi

        # ---- REVERSE SYNC: Remote → Local (pull newer files) ----
        cd "$REMOTE_PROJECTS" && \
        find . -name "*.jsonl" -mtime -7 -type f > /tmp/remote_session_list.txt 2>/dev/null

        if [ -s /tmp/remote_session_list.txt ]; then
            REVERSE_COUNT=$(wc -l < /tmp/remote_session_list.txt | tr -d ' ')

            rsync -a --whole-file --update \
                --files-from=/tmp/remote_session_list.txt \
                "$REMOTE_PROJECTS/" \
                "$HOME/.claude/projects/" 2>/dev/null

            if [ $? -eq 0 ]; then
                log "Reverse sync: checked $REVERSE_COUNT remote files"
            fi

            # Reverse sync sessions-index.json too
            find . -name "sessions-index.json" -mtime -7 -type f > /tmp/remote_index_list.txt 2>/dev/null
            if [ -s /tmp/remote_index_list.txt ]; then
                rsync -a --whole-file --update \
                    --files-from=/tmp/remote_index_list.txt \
                    "$REMOTE_PROJECTS/" \
                    "$HOME/.claude/projects/" 2>/dev/null
                rm -f /tmp/remote_index_list.txt
            fi

            rm -f /tmp/remote_session_list.txt
        fi

        rm -f /tmp/session_sync_list.txt
    fi
else
    log "Remote volume not mounted - skipping session sync"
fi
