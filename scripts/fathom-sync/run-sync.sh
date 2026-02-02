#!/bin/bash
# Fathom Transcript Sync - Wrapper Script
# Called by launchd to sync transcripts daily

set -e

# Use the fathom MCP server's Python environment
PYTHON="~/.claude/mcp-servers/fathom/.venv/bin/python"
SCRIPT="~/.claude/scripts/fathom-sync/sync_fathom_transcripts.py"

# Load API key from MCP config
export FATHOM_API_KEY="xBzezPDDj8kIsnXDOwsTiw.Pgx0ZdvtWIPCyYsP9rDTWdLzwdI94HyLOaCb5OHkzUg"

# Run the sync script
"$PYTHON" "$SCRIPT" --days 1
