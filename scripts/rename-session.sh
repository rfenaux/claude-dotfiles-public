#!/bin/bash
# Programmatically rename a Claude Code session
# Usage: rename-session.sh <session-id> <new-name>
#
# Updates the sessions-index.json file to change the session summary

set -euo pipefail

SESSION_ID="${1:-}"
NEW_NAME="${2:-}"

if [[ -z "$SESSION_ID" || -z "$NEW_NAME" ]]; then
    echo "Usage: rename-session.sh <session-id> <new-name>"
    echo "Example: rename-session.sh abc123-def456 '2026-01-23_1130_my-session-title'"
    exit 1
fi

# Find the project directory for this session
PROJECT_DIR=""
for dir in ~/.claude/projects/*/; do
    if [[ -f "${dir}${SESSION_ID}.jsonl" ]]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [[ -z "$PROJECT_DIR" ]]; then
    echo "Error: Session $SESSION_ID not found in any project"
    exit 1
fi

INDEX_FILE="${PROJECT_DIR}sessions-index.json"

if [[ ! -f "$INDEX_FILE" ]]; then
    echo "Error: sessions-index.json not found in $PROJECT_DIR"
    exit 1
fi

# Update the summary field for this session
jq --arg sid "$SESSION_ID" --arg name "$NEW_NAME" '
  .entries = [.entries[] | if .sessionId == $sid then .summary = $name else . end]
' "$INDEX_FILE" > /tmp/sessions-index-new.json

# Validate JSON before replacing
if jq empty /tmp/sessions-index-new.json 2>/dev/null; then
    mv /tmp/sessions-index-new.json "$INDEX_FILE"
    echo "✓ Session $SESSION_ID renamed to: $NEW_NAME"
else
    echo "Error: Failed to generate valid JSON"
    rm -f /tmp/sessions-index-new.json
    exit 1
fi
