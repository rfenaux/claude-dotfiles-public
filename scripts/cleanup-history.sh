#!/usr/bin/env bash
# cleanup-history.sh - Remove old debug/history files
# Usage: ./cleanup-history.sh [--dry-run]
# Retention: debug/file-history=30 days, conversation-history=90 days

set -euo pipefail

DRY_RUN=""
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN="echo [DRY RUN] would delete:"

CLAUDE_DIR="${HOME}/.claude"
DEBUG_RETENTION=30
HISTORY_RETENTION=30
CONVO_RETENTION=90

echo "=== Claude Code History Cleanup ==="
echo "Retention: debug=${DEBUG_RETENTION}d, file-history=${HISTORY_RETENTION}d, conversation=${CONVO_RETENTION}d"
echo ""

for dir_info in "debug:${DEBUG_RETENTION}" "file-history:${HISTORY_RETENTION}" "conversation-history:${CONVO_RETENTION}"; do
    dir="${dir_info%%:*}"
    days="${dir_info##*:}"
    target="${CLAUDE_DIR}/${dir}"

    if [[ -d "$target" ]]; then
        before=$(find "$target" -type f | wc -l | tr -d ' ')
        if [[ -n "$DRY_RUN" ]]; then
            count=$(find "$target" -type f -mtime +${days} | wc -l | tr -d ' ')
            echo "${dir}: ${count} files older than ${days} days (of ${before} total)"
        else
            find "$target" -type f -mtime +${days} -delete
            after=$(find "$target" -type f | wc -l | tr -d ' ')
            deleted=$((before - after))
            echo "${dir}: deleted ${deleted} files (${before} → ${after})"
        fi
    else
        echo "${dir}: directory not found, skipping"
    fi
done

# Also clean empty directories
find "${CLAUDE_DIR}/debug" "${CLAUDE_DIR}/file-history" "${CLAUDE_DIR}/conversation-history" -type d -empty -delete 2>/dev/null || true

echo ""
echo "Cleanup complete."
