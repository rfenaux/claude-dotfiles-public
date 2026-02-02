#!/bin/bash
# Detects sub-agents and swaps to slim CLAUDE.md
#
# Main session: Started via wrapper → has CLAUDE_MAIN_SESSION=true → keep full
# Sub-agent: Spawned via Task tool → no env var → swap to slim

CLAUDE_DIR="$HOME/.claude"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
CLAUDE_MD_SLIM="$CLAUDE_DIR/CLAUDE.md.slim"

# If CLAUDE_MAIN_SESSION is set, this is a main session - do nothing
if [[ "${CLAUDE_MAIN_SESSION:-}" == "true" ]]; then
    exit 0
fi

# This is a sub-agent - swap to slim if available
if [[ -f "$CLAUDE_MD_SLIM" ]]; then
    cp "$CLAUDE_MD_SLIM" "$CLAUDE_MD"
    echo "Sub-agent detected: using slim CLAUDE.md"
fi
