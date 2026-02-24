#!/bin/bash
# proactive-rag-surfacer.sh - Surface relevant documents at session start
#
# Runs on: SessionStart hook
# Purpose:
#   1. Extract CTM context (active task, tags, decisions)
#   2. Build weighted query for RAG search
#   3. Cascade through lessons → config → project RAG indexes
#   4. Output brief summaries of relevant documents
#
# Output is added to Claude's context via hook system.
# Fails silently to not block session start.

set +e  # fail-silent: hooks must not abort on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
LIB_DIR="$CLAUDE_DIR/lib"
CONFIG_FILE="$CLAUDE_DIR/config/proactive-rag.json"
LOG_FILE="$CLAUDE_DIR/logs/proactive-memory.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
}

# ============================================
# SECTION 1: Check if enabled
# ============================================

if [ -f "$CONFIG_FILE" ]; then
    ENABLED=$(jq -r '.enabled // true' "$CONFIG_FILE" 2>/dev/null)
    if [ "$ENABLED" = "false" ]; then
        log "Proactive RAG disabled via config"
        exit 0
    fi
fi

# ============================================
# SECTION 2: Check dependencies
# ============================================

# Check if Python script exists
PYTHON_SCRIPT="$LIB_DIR/proactive_rag.py"
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log "Python script not found: $PYTHON_SCRIPT"
    exit 0
fi

# Check if uv is available (for running with RAG server dependencies)
# Try common locations
UV_PATH=""
for uv_candidate in "/opt/homebrew/bin/uv" "$HOME/.local/bin/uv" "$(which uv 2>/dev/null)"; do
    if [ -x "$uv_candidate" ]; then
        UV_PATH="$uv_candidate"
        break
    fi
done

if [ -n "$UV_PATH" ]; then
    USE_UV=true
else
    log "uv not found, falling back to python3"
    USE_UV=false
fi

# ============================================
# SECTION 3: Run proactive RAG surfacing
# ============================================

PROJECT_PATH="${PWD}"

log "Starting proactive RAG surfacing for project: $PROJECT_PATH"

# Run the Python script
# Use uv if available to ensure RAG server dependencies are available
if [ "$USE_UV" = true ]; then
    OUTPUT=$("$UV_PATH" run --directory "$CLAUDE_DIR/mcp-servers/rag-server" \
        python "$PYTHON_SCRIPT" --project "$PROJECT_PATH" 2>/dev/null) || true
else
    OUTPUT=$(python3 "$PYTHON_SCRIPT" --project "$PROJECT_PATH" 2>/dev/null) || true
fi

# ============================================
# SECTION 4: Output results
# ============================================

if [ -n "$OUTPUT" ]; then
    log "Proactive RAG surfaced ${#OUTPUT} characters"
    echo "$OUTPUT"

    # v3.3: Log surfacing event for metrics
    SURFACING_LOG="$CLAUDE_DIR/lessons/surfacing.jsonl"
    SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
    CTM_TASK_ID=""
    if [ -f "$CLAUDE_DIR/ctm/scheduler.json" ]; then
        CTM_TASK_ID=$(python3 -c "
import json
d = json.load(open('$CLAUDE_DIR/ctm/scheduler.json'))
print(d.get('active_agent') or (d.get('priority_queue',[['']])[0][0] if d.get('priority_queue') else ''))
" 2>/dev/null || echo "")
    fi
    python3 -c "
import json, sys
from datetime import datetime, timezone
event = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'context': 'SessionStart',
    'session_id': sys.argv[1],
    'ctm_task_id': sys.argv[2] or None,
    'chars_surfaced': int(sys.argv[3])
}
with open(sys.argv[4], 'a') as f:
    f.write(json.dumps(event, separators=(',',':')) + '\n')
" "$SESSION_ID" "$CTM_TASK_ID" "${#OUTPUT}" "$SURFACING_LOG" 2>/dev/null || true
else
    log "No proactive context to surface"
fi

exit 0
