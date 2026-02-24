#!/bin/bash
# daily-memory-log.sh - Create daily memory log at session start
# Auto-creates temporal memory files for decision/learning capture
#
# Part of: OpenClaw Phase 2 (F05, QW-5)
# Created: 2026-02-14
# Event: SessionStart
#
# Creates ~/.claude/memory/daily/YYYY-MM-DD.md if not exists.
# Injects yesterday's log summary for continuity.

set +e  # fail-silent: hooks must not abort on error

MEMORY_DIR="$HOME/.claude/memory/daily"
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d yesterday +%Y-%m-%d 2>/dev/null || echo "")
TODAY_FILE="$MEMORY_DIR/$TODAY.md"

# Ensure directory exists
mkdir -p "$MEMORY_DIR"

# Create today's log if not exists
if [ ! -f "$TODAY_FILE" ]; then
    cat > "$TODAY_FILE" << EOF
# Session Notes: $TODAY

## Decisions

<!-- Auto-captured decisions will be appended below -->

## Learnings

<!-- Auto-captured learnings will be appended below -->

## Notes

<!-- Manual notes -->

EOF
fi

# Build output
OUTPUT=""

# Show today's log stats
TODAY_LINES=$(wc -l < "$TODAY_FILE" | tr -d ' ')
if [ "$TODAY_LINES" -gt 12 ]; then
    # Has content beyond template
    DECISION_COUNT=$(grep -c "^- " "$TODAY_FILE" 2>/dev/null) || DECISION_COUNT=0
    if [ "$DECISION_COUNT" -gt 0 ]; then
        OUTPUT="[Daily Log] $TODAY: $DECISION_COUNT entries"
    fi
fi

# Show yesterday summary if exists
if [ -n "$YESTERDAY" ] && [ -f "$MEMORY_DIR/$YESTERDAY.md" ]; then
    YESTERDAY_LINES=$(wc -l < "$MEMORY_DIR/$YESTERDAY.md" | tr -d ' ')
    if [ "$YESTERDAY_LINES" -gt 15 ]; then
        YESTERDAY_DECISIONS=$(grep -c "^- " "$MEMORY_DIR/$YESTERDAY.md" 2>/dev/null) || YESTERDAY_DECISIONS=0
        if [ "$YESTERDAY_DECISIONS" -gt 0 ]; then
            OUTPUT="${OUTPUT:+$OUTPUT | }Yesterday ($YESTERDAY): $YESTERDAY_DECISIONS entries"
        fi
    fi
fi

# Cleanup: remove logs older than 30 days
find "$MEMORY_DIR" -name "*.md" -mtime +30 -delete 2>/dev/null || true

# Output summary (only if there's content to show)
if [ -n "$OUTPUT" ]; then
    echo "$OUTPUT"
fi

exit 0
