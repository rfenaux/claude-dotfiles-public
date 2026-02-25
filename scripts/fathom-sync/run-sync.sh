#!/bin/bash
# Fathom Transcript Sync - Wrapper Script
# Called by launchd to sync transcripts daily

set -e

# Use the fathom MCP server's Python environment
PYTHON="${HOME}/.claude/mcp-servers/fathom/.venv/bin/python"
SCRIPT="${HOME}/.claude/scripts/fathom-sync/sync_fathom_transcripts.py"

# Load API key from environment (set in ~/.zshrc or .env)
export FATHOM_API_KEY="${FATHOM_API_KEY:?Error: FATHOM_API_KEY not set. Add to ~/.zshrc or ~/.env}"

# Run the sync script
"$PYTHON" "$SCRIPT" --days 1
