#!/bin/bash
# cleanup-conversations.sh - Remove old conversation history files
# Keeps last N days of conversations, deletes older ones
# Run manually or via weekly launchd job

set -euo pipefail

CONV_DIR="$HOME/.claude/conversation-history"
RETENTION_DAYS="${1:-30}"

[[ -d "$CONV_DIR" ]] || { echo "[Cleanup] No conversation-history directory"; exit 0; }

# Count before
before=$(find "$CONV_DIR" -type f | wc -l | tr -d ' ')
before_size=$(du -sh "$CONV_DIR" 2>/dev/null | cut -f1)

# Delete files older than retention period
deleted=0
while IFS= read -r -d '' file; do
    rm -f "$file"
    ((deleted++))
done < <(find "$CONV_DIR" -type f -mtime +"$RETENTION_DAYS" -print0 2>/dev/null)

# Count after
after=$(find "$CONV_DIR" -type f | wc -l | tr -d ' ')
after_size=$(du -sh "$CONV_DIR" 2>/dev/null | cut -f1)

echo "[Cleanup] conversation-history: $deleted files deleted ($before -> $after files, $before_size -> $after_size)"
