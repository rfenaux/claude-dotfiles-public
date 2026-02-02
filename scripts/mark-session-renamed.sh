#!/bin/bash
# Mark a session as renamed in the state file
# Usage: mark-session-renamed.sh <session-id>

set -euo pipefail

STATE_FILE="$HOME/.claude/session-rename-state.json"
SESSION_ID="${1:-}"

if [[ -z "$SESSION_ID" ]]; then
    echo "Usage: mark-session-renamed.sh <session-id>"
    exit 1
fi

# Ensure state file exists
if [[ ! -f "$STATE_FILE" ]]; then
    echo '{"renamed_sessions":[],"message_counts":{}}' > "$STATE_FILE"
fi

# Add session to renamed list (if not already there)
jq --arg sid "$SESSION_ID" '
  if (.renamed_sessions | index($sid)) then .
  else .renamed_sessions += [$sid]
  end
' "$STATE_FILE" > /tmp/rename-state.json && mv /tmp/rename-state.json "$STATE_FILE"

echo "Session $SESSION_ID marked as renamed"
