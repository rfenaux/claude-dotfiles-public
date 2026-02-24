#!/bin/bash
# pattern-tracker.sh - Track tool usage for intent prediction
#
# Runs on: PostToolUse hook
# Purpose:
#   1. Extract tool name from PostToolUse event
#   2. Track the tool usage with context
#   3. Silently update patterns (no output)
#
# Fails silently to not disrupt workflow.

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "pattern-tracker" || exit 0
start_timing "pattern-tracker"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
LIB_DIR="$CLAUDE_DIR/lib"
LOG_FILE="$CLAUDE_DIR/logs/pattern-tracker.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
}

# ============================================
# SECTION 1: Parse PostToolUse event
# ============================================

# Read JSON from stdin (PostToolUse provides tool_name, tool_input, etc.)
INPUT=$(cat)

# Extract tool name from the event
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)

if [ -z "$TOOL_NAME" ]; then
    log "No tool_name in event, skipping"
    exit 0
fi

# Skip tracking for certain tools (avoid noise)
case "$TOOL_NAME" in
    Read|Glob|Grep)
        # These are high-frequency, low-signal tools
        exit 0
        ;;
esac

# ============================================
# SECTION 2: Extract context
# ============================================

# Get project path from PWD
PROJECT_PATH="${PWD}"

# Extract context keywords from tool input
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // {} | tostring' 2>/dev/null)

# Build context string from tool name and input keywords
CONTEXT="$TOOL_NAME"

# Add query/command/path from tool input if present
QUERY=$(echo "$INPUT" | jq -r '.tool_input.query // .tool_input.command // .tool_input.path // empty' 2>/dev/null)
if [ -n "$QUERY" ]; then
    CONTEXT="$CONTEXT $QUERY"
fi

# ============================================
# SECTION 3: Track usage
# ============================================

PYTHON_SCRIPT="$LIB_DIR/intent_predictor.py"
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log "Python script not found: $PYTHON_SCRIPT"
    exit 0
fi

# Check if uv is available
UV_PATH=""
for uv_candidate in "/opt/homebrew/bin/uv" "$HOME/.local/bin/uv" "$(which uv 2>/dev/null)"; do
    if [ -x "$uv_candidate" ]; then
        UV_PATH="$uv_candidate"
        break
    fi
done

# Run the tracking (silent - no output)
if [ -n "$UV_PATH" ]; then
    "$UV_PATH" run python "$PYTHON_SCRIPT" track \
        --tool "$TOOL_NAME" \
        --context "$CONTEXT" \
        --project "$PROJECT_PATH" \
        >> "$LOG_FILE" 2>&1 || record_failure "pattern-tracker"
else
    python3 "$PYTHON_SCRIPT" track \
        --tool "$TOOL_NAME" \
        --context "$CONTEXT" \
        --project "$PROJECT_PATH" \
        >> "$LOG_FILE" 2>&1 || record_failure "pattern-tracker"
fi

log "Tracked: $TOOL_NAME"
end_timing "pattern-tracker"
exit 0
