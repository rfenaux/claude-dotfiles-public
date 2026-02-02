#!/bin/bash
# Append to Daily Memory Log
# Usage: daily-log-append.sh <project_path> <type> <content>
# Types: decision, learning, note
#
# Part of: OpenClaw-inspired improvements (Phase 2, F05)
# Created: 2026-01-30

PROJECT_PATH="$1"
TYPE="$2"
CONTENT="$3"

if [ -z "$PROJECT_PATH" ] || [ -z "$TYPE" ] || [ -z "$CONTENT" ]; then
    echo "Usage: daily-log-append.sh <project_path> <type> <content>"
    echo "Types: decision, learning, note"
    exit 1
fi

MEMORY_DIR="$PROJECT_PATH/.claude/memory"
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%H:%M)
LOG_FILE="$MEMORY_DIR/$TODAY.md"

# Ensure directory exists
mkdir -p "$MEMORY_DIR"

# Create log file if not exists
if [ ! -f "$LOG_FILE" ]; then
    cat > "$LOG_FILE" << EOF
# Session Notes: $TODAY

## Decisions

## Learnings

## Notes

---
EOF
fi

# Map type to section
case "$TYPE" in
    decision|decisions)
        SECTION="## Decisions"
        ;;
    learning|learnings)
        SECTION="## Learnings"
        ;;
    note|notes|*)
        SECTION="## Notes"
        ;;
esac

# Create temp file for atomic write
TEMP_FILE=$(mktemp)

# Read file and insert content after section header
awk -v section="$SECTION" -v timestamp="$TIMESTAMP" -v content="$CONTENT" '
{
    print
    if ($0 == section) {
        print ""
        print "- [" timestamp "] " content
    }
}
' "$LOG_FILE" > "$TEMP_FILE"

# Move temp file to log file
mv "$TEMP_FILE" "$LOG_FILE"

echo "Appended to $LOG_FILE"
