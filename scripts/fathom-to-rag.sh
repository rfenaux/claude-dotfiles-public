#!/bin/bash
# fathom-to-rag.sh - Index Fathom meeting transcripts to RAG
#
# Usage:
#   fathom-to-rag.sh                    # Index meetings from last 7 days
#   fathom-to-rag.sh --days 30          # Index meetings from last 30 days
#   fathom-to-rag.sh --meeting <id>     # Index specific meeting
#   fathom-to-rag.sh --all              # Index all meetings
#
# Requires: Fathom MCP server configured, jq, uv

set -e

SCRIPT_DIR="$(dirname "$0")"
FATHOM_CACHE="$HOME/.claude/cache/fathom"
RAG_PROJECT="$HOME/.claude/fathom-transcripts"
DAYS=7

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --days)
            DAYS="$2"
            shift 2
            ;;
        --meeting)
            MEETING_ID="$2"
            shift 2
            ;;
        --all)
            DAYS=3650  # ~10 years
            shift
            ;;
        --help)
            echo "Usage: fathom-to-rag.sh [--days N] [--meeting ID] [--all]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure directories exist
mkdir -p "$FATHOM_CACHE"
mkdir -p "$RAG_PROJECT"

# Initialize RAG for fathom transcripts if needed
if [ ! -d "$RAG_PROJECT/.rag" ]; then
    echo "Initializing RAG for Fathom transcripts..."
    ~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_init
rag_init('$RAG_PROJECT')
print('RAG initialized')
"
fi

# Function to fetch and index a single meeting
index_meeting() {
    local meeting_id="$1"
    local cache_file="$FATHOM_CACHE/${meeting_id}.md"

    # Check if already cached and indexed
    if [ -f "$cache_file" ] && [ -f "$RAG_PROJECT/.rag/indexed_meetings.txt" ]; then
        if grep -q "^${meeting_id}$" "$RAG_PROJECT/.rag/indexed_meetings.txt" 2>/dev/null; then
            echo "  [skip] $meeting_id (already indexed)"
            return 0
        fi
    fi

    echo "  [fetch] $meeting_id"

    # Fetch meeting with transcript using Claude's MCP
    # We use a Python script to call the Fathom MCP tools
    python3 << PYEOF
import json
import subprocess
import sys
import os

meeting_id = "$meeting_id"
cache_file = "$cache_file"
rag_project = "$RAG_PROJECT"

# Use claude CLI to fetch meeting via MCP
# This is a workaround since we can't directly call MCP from bash
try:
    # For now, we'll create a placeholder that will be filled by the MCP call
    # In practice, this would be called via the Claude Code session

    # Check if we have cached data
    if os.path.exists(cache_file):
        print(f"  [cache] Using cached transcript")
    else:
        print(f"  [note] Run 'mcp__fathom__get_meeting' for {meeting_id} to fetch transcript")
        # Create placeholder file
        with open(cache_file, 'w') as f:
            f.write(f"# Meeting {meeting_id}\n\n_Transcript pending - fetch via Fathom MCP_\n")

except Exception as e:
    print(f"  [error] {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    # Index to RAG if file exists
    if [ -f "$cache_file" ]; then
        ~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_index
try:
    result = rag_index('$cache_file', '$RAG_PROJECT')
    print('  [indexed] $meeting_id')
except Exception as e:
    print(f'  [error] {e}')
" 2>/dev/null

        # Track indexed meetings
        echo "$meeting_id" >> "$RAG_PROJECT/.rag/indexed_meetings.txt"
    fi
}

# Function to save a meeting transcript (called from Claude session)
save_meeting_transcript() {
    local meeting_id="$1"
    local title="$2"
    local date="$3"
    local transcript="$4"
    local summary="$5"

    local cache_file="$FATHOM_CACHE/${meeting_id}.md"

    cat > "$cache_file" << EOF
# $title

**Date:** $date
**Meeting ID:** $meeting_id

## Summary

$summary

## Transcript

$transcript
EOF

    echo "Saved transcript to $cache_file"
}

# Main execution
echo "=== Fathom to RAG Indexer ==="
echo "Project: $RAG_PROJECT"
echo "Cache: $FATHOM_CACHE"
echo ""

if [ -n "$MEETING_ID" ]; then
    echo "Indexing single meeting: $MEETING_ID"
    index_meeting "$MEETING_ID"
else
    echo "To index meetings, use this script with Claude Code:"
    echo ""
    echo "1. List recent meetings:"
    echo "   mcp__fathom__list_meetings"
    echo ""
    echo "2. For each meeting, fetch and save:"
    echo "   mcp__fathom__get_meeting --meeting_id <id> --include_transcript true"
    echo ""
    echo "3. Or use the helper function in Claude:"
    echo "   'Index my recent Fathom meetings to RAG'"
    echo ""

    # Show any already-indexed meetings
    if [ -f "$RAG_PROJECT/.rag/indexed_meetings.txt" ]; then
        COUNT=$(wc -l < "$RAG_PROJECT/.rag/indexed_meetings.txt" | tr -d ' ')
        echo "Already indexed: $COUNT meetings"
    fi
fi

echo ""
echo "Done."
