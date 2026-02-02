#!/bin/bash
# Agent Completion Hook for CDP
# Called when a sub-agent completes work
#
# Integration: agent complete → commit OUTPUT.md + update CTM
#
# Usage: agent-complete.sh <workspace-path> <agent-id> <status>

set -e

WORKSPACE="$1"
AGENT_ID="$2"
STATUS="${3:-completed}"

LOG_FILE="$HOME/.claude/ctm/logs/agent-complete.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [agent-complete] $1" >> "$LOG_FILE"
}

if [ -z "$WORKSPACE" ] || [ ! -d "$WORKSPACE" ]; then
    log "Invalid workspace: $WORKSPACE"
    exit 1
fi

log "Agent $AGENT_ID completed with status: $STATUS"

# Get project root (parent of .agent-workspaces)
PROJECT_DIR=$(dirname "$(dirname "$WORKSPACE")")

# Check if OUTPUT.md exists
OUTPUT_FILE="$WORKSPACE/OUTPUT.md"
if [ ! -f "$OUTPUT_FILE" ]; then
    log "No OUTPUT.md found at $OUTPUT_FILE"
    exit 0
fi

log "Processing OUTPUT.md for agent $AGENT_ID"

# 1. Commit OUTPUT.md to git (if project has git)
if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"

    # Get relative path
    REL_WORKSPACE="${WORKSPACE#$PROJECT_DIR/}"

    # Stage OUTPUT.md
    git add "$REL_WORKSPACE/OUTPUT.md" 2>/dev/null || true

    # Extract summary from OUTPUT.md for commit message
    SUMMARY=$(head -5 "$OUTPUT_FILE" | grep -E "^##|^\*\*" | head -1 | sed 's/[#*]//g' | xargs)

    if [ -z "$SUMMARY" ]; then
        SUMMARY="Agent $AGENT_ID completed"
    fi

    # Commit
    git commit -m "Agent output: $SUMMARY

Agent ID: $AGENT_ID
Status: $STATUS
Workspace: $REL_WORKSPACE

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>" 2>/dev/null && {
        COMMIT_HASH=$(git rev-parse --short HEAD)
        log "Committed OUTPUT.md: $COMMIT_HASH"
        echo "[Git] Agent output committed: $COMMIT_HASH"
    } || {
        log "Git commit skipped (no changes or error)"
    }
fi

# 2. Update CTM context with agent completion
if [ -f "$HOME/.claude/ctm/scheduler.json" ]; then
    cd "$HOME/.claude/ctm/lib"

    python3 << EOF
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')

try:
    from scheduler import get_scheduler
    from agents import get_agent, update_agent

    scheduler = get_scheduler()
    active_id = scheduler.get_active()

    if active_id:
        agent = get_agent(active_id)
        if agent:
            # Add note about sub-agent completion
            note = {
                "text": f"Sub-agent {'"$AGENT_ID"'} completed ({'"$STATUS"'})",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "agent_completion"
            }

            if "notes" not in agent.context:
                agent.context["notes"] = []
            agent.context["notes"].append(note)

            update_agent(agent)
            print(f"[CTM] Noted agent completion for [{active_id}]")
except Exception as e:
    print(f"CTM update skipped: {e}")
EOF
fi

# 3. Index OUTPUT.md to RAG (if project has RAG)
if [ -d "$PROJECT_DIR/.rag" ]; then
    log "Indexing OUTPUT.md to RAG"

    python3 << EOF &
import subprocess
try:
    result = subprocess.run(
        ["python3", "-m", "rag_server.index", "--path", "$OUTPUT_FILE", "--project", "$PROJECT_DIR"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print("[RAG] Indexed OUTPUT.md")
except Exception as e:
    print(f"RAG index skipped: {e}")
EOF
fi

log "Agent completion processing done"
