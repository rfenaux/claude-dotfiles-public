#!/bin/bash
# dotfiles-sync.sh - Pull latest config from GitHub on session start
# Called by SessionStart hook to ensure multi-device sync
#
# Features:
# - Auto-stash local changes before pull
# - Auto-resolve merge conflicts for session/history files (keep local)
# - Handle diverged state with rebase
# - Restore local changes after sync
# - Claude CLI fallback for complex issues (optional)

set -e

DOTFILES="git --git-dir=$HOME/.dotfiles.git --work-tree=$HOME"
LOG_FILE="/tmp/dotfiles-sync.log"
CLAUDE_FALLBACK="${DOTFILES_CLAUDE_FALLBACK:-true}"  # Enable by default

# Failover configuration
SNAPSHOT_DIR="$HOME/.dotfiles-snapshot"
SNAPSHOT_COMMIT_FILE="$SNAPSHOT_DIR/.commit"
ISSUE_REPORT_DIR="$HOME/.claude/sync-issues"
VALIDATION_ERRORS=()

# Files that should always keep local version on conflict (session-specific)
SESSION_FILES=(
    ".claude.json"
    ".claude.json.backup"
    ".claude/history.jsonl"
    ".claude/projects/-Users-raphael/sessions-index.json"
    ".claude/settings.local.json"
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Create snapshot of current config before sync
create_snapshot() {
    log "Creating pre-sync snapshot..."

    rm -rf "$SNAPSHOT_DIR"
    mkdir -p "$SNAPSHOT_DIR"

    # Record current commit
    $DOTFILES rev-parse HEAD > "$SNAPSHOT_COMMIT_FILE" 2>/dev/null || echo "unknown" > "$SNAPSHOT_COMMIT_FILE"

    # Copy critical files
    if [ -d "$HOME/.claude/ctm/lib" ]; then
        cp -r "$HOME/.claude/ctm/lib" "$SNAPSHOT_DIR/ctm-lib"
    fi

    [ -f "$HOME/.claude/CLAUDE.md" ] && cp "$HOME/.claude/CLAUDE.md" "$SNAPSHOT_DIR/"
    [ -f "$HOME/.claude/settings.json" ] && cp "$HOME/.claude/settings.json" "$SNAPSHOT_DIR/"
    [ -f "$HOME/.mcp.json" ] && cp "$HOME/.mcp.json" "$SNAPSHOT_DIR/"

    # Copy templates
    if [ -d "$HOME/.claude/ctm/templates" ]; then
        cp -r "$HOME/.claude/ctm/templates" "$SNAPSHOT_DIR/ctm-templates"
    fi

    # Copy hooks (they can break Claude too)
    if [ -d "$HOME/.claude/hooks" ]; then
        cp -r "$HOME/.claude/hooks" "$SNAPSHOT_DIR/hooks"
    fi

    # Copy agents (custom agents)
    if [ -d "$HOME/.claude/agents" ]; then
        cp -r "$HOME/.claude/agents" "$SNAPSHOT_DIR/agents"
    fi

    log "Snapshot created at $SNAPSHOT_DIR"
}

# Clean up snapshot after successful sync
cleanup_snapshot() {
    if [ -d "$SNAPSHOT_DIR" ]; then
        rm -rf "$SNAPSHOT_DIR"
        log "Snapshot cleaned up"
    fi

    # Clean old issue reports (older than 30 days)
    if [ -d "$ISSUE_REPORT_DIR" ]; then
        find "$ISSUE_REPORT_DIR" -name "issue-*.md" -mtime +30 -delete 2>/dev/null || true
    fi
}

# Validate sync - check that critical components work
validate_sync() {
    log "Running post-sync validation..."
    VALIDATION_ERRORS=()

    # 1. Test CTM core Python imports
    if ! python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude/ctm/lib')
from config import load_config, get_ctm_dir
from agents import Agent, get_agent, list_agents
from scheduler import get_scheduler
from briefing import generate_briefing
print('CTM core imports OK')
" 2>/dev/null; then
        VALIDATION_ERRORS+=("CTM core Python imports failed")
    fi

    # 2. Test CTM v3.0 modules
    if ! python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude/ctm/lib')
from dependencies import find_blockers
from progress import infer_progress
from session_snapshot import load_snapshot
from templates import list_templates
print('CTM v3.0 imports OK')
" 2>/dev/null; then
        VALIDATION_ERRORS+=("CTM v3.0 imports failed")
    fi

    # 3. Validate JSON configs
    if [ -f "$HOME/.mcp.json" ]; then
        if ! python3 -c "import json; json.load(open('$HOME/.mcp.json'))" 2>/dev/null; then
            VALIDATION_ERRORS+=("Invalid .mcp.json")
        fi
    fi

    if [ -f "$HOME/.claude/settings.json" ]; then
        if ! python3 -c "import json; json.load(open('$HOME/.claude/settings.json'))" 2>/dev/null; then
            VALIDATION_ERRORS+=("Invalid settings.json")
        fi
    fi

    # 4. Validate YAML templates
    for yaml_file in "$HOME/.claude/ctm/templates/"*.yaml; do
        if [ -f "$yaml_file" ]; then
            if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
                VALIDATION_ERRORS+=("Invalid YAML: $(basename "$yaml_file")")
            fi
        fi
    done

    # 5. Check critical files exist
    CRITICAL_FILES=(
        "$HOME/.claude/CLAUDE.md"
        "$HOME/.claude/ctm/lib/ctm.py"
        "$HOME/.claude/ctm/lib/config.py"
        "$HOME/.claude/ctm/lib/agents.py"
        "$HOME/.claude/ctm/lib/briefing.py"
    )
    for file in "${CRITICAL_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            VALIDATION_ERRORS+=("Missing critical file: $(basename "$file")")
        fi
    done

    # 6. Validate shell scripts (hooks) have no syntax errors
    for hook_file in "$HOME/.claude/hooks/"*/*.sh "$HOME/.claude/scripts/"*.sh; do
        if [ -f "$hook_file" ]; then
            if ! bash -n "$hook_file" 2>/dev/null; then
                VALIDATION_ERRORS+=("Invalid shell script: $(basename "$hook_file")")
            fi
        fi
    done

    # Return result
    if [ ${#VALIDATION_ERRORS[@]} -eq 0 ]; then
        log "Validation passed"
        return 0
    else
        log "Validation failed: ${VALIDATION_ERRORS[*]}"
        return 1
    fi
}

# Rollback to snapshot on validation failure
rollback_sync() {
    log "Rolling back to snapshot..."

    if [ ! -d "$SNAPSHOT_DIR" ]; then
        log "ERROR: No snapshot found - cannot rollback"
        return 1
    fi

    # Get original commit
    if [ -f "$SNAPSHOT_COMMIT_FILE" ]; then
        ORIGINAL_COMMIT=$(cat "$SNAPSHOT_COMMIT_FILE")
        if [ "$ORIGINAL_COMMIT" != "unknown" ]; then
            # Hard reset to original commit
            $DOTFILES reset --hard "$ORIGINAL_COMMIT" 2>/dev/null || {
                log "Git reset failed - restoring files manually"
            }
            log "Reset to commit: $ORIGINAL_COMMIT"
        fi
    fi

    # Restore critical files from snapshot (belt and suspenders)
    if [ -d "$SNAPSHOT_DIR/ctm-lib" ]; then
        rm -rf "$HOME/.claude/ctm/lib"
        cp -r "$SNAPSHOT_DIR/ctm-lib" "$HOME/.claude/ctm/lib"
        log "Restored CTM lib from snapshot"
    fi

    if [ -d "$SNAPSHOT_DIR/ctm-templates" ]; then
        rm -rf "$HOME/.claude/ctm/templates"
        cp -r "$SNAPSHOT_DIR/ctm-templates" "$HOME/.claude/ctm/templates"
        log "Restored CTM templates from snapshot"
    fi

    [ -f "$SNAPSHOT_DIR/CLAUDE.md" ] && cp "$SNAPSHOT_DIR/CLAUDE.md" "$HOME/.claude/"
    [ -f "$SNAPSHOT_DIR/settings.json" ] && cp "$SNAPSHOT_DIR/settings.json" "$HOME/.claude/"
    [ -f "$SNAPSHOT_DIR/.mcp.json" ] && cp "$SNAPSHOT_DIR/.mcp.json" "$HOME/"

    # Restore hooks
    if [ -d "$SNAPSHOT_DIR/hooks" ]; then
        rm -rf "$HOME/.claude/hooks"
        cp -r "$SNAPSHOT_DIR/hooks" "$HOME/.claude/hooks"
        log "Restored hooks from snapshot"
    fi

    # Restore agents
    if [ -d "$SNAPSHOT_DIR/agents" ]; then
        rm -rf "$HOME/.claude/agents"
        cp -r "$SNAPSHOT_DIR/agents" "$HOME/.claude/agents"
        log "Restored agents from snapshot"
    fi

    log "Rollback complete"
    return 0
}

# Create detailed issue report for debugging
create_issue_report() {
    local timestamp=$(date '+%Y%m%d-%H%M%S')
    local report_file="$ISSUE_REPORT_DIR/issue-$timestamp.md"

    mkdir -p "$ISSUE_REPORT_DIR"

    local original_commit="unknown"
    [ -f "$SNAPSHOT_COMMIT_FILE" ] && original_commit=$(cat "$SNAPSHOT_COMMIT_FILE")

    local failed_commit
    failed_commit=$($DOTFILES rev-parse HEAD 2>/dev/null || echo "unknown")

    cat > "$report_file" << EOF
# Dotfiles Sync Failure Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Device:** $(hostname)
**Original Commit:** $original_commit
**Failed Commit:** $failed_commit

## Validation Errors

$(for err in "${VALIDATION_ERRORS[@]}"; do echo "- $err"; done)

## Failed Commit Details

\`\`\`
$($DOTFILES log -1 --stat 2>/dev/null || echo "Could not get commit details")
\`\`\`

## Changed Files (since working commit)

\`\`\`
$($DOTFILES diff --name-only "$original_commit"..HEAD 2>/dev/null || echo "Could not diff")
\`\`\`

## Action Required

Review the changes in the failed commit and fix the issues before re-syncing.

### Quick Commands

\`\`\`bash
# View this report
cat $report_file

# View the problematic changes
dotfiles diff $original_commit..HEAD

# Manually retry sync
~/.claude/scripts/dotfiles-sync.sh

# Check sync log
cat /tmp/dotfiles-sync.log
\`\`\`
EOF

    log "Issue report created: $report_file"
    echo "$report_file"
}

# Call Claude CLI for help with complex issues
# Usage: claude_help "description of the problem"
claude_help() {
    local issue="$1"

    if [[ "$CLAUDE_FALLBACK" != "true" ]]; then
        log "Claude fallback disabled"
        return 1
    fi

    # Check if claude CLI is available
    if ! command -v claude &>/dev/null; then
        log "Claude CLI not found"
        return 1
    fi

    # Avoid recursive calls (if we're already in a Claude session)
    if [[ -n "$CLAUDE_SESSION_ID" ]]; then
        log "Already in Claude session - skipping recursive call"
        return 1
    fi

    log "Calling Claude for help: $issue"

    local status=$($DOTFILES status 2>&1)
    local prompt="Fix this dotfiles sync issue. Work directory is \$HOME with bare repo at ~/.dotfiles.git.

Issue: $issue

Current status:
$status

Rules:
- Use 'git --git-dir=\$HOME/.dotfiles.git --work-tree=\$HOME' for all git commands
- For session files (.claude.json, history.jsonl, sessions-index.json), keep LOCAL version
- For config files (CLAUDE.md, settings.json, agents/), keep REMOTE version
- Complete the operation so 'dotfiles pull' works cleanly
- Output only the fix commands, no explanation"

    # Run claude in non-interactive mode with the prompt
    if claude -p "$prompt" --allowedTools "Bash(git *)" 2>/dev/null; then
        log "Claude resolved the issue"
        return 0
    else
        log "Claude could not resolve the issue"
        return 1
    fi
}

# Handle post-sync validation and finalization
# Returns 0 on success, 1 on failure (after rollback)
validate_and_finalize() {
    local sync_method="$1"  # e.g., "pull", "rebase", "merged"

    if validate_sync; then
        cleanup_snapshot
        echo "Config synced from remote ($sync_method) ✓"
        return 0
    else
        echo "⚠️  Sync validation failed - rolling back"
        rollback_sync
        local report_file
        report_file=$(create_issue_report)

        echo "❌ Sync failed and rolled back"
        echo "📋 Issue report: $report_file"
        echo ""
        echo "Errors:"
        for err in "${VALIDATION_ERRORS[@]}"; do
            echo "  - $err"
        done
        return 1
    fi
}

# Resolve merge conflicts by keeping local for session files
resolve_conflicts() {
    local conflicts=$($DOTFILES diff --name-only --diff-filter=U 2>/dev/null || true)
    if [ -z "$conflicts" ]; then
        return 0
    fi

    log "Resolving conflicts..."
    local resolved=0

    for file in $conflicts; do
        local keep_local=false
        for session_file in "${SESSION_FILES[@]}"; do
            if [[ "$file" == "$session_file" ]] || [[ "$file" == *"history"* ]] || [[ "$file" == *"sessions"* ]]; then
                keep_local=true
                break
            fi
        done

        if $keep_local; then
            log "Keeping local: $file"
            $DOTFILES checkout --ours "$file" 2>/dev/null
            $DOTFILES add "$file" 2>/dev/null
            ((resolved++))
        else
            log "Keeping remote: $file"
            $DOTFILES checkout --theirs "$file" 2>/dev/null
            $DOTFILES add "$file" 2>/dev/null
            ((resolved++))
        fi
    done

    if [ $resolved -gt 0 ]; then
        # Complete the merge
        $DOTFILES commit -m "Auto-resolve merge conflicts ($(date +%Y-%m-%d))" --no-edit 2>/dev/null || true
        log "Resolved $resolved conflicts"
    fi

    return 0
}

# Check if dotfiles repo exists
if [ ! -d "$HOME/.dotfiles.git" ]; then
    echo "Dotfiles repo not initialized"
    exit 0
fi

# Check for ongoing merge and resolve it
if [ -f "$HOME/.dotfiles.git/MERGE_HEAD" ]; then
    log "Found incomplete merge - resolving..."
    resolve_conflicts
fi

# Check network connectivity (quick test)
if ! ping -c 1 -W 2 github.com &>/dev/null; then
    log "No network - skipping sync"
    echo "Offline - skipping dotfiles sync"
    exit 0
fi

cd "$HOME"

# Create snapshot before any changes
create_snapshot

# Fetch remote changes
log "Fetching from origin..."
$DOTFILES fetch origin main --quiet 2>/dev/null || {
    log "Fetch failed - skipping sync"
    echo "Fetch failed - skipping sync"
    exit 0
}

# Check if we're behind
LOCAL=$($DOTFILES rev-parse HEAD)
REMOTE=$($DOTFILES rev-parse origin/main)
BASE=$($DOTFILES merge-base HEAD origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up to date"
    cleanup_snapshot
    echo "Config up to date"
    exit 0
fi

if [ "$LOCAL" = "$BASE" ]; then
    # We're behind - safe to pull
    log "Behind origin - pulling updates..."

    # Check for local uncommitted changes
    if ! $DOTFILES diff --quiet 2>/dev/null; then
        log "Local changes detected - stashing"
        $DOTFILES stash push -m "Auto-stash before sync $(date +%Y%m%d-%H%M%S)" --quiet
        STASHED=1
    fi

    # Pull changes
    if $DOTFILES pull origin main --quiet 2>/dev/null; then
        log "Pull successful"

        # Count what changed
        CHANGED=$($DOTFILES diff --stat HEAD@{1} HEAD 2>/dev/null | tail -1 || echo "")

        if [ -n "$STASHED" ]; then
            # Try to restore stash
            if $DOTFILES stash pop --quiet 2>/dev/null; then
                log "Stash restored"
            else
                log "WARNING: Stash conflict - resolving..."
                # Stash pop left conflict markers - resolve them
                local stash_conflicts=$($DOTFILES diff --name-only --diff-filter=U 2>/dev/null || true)
                if [ -n "$stash_conflicts" ]; then
                    for file in $stash_conflicts; do
                        local keep_stash=false
                        for session_file in "${SESSION_FILES[@]}"; do
                            if [[ "$file" == "$session_file" ]] || [[ "$file" == *"history"* ]] || [[ "$file" == *"sessions"* ]]; then
                                keep_stash=true
                                break
                            fi
                        done

                        if $keep_stash; then
                            # Keep stashed version (local changes) for session files
                            log "Keeping stashed version: $file"
                            $DOTFILES checkout --theirs "$file" 2>/dev/null || true
                        else
                            # Keep pulled version for config files
                            log "Keeping pulled version: $file"
                            $DOTFILES checkout --ours "$file" 2>/dev/null || true
                        fi
                        $DOTFILES add "$file" 2>/dev/null || true
                    done
                    # Clear the stash since we've resolved manually
                    $DOTFILES stash drop --quiet 2>/dev/null || true
                    log "Stash conflicts resolved"
                else
                    # No conflicts detected but stash pop still failed - drop stash
                    $DOTFILES stash drop --quiet 2>/dev/null || true
                    log "Stash dropped (no conflicts found)"
                fi
            fi
        fi

        # Validate after sync
        if validate_and_finalize "pull"; then
            if [ -n "$CHANGED" ]; then
                echo "$CHANGED"
            fi
        fi
    else
        # Pull failed - might have conflicts
        log "Pull had issues - checking for conflicts"
        if ! resolve_conflicts; then
            log "Auto-resolve failed - trying Claude fallback"
            if claude_help "Pull failed with merge conflicts that auto-resolve couldn't fix."; then
                validate_and_finalize "Claude-assisted"
            else
                echo "Config sync failed - check $LOG_FILE"
                cleanup_snapshot
            fi
        else
            validate_and_finalize "auto-resolved conflicts"
        fi
    fi

elif [ "$REMOTE" = "$BASE" ]; then
    # We're ahead - nothing to pull
    log "Ahead of origin - no pull needed"
    cleanup_snapshot
    echo "Config ahead of remote (will push on exit)"

else
    # Diverged - try rebase approach
    log "Local and remote diverged - attempting rebase"

    # Stash any local changes
    if ! $DOTFILES diff --quiet 2>/dev/null; then
        log "Stashing local changes before rebase"
        $DOTFILES stash push -m "Auto-stash before rebase $(date +%Y%m%d-%H%M%S)" --quiet
        STASHED=1
    fi

    # Try pull with rebase
    if $DOTFILES pull --rebase origin main 2>/dev/null; then
        log "Rebase successful"
        validate_and_finalize "rebased"
    else
        # Rebase failed - abort and try merge with auto-resolve
        log "Rebase failed - trying merge with auto-resolve"
        $DOTFILES rebase --abort 2>/dev/null || true

        if $DOTFILES merge origin/main --no-edit 2>/dev/null; then
            log "Merge successful"
            validate_and_finalize "merged"
        elif resolve_conflicts; then
            validate_and_finalize "auto-resolved"
        elif claude_help "Diverged history - both rebase and merge failed. Need to reconcile local and remote."; then
            validate_and_finalize "Claude-assisted"
        else
            log "All sync methods failed"
            echo "Config sync failed - manual intervention needed"
            echo "Run: dotfiles status"
            cleanup_snapshot
        fi
    fi

    # Restore stash
    if [ -n "$STASHED" ]; then
        if $DOTFILES stash pop --quiet 2>/dev/null; then
            log "Stash restored"
        else
            log "WARNING: Stash conflict after rebase/merge - resolving..."
            local stash_conflicts=$($DOTFILES diff --name-only --diff-filter=U 2>/dev/null || true)
            if [ -n "$stash_conflicts" ]; then
                for file in $stash_conflicts; do
                    local keep_stash=false
                    for session_file in "${SESSION_FILES[@]}"; do
                        if [[ "$file" == "$session_file" ]] || [[ "$file" == *"history"* ]] || [[ "$file" == *"sessions"* ]]; then
                            keep_stash=true
                            break
                        fi
                    done

                    if $keep_stash; then
                        log "Keeping stashed version: $file"
                        $DOTFILES checkout --theirs "$file" 2>/dev/null || true
                    else
                        log "Keeping pulled version: $file"
                        $DOTFILES checkout --ours "$file" 2>/dev/null || true
                    fi
                    $DOTFILES add "$file" 2>/dev/null || true
                done
                $DOTFILES stash drop --quiet 2>/dev/null || true
                log "Stash conflicts resolved"
            else
                $DOTFILES stash drop --quiet 2>/dev/null || true
                log "Stash dropped (no conflicts found)"
            fi
        fi
    fi
fi
