#!/bin/bash
# cleanup-debug.sh - Remove old debug files
# Keeps last N days of debug output, deletes older ones
# Run manually or via weekly launchd job

set -euo pipefail

DEBUG_DIR="$HOME/.claude/debug"
RETENTION_DAYS="${1:-7}"

[[ -d "$DEBUG_DIR" ]] || { echo "[Cleanup] No debug directory"; exit 0; }

# Count before
before=$(find "$DEBUG_DIR" -type f | wc -l | tr -d ' ')
before_size=$(du -sh "$DEBUG_DIR" 2>/dev/null | cut -f1)

# Delete files older than retention period
deleted=0
while IFS= read -r -d '' file; do
    rm -f "$file"
    ((deleted++))
done < <(find "$DEBUG_DIR" -type f -mtime +"$RETENTION_DAYS" -print0 2>/dev/null)

# Count after
after=$(find "$DEBUG_DIR" -type f | wc -l | tr -d ' ')
after_size=$(du -sh "$DEBUG_DIR" 2>/dev/null | cut -f1)

echo "[Cleanup] debug: $deleted files deleted ($before -> $after files, $before_size -> $after_size)"
