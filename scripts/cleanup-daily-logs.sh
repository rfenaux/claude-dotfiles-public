#!/bin/bash
# Cleanup old daily logs (older than 30 days by default)
#
# Part of: OpenClaw-inspired improvements (Phase 2, F05)
# Created: 2026-01-30

RETENTION_DAYS=${1:-30}

echo "Cleaning up daily logs older than $RETENTION_DAYS days..."

count=0

# Global memory directory
if [ -d "$HOME/.claude/memory" ]; then
    deleted=$(find "$HOME/.claude/memory" -name "????-??-??.md" -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
    count=$((count + deleted))
fi

# Project memory directories
for dir in ~/Documents/Projects/*/.claude/memory ~/Documents/Docs*/*/.claude/memory; do
    if [ -d "$dir" ]; then
        deleted=$(find "$dir" -name "????-??-??.md" -mtime +$RETENTION_DAYS -delete -print 2>/dev/null | wc -l)
        count=$((count + deleted))
    fi
done 2>/dev/null

echo "Deleted $count old log files."
