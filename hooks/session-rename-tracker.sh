#!/bin/bash
# Session Rename Tracker
# Tracks message count and suggests rename after threshold
# Called by: UserPromptSubmit, PreCompact, SessionEnd hooks

set -euo pipefail

STATE_FILE="$HOME/.claude/session-rename-state.json"
THRESHOLD=4  # Suggest rename after this many user messages

# Ensure state file exists
if [[ ! -f "$STATE_FILE" ]]; then
    echo '{"renamed_sessions":[],"message_counts":{}}' > "$STATE_FILE"
fi

# Read input from stdin (hook context)
input=$(cat)

# Extract session ID
session_id=$(echo "$input" | jq -r '.session_id // empty')
[[ -z "$session_id" ]] && exit 0

# Get trigger type from environment (set by different hooks)
trigger="${RENAME_TRIGGER:-message}"

# Check if already renamed
already_renamed=$(jq -r --arg sid "$session_id" '.renamed_sessions | index($sid) != null' "$STATE_FILE" 2>/dev/null || echo "false")

if [[ "$already_renamed" == "true" ]]; then
    exit 0  # Already renamed, skip
fi

case "$trigger" in
    message)
        # Increment message count
        current_count=$(jq -r --arg sid "$session_id" '.message_counts[$sid] // 0' "$STATE_FILE")
        new_count=$((current_count + 1))

        # Update count in state file
        jq --arg sid "$session_id" --argjson count "$new_count" \
            '.message_counts[$sid] = $count' "$STATE_FILE" > /tmp/rename-state.json \
            && mv /tmp/rename-state.json "$STATE_FILE"

        # Check threshold
        if [[ $new_count -eq $THRESHOLD ]]; then
            echo "[Session] 💡 Consider running /rename-smart to name this session"
        fi
        ;;

    precompact)
        # Always suggest at precompact if not renamed
        echo "[Session] 📝 Session unnamed - consider /rename-smart before compaction"
        ;;

    sessionend)
        # Suggest at session end if not renamed
        echo "[Session] 📝 Session still unnamed - run /rename-smart to preserve context"
        ;;
esac

exit 0
