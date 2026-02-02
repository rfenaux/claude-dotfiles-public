#!/bin/bash
# decision-drift-check.sh - Pre-session hook to surface decisions from conversation files
# Checks for decision keywords in .txt files and compares against DECISIONS.md

PROJECT_DIR="${PWD}"
DECISIONS_FILE="${PROJECT_DIR}/.claude/context/DECISIONS.md"

# Colors
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Find .txt files in project root (conversation exports)
TXT_FILES=$(find "$PROJECT_DIR" -maxdepth 1 -name "*.txt" -type f 2>/dev/null)

if [ -z "$TXT_FILES" ]; then
    exit 0
fi

# Search for decision keywords
RESOLVED_MATCHES=$(grep -l -i "resolved\|decided\|confirmed\|question.*yes\|all.*done" $TXT_FILES 2>/dev/null)

if [ -n "$RESOLVED_MATCHES" ]; then
    echo -e "${YELLOW}[Decision Drift Check]${NC} Found decision keywords in conversation files:"
    for file in $RESOLVED_MATCHES; do
        BASENAME=$(basename "$file")
        # Extract date from filename if present (format: YYYY-MM-DD-*)
        DATE_MATCH=$(echo "$BASENAME" | grep -oE "^[0-9]{4}-[0-9]{2}-[0-9]{2}")
        if [ -n "$DATE_MATCH" ]; then
            echo -e "  ${GREEN}→${NC} $BASENAME (from $DATE_MATCH)"
        else
            echo -e "  ${GREEN}→${NC} $BASENAME"
        fi
    done

    # Check if DECISIONS.md exists and has PENDING items
    if [ -f "$DECISIONS_FILE" ]; then
        PENDING_COUNT=$(grep -c "PENDING\|Pending\|pending" "$DECISIONS_FILE" 2>/dev/null || echo "0")
        if [ "$PENDING_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}  ⚠ DECISIONS.md has $PENDING_COUNT pending items - may need reconciliation${NC}"
            echo -e "  Run: /decision-sync"
        fi
    fi
    echo ""
fi
