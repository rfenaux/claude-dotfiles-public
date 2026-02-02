#!/bin/bash
# Daily Memory Log Initialization
# Creates today's log file and injects recent logs into context
#
# Part of: OpenClaw-inspired improvements (Phase 2, F05)
# Created: 2026-01-30

# Get project path from environment or current directory
PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"
MEMORY_DIR="$PROJECT_PATH/.claude/memory"

# Date handling (macOS and Linux compatible)
TODAY=$(date +%Y-%m-%d)
if [[ "$OSTYPE" == "darwin"* ]]; then
    YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null)
else
    YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null)
fi

# Only proceed if this looks like a Claude project
if [ ! -d "$PROJECT_PATH/.claude" ]; then
    exit 0
fi

# Ensure memory directory exists
mkdir -p "$MEMORY_DIR" 2>/dev/null || exit 0

# Create today's log if not exists
if [ ! -f "$MEMORY_DIR/$TODAY.md" ]; then
    cat > "$MEMORY_DIR/$TODAY.md" << EOF
# Session Notes: $TODAY

## Decisions

<!-- Decisions will be auto-captured here -->

## Learnings

<!-- Learnings discovered during sessions -->

## Notes

<!-- Manual notes and observations -->

---
*Auto-created by daily-log-init*
EOF
fi

# Output for context injection (keep brief to save tokens)
echo ""
echo "=== Daily Memory ($TODAY) ==="

# Show today's log (first 25 lines, skip empty/comment lines for brevity)
if [ -f "$MEMORY_DIR/$TODAY.md" ]; then
    grep -v "^$\|^<!--\|^---\|^\*Auto" "$MEMORY_DIR/$TODAY.md" 2>/dev/null | head -25
fi

# Show yesterday's key items if exists
if [ -n "$YESTERDAY" ] && [ -f "$MEMORY_DIR/$YESTERDAY.md" ]; then
    # Check if there's actual content (not just template)
    content_lines=$(grep -c "^- " "$MEMORY_DIR/$YESTERDAY.md" 2>/dev/null || echo "0")
    if [ "$content_lines" -gt 0 ]; then
        echo ""
        echo "--- Yesterday ($YESTERDAY) ---"
        # Show headers and items
        grep -E "^## |^- " "$MEMORY_DIR/$YESTERDAY.md" 2>/dev/null | head -10
    fi
fi
